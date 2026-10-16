"""Which language / spelling convention reproduces LP2's word-length histogram?

wordlen.py showed that LP2's word lengths reject English written in Gematria Primus runes (G = 227, p ~ 1e-42) and
that "English runes plus one extra rune in ~40% of multi-rune words" fits (p = 0.025). This script widens the search
with public-domain corpora in other languages, spelled as runes (digraph-aware, as lp.word_to_key does) and as plain
letters, plus a two-parameter family on English:

    length = runes + (each digraph rune spelled as two letters with probability r) + (extra rune, prob. a, multi-rune words)

Every model is compared with LP2's 2,928 word lengths (bins 1..11, 12+) by a G-test; df = 11 - fitted parameters.

    python work/wordlen_languages.py --fetch     # download the corpora to work/ref/corpora/ (not committed)
    python work/wordlen_languages.py
"""
import argparse
import os
import re
import sys
import unicodedata
import urllib.request
from math import comb

import numpy as np
from scipy.stats import chi2

import lp
import stats

HERE = os.path.dirname(os.path.abspath(__file__))
CORP = os.path.join(HERE, "ref", "corpora")
BINS = 12
# name -> (Gutenberg id, language, skip start marker, max chars)
CORPORA = {
    "English (Emerson, Essays I)": (None, "en", None, None),
    "English (Beowulf, translation)": (16328, "en", "BEOWULF", 400000),
    "English (KJV Bible)": (10, "en", "In the beginning", 400000),
    "English (Milton, Paradise Lost)": (26, "en", "BOOK I", 400000),
    "English (Plato, Republic)": (1497, "en", "BOOK I", 400000),
    "English (Marcus Aurelius)": (2680, "en", "THE FIRST BOOK", 400000),
    "English (Nietzsche, Zarathustra)": (1998, "en", "ZARATHUSTRA'S PROLOGUE", 400000),
    "English (Nietzsche, Beyond G&E)": (4363, "en", "PREFACE", 400000),
    "English (Thoreau, Walden)": (205, "en", "Economy", 400000),
    "English (Spinoza, Ethics)": (3800, "en", "PART I", 400000),
    "English (Darwin, Origin)": (2009, "en", "INTRODUCTION", 400000),
    "Latin (Caesar, De bello Gallico)": (218, "la", "GALLIA", 400000),
    "Latin (Vergil, Aeneid)": (227, "la", "ARMA", 400000),
    "German (Goethe, Faust I)": (2229, "de", "Faust", 400000),
    "French (Hugo, Les Miserables I)": (17489, "fr", "FANTINE", 400000),
    "Spanish (Cervantes, Don Quijote)": (2000, "es", "PRIMERA PARTE", 400000),
    "Italian (Dante, Commedia)": (1012, "it", "Nel mezzo", 400000),
}


def fetch():
    os.makedirs(CORP, exist_ok=True)
    with open(os.path.join(CORP, ".gitignore"), "w", newline="\n") as f:
        f.write("*\n!.gitignore\n")
    for name, (gid, *_rest) in CORPORA.items():
        if gid is None:
            continue
        path = os.path.join(CORP, f"pg{gid}.txt")
        if not os.path.exists(path):
            print("downloading", name)
            urllib.request.urlretrieve(f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt", path)


def words_of(name):
    gid, lang, marker, cap = CORPORA[name]
    if gid is None:
        txt = open(os.path.join(HERE, "ref", "emerson_essays1.txt"), encoding="utf-8").read()
        txt = txt[txt.index("SELF-RELIANCE"):].split("*** END OF")[0]
    else:
        path = os.path.join(CORP, f"pg{gid}.txt")
        if not os.path.exists(path):
            return None
        txt = open(path, encoding="utf-8", errors="replace").read()
        txt = txt.split("*** START OF", 1)[-1].split("*** END OF", 1)[0]
        i = txt.find(marker)
        txt = txt[i if i >= 0 else 0:][:cap]
    txt = txt.replace("æ", "ae").replace("Æ", "AE").replace("œ", "oe").replace("Œ", "OE")
    txt = unicodedata.normalize("NFD", txt)
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return [w.upper() for w in re.findall(r"[A-Za-z]+", txt)]


def hist(lengths):
    h = np.zeros(BINS)
    for L in lengths:
        h[min(L, BINS) - 1] += 1
    return h


def g_test(obs, p, fitted=0):
    p = np.clip(p, 1e-9, None)
    p = p / p.sum()
    e = obs.sum() * p
    m = obs > 0
    g = 2 * float((obs[m] * np.log(obs[m] / e[m])).sum())
    df = BINS - 1 - fitted
    return g, df, float(chi2.sf(g, df))


def rune_len(w):
    return len(lp.word_to_key(w.replace("IO", "IA")))


def family(words, r_grid, a_grid):
    """Length distribution for each r: every digraph rune is kept as one rune with prob 1-r and spelled as two letters
    with prob r (r = 0: pure runes, r = 1: plain letters). The extra-rune parameter a is applied by the caller."""
    letters = np.array([len(w) for w in words])
    runes = np.array([rune_len(w) for w in words])
    out = {}
    for r in r_grid:
        # expected length distribution: runes + (letters - runes) * Bernoulli-ish; do it per word by binomial
        base = np.zeros(64)
        for l, ru in zip(letters, runes):
            k = l - ru                       # number of digraph collapses available
            if k == 0:
                base[ru] += 1
            else:
                for j in range(k + 1):
                    base[ru + j] += comb(k, j) * (r ** j) * ((1 - r) ** (k - j))
        out[r] = base
    return out


def mechanisms(obs, ws):
    """One-parameter mechanisms on English in runes (Emerson), each fitted to LP2 by minimum G."""
    import collections
    import random
    base = [rune_len(w) for w in ws]
    cnt = collections.Counter(base)

    def fit(make):
        best = None
        for x in np.linspace(0.0, 0.9, 91):
            q = make(x)
            g, df, p = g_test(obs, q / q.sum(), fitted=1)
            if best is None or g < best[0]:
                best = (g, df, p, x)
        return best

    def shift(a):
        q = np.zeros(64)
        for L, n in cnt.items():
            if L == 1:
                q[1] += n
            else:
                q[L] += n * (1 - a)
                q[L + 1] += n * a
        return np.concatenate([q[1:BINS], [q[BINS:].sum()]])

    def per_rune(lam):
        from math import comb
        q = np.zeros(80)
        for L, n in cnt.items():
            for k in range(0, min(L, 4) + 1):
                q[min(L + k, 79)] += n * comb(L, k) * lam ** k * (1 - lam) ** (L - k)
        return np.concatenate([q[1:BINS], [q[BINS:].sum()]])

    def delete2(d):
        q = np.zeros(BINS)
        for L, n in cnt.items():
            q[min(L, BINS) - 1] += n * ((1 - d) if L == 2 else 1.0)
        return q

    def merge(m):
        R = random.Random(1)
        out, cur = [], 0
        for L in base:
            cur += L
            if R.random() >= m:
                out.append(cur)
                cur = 0
        return hist(out)

    rows = [("+1 rune in a fraction a of multi-rune words", fit(shift)),
            ("inserted rune at rate lam per rune, anywhere", fit(lambda x: per_rune(x * 0.5))),
            ("adjacent words fused (boundary lost) w.p. m", fit(lambda x: merge(x / 3))),
            ("2-rune words missing w.p. d (renormalised)", fit(delete2))]
    out = ["", "One-parameter mechanisms on English in runes (Emerson), fitted to LP2 (df = 10):"]
    for name, (g, df, p, x) in rows:
        out.append(f"  {name:48s} G={g:6.1f} p={p:.1e}")
    out.append("(per-rune insertion and boundary fusion are parameterised on grids x/2 and x/3; best values are not shown.)")
    return out


def digraph_expansion(obs, ws):
    """Which digraph rune, spelled as two letters, explains most of English-in-runes' excess of 2-rune words?"""
    seqs = [s for s in (lp.word_to_key(w.replace("IO", "IA")) for w in ws) if s]
    names = [n for n in lp.LATIN if len(n) >= 2]

    def dist(expand):
        q = np.zeros(80)
        for s in seqs:
            extra = sum(len(lp.LATIN[r]) - 1 for r in s if lp.LATIN[r] in expand)
            q[min(len(s) + extra, 79)] += 1
        return np.concatenate([q[1:BINS], [q[BINS:].sum()]]) / q[1:].sum()

    out = ["", "Spelling a digraph rune as two letters (all occurrences), English runes, no other parameter (df = 11):"]
    for n in names:
        g, df, p = g_test(obs, dist({n}))
        out.append(f"  only {n:4s} as letters   G={g:6.1f} p={p:.1e}")
    g, df, p = g_test(obs, dist(set(names)))
    out.append(f"  all digraphs as letters  G={g:6.1f} p={p:.1e}")
    out.append("(THE is the commonest English word and a 2-rune word only because TH is one rune; spelling TH as T+H "
               "moves it to 3 runes and removes most of the discrepancy, but not all of it.)")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    args = ap.parse_args()
    if args.fetch:
        fetch()
    segs = stats.SEGS
    lp2 = []
    for i in stats.UNSOLVED:
        c = lp.runes_of(segs[i])
        lp2 += [b - a for _, a, b in lp.word_spans(segs[i], c)]
    obs = hist(lp2)
    out = [f"LP2: {len(lp2)} words, mean {np.mean(lp2):.2f}. share by length 1..11,12+ (%):",
           "  " + "LP2".ljust(78) + " ".join(f"{x:5.1f}" for x in 100 * obs / obs.sum())]
    rows = []
    for name in CORPORA:
        ws = words_of(name)
        if ws is None:
            out.append(f"  {name}: corpus missing (run with --fetch)")
            continue
        for conv, fn in (("runes", rune_len), ("letters", len)):
            h = hist([fn(w) for w in ws[:60000]])
            g, df, p = g_test(obs, h)
            rows.append((p, f"{name} [{conv}]", h, g, df))
    # English two-parameter family on Emerson
    ws = words_of("English (Emerson, Essays I)")[:60000]
    fam = family(ws, np.linspace(0, 1, 11), None)
    best = None
    for r, base in fam.items():
        b = np.concatenate([base[1:BINS], [base[BINS:].sum()]])
        b = b / b.sum()
        for a in np.linspace(0, 0.8, 81):
            q = b.copy()
            ins = b.copy()
            ins[0] = 0                                   # one-rune words never get a null
            q = q - a * ins
            q[1:] += a * ins[:-1]
            q[-1] += a * ins[-1]
            g, df, p = g_test(obs, q, fitted=2)
            if best is None or g < best[0]:
                best = (g, df, p, r, a, q)
    g, df, p, r, a, q = best
    rows.append((p, f"English runes (digraphs spelled as letters in {100 * r:.0f}%), extra rune in {100 * a:.0f}% of multi-rune words "
                    f"(2 fitted)", q * obs.sum(), g, df))
    for p, name, h, g, df in sorted(rows, key=lambda t: -t[0]):
        out.append("  " + name.ljust(78)[:90] + " " + " ".join(f"{x:5.1f}" for x in 100 * h / h.sum())
                   + f"   G={g:7.1f} df={df} p={p:.1e}")
    out.append("(sorted by p; a model fits LP2 if p is not tiny. Two-parameter rows have 2 fewer df.)")
    out += mechanisms(obs, ws)
    out += digraph_expansion(obs, ws)
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "wordlen_languages.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
