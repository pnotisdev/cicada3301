"""Ciphertext-feedback hypothesis, step 1: coincidences at lag P in c'_i = c_i - a*c_{i-1} (mod 29), for every a.

LP2's doublet fingerprint is what a ciphertext-feedback cipher c_i = c_{i-1}*a + p_i + k_i gives if the encryptor
avoids the shift that would repeat a rune. Every earlier screen assumed c = p + k, so none of them looked at c'.
If the key of such a cipher is periodic with period P, then c'_i - c'_{i+P} = p_i - p_{i+P} and the coincidence rate
of c' at lag P rises from 1/29 to the plaintext's (about 6.5% for English); the skip rule lets the key pointer drift
(about 0.028 per rune), so this plain lag scan is only meaningful for short periods (<= ~60).

For a = 0 (the ordinary cipher) this repeats the old lag scan as a reference. Segments are kept apart (no pair
crosses a segment boundary).

    python work/chain_lag.py          # -> results/analysis/chain_lag.txt
"""
import os
import sys
from math import sqrt

import numpy as np

import lp
import stats

HERE = os.path.dirname(os.path.abspath(__file__))
N = lp.N
MAXLAG = 120


def transformed(a):
    out = []
    for i in stats.UNSOLVED:
        c = np.array(lp.runes_of(stats.SEGS[i]))
        out.append(c if a == 0 else (c[1:] - a * c[:-1]) % N)
    return out


def lag_stats(segs, lag):
    num = den = 0
    for s in segs:
        if len(s) > lag:
            num += int((s[:-lag] == s[lag:]).sum())
            den += len(s) - lag
    return num, den


def main():
    out, hits = [], []
    P = out.append
    allc = np.concatenate(transformed(0))
    P(f"{len(allc)} runes in {len(stats.UNSOLVED)} segments; lags 1..{MAXLAG}; z = (equal pairs - n S) / sd, S = sum f^2 of c'")
    P("")
    P("   a   S%     max z (lag)    2nd (lag)     lags with z > 3.5        sum of z^2 over lags 2..60 (expect ~59)")
    rows = []
    for a in range(N):
        segs = transformed(a)
        cat = np.concatenate(segs)
        f = np.bincount(cat, minlength=N) / len(cat)
        S = float((f ** 2).sum())
        zs = []
        for lag in range(1, MAXLAG + 1):
            e, n = lag_stats(segs, lag)
            zs.append((e - n * S) / sqrt(n * S * (1 - S)))
        zs = np.array(zs)
        z2 = zs[1:]                                  # lag 1 is the anti-repeat lag (a = 0, 1: suppressed by the rule)
        order = np.argsort(-z2)
        big = [int(l) + 2 for l in np.where(z2 > 3.5)[0]]
        rows.append((a, S, zs))
        P(f"  {a:2d}  {100 * S:5.3f}  {z2[order[0]]:+5.2f} ({order[0] + 2:3d})  {z2[order[1]]:+5.2f} ({order[1] + 2:3d})   "
          f"{str(big) if big else '-':24s}  {float((zs[1:60] ** 2).sum()):6.1f}")
        hits += [(z2[k], a, k + 2) for k in range(len(z2))]
    hits.sort(reverse=True)
    P("")
    P(f"{29 * (MAXLAG - 1)} (a, lag) tests; the largest z of that many standard normals is about 4.0 +- 0.3.")
    P("top 8: " + "; ".join(f"a={a} lag={lag} z={z:+.2f}" for z, a, lag in hits[:8]))
    P("lag 1 (z) for a = 0, 1, 2: " + ", ".join(f"{rows[a][2][0]:+.1f}" for a in (0, 1, 2)))
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "chain_lag.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
