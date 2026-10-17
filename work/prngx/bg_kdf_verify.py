#!/usr/bin/env python3
"""Whole-section check of the best rows of a boundary-free KDF-lane sweep (`prngx bgsweep seq` on the library written by kdf_streams.py build): rebuild the
candidate's stream with kdf_streams.stream (long: 3x the section), decode the WHOLE section with the bigram beam (work/phpmt/bg.py) and compare with the same decode
of 8 random strings. A true key keeps about +10 per rune; a wrong one about -10.5.

    python work/prngx/bg_kdf_verify.py <lib.txt.tsv> [--top 10]
"""
import argparse
import os
import random
import string
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
ROOT = os.path.dirname(WORK)
sys.path.insert(0, HERE)
sys.path.insert(0, WORK)
sys.path.insert(0, os.path.join(WORK, "phpmt"))
import bg  # noqa: E402
import kdf_streams as ks  # noqa: E402
import lp  # noqa: E402
import stats  # noqa: E402


def keys_for(tag, cand, mp, n):
    b = ks.stream(tag, cand.encode("utf-8"), 12 * n)
    v = [x % 29 for x in b] if mp == 0 else [x % 29 for x in b if x < 232]
    return np.array(v[:3 * n + 60])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tsv")
    ap.add_argument("--top", type=int, default=10)
    a = ap.parse_args()
    lib = a.tsv[:-4]
    index = {}
    with open(lib + ".index", encoding="utf-8") as f:
        for line in f:
            n, cand, tm = line.rstrip("\n").split("\t")
            index[int(n)] = (cand, tm)
    with open(a.tsv, encoding="utf-8") as f:
        rows = [l.rstrip("\n").split("\t") for l in f.read().splitlines()[1:]]
    tbl = bg.load_table()
    runes = np.array(lp.runes_of(stats.SEGS[7]))
    print(f"# boundary-free whole-section check of the best {min(a.top, len(rows))} KDF-lane rows of {os.path.basename(a.tsv)}: bigram score per rune over "
          f"{len(runes)} runes of section 0.7 (a true key keeps about +10, a wrong one about -10.5), against 8 random strings through the same stream and map")
    rng = random.Random(7)
    seen, k = set(), 0
    for r in rows:
        score, seed, win, model, mp_mult, sign, atb = r[:7]
        cand, tm = index[int(seed) // 128]
        tag, mpi = tm.rsplit(":", 1)
        key = (cand, tm, model, mp_mult, sign, atb)
        if key in seen:
            continue
        seen.add(key)
        mult = int(mp_mult) + 1                       # the seq generator's map is multiplier - 1

        def whole(c):
            keys = (keys_for(tag, c, int(mpi), len(runes)) * mult) % 29
            s, _ = bg.ref_decode(runes, -1, keys, int(sign), bool(int(atb)), int(model), tbl)
            return s / len(runes)

        real = whole(cand)
        rnd = [whole("".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randrange(5, 12)))) for _ in range(8)]
        print(f"{score}\t{cand[:30]!r}\t{tag} map {mpi} mult {mult} model {model} sign {sign} atb {atb}: {real:+.2f} per rune "
              f"(random strings {np.mean(rnd):+.2f} +- {np.std(rnd):.2f})")
        k += 1
        if k >= a.top:
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
