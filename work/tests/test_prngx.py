"""prngx (more PRNG families): generators match real implementations; planted seeds are recovered by a sweep."""
import os
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PX = os.path.join(os.path.dirname(HERE), "prngx")
_EXE = "prngx.exe" if os.name == "nt" else "prngx"
BIN = os.path.abspath(os.environ["PRNGX_BIN"]) if os.environ.get("PRNGX_BIN") else next((p for p in (os.path.join(PX, d, "release", _EXE) for d in ("target", "target_seq"))
                                           if os.path.exists(p)), os.path.join(PX, "target", "release", _EXE))
DATA = os.path.join(os.path.dirname(HERE), "phpmt", "data")


@unittest.skipUnless(os.path.exists(BIN) and os.path.exists(os.path.join(DATA, "english.txt")),
                     "build with: cargo build --release (in work/prngx) and run work/phpmt/export_data.py")
class Prngx(unittest.TestCase):
    def run_bin(self, *args, **env):
        return subprocess.run([BIN, *args], cwd=PX, capture_output=True, text=True, check=True, env=dict(os.environ, **env))

    def test_vectors_match_real_implementations(self):
        out = self.run_bin("vectors", "ref/vectors.txt").stdout
        self.assertIn("0 mismatch", out)
        self.assertNotIn("MISMATCH", out)

    def test_planted_seed_recovered_for_each_generator(self):
        cases = [("mt", 777777, 2, 0, -1, 1), ("pymt", 424242, 5, 1, 1, 0), ("msvc", 31337, 1, 0, 1, 1),
                 ("java", 987654, 1, 1, -1, 0), ("rand48", 123456, 0, 0, 1, 0)]
        with tempfile.TemporaryDirectory() as d:
            for gen, seed, mp, model, sign, atb in cases:
                planted, tsv = os.path.join(d, gen + ".txt"), os.path.join(d, gen + ".tsv")
                self.run_bin("plant", gen, os.path.join(DATA, "english.txt"), str(seed), str(mp), str(model), str(sign),
                             str(atb), "0.18", planted)
                self.run_bin("sweep", gen, planted, os.path.join(DATA, "dict.txt"), str(seed - 3000), str(seed + 3000), tsv, "4")
                with open(tsv, encoding="utf-8") as f:
                    rows = [line.split("\t") for line in f.read().splitlines()[1:]]
                self.assertEqual(rows[0][1], str(seed), gen)
                # the anti-repeat model can tie (a window without a collision does not tell skip from coin)
                self.assertEqual(rows[0][4:7], [str(mp), str(sign), str(atb)], gen)


if __name__ == "__main__":
    unittest.main()
