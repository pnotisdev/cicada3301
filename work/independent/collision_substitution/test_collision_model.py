"""Human-run local identities and independently enumerated tiny controls."""
from fractions import Fraction as F
import math
import unittest

import collision_model as M


def direct_next(history, y, taps, q):
    """Enumerate attempted ciphertext and forward repair coin, not moment vectors."""
    if not history:
        return F(1, M.Q)
    a, total = history[-1], F(0)
    for attempt in range(M.Q):
        if attempt != a:
            if attempt == y:
                total += F(1, M.Q)
            continue
        if y == a:
            total += (1 - q) / M.Q
        for lag, exponent, weight in taps:
            if len(history) >= lag:
                if y == M.transform(history[-lag], exponent):
                    total += q * weight / M.Q
            elif y != a:
                total += q * weight / (M.Q * (M.Q - 1))
    return total


class CollisionModelTests(unittest.TestCase):
    def test_group(self):
        self.assertEqual(pow(-2, 14, 29), 28)
        self.assertNotEqual(pow(-2, 4, 29), 1)
        for x in range(29):
            self.assertEqual(M.transform(x, 28), x)
            self.assertEqual(M.transform(M.transform(x, 1), -1), x)
        self.assertEqual([x for x in range(29) if M.transform(x, 1) == x], [8])

    def test_normalization_and_independent_overlay(self):
        histories = ([8], [15], [1, 2], [0, 2, 4, 6, 9, 12, 15, 8])
        for name, taps in M.templates():
            for history in histories:
                for q in (F(0), M.DESIGN_Q, F(1)):
                    for guarded in (False, True):
                        with self.subTest(name=name, history=history, q=q, guarded=guarded):
                            k = M.kernel(history, taps, q, guarded=guarded)
                            self.assertEqual(sum(k), 1)
                            self.assertTrue(all(v >= 0 for v in k))
                            self.assertEqual(k, M.independent_overlay_kernel(history, taps, q, guarded=guarded))

    def test_forward_enumerator_and_kernel(self):
        taps = ((1, 1, F(1, 2)), (2, 1, F(1, 2)))
        for history in ([8], [1], [15, 8], [8, 15]):
            k = M.kernel(history, taps, F(1, 2))
            self.assertEqual(k, [direct_next(history, y, taps, F(1, 2)) for y in range(29)])

    def test_two_point_recurrence_against_enumeration(self):
        cases = (((2, 0, F(1)),), ((2, 1, F(1)),),
                 ((1, 1, F(1, 2)), (2, 1, F(1, 2))))
        q = F(1, 2)
        for taps in cases:
            pairs = M.moments(3, taps, q)
            for j in (0, 1):
                for x in (0, 8, 15):
                    for y in (x, M.transform(x, 1), 7):
                        expected = F(0)
                        if j == 0:
                            for mid in range(29):
                                expected += F(1, 29) * direct_next([x], mid, taps, q) * direct_next([x, mid], y, taps, q)
                        else:
                            for first in range(29):
                                expected += F(1, 29) * direct_next([first], x, taps, q) * direct_next([first, x], y, taps, q)
                        self.assertEqual(M.pair_probability(pairs[j, 2], x, y), expected)

    def test_copy_family_cannot_force_nonidentity_T_mean(self):
        for lag in range(1, 9):
            for vector in M.moments(10, ((lag, 0, F(1)),)).values():
                self.assertTrue(all(v == 0 for v in vector[1:]))
                self.assertEqual(M.relation_probabilities(vector, 1)["any_source"], F(1, 29))

    def test_nonfixed_rune_symmetry(self):
        for vector in M.moments(8, ((6, 1, F(1)),)).values():
            for exponent in (0, 1):
                predicted = M.relation_probabilities(vector, exponent)
                for x in range(29):
                    actual = M.pair_probability(vector, x, M.transform(x, exponent))
                    key = "source_8" if x == 8 else "each_source_other_than_8"
                    self.assertEqual(actual, predicted[key])
                self.assertEqual(predicted["any_source"], predicted["source_8"] + 28 * predicted["each_source_other_than_8"])

    def test_first_eligible_T6(self):
        q = M.DESIGN_Q
        pairs = M.moments(7, ((6, 1, F(1)),), q)
        rho, lam = q / 29, -q / 28
        self.assertEqual(pairs[0, 6][1], rho)
        self.assertEqual(pairs[1, 6][0], -rho * lam ** 4)
        self.assertEqual(M.relation_probabilities(pairs[0, 6], 1)["any_source"], F(1, 29) + F(28, 29) * rho)

    def test_copy1_cancels_the_repair(self):
        self.assertTrue(all(all(v == 0 for v in row) for row in M.moments(8, ((1, 0, F(1)),)).values()))

    def test_exact_conditional_null_counts(self):
        c = M.conditional_null([9, 9], [0, 8], 1123)
        self.assertEqual(M.section_doublets(c, [9, 9]), [0, 8])
        self.assertTrue(all(0 <= x < 29 for x in c))

    def test_fast_scan_matches_direct_kernel(self):
        c = [1, 2, 3, 4, 5, 6, 22, 20, 7, 7, 8, 9, 2, 11, 23, 0]
        local = list(range(8)) * 2
        result = M.scan(c, local)
        q = M.DESIGN_Q
        for label, exponent in (("I", 0), ("T", 1)):
            for lag in (1, 2, 6):
                for guarded in (False, True):
                    expected = 0.0
                    for i, p in enumerate(local):
                        if p < lag:
                            continue
                        prob = M.kernel(c[i - p:i], ((lag, exponent, F(1)),), q, guarded=guarded)[c[i]]
                        base = M.baseline_probability(c[i], c[i - 1], q)
                        expected += math.log(float(prob / base))
                    got = next(r["score"] for r in result["primary"] if r.get("rule") == f"{label}_{lag}" and r.get("guarded") == guarded)
                    self.assertAlmostEqual(got, expected, places=10)
        for name, taps in M.templates()[-3:]:
            expected = 0.0
            for i, p in enumerate(local):
                if p < 1:
                    continue
                prob = M.kernel(c[i - p:i], taps, q)[c[i]]
                expected += math.log(float(prob / M.baseline_probability(c[i], c[i - 1], q)))
            got = next(r["score"] for r in result["primary"] if r.get("rule") == name)
            self.assertAlmostEqual(got, expected, places=10)

    def test_budget_mgf_envelope_spends_all_repair_choices(self):
        for a, b, target in ((0, 3, 5), (3, 3, 5), (8, 8, 8), (0, 8, 8)):
            h = [int(y == b) + int(y == target) for y in range(29)]
            for lam in (1 / 16, 1 / 4, 1):
                base = sum(math.exp(lam * v) for v in h) / 29
                bound = base + (math.exp(lam * max(h)) - math.exp(lam * h[a])) / 29
                actual_max = 0.0
                for replacement in range(29):
                    actual = sum((1 / 29 - (1 / 29 if y == a else 0) + (1 / 29 if y == replacement else 0))
                                 * math.exp(lam * h[y]) for y in range(29))
                    self.assertLessEqual(actual, bound + 1e-12)
                    actual_max = max(actual_max, actual)
                self.assertAlmostEqual(actual_max, bound, places=12)
        empty = M.budget_evalue([1, 2, 3], [0, 0, 0])
        self.assertEqual(empty["eligible"], 0)
        self.assertFalse(empty["reject_budget"])

    def test_retaining_a_colliding_key_needs_plaintext_differences(self):
        previous, plaintext, key = 7, 3, 4
        self.assertEqual((plaintext + key) % 29, previous)
        for next_plaintext in (3, 10):
            self.assertEqual((next_plaintext + key) % 29, (previous + next_plaintext - plaintext) % 29)
        self.assertNotEqual((3 + key) % 29, (10 + key) % 29)


if __name__ == "__main__":
    unittest.main(verbosity=2)
