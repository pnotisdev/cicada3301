"""Is there a FIXED MAP between runes at a fixed distance? (the general case of the lag-5 equality and the lag-6 relation c' = 24 - 2c)

An evolving-alphabet cipher, a key that obeys a recurrence, or any cipher whose alphabet at position i + d is a fixed transformation g_d of the alphabet at i, makes equal plaintext
letters at distance d show up as pairs (c, g_d(c)): the 29 x 29 table of rune pairs has an excess along the graph of ONE permutation g_d, whatever g_d is (equality and affine maps
are special cases; the affine scan lag5_affine.py covers only those). For every relation family the permutation that maximises the excess over independence is found by the assignment
problem (Hungarian method) and its z (excess / sqrt of the expected count on the matched cells) is calibrated on 1,000 shuffles of LP2's runes inside sections.

Relation families: (a) within words, distance d = 1..12; (b) the same position j of word w and of word w + m (m = 1, 2, 3: an alphabet that evolves from word to word by a fixed map; the first
runes only, and all positions); (c) distance d across the whole section (not word bound), d = 1..12, for comparison.
Control: a random text with LP2's word structure in which c_i = g(c_(i-5)) with probability eps inside words, for a random permutation g and for equality.

    python work/families/perm_relations.py          # -> results/analysis/perm_relations.txt
"""
import os
import sys

import numpy as np
from scipy.optimize import linear_sum_assignment

import fam_data as D

HERE = os.path.dirname(os.path.abspath(__file__))
N = D.N
OUT = []


def say(s=""):
    print(s)
    OUT.append(s)


def pairs_within(C, start, sid, d):
    wid = np.cumsum(start)
    v = (wid[d:] == wid[:-d]) & (sid[d:] == sid[:-d])
    return C[:-d][v], C[d:][v]


def pairs_section(C, start, sid, d):
    v = sid[d:] == sid[:-d]
    return C[:-d][v], C[d:][v]


def pairs_words(C, start, sid, m, first_only=False):
    ws = np.flatnonzero(start)
    we = np.append(ws[1:], len(C))
    a, b = [], []
    for w in range(len(ws) - m):
        if sid[ws[w]] != sid[ws[w + m]]:
            continue
        n = 1 if first_only else min(we[w] - ws[w], we[w + m] - ws[w + m])
        a.extend(C[ws[w]:ws[w] + n]); b.extend(C[ws[w + m]:ws[w + m] + n])
    return np.array(a), np.array(b)


def best_perm(a, b, f):
    """(z, permutation, excess) of the permutation with the largest excess of the pair counts over independence"""
    T = np.bincount(a * N + b, minlength=N * N).reshape(N, N).astype(float)
    E = len(a) * np.outer(f, f)
    W = T - E
    r, c = linear_sum_assignment(-W)
    exc = W[r, c].sum()
    return exc / np.sqrt(max(E[r, c].sum(), 1e-9)), c, exc, T[r, c].sum(), E[r, c].sum()


FAMILIES = ([(f"within words, distance {d}", "within", d) for d in range(1, 13)] + [(f"across the section, distance {d}", "section", d) for d in range(1, 13)] +
            [(f"same position, word w and w+{m} (all positions)", "words", m) for m in (1, 2, 3)] + [(f"first runes of word w and w+{m}", "first", m) for m in (1, 2, 3)])


def get_pairs(kind, p, C, start, sid):
    return {"within": lambda: pairs_within(C, start, sid, p), "section": lambda: pairs_section(C, start, sid, p), "words": lambda: pairs_words(C, start, sid, p),
            "first": lambda: pairs_words(C, start, sid, p, True)}[kind]()


def statistics(C, start, sid):
    f = np.bincount(C, minlength=N) / len(C)
    return [best_perm(*get_pairs(kind, p, C, start, sid), f)[0] for _, kind, p in FAMILIES]


def describe(c):
    """how close the permutation c (c -> perm[c]) is to equality or to an affine map a c + b (number of the 29 runes it agrees on)"""
    best = (int((c == np.arange(N)).sum()), "equality", None)
    for a in range(1, N):
        for b in range(N):
            k = int((c == (a * np.arange(N) + b) % N).sum())
            if k > best[0]:
                best = (k, "affine", (a, b))
    return best


def main():
    runes, start, sid = D.lp2()
    rng = np.random.default_rng(21)
    obs = statistics(runes, start, sid)
    say(f"LP2: {len(runes)} runes, {int(start.sum())} words; {len(FAMILIES)} relation families; null = 1,000 shuffles of the runes inside each section")
    null = []
    for _ in range(1000):
        Cp = runes.copy()
        for k in np.unique(sid):
            m = sid == k
            Cp[m] = rng.permutation(Cp[m])
        null.append(statistics(Cp, start, sid))
    null = np.array(null)
    gmax = null.max(1)
    f = np.bincount(runes, minlength=N) / len(runes)
    say(f"{'relation':52s}{'pairs':>7s}{'z':>7s}{'P(null)':>9s}   matched pairs / expected   closest simple map")
    for i, (name, kind, p) in enumerate(FAMILIES):
        a, b = get_pairs(kind, p, runes, start, sid)
        z, perm, exc, o, e = best_perm(a, b, f)
        k, what, par = describe(perm)
        say(f"{name:52s}{len(a):7d}{z:+7.2f}{(null[:, i] >= z).mean():9.3f}   {int(o)} / {e:.1f}   {k} of 29 runes follow {what}" + (f" {par[0]} c + {par[1]}" if par else ""))
    top = max(obs)
    say(f"best z over all {len(FAMILIES)} families: {top:+.2f} ({FAMILIES[obs.index(top)][0]}); shuffle null of the best over families: median {np.median(gmax):+.2f}, "
        f"95th percentile {np.percentile(gmax, 95):+.2f}, P(null best >= observed) = {(gmax >= top).mean():.3f}")
    # ---- control: a random text with LP2's word structure and a planted fixed map at distance 5 inside words
    say("")
    say("control: random runes with LP2's word structure, c_i = g(c_(i-5)) inside words with probability eps (the family 'within words, distance 5'):")
    wid = np.cumsum(start)
    g_rand = rng.permutation(N)
    fam5 = [i for i, (_, kind, p) in enumerate(FAMILIES) if kind == "within" and p == 5][0]
    for label, g in (("equality", np.arange(N)), ("a random permutation", g_rand)):
        for eps in (0.015, 0.03, 0.06):
            zs = []
            for _ in range(20):
                C = rng.integers(0, N, len(runes))
                inw = np.flatnonzero((wid[5:] == wid[:-5]) & (sid[5:] == sid[:-5])) + 5
                pick = inw[rng.random(len(inw)) < eps]
                for i in pick:
                    C[i] = g[C[i - 5]]
                zs.append(statistics(C, start, sid)[fam5])
            say(f"   {label:22s} eps {eps}: z {np.mean(zs):+.1f} (min {np.min(zs):+.1f}); null 95th percentile of this family {np.percentile(null[:, fam5], 95):+.1f}; "
                f"detected in {int(np.sum(np.array(zs) > np.percentile(null[:, fam5], 99)))} of 20")
    dest = os.path.join(HERE, "..", "..", "results", "analysis")
    with open(os.path.join(dest, "perm_relations.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    sys.exit(main())
