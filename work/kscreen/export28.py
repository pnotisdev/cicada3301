"""A keystream library whose values are NATIVE mod 28 (for the step-domain variants A and C, whose key lives in Z28): the same families as
export.py (number sequences, constants' digits in base 28, hash streams of the Cicada strings, solved-text keywords) built with the alphabet
size patched to 28, so that for example sha256-counter bytes are reduced mod 28 and primes mod 28 instead of being reduced mod 29 and then
mod 28 again by step28.py.

    python work/kscreen/export28.py            # -> data/library28.ksb   (git-ignored build output, like library.ksb)
"""
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, WORK)
sys.path.insert(0, HERE)
import export  # noqa: E402
import keystreams  # noqa: E402

NC = 28


def build():
    export.N = NC            # export.arr and the hash/digit builders read the module-level alphabet size
    keystreams.N = NC        # so do the number families of keystreams.py
    ks = export.library()
    out = {}
    for name, v in ks.items():
        v = np.asarray(v, dtype=np.int64) % NC
        out[name] = v
    return out


def write(path, ks):
    with open(path, "wb") as f:
        f.write(b"KSB1" + struct.pack("<I", len(ks)))
        for name, v in ks.items():
            p = keystreams.period(v, max_p=5000, probe=min(3000, len(v) // 2))
            if p:
                v = v[:p + export.KEEP]
            nb = name.encode("utf-8")[:300]
            f.write(struct.pack("<H", len(nb)) + nb + struct.pack("<I", len(v)) + bytes(v.astype(np.uint8)))


def main():
    ks = build()
    path = os.path.join(HERE, "data", "library28.ksb")
    write(path, ks)
    print(f"wrote {len(ks)} streams with values 0..{NC - 1} to data/library28.ksb")
    return 0


if __name__ == "__main__":
    sys.exit(main())
