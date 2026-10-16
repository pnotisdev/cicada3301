"""Repeated bigrams inside words: LP2's distance-5 echo is clustered, and looks like English leaking through.

within_word.py (distance-5 coincidence, +3.7 sigma pooled) is the single positive statistical signal in LP2. This
script adds three things:

1. **Clustering.** Where a rune equals the one five positions earlier, the *next* pair very often does too: inside
   words, the bigram at positions (j, j+1) equals the bigram at (j+5, j+6) 9 times against 1.6 expected (Poisson
   P ~ 1e-4; a chain-null Monte Carlo agrees). Other lags are at chance. Outside words (bigram windows crossing a
   word boundary) lag 5 is at chance too, so the effect is word-internal.
2. **A yardstick.** English written in runes has the same internal structure at lag 5 (coincidence 6.4%, bigram
   repeats 6x the chance level). LP2's bigram-repeat ratio at lag 5 (6.0) matches that, while its coincidence rate
   (4.9%) is half way between chance (3.5%) and English (6.4%).
3. **Two mechanism checks** (simulated English enciphered under the anti-repeat rule), each compared with LP2 on
   the same features: a *per-word random key of period 5* (reproduces the bigram clustering and a coincidence rate
   that is too high, but the lag-5 difference histogram it predicts is far from flat, which LP2's is), and a *copy
   process* (rune j copies rune j-5 with probability rho: matches a coincidence rate, but not the bigram clustering).

    python work/word_internal_repeats.py [--reps 20000]     # -> results/analysis/word_internal_repeats.txt
"""
import argparse
import os
import random
import re
import sys
from collections import Counter
from math import sqrt

import numpy as np
from scipy.stats import poisson

import lp
import stats

N = lp.N
HERE = os.path.dirname(os.path.abspath(__file__))


def lp2_words():
    out = []
    for i in stats.UNSOLVED:
        c = lp.runes_of(stats.SEGS[i])
        out += [c[a:b] for _, a, b in lp.word_spans(stats.SEGS[i], c)]
    return out


def english_words(limit=60000):
    path = os.path.join(HERE, "ref", "emerson_essays1.txt")
    with open(path, encoding="utf-8") as f:
        txt = f.read()
    txt = txt[txt.index("SELF-RELIANCE"):].split("*** END OF")[0]
    seqs = (lp.word_to_key(w.upper().replace("IO", "IA")) for w in re.findall(r"[A-Za-z]+", txt))
    return [s for s in seqs if s][:limit]


def flatten(words):
    """runes and word ids as arrays"""
    r = np.array([x for w in words for x in w])
    wid = np.repeat(np.arange(len(words)), [len(w) for w in words])
    return r, wid


def bigram_pairs(r, wid, g):
    """number of (j, j+g) bigram-window pairs lying inside single words, and how many are equal"""
    n = len(r) - g - 1
    inside = (wid[:n] == wid[1:n + 1]) & (wid[:n] == wid[g:g + n]) & (wid[:n] == wid[g + 1:g + 1 + n])
    eq = (r[:n] == r[g:g + n]) & (r[1:n + 1] == r[g + 1:g + 1 + n])
    return int(inside.sum()), int((eq & inside).sum())


def coincidence(r, wid, g):
    n = len(r) - g
    inside = wid[:n] == wid[g:]
    eq = r[:n] == r[g:]
    return int(inside.sum()), int((eq & inside).sum())


def chain_null(wid, n, rng, doublet=0.0066):
    """random stream with LP2's anti-repeat marginal: c = cumsum of steps, step 0 has probability `doublet`"""
    p = np.full(N, (1 - doublet) / (N - 1))
    p[0] = doublet
    steps = rng.choice(N, size=n, p=p)
    return np.cumsum(steps) % N


def simulate(seqs, model, rng, q=0.82, period=5, rho=0.0):
    """English words enciphered under the skip rule; model: 'otp', 'wordkey' (random key of `period` per word,
    restarted at every word) or 'copy' (rune j = rune j-5 with probability rho, else OTP)."""
    out, prev = [], -1
    for s in seqs:
        key = [rng.randrange(N) for _ in range(period)] if model == "wordkey" else None
        c, ptr = [], 0
        for j, t in enumerate(s):
            if model == "copy" and j >= 5 and rng.random() < rho:
                y = c[j - 5]
            else:
                y = (t + (rng.randrange(N) if key is None else key[ptr % period])) % N
                ptr += 1
                while y == prev and rng.random() < q:
                    y = (t + (rng.randrange(N) if key is None else key[ptr % period])) % N
                    ptr += 1
            c.append(y)
            prev = y
        out.append(c)
    return out


def features(words):
    r, wid = flatten(words)
    f = {}
    for g in range(2, 8):
        n, e = coincidence(r, wid, g)
        f[f"c{g}"] = 100 * e / n
    n2, o2 = bigram_pairs(r, wid, 5)
    f["bg5_ratio"] = o2 / (n2 / 841.0)
    h = np.zeros(N)
    for w in words:
        for j in range(len(w) - 5):
            h[(w[j + 5] - w[j]) % N] += 1
    h2 = h[1:]
    e2 = h2.sum() / 28
    f["d5_chi2_per_df"] = float(((h2 - e2) ** 2 / e2).sum() / 27)
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20000)
    args = ap.parse_args()
    words = lp2_words()
    r, wid = flatten(words)
    f = np.bincount(r, minlength=N) / len(r)
    S = float((f ** 2).sum())
    out = []
    P = out.append
    P(f"LP2: {len(words)} words, {len(r)} runes; chance coincidence S = {100 * S:.3f}%")
    P("")
    P("A. Inside words, by lag g: coincidences (rune j == rune j+g) and repeated bigrams ((j,j+1) == (j+g,j+g+1)).")
    P("   expected bigram repeats = pairs * S^2; MC = fraction of chain-null streams (LP2's word structure, anti-repeat "
      f"marginal) with at least as many, {args.reps} streams")
    rng = np.random.default_rng(7)
    null_bg = {g: [] for g in range(2, 10)}
    for _ in range(args.reps):
        rn = chain_null(wid, len(r), rng)
        for g in range(2, 10):
            null_bg[g].append(bigram_pairs(rn, wid, g)[1])
    P("   g | coinc. pairs equal  rate%     z | bigram pairs  obs   exp  Poisson P   MC P")
    for g in range(2, 10):
        n, e = coincidence(r, wid, g)
        z = (e - n * S) / sqrt(n * S * (1 - S))
        n2, o2 = bigram_pairs(r, wid, g)
        exp = n2 * S * S
        mc = (np.sum(np.array(null_bg[g]) >= o2) + 1) / (args.reps + 1)
        P(f"  {g:2d} | {n:12d} {e:5d} {100 * e / n:6.2f} {z:+5.1f} | {n2:11d} {o2:5d} {exp:5.2f}  {poisson.sf(o2 - 1, exp):9.1e}  {mc:.1e}")
    P("   (9 lags tested: multiply the lag-5 P by 8 for a look-elsewhere correction)")
    P("")
    P("B. Where does the lag-5 excess live? bigram windows, lag 5:")
    n_all = len(r) - 6
    eq_all = (r[:n_all] == r[5:5 + n_all]) & (r[1:n_all + 1] == r[6:6 + n_all])
    n_in, o_in = bigram_pairs(r, wid, 5)
    P(f"   whole stream: {int(eq_all.sum())} repeats, {n_all * S * S:.1f} expected;  both windows inside one word: {o_in} "
      f"observed, {n_in * S * S:.2f} expected;  all other windows: {int(eq_all.sum()) - o_in} observed, "
      f"{(n_all - n_in) * S * S:.1f} expected")
    P("")
    P("C. The words with a repeated bigram at lag 5 (rune values and letters):")
    for w in words:
        if any(w[j] == w[j + 5] and w[j + 1] == w[j + 6] for j in range(len(w) - 6)):
            P("   " + " ".join(f"{x:2d}" for x in w) + "   " + "".join(lp.LATIN[x] for x in w))
    P("")
    eng = english_words()
    re_, we_ = flatten(eng)
    P("D. English in runes (Emerson), inside words: coincidence rate and bigram-repeat ratio to the chance level:")
    for g in range(2, 9):
        n, e = coincidence(re_, we_, g)
        n2, o2 = bigram_pairs(re_, we_, g)
        n_l, e_l = coincidence(r, wid, g)
        n2_l, o2_l = bigram_pairs(r, wid, g)
        P(f"   lag {g}: English {100 * e / n:5.2f}%, ratio {o2 / (n2 / 841):5.1f}   |   LP2 {100 * e_l / n_l:5.2f}%, "
          f"ratio {o2_l / (n2_l / 841):5.1f}")
    P("")
    P("E. Mechanism checks (20,000 English words enciphered under the anti-repeat rule), same features as LP2:")
    seqs = eng[:20000]
    rr = random.Random(5)
    P("   " + "model".ljust(30) + "  c2    c3    c4    c5    c6    c7   bg5 ratio  lag-5 diff chi2/df (excl. d=0)")
    real = features(words)

    def row(name, fe):
        P("   " + name.ljust(30) + "".join(f" {fe[f'c{g}']:5.2f}" for g in range(2, 8))
          + f"   {fe['bg5_ratio']:7.2f}   {fe['d5_chi2_per_df']:8.2f}")
    row("LP2", real)
    row("OTP key (control)", features(simulate(seqs, "otp", rr)))
    row("per-word random key, period 5", features(simulate(seqs, "wordkey", rr, period=5)))
    row("per-word random key, period 4", features(simulate(seqs, "wordkey", rr, period=4)))
    row("copy rune j-5, rho = 0.015", features(simulate(seqs, "copy", rr, rho=0.015)))
    row("copy rune j-5, rho = 0.03", features(simulate(seqs, "copy", rr, rho=0.03)))
    P("   (the chi2/df of LP2 comes from 2,073 pairs and has a standard deviation of 0.27; the simulations use ~15,000 "
      "pairs, so their chi2/df excess shrinks by ~7x when scaled to LP2's size)")
    P("")
    P("Reading: the lag-5 bigram clustering is significant (P ~ 1e-4 before the look-elsewhere factor) and word-internal. "
      "A per-word period-5 key reproduces the clustering but, if aligned in more than ~25% of the pairs, predicts a "
      "lag-5 difference histogram that LP2 does not have; an independent copy process does not reproduce the "
      "clustering. No mechanism is identified. The finding is a constraint for any model of the key: whatever it is, it "
      "repeats runes at distance five inside words and not across word boundaries.")
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "word_internal_repeats.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
