"""Word-internal structure tools (rewritten in review): brute-force agreement of the counters, a planted copy process that the
counters must detect, a random null that they must not, and the algebra behind the dictionary test."""
import os
import random
import sys
import unittest

import numpy as np
from scipy.stats import poisson

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import lag5_check as l5  # noqa: E402
import word_internal_repeats as wir  # noqa: E402
import word_key_dictionary as wkd  # noqa: E402

N = 29


def words_to_arrays(words):
    r = np.array([x for w in words for x in w])
    wid = np.repeat(np.arange(len(words)), [len(w) for w in words])
    return r, wid


def random_words(rng, n, alphabet=N, lo=2, hi=14):
    return [[rng.randrange(alphabet) for _ in range(rng.randrange(lo, hi))] for _ in range(n)]


class CountersAgreeWithBruteForce(unittest.TestCase):
    def test_lag5_check_counts(self):
        rng = random.Random(5)
        words = random_words(rng, 300, alphabet=3)  # small alphabet: many coincidences, every branch is exercised
        r, wid = words_to_arrays(words)
        for g in (2, 5, 7):
            nw = e = nb = b = ce = 0
            for w in words:
                for j in range(len(w) - g):
                    nw += 1
                    e += w[j] == w[j + g]
                for j in range(len(w) - g - 1):
                    nb += 1
                    same = w[j] == w[j + g]
                    b += same and w[j + 1] == w[j + g + 1]
                    ce += same
            self.assertEqual(tuple(l5.counts(r, wid, g)), (nw, e, nb, b, ce), g)

    def test_branch_counter_agrees_with_ours(self):
        rng = random.Random(6)
        r, wid = words_to_arrays(random_words(rng, 300, alphabet=4))
        for g in (2, 5):
            nw, e, nb, b, ce = l5.counts(r, wid, g)
            self.assertEqual(wir.bigram_pairs(r, wid, g), (nb, b))
            self.assertEqual(wir.coincidence(r, wid, g), (nw, e))


class Detection(unittest.TestCase):
    @staticmethod
    def bigram_p(words, g=5):
        r, wid = words_to_arrays(words)
        S = float(((np.bincount(r, minlength=N) / len(r)) ** 2).sum())
        nw, e, nb, b, ce = l5.counts(r, wid, g)
        return poisson.sf(b - 1, nb * S * S), b, nb * S * S

    def test_random_words_have_no_lag5_clustering(self):
        for seed in range(5):
            rng = random.Random(100 + seed)
            p, b, exp = self.bigram_p(random_words(rng, 1500, lo=6, hi=14))
            self.assertGreater(p, 1e-3, (seed, b, exp))

    def test_planted_copy_runs_are_detected(self):
        """control: a rune copies the rune five back with a run of two (j and j+1) in 2% of the long words"""
        rng = random.Random(7)
        words = random_words(rng, 1500, lo=6, hi=14)
        for w in words:
            if rng.random() < 0.02 and len(w) >= 8:
                j = rng.randrange(0, len(w) - 6)
                w[j + 5], w[j + 6] = w[j], w[j + 1]
        p, b, exp = self.bigram_p(words)
        self.assertLess(p, 1e-4, (b, exp))


class DictionaryAlgebra(unittest.TestCase):
    def test_operators_annihilate_the_key_family(self):
        rng = random.Random(8)
        for d in (0, 1, 2):
            co = [rng.randrange(N) for _ in range(d + 1)]
            key = np.array([sum(co[i] * pow(j, i, N) for i in range(d + 1)) % N for j in range(12)])
            self.assertTrue((wkd.fdiff(key, d + 1) == 0).all(), d)
        vec = [rng.randrange(N) for _ in range(5)]
        self.assertTrue((wkd.lagdiff(np.array([vec[j % 5] for j in range(14)]), 5) == 0).all())

    def test_planted_keys_found_and_null_not(self):
        rng = random.Random(1)
        seqs = wkd.sample_dictionary(rng, per_len=60, lo=8, hi=10)
        lens = [len(s) for s in seqs]
        for kind, par in (("poly", 1), ("per", 5)):
            planted = wkd.table(wkd.encipher(seqs, kind, par, rng), kind, par)
            sur = wkd.table(wkd.surrogate(lens, rng), kind, par)
            self.assertTrue(planted)
            for L, (n, hits, _e) in planted.items():
                self.assertGreater(hits / n, 0.6, (kind, par, L))
            for L, (n, hits, e) in sur.items():
                self.assertLessEqual(hits, n * e + 4 * (n * e) ** 0.5 + 2, (kind, par, L))

    def test_wrong_family_is_not_detected(self):
        """a period-5 per-word key is not a constant shift: the Caesar-per-word test must stay at its null"""
        rng = random.Random(2)
        seqs = wkd.sample_dictionary(rng, per_len=60, lo=8, hi=10)
        t = wkd.table(wkd.encipher(seqs, "per", 5, rng), "poly", 0)
        for L, (n, hits, e) in t.items():
            self.assertLessEqual(hits, n * e + 4 * (n * e) ** 0.5 + 2, L)


class ChainNull(unittest.TestCase):
    def test_chain_null_has_lp2_doublet_rate(self):
        c = wir.chain_null(None, 200000, np.random.default_rng(3))
        self.assertAlmostEqual(float((c[1:] == c[:-1]).mean()), 0.0066, delta=0.002)


if __name__ == "__main__":
    unittest.main()
