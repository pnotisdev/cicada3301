"""Local tests, run by echo_nulls.py gate; no Rust/GPU engines or experiments."""
import math
import random
import unittest

from echo_nulls import (Q, add_log, eligible, forward, ordinary_arcs, plant)
from manual_common import lp_module


def toy_logs():
    rows = []
    for a in range(30):
        row = [1 + ((a + 3) * (b + 7)) % 17 for b in range(Q)]
        rows.append([math.log(x / sum(row)) for x in row])
    return rows


def exhaustive_mass(c, starts, key, offset, mult, atb, rho, logs, q):
    """Independent slow enumerator: enumerate PLAINTEXT, simulate forward draws.

    No inverse-arcs routine, state merging, or log-sum helper from the decoder.
    Suitable only for tiny fixtures. The uniform hypothesis is the same function
    with all plaintext probabilities 1/29.
    """
    def visit(i, j, last, was_null):
        if i == len(c):
            return 1.0
        prev = c[i - 1] if i else -1
        may = i - starts[i] >= 6 and (24 - 2 * c[i - 6]) % Q != prev
        chance = rho if may and not was_null else 0.0
        total = 0.0
        if chance and c[i] == (24 - 2 * c[i - 6]) % Q:
            total += chance * visit(i + 1, j, last, True)
        for p in range(Q):
            raw = Q - 1 - p if atb else p
            weight = (1 - chance) * math.exp(logs[last][p])
            at = j
            while at < len(key):
                y = (raw + mult * key[at]) % Q
                if y == c[i]:
                    total += weight * (1 - q if y == prev else 1) * visit(i + 1, at + 1, p, False)
                if prev < 0 or y != prev:
                    break
                weight *= q
                at += 1
        return total
    return visit(0, offset, Q, False)


class ExactForwardTests(unittest.TestCase):
    def test_log_merge(self):
        table = {}
        add_log(table, 1, -1000)
        add_log(table, 1, -1000)
        self.assertAlmostEqual(table[1], -1000 + math.log(2), places=12)

    def test_arcs_include_multiple_rejected_draws(self):
        # raw=4, keys 5,5,8: two rejected ciphertext-9 draws, then ciphertext 12.
        arcs = ordinary_arcs(12, 9, [5, 5, 8, 1], 0, 1, 0.8)
        self.assertTrue(any(j == 3 and p == 4 and abs(w - 2 * math.log(0.8)) < 1e-12
                            for j, p, w in arcs))
        self.assertEqual(ordinary_arcs(12, -1, [5, 5, 8], 0, 1, 0.8), [(1, 7, 0.0)])

    def test_inverse_forward_matches_brute_force(self):
        key = [5, 5, 8] + [random.Random(901 + i).randrange(Q) for i in range(50)]
        logs = toy_logs()
        uniform = [[-math.log(Q)] * Q for _ in range(30)]
        for c in ([1, 1, 3], [1, 2, 3, 4, 5, 6, 22, 8], [1, 2, 3, 4, 5, 6, 22, 20]):
            starts = [0] * len(c)
            for mult, atb in ((1, False), (28, True)):
                for rho in (0.0, 0.20):
                    with self.subTest(c=c, mult=mult, atb=atb, rho=rho):
                        got = forward(c, starts, key, 0, mult, atb, rho, logs, q=0.4)
                        a = exhaustive_mass(c, starts, key, 0, mult, atb, rho, logs, 0.4)
                        b = exhaustive_mass(c, starts, key, 0, mult, atb, rho, uniform, 0.4)
                        self.assertGreater(a, 0)
                        self.assertGreater(b, 0)
                        self.assertAlmostEqual(got["language_log_mass"], math.log(a), places=10)
                        self.assertAlmostEqual(got["uniform_log_mass"], math.log(b), places=10)
                        self.assertAlmostEqual(got["score_nats"], math.log(a / b), places=10)

    def test_uniform_language_ratio_is_zero(self):
        logs = [[-math.log(Q)] * Q for _ in range(30)]
        key = list(range(Q)) * 4
        c = [1, 2, 3, 4, 5, 6, 22, 8]
        got = forward(c, [0] * len(c), key, 0, 1, False, 0.2, logs)
        self.assertAlmostEqual(got["score_nats"], 0, places=11)

    def test_no_skip_no_null_is_direct_bigrams(self):
        logs = toy_logs()
        c, key = [7, 11, 4, 2, 25], [3, 9, 6, 8, 2, 12]
        p = [(ci - ki) % Q for ci, ki in zip(c, key)]
        expected = sum(logs[a][b] + math.log(Q) for a, b in zip([Q] + p[:-1], p))
        answer = forward(c, [0] * len(c), key, 0, 1, False, 0, logs, q=0, trace=True)
        self.assertAlmostEqual(answer["score_nats"], expected, places=11)
        self.assertEqual(answer["plain"], p)
        self.assertEqual(answer["deleted"], [])

    def test_trace_does_not_change_marginal_score(self):
        logs = toy_logs()
        c = [1, 2, 3, 4, 5, 6, 22, 8]
        key = [random.Random(702 + i).randrange(Q) for i in range(100)]
        a = forward(c, [0] * len(c), key, 0, 1, False, 0.2, logs)
        b = forward(c, [0] * len(c), key, 0, 1, False, 0.2, logs, trace=True)
        self.assertEqual(a["score_nats"], b["score_nats"])
        self.assertEqual(len(b["aligned"]), len(c))
        for i in b["deleted"]:
            self.assertGreaterEqual(i, 6)
            self.assertEqual(c[i], (24 - 2 * c[i - 6]) % Q)
            self.assertFalse(i - 1 in b["deleted"])

    def test_word_scope_and_collision_guard(self):
        c = [1, 2, 3, 4, 5, 6, 22, 8]
        self.assertTrue(eligible(c, [0] * len(c), 6))
        self.assertFalse(eligible(c, [0] * 6 + [6, 6], 6))
        c[5] = 22
        self.assertFalse(eligible(c, [0] * len(c), 6))

    def test_plaintext_plant_without_skips_or_nulls(self):
        p = list(range(Q))
        key = list(range(Q)) * 2
        for mult in (1, 28):
            for atb in (False, True):
                c, aligned = plant(p, [0] * len(p), key, 2, mult, atb, 0, 41, q=0)
                self.assertEqual(aligned, p)
                raw = [Q - 1 - x if atb else x for x in p]
                self.assertEqual(c, [(x + mult * key[i + 2]) % Q for i, x in enumerate(raw)])

    def test_layout_wrap_convention(self):
        lp = lp_module()
        toks = [0, "\n", 1, "%", 2, " ", 3]
        spans = lp.word_spans(toks, [0, 1, 2, 3])
        self.assertEqual([(a, b) for _, a, b in spans], [(0, 3), (3, 4)])

    def test_invalid_arguments(self):
        with self.assertRaises(ValueError):
            forward([], [], [1], 0, 1, False, 0.1, toy_logs())
        with self.assertRaises(ValueError):
            forward([1], [0], [1], 0, 1, False, 1, toy_logs())


if __name__ == "__main__":
    unittest.main(verbosity=2)
