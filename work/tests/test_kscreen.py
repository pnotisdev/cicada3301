"""Language-agnostic keystream screen (work/kscreen): recovers planted keys under both anti-repeat models,
behind a substituted plaintext alphabet, and keeps random keys well below the decision threshold."""
import os
import re
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
KS = os.path.join(os.path.dirname(HERE), "kscreen")
BIN = os.path.join(KS, "target", "release", "kscreen" + (".exe" if os.name == "nt" else ""))
PLAIN = os.path.join(os.path.dirname(HERE), "phpmt", "data", "english.txt")


def window_bests(tsv):
    out = {}
    with open(tsv, encoding="utf-8") as f:
        lines = f.read().splitlines()
    for line in lines:
        m = re.match(r"# window (\S+) best ([\d.]+) item=(.*) offset=(\S+) mult=(\d+) model=(\d+)", line)
        if m:
            out[m.group(1)] = (float(m.group(2)), m.group(3), m.group(4))
    return out


@unittest.skipUnless(os.path.exists(BIN) and os.path.exists(PLAIN),
                     "build with: cargo build --release (in work/kscreen) and run work/phpmt/export_data.py")
class KScreen(unittest.TestCase):
    def run_bin(self, *args):
        return subprocess.run([BIN, *args], cwd=KS, capture_output=True, text=True, check=True)

    def plant_and_screen(self, family, item, offset, model, subst, extra=()):
        with tempfile.TemporaryDirectory() as d:
            plant, tsv = os.path.join(d, "plant.txt"), os.path.join(d, "out.tsv")
            self.run_bin("plant", PLAIN, family, item, offset, "1", str(model), "0.18", "5", str(subst), plant)
            with open(plant, encoding="utf-8") as f:
                truth = dict(re.findall(r"# truth (\S+) item=.* offset=(\S+) mult", f.read()))
            self.run_bin("screen", plant, family, tsv, f"only={item}", "threads=4", *extra)
            return truth, window_bests(tsv)

    def test_fibonacci_key_coin_model_substituted_alphabet(self):
        truth, best = self.plant_and_screen("lin:2", "lin2:1,1", "state=1,1", 1, 1, ("mults=1",))
        for win, off in truth.items():
            ioc, item, boff = best[win]
            self.assertEqual(item, "lin2:1,1")
            self.assertGreater(ioc, 1.4)

    def test_polynomial_key_skip_model(self):
        truth, best = self.plant_and_screen("poly:2", "poly2:3,5", "7", 0, 0, ("mults=1",))
        self.assertEqual(best["plant_0"][2], truth["plant_0"])
        self.assertTrue(all(v[0] > 1.4 for v in best.values()))

    def test_random_keys_stay_below_threshold(self):
        with tempfile.TemporaryDirectory() as d:
            tsv = os.path.join(d, "null.tsv")
            self.run_bin("screen", PLAIN, "rand:4:9", tsv, "threads=4")
            self.assertLess(max(v[0] for v in window_bests(tsv).values()), 1.35)

    def test_verify_redecodes_planted_text(self):
        with tempfile.TemporaryDirectory() as d:
            plant = os.path.join(d, "plant.txt")
            self.run_bin("plant", PLAIN, "lin:2", "lin2:2,3", "state=4,9", "1", "0", "0.18", "8", "0", plant)
            out = self.run_bin("verify", plant, "lin:2", "lin2:2,3", "state=4,9", "1", "0", "plant_0").stdout
        self.assertGreater(float(re.search(r"ioc ([\d.]+)", out).group(1)), 1.5)


if __name__ == "__main__":
    unittest.main()
