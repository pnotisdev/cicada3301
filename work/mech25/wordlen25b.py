"""Phase 25 part B2: segmentation-side plaintext models on top of letter spelling (Emerson, the best corpus): (i) a short word (<= s letters) is glued to the
following word with probability m (missing separators); (ii) the +1-rune insertion model of work/wordlen.py applied to letters (fitted r), for comparison.
One fitted parameter each (df 10). Also the Emerson letter-spelling G computed here (same binning) as the reference.

    python work/mech25/wordlen25b.py      # -> results/analysis/wordlen25b.txt
"""
import os
import sys

import numpy as np
from scipy.stats import chi2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import lp  # noqa: E402
import stats  # noqa: E402
import wordlen as W  # noqa: E402
import wordlen25 as B  # noqa: E402


def main():
    segs = lp.load_segments()
    lp2 = []
    for i in stats.UNSOLVED:
        c = lp.runes_of(segs[i])
        lp2 += [b - a for _, a, b in lp.word_spans(segs[i], c)]
    obs = W.hist(lp2)
    ws = B.words_of("emerson_essays1.txt")
    L = np.array([B.spell_len(w, set()) for w in ws])
    out = []
    base = W.hist(L)
    out.append(f"Emerson letters: G {W.g_test(obs, base)[0]:.1f} (df 11)")
    rng = np.random.default_rng(7)
    best = {}
    for s in (1, 2, 3):
        for m in np.linspace(0, 1, 41):
            gs = []
            for _ in range(3):
                glued, i = [], 0
                while i < len(L):
                    x = L[i]
                    while x <= s and i + 1 < len(L) and rng.random() < m:
                        i += 1; x += L[i]
                    glued.append(x); i += 1
                gs.append(W.hist(glued))
            h = np.mean(gs, axis=0)
            g = W.g_test(obs, h)[0]
            if s not in best or g < best[s][0]:
                best[s] = (g, m)
    for s, (g, m) in best.items():
        out.append(f"short words (<= {s} letters) glued to the next with prob {m:.3f}: G {g:.1f} (df 10, p {chi2.sf(g, 10):.2e})")
    gi = None
    for r in np.linspace(0, 0.8, 161):
        q = base / base.sum()
        ins = q.copy(); ins[0] = 0
        q = q - r * ins; q[1:] += r * ins[:-1]; q[-1] += r * ins[-1]
        g = W.g_test(obs, q)[0]
        if gi is None or g < gi[0]:
            gi = (g, r)
    out.append(f"+1 rune in a fraction r of multi-rune words (letters): G {gi[0]:.1f} at r {gi[1]:.3f} (df 10, p {chi2.sf(gi[0], 10):.2e})")
    print("\n".join(out))
    open(os.path.join(HERE, "..", "..", "results", "analysis", "wordlen25b.txt"), "w", newline="\n").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
