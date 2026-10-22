"""scripts/reproduce_signals.py --fast: every claim in docs/FINDINGS.md section 1 that the fast subset covers still reproduces."""
import contextlib
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "scripts"))
import reproduce_signals as rs  # noqa: E402


class ReproduceSignals(unittest.TestCase):
    def test_fast_subset_has_no_fail(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            bad = rs.main(fast=True)
        self.assertEqual(bad, 0, "\n".join(l for l in buf.getvalue().splitlines() if l.startswith("FAIL")))
        self.assertGreater(len(rs.ROWS), 30)


if __name__ == "__main__":
    unittest.main()
