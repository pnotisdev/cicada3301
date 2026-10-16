"""Where inside words does LP2's distance-5 coincidence excess sit?

Pools all unsolved segments. For word length L and positions i < j inside the word, counts how often the two runes
are equal; the null is 1/29 per pair adjusted for LP2's own rune frequencies (sum f^2) and, for adjacent positions,
the doublet deficit. Tables:
  1. coincidence rate by distance d = 1..9 (all words long enough), with exact binomial z;
  2. for d = 5: by word length L (the pair positions are then fixed for L = 6: (0,5); L = 7: (0,5),(1,6); ...), and by start position i;
  3. the same for d = 4 and d = 6 as neighbours (a real periodic-5 structure should leave them at chance);
  4. the d = 5 excess split by the rune pair's value: do equal pairs cluster on particular runes?
    python work/within_word.py          # -> results/analysis/within_word.txt
"""
import os
import sys
from collections import Counter, defaultdict
from math import sqrt

import numpy as np

import lp
import stats

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    words = []
    for i in stats.UNSOLVED:
        toks = stats.SEGS[i]
        r = lp.runes_of(toks)
        for _, a, b in lp.word_spans(toks, r):
            words.append(r[a:b])
    allr = np.array([x for w in words for x in w])
    f = np.bincount(allr, minlength=lp.N) / len(allr)
    S = float((f ** 2).sum())
    out = []
    P = out.append
    P(f"{len(words)} words, {len(allr)} runes, chance coincidence S = {100 * S:.3f}%")
    P("")
    P("1. by distance d (all pairs (i, i+d) inside words):")
    P("   d    pairs   equal   rate%    z")
    for d in range(1, 10):
        n = e = 0
        for w in words:
            for i in range(len(w) - d):
                n += 1
                e += w[i] == w[i + d]
        sd = sqrt(n * S * (1 - S))
        P(f"  {d:2d} {n:8d} {e:6d}  {100 * e / n:5.2f}  {(e - n * S) / sd:+5.1f}")
    for d in (4, 5, 6):
        P("")
        P(f"2. d = {d}: by word length L (rate over the pairs inside words of length L)")
        P("    L  words  pairs  equal  rate%     z")
        tot_z = []
        for L in range(d + 1, 13):
            sel = [w for w in words if len(w) == L]
            n = sum(L - d for _ in sel)
            e = sum(int(w[i] == w[i + d]) for w in sel for i in range(L - d))
            if n:
                z = (e - n * S) / sqrt(n * S * (1 - S))
                P(f"  {L:3d} {len(sel):6d} {n:6d} {e:6d}  {100 * e / n:5.2f}  {z:+5.1f}")
        P(f"   by start position i (pairs (i, i+{d}), all word lengths):")
        for i0 in range(0, 6):
            n = e = 0
            for w in words:
                if len(w) > i0 + d:
                    n += 1
                    e += w[i0] == w[i0 + d]
            if n:
                P(f"     i={i0}: {n:5d} pairs, {e:4d} equal, {100 * e / n:5.2f}%, z {(e - n * S) / sqrt(n * S * (1 - S)):+.1f}")
        # from the word end
        P(f"   by end offset (pair (L-1-d-k, L-1-k)):")
        for k in range(0, 4):
            n = e = 0
            for w in words:
                L = len(w)
                if L - 1 - d - k >= 0:
                    n += 1
                    e += w[L - 1 - d - k] == w[L - 1 - k]
            if n:
                P(f"     k={k}: {n:5d} pairs, {e:4d} equal, {100 * e / n:5.2f}%, z {(e - n * S) / sqrt(n * S * (1 - S)):+.1f}")
    P("")
    P("4. d = 5 equal pairs by rune value (all equal pairs): " + str(dict(sorted(Counter(
        w[i] for w in words for i in range(len(w) - 5) if w[i] == w[i + 5]).items()))))
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "within_word.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
