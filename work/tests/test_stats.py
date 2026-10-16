"""Phase 3: guard the statistical facts the attack plan relies on."""
import os
import random
import sys
import unittest
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import lp  # noqa: E402
import sim  # noqa: E402
import stats  # noqa: E402

S = stats.SEGS


def gsum(runes):
    return sum(lp.PRIME[r] for r in runes)


class Numerals(unittest.TestCase):
    def test_list_markers_kept_as_tokens(self):
        self.assertEqual([t for _, t in lp.numeral_positions(S[4])], ["#1", "#2"])      # solved
        self.assertEqual([t for _, t in lp.numeral_positions(S[14])],
                         ["#1", "#2", "#3", "#4", "#5"])                                    # unsolved
        self.assertEqual(lp.numeral_positions(S[9]), [(692, "#7")])

    def test_numerals_do_not_change_rune_stream(self):
        self.assertEqual(sum(len(lp.runes_of(s)) for s in S[7:16]), 12956)


class MagicSquares(unittest.TestCase):
    def _cells(self, toks):
        out, cur = [], []
        for t in toks + [" "]:
            if isinstance(t, int):
                cur.append(t)
            else:
                if cur:
                    out.append(gsum(cur))
                    cur = []
                if t.startswith("#"):
                    out.append(int(t[1:]))
        return out

    def _magic(self, vals, total):
        rows = [vals[i * 5:(i + 1) * 5] for i in range(5)]
        sums = [sum(r) for r in rows] + [sum(r[j] for r in rows) for j in range(5)]
        sums += [sum(rows[i][i] for i in range(5)), sum(rows[i][4 - i] for i in range(5))]
        self.assertEqual(set(sums), {total})

    def test_some_wisdom_word_square_is_1033(self):
        self._magic(self._cells(S[2])[-25:], 1033)

    def test_page14_square_is_3301(self):
        self._magic([int(t[1:]) for t in S[6] if isinstance(t, str) and t.startswith("#")][:25], 3301)


class UnsolvedFingerprint(unittest.TestCase):
    c = stats.stream()

    def test_flat_unigrams_and_no_literal_f(self):
        self.assertLess(abs(lp.ioc(self.c) - 1.0), 0.002)
        self.assertLess(abs(100 * self.c.count(0) / len(self.c) - 100 / 29), 0.6)

    def test_only_difference_zero_is_depleted(self):
        d = Counter()
        for i in stats.UNSOLVED:
            r = lp.runes_of(S[i])
            d.update((b - a) % 29 for a, b in zip(r, r[1:]))
        n = sum(d.values())
        e = n / 29
        self.assertLess(d[0], 0.25 * e)
        self.assertLess(sum((d[k] - e) ** 2 / e for k in range(1, 29)), 55.5)

    def test_only_lag_one_is_depleted(self):
        for k in (2, 3, 5, 10):
            hit = sum(a == b for i in stats.UNSOLVED for a, b in
                      zip(lp.runes_of(S[i]), lp.runes_of(S[i])[k:]))
            self.assertGreater(hit / len(self.c), 0.029)


class Generators(unittest.TestCase):
    def test_only_collision_rule_reproduces_doublet_rate(self):
        p = sim.english_runes()[:13000]
        R = random.Random(3301)
        self.assertGreater(sim.fingerprint(sim.g_random(p, R))["doublet"], 2.8)
        self.assertGreater(sim.fingerprint(sim.g_totient(p, R))["doublet"], 2.8)
        self.assertLess(abs(sim.fingerprint(sim.make_reroll(0.8)(p, R))["doublet"] - 0.66), 0.35)

    def test_english_running_key_ioc_too_high(self):
        eng = sim.english_runes()
        p, k = eng[:12956], eng[40000:40000 + 12956]
        self.assertGreater(lp.ioc([(a + b) % 29 for a, b in zip(p, k)]), 1.02)


if __name__ == "__main__":
    unittest.main()
