"""Phase 4 item 3: crib deductions, key-reuse scans and the constraint solver."""
import os
import random
import sys
import unittest
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import attack  # noqa: E402
import crib  # noqa: E402
import cribsolve as cs  # noqa: E402
import lp  # noqa: E402


class Deductions(unittest.TestCase):
    cw = crib.cipher_words()

    def test_one_rune_words_use_all_runes(self):
        ones = Counter(w[0] for _, _, w in self.cw if len(w) == 1)
        self.assertEqual(sum(ones.values()), 99)  # line-wrapped words rejoined (318 before the fix)
        self.assertEqual(len(ones), 29)

    def test_two_rune_words_look_freshly_keyed(self):
        twos = [w for _, _, w in self.cw if len(w) == 2]
        self.assertGreater(len(set(twos)), 330)  # random key ~357; deterministic word encryption ~27


class Scans(unittest.TestCase):
    def test_lag_scan_detects_planted_period(self):
        R = random.Random(2)
        pt = lp.runes_of(attack.synthetic_tokens(3000, start=8000))
        key = [R.randrange(29) for _ in range(113)]
        ct = [(p + key[i % 113]) % 29 for i, p in enumerate(pt)]
        h, t = crib.lag_scan([ct], 1000)
        z = crib.zscores(h, t)
        z[:2] = -np.inf
        self.assertEqual(int(np.argmax(z)) % 113, 0)

    def test_cross_scan_detects_reused_key(self):
        R = random.Random(3)
        k = [R.randrange(29) for _ in range(2000)]
        a = [(p + k[i + 40]) % 29 for i, p in enumerate(lp.runes_of(attack.synthetic_tokens(800, start=1000)))]
        b = [(p + k[i]) % 29 for i, p in enumerate(lp.runes_of(attack.synthetic_tokens(800, start=9000)))]
        offs, v, ov = crib.cross_scan(a, b)
        z = crib.zscores(v, ov)
        z[ov < 150] = -np.inf
        self.assertEqual(int(offs[np.argmax(z)]), -40)


class Solver(unittest.TestCase):
    def test_periodic_key_recovered(self):
        R = random.Random(37)
        pt = attack.synthetic_tokens(400, start=12000)
        key = [R.randrange(29) for _ in range(31)]
        ct = cs._encrypt(pt, lambda i: key[i % 31])
        prob = cs.periodic_problem(ct, 31)
        res = prob.solve(time_limit=30)
        acc, cov = cs.accuracy(prob, res["assign"], [pt])
        self.assertGreater(acc, 0.95)
        self.assertGreater(cov, 0.95)

    def test_beam_separates_true_and_wrong_period(self):
        R = random.Random(11)
        L = 99
        pt = attack.synthetic_tokens(1200, start=R.randrange(5000, 60000))
        key = [R.randrange(29) for _ in range(L)]
        ct = cs._encrypt(pt, lambda i: key[i % L])
        true_p, wrong_p = cs.periodic_problem(ct, L), cs.periodic_problem(ct, L + 2)
        t, w = true_p.solve_beam(width=100, per_state=20), wrong_p.solve_beam(width=100, per_state=20)
        acc, _ = cs.accuracy(true_p, t["assign"], [pt])
        self.assertGreater(acc, 0.85)
        unexplained = lambda p, r: sum(r["words"].get(x, 0) is None for x in p.linked) / len(p.linked)  # noqa: E731
        self.assertLess(unexplained(true_p, t), 0.2)
        self.assertGreater(unexplained(wrong_p, w), 0.5)

    def test_key_reuse_mostly_recovered(self):
        R = random.Random(5)
        pa, pb = attack.synthetic_tokens(200, start=15000), attack.synthetic_tokens(200, start=25000)
        k = [R.randrange(29) for _ in range(300)]
        prob = cs.depth_problem(cs._encrypt(pa, lambda i: k[i]), cs._encrypt(pb, lambda i: k[i]), 0)
        res = prob.solve_beam(width=100)
        acc, _ = cs.accuracy(prob, res["assign"], [pa, pb])
        self.assertGreater(acc, 0.6)


if __name__ == "__main__":
    unittest.main()
