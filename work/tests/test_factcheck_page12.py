"""Checks of work/factcheck_page12.py (the Reddit page-12 fact check, work/log/factcheck_page12_2026-10-18.md).

The planted controls of the script show that its encryption and decryption are inverses; these tests also tie the Bifid code
to the textbook example, check the inverses of the two key stages, and pin the page facts the write-up quotes.
"""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import factcheck_page12 as fc  # noqa: E402


class TestFactcheckPage12(unittest.TestCase):
    def test_bifid_textbook_example(self):
        """the classic 5 x 5 example: FLEEATONCE -> UAEOLWRINS with the square BGWKZ QPNDS IOAXE FCLUM THYVR"""
        abc = "ABCDEFGHIKLMNOPQRSTUVWXYZ"                     # 25 letters, I = J
        sq = fc.Square("textbook", [abc.index(ch) for ch in "BGWKZQPNDSIOAXEFCLUMTHYVR"], 25, 5, 5)
        P = np.array([abc.index(ch) for ch in "FLEEATONCE"])
        C, _ = fc.bifid_encrypt(P, sq, 0)
        self.assertEqual("".join(abc[x] for x in C), "UAEOLWRINS")
        self.assertEqual(list(fc.bifid_decrypt(C[None, :], sq, 0, False)[0]), list(P))

    def test_bifid_inverse_on_the_claims_squares(self):
        rng = np.random.default_rng(1)
        for sq in fc.RSQ + fc.LSQ:
            for p in fc.PERIODS:
                P, _ = fc.make_reachable(rng.integers(sq.size, size=97), sq, p, rng)
                C, _ = fc.bifid_encrypt(P, sq, p)
                self.assertTrue((C < sq.size).all())
                for wrap in (False, True):
                    self.assertEqual(list(fc.bifid_decrypt(C[None, :], sq, p, wrap)[0]), list(P))

    def test_key_stage_inverses(self):
        rng = np.random.default_rng(2)
        X = rng.integers(fc.N, size=300)
        i = 1059 + np.arange(300)
        for m in fc.INVERTIBLE_MULTS:
            self.assertEqual(list(fc.invert_mult(m, fc.apply_mult(m, X, i), i)), list(X), m)
        for k in fc.KEYS:
            self.assertEqual(list(fc.invert_key(k, fc.apply_key(k, X, i), i)), list(X), k[0])

    def test_page_facts(self):
        seg, lo, hi = fc.page_span(fc.tp_of_image(12 + 17))        # LP2 12.jpg = image 29
        self.assertEqual((seg, lo, hi - lo), (9, 1059, 261))
        c = np.array(fc.lp.runes_of(fc.SEGS[seg])[lo:hi])
        self.assertEqual(int((c[1:] == c[:-1]).sum()), 1)           # one doublet on the page
        self.assertEqual(len(fc.CLAIM_RUNES), 56)
        self.assertEqual(fc.page_span(fc.tp_of_image(56 + 17))[0], 16)   # LP2 56.jpg is An End (section 0.16)
        self.assertEqual(fc.page_span(fc.tp_of_image(12))[0], 4)         # image 12 is The Loss of Divinity (0.4)


if __name__ == "__main__":
    unittest.main()
