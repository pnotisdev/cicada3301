"""Boundary-free mode of hashscan (bgsweep / bgscores): the Rust decoder equals the Python reference (work/phpmt/bg.py::ref_decode) on keys built
from hashlib, a planted passphrase is recovered at rank 1, and random strings give no score near a true key."""
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(WORK, "phpmt"))
sys.path.insert(0, WORK)

import bg  # noqa: E402

HS = os.path.join(WORK, "hashscan")
_EXE = "hashscan.exe" if os.name == "nt" else "hashscan"
BIN = os.path.abspath(os.environ["HASHSCAN_BIN"]) if os.environ.get("HASHSCAN_BIN") else os.path.join(HS, "target", "release", _EXE)
DATA = os.path.join(WORK, "phpmt", "data")
TABLE = os.path.join(DATA, "bigram.txt")
NEED = 200


def stream(algo, conv, s, n):
    H = [hashlib.md5, hashlib.sha1, hashlib.sha256, hashlib.sha512][algo]
    out = b""
    if conv == 3:
        x = H(s).digest()
        while len(out) < n:
            out += x
            x = H(x).digest()
    else:
        ctr = 1 if conv == 2 else 0
        while len(out) < n:
            out += H(s + (ctr.to_bytes(4, "big") if conv == 0 else str(ctr).encode())).digest()
            ctr += 1
    return out[:n]


def keys_of(b, mp, limit=160):
    out = []
    for x in b:
        if len(out) >= limit:
            break
        if mp == 0:
            out.append(x % 29)
        elif mp == 1:
            out.append((x * 29) >> 8)
        elif x < 232:
            out.append(x % 29)
    return out


def read_first_window(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    prev = int(lines[0].split()[2])
    return prev, [int(x) for x in lines[1][2:].split()][:bg.NR]


@unittest.skipUnless(os.path.exists(BIN) and os.path.exists(TABLE), "build with cargo build --release in work/hashscan and run work/phpmt/bg.py table")
class HashscanBg(unittest.TestCase):
    def run_bin(self, *args):
        return subprocess.run([BIN, *args], cwd=HS, capture_output=True, text=True, check=True, encoding="utf-8")

    def test_rust_scores_equal_the_python_reference(self):
        tbl = bg.load_table()
        win = os.path.join(DATA, "windows_07.txt")
        prev, runes = read_first_window(win)
        for cand in ("cicada", "3301", "the primes are sacred"):
            got = {}
            for line in self.run_bin("bgscores", cand, win, TABLE).stdout.splitlines():
                a, c, m, sub, sc = (int(x) for x in line.split())
                got[(a, c, m, sub)] = sc
            self.assertEqual(len(got), 4 * 4 * 3 * 8)
            for (a, c, m, sub), sc in got.items():
                model, sign, atb = (sub >> 2) & 1, 1 if (sub >> 1) & 1 == 0 else -1, bool(sub & 1)
                ref, _ = bg.ref_decode(runes, prev, keys_of(stream(a, c, cand.encode(), NEED), m), sign, atb, model, tbl, bg.ABORT_AT, bg.ABORT_THR)
                self.assertEqual(sc, ref, (cand, a, c, m, sub))

    def test_planted_passphrase_is_recovered_and_random_strings_are_not(self):
        cases = [("cicada3301", 2, 1, 0, 0, 1, 0), ("the primes are sacred", 3, 0, 2, 1, -1, 1), ("emergence", 0, 3, 1, 0, 1, 1)]
        with tempfile.TemporaryDirectory() as d:
            cands = os.path.join(d, "cands.txt")
            with open(cands, "w", newline="\n", encoding="utf-8") as f:
                f.write("\n".join([f"word{i}" for i in range(3000)] + [c[0] for c in cases]) + "\n")
            for cand, algo, conv, mp, model, sign, atb in cases:
                planted, tsv = os.path.join(d, "p.txt"), os.path.join(d, "o.tsv")
                self.run_bin("plant", str(algo), str(conv), str(mp), str(model), str(sign), str(atb), "0.18", cand,
                             os.path.join(DATA, "english.txt"), planted)
                self.run_bin("bgsweep", cands, planted, TABLE, tsv, "4")
                rows = [line.split("\t") for line in open(tsv, encoding="utf-8").read().splitlines()[1:]]
                self.assertEqual(rows[0][1], cand)
                self.assertEqual(rows[0][3:6], [str(algo), str(conv), str(mp)])
                self.assertGreater(int(rows[0][0]), 300)
                others = [int(r[0]) for r in rows if r[1] != cand]
                self.assertLess(max(others or [-999]), 150)


if __name__ == "__main__":
    unittest.main()
