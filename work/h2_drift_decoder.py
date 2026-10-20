"""Phase 32 prototype: a drift-aware, tableau-invariant statistic for H2 (c_i = T[k_j][p_i], T an unknown tableau).

Spec and gate: work/log/phase32_h2_drift.md. Nothing in LP2 is solved and LP2 is NOT decoded here.

Idea (the phase 23 beam with the shift integrated out replaced by a permutation integrated out): ciphertext runes grouped by
the key value under them are, at the right stream and offset, each a *relabelling* of the plaintext (any permutation of the
29 runes). The class's rune counts n_a are then a permuted plaintext histogram, so the class is scored by the sequential
Dirichlet-multinomial predictive 29 (n_a + alpha) / (n + 29 alpha), alpha = 1.22 (matches English sum f^2 = 0.061):
invariant to the tableau and to the key map, O(1) per branch. The key pointer branches +0/+1/+2 per rune (skip cost
ln(0.81/29) each) and the beam keeps the best `per_ptr` histories per pointer, as work/book_key_decoder.py (read-only).

Usage: python work/h2_drift_decoder.py [--quick]    (1 core)
"""
import os
import sys
import time

import numpy as np
from numba import njit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lp  # noqa: E402
from book_key_flatness import HERE, gutenberg_body, to_runes  # noqa: E402

N = lp.N
LN_SKIP = float(np.log(0.81 / N))
ALPHA = 1.22


@njit(cache=True)
def beam_h2(c, key, o, R, alpha, beam, ln_skip, per_ptr=8, spread=8):
    """Best-path score (nats vs a uniform cipher) and the key pointer per rune. key values must lie in 0..R-1."""
    n, Q = len(c), 29
    lnA = np.log(np.arange(n + 2) + alpha)
    lnB = np.log(np.arange(n + 2) + Q * alpha)
    lnQ = np.log(29.0)
    C = np.zeros((beam, R, Q), dtype=np.int16)
    T = np.zeros((beam, R), dtype=np.int16)
    S = np.zeros(beam)
    J = np.zeros(beam, dtype=np.int64)
    for u in range(spread):
        J[u] = o + u
    W = spread
    nc = 3 * beam
    cs, cj, cw = np.empty(nc), np.empty(nc, np.int64), np.empty(nc, np.int64)
    C2, T2, S2, J2 = np.empty_like(C), np.empty_like(T), np.empty_like(S), np.empty_like(J)
    par = np.zeros((n, beam), dtype=np.int64)
    ptr = np.zeros((n, beam), dtype=np.int64)
    for i in range(n):
        x = c[i]
        m = 0
        for w in range(W):
            for dk in range(3):
                k = J[w] + dk
                if k >= len(key):
                    continue
                g = key[k]
                cs[m] = S[w] + lnQ + lnA[C[w, g, x]] - lnB[T[w, g]] + dk * ln_skip
                cj[m], cw[m] = k, w
                m += 1
        order = np.argsort(-cs[:m])
        W2 = 0
        for t in order:
            same = 0
            for u in range(W2):
                if J2[u] == cj[t] + 1:
                    same += 1
            if same >= per_ptr:
                continue
            w = cw[t]
            g = key[cj[t]]
            C2[W2] = C[w]
            T2[W2] = T[w]
            C2[W2, g, x] += 1
            T2[W2, g] += 1
            S2[W2] = cs[t]
            J2[W2] = cj[t] + 1
            par[i, W2] = w
            ptr[i, W2] = cj[t]
            W2 += 1
            if W2 == beam:
                break
        if W2 == 0:
            return -1e18, np.zeros(n, np.int64)
        C[:W2], T[:W2], S[:W2], J[:W2] = C2[:W2], T2[:W2], S2[:W2], J2[:W2]
        W = W2
    path = np.zeros(n, dtype=np.int64)
    w = 0
    for i in range(n - 1, -1, -1):
        path[i] = ptr[i, w]
        w = par[i, w]
    return S[0], path


def coincidence(c, key, o):
    """The old H2 statistic (work/proposals/h2_coincidence): pairs with equal key value and equal cipher rune, no drift."""
    cell = np.bincount(key[o:o + len(c)] * N + c, minlength=N * N)
    return int((cell * (cell - 1) // 2).sum())


def encrypt_tableau(p, key, T, rng, q=0.81):
    """c_i = T[key_j][p_i]; if c_i == c_(i-1) take the next key value with probability q (repeat). Returns c, pointers used."""
    c = np.empty(len(p), dtype=np.int64)
    used = np.empty(len(p), dtype=np.int64)
    j, prev = 0, -1
    for i, pi in enumerate(p):
        ci = T[key[j], pi]
        while ci == prev and rng.random() < q:
            j += 1
            ci = T[key[j], pi]
        c[i], used[i], prev, j = ci, j, ci, j + 1
    return c, used


def streams(rng):
    pr = []
    k = 2
    while len(pr) < 30000:
        if all(k % d for d in range(2, int(k ** .5) + 1)):
            pr.append(k)
        k += 1
    return {"uniform R=29": rng.integers(0, 29, 30000), "primes mod 29": np.array(pr) % 29}


def job(args):
    n, seed, additive = args
    rng = np.random.default_rng(seed)
    em = open(os.path.join(HERE, "ref", "emerson_essays1.txt"), encoding="utf-8", errors="ignore").read()
    P = to_runes(em)
    ST = streams(rng)
    R, SP = 29, 8
    rows = []
    for sname, key in ST.items():
        reps = 24
        true, old_z, nulls, acc = [], [], {"offset": [], "uniform": []}, []
        t0 = time.perf_counter()
        for r in range(reps):
            T = np.array([rng.permutation(N) for _ in range(R)])
            if additive:
                T = np.array([(np.arange(N) + rng.integers(0, N)) % N for _ in range(R)])
            po = int(rng.integers(0, len(P) - n))
            o = int(rng.integers(0, len(key) - 4 * n))
            kk = key[o:]
            c, used = encrypt_tableau(P[po:po + n], kk, T, rng)
            og = max(o - int(rng.integers(0, SP)), 0)
            s, path = beam_h2(c, key, og, R, ALPHA, 64, LN_SKIP, 8, SP)
            true.append(s / n)
            acc.append(float(np.mean(path == o + used)))
            offs = [int(x) for x in rng.integers(0, len(key) - 4 * n, 40)]
            co = np.array([coincidence(c, key, x) for x in offs])
            old_z.append((coincidence(c, key, o) - co.mean()) / (co.std() + 1e-9))
            oo = int(rng.integers(0, len(key) - 4 * n))
            nulls["offset"].append(beam_h2(c, key, oo, R, ALPHA, 64, LN_SKIP, 8, SP)[0] / n)
            cu = encrypt_tableau(P[po:po + n], rng.integers(0, 29, 4 * n), T, rng)[0]
            nulls["uniform"].append(beam_h2(cu, key, og, R, ALPHA, 64, LN_SKIP, 8, SP)[0] / n)
        cost = (time.perf_counter() - t0) / (reps * 3)
        # tail: uniform-key ciphers against random offsets of this stream (the family a screen faces)
        tail = []
        for t in range(300):
            if t % 30 == 0:
                T = np.array([rng.permutation(N) for _ in range(R)])
                po = int(rng.integers(0, len(P) - n))
                cu = encrypt_tableau(P[po:po + n], rng.integers(0, 29, 4 * n), T, rng)[0]
            tail.append(beam_h2(cu, key, int(rng.integers(0, len(key) - 4 * n)), R, ALPHA, 64, LN_SKIP, 8, SP)[0] / n)
        tail = np.array(tail)
        mu, sd = tail.mean(), tail.std(ddof=1)
        true = np.array(true)
        nulls = {k: np.array(v) for k, v in nulls.items()}
        thr_g = mu + 4.5 * sd
        rows.append(f"  n={n} {'additive' if additive else 'random permutations'} tableau, stream {sname}: {reps} plants, "
                    f"{cost * 1e3:.0f} ms per decode, path accuracy median {np.median(acc):.2f} (>=0.9 in {sum(a >= .9 for a in acc)}/{reps})\n"
                    f"      new beam score: plants median {np.median(true):+.4f} (z {np.median((true - mu) / sd):+.1f}); tail {len(tail)} uniform-key x random offsets "
                    f"{mu:+.4f} +- {sd:.4f}, max {tail.max():+.4f}; POWER at mu+4.5sd {int((true > thr_g).sum())}/{reps}, above tail max {int((true > tail.max()).sum())}/{reps}; "
                    f"nulls above mu+4.5sd: wrong offset {int((nulls['offset'] > thr_g).sum())}/{reps}, uniform key {int((nulls['uniform'] > thr_g).sum())}/{reps}\n"
                    f"      old coincidence z (no drift, true offset vs 40 random offsets): median {np.median(old_z):+.1f}, plants with z > 4.5: {int((np.array(old_z) > 4.5).sum())}/{reps}")
    return "\n".join(rows)


def main():
    rng = np.random.default_rng(1)
    beam_h2(rng.integers(0, 29, 40), rng.integers(0, 29, 400), 0, 29, ALPHA, 8, LN_SKIP, 2, 2)   # compile
    lens = [int(x) for x in sys.argv[sys.argv.index("--n") + 1].split(",")] if "--n" in sys.argv else [300] if "--quick" in sys.argv else [300, 729, 1524]
    print("Phase 32 gate: tableau-invariant drift-tracking statistic for H2 (1 core). Nothing in LP2 is solved; LP2 is NOT touched.\n"
          "Plaintext Emerson (digraph runes); skip rule q = 0.81; beam 64 x 8 histories per pointer, alpha 1.22, free start spread 8.")
    for n in lens:
        for additive in (False, True):
            print(job((n, 3200 + n + additive, additive)), flush=True)


if __name__ == "__main__":
    main()
