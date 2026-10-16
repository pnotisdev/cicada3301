"""Why are line-initial runes non-uniform? Typographic overflow, not cryptography.

restart_columns.py finds one unexpected number: the first runes of the 594 physical lines are not uniform
(chi2 78.7 on 28 df, z = +6.7 for equal pairs in column 0), while no other column or unit type shows anything.
LP2's lines hold 17-26 runes (mean 21.8): they are set to a fixed width, so a line breaks before the first rune
that no longer fits. A wide glyph is therefore more likely to be the overflowing (first-of-next-line) rune.

This script fits one width per rune from the line compositions alone (least squares: the widths on a full line sum
to a constant) and checks whether the widths predict the line-initial excess:
  1. corr(width, first-rune enrichment) and a permutation p-value;
  2. chi2 of the first runes against the flat model and against the overflow model P(first = x) ~ f_x w_x;
  3. out-of-sample: widths fitted on segments 0.11-0.15, tested on 0.7-0.9, and the reverse.

    python work/line_layout.py
"""
import os
import sys

import numpy as np

import lp
import stats
from restart_columns import N, units_of

HERE = os.path.dirname(os.path.abspath(__file__))


def fit_widths(units):
    A = np.array([np.bincount(u, minlength=N) for u in units if len(u) >= 17], float)
    w = np.linalg.solve(A.T @ A + 1e-3 * np.eye(N), A.T @ np.ones(len(A)))
    return w * N / w.sum()


def chi2(first, p):
    c = np.bincount(first, minlength=N)
    n = len(first)
    return float((((c - n * p) ** 2) / (n * p)).sum())


def main():
    segs = stats.SEGS
    idxs = list(stats.UNSOLVED)
    allr = np.array([x for i in idxs for x in lp.runes_of(segs[i])])
    f = np.bincount(allr, minlength=N) / len(allr)
    units = units_of("line", segs, idxs)
    firsts = np.array([u[0] for u in units])
    out = []
    P = out.append
    w = fit_widths(units)
    P(f"{len(units)} lines; {sum(len(u) >= 17 for u in units)} full lines (>= 17 runes) used for the width fit.")
    P("fitted glyph widths (mean 1): " + " ".join(f"{lp.LATIN[x]}={w[x]:.2f}" for x in range(N)))
    n = len(firsts)
    enr = np.bincount(firsts, minlength=N) / (n * f)
    r = float(np.corrcoef(w, enr)[0, 1])
    rng = np.random.default_rng(1)
    pperm = float(np.mean([np.corrcoef(rng.permutation(w), enr)[0, 1] >= r for _ in range(20000)]))
    P(f"corr(width, first-rune enrichment) = {r:.2f}; permutation p = {pperm:.4f}")
    pf = f * np.clip(w, 0.05, None)
    pf /= pf.sum()
    P(f"chi2 of line-initial runes (28 df): flat {chi2(firsts, f):.1f}; overflow model {chi2(firsts, pf):.1f} "
      f"(widths fitted in-sample, 28 free parameters)")
    half = {"A": (7, 8, 9), "B": (11, 12, 13, 14, 15)}
    for fit_on, test_on in (("B", "A"), ("A", "B")):
        uf = units_of("line", segs, list(half[fit_on]))
        ut = units_of("line", segs, list(half[test_on]))
        wf = fit_widths(uf)
        ft = np.array([u[0] for u in ut])
        pm = f * np.clip(wf, 0.05, None)
        pm /= pm.sum()
        P(f"out-of-sample: widths fitted on segments {half[fit_on]}, tested on {half[test_on]} ({len(ft)} lines): "
          f"chi2 flat {chi2(ft, f):.1f} -> overflow model {chi2(ft, pm):.1f}")
    P("")
    P("Reading: the overflow model removes most of the excess in sample (78.7 -> 36.6 on 28 df) and part of it out of "
      "sample (the widths are fitted from only 167 or 426 lines there), and the widest glyph (EA) and the narrowest (I) "
      "lead the enrichment/deficit; corr(width, enrichment) = +0.74. The line-start anomaly is therefore mostly a "
      "layout effect of the printed ciphertext runes. A leftover of chi2 ~51 on 426 lines out of sample is not "
      "explained; real glyph widths measured from the page images would settle it. Either way it carries no key "
      "information: a per-line key restart would show in columns 1-59 as well.")
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "line_layout.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
