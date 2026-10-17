"""Is LP2's word-length histogram that of English with its most frequent words (function words) removed? (A text without serial word-length structure and
with a deficit of short words: a list of content words, e.g. keywords, in no sentence order.) For each English text and each N, the N most frequent
word types are removed, the remaining tokens are spelled in runes (digraphs as single runes, as lp.word_to_key) and the length histogram is compared with
LP2's by the G-test (12 bins; df = 11, no fitted parameter besides N which is scanned, so read the best p as optimistic by the number of N tried).

    python work/wordlen_stoplist.py          # -> results/analysis/wordlen_stoplist.txt
"""
import os
import re
import sys
from collections import Counter

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


def g_test(obs, p, df=BINS - 1):
    p = np.clip(p, 1e-9, None)
    p = p / p.sum()
    e = obs.sum() * p
    m = obs > 0
    g = 2 * float((obs[m] * np.log(obs[m] / e[m])).sum())
    return g, float(chi2.sf(g, df))


def words_of(path, marker=None, cap=400000):
    with open(path, encoding="utf-8", errors="replace") as f:
        txt = f.read()
    if "*** START OF" in txt:
        txt = txt.split("*** START OF", 1)[-1].split("*** END OF", 1)[0]
    if marker:
        i = txt.find(marker)
        txt = txt[i if i >= 0 else 0:]
    return [w.upper() for w in re.findall(r"[A-Za-z]+", txt[:cap])]


def main():
    lens = []
    for i in stats.UNSOLVED:
        c = lp.runes_of(stats.SEGS[i])
        lens += [b - a for _, a, b in lp.word_spans(stats.SEGS[i], c)]
    obs = hist(lens)
    texts = [("Emerson", os.path.join(HERE, "ref", "emerson_essays1.txt"), "SELF-RELIANCE"),
             ("KJV", os.path.join(HERE, "ref", "corpora", "pg10.txt"), "In the beginning"),
             ("Walden", os.path.join(HERE, "ref", "corpora", "pg205.txt"), "Economy"),
             ("Milton", os.path.join(HERE, "ref", "corpora", "pg26.txt"), "BOOK I"),
             ("Plato", os.path.join(HERE, "ref", "corpora", "pg1497.txt"), "BOOK I")]
    out = [f"LP2: {len(lens)} words; share by length 1..11,12+ (%): " + " ".join(f"{x:.1f}" for x in 100 * obs / obs.sum()), "",
           "English with the N most frequent word types removed, length in runes (digraph runes single); G / p against LP2 (df 11):", ""]
    for name, path, marker in texts:
        if not os.path.exists(path):
            continue
        ws = words_of(path, marker)
        cnt = Counter(ws)
        rank = [w for w, _ in cnt.most_common()]
        cache = {w: len(lp.word_to_key(w.replace("IO", "IA"))) for w in cnt}
        best = None
        rows = []
        for n in (0, 5, 10, 20, 30, 40, 50, 75, 100, 150, 200, 300):
            stop = set(rank[:n])
            h = hist([cache[w] for w in ws if w not in stop])
            g, p = g_test(obs, h / h.sum())
            rows.append((n, g, p, h))
            if best is None or g < best[1]:
                best = (n, g, p, h)
        out.append(f"{name}: " + "  ".join(f"N={n}: G {g:.0f}" for n, g, p, h in rows))
        out.append(f"   best N={best[0]}: G = {best[1]:.1f}, p = {best[2]:.2e}; shares " + " ".join(f"{x:.1f}" for x in 100 * best[3] / best[3].sum()))
    out.append("")
    out.append("Reading: a good fit (p not tiny) at some N would support a text of content words in no sentence order; the best fits of "
               "wordlen_languages.py (extra rune in 40% of words, 2-rune words missing) have G 17-20.")
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "wordlen_stoplist.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
