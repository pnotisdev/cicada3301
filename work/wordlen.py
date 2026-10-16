"""Word-length test: which plaintext conventions could produce LP2's word lengths?

LP2 has far fewer 2-rune words than English written in Gematria Primus runes (15.9% against 24-27%). Candidate
explanations are compared by a G-test on the length histogram (1..11, 12+), with p-values:
  - English in GP runes (Emerson; the solved LP sections), the toolkit's default assumption;
  - English counted in LETTERS, i.e. no digraph runes (TH, NG, EA, OE, AE, EO, IA/IO written letter by letter),
    as if the plaintext alphabet were Latin letters mapped one-to-one onto runes;
  - English in runes with one extra (null) rune in a fraction r of words (fitted).

    python wordlen.py
"""
import collections
import os
import re
import sys

import numpy as np
from scipy.stats import chi2

import lp
import stats

HERE = os.path.dirname(os.path.abspath(__file__))
BINS = 12


def hist(lengths):
    h = np.zeros(BINS)
    for L in lengths:
        h[min(L, BINS) - 1] += 1
    return h


def g_test(obs, p_model, fitted=0):
    p = np.clip(p_model, 1e-9, None)
    p = p / p.sum()
    exp = obs.sum() * p
    m = obs > 0
    g = 2 * float((obs[m] * np.log(obs[m] / exp[m])).sum())
    df = BINS - 1 - fitted
    return g, df, float(chi2.sf(g, df))


def emerson_words():
    txt = open(os.path.join(HERE, "ref", "emerson_essays1.txt"), encoding="utf-8").read()
    txt = txt[txt.index("SELF-RELIANCE"):].split("*** END OF")[0]
    return [w.upper() for w in re.findall(r"[A-Za-z]+", txt)]


def main():
    segs = lp.load_segments()
    lp2 = []
    for i in stats.UNSOLVED:
        c = lp.runes_of(segs[i])
        lp2 += [b - a for _, a, b in lp.word_spans(segs[i], c)]
    obs = hist(lp2)
    words = emerson_words()
    em_runes = [len(lp.word_to_key(w.replace("IO", "IA"))) for w in words]
    em_runes = [x for x in em_runes if x]
    em_letters = [len(w) for w in words]
    sol_runes, sol_letters = [], []
    for i, (_, f) in lp.KNOWN.items():
        c = lp.runes_of(segs[i])
        p = f(c)
        for _, a, b in lp.word_spans(segs[i], c):
            sol_runes.append(b - a)
            sol_letters.append(len("".join(lp.LATIN[x] for x in p[a:b])))
    models = {
        "English, GP runes (Emerson)": hist(em_runes),
        "English, GP runes (solved LP)": hist(sol_runes),
        "English, letters (Emerson)": hist(em_letters),
        "English, letters (solved LP)": hist(sol_letters),
    }
    out = [f"LP2: {len(lp2)} words, mean {np.mean(lp2):.2f} runes",
           "share by length 1..11,12+ (%):",
           "  " + "LP2".ljust(34) + " ".join(f"{x:5.1f}" for x in 100 * obs / obs.sum())]
    rows = []
    for name, h in models.items():
        g, df, p = g_test(obs, h)
        rows.append((name, h, g, df, p, ""))
    # null-insertion model on GP-rune English
    base = models["English, GP runes (Emerson)"] / models["English, GP runes (Emerson)"].sum()
    best = None
    for r in np.linspace(0, 0.8, 161):
        for multi_only in (True, False):
            q = base.copy()
            ins = base.copy()
            if multi_only:
                ins[0] = 0
            q = q - r * ins
            q[1:] += r * ins[:-1]
            q[-1] += r * ins[-1]
            g, df, p = g_test(obs, q, fitted=1)
            if best is None or g < best[2]:
                best = (f"English runes + null rune in {100 * r:.0f}% of {'multi-rune ' if multi_only else ''}words",
                        q, g, df, p, "")
    rows.append(best)
    for name, h, g, df, p, _ in rows:
        out.append("  " + name.ljust(34) + " ".join(f"{x:5.1f}" for x in 100 * h / h.sum())
                   + f"   G={g:7.1f} df={df} p={p:.2e}")
    out.append("(G-test of LP2's histogram against each model; a model fits if p is not tiny)")
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "wordlen.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
