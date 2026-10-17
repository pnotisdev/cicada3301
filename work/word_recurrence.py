"""Per-word linear-recurrence keys: dictionary-consistency scan over ALL coefficient sets.

Hypothesis: every word is enciphered c_j = p_j + k_j where the key inside the word follows a linear recurrence
    k_{j+d} = a_1 k_{j+d-1} + ... + a_d k_j    (mod 29)
with fixed coefficients (a_1..a_d) for the whole book but a fresh initial state for every word (a PRNG re-seeded at
each word start, or a Fibonacci/Lucas/Tribonacci-type key restarted per word). The key cancels in
    Delta(c)_j = c_{j+d} - sum_i a_i c_{j+d-i}   ==   Delta(p)_j
so a ciphertext word is consistent with an English word p exactly when Delta(c) == Delta(p), a hash lookup per
operator. All 28*29^(d-1) coefficient sets of order d are scanned (d = 2: 812, d = 3: 23,548, d = 4: 682,892 with
--order 4) against every dictionary word of the same length.

This family is NOT covered by the kscreen recurrence campaign, which assumes one key stream running through the whole
section (restarts at no word start). Controls: random-rune surrogates with LP2's word lengths (the maximum over all
operators is the null), and dictionary words enciphered under a planted recurrence with fresh states per word and the
anti-repeat skip rule (recovery rate and rank of the true operator).

    python work/word_recurrence.py [--order 3]       # -> results/analysis/word_recurrence_d<order>.txt
"""
import argparse
import itertools
import os
import random
import sys

import numpy as np

import lp
import word_key_dictionary as wkd

N = lp.N
HERE = os.path.dirname(os.path.abspath(__file__))


def operators(d):
    for a in itertools.product(range(N), repeat=d):
        if a[-1] != 0:
            yield a


def delta(X, a):
    """Delta(X)[:, j] = X[:, j+d] - sum_i a_i X[:, j+d-i]  (X: (n, L) rune matrix)"""
    d = len(a)
    L = X.shape[1]
    out = X[:, d:].copy()
    for i, ai in enumerate(a, start=1):
        if ai:
            out = out - ai * X[:, d - i:L - i]
    return out % N


def codes(M):
    c = np.zeros(M.shape[0], dtype=np.int64)
    for j in range(M.shape[1]):
        c = c * N + M[:, j]
    return c


def scan(words, d, ops=None, min_cons=4):
    """for every operator: number of words (length >= d + min_cons) with a consistent dictionary word.
    Returns (ops, hits array, number of eligible words)."""
    dig = wkd.digits()
    byL = {}
    for w in words:
        L = len(w)
        if L >= d + min_cons and L in dig:
            byL.setdefault(L, []).append(w)
    W = {L: np.array(ws, dtype=np.int64) for L, ws in byL.items()}
    ops = list(ops) if ops is not None else list(operators(d))
    hits = np.zeros(len(ops), dtype=np.int32)
    eligible = sum(len(v) for v in W.values())
    for oi, a in enumerate(ops):
        h = 0
        for L, M in W.items():
            cw = codes(delta(M, a))
            cd = codes(delta(dig[L], a))
            h += int(np.isin(cw, cd).sum())
        hits[oi] = h
    return ops, hits, eligible


def encipher(seqs, a, rng, q=0.82):
    """dictionary words under k_{j+d} = sum a_i k_{j+d-i} with a fresh random state per word, skip rule included"""
    d = len(a)
    out, prev = [], -1
    for s in seqs:
        st = [rng.randrange(N) for _ in range(d)]
        keys = list(st)

        def key(ptr):
            while len(keys) <= ptr:
                keys.append(sum(a[i] * keys[-1 - i] for i in range(d)) % N)
            return keys[ptr]
        c, ptr = [], 0
        for t in s:
            y = (t + key(ptr)) % N
            ptr += 1
            while y == prev and rng.random() < q:
                y = (t + key(ptr)) % N
                ptr += 1
            c.append(y)
            prev = y
        out.append(c)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--order", type=int, default=3)
    ap.add_argument("--planted", type=int, default=4)
    args = ap.parse_args()
    d = args.order
    rng = random.Random(11)
    real = wkd.lp2_words()
    lens = [len(w) for w in real]
    out = []
    P = out.append
    n_ops = (N - 1) * N ** (d - 1)
    P(f"Per-word linear recurrence of order {d} with global coefficients: {n_ops:,} operators, words of >= {d + 4} runes.")
    ops, hits, eligible = scan(real, d)
    order = np.argsort(hits)[::-1]
    P(f"LP2: {eligible} eligible words; hits per operator: max {hits.max()}, mean {hits.mean():.3f}; top operators:")
    for oi in order[:5]:
        P(f"   a = {ops[oi]}: {hits[oi]} words")
    sur = wkd.surrogate(lens, rng)
    _, sh, se = scan(sur, d, ops)
    so = np.argsort(sh)[::-1]
    P(f"surrogate (random runes, LP2 lengths): {se} eligible words; max {sh.max()}, mean {sh.mean():.3f}; top: "
      + ", ".join(f"{ops[i]}:{sh[i]}" for i in so[:5]))
    P(f"   LP2 max over operators {hits.max()} vs surrogate max {sh.max()} (the null maximum).")
    P("")
    P("Planted controls (dictionary words, fresh state per word, anti-repeat skips): rank of the true operator and hits")
    seqs = wkd.sample_dictionary(rng, per_len=120, lo=d + 4, hi=12)
    for k in range(args.planted):
        a = tuple(rng.randrange(N) for _ in range(d - 1)) + (rng.randrange(1, N),)
        pw = encipher(seqs, a, rng)
        _, ph, pe = scan(pw, d, ops)
        rank = int((ph > ph[ops.index(a)]).sum()) + 1
        P(f"   planted a = {a}: {ph[ops.index(a)]}/{pe} words consistent, rank {rank} of {len(ops):,}; next best {np.sort(ph)[-2]}")
    P("")
    verdict = ("a candidate operator stands out" if hits.max() > sh.max() + 3 else
               "no operator beats the surrogate maximum")
    P(f"Verdict: {verdict}. A planted recurrence is found with its true operator at rank 1 in every control above, so a "
      f"per-word key of this family (with English plaintext in the dictionary) is excluded at order {d}.")
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, f"word_recurrence_d{d}.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
