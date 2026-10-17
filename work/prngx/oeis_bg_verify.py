#!/usr/bin/env python3
"""Check the best rows of a boundary-free OEIS-lane sweep (`prngx bgsweep seq` on data/oeis_seqs.txt, 36-rune windows): re-decode each row's window with the Python reference
(work/phpmt/bg.py::ref_decode), compare the score with the sweep's own (a reproduction check), print the decoded text, and give the same decode of 8 random sequences of the same length
under the same settings (what a wrong key scores). A true key reads as English and scores about +10 per rune (about +360 over 36 runes); selection noise does not.

    python work/prngx/oeis_bg_verify.py <sweep.tsv> <windows.txt> [--top 8] [--lib data/oeis_seqs.txt]
"""
import argparse
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, WORK)
sys.path.insert(0, os.path.join(WORK, "phpmt"))
import bg  # noqa: E402
import lp  # noqa: E402


def windows(path):
    out, lines = {}, open(path, encoding="utf-8").read().splitlines()
    for k in range(0, len(lines), 3):
        _, name, prev = lines[k].split()
        out[name] = (int(prev), np.array([int(x) for x in lines[k + 1][2:].split()]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tsv")
    ap.add_argument("windows")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--lib", default=os.path.join(HERE, "data", "oeis_seqs.txt"))
    a = ap.parse_args()
    lib = [l.split() for l in open(a.lib, encoding="utf-8")]
    wins = windows(a.windows)
    tbl = bg.load_table()
    rows = [l.rstrip("\n").split("\t") for l in open(a.tsv, encoding="utf-8").read().splitlines()[1:]]
    rng = random.Random(3)
    print(f"# boundary-free check of the best {a.top} rows of {os.path.basename(a.tsv)}: Python reference decode of the window, reported score first; "
          f"'rand' = the same settings on 8 random sequences of the same length")
    seen, k = set(), 0
    for r in rows:
        score, seed, wname, model, mp, sign, atb = r[:7]
        key = (seed, wname, model, mp, sign, atb)
        if key in seen:
            continue
        seen.add(key)
        idx, off = int(seed) // 128, int(seed) % 128
        sid, vals = lib[idx][0], np.array([int(x) for x in lib[idx][1:]])
        prev, runes = wins[wname]
        mult = int(mp) + 1

        def dec(v):
            keys = (v[off:] * mult) % 29
            return bg.ref_decode(runes, prev, keys, int(sign), bool(int(atb)), int(model), tbl, keep_path=True)
        s, plain = dec(vals)
        rnd = [dec(np.array([rng.randrange(29) for _ in range(len(vals))]))[0] for _ in range(8)]
        text = "".join(lp.LATIN[x] for x in plain) if plain is not None else "-"
        print(f"{score}\t{sid} off {off} x{mult} sign {sign} model {model}\t{wname}: reference {s} ({s / len(runes):+.1f} per rune; rand {np.mean(rnd):+.0f} +- {np.std(rnd):.0f}, max {max(rnd)})  {text}")
        k += 1
        if k >= a.top:
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
