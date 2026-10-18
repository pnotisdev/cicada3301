"""Checks for the H5 power map (run from work/h5power: python -m unittest test_h5power)."""
import os
import random
import subprocess
import tempfile
import unittest

import h5power as H

PLAIN = H.M.english_pool(0.6, 0.601)[:300]


class Planter(unittest.TestCase):
    def test_no_redraw_gives_composite_key_decode(self):
        rng = random.Random(1)
        t = bytes(rng.randrange(29) for _ in range(H.STREAM_LEN))
        w = [rng.randrange(29) for _ in range(5)]
        out = H.plant(PLAIN, t, 40, w, 0, rng, keep=1.0)      # keep = 1: collisions are never redrawn
        dec = [(c - (t[40 + i] + w[i % 5])) % 29 for i, c in enumerate(out)]
        self.assertEqual(dec, PLAIN)

    def test_redraw_removes_most_doublets(self):
        rng = random.Random(2)
        d = n = 0
        for _ in range(100):
            t = bytes(rng.randrange(29) for _ in range(H.STREAM_LEN))
            out = H.plant(PLAIN, t, 0, [rng.randrange(29) for _ in range(7)], 0, rng, keep=0.0)
            d += sum(a == b for a, b in zip(out, out[1:]))
            n += len(out) - 1
        self.assertLess(d / n, 0.0005)


@unittest.skipUnless(os.path.exists(H.BIN), "h5rs is not built")
class EngineSmoke(unittest.TestCase):
    def test_engine_recovers_a_short_keyword_plant_at_its_true_cell(self):
        hits = 0
        for seed in range(6):
            with tempfile.TemporaryDirectory() as d:
                rec = H.one(("t", 2, 0, "iid", "english", seed, d))
                hits += (rec["true_ioc"] or 0) >= 1.6
        self.assertGreaterEqual(hits, 3)                        # recall at L=2, skip, is about 94%: 3 of 6 is a very loose floor


if __name__ == "__main__":
    unittest.main()
