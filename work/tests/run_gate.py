"""Run a unittest module as a gate (python work/tests/run_gate.py work.tests.test_stepmt): passes only if no test fails, errors OR is
skipped, because a GPU gate that skipped every test (no CuPy, no Rust build) has not passed anything."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))   # the repository root


def main():
    suite = unittest.defaultTestLoader.loadTestsFromName(sys.argv[1])
    r = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    ok = r.wasSuccessful() and not r.skipped
    print("GATE PASSED" if ok else f"GATE FAILED (failures={len(r.failures)}, errors={len(r.errors)}, skipped={len(r.skipped)})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
