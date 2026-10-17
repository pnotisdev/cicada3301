#!/usr/bin/env python3
"""Whole-section check of the best candidates of a hashscan `bgsweep` (boundary-free score): rebuild the candidate's hash stream with Python's hashlib
(independent of the Rust code), decode the WHOLE section with the bigram beam of work/phpmt/bg.py and compare the score per rune with the same decode of
8 random strings. A true key keeps about +10 per rune over the section, a wrong one about -12.

    python work/hashscan/bg_verify.py results/hashscan/bg_<tier>.tsv [--top 10]
"""
import argparse
import hashlib
import os
import random
import re
import string
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
sys.path.insert(0, str(WORK))
sys.path.insert(0, str(WORK / "phpmt"))
import bg  # noqa: E402
import lp  # noqa: E402
import stats  # noqa: E402


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


def keys_of(b, mp, limit):
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
    return np.array(out)


def whole(cand, algo, conv, mp, model, sign, atb, runes, prev, tbl):
    key = keys_of(stream(algo, conv, cand.encode(), 12 * len(runes)), mp, 3 * len(runes) + 60)
    s, _ = bg.ref_decode(runes, prev, key, sign, bool(atb), model, tbl)
    return s / len(runes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tsv")
    ap.add_argument("--top", type=int, default=10)
    a = ap.parse_args()
    tbl = bg.load_table()
    rows = [l.split("\t") for l in Path(a.tsv).read_text(encoding="utf-8").splitlines()[1:] if l.strip()]
    rel = os.path.relpath(a.tsv, WORK.parent).replace(os.sep, "/")
    print(f"# boundary-free whole-section check of the best {min(a.top, len(rows))} candidates of {rel}: bigram score per rune over the whole section "
          "(a true key keeps about +10 per rune, a wrong one about -12), against 8 random strings of the same kind")
    rng = random.Random(1)
    for score, cand, window, algo, conv, mp, model, sign, atb in rows[:a.top]:
        sec = int(re.match(r"seg0\.(\d+)", window).group(1))
        runes = np.array(lp.runes_of(stats.SEGS[sec]))
        prev = int(lp.runes_of(stats.SEGS[sec - 1])[-1]) if sec > 7 else -1
        args = (int(algo), int(conv), int(mp), int(model), int(sign), int(atb), runes, prev, tbl)
        real = whole(cand, *args)
        rnd = [whole("".join(rng.choice(string.ascii_lowercase) for _ in range(8)), *args) for _ in range(8)]
        print(f"{score}\t{cand!r}\talgo {algo} conv {conv} map {mp} model {model} sign {sign} atb {atb}: {real:+.2f} per rune over {len(runes)} runes "
              f"(random strings {np.mean(rnd):+.2f} +- {np.std(rnd):.2f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
