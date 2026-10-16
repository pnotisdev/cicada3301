"""Which language / spelling convention reproduces LP2's word-length histogram?

wordlen.py showed that LP2's word lengths reject English written in Gematria Primus runes (G = 227, p ~ 1e-42) and
that "English runes plus one extra rune in ~40% of multi-rune words" fits (p = 0.025). This script widens the search
with public-domain corpora in other languages, spelled as runes (digraph-aware, as lp.word_to_key does) and as plain
letters, plus a two-parameter family on English:

    length = letters - (digraph runes collapsed with probability r) + (extra rune with probability a, multi-rune words)

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
    """Distribution over lengths for each (r, a): every digraph rune is kept with prob 1-r (collapsed to letters
    otherwise) and multi-rune words get an extra rune with prob a."""
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
    rows.append((p, f"English, digraph runes collapsed {100 * r:.0f}%, null rune in {100 * a:.0f}% of multi-rune words "
                    f"(2 fitted)", q * obs.sum(), g, df))
    for p, name, h, g, df in sorted(rows, key=lambda t: -t[0]):
        out.append("  " + name.ljust(78)[:90] + " " + " ".join(f"{x:5.1f}" for x in 100 * h / h.sum())
                   + f"   G={g:7.1f} df={df} p={p:.1e}")
    out.append("(sorted by p; a model fits LP2 if p is not tiny. Two-parameter rows have 2 fewer df.)")
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "wordlen_languages.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
