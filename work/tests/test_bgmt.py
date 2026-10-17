"""Boundary-free seed sweep (work/phpmt/bg.py + bgmt.cu): gates of docs/GPU_PORT.md.
  (a) the generator section of bgmt.cu is the text of phpmt.cu's (so the validated key maps are the ones used);
  (b) every score of every variant equals the Python reference `ref_decode` run on the Rust engine's key values;
  (c) a planted seed (English enciphered under a known seed, variant and skip/coin model) is recovered at rank 1, for every generator;
  (d) random ciphertext gives no candidate;
  (e) the score does not depend on word separators (there are none in its input) -- LP2's separators imposed on English plaintext leave a planted seed
      as visible as with the English words' own (the dictionary score drops from 33 to 0 there: work/log/phase9_boundaries.md)."""
import os
import subprocess
import sys
import tempfile
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(WORK, "phpmt"))
sys.path.insert(0, WORK)

import make_bgmt  # noqa: E402

try:
    import cupy  # noqa: F401
    import bg
    CUDA = True
except Exception:  # noqa: BLE001
    CUDA = False

PH = os.path.join(WORK, "phpmt")
_EXE = "phpmt.exe" if os.name == "nt" else "phpmt"
_CAND = [p for p in (os.path.join(PH, "target", "release", _EXE), os.path.join(PH, "target_gen", "release", _EXE)) if os.path.exists(p)]
BIN = max(_CAND, key=os.path.getmtime) if _CAND else None
GENS = ["php", "glibc", "net", "py3", "mt32", "mt31", "java", "msvc", "drand48", "ruby"]
K = 160


def rust_keys(gen, lo, hi):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "k.txt")
        subprocess.run([BIN, "keys", gen, str(lo), str(hi), out], check=True, capture_output=True)
        res = {}
        with open(out) as f:
            for line in f:
                v = [int(x) for x in line.split()]
                res[v[0]] = [np.array(v[1:1 + K]), np.array(v[1 + K:])]
    return res


def planted_window(gen, seed, mp, model, sign, atb, d):
    """the first 120 runes of English enciphered by the Rust `plant` mode (the L line is irrelevant here)"""
    out = os.path.join(d, "planted.txt")
    subprocess.run([BIN, "plant", gen, os.path.join(PH, "data", "english.txt"), str(seed), str(mp), str(model), str(sign), str(atb), "0.18", out],
                   cwd=PH, check=True, capture_output=True)
    with open(out) as f:
        lines = f.read().splitlines()
    prev = int(lines[0].split()[2])
    runes = np.array([int(x) for x in lines[1][2:].split()][:bg.NR])
    return ("plant", prev, runes)


class Sections(unittest.TestCase):
    def test_generator_section_is_phpmts(self):
        with open(os.path.join(PH, "bgmt.cu"), encoding="utf-8") as f:
            a = f.read()
        with open(os.path.join(PH, "phpmt.cu"), encoding="utf-8") as f:
            b = f.read()
        self.assertEqual(make_bgmt.generator_section(a), make_bgmt.generator_section(b))
        self.assertEqual(a, make_bgmt.build(), "bgmt.cu is stale: run work/phpmt/make_bgmt.py")


@unittest.skipUnless(CUDA and BIN, "needs CuPy and the Rust build")
class BgSweep(unittest.TestCase):
    def test_scores_equal_the_python_reference(self):
        tbl = bg.load_table()
        wins = bg.make_windows("all")[:2]
        for gen in GENS:
            S = bg.Sweep(gen, wins, dump=1)
            lo, hi = 3000, 3004
            keys = rust_keys(gen, lo, hi)
            gpu = S.scores(lo, hi - lo)
            for g, seed in enumerate(range(lo, hi)):
                for wi, (_, prev, runes) in enumerate(wins):
                    for v in range(16):
                        model, mp, sign, atb = bg.variant_parts(v)
                        ref, _ = bg.ref_decode(runes, prev, keys[seed][mp], sign, bool(atb), model, tbl, bg.ABORT_AT, bg.ABORT_THR)
                        self.assertEqual(int(gpu[g, wi, v]), ref, (gen, seed, wi, v))

    def test_planted_seed_is_recovered_for_every_generator(self):
        cases = [("php", 777777, 0, 1, 1, 0), ("glibc", 424242, 1, 1, -1, 1), ("net", 31337, 0, 0, 1, 0), ("py3", 123456, 0, 1, 1, 0),
                 ("mt32", 54321, 0, 1, 1, 1), ("mt31", 222222, 1, 0, 1, 0), ("java", 42424, 0, 1, -1, 0), ("msvc", 5555, 1, 1, 1, 1),
                 ("drand48", 160000, 0, 0, 1, 0), ("ruby", 313131, 1, 1, -1, 0)]
        for gen, seed, mp, model, sign, atb in cases:
            with tempfile.TemporaryDirectory() as d:
                win = planted_window(gen, seed, mp, model, sign, atb, d)
            S = bg.Sweep(gen, [win])
            cnt = S.launch(max(0, seed - 2000), 4000, 150)
            got = S.cand[:2 * cnt].get().reshape(cnt, 2)
            self.assertGreater(cnt, 0, gen)
            best = got[np.argmax(got[:, 1] >> 16)]
            self.assertEqual(int(best[0]), seed, gen)
            self.assertGreater((int(best[1]) >> 16) - 2048, bg.THR, gen)
            others = [(int(x[1]) >> 16) - 2048 for x in got if int(x[0]) != seed]
            self.assertLess(max(others or [-999]), 150, gen)

    def test_random_ciphertext_gives_no_candidate(self):
        rng = np.random.default_rng(4)
        win = ("random", 3, rng.integers(0, 29, bg.NR))
        for gen in ("py3", "java", "php"):
            S = bg.Sweep(gen, [win])
            self.assertEqual(S.launch(100000, 300000, bg.THR), 0, gen)

    def test_separators_do_not_matter(self):
        """the dictionary score of phpmt cannot see a planted seed once LP2's word separators replace the English words' own; this one has none"""
        with tempfile.TemporaryDirectory() as d:
            win = planted_window("php", 777777, 0, 1, 1, 0, d)
        S = bg.Sweep("php", [win])
        cnt = S.launch(776000, 2000, bg.THR)
        got = S.cand[:2 * cnt].get().reshape(cnt, 2)
        self.assertIn(777777, [int(x[0]) for x in got])


if __name__ == "__main__":
    unittest.main()
