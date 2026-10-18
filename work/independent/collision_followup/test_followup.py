"""Unexecuted here. Human gate: identities, independent likelihoods and planted wiring."""
from fractions import Fraction as F
import itertools
import math
import unittest

import analysis as A
M = A.M


class FollowupTests(unittest.TestCase):
    def test_split_fixed_disjoint_complete(self):
        self.assertFalse(set(A.TRAIN) & set(A.VALIDATE))
        self.assertEqual(set(A.TRAIN) | set(A.VALIDATE), set(range(7, 16))-{10})

    def test_single_frozen_score_against_direct_kernel(self):
        c = [1, 3, 5, 7, 8, 10, 22, 4, 4, 6, 7, 8, 9, 0, 1, 2]
        local = list(range(8))*2
        for guarded in (False, True):
            rule = dict(lag=6, a=27, b=24, guarded=guarded)
            direct = 0.
            for i, p in enumerate(local):
                if p >= 6:
                    k = M.kernel(c[i-p:i], ((6, 1, F(1)),), guarded=guarded)[c[i]]
                    direct += math.log(float(k/M.baseline_probability(c[i], c[i-1])))
            self.assertAlmostEqual(A.score(c, local, rule), direct, places=10)
        for w in (F(1, 4), F(1, 2), F(3, 4)):
            rule = dict(rule=f"mix_I5_T6_w={w}")
            direct = 0.
            for i, p in enumerate(local):
                if p:
                    k = M.kernel(c[i-p:i], ((5, 0, w), (6, 1, 1-w)))[c[i]]
                    direct += math.log(float(k/M.baseline_probability(c[i], c[i-1])))
            self.assertAlmostEqual(A.score(c, local, rule), direct, places=10)

    def test_float_moments_against_exact_rational(self):
        for q in (F(0), F(81, 100), F(1)):
            exact = M.moments(9, ((6, 1, F(1)),), q)
            actual = A.float_moments(9, float(q))
            for key in exact:
                for x, y in zip(exact[key], actual[key]):
                    self.assertAlmostEqual(float(x), float(y), places=12)

    def test_section_q_own_doublets(self):
        section = dict(word_lengths=[8, 9, 2], length=19)
        q = .72
        mu, ds = A.section_mean(section, q)
        fitted, predicted, actual_ds = A.fit_section(section, ds)
        self.assertAlmostEqual(fitted, q, places=6)
        self.assertAlmostEqual(mu, predicted, places=6)
        self.assertAlmostEqual(ds, actual_ds, places=6)
        self.assertAlmostEqual(A.section_mean(section, 0)[0], 5/29, places=12)

    def test_heterogeneity_positive_and_null_wiring(self):
        null = [dict(observed=10, expected=10), dict(observed=10, expected=10)]
        plant = [dict(observed=0, expected=10), dict(observed=20, expected=10)]
        self.assertEqual(A.heterogeneity(null), (0, 0))
        self.assertGreater(A.heterogeneity(plant)[0], 10)

    def test_binomial_against_enumeration(self):
        p = F(2, 5)
        dist = [F(0)]*5
        for bits in itertools.product((0, 1), repeat=4):
            k = sum(bits)
            dist[k] += p**k*(1-p)**(4-k)
        self.assertEqual(A.binomial(4, p), dist)
        self.assertEqual(A.convolve(A.binomial(2, p), A.binomial(2, p)), dist)

    def test_exact_power_null_and_planted_oracle(self):
        null = A.exact_power(8, 3, F(1, 4), F(1, 4))
        self.assertEqual(null["size"], F(1, 20))
        self.assertEqual(null["power"], F(1, 20))
        plant = A.exact_power(8, 8, F(1, 4), F(1))
        self.assertEqual(plant["power"], 1)
        self.assertLessEqual(plant["nonrandom_power"], plant["power"])

    def test_hidden_labels_count_convolution_exact(self):
        # Brute-force independently handles exactly two real repairs at four sites.
        p0, p1 = F(1, 4), F(3, 4)
        expected = [F(0)]*5
        for bits in itertools.product((0, 1), repeat=4):
            mass = F(1)
            for i, bit in enumerate(bits):
                p = p1 if i < 2 else p0
                mass *= p if bit else 1-p
            expected[sum(bits)] += mass
        self.assertEqual(A.convolve(A.binomial(2, p0), A.binomial(2, p1)), expected)

    def test_plant_likelihood_and_no_echo_null_wiring(self):
        local = list(range(8))*200
        c, repairs = M.collision_plant(local, [len(local)], 6, 1, 518003)
        self.assertTrue(repairs)
        rule = dict(lag=6, a=27, b=24, guarded=False)
        self.assertTrue(math.isfinite(A.score(c, local, rule)))
        # This is deterministic likelihood wiring, not a new power estimate.
        null = M.conditional_null([len(local)], [10], 518004)
        self.assertEqual(M.section_doublets(null, [len(local)]), [10])


if __name__ == "__main__":
    unittest.main(verbosity=2)
