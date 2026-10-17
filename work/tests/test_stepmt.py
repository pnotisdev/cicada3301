"""GPU seed sweep of the step-domain cipher (work/phpmt/step.py + stepmt.cu): gates of docs/GPU_PORT.md.
  (a) key values of every generator, both alphabets (28 / 29), equal the Rust `keys` mode (which test_gens.py checks against
      CPython, NumPy and published vectors);
  (b) every score of every setting equals the numpy reference built from those keys and step28.py;
  (c) a planted seed is recovered at rank 1, with its exact setting, for every generator;
  (d) random ciphertext gives no candidate."""
import os
import subprocess
import sys
import tempfile
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(WORK, "phpmt"))
sys.path.insert(0, os.path.join(WORK, "kscreen"))
sys.path.insert(0, WORK)

try:
    import cupy  # noqa: F401
    import step as ST
    CUDA = True
except Exception:  # noqa: BLE001
    CUDA = False

import step28  # noqa: E402

PH = os.path.join(WORK, "phpmt")
_EXE = "phpmt.exe" if os.name == "nt" else "phpmt"
_CAND = [p for p in (os.path.join(PH, "target", "release", _EXE), os.path.join(PH, "target_gen", "release", _EXE)) if os.path.exists(p)]
BIN = max(_CAND, key=os.path.getmtime) if _CAND else None
K = 256
GENS = ["php", "glibc", "net", "py3", "mt32", "mt31", "java", "msvc", "drand48", "ruby"]
SEED_SETS = [(0, 12), (2147483640, 2147483650), (4294967290, 4294967296)]


def rust_keys(gen, lo, hi, km):
    """{seed: [map0, map1]} from the Rust engine"""
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "k.txt")
        subprocess.run([BIN, "keysn", gen, str(lo), str(hi), out, str(km), str(K)], check=True, capture_output=True)
        res = {}
        with open(out) as f:
            for line in f:
                v = [int(x) for x in line.split()]
                res[v[0]] = [np.array(v[1:1 + K]), np.array(v[1 + K:])]
    return res


@unittest.skipUnless(CUDA and BIN, "needs CuPy and the Rust build (cargo build --release in work/phpmt)")
class StepSweep(unittest.TestCase):
    def test_keys_equal_the_rust_engine(self):
        for gen in GENS:
            S = ST.Step(gen, ST.make_windows("07"), dump=2)
            for lo, hi in SEED_SETS:
                r28, r29 = rust_keys(gen, lo, hi, 28), rust_keys(gen, lo, hi, 29)
                g = S.keys(lo, hi - lo)
                for seed in range(lo, hi):
                    for m in range(2):
                        self.assertTrue((g[seed][0][m] == r28[seed][m]).all(), (gen, seed, "km 28 map", m))
                        self.assertTrue((g[seed][1][m] == r29[seed][m]).all(), (gen, seed, "km 29 map", m))

    def test_scores_equal_the_numpy_reference(self):
        for gen in GENS:
            wins = ST.make_windows("07") + ST.make_windows("all")[3:5]
            S = ST.Step(gen, wins, dump=1)
            lo, hi = 1000, 1010
            r28, r29 = rust_keys(gen, lo, hi, 28), rust_keys(gen, lo, hi, 29)
            gpu = S.scores(lo, hi - lo)
            for seed in range(lo, hi):
                ref = ST.ref_scores(r28[seed], r29[seed], wins)
                for (w, c), v in ref.items():
                    self.assertEqual(gpu[(seed, w, c)], v, (gen, seed, w, c))

    def test_planted_seed_is_recovered(self):
        rng = np.random.default_rng(7)
        import attack
        import lp
        for gi, gen in enumerate(GENS):
            seed = int(rng.integers(100000, 2 ** 31 - 5000))
            r28, r29 = rust_keys(gen, seed, seed + 1, 28)[seed], rust_keys(gen, seed, seed + 1, 29)[seed]
            for variant, mp, mode, m in (("A", gi % 2, "drop", 5), ("B", (gi + 1) % 2, "keep", 3), ("C", gi % 2, "keep", 11)):
                toks = attack.synthetic_tokens(300, start=int(rng.integers(5000, 40000)))
                p = np.array(lp.runes_of(toks))[:ST.NS]
                p = np.where(p == 14, 6, p)
                q = np.where(p > 14, p - 1, p)
                ditto = rng.random(len(q)) < 0.0066
                ditto[20] = True                      # a zero step makes the two modes differ
                key = step28.LOG2[r29[mp][r29[mp] != 0]] if variant == "B" else r28[mp]
                off = gi % 2                          # the pad's first key index inside the window: 0 or 1
                c, prev = step28.encrypt(q, key, variant, mode, m, off, ditto)
                S = ST.Step(gen, [("plant", prev, c, off)])
                S.hist[:] = 0
                lo = seed - 1500
                cnt = S.launch(lo, 3000, 1.40)
                got = S.cand[:2 * cnt].get().reshape(cnt, 2)
                self.assertGreater(cnt, 0, (gen, variant))
                best = got[np.argmax(got[:, 1] >> 16)]
                combo = int(best[1]) & 0xFF
                self.assertEqual(int(best[0]), seed, (gen, variant, "seed"))
                got_v, got_mp, got_mode, got_m = ST.combo_parts(combo)
                # m and m + 14 differ only where the key is odd and English keeps ~77% of its coincidences under a shift by 14,
                # so on 240 steps the two can swap places; the long verification separates them
                self.assertEqual((got_v, got_mp, got_mode), (variant, mp, mode), (gen, variant, "setting"))
                self.assertIn(got_m, (m, (m + 14) % 28), (gen, variant, "multiplier"))
                self.assertGreater(int(best[1]) >> 16, 1500)

    def test_random_ciphertext_gives_no_candidate(self):
        rng = np.random.default_rng(8)
        c = rng.integers(0, 29, ST.NS)
        for gen in ("py3", "java"):
            S = ST.Step(gen, [("random", 3, c)])
            self.assertEqual(S.launch(5000, 200000, ST.THR), 0, gen)


@unittest.skipUnless(BIN, "needs the Rust build (cargo build --release in work/phpmt)")
class Verify(unittest.TestCase):
    def test_a_planted_seed_keeps_its_ioc_beyond_the_window_and_a_wrong_seed_does_not(self):
        from unittest import mock
        import attack
        import lp
        import step_verify as SV
        rng = np.random.default_rng(9)
        seed = 424242
        toks = attack.synthetic_tokens(1500, start=7000)
        p = np.array(lp.runes_of(toks))[:1000]
        p = np.where(p == 14, 6, p)
        q = np.where(p > 14, p - 1, p)
        key = _long("py3", seed, 28, 1200)[1]
        c, prev = step28.encrypt(q, key, "A", "keep", 5, 0, rng.random(len(q)) < 0.0066, prev=3)
        # stand-ins for section 0.8 (its last rune is the previous rune) and section 0.9 (the ciphertext)
        with mock.patch.object(SV.lp, "runes_of", side_effect=lambda t: list(t)),                 mock.patch.object(SV.stats, "SEGS", {8: [3], 9: [int(x) for x in c]}),                 mock.patch.object(SV, "rust_keys", side_effect=_long):
            w, beyond, n = SV.verify("py3", seed, "sec0.9@0", "A", 1, "keep", 5)
            w2, beyond2, n2 = SV.verify("py3", seed + 1, "sec0.9@0", "A", 1, "keep", 5)
        self.assertGreater(w, 1.5)
        self.assertGreater(beyond, 1.5)
        self.assertLess(beyond2, 1.25)


def _long(gen, seed, km, count):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "k.txt")
        subprocess.run([BIN, "keysn", gen, str(seed), str(seed + 1), out, str(km), str(count)], check=True, capture_output=True)
        v = [int(x) for x in open(out).read().split()]
    return [np.array(v[1:1 + count]), np.array(v[1 + count:])]


if __name__ == "__main__":
    unittest.main()
