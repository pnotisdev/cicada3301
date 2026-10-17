"""Probe 3 (2026-10-17, laptop): two keyless exclusions.

H-MULT (multiplicative keystream): c = D(p) * k (mod 29) with k != 0, any plaintext alphabet D, any key, with or
without the anti-repeat rule. Then c = 0 (rune F) exactly where the plaintext has the one letter X = D^-1(0), so the
rune F of LP2 must have the frequency and the word-position profile of a single plaintext letter. Test: compare F's
profile in LP2 (share of all runes, of 1-rune words, of word-initial and word-final positions, of 2-rune words) with
every English letter's profile in Emerson (GP runes), by a G-test against the hypothesis "F is letter X".

H-CUM (uniformised running key): k_i = t_1 + ... + t_i (mod 29) for an English text t (or c = cumulative sum of
p + t, the chain form). The step c[i+1] - c[i] is then p[i+1] - p[i] + t[i+1] (or p + t), whose distribution is not
flat. LP2's step histogram is flat apart from the missing zero (chi-square 41 on 27 df). Simulated with Emerson as
plaintext and other Gutenberg texts as t, under the skip rule.
"""
import math
import os
import random
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, WORK)
sys.path.insert(0, HERE)
import lp  # noqa: E402
from probe1 import english_words, words_of  # noqa: E402
from probe2 import text_runes  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
N = lp.N
LP2 = list(range(7, 16))


def profile(words, sym):
    """Counts (in symbol-occurrence classes) for one symbol: 1-rune word, initial, final, medial; and totals."""
    one = sum(1 for w in words if len(w) == 1 and w[0] == sym)
    ini = sum(1 for w in words if len(w) > 1 and w[0] == sym)
    fin = sum(1 for w in words if len(w) > 1 and w[-1] == sym)
    med = sum(1 for w in words if len(w) > 2 for x in w[1:-1] if x == sym)
    return [one, ini, fin, med]


def slots(words):
    one = sum(1 for w in words if len(w) == 1)
    multi = sum(1 for w in words if len(w) > 1)
    med = sum(len(w) - 2 for w in words if len(w) > 2)
    return [one, multi, multi, med]


def g_test(obs, tot, p):
    """G statistic of observed counts obs (out of tot slots per class) against class probabilities p."""
    g = 0.0
    for o, n, q in zip(obs, tot, p):
        q = min(max(q, 1e-9), 1 - 1e-9)
        e = n * q
        if o > 0:
            g += 2 * o * math.log(o / e)
        if n - o > 0:
            g += 2 * (n - o) * math.log((n - o) / (n - e))
    return g


def mult_test():
    segs = lp.load_segments()
    lw = [w for i in LP2 for w in words_of(segs[i])]
    ew = english_words()
    lslots = slots(lw)
    eslots = slots(ew)
    fobs = profile(lw, 0)
    print("H-MULT: profile of rune F in LP2 [1-rune words, word-initial, word-final, medial] =", fobs,
          "of slots", lslots)
    print(f"  F share of runes {100 * sum(fobs[:1] + fobs[1:]) / sum(map(len, lw)):.2f}%;"
          f" a uniform symbol would give G small (shown as 'uniform' below)")
    rows = []
    for x in range(N):
        prof = profile(ew, x)
        p = [o / n for o, n in zip(prof, eslots)]
        rows.append((g_test(fobs, lslots, p), lp.LATIN[x], p))
    rows.sort()
    unif = g_test(fobs, lslots, [1 / N] * 4)
    print(f"  G against 'F is a uniform cipher symbol': {unif:.1f} (4 df)")
    print("  best English letters X (G, 4 df; p < 0.001 needs G > 18.5):")
    for g, lat, p in rows[:6]:
        print(f"    X = {lat:3s} G = {g:7.1f}  expected profile shares " + " ".join(f"{100 * q:.2f}%" for q in p))
    # any numbering of the runes puts the fixed point on some rune: try every rune against every letter
    eprof = {x: [o / n for o, n in zip(profile(ew, x), eslots)] for x in range(N)}
    best = []
    for r in range(N):
        obs = profile(lw, r)
        g, x = min((g_test(obs, lslots, eprof[x]), x) for x in range(N))
        best.append((g, lp.LATIN[r], lp.LATIN[x], obs))
    best.sort()
    print("  every rune as the fixed point (29 runes x 29 letters), best fits:")
    for g, r, x, obs in best[:4]:
        print(f"    rune {r:3s} ~ letter {x:3s} G = {g:6.1f}  profile {obs}")
    return rows


def cum_test():
    R = random.Random(1033)
    emer = text_runes(os.path.join(WORK, "ref", "emerson_essays1.txt"))
    corp = os.path.join(WORK, "ref", "corpora")
    n = 12956
    print("\nH-CUM: chi-square (27 df, LP2 = 41.2) of the step histogram without bin 0, n = 12,956, skip rule q = 0.8")
    for f in sorted(os.listdir(corp))[:5]:
        t = text_runes(os.path.join(corp, f), limit=3 * n)
        if len(t) < 2 * n:
            continue
        off = R.randrange(0, len(emer) - n)
        p = emer[off:off + n]
        for form in ("p + cumsum(t)", "cumsum(p + t)"):
            ks, s = [], 0
            for x in t:
                s = (s + x) % N
                ks.append(s)
            c, j = [], 0
            for x in p:
                if form == "p + cumsum(t)":
                    y = (x + ks[j]) % N
                    j += 1
                    while c and y == c[-1] and R.random() < 0.8:
                        y = (x + ks[j]) % N
                        j += 1
                else:
                    prev = c[-1] if c else 0
                    y = (prev + x + t[j]) % N
                    j += 1
                    while c and y == c[-1] and R.random() < 0.8:
                        y = (prev + x + t[j]) % N
                        j += 1
                c.append(y)
            st = Counter((b - a) % N for a, b in zip(c, c[1:]))
            m = sum(st.values()) - st[0]
            e = m / 28
            chi = sum((st[b] - e) ** 2 / e for b in range(1, N))
            print(f"  t = {f:12s} {form:14s} chi-square {chi:8.1f}")


if __name__ == "__main__":
    mult_test()
    cum_test()
