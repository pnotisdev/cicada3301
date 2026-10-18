"""Builds work/kscreen/data/library_nonflat.ksb: the library streams that the standalone flat-IoC filter EXCLUDED (library.ksb minus library_flat.ksb).

The H5 sweep so far tests only the 581 streams that pass the filter on their own; a stream plus a keyword has a flatter marginal than the stream alone
(work/independent/frontier/REPORT.md, D2), so the excluded streams are a legitimate second universe. The file is generated per PC (work/kscreen/data/ is git-ignored).
    python jobs/night2_prepare.py
"""
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "work", "kscreen", "data")


def read_ksb(path):
    with open(path, "rb") as f:
        d = f.read()
    assert d[:4] == b"KSB1"
    n = struct.unpack_from("<I", d, 4)[0]
    pos, out = 8, []
    for _ in range(n):
        ln = struct.unpack_from("<H", d, pos)[0]
        pos += 2
        name = d[pos:pos + ln]
        pos += ln
        m = struct.unpack_from("<I", d, pos)[0]
        pos += 4
        out.append((name, d[pos:pos + m]))
        pos += m
    return out


def main():
    full = read_ksb(os.path.join(DATA, "library.ksb"))
    flat = {n for n, _ in read_ksb(os.path.join(DATA, "library_flat.ksb"))}
    rest = [(n, v) for n, v in full if n not in flat]
    out = os.path.join(DATA, "library_nonflat.ksb")
    with open(out, "wb") as f:
        f.write(b"KSB1" + struct.pack("<I", len(rest)))
        for n, v in rest:
            f.write(struct.pack("<H", len(n)) + n + struct.pack("<I", len(v)) + v)
    long_enough = sum(len(v) >= 2407 for _, v in rest)
    print(f"library {len(full)} streams, flat {len(flat)}, non-flat written {len(rest)} ({long_enough} long enough for every offset) -> work/kscreen/data/library_nonflat.ksb")
    return 0 if rest else 1


if __name__ == "__main__":
    sys.exit(main())
