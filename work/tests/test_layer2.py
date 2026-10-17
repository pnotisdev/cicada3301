"""Two-layer screen (work/layer2, hypothesis H-LAYER): planted keyword-inside-stream ciphers are found at their offset with
their keyword (literal F on and off, plain and Atbash alphabets, skip and coin models), the whole-window re-decode reads
the planted text, wrong offsets stay far below the decision threshold, and periodic mode finds a keyword it was not given."""
import os
import re
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
L2 = os.path.join(os.path.dirname(HERE), "layer2")
BIN = os.path.join(L2, "target", "release", "layer2" + (".exe" if os.name == "nt" else ""))
PLAIN = os.path.join(os.path.dirname(HERE), "phpmt", "data", "english.txt")
CORE = os.path.join(L2, "data", "core.ksb")
DIVINITY = "23,10,1,10,9,10,16,26"
FIRFUM = "0,10,4,0,1,19,0,18,4,18,9,0,18"


def window_bests(tsv):
    out = {}
    with open(tsv, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"# window (\S+) best (\S+) item=(.*) offset=(\d+) mult=(\d+) model=(\d+) (.*)$", line)
            if m:
                out[m.group(1)] = (float(m.group(2)), int(m.group(4)), m.group(7))
    return out


@unittest.skipUnless(all(os.path.exists(p) for p in (BIN, PLAIN, CORE)),
                     "build with: cargo build --release (in work/layer2), then python work/layer2/export.py")
class Layer2(unittest.TestCase):
    def run_bin(self, *args):
        return subprocess.run([BIN, *args], cwd=L2, capture_output=True, text=True, check=True).stdout

    def plant(self, d, item, off, mult, model, kw, phase, isign, litf, atb):
        path = os.path.join(d, "plant.txt")
        self.run_bin("plant", PLAIN, "file:" + CORE, item, str(off), str(mult), str(model), "0.18", "3", kw, str(phase),
                     str(isign), str(litf), str(atb), path)
        return path

    def bigram_screen(self, d, plant, item, kwline, offs):
        kwf, tsv = os.path.join(d, "kw.txt"), os.path.join(d, "out.tsv")
        with open(kwf, "w", encoding="utf-8") as f:
            f.write(kwline + "\n")
        self.run_bin("screen", plant, "file:" + CORE, tsv, "mode=bigram", f"kw={kwf}", f"only={item}", f"offs={offs}", "threads=4")
        return window_bests(tsv)

    def test_literal_f_keyword_inside_totient_skip_model(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.plant(d, "primes-1 (totient)", 1234, 1, 0, DIVINITY, 3, 1, 1, 0)
            best = self.bigram_screen(d, p, "primes-1 (totient)", "DIVINITY " + DIVINITY.replace(",", " "), "1200:1300")
            sc, off, inner = best["plant_0"]
            self.assertLessEqual(abs(off - 1234), 2)
            self.assertIn("kw=DIVINITY", inner)
            self.assertGreater(sc, 5.0)
            # windows 1 and 2 have their true offsets (2231, 3228) outside the range: chance level only
            self.assertLess(max(best["plant_1"][0], best["plant_2"][0]), 0.0)
            out = self.run_bin("verify", p, "file:" + CORE, "primes-1 (totient)", "1234", "1", "0", "plant_0", "mode=bigram",
                               "kwvals=" + DIVINITY, "isign=1", "phase=3", "litf=1", "atb=0", "controls=5")
            self.assertGreater(float(re.search(r"score (-?[\d.]+)", out).group(1)), 5.0)
            self.assertIn("HIMSELFANDHIS", re.search(r"^text (.*)$", out, re.M).group(1))
            cmax = float(re.search(r"controls 5 random offsets: mean (-?[\d.]+) max (-?[\d.]+)", out).group(2))
            self.assertLess(cmax, 0.0)

    def test_atbash_negative_signs_coin_model(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.plant(d, "pi digits (base 29)", 777, 28, 1, FIRFUM, 0, 28, 0, 1)
            best = self.bigram_screen(d, p, "pi digits (base 29)", "FIRFUMFERENFE " + FIRFUM.replace(",", " "), "740:820")
            sc, off, inner = best["plant_0"]
            self.assertLessEqual(abs(off - 777), 2)
            self.assertIn("atb=1", inner)
            self.assertGreater(sc, 5.0)

    def test_periodic_mode_finds_an_unlisted_keyword(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.plant(d, "primes", 2000, 1, 0, "7,18,4,3,16,24", 2, 1, 0, 0)
            tsv = os.path.join(d, "per.tsv")
            self.run_bin("screen", p, "file:" + CORE, tsv, "mode=periodic", "only=primes", "ms=2:12", "litf=0", "offs=1950:2050",
                         "threads=4")
            z, off, inner = window_bests(tsv)["plant_0"]
            self.assertLessEqual(abs(off - 2000), 2)
            self.assertIn(inner.split()[0], ("m=6", "m=12"))
            self.assertGreater(z, 8.0)


if __name__ == "__main__":
    unittest.main()
