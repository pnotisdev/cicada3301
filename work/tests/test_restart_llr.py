"""LLR restart test: a planted per-unit key restart is detected, a continuous key is not."""
import os
import random
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import restart_columns as rc  # noqa: E402
import restart_llr as rl  # noqa: E402
import sim  # noqa: E402


class RestartLLR(unittest.TestCase):
    def setUp(self):
        rl.MC = 300
        self.eng = sim.english_runes()
        self.rng = np.random.default_rng(1)

    @staticmethod
    def freq(units):
        allr = np.array([x for u in units for x in u])
        return np.bincount(allr, minlength=rc.N) / len(allr)

    def test_planted_restart_detected(self):
        units = rc.simulate_units([260] * 40, True, self.eng, random.Random(1), start=3000)
        z = rl.column_z(units, self.freq(units), self.rng, nj=24)
        self.assertGreater(rl.summ(z)[1], 8.0)

    def test_continuous_key_not_flagged(self):
        units = rc.simulate_units([260] * 40, False, self.eng, random.Random(2), start=3000)
        z = rl.column_z(units, self.freq(units), self.rng, nj=24)
        self.assertLess(abs(rl.summ(z)[1]), 3.5)


if __name__ == "__main__":
    unittest.main()
