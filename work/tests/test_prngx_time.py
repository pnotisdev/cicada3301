"""prng-time (work/prngx/time_campaign.py): generators seeded with millisecond timestamps. Java's 48-bit seeds and CPython's
two-word seeds match independent implementations, planted timestamp seeds are recovered at rank 1 by the boundary-free
sweep with the campaign's map settings, random ciphertext gives no candidate, and the whole-section check confirms a plant
and rejects a chance row."""
import os
import random
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
PX = os.path.join(WORK, "prngx")
DATA = os.path.join(WORK, "phpmt", "data")
_EXE = "prngx.exe" if os.name == "nt" else "prngx"
_CANDS = [os.path.join(PX, d, "release", _EXE) for d in ("target", "target_time")]
BIN = os.path.abspath(os.environ["PRNGX_BIN"]) if os.environ.get("PRNGX_BIN") else max(
    [p for p in _CANDS if os.path.exists(p)] or [_CANDS[0]], key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0)
sys.path.insert(0, PX)


def rows(tsv):
    with open(tsv, encoding="utf-8") as f:
        return [line.split("\t") for line in f.read().splitlines()[1:] if line.strip()]


@unittest.skipUnless(os.path.exists(BIN) and os.path.exists(os.path.join(DATA, "bigram.txt")),
                     "build with cargo build --release (in work/prngx) and run work/phpmt/export_data.py and work/phpmt/bg.py table")
class PrngTime(unittest.TestCase):
    def run_bin(self, *args, **env):
        return subprocess.run([BIN, *args], cwd=PX, capture_output=True, text=True, check=True, env=dict(os.environ, **env))

    def test_vectors_including_millisecond_seeds(self):
        out = self.run_bin("vectors", "ref/vectors.txt").stdout
        self.assertIn(" 0 mismatch", out)
        with open(os.path.join(PX, "ref", "vectors.txt"), encoding="utf-8") as f:
            text = f.read()
        self.assertIn("pymt 1388534400000 raw", text)
        self.assertIn("java 1388534400000 0", text)

    def test_engine_keys_equal_independent_keys(self):
        """`prngx keys` against CPython's random.Random and the java.util.Random specification (time_verify.keys)"""
        import time_verify
        for gen, seed, mp in (("java", 1388534412345, 0), ("java", 1370000004242, 1), ("java", -2014, 2), ("pymt", 1389052800777, 2),
                              ("pymt", 4294967296, 3), ("pymt", 1325400000123, 5), ("pymt", -1388534400000, 2), ("pymt", 3301, 2)):
            got = [int(x) for x in self.run_bin("keys", gen, str(seed), str(mp), "200").stdout.split()]
            self.assertEqual(got, [int(x) for x in time_verify.keys(gen, seed, mp, 200)], (gen, seed, mp))

    def plant_and_sweep(self, d, gen, seed, mp, model, sign, atb, maps):
        planted, tsv = os.path.join(d, f"{gen}.txt"), os.path.join(d, f"{gen}.tsv")
        self.run_bin("plant", gen, os.path.join(DATA, "english.txt"), str(seed), str(mp), str(model), str(sign), str(atb),
                     "0.18", planted)
        self.run_bin("bgsweep", gen, planted, os.path.join(DATA, "bigram.txt"), str(seed - 3000), str(seed + 3000), tsv, "4",
                     PRNGX_MAPS=maps)
        return planted, tsv

    def test_planted_timestamp_seeds_recovered(self):
        import time_campaign
        with tempfile.TemporaryDirectory() as d:
            for gen, seed, mp, model, sign, atb in (("java", 1388534412345, 0, 0, 1, 0), ("pymt", 1389052800777, 2, 1, -1, 0),
                                                    ("pymt", 1325400000123, 5, 0, 1, 1)):
                _, tsv = self.plant_and_sweep(d, gen, seed, mp, model, sign, atb, time_campaign.MAPS[gen])
                top = rows(tsv)[0]
                self.assertEqual(top[1], str(seed), gen)
                self.assertEqual(top[4:7], [str(mp), str(sign), str(atb)], gen)
                self.assertGreaterEqual(int(top[0]), 300, gen)

    def test_random_ciphertext_gives_no_candidate(self):
        rng = random.Random(29)
        with tempfile.TemporaryDirectory() as d:
            win = os.path.join(d, "random.txt")
            with open(win, "w", newline="\n", encoding="utf-8") as f:
                for w in range(3):
                    c = [rng.randrange(29)]
                    while len(c) < 400:
                        y = rng.randrange(29)
                        if y != c[-1] or rng.random() > 0.8:
                            c.append(y)
                    f.write(f"W random_{w} -1\nR {' '.join(map(str, c))}\nL {' '.join(['4'] * 100)}\n")
            for gen in ("java", "pymt"):
                tsv = os.path.join(d, f"null_{gen}.tsv")
                self.run_bin("bgsweep", gen, win, os.path.join(DATA, "bigram.txt"), "1388534400000", "1388534420000", tsv, "4")
                best = max((int(r[0]) for r in rows(tsv)), default=-1)
                self.assertLess(best, 300, gen)

    def test_whole_section_check_confirms_plant_and_rejects_noise(self):
        import time_verify
        with tempfile.TemporaryDirectory() as d:
            planted, tsv = self.plant_and_sweep(d, "java", 1388534412345, 0, 0, 1, 0, "0,1,2")
            top = rows(tsv)[0]
            # the true row, then the same setting with a neighbouring (wrong) seed
            check = os.path.join(d, "check.tsv")
            with open(check, "w", newline="\n", encoding="utf-8") as f:
                f.write("score\tseed\twindow\tmodel\tmap\tsign\tatbash\n")
                f.write("\t".join(top[:7]) + "\n")
                f.write("\t".join([top[0], str(int(top[1]) + 1)] + top[2:7]) + "\n")
            lines = []
            n = time_verify.verify(check, "java", top=2, controls=4, out=lines.append, plant=planted)
            self.assertEqual(n, 1)
            self.assertTrue(lines[1].startswith("CANDIDATE") and "seed 1388534412345" in lines[1])
            self.assertTrue(lines[2].startswith("noise") and "seed 1388534412346" in lines[2])


if __name__ == "__main__":
    unittest.main()
