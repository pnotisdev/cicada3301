"""Phase 25 part A2: (a) look-elsewhere over source rune x lag (2..8) for in-word equality; (b) S unigram count in LP2 and what a literal-S rule would cost;
(c) which English words carry the plaintext S..S pairs at lag 5; (d) the LP2 words that carry the 11 S,S hits.

    python work/mech25/lag5_s2.py     # -> results/analysis/lag5_s2.txt
"""
import collections
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "families"))
import measure as M  # noqa: E402
import wordlen25 as B  # noqa: E402
import lp  # noqa: E402

N, SR = 29, 15


def hits(c, wid, sid, L):
    i = np.arange(L, len(c))
    same = (sid[i] == sid[i - L]) & (wid[i] == wid[i - L])
    return np.bincount(c[i - L][same & (c[i] == c[i - L])], minlength=N), i[same & (c[i] == c[i - L])]


def shuf(c, sid, rng):
    c = c.copy()
    for k in np.unique(sid):
        m = sid == k
        c[m] = rng.permutation(c[m])
    return c


def main():
    ref, (c, start, sid) = M.lp2_stats()
    wid, loc = M.wordinfo(start)
    out = []

    def say(x=""):
        print(x, flush=True); out.append(x)

    rng = np.random.default_rng(2513)
    lags = range(2, 9)
    sh = np.array([[hits(shuf(c, sid, rng), wid, sid, L)[0] for L in lags] for _ in range(500)])   # (500, 7, 29)
    e = sh.mean(0); sd = np.sqrt(e + 0.5)
    obs = np.array([hits(c, wid, sid, L)[0] for L in lags])
    z = (obs - e) / sd
    zsh = ((sh - e) / sd).max(axis=(1, 2))
    li, ri = np.unravel_index(np.argmax(z), z.shape)
    say(f"(a) max z over 29 source runes x lags 2..8 (equality, in-word): LP2 {z.max():.2f} at lag {li + 2}, source {lp.LATIN[ri]} ({obs[li, ri]} hits, {e[li, ri]:.1f} expected)")
    say(f"    shuffle null (500) of the same maximum: median {np.median(zsh):.2f}, 95th pct {np.percentile(zsh, 95):.2f}, max {zsh.max():.2f}; P(null >= LP2) = {(zsh >= z.max()).mean():.4f} (floor 1/500)")
    say("    next largest cells: " + ", ".join(f"lag {a + 2} {lp.LATIN[b]} z {z[a, b]:+.2f}" for a, b in sorted(np.ndindex(z.shape), key=lambda t: -z[t])[1:5]))
    nS = int((c == SR).sum())
    say(f"(b) LP2 unigram S: {nS} of {len(c)} (flat expectation {len(c) / N:.0f} +- {np.sqrt(len(c) / N):.0f}); English S share is 0.07-0.09, so a literal-S rule for a fraction g of S would add ~ g*{0.08 * len(c):.0f} S runes: g <= {(2 * np.sqrt(len(c) / N)) / (0.08 * len(c)):.3f} at 2 sd")
    # plaintext S..S words
    cnt = collections.Counter()
    tot = 0
    for w in B.words_of("emerson_essays1.txt"):
        r = lp.word_to_key(w.upper().replace("IO", "IA"))
        for i in range(5, len(r)):
            if r[i] == SR and r[i - 5] == SR:
                cnt[w.lower()] += 1; tot += 1
    say(f"(c) Emerson, plaintext in-word lag-5 S..S pairs: {tot}; top words " + ", ".join(f"{w} {k}" for w, k in cnt.most_common(12)))
    # LP2 hits
    h, idx = hits(c, wid, sid, 5)
    ids = idx[c[idx] == SR]
    words = collections.defaultdict(list)
    for j in ids:
        words[wid[j]].append(j)
    segs = lp.load_segments()
    say(f"(d) LP2 S,S lag-5 hits: {len(ids)}; word positions of the later S: {sorted(int(loc[j]) for j in ids)}; words (rune strings):")
    for w, js in words.items():
        a = np.flatnonzero(wid == w)
        say("    " + "".join(lp.LATIN[x] + "." for x in c[a]) + f"  (later S at {[int(loc[j]) for j in js]})")
    with open(os.path.join(HERE, "..", "..", "results", "analysis", "lag5_s2.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
