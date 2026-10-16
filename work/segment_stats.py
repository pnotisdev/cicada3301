"""Per-section statistics of LP2: does every section look the same, or do some sections differ (as if they used a
different method, like the solved sections)?

For each unsolved segment: runes, IoC, doublet rate, mean word length and the share of 1/2/3-rune words, the
within-word coincidence rate at distances 1..8 (aldegonde's echo), and the rune-frequency chi-square. Each value is
compared with 2,000 shuffles of the segment's own runes (words kept, runes permuted among positions), which keeps the
word-length structure and removes any rune-order structure; z = (observed - shuffle mean) / shuffle sd.

    python work/segment_stats.py          # -> results/analysis/segment_stats.txt
"""
import os
import sys

import numpy as np

import lp
import stats

HERE = os.path.dirname(os.path.abspath(__file__))
N = lp.N
D = 8


def features(runes, lens):
    r = np.asarray(runes)
    n = len(r)
    cnt = np.bincount(r, minlength=N)
    ioc = N * float((cnt * (cnt - 1)).sum()) / (n * (n - 1))
    dbl = float((r[1:] == r[:-1]).mean())
    pos = np.cumsum([0] + list(lens))
    within = []
    for d in range(1, D + 1):
        num = den = 0
        for a, b in zip(pos[:-1], pos[1:]):
            if b - a > d:
                w = r[a:b]
                num += int((w[:-d] == w[d:]).sum())
                den += len(w) - d
        within.append(num / den if den else float("nan"))
    return ioc, dbl, within


def main():
    rng = np.random.default_rng(3301)
    rows, out = [], []
    P = out.append
    P("segment  runes  words  meanlen  1-rune  2-rune  IoC    zIoC   doublet%  zDbl  | within-word coincidence % at d=1..8 (z vs shuffles)")
    for i in stats.UNSOLVED:
        toks = stats.SEGS[i]
        runes = lp.runes_of(toks)
        lens = [b - a for _, a, b in lp.word_spans(toks, runes)]
        if len(runes) < 100:
            continue
        ioc, dbl, within = features(runes, lens)
        sh = []
        for _ in range(2000):
            perm = rng.permutation(runes)
            sh.append(features(perm, lens))
        s_ioc = np.array([s[0] for s in sh])
        s_dbl = np.array([s[1] for s in sh])
        s_w = np.array([s[2] for s in sh])
        z = lambda x, a: (x - a.mean()) / a.std() if a.std() > 0 else 0.0
        ml = np.mean(lens)
        P(f"0.{i:<7d}{len(runes):5d} {len(lens):6d}   {ml:5.2f}   {100 * np.mean(np.array(lens) == 1):5.1f}   "
          f"{100 * np.mean(np.array(lens) == 2):5.1f}  {ioc:6.3f} {z(ioc, s_ioc):+5.1f}   {100 * dbl:6.2f}  {z(dbl, s_dbl):+5.1f}  | "
          + " ".join(f"{100 * w:4.1f}({z(w, s_w[:, d]):+.1f})" for d, w in enumerate(within)))
    P("")
    P("shuffle nulls keep the segment's rune counts and word lengths; doublet and within-word statistics under the null are "
      "those of an order-free rune sequence (the real text has the doublet deficit, so z(doublet) is expected to be very negative).")
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "segment_stats.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
