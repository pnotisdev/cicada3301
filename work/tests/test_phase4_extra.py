"""Base-60 grid decoding and the reversed-direction screen."""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import attack  # noqa: E402
import grid60  # noqa: E402
import lp  # noqa: E402


class Base60Grid(unittest.TestCase):
    def test_grid_is_256_bytes(self):
        g = grid60.grid_bytes()
        self.assertEqual(len(g), 256)
        self.assertEqual(max(g), 255)  # "4F" = 4*60 + 15
        self.assertGreater(grid60.entropy(g), 6.9)

    def test_an_end_hash_is_512_bits(self):
        self.assertEqual(len(grid60.an_end_hash()), 128)


class ReverseScreen(unittest.TestCase):
    def test_key_from_segment_end_found_with_reversed_dictionary(self):
        ps = lp.primes(3000)
        ks = np.array([p - 1 for p in ps], dtype=np.int64) % 29
        rev = attack.synthetic_tokens(300, start=7000)[::-1]
        T = attack.Text(attack.encrypt_tokens(rev, lambda j: int(ks[j]) + 3, q=0.8, seed=3))
        c = np.array(T.c)
        s = attack.fast_screen(c, T.words, ks, reverse=True)
        self.assertEqual(int(s.argmax()), 3)
        self.assertGreater(s.max(), 0.45)
        self.assertLess(attack.fast_screen(c, T.words, ks, reverse=False).max(), 0.25)


if __name__ == "__main__":
    unittest.main()
