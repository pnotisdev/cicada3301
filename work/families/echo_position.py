"""Where do the within-word lag-5 coincidences and the lag-6 relation c' = 24 - 2c sit?  Keyless falsifier for position-independent echo mechanisms.

The two effects were found on within-word pairs only (results/analysis/lag5_affine.txt: lag 5 equality 105 observed / 72.6 expected, lag 6 relation 80 / 44.5). A mechanism that writes the echo at ANY position
(a rare copy / affine image of the rune 5 or 6 back, a structured collision re-roll) leaves the same excess on pairs that span a word boundary, which were not used to select the relation (an out-of-sample
check); a mechanism gated on the word-local position (earlier rune = the word's first rune, later rune = its 6th or 7th) puts all of it on one offset. Both are counted here.

For each category the observed hits are set against 300 shuffles of LP2's runes inside sections (the word cuts fixed), so the expectation includes the unigram and word-length structure.

    python work/families/echo_position.py          # -> results/analysis/echo_position.txt
"""
import os
import sys

import numpy as np

import fam_data as D

HERE = os.path.dirname(os.path.abspath(__file__))
N = D.N
S = 15
OUT = []


def say(s=""):
    print(s)
    OUT.append(s)


def categories(start, sid, L):
    """for every pair (i - L, i): section-ok, same word, local index of the earlier rune"""
    T = len(start)
    idx = np.arange(T)
    wid = np.cumsum(start)
    first = np.maximum.accumulate(np.where(start, idx, 0))
    loc = idx - first
    i = np.arange(L, T)
    ok = sid[i] == sid[i - L]
    same = ok & (wid[i] == wid[i - L])
    cross = ok & ~same
    return i, same, cross, loc[i - L]


def same_word(start, t, L):
    """True when the runes t - L and t lie in one word (no word start in (t - L, t])"""
    return not start[t - L + 1:t + 1].any()


def counts(C, i, same, cross, jloc, L, rel, only_s=False):
    h = C[i] == rel[C[i - L]]
    if only_s:
        h &= C[i] == S
    out = {"within": (int(h[same].sum()), int(same.sum())), "cross": (int(h[cross].sum()), int(cross.sum()))}
    for j in range(5):
        m = same & ((jloc == j) if j < 4 else (jloc >= 4))
        out[f"within, earlier rune at word position {j}{'+' if j == 4 else ''}"] = (int(h[m].sum()), int(m.sum()))
    return out


def main():
    runes, start, sid = D.lp2()
    rng = np.random.default_rng(11)
    eq = np.arange(N)
    aff = (27 * np.arange(N) + 24) % N          # c' = 24 - 2c
    tests = (("lag 5, equality (any rune)", 5, eq, False), ("lag 5, equality carried by S", 5, eq, True), ("lag 6, c' = 24 - 2c", 6, aff, False))
    say("LP2 sections 0.7-0.15, the project's word cuts; 300 shuffles inside sections; expected = shuffle mean, z = (observed - mean) / shuffle sd")
    say("")
    for name, L, rel, only_s in tests:
        i, same, cross, jloc = categories(start, sid, L)
        real = counts(runes, i, same, cross, jloc, L, rel, only_s)
        null = {k: [] for k in real}
        for _ in range(300):
            Cp = runes.copy()
            for k in np.unique(sid):
                m = sid == k
                Cp[m] = rng.permutation(Cp[m])
            for k, (h, n) in counts(Cp, i, same, cross, jloc, L, rel, only_s).items():
                null[k].append(h)
        say(f"{name}:")
        for k, (h, n) in real.items():
            mu, sd = np.mean(null[k]), max(np.std(null[k]), 1e-9)
            say(f"   {k:48s} pairs {n:6d}  hits {h:4d}  expected {mu:6.1f}  excess {h - mu:+6.1f}  z {(h - mu) / sd:+5.2f}")
        say("")
    say("Reading: the relation was selected on within-word pairs, so the 'within' z carries a selection bias (look-elsewhere P 0.005); the 'cross' rows are out of sample.")
    say("")
    say("Control: LP2's runes shuffled inside sections, then an echo planted at the observed within-word rate (lag 5: copy the rune 5 back, q 0.0153; lag 6: write 24 - 2c of the rune 6 back, q 0.0283), either at every position")
    say("or inside words only; the same categories are counted (mean of 20 plants; excess over the unplanted shuffle mean):")
    for name, L, rel, q in (("lag 5 equality", 5, eq, 0.0153), ("lag 6 relation", 6, aff, 0.0283)):
        i, same, cross, jloc = categories(start, sid, L)
        base = []
        planted = {"every position": [], "inside words only": []}
        for rep in range(20):
            Cp = runes.copy()
            for k in np.unique(sid):
                m = sid == k
                Cp[m] = rng.permutation(Cp[m])
            c0 = counts(Cp, i, same, cross, jloc, L, rel)
            base.append((c0["within"][0], c0["cross"][0]))
            for mode in planted:
                C2 = Cp.copy()
                for t in range(L, len(C2)):
                    if sid[t] != sid[t - L] or (mode == "inside words only" and not same_word(start, t, L)):
                        continue
                    if rng.random() < q:
                        C2[t] = rel[C2[t - L]]
                c1 = counts(C2, i, same, cross, jloc, L, rel)
                planted[mode].append((c1["within"][0], c1["cross"][0]))
        b = np.mean(base, axis=0)
        for mode, v in planted.items():
            d = np.mean(v, axis=0) - b
            say(f"   {name}, echo {mode:18s}: excess within {d[0]:+6.1f}, across word boundaries {d[1]:+6.1f}")
    dest = os.path.join(HERE, "..", "..", "results", "analysis")
    with open(os.path.join(dest, "echo_position.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    sys.exit(main())
