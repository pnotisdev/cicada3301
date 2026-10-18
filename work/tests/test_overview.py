"""The status pages are views of docs/registry.toml: the registry must validate (statuses, links, every results folder and work script described)
and the generated files (STATUS.md, results/INDEX.md, results/index.html, the README status block) must be current.
Fix: python scripts/build_overview.py"""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Overview(unittest.TestCase):
    def test_registry_and_generated_pages_are_current(self):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "build_overview.py"), "--check"],
                           capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
