"""Word-internal structure tools: planted per-word keys are detected by the dictionary test, random words are not,
and the repeated-bigram counter agrees with a brute-force count."""
import os
import random
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import word_internal_repeats as wir  # noqa: E402
import word_key_dictionary as wkd  # noqa: E402


class WordKeyDictionary(unittest.TestCase):
    def test_planted_keys_detected_and_random_words_not(self):
        rng = random.Random(1)
        seqs = wkd.sample_dictionary(rng, per_len=60, lo=8, hi=10)
        lens = [len(s) for s in seqs]
        for kind, par in (("poly", 1), ("per", 5)):
            planted = wkd.table(wkd.encipher(seqs, kind, par, rng), kind, par)
            sur = wkd.table(wkd.surrogate(lens, rng), kind, par)
            for L, (n, hits, _e) in planted.items():
                self.assertGreater(hits / n, 0.6, (kind, par, L))
            for L, (n, hits, e) in sur.items():
                self.assertLessEqual(hits, n * e + 4 * (n * e) ** 0.5 + 2, (kind, par, L))


class RepeatCounter(unittest.TestCase):
    def test_bigram_pairs_match_brute_force(self):
        rng = random.Random(2)
        words = [[rng.randrange(4) for _ in range(rng.randrange(6, 12))] for _ in range(200)]
        r, wid = wir.flatten(words)
        for g in (2, 5):
            n_in, n_eq = wir.bigram_pairs(r, wid, g)
            bn = be = 0
            for w in words:
                for j in range(len(w) - g - 1):
                    bn += 1
                    be += w[j] == w[j + g] and w[j + 1] == w[j + g + 1]
            self.assertEqual((n_in, n_eq), (bn, be))

    def test_chain_null_has_lp2_doublet_rate(self):
        rng = np.random.default_rng(3)
        c = wir.chain_null(None, 200000, rng)
        self.assertAlmostEqual(float((c[1:] == c[:-1]).mean()), 0.0066, delta=0.002)


if __name__ == "__main__":
    unittest.main()
