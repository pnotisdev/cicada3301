"""Key-restart column test: a planted per-unit restart is detected, a continuous key is not."""
import os
import random
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import restart_columns as rc  # noqa: E402
import sim  # noqa: E402


class RestartColumns(unittest.TestCase):
    def setUp(self):
        self.eng = sim.english_runes()
        self.lengths = [260] * 50

    @staticmethod
    def pool_freq(units):
        allr = np.array([x for u in units for x in u])
        return np.bincount(allr, minlength=rc.N) / len(allr)

    def test_planted_restart_detected(self):
        units = rc.simulate_units(self.lengths, True, self.eng, random.Random(1), start=3000)
        z, _ = rc.column_stats(units, self.pool_freq(units))
        self.assertGreater(rc.summarize(z)[1], 8.0)

    def test_continuous_key_not_flagged(self):
        units = rc.simulate_units(self.lengths, False, self.eng, random.Random(2), start=3000)
        z, _ = rc.column_stats(units, self.pool_freq(units))
        self.assertLess(rc.summarize(z)[0], 4.5)
        self.assertLess(abs(rc.summarize(z)[1]), 3.5)


if __name__ == "__main__":
    unittest.main()
