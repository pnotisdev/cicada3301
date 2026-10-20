"""Phase 25 part B: plaintext-side explanations of LP2's word-length histogram, no cipher insertion.

For each corpus (English texts, five other languages) and each spelling convention (every subset of the digraph runes TH, EO, NG/ING, OE, AE, IA(+IO->IA), EA
used as single runes; the rest letter by letter) the histogram of word lengths in runes (bins 1..11, 12+, as work/wordlen.py) is compared with LP2's by the
repo's G test (g_test(LP2 counts, model)). Reported: G for all-digraph, all-letter, TH-only, and the best of the 128 subsets per corpus (a 128-way look-elsewhere:
a null of the best subset is estimated by taking the best G of the same subsets against 20 resampled halves of LP2's own word list is NOT done; instead the
best-of-128 G is compared with the G spread of LP2's two halves against each other).

    python work/mech25/wordlen25.py       # -> results/analysis/wordlen25.txt
"""
import itertools
import os
import re
import sys
import unicodedata

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import lp  # noqa: E402
import stats  # noqa: E402
import wordlen as W  # noqa: E402

REF = os.path.join(HERE, "..", "ref")
CORP = {"Emerson (en)": "emerson_essays1.txt", "Walden (en)": "corpora/pg205.txt", "Origin (en)": "corpora/pg2009.txt", "Republic (en)": "corpora/pg1497.txt",
        "Paradise Lost (en)": "corpora/pg26.txt", "KJV (en)": "corpora/pg10.txt", "Beowulf transl. (en)": "corpora/pg16328.txt",
        "Latin (Aeneid)": "corpora/pg227.txt", "Latin (Caesar)": "corpora/pg218.txt", "German (Faust)": "corpora/pg2229.txt", "Italian (Dante)": "corpora/pg1012.txt",
        "Spanish (Quijote)": "corpora/pg2000.txt", "French (Misérables)": "corpora/pg17489.txt"}
ALIAS = {"V": 1, "K": 5, "Z": 15, "Q": 5}
SW = ["TH", "EO", "NG", "OE", "AE", "IA", "EA"]


def spell_len(word, on):
    """length in runes of one word; `on` = set of digraph switches in use"""
    w = word.upper().replace("QU", "CW")
    if "IA" in on:
        w = w.replace("IO", "IA")
    multi = []
    if "NG" in on: multi += ["ING", "NG"]
    multi += [d for d in ("TH", "EO", "OE", "AE", "IA", "EA") if d in on]
    multi.sort(key=lambda s: -len(s))
    n = 0
    while w:
        for d in multi:
            if w.startswith(d):
                w = w[len(d):]; break
        else:
            w = w[1:]
        n += 1
    return n


def words_of(path):
    t = open(os.path.join(REF, path), encoding="utf-8", errors="ignore").read()
    if "SELF-RELIANCE" in t:
        t = t[t.index("SELF-RELIANCE"):]
    a, b = t.find("*** START"), t.find("*** END")
    if a >= 0 and b > a:
        t = t[t.find("\n", a) + 1:b]
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    return [w for w in re.findall(r"[A-Za-z]+", t)][:200000]


def main():
    segs = lp.load_segments()
    lp2 = []
    for i in stats.UNSOLVED:
        c = lp.runes_of(segs[i])
        lp2 += [b - a for _, a, b in lp.word_spans(segs[i], c)]
    obs = W.hist(lp2)
    out = []

    def say(x=""):
        print(x, flush=True); out.append(x)

    rng = np.random.default_rng(25)
    halves = []
    for _ in range(200):
        p = rng.permutation(len(lp2)); h1 = W.hist(np.array(lp2)[p[:len(p) // 2]]); h2 = W.hist(np.array(lp2)[p[len(p) // 2:]])
        halves.append(W.g_test(2 * h1, h2) if False else W.g_test(h1, h2))
    say(f"LP2: {len(lp2)} words. Noise floor: G of one random half of LP2's words against the other half's histogram (df 11): mean {np.mean(halves):.1f}, 95th pct {np.percentile(halves, 95):.1f}"
        " (these halves are half-size, so a full-size model G is compared with the 'infinite-sample' model: G > ~25 is a real mismatch)")
    say("")
    say("corpus                 words    all-digraph  all-letter  TH only   TH+NG    best of 128 subsets (switches on)")
    allsub = [frozenset(s) for r in range(len(SW) + 1) for s in itertools.combinations(SW, r)]
    res = {}
    for name, path in CORP.items():
        ws = words_of(path)
        types = {}
        for w in ws:
            types[w.lower()] = types.get(w.lower(), 0) + 1
        def histo(on):
            h = np.zeros(W.BINS)
            for w, k in types.items():
                h[min(spell_len(w, on), W.BINS) - 1] += k
            return h
        G = {s: W.g_test(obs, histo(s))[0] for s in allsub}
        best = min(G, key=G.get)
        res[name] = (G, best)
        say(f"{name:22s} {len(ws):7d}  {G[frozenset(SW)]:8.1f}  {G[frozenset()]:9.1f}  {G[frozenset(['TH'])]:7.1f}  {G[frozenset(['TH','NG'])]:7.1f}   {G[best]:7.1f}  ({','.join(sorted(best)) or 'none'})")
    say("")
    say("Solved pages (LP1 solved sections, 1 reading): runes vs letters G 202.8 / 156.6 (work/wordlen.py)")
    with open(os.path.join(HERE, "..", "..", "results", "analysis", "wordlen25.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
