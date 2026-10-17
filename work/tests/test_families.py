"""Family simulations (work/families): the fingerprint reproduces the project's own counts for the real LP2, every simulator leaves its known mark on the statistic
meant to catch it (positive controls), the avoid-repeat rule does what it says, and a nearest-centroid classifier recovers planted families."""
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(WORK, "families"))
sys.path.insert(0, WORK)

import fam_data as D  # noqa: E402
import fam_fingerprint as F  # noqa: E402
import fam_sims as S  # noqa: E402

HAVE = os.path.exists(os.path.join(WORK, "ref", "corpora", "pg205.txt")) and os.path.exists(os.path.join(WORK, "ref", "emerson_essays1.txt"))


@unittest.skipUnless(HAVE, "needs the Gutenberg texts in work/ref/corpora (python scripts/fetch_data.py)")
class Families(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real = D.lp2()
        cls.eng = D.english(120_000)
        cls.rng = np.random.default_rng(4)
        runes, start, sid = cls.real
        cls.sec = np.append(True, sid[1:] != sid[:-1])

    def sim(self, fn, R=8, **k):
        runes, start, sid = self.real
        P, st = D.windows(self.eng, len(runes), R, self.rng, False, start, self.sec)
        return F.many(fn(P, st, self.rng, **k), st, sid)

    def col(self, X, name):
        return X[:, F.NAMES.index(name)]

    def test_real_fingerprint_reproduces_the_project_counts(self):
        runes, start, sid = self.real
        # words as lp.word_spans cuts them since 2026-10-17 (bare page breaks are wraps): 2,896 words, not 2,928
        self.assertEqual((len(runes), int(start.sum())), (12956, 2896))
        fp = F.fingerprint(runes, start, sid)
        self.assertAlmostEqual(fp["dbl_in"], 100 * 63 / 10060, places=3)            # within_word.txt: 63 doublets in 10,060 adjacent in-word pairs
        self.assertAlmostEqual(fp["z5"], 3.73, delta=0.1)                           # 104 equal of 2,105 at lag 5 (z +3.7)
        self.assertAlmostEqual(fp["ioc"], 1.0, delta=0.01)

    def test_each_simulator_leaves_its_mark(self):
        X = {name: self.sim(f, **p) for name, f, p in (("random", S.random_, {}), ("plain", S.plain, {}), ("vig", S.vigenere, {"L": 11}), ("cta", S.ctauto, {"m": 5}),
                                                        ("wk", S.wordkey, {}), ("aw", S.alphawalk, {"period": 5, "q": 0.0}), ("aw4", S.alphawalk, {"period": 4, "q": 0.0}))}
        self.assertLess(self.col(X["random"], "ioc").max(), 1.03)
        self.assertGreater(self.col(X["plain"], "ioc").min(), 1.5)                  # English leaks into the IoC
        self.assertGreater(self.col(X["vig"], "lagz").min(), 6)                     # period 11 shows at lag 11
        self.assertLess(self.col(X["random"], "lagz").max(), 4.5)
        self.assertGreater(self.col(X["cta"], "dioc").min(), 1.4)                   # a ciphertext autokey leaks in the lag-5 differences
        self.assertGreater(self.col(X["wk"], "first").min(), 1.4)                   # a per-word key leaks in the word-initial runes
        self.assertGreater(self.col(X["aw"], "z5").mean(), 4.0)                      # period-5 alphabets: lag-5 coincidences ...
        self.assertLess(self.col(X["aw"], "zoth").mean(), 2.5)                       # ... and the neighbouring lags stay at chance
        self.assertGreater(self.col(X["aw4"], "zoth").mean(), 4.5)                   # period 4: the excess moves to lag 4 (counted in zoth)

    def test_avoid_repeat_rule(self):
        self.assertEqual(self.col(self.sim(S.runkey, q=1.0), "dbl_in").max(), 0.0)
        self.assertEqual(self.col(self.sim(S.runkey, q=1.0), "dbl_seam").max(), 0.0)
        d = self.col(self.sim(S.runkey, q=0.0), "dbl_in")
        self.assertTrue(3.0 < d.mean() < 4.0)                                       # 1/29 = 3.45%
        d = self.col(self.sim(S.runkey, q=0.81), "dbl_in")
        self.assertTrue(0.4 < d.mean() < 0.9)                                       # (1 - q) / 29 = 0.66%

    def test_alphawalk_skip_probability_does_not_depend_on_the_number_of_replicates(self):
        for R in (3, 100):
            d = self.col(self.sim(S.alphawalk, R=R, period=5, q=0.81), "dbl_in").mean()
            self.assertTrue(0.35 < d < 1.0, (R, d))                                 # (1 - q) / 29 = 0.66%
        self.assertEqual(self.col(self.sim(S.alphawalk, R=6, period=5, q=1.0), "dbl_in").max(), 0.0)

    def test_classifier_recovers_planted_families(self):
        rows = [("runkey", S.runkey, {"q": 0.81}), ("vig", S.vigenere, {"L": 11}), ("aw", S.alphawalk, {"period": 5, "q": 0.81}), ("cta", S.ctauto, {"m": 1}), ("plain", S.plain, {})]
        M = {n: self.sim(f, R=12, **p) for n, f, p in rows}
        sd = np.sqrt(np.mean([m.var(0) for m in M.values()], axis=0)) + 1e-9
        cent = {n: m[:6].mean(0) / sd for n, m in M.items()}
        names = list(cent)
        C = np.array([cent[n] for n in names])
        for n, m in M.items():
            pred = [names[int(np.argmin(((C - x / sd) ** 2).sum(1)))] for x in m[6:]]
            self.assertGreaterEqual(np.mean([p == n for p in pred]), 0.8, (n, pred))

    def test_echo_power(self):
        self.assertGreater(np.mean(self.col(self.sim(S.echo, q=0.81, eps=0.03), "z5") >= 3), 0.9)
        self.assertLess(np.mean(self.col(self.sim(S.echo, q=0.81, eps=0.0), "z5") >= 3), 0.3)


if __name__ == "__main__":
    unittest.main()
