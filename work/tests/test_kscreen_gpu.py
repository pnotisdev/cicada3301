"""CUDA port of the keystream screen (work/kscreen/gpu.py) against the Rust engine: the gates of docs/GPU_PORT.md.
Skipped when there is no usable CUDA device (the laptop, CI) or no CPU engine to compare with."""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
KS = os.path.join(os.path.dirname(HERE), "kscreen")
sys.path.insert(0, KS)
CPU = os.path.join(KS, "target", "release", "kscreen" + (".exe" if os.name == "nt" else ""))
GPU = os.path.join(KS, "gpu.py")


def cuda_usable():
    try:
        return subprocess.run([sys.executable, GPU, "probe"], capture_output=True, timeout=120).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


READY = os.path.exists(CPU) and os.path.exists(os.path.join(KS, "data", "library.ksb")) and cuda_usable()


@unittest.skipUnless(READY, "needs a CUDA device with cupy-cuda12x (pip install -r requirements-gpu.txt) and the built CPU engine")
class KScreenGpu(unittest.TestCase):
    def test_every_decode_matches_cpu(self):
        # gate (a), decode by decode: s and runes used for ~40,000 decodes of every family kind, incl. the fallback kernel
        r = subprocess.run([sys.executable, GPU, "selfcheck"], cwd=KS, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("fallback kernel ran", r.stdout)

    def test_full_screens_match_cpu(self):
        # gate (a), aggregates: decode counts, early aborts, whole IoC histogram, each window's best, the top hits
        import tsvdiff
        cases = [("data/segments.txt", "file:data/library.ksb", ["items=0:6", "mults=1,28"]),
                 ("data/heads.txt", "lin:2", ["mults=1", "items=0:40"]),
                 ("data/pages.txt", "poly:2", ["mults=1"]),
                 ("data/chain/segments_a7.txt", "file:data/library.ksb", ["items=0:4", "mults=1,28"])]   # P lines (chain windows)
        import chain_windows
        if not os.path.exists(os.path.join(KS, "data", "chain", "segments_a7.txt")):
            chain_windows.make(7, "segments")
        with tempfile.TemporaryDirectory() as d:
            for k, (win, fam, extra) in enumerate(cases):
                a, b = os.path.join(d, f"cpu{k}.tsv"), os.path.join(d, f"gpu{k}.tsv")
                subprocess.run([CPU, "screen", win, fam, a, "threads=4", *extra], cwd=KS, capture_output=True, check=True)
                subprocess.run([sys.executable, GPU, "screen", win, fam, b, *extra], cwd=KS, capture_output=True, check=True)
                self.assertEqual(tsvdiff.compare(tsvdiff.parse(a), tsvdiff.parse(b)), [], f"{fam} {extra}")

    def test_planted_keys_recovered_and_null_clean(self):
        # gate (b): the kscreen selftest (15 planted windows, random-key null) through the GPU screen
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "selftest_cuda.txt")
            r = subprocess.run([sys.executable, os.path.join(KS, "selftest.py"), "--engine", "cuda", "--out", out],
                               cwd=KS, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-2000:])
            with open(out, encoding="utf-8") as f:
                self.assertTrue(f.read().rstrip().endswith("SELFTEST PASSED"))


if __name__ == "__main__":
    unittest.main()
