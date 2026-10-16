"""Separator layer of the transcription against the page images (work/separator_audit.py)."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import separator_audit as sa  # noqa: E402


class SeparatorAudit(unittest.TestCase):
    def test_three_pages_match_except_the_apostrophe_tick(self):
        tally, rows, ticks = sa.audit([20, 21, 22])
        measured = sum(v for k, v in tally.items() if k != "unmeasurable")
        self.assertGreater(measured, 550)
        # every word dot and clause mark in the transcription is in the image, and nothing extra, except one tick glyph
        self.assertEqual(tally[("word", "none")], 0)
        self.assertEqual(tally[("clause", "none")], 0)
        self.assertEqual(tally[("none", "clause")], 0)
        self.assertGreater(tally[("word", "word")], 120)
        self.assertEqual(len(rows), 1)
        n, line, gap, tr, seen, marks = rows[0]
        self.assertEqual((n, tr, seen), (21, "none", "word"))
        self.assertTrue(any(355 <= a <= 370 for a in marks))          # the tick stamp, ~362 px
        self.assertEqual(len(ticks), 1)


if __name__ == "__main__":
    unittest.main()
