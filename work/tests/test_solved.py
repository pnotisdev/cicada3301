"""Regression tests: every solved Liber Primus section must decode exactly.

Run from the work/ folder:
    python -m unittest discover -s tests -v
"""
import io
import os
import sys
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import lp  # noqa: E402

SEGS = lp.load_segments()

# Independent anchors: a phrase from each section, checked separately from the golden file.
PHRASES = {
    0: ["A WARNING. BELIEUE NOTHING FROM THIS BOOC", "FOR ALL IS SACRED."],
    1: ["WELCOME PILGRIM TO THE GREAT JOURNEY TOWARD THE END OF ALL THINGS",
        "YOU ARE A LAW UNTO YOURSELF", "COMMAND YOUR OWN SELF."],
    2: ["THE PRIMES ARE SACRED", "ALL THINGS SHOULD BE ENCRYPTED"],
    3: ["A MAN DECIDED TO GO AND STUDY WITH A MASTER", "DO FOUR UNREASONABLE THINGS EACH DAY."],
    4: ["THE LOSS OF DIUINITY", "PROGRAM YOUR MIND. PROGRAM REALITY."],
    5: ["THE I IS THE UOICE OF THE CIRCUMFERENCE", "AND THE STUDENTS WERE ENLIGHTENED."],
    6: ["CWESTIAN ALL THINGS. DISCOUER TRUTH INSIDE YOURSELF"],
    16: ["WITHIN THE DEEP WEB THERE EXISTS A PAGE THAT HASHES TO",
         "IT IS THE DUTY OF EUERY PILGRIM TO SEEC OUT THIS PAGE."],
    17: ["LICE THE INSTAR TUNNELING TO THE SURFACE", "FIND THE DIUINITY WITHIN AND EMERGE."],
}

# Keystream sections: (segment, key function, literal-F positions in KNOWN)
KEYSTREAMS = {
    1: (lambda j: lp._DIVINITY[j % len(lp._DIVINITY)], [48, 74, 84, 132, 159, 160, 250, 421, 443, 465, 514]),
    5: (lambda j: lp._FIRFUM[j % len(lp._FIRFUM)], [49, 58]),
    16: (lambda j: lp._PRIMES[j] - 1, [56]),
}


class SolvedSections(unittest.TestCase):
    def test_transcription_shape(self):
        self.assertEqual(len(SEGS), 18)
        self.assertEqual(sum(len(lp.runes_of(s)) for s in SEGS[7:16]), 12956)

    def test_phrases(self):
        for i, phrases in PHRASES.items():
            text = lp.decrypt_known(SEGS, i)
            for p in phrases:
                with self.subTest(seg=i, phrase=p):
                    self.assertIn(p, text)

    def test_golden_output(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            lp.main(["lp.py", "known"])
        with open(os.path.join(HERE, "expected_solved.txt"), encoding="utf-8") as f:
            self.assertEqual(buf.getvalue(), f.read())

    def test_dictionary_coverage(self):
        # Every solved section should be overwhelmingly real English. 0.2 is lower
        # because its "SHADOWS AETHEREAL BUFFERS ..." line is rare-word plaintext.
        for i in lp.KNOWN:
            with self.subTest(seg=i):
                s = SEGS[i]
                plain = lp.KNOWN[i][1](lp.runes_of(s))
                self.assertGreater(lp.word_score(s, plain), 0.40 if i == 2 else 0.65)

    def test_literal_f_rule(self):
        # Phase 1 finding: literal positions are exactly the plaintext F's.
        for i, (_, literal) in KEYSTREAMS.items():
            with self.subTest(seg=i):
                plain = lp.KNOWN[i][1](lp.runes_of(SEGS[i]))
                self.assertEqual([k for k, x in enumerate(plain) if x == 0], literal)

    def test_literal_f_search_rediscovers_positions(self):
        for i, (keyfn, literal) in KEYSTREAMS.items():
            with self.subTest(seg=i):
                self.assertEqual(lp.find_literal_f(SEGS[i], keyfn), literal)

    def test_unsolved_stats_baseline(self):
        # Guards the statistics Phase 3 builds on: flat IoC and the doublet anomaly.
        c = [x for s in SEGS[7:16] for x in lp.runes_of(s)]
        self.assertLess(abs(lp.ioc(c) - 1.0), 0.03)
        self.assertEqual(sum(c[k] == c[k + 1] for k in range(len(c) - 1)), 86)


if __name__ == "__main__":
    unittest.main()
