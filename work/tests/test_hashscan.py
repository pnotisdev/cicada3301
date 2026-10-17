"""hashscan: hash streams match Python's hashlib; planted passphrases are recovered by a sweep."""
import hashlib
import os
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HS = os.path.join(os.path.dirname(HERE), "hashscan")
_EXE = "hashscan.exe" if os.name == "nt" else "hashscan"
BIN = os.path.abspath(os.environ["HASHSCAN_BIN"]) if os.environ.get("HASHSCAN_BIN") else os.path.join(HS, "target", "release", _EXE)
DATA = os.path.join(os.path.dirname(HERE), "phpmt", "data")


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


@unittest.skipUnless(os.path.exists(BIN) and os.path.exists(os.path.join(DATA, "english.txt")),
                     "build with: cargo build --release (in work/hashscan) and run work/phpmt/export_data.py")
class Hashscan(unittest.TestCase):
    def run_bin(self, *args):
        return subprocess.run([BIN, *args], cwd=HS, capture_output=True, text=True, check=True, encoding="utf-8")

    def test_streams_match_hashlib(self):
        for line in self.run_bin("vectors").stdout.splitlines():
            a, c, *v = line.split()
            self.assertEqual([int(x) for x in v], list(stream(int(a), int(c), b"cicada", 40)), (a, c))

    def test_planted_passphrase_recovered(self):
        cases = [("cicada3301", 2, 1, 0, 0, 1, 0), ("the primes are sacred", 3, 0, 2, 1, -1, 1), ("emergence", 0, 3, 1, 0, 1, 1)]
        with tempfile.TemporaryDirectory() as d:
            cands = os.path.join(d, "cands.txt")
            with open(cands, "w", newline="\n", encoding="utf-8") as f:
                f.write("\n".join([f"word{i}" for i in range(3000)] + [c[0] for c in cases]) + "\n")
            for cand, algo, conv, mp, model, sign, atb in cases:
                planted, tsv = os.path.join(d, "p.txt"), os.path.join(d, "o.tsv")
                self.run_bin("plant", str(algo), str(conv), str(mp), str(model), str(sign), str(atb), "0.18", cand,
                             os.path.join(DATA, "english.txt"), planted)
                self.run_bin("sweep", cands, planted, os.path.join(DATA, "dict.txt"), tsv, "4")
                with open(tsv, encoding="utf-8") as f:
                    rows = [line.split("\t") for line in f.read().splitlines()[1:]]
                self.assertEqual(rows[0][1], cand)
                self.assertEqual(rows[0][3:6], [str(algo), str(conv), str(mp)])


if __name__ == "__main__":
    unittest.main()
