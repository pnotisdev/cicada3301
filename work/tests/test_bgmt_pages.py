"""Gate for the per-page seed sweeps (work/phpmt/bg.py sweep <gen> pages ...): the same engine as test_bgmt with the 44 page windows. A fresh seed per page is only tested if (1) the window set is what it claims,
(2) a planted seed is recovered among the page windows with every other window silent, (3) random ciphertext gives no candidate. Skipped without a CUDA device (CuPy)."""
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, WORK)
sys.path.insert(0, os.path.join(WORK, "phpmt"))
sys.path.insert(0, HERE)

try:
    import cupy as cp
    HAVE = cp.cuda.runtime.getDeviceCount() > 0
except Exception:  # noqa: BLE001
    HAVE = False

if HAVE:
    import bg
    import test_bgmt as T


@unittest.skipUnless(HAVE, "needs a CUDA device with cupy-cuda12x")
class Pages(unittest.TestCase):
    def test_page_windows_are_what_they_claim(self):
        wins = bg.make_windows("pages")
        self.assertGreaterEqual(len(wins), 40)
        self.assertEqual(len({w[0] for w in wins}), len(wins))
        self.assertTrue(all(len(w[2]) == bg.NR and w[0].startswith("page_0.") and not w[0].endswith("@0") for w in wins))

    def test_planted_seed_is_recovered_among_the_page_windows(self):
        import tempfile
        pages = bg.make_windows("pages")
        for gen, seed, mp, model, sign, atb in (("php", 777777, 0, 1, 1, 0), ("py3", 123456, 0, 1, 1, 0), ("java", 42424, 0, 1, -1, 0), ("glibc", 424242, 1, 1, -1, 1)):
            with tempfile.TemporaryDirectory() as d:
                plant = T.planted_window(gen, seed, mp, model, sign, atb, d)
            S = bg.Sweep(gen, pages + [plant])
            cnt = S.launch(max(0, seed - 2000), 4000, 150)
            got = S.cand[:2 * cnt].get().reshape(cnt, 2)
            self.assertGreater(cnt, 0, gen)
            win = (got[:, 1].astype(np.int64) >> 8) & 0xFF
            score = (got[:, 1].astype(np.int64) >> 16) - 2048
            best = int(np.argmax(score))
            self.assertEqual((int(got[best, 0]), int(win[best])), (seed, len(pages)), gen)
            self.assertGreater(int(score[best]), bg.THR, gen)
            others = [int(s) for s, w in zip(score, win) if w != len(pages)]
            self.assertLess(max(others or [-999]), 150, gen)

    def test_random_ciphertext_gives_no_candidate(self):
        pages = bg.make_windows("pages")
        rng = np.random.default_rng(9)
        rnd = [(f"random{i}", int(rng.integers(0, 29)), rng.integers(0, 29, bg.NR)) for i in range(len(pages))]
        for gen in ("py3", "java", "php"):
            self.assertEqual(bg.Sweep(gen, rnd).launch(100000, 300000, bg.THR), 0, gen)


if __name__ == "__main__":
    unittest.main()
