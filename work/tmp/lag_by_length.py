"""Exploration: coincidence rate (rune j == rune j+g inside a word) by word length L and lag g, in sigmas from chance.
Looks for structure tied to the word length (e.g. a half-word lag)."""
import os
import sys

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
print(f"S = {100 * S:.2f}%   cells: excess z (obs/windows); * = lag is half the word length")
lags = range(2, 10)
print("  L  nwords | " + "  ".join(f"g={g:<9d}" for g in lags))
for L in range(5, 15):
    ws = [w for w in words if len(w) == L]
    cells = []
    for g in lags:
        if g >= L:
            cells.append(" " * 11)
            continue
        n = len(ws) * (L - g)
        e = sum(w[j] == w[j + g] for w in ws for j in range(L - g))
        z = (e - n * S) / np.sqrt(n * S * (1 - S))
        mark = "*" if 2 * g == L else " "
        cells.append(f"{z:+5.1f}{mark}({e:2d}/{n:3d})")
    print(f" {L:2d}  {len(ws):5d} | " + " ".join(cells))
