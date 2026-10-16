"""Can lost word separators explain LP2's word-length histogram?

aldegonde found that most clean disagreements between the page images and the transcription are separators present in
the image and missing from the transcription. If every separator is lost independently with probability m, adjacent words
merge: lengths a and b become a + b. This fits m (and a second convention for how English is written in runes: digraph runes
or letters) by the G-test used in wordlen.py, on top of the plain English models.

    python work/seploss.py          # -> results/analysis/seploss.txt
"""
import os
import sys

import numpy as np
from scipy.stats import chi2

import lp
import stats
import wordlen

HERE = os.path.dirname(os.path.abspath(__file__))
BINS = wordlen.BINS


def merged_hist(lengths, m, rng, reps=40):
    """Expected share by length 1..BINS (BINS = '>= BINS') after each separator is lost with probability m."""
    L = np.asarray(lengths)
    n = len(L)
    out = np.zeros(BINS)
    tot = 0
    for _ in range(reps):
        lost = rng.random(n - 1) < m                       # separator after word i is lost
        starts = np.concatenate([[0], np.where(~lost)[0] + 1])
        cs = np.concatenate([[0], np.cumsum(L)])
        merged = cs[np.append(starts[1:], n)] - cs[starts]
        h = np.bincount(np.minimum(merged, BINS), minlength=BINS + 1)[1:BINS + 1]
        out += h
        tot += h.sum()
    return out / tot


def main():
    segs = lp.load_segments()
    lp2 = []
    for i in stats.UNSOLVED:
        c = lp.runes_of(segs[i])
        lp2 += [b - a for _, a, b in lp.word_spans(segs[i], c)]
    obs = wordlen.hist(lp2)
    words = wordlen.emerson_words()
    em_runes = [x for x in (len(lp.word_to_key(w.replace("IO", "IA"))) for w in words) if x]
    em_letters = [len(w) for w in words]
    rng = np.random.default_rng(3301)
    out = []
    P = out.append
    P(f"LP2: {len(lp2)} words, mean {np.mean(lp2):.2f}; English (Emerson): {len(em_runes)} words, mean {np.mean(em_runes):.2f} "
      f"runes, {np.mean(em_letters):.2f} letters")
    P("share by length 1..11, 12+ (%):")
    P("  LP2                    " + " ".join(f"{100 * x / obs.sum():5.1f}" for x in obs))
    best = {}
    for name, L in (("English, GP runes", em_runes), ("English, letters", em_letters)):
        P("")
        P(f"{name}: each separator lost with probability m")
        P("     m   " + " ".join(f"{i + 1:>5d}" for i in range(BINS - 1)) + "  12+      G   df      p")
        rows = []
        for m in np.arange(0.0, 0.401, 0.025):
            p = merged_hist(L, m, rng)
            g, df, pv = wordlen.g_test(obs, p, fitted=1)
            rows.append((m, g, pv))
            P(f"  {m:5.3f} " + " ".join(f"{100 * x:5.1f}" for x in p) + f"  {g:7.1f} {df:3d}  {pv:.2e}")
        best[name] = min(rows, key=lambda r: r[1])
    P("")
    for name, (m, g, pv) in best.items():
        P(f"best fit, {name}: m = {m:.3f}, G = {g:.1f}, p = {pv:.2e}")
    P("(reference, from wordlen.py: English in runes G = 227; letters G = 55; English runes + one extra rune in 40% of multi-rune "
      "words G = 20.5 with 1 fitted parameter, p = 0.025)")
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "seploss.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
