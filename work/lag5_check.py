"""Independent check of the lag-5 clustering claim of research/word-internal-lag5.

Claim: inside words, the bigram at (j, j+1) equals the bigram at (j+5, j+6) 9 times against ~1.5 expected.
Three nulls, none taken from the branch's code:
  A. analytic:   pairs * S^2, S = sum of squared rune frequencies (Poisson tail);
  B. conditional: given the observed number of lag-g coincidences, how often does the NEXT position coincide too?
     (separates "lag 5 coincides more often" from "coincidences cluster"), exact binomial tail;
  C. permutation: runes shuffled inside each section (word lengths, section frequencies kept), the same bigram count for
     lags 2..8, and the p-value of the best lag (look-elsewhere over the lags).

    python work/lag5_check.py [--reps 10000]        # -> results/analysis/lag5_check.txt
"""
import argparse
import os
import sys

import numpy as np
from scipy.stats import binom, poisson

import lp
import stats

N = lp.N
HERE = os.path.dirname(os.path.abspath(__file__))
LAGS = range(2, 9)


def sections():
    """per UNSOLVED segment: (runes, word id per rune)"""
    out = []
    for i in stats.UNSOLVED:
        c = lp.runes_of(stats.SEGS[i])
        wid = np.full(len(c), -1)
        for k, (_, a, b) in enumerate(lp.word_spans(stats.SEGS[i], c)):
            wid[a:b] = k
        out.append((np.array(c), wid))
    return out


def counts(r, wid, g):
    """(coincidence windows, coincidences, bigram windows, equal bigrams, coincidences whose next position also coincides)
    for pairs (j, j+g) that lie inside one word"""
    n = len(r) - g
    ins = (wid[:n] == wid[g:]) & (wid[:n] >= 0)
    eq = (r[:n] == r[g:]) & ins
    m = n - 1
    ins2 = ins[:m] & ins[1:m + 1]  # j and j+1 both inside the same word at both ends (word ids equal across)
    ins2 &= wid[:m] == wid[1:m + 1]
    both = eq[:m] & eq[1:m + 1] & ins2
    return int(ins.sum()), int(eq.sum()), int(ins2.sum()), int(both.sum()), int((eq[:m] & ins2).sum())


def total(secs, g, perm=None):
    t = np.zeros(5, dtype=np.int64)
    for k, (r, wid) in enumerate(secs):
        t += counts(r if perm is None else perm[k], wid, g)
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=10000)
    args = ap.parse_args()
    secs = sections()
    allr = np.concatenate([r[w >= 0] for r, w in secs])
    S = float(((np.bincount(allr, minlength=N) / len(allr)) ** 2).sum())
    out = []
    P = out.append
    P(f"LP2: {len(allr)} runes in words, chance coincidence S = {100 * S:.3f}%")
    P("")
    P("lag | coincid. in-word windows  obs  rate | bigram windows  obs  exp(S^2)  Poisson p | "
      "next-coincides: obs/coinc  (rate vs S)  binomial p")
    obs = {}
    for g in LAGS:
        nw, e, nb, b, ce = total(secs, g)
        obs[g] = (nw, e, nb, b, ce)
        pa = poisson.sf(b - 1, nb * S * S)
        pb = binom.sf(b - 1, ce, S)
        P(f" {g}  | {nw:6d} {e:4d} {100 * e / nw:5.2f}%        | {nb:6d} {b:3d}  {nb * S * S:5.2f}   {pa:.1e}   | "
          f"{b:2d}/{ce:3d}  ({100 * b / max(ce, 1):4.1f}% vs {100 * S:.1f}%)  {pb:.1e}")
    P("")
    rng = np.random.default_rng(11)
    lags = list(LAGS)
    cb = np.zeros((args.reps, len(lags)), dtype=np.int64)  # bigram repeats per shuffle and lag
    cc = np.zeros_like(cb)  # coincidences
    for i in range(args.reps):
        perm = []
        for r, wid in secs:
            q = r.copy()
            m = wid >= 0
            q[m] = rng.permutation(q[m])
            perm.append(q)
        for k, g in enumerate(lags):
            t = total(secs, g, perm)
            cb[i, k], cc[i, k] = t[3], t[1]

    def tail(col, x):
        return (int((col >= x).sum()) + 1) / (len(col) + 1)

    P(f"C. Permutation null ({args.reps} shuffles of the runes inside each section; word layout fixed):")
    P("   lag | P(coincidences >= obs) | P(bigram repeats >= obs)")
    for k, g in enumerate(lags):
        P(f"    {g}  |        {tail(cc[:, k], obs[g][1]):.4f}          |       {tail(cb[:, k], obs[g][3]):.4f}")
    # look-elsewhere over the lags: the smallest per-lag tail probability, compared with the same quantity in each shuffle
    sf = [np.array([tail(cb[:, k], x) for x in range(int(cb[:, k].max()) + 2)]) for k in range(len(lags))]
    minp = np.array([min(sf[k][min(int(cb[i, k]), len(sf[k]) - 1)] for k in range(len(lags))) for i in range(args.reps)])
    pobs = min(tail(cb[:, k], obs[g][3]) for k, g in enumerate(lags))
    P(f"   smallest per-lag p of the observed data = {pobs:.4f}; P(a shuffle has a smallest p <= that) = "
      f"{(int((minp <= pobs).sum()) + 1) / (args.reps + 1):.4f}   (look-elsewhere over {len(lags)} lags)")
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "lag5_check.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
