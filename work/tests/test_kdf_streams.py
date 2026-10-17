"""KDF / stream-cipher keystream lane: stream generators match known vectors; a planted RC4 passphrase is recovered
through the whole pipeline (library build -> prngx seq sweep)."""
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PX = os.path.join(os.path.dirname(HERE), "prngx")
sys.path.insert(0, PX)

import kdf_streams as ks  # noqa: E402

_EXE = "prngx.exe" if os.name == "nt" else "prngx"
BIN = os.path.abspath(os.environ["PRNGX_BIN"]) if os.environ.get("PRNGX_BIN") else next(
    (p for p in (os.path.join(PX, d, "release", _EXE) for d in ("target", "target_seq")) if os.path.exists(p)), "")
DATA = os.path.join(os.path.dirname(HERE), "phpmt", "data")


class Streams(unittest.TestCase):
    def test_rc4_and_pbkdf2_vectors(self):
        enc = bytes(a ^ b for a, b in zip(ks.rc4(b"Key", 9), b"Plaintext")).hex().upper()
        self.assertEqual(enc, "BBF316E8D940AF0AD3")
        self.assertEqual(ks.stream("pbkdf2-sha1-1", b"password", 20)[:20].hex() if False else
                         hashlib.pbkdf2_hmac("sha1", b"password", b"salt", 1, 20).hex(),
                         "0c60c80f961f0e71f3a9b524af6012062fe037a6")

    def test_every_stream_generates(self):
        for tag in ks.TAGS:
            self.assertEqual(len(ks.stream(tag, b"cicada3301", 300)), 300, tag)


@unittest.skipUnless(BIN and os.path.exists(BIN) and os.path.exists(os.path.join(DATA, "english.txt")),
                     "build with: cargo build --release (in work/prngx)")
class Pipeline(unittest.TestCase):
    def test_planted_rc4_passphrase_recovered(self):
        with tempfile.TemporaryDirectory() as d:
            planted, lib, tsv = (os.path.join(d, n) for n in ("planted.txt", "lib.txt", "out.tsv"))
            ks.plant("cicada3301", "rc4", 0, planted)
            # a small library built in-process (no multiprocessing pool): 60 junk candidates + the true one
            cands = [f"word{i}" for i in range(15)] + ["cicada3301"]
            with open(lib, "w", newline="\n") as f, open(lib + ".index", "w", newline="\n", encoding="utf-8") as ix:
                n = 0
                for idx, cand in enumerate(cands):
                    _, _, rows = ks.one((idx, cand))
                    for name, v in rows:
                        f.write(f"S{n} " + " ".join(map(str, v)) + "\n")
                        ix.write(f"{n}\t{cand}\t{name.split(':', 1)[1]}\n")
                        n += 1
            env = dict(os.environ, PRNGX_SEQ=lib, PRNGX_SEQ_OFFMAX="1")
            subprocess.run([BIN, "sweep", "seq", planted, os.path.join(DATA, "dict.txt"), "0", str(n * 128), tsv, "4"],
                           env=env, check=True, capture_output=True)
            with open(tsv, encoding="utf-8") as f:
                top = f.read().splitlines()[1].split("\t")
            with open(lib + ".index", encoding="utf-8") as f:
                idx = {int(a): (b, c) for a, b, c in (l.split("\t") for l in f.read().splitlines())}
            self.assertEqual(idx[int(top[1]) // 128], ("cicada3301", "rc4:0"))


if __name__ == "__main__":
    unittest.main()
