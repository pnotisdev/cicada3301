"""Hash-seed keystreams for every word and two-word phrase of the solved text (the same construction as export.hash_streams, whose seed list is
only ~65 Cicada strings): sha256 / sha512 / md5 counter streams and the sha256 chain, each reduced mod 29 and by rejection, for the seed in upper and in
lower case. About 13,000 streams of 20,000 values.

    python work/kscreen/export_hashwords.py          # -> data/library_hashwords.ksb (git-ignored build output)
"""
import hashlib
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, WORK)
import keystreams  # noqa: E402

N = 29
L = keystreams.LEN
NEED = L * 2


def seeds():
    out = []
    for name in keystreams.keywords():
        w = name[3:]
        for s in (w, w.lower()):
            if s not in out:
                out.append(s)
    return out


def streams(sb, label):
    raw_by = {}
    for hn, H in (("sha256", hashlib.sha256), ("sha512", hashlib.sha512), ("md5", hashlib.md5)):
        raw, i = bytearray(), 0
        while len(raw) < NEED:
            raw += H(sb + i.to_bytes(4, "big")).digest()
            i += 1
        raw_by[f"{hn}-ctr"] = bytes(raw)
    raw, x = bytearray(), hashlib.sha256(sb).digest()
    while len(raw) < NEED:
        raw += x
        x = hashlib.sha256(x).digest()
    raw_by["sha256-chain"] = bytes(raw)
    for gname, raw in raw_by.items():
        b = np.frombuffer(raw, dtype=np.uint8).astype(np.int64)
        yield f"{gname} mod :{label}", (b % N)[:L]
        yield f"{gname} reject :{label}", (b[b < 232] % N)[:L]


def main():
    ss = seeds()
    path = os.path.join(HERE, "data", "library_hashwords.ksb")
    n = 0
    with open(path, "wb") as f:
        f.write(b"KSB1" + struct.pack("<I", len(ss) * 8))
        for s in ss:
            for name, v in streams(s.encode(), s):
                nb = name.encode("utf-8")[:300]
                f.write(struct.pack("<H", len(nb)) + nb + struct.pack("<I", len(v)) + bytes(np.asarray(v, dtype=np.uint8)))
                n += 1
    assert n == len(ss) * 8, (n, len(ss))
    print(f"wrote {n} hash streams for {len(ss)} seeds to data/library_hashwords.ksb")
    return 0


if __name__ == "__main__":
    sys.exit(main())
