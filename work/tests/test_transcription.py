"""Phase 2: the verified transcription differs from the community master only by the errata."""
import csv
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import lp  # noqa: E402


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read().splitlines()


class VerifiedTranscription(unittest.TestCase):
    def test_only_errata_lines_differ(self):
        a, b = read(lp.MASTER_ORIGINAL), read(lp.MASTER)
        self.assertEqual(len(a), len(b))
        changed = [(x, y) for x, y in zip(a, b) if x != y]
        with open(os.path.join(os.path.dirname(lp.MASTER), "errata.tsv"), encoding="utf-8") as f:
            errata = list(csv.DictReader(f, delimiter="\t"))
        self.assertEqual(len(changed), len(errata))
        for (old, new), e in zip(changed, errata):
            self.assertIn(e["master"].split()[0], old)
            self.assertIn(e["verified"].split()[0], new)

    def test_rune_count_unchanged(self):
        count = lambda lines: sum(ch in lp.RUNE_IDX for l in lines for ch in l)
        self.assertEqual(count(read(lp.MASTER_ORIGINAL)), count(read(lp.MASTER)))

    def test_believe_fixed(self):
        text = lp.decrypt_known(lp.load_segments(), 4)
        self.assertIn("BECAUSE WE BELIEUE THE FOLLOWING", text)


if __name__ == "__main__":
    unittest.main()
