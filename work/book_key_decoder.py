"""Phase 23 gate: a table-invariant, drift-tracking decoder for a candidate book as LP2's running key.

Model: c_i = p_i + pi(k_j) (mod 29), k = a book's runes, pi an unknown letter->rune table (any map), j the key pointer,
which advances one per rune plus a skip whenever p_i + pi(k_j) == c_(i-1) (probability q = 0.81 per attempt).

At the right book and offset the ciphertext runes grouped by the key letter under them are each a Caesar shift of the
plaintext, whatever pi is. The decoder is the H5 column beam (work/h5slice, beam_coincidence_nats) with the 29 key letters
as the columns: per group g it keeps G[g, v] = sum log(29 f(c_i - v)) over the group's runes, scores
sum_g logsumexp_v (G[g, v] - log 29) (the shift pi(g) integrated out, uniform prior: table-free) plus ln(0.028) per
skip, branches the pointer +0/+1/+2 per rune, keeps the best state per pointer and the top `beam` pointers.

Score = that log-likelihood ratio against a uniform cipher (nats). Spec, controls and decision rule:
work/log/phase23_book_key_decoder.md. Usage: python work/book_key_decoder.py [--quick]
"""
import os
import sys
import time

import numpy as np
from numba import njit
from scipy.optimize import linear_sum_assignment

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lp  # noqa: E402
from book_key_flatness import (HERE, dist, encrypt_skip, flattest_table, gutenberg_body,  # noqa: E402
                               to_runes)

N = lp.N
LN_SKIP = float(np.log(0.81 / N))     # one skip: ~ (1/29) * q


def log_ratio(P):
    """MT[x, v] = log(29 * f((x - v) mod 29)): plaintext model f against a uniform cipher."""
    f = (np.bincount(P, minlength=N) + 0.5) / (len(P) + 0.5 * N)
    return np.array([[np.log(N * f[(x - v) % N]) for v in range(N)] for x in range(N)])


@njit(cache=True)
def _lse(a):
    m = a.max()
    return m + np.log(np.exp(a - m).sum())


@njit(cache=True)
def beam_decode(c, key, o, MT, beam, ln_skip, per_ptr=8, spread=1):
    """Best-path score (nats) and key pointer per rune for the window c with the key starting at key[o + u],
    u in 0..spread-1 free (so a screen can step offsets by `spread`).

    Keeps up to `per_ptr` histories per pointer: the score is not additive (a group's gain depends on its earlier
    members), so one history per pointer (as h5slice) loses the true path to an early lucky one."""
    n, Q = len(c), 29
    lnQ = np.log(29.0)
    G = np.zeros((beam, Q, Q))
    Lc = np.zeros((beam, Q))
    S = np.zeros(beam)
    J = np.zeros(beam, dtype=np.int64)
    for u in range(spread):
        J[u] = o + u
    W = spread
    nc = 3 * beam
    cs, cj, cw, cg, cl = np.empty(nc), np.empty(nc, np.int64), np.empty(nc, np.int64), np.empty(nc, np.int64), np.empty(nc)
    G2, Lc2, S2, J2 = np.empty_like(G), np.empty_like(Lc), np.empty_like(S), np.empty_like(J)
    par = np.zeros((n, beam), dtype=np.int64)
    ptr = np.zeros((n, beam), dtype=np.int64)
    upd = np.empty(Q)
    for i in range(n):
        x = c[i]
        m = 0
        for w in range(W):
            for dk in range(3):
                k = J[w] + dk
                if k >= len(key):
                    continue
                g = key[k]
                for v in range(Q):
                    upd[v] = G[w, g, v] + MT[x, v]
                new = _lse(upd) - lnQ
                cs[m] = S[w] + new - Lc[w, g] + dk * ln_skip
                cj[m], cw[m], cg[m], cl[m] = k, w, g, new
                m += 1
        order = np.argsort(-cs[:m])
        W2 = 0
        for t in order:                   # best `per_ptr` states per pointer, top `beam` states
            same = 0
            for u in range(W2):
                if J2[u] == cj[t] + 1:
                    same += 1
            if same >= per_ptr:
                continue
            w, g = cw[t], cg[t]
            G2[W2] = G[w]
            for v in range(Q):
                G2[W2, g, v] += MT[x, v]
            Lc2[W2] = Lc[w]
            Lc2[W2, g] = cl[t]
            S2[W2] = cs[t]
            J2[W2] = cj[t] + 1
            par[i, W2] = w
            ptr[i, W2] = cj[t]
            W2 += 1
            if W2 == beam:
                break
        if W2 == 0:
            return -1e18, np.zeros(n, np.int64)
        G[:W2], Lc[:W2], S[:W2], J[:W2] = G2[:W2], Lc2[:W2], S2[:W2], J2[:W2]
        W = W2
    path = np.zeros(n, dtype=np.int64)
    w = 0                                 # states are sorted, 0 is the best
    for i in range(n - 1, -1, -1):
        path[i] = ptr[i, w]
        w = par[i, w]
    return S[0], path


def shifts_of(c, key, path, MT, perm=True):
    """The table s (s[g] = pi(g)) maximising sum log f(c_i - s[k_j]) over the path: a permutation by assignment
    (perm=True, the task's model), else each group's own argmax (any map: also covers a non-injective table)."""
    G = np.zeros((N, N))
    np.add.at(G, key[path], MT[c])
    return linear_sum_assignment(-G)[1] if perm else G.argmax(axis=1)


@njit(cache=True)
def viterbi_fixed(c, prev0, key, o, s, MT, D, lnq, ln_keep, spread=1):
    """Exact DP over the drift d in 0..D for a FIXED table s, with the anti-repeat rule's exact likelihood (ratio to a
    uniform cipher): no skip at i: 29 f(c_i - s[k_j]) (times 0.19 if c_i == c_(i-1)); one skip: the rejected value must
    have collided, i.e. p = c_(i-1) - s[k_j] = c_i - s[k_(j+1)], ratio 29 f(p) q; two skips need s[k_j] == s[k_(j+1)]."""
    n, Q = len(c), 29
    NEG = -1e18
    V = np.full(D + 1, NEG)
    V[:spread] = 0.0                       # free start drift 0..spread-1
    back = np.zeros((n, D + 1), dtype=np.int64)
    for i in range(n):
        x = c[i]
        prev = prev0 if i == 0 else c[i - 1]
        keep = ln_keep if x == prev else 0.0
        V2 = np.full(D + 1, NEG)
        for d in range(D + 1):
            j = o + i + d                       # pointer of the key value used at i
            if j >= len(key):
                continue
            best, arg = NEG, 0
            for m in range(3):                  # m skips at i: came from drift d - m
                dp = d - m
                if dp < 0 or V[dp] <= NEG:
                    continue
                if m == 0:
                    e = MT[x, s[key[j]]] + keep
                else:
                    if prev < 0:
                        continue
                    p = (prev - s[key[j - m]]) % Q
                    if (x - s[key[j]]) % Q != p or (m == 2 and s[key[j - 2]] != s[key[j - 1]]):
                        continue
                    e = MT[p, 0] + m * lnq + keep
                v = V[dp] + e
                if v > best:
                    best, arg = v, dp
            V2[d], back[i, d] = best, arg
        V = V2
    d = int(np.argmax(V))
    score = V[d]
    path = np.zeros(n, dtype=np.int64)
    for i in range(n - 1, -1, -1):
        path[i] = o + i + d
        d = back[i, d]
    return score, path


def decode(c, key, o, MT, beam=64, per_ptr=8, iters=4, prev0=-1, spread=8):
    """Beam init (table-free), then hard EM: shifts from the path, exact Viterbi with those shifts, repeat.

    Returns (beam score, EM score, path, shifts); both scores in nats against a uniform cipher, per window."""
    sb, path = beam_decode(c, key, o, MT, beam, LN_SKIP, per_ptr, spread)
    D = spread + max(8, int(3 * len(c) / 29))   # shortcut: drift cap 3x the expected skips, raise if plants hit it
    se, s = -1e18, None
    for _ in range(iters):
        s2 = shifts_of(c, key, path, MT)
        sc, p2 = viterbi_fixed(c, prev0, key, o, s2, MT, D, np.log(0.81), np.log(0.19), spread)
        if sc <= se + 1e-9:
            break
        se, s, path = sc, s2, p2
    return sb, se, path, s


def decrypt(c, key, path, s):
    return (c - s[key[path]]) % N


def corpus():
    K = {}
    for name, f in (("KJV", "pg10.txt"), ("Paradise Lost", "pg26.txt"), ("Meditations", "pg2680.txt"),
                    ("Zarathustra", "pg1998.txt"), ("Republic", "pg1497.txt")):
        raw = gutenberg_body(os.path.join(HERE, "ref", "corpora", f))
        K[name] = (to_runes(raw), to_runes(raw, letters=True))
    return K


def plant(P, Kb, n, rng, table, uniform=False):
    """A window of n runes: plaintext from P, key from book Kb at a random offset, through `table`, skip rule."""
    po = rng.integers(0, len(P) - n - 1)
    o = int(rng.integers(0, len(Kb) - 3 * n))
    k = rng.integers(0, N, 3 * n) if uniform else table[Kb[o:o + 3 * n]]
    c, used = encrypt_skip_ptr(P[po:po + n], k, rng)
    return c, o, used, P[po:po + n]


def encrypt_skip_ptr(p, k, rng, q=0.81):
    """encrypt_skip (book_key_flatness.py) that also returns the key pointer used per rune (for path accuracy)."""
    c = np.empty(len(p), dtype=np.int64)
    used = np.empty(len(p), dtype=np.int64)
    j, prev = 0, -1
    for i, pi in enumerate(p):
        ci = (pi + k[j]) % N
        while ci == prev and rng.random() < q:
            j += 1
            ci = (pi + k[j]) % N
        c[i], used[i], prev, j = ci, j, ci, j + 1
    return c, used




# ---------------------------------------------------------------- gate (controls only; no LP2 run here)
SPREAD = 8
Z_FAMILY = 6.1     # one-sided p = 5e-10 = 0.05 / 1e8 (8 windows x 2 spellings x ~6e6 book offsets), see the spec
REPS = {300: 40, 729: 30, 1524: 20, 3316: 12}
TAIL = {300: 3000, 729: 2000, 1524: 1000, 3316: 400}


def job(args):
    letters, n, seed = args
    rng = np.random.default_rng(seed)
    em = open(os.path.join(HERE, "ref", "emerson_essays1.txt"), encoding="utf-8", errors="ignore").read()
    P = to_runes(em)                                                       # plaintext: digraph spelling (solved pages)
    MT = log_ratio(to_runes(gutenberg_body(os.path.join(HERE, "ref", "corpora", "pg205.txt"))))  # model: Walden
    books = {k: v[letters] for k, v in corpus().items()}
    names = list(books)
    t_true, acc, ioc_p, agree, nulls, cost = [], [], [], [], {"offset": [], "book": [], "uniform": []}, []
    for r in range(REPS[n]):
        Kb = books[names[r % len(names)]]
        _, pi = flattest_table(dist(P), dist(Kb), rng, restarts=3)
        table = np.argsort(pi)                                             # key symbol -> rune, as book_key_flatness
        c, o, used, ptxt = plant(P, Kb, n, rng, table)
        og = o - int(rng.integers(0, SPREAD))                              # the screen's grid offset below the truth
        t0 = time.perf_counter()
        sb, se, path, s = decode(c, Kb, og, MT)
        cost.append(time.perf_counter() - t0)
        t_true.append((sb / n, se / n))
        acc.append(float(np.mean(path == o + used)))
        ioc_p.append(lp.ioc(list(decrypt(c, Kb, path, s))))
        present = np.unique(Kb[o + used])
        agree.append(float(np.mean(s[present] == table[present])))
        oo = int(rng.integers(0, len(Kb) - 3 * n))
        nulls["offset"].append([v / n for v in decode(c, Kb, oo, MT)[:2]])
        other = books[names[(r + 1) % len(names)]]
        nulls["book"].append([v / n for v in decode(c, other, int(rng.integers(0, len(other) - 3 * n)), MT)[:2]])
        cu = plant(P, Kb, n, rng, table, uniform=True)[0]
        nulls["uniform"].append([v / n for v in decode(cu, Kb, og, MT)[:2]])
    # tail: flat (uniform-key) ciphers against random offsets of the KJV, the family a screen of one book faces
    K = books["KJV"]
    tail = []
    for t in range(TAIL[n]):
        if t % 50 == 0:
            cu = plant(P, K, n, rng, np.arange(N), uniform=True)[0]
        tail.append([v / n for v in decode(cu, K, int(rng.integers(0, len(K) - 3 * n)), MT)[:2]])
    tail, t_true = np.array(tail), np.array(t_true)
    out = [f"\n--- key spelling {'letters' if letters else 'digraph'}, window {n} runes: {REPS[n]} plants (flattened "
           f"table, skip q=0.81, grid offset 0-7 below the truth), decode {np.mean(cost) * 1e3:.0f} ms = "
           f"{np.mean(cost) / SPREAD * 1e3:.1f} ms per book-offset (stride {SPREAD})"]
    out.append(f"    plants: path accuracy mean {np.mean(acc):.3f}, median {np.median(acc):.3f}, >=0.9 in "
               f"{sum(a >= 0.9 for a in acc)}/{REPS[n]}, <0.5 in {sum(a < 0.5 for a in acc)}; table agreement "
               f"{np.mean(agree):.2f}; decrypted IoC mean {np.mean(ioc_p):.3f} (plaintext ~1.77)")
    for k, name in ((0, "beam (table-free)"), (1, "EM (best table)")):
        mu, sd = tail[:, k].mean(), tail[:, k].std(ddof=1)
        # exponential tail fitted to the top 5% (heavier than Gaussian at n = 300), extrapolated to p = 5e-10
        u = np.quantile(tail[:, k], 0.95)
        thr_exp = u + (tail[tail[:, k] > u, k] - u).mean() * np.log(0.05 / 5e-10)
        thr = max(mu + Z_FAMILY * sd, thr_exp, tail[:, k].max())
        g3 = float(np.mean(tail[:, k] > mu + 3 * sd))
        out.append(f"    {name:18s} plants {t_true[:, k].mean():+.4f} (min {t_true[:, k].min():+.4f}); tail {len(tail)}: "
                   f"{mu:+.4f} +- {sd:.4f}, max {tail[:, k].max():+.4f} (> mu+3sd: {g3:.4f}, Gaussian 0.0013); "
                   f"threshold {thr:+.4f} (Gauss {mu + Z_FAMILY * sd:+.4f}, exp tail {thr_exp:+.4f}): POWER {int((t_true[:, k] > thr).sum())}/{REPS[n]}; plant z median "
                   f"{np.median((t_true[:, k] - mu) / sd):+.1f}")
        for kind, v in nulls.items():
            v = np.array(v)[:, k]
            out.append(f"        null {kind:8s} {v.mean():+.4f} +- {v.std(ddof=1):.4f}, max {v.max():+.4f}, "
                       f"above threshold {int((v > thr).sum())}/{len(v)}")
    return "\n".join(out)


def main():
    from multiprocessing import Pool
    # self-check: encrypt_skip_ptr reproduces encrypt_skip exactly (same rng stream)
    rng = np.random.default_rng(1)
    pp, kk = rng.integers(0, N, 500), rng.integers(0, N, 1500)
    s0 = rng.bit_generator.state
    a = encrypt_skip(pp, kk, rng)
    rng.bit_generator.state = s0
    assert (a == encrypt_skip_ptr(pp, kk, rng)[0]).all()
    MT = log_ratio(to_runes(gutenberg_body(os.path.join(HERE, "ref", "corpora", "pg205.txt"))))
    decode(np.zeros(40, np.int64), np.zeros(400, np.int64), 0, MT)        # compile once before forking
    lens = [300, 729] if "--quick" in sys.argv else list(REPS)
    tasks = [(lt, n, 2300 + 10 * n + lt) for n in lens for lt in (False, True)]
    print("Phase 23 gate: table-invariant drift-tracking book-key decoder. Nothing in LP2 is solved; LP2 is NOT decoded "
          "here.\nPlaintext Emerson (digraph runes), plaintext model Walden; key books KJV, Paradise Lost, Meditations, "
          f"Zarathustra, Republic; beam 64 x 8 per pointer, hard EM <= 4 rounds; family threshold max(mu + "
          f"{Z_FAMILY} sd, exponential-tail extrapolation to p = 5e-10, tail max)", flush=True)
    with Pool(min(len(tasks), 8)) as pool:
        for block in pool.imap(job, tasks):
            print(block, flush=True)


if __name__ == "__main__":
    main()
