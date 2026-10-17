"""Boundary-free mode of prngx (bgsweep / bgscore): the Rust decoder equals the Python reference (work/phpmt/bg.py::ref_decode) on keys built by independent
code (numpy / CPython for the two Mersenne families, a Python LCG for MSVC), and planted seeds are recovered at rank 1 for every generator."""
import os
import random
import subprocess
import sys
import tempfile
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(WORK, "phpmt"))
sys.path.insert(0, WORK)

import bg  # noqa: E402

PX = os.path.join(WORK, "prngx")
_EXE = "prngx.exe" if os.name == "nt" else "prngx"
BIN = os.path.abspath(os.environ["PRNGX_BIN"]) if os.environ.get("PRNGX_BIN") else next(
    (p for p in (os.path.join(PX, d, "release", _EXE) for d in ("target", "target_seq")) if os.path.exists(p)), os.path.join(PX, "target", "release", _EXE))
DATA = os.path.join(WORK, "phpmt", "data")
TABLE = os.path.join(DATA, "bigram.txt")


def raw_mt(seed, n):
    return [int(x) for x in np.random.RandomState(seed).randint(0, 2 ** 32, size=n, dtype=np.uint32)]


def raw_pymt(seed, n):
    random.seed(seed)
    return [random.getrandbits(32) for _ in range(n)]


def raw_msvc(seed, n):
    x, out = seed, []
    for _ in range(n):
        x = (x * 214013 + 2531011) & 0xFFFFFFFF
        out.append((x >> 16) & 0x7FFF)
    return out


def read_first_window(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    return int(lines[0].split()[2]), [int(x) for x in lines[1][2:].split()][:bg.NR]


@unittest.skipUnless(os.path.exists(BIN) and os.path.exists(TABLE), "build with cargo build --release in work/prngx and run work/phpmt/bg.py table")
class PrngxBg(unittest.TestCase):
    def run_bin(self, *args, **env):
        return subprocess.run([BIN, *args], cwd=PX, capture_output=True, text=True, check=True, env=dict(os.environ, **env), encoding="utf-8")

    def test_rust_scores_equal_the_python_reference(self):
        tbl = bg.load_table()
        win = os.path.join(DATA, "windows_07.txt")
        prev, runes = read_first_window(win)
        cases = [("mt", raw_mt, 0, lambda r: r % 29), ("pymt", raw_pymt, 0, lambda r: r % 29),
                 ("msvc", raw_msvc, 0, lambda r: r % 29), ("msvc", raw_msvc, 1, lambda r: (r * 29) >> 15)]
        for gen, rawf, mp, fn in cases:
            for seed in (12345, 777777):
                keys = [fn(r) for r in rawf(seed, 400)][:160]
                for model, sign, atb in ((0, 1, 0), (1, -1, 1), (0, -1, 0), (1, 1, 1)):
                    got = int(self.run_bin("bgscore", gen, win, TABLE, str(seed), str(mp), str(model), str(sign), str(atb)).stdout.split()[0])
                    ref, _ = bg.ref_decode(runes, prev, keys, sign, bool(atb), model, tbl, bg.ABORT_AT, bg.ABORT_THR)
                    self.assertEqual(got, ref, (gen, seed, mp, model, sign, atb))

    def test_planted_seed_is_recovered_for_each_generator(self):
        cases = [("mt", 777777, 2, 0, -1, 1), ("pymt", 424242, 5, 1, 1, 0), ("msvc", 31337, 1, 0, 1, 1), ("java", 987654, 1, 1, -1, 0),
                 ("rand48", 123456, 0, 0, 1, 0)]
        with tempfile.TemporaryDirectory() as d:
            for gen, seed, mp, model, sign, atb in cases:
                planted, tsv = os.path.join(d, gen + ".txt"), os.path.join(d, gen + ".tsv")
                self.run_bin("plant", gen, os.path.join(DATA, "english.txt"), str(seed), str(mp), str(model), str(sign), str(atb), "0.18", planted)
                self.run_bin("bgsweep", gen, planted, TABLE, str(seed - 3000), str(seed + 3000), tsv, "4")
                rows = [line.split("\t") for line in open(tsv, encoding="utf-8").read().splitlines()[1:]]
                self.assertEqual(rows[0][1], str(seed), gen)
                self.assertEqual(rows[0][4:7], [str(mp), str(sign), str(atb)], gen)
                self.assertGreater(int(rows[0][0]), 300)
                others = [int(r[0]) for r in rows if r[1] != str(seed)]
                self.assertLess(max(others or [-999]), 150, gen)


    def test_kdf_pipeline_recovers_a_planted_rc4_passphrase(self):
        """the laptop's KDF lane (RC4 / AES / PBKDF2 ... streams of passphrases) scored without word separators"""
        sys.path.insert(0, PX)
        import kdf_streams as ks
        with tempfile.TemporaryDirectory() as d:
            planted, lib, tsv = (os.path.join(d, n) for n in ("planted.txt", "lib.txt", "out.tsv"))
            ks.plant("cicada3301", "rc4", 0, planted)
            cands = [f"word{i}" for i in range(15)] + ["cicada3301"]
            with open(lib, "w", newline="\n") as f, open(lib + ".index", "w", newline="\n", encoding="utf-8") as ix:
                n = 0
                for idx, cand in enumerate(cands):
                    _, _, rows = ks.one((idx, cand))
                    for name, v in rows:
                        f.write(f"S{n} " + " ".join(map(str, v)) + "\n")
                        ix.write(f"{n}\t{cand}\t{name.split(':', 1)[1]}\n")
                        n += 1
            self.run_bin("bgsweep", "seq", planted, TABLE, "0", str(n * 128), tsv, "4", PRNGX_SEQ=lib, PRNGX_SEQ_OFFMAX="1")
            with open(tsv, encoding="utf-8") as f:
                rows = [line.split("\t") for line in f.read().splitlines()[1:]]
            with open(lib + ".index", encoding="utf-8") as f:
                idx = {int(a): (b, c) for a, b, c in (l.split("\t") for l in f.read().splitlines())}
            self.assertEqual(idx[int(rows[0][1]) // 128], ("cicada3301", "rc4:0"))
            self.assertGreater(int(rows[0][0]), 300)


if __name__ == "__main__":
    unittest.main()
