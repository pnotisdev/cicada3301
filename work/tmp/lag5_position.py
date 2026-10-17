"""Exploration: where inside a word do the lag-5 coincidences and repeated bigrams sit (start position j, word length)?"""
import os
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lp  # noqa: E402
import stats  # noqa: E402

words = []
for i in stats.UNSOLVED:
    c = lp.runes_of(stats.SEGS[i])
    words += [c[a:b] for _, a, b in lp.word_spans(stats.SEGS[i], c)]
allr = np.array([x for w in words for x in w])
S = float(((np.bincount(allr, minlength=29) / len(allr)) ** 2).sum())
G = int(sys.argv[1]) if len(sys.argv) > 1 else 5

by_j = Counter()
tot_j = Counter()
by_len = Counter()
tot_len = Counter()
bg_j = Counter()
bg_tot = Counter()
for w in words:
    L = len(w)
    for j in range(L - G):
        tot_j[j] += 1
        tot_len[L] += 1
        if w[j] == w[j + G]:
            by_j[j] += 1
            by_len[L] += 1
    for j in range(L - G - 1):
        bg_tot[j] += 1
        if w[j] == w[j + G] and w[j + 1] == w[j + G + 1]:
            bg_j[j] += 1
print(f"lag {G}, S = {100 * S:.2f}%")
print("start position j: coincidences/windows (rate)   bigram repeats/windows (exp)")
for j in sorted(tot_j):
    print(f"  j={j:2d}  {by_j[j]:3d}/{tot_j[j]:4d} ({100 * by_j[j] / tot_j[j]:4.1f}%)   {bg_j[j]:2d}/{bg_tot[j]:4d} ({bg_tot[j] * S * S:.2f})")
print("word length: coincidences/windows (rate)")
for L in sorted(tot_len):
    print(f"  L={L:2d}  {by_len[L]:3d}/{tot_len[L]:4d} ({100 * by_len[L] / tot_len[L]:4.1f}%)  windows expected {tot_len[L] * S:.1f}")
