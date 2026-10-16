"""Key-restart test by column coincidences (two-time-pad / shared-key-start detector).

Hypothesis: the key (or its PRNG seed) restarts at the beginning of every structural unit: page, line,
paragraph, sentence, word, segment. Then the j-th rune of every unit was enciphered with (almost) the same key
value k_j, so c = p + k_j puts all j-th runes in one "column" whose runes differ only by plaintext differences.
English plaintext makes equal pairs in a column about 1.8x as frequent as chance (rune IoC 1.8). With many
units the column test is far stronger than any pairwise test: 56 pages give 1,540 pairs per column.

Under the anti-repeat skip rule the key pointer drifts ahead of the rune index by about 0.028 per rune, so the
columns stay aligned for the first ~20-40 runes of a unit and then blur. The test therefore looks at the first
J columns, counted from the start of the unit and (key running backwards) from its end.

Statistic: for column j, X = number of equal pairs among the n_j runes. Under the null (runes drawn from the
global rune distribution f) E[X] = C(n,2) S and Var[X] = C(n,2)(S-S^2) + n(n-1)(n-2)(T-S^2) with S = sum f^2,
T = sum f^3 (exact for the multinomial). z_j = (X - E)/sd. Summaries: the maximum z over columns, and
Z_sum = sum_{j<J0} z_j / sqrt(J0).

    python work/restart_columns.py              # LP2 + positive controls + null controls
    python work/restart_columns.py --quick
"""
import argparse
import os
import random
import sys
from math import comb, sqrt

import numpy as np

import lp
import sim
import stats

N = lp.N
HERE = os.path.dirname(os.path.abspath(__file__))
J = 60
J0 = 20


def units_of(kind, segs, idxs):
    """List of rune lists, one per unit, for one structural boundary type."""
    seps = {
        "segment": set(),
        "page": {"%"},
        "paragraph": {"%", "&"},
        "line": {"%", "&", "\n"},
        "sentence": {"%", "&", "."},              # '.' is the transcription's clause separator
        # a bare line break inside a word is a typographic wrap, not a word boundary (see lp.word_spans)
        "word": {"%", "&", " ", "."},
    }[kind]
    out = []
    for i in idxs:
        cur = []
        for t in segs[i]:
            if isinstance(t, int):
                cur.append(t)
            elif t in seps:
                if cur:
                    out.append(cur)
                cur = []
        if cur:
            out.append(cur)
    return out


def column_stats(units, freq, reverse=False, nj=J):
    """z-scores per column j for a list of units (rune lists)."""
    S = float((freq ** 2).sum())
    T = float((freq ** 3).sum())
    zs, ns = [], []
    for j in range(nj):
        col = [(u[::-1] if reverse else u)[j] for u in units if len(u) > j]
        n = len(col)
        ns.append(n)
        if n < 6:
            zs.append(0.0)
            continue
        cnt = np.bincount(col, minlength=N)
        x = float((cnt * (cnt - 1) // 2).sum())
        e = comb(n, 2) * S
        var = comb(n, 2) * (S - S * S) + n * (n - 1) * (n - 2) * (T - S * S)
        zs.append((x - e) / sqrt(var))
    return np.array(zs), np.array(ns)


def summarize(z):
    return float(z.max()), float(z[:J0].sum() / sqrt(J0))


def simulate_units(lengths, restart, eng, rng, q=0.82, start=2000, backward=False):
    """English runes cut into units of the given lengths and enciphered with the skip rule. restart=True: every unit
    starts at key index 0 of one shared random key; restart=False: the key continues across units."""
    key = [rng.randrange(N) for _ in range(2 * sum(lengths) + 400)]
    pos, j, units = start, 0, []
    prev = -1
    for L in lengths:
        if restart:
            j, prev = 0, -1
        cur = []
        plain = eng[pos:pos + L]
        for t in (plain[::-1] if backward else plain):
            y = (t + key[j]) % N
            j += 1
            while y == prev and rng.random() < q:
                y = (t + key[j]) % N
                j += 1
            cur.append(y)
            prev = y
        pos += L
        units.append(cur[::-1] if backward else cur)
    return units


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    segs = stats.SEGS
    idxs = list(stats.UNSOLVED)
    allr = np.array([x for i in idxs for x in lp.runes_of(segs[i])])
    freq = np.bincount(allr, minlength=N) / len(allr)
    eng = sim.english_runes()
    rng = random.Random(11)
    reps = 3 if args.quick else 12
    out = []
    P = out.append
    P(f"LP2: {len(allr)} runes; columns 0..{J - 1} from each unit's start (key forward) and end (key backward); "
      f"Z_sum over the first {J0}.")
    P("")
    P(f"{'unit':10s} {'n units':>7s} {'dir':>5s} {'max z':>7s} {'at col':>6s} {'Z_sum':>7s}   "
      f"{'restart control: Z_sum mean/min':>32s}   {'continuous-key null: max z (max over reps)':>44s}")
    kinds = ["segment", "page", "paragraph", "line", "sentence", "word"]
    for kind in kinds:
        units = units_of(kind, segs, idxs)
        lengths = [len(u) for u in units]
        for rev in (False, True):
            z, ns = column_stats(units, freq, reverse=rev)
            mx, zsum = summarize(z)
            zs_rst, mx_null = [], []
            for r in range(reps):
                st = 1000 + (31000 * r) % 200000
                u1 = simulate_units(lengths, True, eng, rng, start=st, backward=rev)
                zs_rst.append(summarize(column_stats(u1, freq, reverse=rev)[0])[1])
                u0 = simulate_units(lengths, False, eng, rng, start=st, backward=rev)
                mx_null.append(summarize(column_stats(u0, freq, reverse=rev)[0])[0])
            out_line = (f"{kind:10s} {len(units):7d} {'end' if rev else 'start':>5s} {mx:7.2f} {int(z.argmax()):6d} "
                        f"{zsum:7.2f}   {np.mean(zs_rst):14.1f} / {np.min(zs_rst):<14.1f}   {max(mx_null):44.2f}")
            P(out_line)
            print(out_line, flush=True)
    P("")
    P("Reading: a restart would show as Z_sum far above 0 (the controls show what a real restart gives) and max z far "
      "above the continuous-key null's maximum. For many columns and 12 unit types/directions, |z| below about 4 is "
      "unremarkable.")
    P("The one exception, line start column 0 (z = +6.7), is typographic: lines are set to a fixed width, so wide glyphs "
      "overflow to the next line more often (see line_layout.py). Columns 1-59 of the same units show nothing, which "
      "a real per-line restart (Z_sum about 170) would not allow.")
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "restart_columns.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    sys.exit(main())
