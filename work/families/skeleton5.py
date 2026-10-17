"""Does LP2 carry the period-5 'twist skeleton' that an outside LLM derived from the lag-5 and lag-6 effects?  (W1 / W2 of the proposal; third-party idea, re-implemented here, not run as sent.)

Skeleton: inside a word the rune at in-word index j is T^(j mod 5)(M_w(p)) with T(x) = 24 - 2x (mod 29) and M_w a word-level affine key. Then for a pair (i - L, i) inside one word with the same plaintext rune,
c_i = T^d(c_(i-L)) with d = (i mod 5) - ((i - L) mod 5) in -4..4 (the in-word indices). L = 5 gives d = 0 (equality), L = 6 gives d = 1 (or -4), and EVERY other lag gives a relation too, fixed in advance
(no look-elsewhere): the predicted excess is about P(equal plaintext runes at that distance) - 1/29, i.e. +2-3% of the pairs at every lag from 2 up. This counts the hits of c_i = T^d(c_(i-L)) over all within-word pairs for
L = 1..12, against 100 shuffles of LP2 inside sections (word cuts fixed), and against plants of the proposal's W1 (English plaintext with LP2's section sizes) at the proposal's own parameters.

    python work/families/skeleton5.py          # -> results/analysis/skeleton5.txt
"""
import os
import sys

import numpy as np

import fam_data as D

HERE = os.path.dirname(os.path.abspath(__file__))
N = D.N
S = 15
LAGS = range(1, 13)
OUT = []


def say(s=""):
    print(s)
    OUT.append(s)


TP = {}
x = np.arange(N)
for d in range(0, 5):
    TP[d] = x.copy()
    x = (27 * x + 24) % N
inv = np.arange(N)
for d in range(1, 5):
    inv = (14 * inv + 12) % N                    # T^-1(y) = 14 y + 12
    TP[-d] = inv.copy()


def layout(start):
    T = len(start)
    idx = np.arange(T)
    first = np.maximum.accumulate(np.where(start, idx, 0))
    return np.cumsum(start), (idx - first)


def hits(C, wid, loc, L):
    """(hits, pairs) of c_i = T^d(c_(i-L)) over the pairs inside one word, d = class difference"""
    i = np.arange(L, len(C))
    same = wid[i] == wid[i - L]
    d = (loc[i] % 5) - (loc[i - L] % 5)
    pred = np.zeros(len(i), int)
    for dd in range(-4, 5):
        m = same & (d == dd)
        pred[m] = TP[dd][C[i - L][m]]
    return int((C[i] == pred)[same].sum()), int(same.sum())


def ss_pairs(C, wid):
    i = np.arange(5, len(C))
    return int(((wid[i] == wid[i - 5]) & (C[i] == S) & (C[i - 5] == S)).sum())


def plant_w1(plain, start, rng, p, qT):
    """the proposal's W1 (word key from the word's Gematria sum, class twist T^(j mod 5), anti-repeat through T), written out again"""
    c = np.empty(len(plain), int)
    ws = np.flatnonzero(start).tolist() + [len(plain)]
    prev = -1
    for s, e in zip(ws[:-1], ws[1:]):
        sw = int(plain[s:e].sum()) % N
        m, t = sw % 28 + 1, sw
        for j in range(s, e):
            if rng.random() >= p:
                y = (plain[j] + rng.integers(N)) % N
                if y == prev and rng.random() < 0.81:
                    y = (plain[j] + rng.integers(N)) % N
            else:
                y = (m * plain[j] + t) % N
                y = TP[(j - s) % 5][y]
                if (y == prev and rng.random() < 0.81) or rng.random() < qT:
                    y = (27 * y + 24) % N
            c[j] = y
            prev = y
    return c


def main():
    runes, start, sid = D.lp2()
    wid, loc = layout(start)
    rng = np.random.default_rng(23)
    eng, estart = D.english(200_000)
    ws = np.flatnonzero(estart)
    n = len(runes)
    say("LP2 sections 0.7-0.15; for each lag L the hits of c_i = T^d(c_(i-L)), T(x) = 24 - 2x, d = difference of the in-word indices mod 5 (L = 5: equality, L = 6: the relation), over the pairs inside one word")
    say("excess = hits - shuffle mean (100 shuffles inside sections); plants = the proposal's W1, English plaintext, mean of 10; z from the shuffle sd (LP2) or the plants' sd of the null")
    real = {L: hits(runes, wid, loc, L) for L in LAGS}
    null = {L: [] for L in LAGS}
    for _ in range(100):
        Cp = runes.copy()
        for k in np.unique(sid):
            m = sid == k
            Cp[m] = rng.permutation(Cp[m])
        for L in LAGS:
            null[L].append(hits(Cp, wid, loc, L)[0])
    settings = (("W1 p=1.0 qT=0", 1.0, 0.0), ("W1 p=0.9 qT=0.15 (the proposal's point)", 0.9, 0.15), ("W1 p=0.7 qT=0", 0.7, 0.0))
    plants = {name: {L: [] for L in LAGS} for name, _, _ in settings}      # excess RATE per pair over the p = 0 plant on the same English text
    ssp = {name: [] for name, _, _ in settings}
    ss_base = []
    for rep in range(10):
        s0 = int(rng.choice(ws[ws < len(eng) - n - 50]))
        plain, pst = eng[s0:s0 + n], estart[s0:s0 + n].copy()
        pst[0] = True
        pw, pl = layout(pst)
        C0 = plant_w1(plain, pst, rng, 0.0, 0.0)
        base = {L: hits(C0, pw, pl, L) for L in LAGS}
        ss_base.append(ss_pairs(C0, pw))
        for name, p, qT in settings:
            C = plant_w1(plain, pst, rng, p, qT)
            for L in LAGS:
                h, npairs = hits(C, pw, pl, L)
                plants[name][L].append((h - base[L][0]) / npairs)
            ssp[name].append(ss_pairs(C, pw))
    say(f"{'lag':>3} {'pairs':>6} {'LP2 excess':>10} {'z':>6}   " + "   ".join(f"{name[:26]:>26}" for name, _, _ in settings))
    say(f"{'':>3} {'':>6} {'':>10} {'':>6}   " + "   ".join(f"{'predicted at LP2 pairs (z of LP2 - pred)':>26}" for _ in settings))
    scale = {}
    for name, _, _ in settings:
        pred = {L: np.mean(plants[name][L]) * real[L][1] for L in LAGS}
        scale[name] = (sum(real[L][0] - np.mean(null[L]) for L in (5, 6))) / max(pred[5] + pred[6], 1e-9)
    for L in LAGS:
        h, npairs = real[L]
        mu, sd = np.mean(null[L]), max(np.std(null[L]), 1e-9)
        cells = []
        for name, _, _ in settings:
            pr = np.mean(plants[name][L]) * npairs
            cells.append(f"{pr:+9.1f} ({(h - mu - pr) / sd:+5.1f})".rjust(26))
        say(f"{L:>3} {npairs:>6} {h - mu:+10.1f} {(h - mu) / sd:+6.2f}   " + "   ".join(cells))
    say("")
    say("Strength fitted to lags 5 and 6 (LP2's excess over the prediction at the setting's own strength): " + "; ".join(f"{name[:22]} {scale[name]:.2f}" for name, _, _ in settings))
    say("Lags 1, 3, 4, 7, 8 are NOT used in the fit; at the fitted strength their predicted excess is that column times the factor above; the z at those lags is (LP2 excess - factor x prediction) / shuffle sd:")
    for name, _, _ in settings:
        zs = []
        for L in (1, 3, 4, 7, 8):
            h, npairs = real[L]
            mu, sd = np.mean(null[L]), max(np.std(null[L]), 1e-9)
            pr = np.mean(plants[name][L]) * npairs * scale[name]
            zs.append(f"lag {L}: pred {pr:+.1f} obs {h - mu:+.1f} z {(h - mu - pr) / sd:+.1f}")
        say(f"   {name[:30]:30s} " + "; ".join(zs))
    say("")
    say("S-S coincidences at lag 5 inside words: LP2 11 (shuffle mean about 2.4); p = 0 plants " + f"{np.mean(ss_base):.1f}; " + "; ".join(f"{name[:22]} {np.mean(ssp[name]):.1f}" for name, _, _ in settings))
    dest = os.path.join(HERE, "..", "..", "results", "analysis")
    with open(os.path.join(dest, "skeleton5.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    sys.exit(main())
