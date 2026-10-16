"""PHP legacy mt_rand engine (work/phpmt): bit-exact against PHP, and recovers a planted seed."""
import os
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PHPMT = os.path.join(os.path.dirname(HERE), "phpmt")
_EXE = "phpmt.exe" if os.name == "nt" else "phpmt"
# target_gen holds the multi-generator build (php / glibc / net); target is the original php-only build
BIN = next((p for p in (os.path.join(PHPMT, "target_gen", "release", _EXE), os.path.join(PHPMT, "target", "release", _EXE))
            if os.path.exists(p)), os.path.join(PHPMT, "target", "release", _EXE))


@unittest.skipUnless(os.path.exists(BIN), "build with: cargo build --release (in work/phpmt)")
class PhpMt(unittest.TestCase):
    def run_bin(self, *args):
        return subprocess.run([BIN, *args], cwd=PHPMT, capture_output=True, text=True, check=True)

    def test_legacy_generator_matches_php(self):
        out = self.run_bin("vectors", "ref/vectors.txt").stdout
        self.assertNotIn("MISMATCH php", out)  # legacy (MT_RAND_PHP) raw and mt_rand(0,28)
        self.assertNotIn("MISMATCH mt 0 raw", out)  # reference MT19937 raw output too

    def test_glibc_and_dotnet_generators_match_references(self):
        out = self.run_bin("vectors_other", "ref/net_vectors.txt").stdout
        self.assertIn(".NET vectors: 33 match, 0 mismatch", out)
        self.assertIn("glibc srandom(1): match (seed 0 == seed 1: true; fast path: true)", out)

    def test_planted_seed_recovered(self):
        with tempfile.TemporaryDirectory() as d:
            planted = os.path.join(d, "planted.txt")
            out = os.path.join(d, "out.tsv")
            self.run_bin("plant", "php", "data/english.txt", "777777", "0", "1", "-1", "0", "0.18", planted)
            self.run_bin("sweep", "php", planted, "data/dict.txt", "700000", "850000", out, "4")
            with open(out) as f:
                rows = [line.split("\t") for line in f.read().splitlines()[1:]]
        self.assertEqual(rows[0][1], "777777")
        self.assertEqual(rows[0][3:7], ["1", "0", "-1", "0"])  # model, map, sign, atbash
        noise = max(int(r[0]) for r in rows if r[1] != "777777")
        self.assertGreater(int(rows[0][0]), noise + 10)


if __name__ == "__main__":
    unittest.main()
