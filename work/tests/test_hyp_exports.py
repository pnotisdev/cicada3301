"""kscreen-hyp inputs (work/kscreen/export_hyp.py), the engine's self-key guard (G lines) and its clocked pointer (clock=): decimation, the
constraint-1 filter, text-number streams, deep constant digits, LP2's own ciphertext as a key aligned with its windows,
and the guard that keeps a window from being deciphered with itself."""
import os
import random
import re
import struct
import subprocess
import sys
import tempfile
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
KS = os.path.join(WORK, "kscreen")
sys.path.insert(0, WORK)
sys.path.insert(0, KS)
import export  # noqa: E402
import export_hyp as eh  # noqa: E402
import keystreams  # noqa: E402
import lp  # noqa: E402
import sim  # noqa: E402

BIN = os.path.join(KS, "target", "release", "kscreen" + (".exe" if os.name == "nt" else ""))
PLAIN = os.path.join(WORK, "phpmt", "data", "english.txt")


class Exports(unittest.TestCase):
    def test_decimation(self):
        v = np.arange(2000) % 29
        d = eh.decimated({"n": v})
        self.assertTrue(np.array_equal(d["dec2:n"], v[::2]))
        self.assertTrue(np.array_equal(d["dec5:n"], v[::5]))
        self.assertNotIn("dec6:n", d)                   # 334 values: shorter than a screen window needs

    def test_constraint_1(self):
        P = keystreams.english_distribution()
        rng = np.random.default_rng(1)
        self.assertTrue(eh.admissible(rng.integers(0, 29, 4000), P))
        self.assertTrue(eh.admissible(rng.integers(0, 29, 450), P))
        self.assertFalse(eh.admissible(np.resize(lp.word_to_key("DIVINITY"), 4000), P))
        self.assertFalse(eh.admissible(np.array(sim.english_runes()[:4000]), P))      # an English running key

    def test_text_numbers(self):
        words = [[1, 2], [3], [28, 0, 5]]
        t = eh.text_numbers("t", words)
        runes = [1, 2, 3, 28, 0, 5]
        self.assertEqual(list(t["t prefix sum of rune indices"]), list(np.cumsum(runes) % 29))
        self.assertEqual(list(t["t prefix sum of prime values"]), list(np.cumsum([lp.PRIME[r] for r in runes]) % 29))
        self.assertEqual(list(t["t word sums of prime values"]), [(lp.PRIME[1] + lp.PRIME[2]) % 29, lp.PRIME[3] % 29,
                                                                   (lp.PRIME[28] + lp.PRIME[0] + lp.PRIME[5]) % 29])
        self.assertEqual(list(t["t prefix sum of rune indices (reversed)"]), list(np.cumsum(runes[::-1]) % 29))

    def test_self_reliance_is_the_essay_body(self):
        w = eh.self_reliance_words()
        self.assertEqual(w[:3], [lp.word_to_key(x) for x in ("SELF", "RELIANCE", "I")])
        self.assertGreater(len(w), 9000)

    def test_deep_digits(self):
        import mpmath
        deep, block = eh.DEEP, eh.BLOCK
        eh.DEEP, eh.BLOCK = (7, 50), 40
        try:
            out = eh.deep_digits()
        finally:
            eh.DEEP, eh.BLOCK = deep, block
        mpmath.mp.dps = 200
        s = mpmath.nstr(mpmath.pi, 150, strip_zeros=False).split(".")[1]
        self.assertEqual(list(out["pi digits (base 10) from position 7"]), [int(ch) % 29 for ch in s[7:47]])
        x = int(mpmath.floor((mpmath.pi - 3) * mpmath.mpf(29) ** 90))
        dig = []
        for _ in range(90):
            x, r = divmod(x, 29)
            dig.append(r)
        self.assertEqual(list(out["pi digits (base 29) from position 50"]), dig[::-1][50:90])

    def test_self_windows_align_with_the_stream(self):
        c, starts = eh.lp2_ciphertext()
        self.assertEqual(len(c), 12956)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "w.txt")
            eh.write_self_windows(path, starts)
            with open(path, encoding="utf-8") as f:
                blocks = f.read().split("W ")[1:]
        self.assertEqual(len(blocks), len(export.segment_windows()))
        for b in blocks:
            runes = [int(x) for x in b.split("\nR ")[1].split("\n")[0].split()]
            g = int(b.split("\nG ")[1])
            self.assertEqual(list(c[g:g + len(runes)]), runes)


def write_ksb(path, name, v):
    nb = name.encode()
    with open(path, "wb") as f:
        f.write(b"KSB1" + struct.pack("<I", 1) + struct.pack("<H", len(nb)) + nb + struct.pack("<I", len(v)) + bytes(v))


@unittest.skipUnless(os.path.exists(BIN), "build with: cargo build --release (in work/kscreen)")
class Guard(unittest.TestCase):
    def test_guard_stops_a_window_deciphering_itself(self):
        rng = random.Random(7)
        s = [rng.randrange(29) for _ in range(1200)]
        win = s[400:800]
        best = {}
        with tempfile.TemporaryDirectory() as d:
            ksb, out = os.path.join(d, "s.ksb"), os.path.join(d, "t.txt")
            write_ksb(ksb, "s", s)
            for tag, g in (("off", ""), ("on", "G 400\n")):
                w = os.path.join(d, f"w_{tag}.txt")
                with open(w, "w", newline="\n") as f:
                    f.write(f"W w {s[399]}\nR {' '.join(map(str, win))}\nL {len(win)}\n{g}")
                subprocess.run([BIN, "trace", w, f"file:{ksb}", out, "mults=1", "offs=388:401"], cwd=KS, check=True,
                               capture_output=True)
                with open(out, encoding="utf-8") as f:
                    rows = [list(map(int, x.split())) for x in f if x.strip()]
                best[tag] = max(29 * r[5] / (r[6] * (r[6] - 1)) for r in rows if r[6] > 1)
        self.assertGreater(best["off"], 3.0)          # offset 400 is the window itself: all-zero "plaintext"
        self.assertLess(best["on"], 1.4)

    @unittest.skipUnless(os.path.exists(PLAIN), "run work/phpmt/export_data.py")
    def test_clocked_pointer_is_found_only_by_a_clocked_screen(self):
        rng = random.Random(11)
        with tempfile.TemporaryDirectory() as d:
            ksb, plant = os.path.join(d, "s.ksb"), os.path.join(d, "p.txt")
            write_ksb(ksb, "s", [rng.randrange(29) for _ in range(20000)])
            subprocess.run([BIN, "plant", PLAIN, f"file:{ksb}", "s", "777", "1", "0", "0.18", "3", "0", plant, "clock=c1"],
                           cwd=KS, check=True, capture_output=True)
            best = {}
            for tag, extra in (("clocked", ["clock=c1"]), ("plain", [])):
                tsv = os.path.join(d, f"{tag}.tsv")
                subprocess.run([BIN, "screen", plant, f"file:{ksb}", tsv, "threads=2", *extra], cwd=KS, check=True,
                               capture_output=True)
                with open(tsv, encoding="utf-8") as f:
                    best[tag] = [float(x) for x in re.findall(r"# window \S+ best ([\d.]+)", f.read())]
        self.assertTrue(all(x >= 1.4 for x in best["clocked"]), best)
        self.assertTrue(all(x < 1.4 for x in best["plain"]), best)


if __name__ == "__main__":
    unittest.main()
