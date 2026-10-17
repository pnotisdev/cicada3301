"""Step-domain chain screen (work/kscreen/step28.py) and its periodicity scan (work/step_periodicity.py)."""
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, WORK)
sys.path.insert(0, os.path.join(WORK, "kscreen"))

import step28 as S  # noqa: E402
import step_periodicity as SP  # noqa: E402

try:
    import cupy  # noqa: F401
    CUDA = True
except Exception:  # noqa: BLE001
    CUDA = False


def random_streams(rng, count, length):
    return [(f"R{i}", rng.integers(0, S.Q, length, dtype=np.int64).astype(np.uint8)) for i in range(count)]


class Model(unittest.TestCase):
    def test_encrypt_then_decode_with_the_key_gives_the_plaintext(self):
        """independent of the screen: subtract the key from the step classes and get the plaintext back exactly"""
        rng = np.random.default_rng(1)
        for variant in ("A", "B", "C"):
            for mode in ("drop", "keep"):
                key = S.key_arrays([("k", rng.integers(0, S.Q, 400, dtype=np.int64))], variant)[0][1]
                q = rng.integers(0, 28, 200)
                ditto = rng.random(200) < 0.05
                c, prev = S.encrypt(q, key, variant, mode, 5, 17, ditto)
                J = S.step_classes(c, prev, variant)
                self.assertTrue(((J == 255) == ditto).all())
                idx = S.key_index(J, mode)
                dec = (J[~ditto] - 5 * key[17 + idx[~ditto]]) % 28
                self.assertTrue((dec == q[~ditto]).all(), (variant, mode))

    def test_windows_tile_the_sections(self):
        w = S.windows_of(300)
        self.assertEqual(len({n for n, _, _ in w}), len(w))
        self.assertTrue(all(len(r) == 300 for _, _, r in w))


class Screen(unittest.TestCase):
    def test_planted_keys_are_recovered_and_the_other_variant_is_blind(self):
        rng = np.random.default_rng(2)
        for variant, mode, m in (("A", "drop", 3), ("A", "keep", 1), ("B", "drop", 5), ("B", "keep", 11), ("C", "drop", 13), ("C", "keep", 9)):
            streams, w, (sname, o0) = S.plant_case(rng, variant, mode, m)
            rows = S.screen(streams, [("p", w[1], w[2])], "cpu", variants=(variant,), modes=(mode,))
            top = max(rows, key=lambda r: r[4])
            self.assertEqual((top[3], top[5], top[6]), (m, sname, o0), (variant, mode))
            self.assertGreater(top[4], 1.5)
            other = "B" if variant != "B" else "A"
            blind = S.screen(streams, [("p", w[1], w[2])], "cpu", variants=(other,), modes=(mode,))
            self.assertLess(max(r[4] for r in blind), 1.3)

    def test_random_keys_stay_near_one(self):
        rng = np.random.default_rng(3)
        rows = S.screen(random_streams(rng, 8, 1200), S.windows_of(300)[:3], "cpu", variants=("A",), modes=("drop",))
        self.assertLess(max(r[4] for r in rows), 1.25)

    @unittest.skipUnless(CUDA, "CuPy not installed")
    def test_cuda_equals_cpu(self):
        rng = np.random.default_rng(4)
        lib, wins = random_streams(rng, 6, 1500), S.windows_of(300)[:2]
        cpu = S.screen(lib, wins, "cpu", variants=("A", "B"), modes=("drop", "keep"))
        gpu = S.screen(lib, wins, "cuda", variants=("A", "B"), modes=("drop", "keep"))
        for x, y in zip(cpu, gpu):
            self.assertEqual((x[:4], round(x[4], 6), x[5], x[6]), (y[:4], round(y[4], 6), y[5], y[6]))


class Periodicity(unittest.TestCase):
    def test_planted_period_is_found_and_random_is_not(self):
        rng = np.random.default_rng(5)
        for variant, mode in (("A", "drop"), ("B", "keep"), ("C", "keep")):
            c, prev = SP.planted(rng, variant, mode, 211)
            lags, z = SP.scan(SP.classes(c, prev, variant, mode))
            k = int(np.argmax(z))
            self.assertEqual(int(lags[k]) % 211, 0)
            self.assertGreater(z[k], 5.5)
        c = rng.integers(0, S.Q, 3000)
        self.assertLess(SP.scan(SP.classes(c, 3, "A", "keep"))[1].max(), 5.5)


if __name__ == "__main__":
    unittest.main()
