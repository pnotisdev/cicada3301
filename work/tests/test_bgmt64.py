"""64-bit seeds for the boundary-free GPU sweep (work/phpmt/bg64.py + bgmt64.cu): the gates of docs/GPU_PORT.md for the `prng-time` port.
  (a) bgmt64.cu is exactly what make_bgmt64.py builds from bgmt.cu (the validated source);
  (b) the kernel's key values equal INDEPENDENT references (CPython's random module, java.util.Random written from its specification: ref_keys64.py) for seeds
      below and above 2^32, at the boundaries (2^31, 2^32 - 1, 2^32, 2^33, 2^40 + 12345, 2^48 - 1) and for random millisecond timestamps of 2012-2014;
  (c) below 2^32 the keys and every decode score equal those of the validated 32-bit kernel (bgmt.cu);
  (d) above 2^32 every score of every variant equals the Python reference decoder run on the independent keys;
  (e) planted timestamp seeds (English enciphered under a known seed, map, variant and rule, by the independent planter) are recovered at rank 1, including a
      chunk that straddles 2^32 (the kernel records the low 32 bits of a seed; bg64.sweep restores the rest);
  (f) random ciphertext gives no candidate; (g) the whole-section check with independent keys confirms a plant and rejects a wrong seed."""
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
PH = os.path.join(WORK, "phpmt")
sys.path.insert(0, PH)
sys.path.insert(0, WORK)

import make_bgmt64  # noqa: E402
import ref_keys64  # noqa: E402

try:
    import cupy  # noqa: F401
    import bg
    import bg64
    CUDA = True
except Exception:  # noqa: BLE001
    CUDA = False

K = 160
BOUNDARY = [0, 1, 3301, 2 ** 31, 2 ** 32 - 1, 2 ** 32, 2 ** 32 + 1, 2 ** 33 - 1, 2 ** 33, 1325376000000, 1388534412345, 1391212800000, 2 ** 40 + 12345, 2 ** 41, 2 ** 48 - 1]
GENS = ["py3", "ruby", "java", "java-abs"]
WINDOW0 = None


class Build(unittest.TestCase):
    def test_kernel_is_built_from_bgmt(self):
        with open(os.path.join(PH, "bgmt64.cu"), encoding="utf-8") as f:
            self.assertEqual(f.read(), make_bgmt64.build(), "bgmt64.cu is stale: run work/phpmt/make_bgmt64.py")

    def test_reference_generators_match_published_values(self):
        j = ref_keys64.JavaRandom
        self.assertEqual([j(42).next_int(), j(0).next_int()], [-1170105035, -1155484576])            # published java.util.Random values
        self.assertEqual(j(42).next_int(), j(42).next(32))
        a, b = ref_keys64.keys("py3", 2 ** 32, 8), ref_keys64.keys("py3", 0, 8)
        self.assertNotEqual(list(a[0]), list(b[0]))                                                  # a second word changes the stream


@unittest.skipUnless(CUDA, "needs CuPy (python -m pip install -r requirements-gpu.txt)")
class Gpu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wins = bg.make_windows("07")
        cls.tbl = bg.load_table()
        cls.rng = np.random.default_rng(64)

    def test_keys_equal_independent_references(self):
        stamps = [int(x) for x in self.rng.integers(1325376000000, 1391212800000, 25)]
        for gen in GENS:
            S = bg64.Sweep64(gen, self.wins, dump=3)
            for seed in BOUNDARY + stamps:
                got = S.keys(seed, 1)[0]
                ref = ref_keys64.keys(gen, seed, K)
                for m in (0, 1):
                    self.assertEqual(list(got[m]), [int(x) for x in ref[m]], (gen, seed, m))

    def test_below_2_32_equals_the_32_bit_kernel(self):
        seeds = list(range(3000, 3006)) + [2 ** 31 - 1, 2 ** 31, 2 ** 32 - 2]
        for gen in ("py3", "ruby", "java"):
            S64, S32 = bg64.Sweep64(gen, self.wins, dump=1), bg.Sweep(gen, self.wins, dump=1)
            for seed in seeds:
                self.assertEqual(S64.scores(seed, 1).tolist(), S32.scores(seed, 1).tolist(), (gen, seed))
            K64, K32 = bg64.Sweep64(gen, self.wins, dump=3), bg.Sweep(gen, self.wins, dump=3)
            for seed in seeds:
                d = self.cp_zeros(2 * K)
                K32.launch(seed, 1, 1 << 30, d)
                self.assertEqual(K64.keys(seed, 1)[0].tolist(), d.get().reshape(2, K).tolist(), (gen, seed))

    @staticmethod
    def cp_zeros(n):
        import cupy
        return cupy.zeros(n, cupy.int32)

    def test_scores_equal_the_python_reference_above_2_32(self):
        _, prev, runes = self.wins[0]
        for gen in GENS:
            S = bg64.Sweep64(gen, self.wins, dump=1)
            for seed in (2 ** 32 + 5, 1388534412345, 2 ** 40 + 1):
                gpu = S.scores(seed, 1)[0, 0]
                keys = ref_keys64.keys(gen, seed, K)
                for v in range(16):
                    model, mp, sign, atb = bg.variant_parts(v)
                    ref, _ = bg.ref_decode(runes, prev, keys[mp], sign, bool(atb), model, self.tbl, bg.ABORT_AT, bg.ABORT_THR)
                    self.assertEqual(int(gpu[v]), ref, (gen, seed, v))

    def test_planted_timestamp_seeds_recovered(self):
        cases = [("py3", 1389052800777, 0, 1, -1, 0), ("py3", 1325400000123, 1, 0, 1, 1), ("ruby", 1360000000999, 0, 0, 1, 0), ("java", 1388534412345, 0, 1, 1, 0),
                 ("java", 1370000004242, 1, 0, -1, 1), ("java-abs", 1391212799999, 1, 0, 1, 0), ("py3", 2 ** 32 + 1234, 0, 0, 1, 0)]
        for gen, seed, mp, model, sign, atb in cases:
            win = ("plant", -1, ref_keys64.plant(gen, seed, mp, model, sign, atb))
            # a chunk of 6,000 seeds centred on the plant; the last case straddles 2^32 (low 32 bits wrap inside the chunk)
            lo = seed - 3000
            rows, _ = bg64.sweep(gen, None, lo, lo + 6000, os.devnull, thr=150, wins=[win], quiet=True)
            self.assertTrue(rows, gen)
            top = rows[0].split("\t")
            self.assertEqual(int(top[1]), seed, (gen, seed))
            self.assertEqual([int(x) for x in top[4:7]], [mp, sign, atb], (gen, seed))
            self.assertGreater(int(top[0]), bg.THR, (gen, seed))
            others = [int(r.split("\t")[0]) for r in rows if int(r.split("\t")[1]) != seed]
            self.assertLess(max(others or [-999]), 150, (gen, seed))

    def test_random_ciphertext_gives_no_candidate(self):
        win = ("random", 3, self.rng.integers(0, 29, bg.NR))
        for gen in GENS:
            S = bg64.Sweep64(gen, [win])
            self.assertEqual(S.launch(1388534400000, 300000, bg.THR), 0, gen)
            self.assertEqual(S.launch(2 ** 32 - 150000, 300000, bg.THR), 0, gen)

    def test_whole_section_check_confirms_plant_and_rejects_a_wrong_seed(self):
        seed = 1388534412345
        plant = ref_keys64.plant("java", seed, 0, 1, 1, 0)
        win = ("plant", -1, plant)
        rows, _ = bg64.sweep("java", None, seed - 500, seed + 500, os.devnull, thr=150, wins=[win], quiet=True)
        top = rows[0].split("\t")
        lines = [rows[0], "\t".join([top[0], str(seed + 1)] + top[2:])]
        out = []
        n = bg64.verify(lines, "java", top=2, controls=4, plant=(-1, plant), out=out.append)
        self.assertEqual(n, 1)
        self.assertTrue(out[0].startswith("CANDIDATE") and f"java seed {seed}	" in out[0], out)
        self.assertTrue(out[1].startswith("noise") and f"java seed {seed + 1}	" in out[1], out)


if __name__ == "__main__":
    unittest.main()
