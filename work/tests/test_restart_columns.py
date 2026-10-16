"""Key-restart column test (work/restart_columns.py): calibration of the statistic, unit extraction, and detection of a
planted per-unit key restart (forward and backward) against a continuous key."""
import os
import random
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import lp  # noqa: E402
import restart_columns as rc  # noqa: E402
import sim  # noqa: E402
import stats  # noqa: E402


def pool_freq(units):
    allr = np.array([x for u in units for x in u])
    return np.bincount(allr, minlength=rc.N) / len(allr)


class Calibration(unittest.TestCase):
    def test_z_is_standard_normal_under_the_null(self):
        # column 0 only (units of length 1): X = equal pairs among n iid runes drawn from a lumpy distribution.
        # The exact multinomial variance must give mean 0 and sd 1; a naive binomial variance would not.
        rng = np.random.default_rng(7)
        f = rng.dirichlet(np.ones(rc.N) * 0.7)
        for n in (40, 300):
            zs = [rc.column_stats([[int(x)] for x in rng.choice(rc.N, size=n, p=f)], f, nj=1)[0][0] for _ in range(2500)]
            self.assertAlmostEqual(float(np.mean(zs)), 0.0, delta=0.08, msg=f"n={n}")
            self.assertAlmostEqual(float(np.std(zs)), 1.0, delta=0.07, msg=f"n={n}")


class Units(unittest.TestCase):
    def test_every_kind_partitions_the_runes(self):
        idxs = list(stats.UNSOLVED)
        total = sum(len(lp.runes_of(stats.SEGS[i])) for i in idxs)
        for kind in ("segment", "page", "paragraph", "line", "sentence", "word"):
            units = rc.units_of(kind, stats.SEGS, idxs)
            self.assertEqual(sum(map(len, units)), total, kind)
            self.assertTrue(all(len(u) > 0 for u in units), kind)

    def test_words_are_the_toolkits_words(self):
        # wrapped words must stay whole: the units equal lp.word_spans, segment by segment
        for i in stats.UNSOLVED:
            want = [b - a for _, a, b in lp.word_spans(stats.SEGS[i], lp.runes_of(stats.SEGS[i]))]
            got = [len(u) for u in rc.units_of("word", stats.SEGS, [i])]
            self.assertEqual(got, want, f"segment {i}")

    def test_lines_are_finer_than_paragraphs(self):
        idxs = list(stats.UNSOLVED)
        n = {k: len(rc.units_of(k, stats.SEGS, idxs)) for k in ("segment", "page", "paragraph", "line", "word")}
        self.assertLess(n["segment"], n["page"])
        self.assertLess(n["page"], n["paragraph"])
        self.assertLess(n["paragraph"], n["line"])
        self.assertLess(n["line"], n["word"])


class Detection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.eng = sim.english_runes()
        cls.lengths = [260] * 50

    def zsum(self, restart, backward, reverse, seed):
        units = rc.simulate_units(self.lengths, restart, self.eng, random.Random(seed), start=3000 + 7000 * seed,
                                  backward=backward)
        z, _ = rc.column_stats(units, pool_freq(units), reverse=reverse)
        return rc.summarize(z)

    def test_planted_forward_restart_is_found_and_continuous_key_is_not(self):
        planted = [self.zsum(True, False, False, s)[1] for s in range(3)]
        null = [self.zsum(False, False, False, s) for s in range(3)]
        self.assertGreater(min(planted), 10.0)
        self.assertLess(max(abs(n[1]) for n in null), 3.5)
        self.assertLess(max(n[0] for n in null), 4.5)

    def test_backward_restart_needs_the_backward_reading(self):
        # a key that runs backwards from each unit's end lines up the unit ENDS, not the starts
        right = self.zsum(True, True, True, 1)[1]
        wrong = self.zsum(True, True, False, 1)[1]
        self.assertGreater(right, 10.0)
        self.assertLess(abs(wrong), 3.5)


if __name__ == "__main__":
    unittest.main()
