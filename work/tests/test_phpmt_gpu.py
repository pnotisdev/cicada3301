"""CUDA port of the seeded-PRNG sweep (work/phpmt/gpu.py) against the Rust engine: the gates of docs/GPU_PORT.md.
Skipped when there is no usable CUDA device (the laptop, CI) or no CPU engine to compare with."""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PH = os.path.join(os.path.dirname(HERE), "phpmt")
CPU = os.path.join(PH, "target", "release", "phpmt" + (".exe" if os.name == "nt" else ""))
GPU = os.path.join(PH, "gpu.py")
PROBE = os.path.join(os.path.dirname(HERE), "kscreen", "gpu.py")


def cuda_usable():
    try:
        return subprocess.run([sys.executable, PROBE, "probe"], capture_output=True, timeout=120).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


READY = os.path.exists(CPU) and os.path.exists(os.path.join(PH, "data", "windows.txt")) and cuda_usable()


def rows(path):
    with open(path, encoding="utf-8") as f:
        return [tuple(line.split("\t")) for line in f.read().splitlines()[1:]]


@unittest.skipUnless(READY, "needs a CUDA device with cupy-cuda12x (pip install -r requirements-gpu.txt) and the built CPU engine")
class PhpmtGpu(unittest.TestCase):
    def test_generators_and_scores_match_cpu(self):
        # gate (a), decode by decode: raw outputs of php / glibc / .NET (incl. seeds at 2^31 and 2^32) and the score of
        # every (seed, window, variant)
        r = subprocess.run([sys.executable, GPU, "selfcheck"], cwd=PH, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_sweep_matches_cpu(self):
        # gate (a), aggregates: the score histogram over every decode, and every hit well above noise
        for gen, hi in (("php", 600000), ("glibc", 600000), ("net", 600000)):
            with tempfile.TemporaryDirectory() as d:
                a, b = os.path.join(d, "cpu.tsv"), os.path.join(d, "gpu.tsv")
                c = subprocess.run([CPU, "sweep", gen, "data/windows.txt", "data/dict.txt", "0", str(hi), a, "4"], cwd=PH,
                                   capture_output=True, text=True, check=True)
                g = subprocess.run([sys.executable, GPU, "sweep", gen, "data/windows.txt", "data/dict.txt", "0", str(hi), b,
                                    "4"], cwd=PH, capture_output=True, text=True, check=True)
                hist = lambda s: [ln for ln in s.splitlines() if ln.startswith("hist ")]
                self.assertTrue(hist(c.stderr) and hist(c.stderr) == hist(g.stderr), gen)
                ra, rb = rows(a), rows(b)
                cut = max(int(r[0]) for r in ra[-1:]) + 1            # above the CPU list's own cut-off the lists are complete
                self.assertEqual({r for r in ra if int(r[0]) >= max(cut, 12)}, {r for r in rb if int(r[0]) >= max(cut, 12)}, gen)

    def test_planted_seed_recovered(self):
        # gate (b): a planted seed comes back at rank 1 for all three generators
        for gen, seed, lo, hi, mp, sign, atb in (("php", 777777, 700000, 850000, 0, 1, 0), ("glibc", 424242, 400000, 450000, 1, -1, 1),
                                                 ("net", 31337, 0, 60000, 0, 1, 0)):
            with tempfile.TemporaryDirectory() as d:
                planted, out = os.path.join(d, "planted.txt"), os.path.join(d, "out.tsv")
                subprocess.run([CPU, "plant", gen, "data/english.txt", str(seed), str(mp), "1", str(sign), str(atb), "0.18", planted],
                               cwd=PH, capture_output=True, check=True)
                subprocess.run([sys.executable, GPU, "sweep", gen, planted, "data/dict.txt", str(lo), str(hi), out, "4"], cwd=PH,
                               capture_output=True, check=True)
                r = rows(out)
            self.assertEqual(r[0][1], str(seed), gen)
            self.assertEqual(list(r[0][3:7]), ["1", str(mp), str(sign), str(atb)], gen)
            noise = max([int(x[0]) for x in r if x[1] != str(seed)] or [0])
            self.assertGreater(int(r[0][0]), noise + 10, gen)


if __name__ == "__main__":
    unittest.main()
