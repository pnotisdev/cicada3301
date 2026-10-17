"""Is the within-word lag-5 / lag-6 excess spread evenly over the 29 source runes, as a two-tap echo rule (apply T, or copy, whatever the rune is) predicts?

An outside LLM's mechanisms A (ciphertext echo at the offsets 5 and 6) and B (rewrite of plaintext repeats) apply the affine image T(x) = 24 - 2x of the rune 6 back (or copy the rune 5 back) to ANY rune, so the excess hits are proportional to the number of pairs with
each source value. The repository's notes say 'three pairs drive' the lag-6 relation, which is the opposite. Q = sum over the 29 source values c of (hits_c - expected_c - s * pairs_c)^2 / (expected_c + 1), s = the overall excess per pair, measures the departure from an even spread.
Calibrated on (a) shuffles of LP2 and (b) plants of the uniform echo at the observed within-word rate into shuffled LP2.

    python work/families/echo_values.py          # -> results/analysis/echo_values.txt
"""
import os
import sys

import numpy as np

import fam_data as D

HERE = os.path.dirname(os.path.abspath(__file__))
N = D.N
OUT = []


def say(s=""):
    print(s)
    OUT.append(s)


def pairs(start, sid, L):
    T = len(start)
    idx = np.arange(T)
    wid = np.cumsum(start)
    i = np.arange(L, T)
    return i, (sid[i] == sid[i - L]) & (wid[i] == wid[i - L])


def by_value(C, i, same, L, rel):
    src = C[i - L][same]
    h = (C[i][same] == rel[src])
    return np.bincount(src, minlength=N), np.bincount(src[h], minlength=N)


def Q(n, h, e, drop=()):
    keep = np.ones(N, bool)
    keep[list(drop)] = False
    n, h, e = n[keep], h[keep], e[keep]
    s = (h.sum() - e.sum()) / n.sum()
    return float((((h - e - s * n) ** 2) / (e + 1.0)).sum()), float(s)


def plant(C0, i, same, L, rel, q, rng):
    """uniform echo: inside words, with probability q the rune becomes rel(rune L back) (in order, so echoes may chain)"""
    C = C0.copy()
    for t, ok in zip(i, same):
        if ok and rng.random() < q:
            C[t] = rel[C[t - L]]
    return C


def main():
    runes, start, sid = D.lp2()
    rng = np.random.default_rng(31)
    eq = np.arange(N)
    aff = (27 * np.arange(N) + 24) % N
    say("LP2 sections 0.7-0.15, within-word pairs. Q measures the departure of the hit excess from an even spread over the 29 source runes (large = concentrated); 200 shuffles and 100 plants of the uniform echo")
    say("")
    for name, L, rel, q in (("lag 6, c' = 24 - 2c", 6, aff, 0.0272), ("lag 5, equality", 5, eq, 0.0148)):
        i, same = pairs(start, sid, L)
        n_real, h_real = by_value(runes, i, same, L, rel)
        e_sum = np.zeros(N)
        shuf = []
        for _ in range(200):
            Cp = runes.copy()
            for k in np.unique(sid):
                m = sid == k
                Cp[m] = rng.permutation(Cp[m])
            shuf.append(by_value(Cp, i, same, L, rel)[1])
        e = np.mean(shuf, axis=0)
        q_real, s_real = Q(n_real, h_real, e)
        q_shuf = []
        for h in shuf[:100]:
            q_shuf.append(Q(n_real, h, e)[0])
        q_pl = []
        for _ in range(100):
            Cp = runes.copy()
            for k in np.unique(sid):
                m = sid == k
                Cp[m] = rng.permutation(Cp[m])
            Cp = plant(Cp, i, same, L, rel, q, rng)
            n_p, h_p = by_value(Cp, i, same, L, rel)
            q_pl.append(Q(n_p, h_p, e)[0])
        say(f"{name}: pairs {int(n_real.sum())}, hits {int(h_real.sum())}, expected {e.sum():.1f}, excess per pair s = {s_real:.4f}")
        say(f"   Q: LP2 {q_real:.1f};  shuffles (no echo, their own fitted s) mean {np.mean(q_shuf):.1f}, 95th pct {np.percentile(q_shuf, 95):.1f};  uniform-echo plants mean {np.mean(q_pl):.1f}, 95th pct {np.percentile(q_pl, 95):.1f}, max {np.max(q_pl):.1f}")
        say(f"   P(plant Q >= LP2 Q) = {(np.array(q_pl) >= q_real).mean():.2f}, P(shuffle Q >= LP2 Q) = {(np.array(q_shuf) >= q_real).mean():.2f}")
        order = np.argsort(-(h_real - e))
        say("   largest excesses (source rune: pairs, hits, expected): " + "; ".join(f"{c}: {int(n_real[c])}, {int(h_real[c])}, {e[c]:.1f}" for c in order[:5]))
        top3 = float((h_real - e)[order[:3]].sum())
        say(f"   the three largest source values carry {top3:+.1f} of the total excess {float((h_real - e).sum()):+.1f}")
        if L == 5:
            q_real2 = Q(n_real, h_real, e, drop=(15,))[0]
            q_pl2 = []
            for _ in range(100):
                Cp = runes.copy()
                for k in np.unique(sid):
                    m = sid == k
                    Cp[m] = rng.permutation(Cp[m])
                Cp = plant(Cp, i, same, L, rel, q, rng)
                n_p, h_p = by_value(Cp, i, same, L, rel)
                q_pl2.append(Q(n_p, h_p, e, drop=(15,))[0])
            say(f"   without source rune S (15; mechanism A has a separate S branch): Q LP2 {q_real2:.1f}; uniform-echo plants mean {np.mean(q_pl2):.1f}, 95th pct {np.percentile(q_pl2, 95):.1f}; P(plant Q >= LP2 Q) = {(np.array(q_pl2) >= q_real2).mean():.2f}")
        say("")
    dest = os.path.join(HERE, "..", "..", "results", "analysis")
    with open(os.path.join(dest, "echo_values.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    sys.exit(main())
