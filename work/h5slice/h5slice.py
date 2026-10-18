"""H5 first slice: drift-tracking decoder for the two-stack model of docs/HYPOTHESES.md (H1).

    c_i = D(p_i) + t_j + w_(j mod L) + b   (mod 29)

with the anti-repeat rule on the COMBINED key k_j = t_j + w_(j mod L) + b:
  * model 0 ("skip"): on a collision the encryptor re-draws with the next key value,
    probability q = 1 - keep = 0.81 per attempt, up to 5 attempts (as work/layer2's plant);
  * model 1 ("coin"): on a collision one key value is always spent, then with probability
    1 - keep the value is re-drawn from the next key value.
and the optional literal-F rule of the solved pages (lp.py: a ciphertext F passes through
unencrypted and consumes no key position).

Decoder (per offset, L):
  outer loop over (offset, L); inner EM over the keyword columns:
   * init: a w-free nats-scored beam over FREE pointer branches (+1/+2/+3 and the
     literal-F branch), scored by the per-column SHIFT-MARGINALIZED English log-likelihood
     (the keyword shift of each column is integrated out over the 29 shifts, so no keyword
     knowledge is used) minus ln(1/0.028) = 3.58 nats per skip (HYPOTHESES.md:18-20).
     Each letter placed in a column adds at most ln(29 f_max) ~ 1.3 nats of evidence above
     the uniform-null level, so a fabricated skip can never pay for itself; the beam buys
     the real skips on truth because they re-align every later rune (about 1.2 nats per
     rune of drift, HYPOTHESES.md:22). An early abort kills cells whose best mean score at
     abort_at runes stays below the unigram-null level + margin (dead nulls, cheaply);
   * estimate the L column shifts w by the maximum-likelihood shift under the English rune
     distribution (the distribution-aware modal class) from p_i = c_i - t_{j(i)};
   * EM over w: a beam over the collision-consistent skip branches only (drift tracking;
     a skip branch exists only where the collision is consistent with the combined key,
     as in work/kscreen), pruning the beam by the plaintext log-likelihood; re-estimate w
     from the best path; repeat until w is stable.
  score = periodic IoC of the decoded columns (mean over columns of 29*sum n(n-1)/(n_c(n_c-1)),
  HYPOTHESES.md:70-78: about 1.8 on truth vs 1.0 +- 0.07 for L = 8, n = 300).

L = 0 decodes with t alone (the blind old screen's view) and scores the plain IoC.

The totient stream is regenerated here: t_n = p_n - 1 mod 29 (p_n the n-th prime), the
library's "primes-1 (totient)" (work/keystreams.py:44).
"""
from __future__ import annotations

import math
import os
import random
import sys
import time

import numpy as np

Q = 29
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
if WORK not in sys.path:
    sys.path.insert(0, WORK)

LATIN = ["F", "U", "TH", "O", "R", "C", "G", "W", "H", "N", "I", "J", "EO", "P", "X", "S", "T", "B", "E", "M",
         "L", "NG", "OE", "D", "A", "AE", "Y", "IA", "EA"]

# subtraction / addition tables over Z_29
SUB = tuple(tuple((a - b) % Q for b in range(Q)) for a in range(Q))
ADD = tuple(tuple((a + b) % Q for b in range(Q)) for a in range(Q))

# DIVINITY as GP indices (work/layer2/data/keywords.txt)
DIVINITY = [23, 10, 1, 10, 9, 10, 16, 26]


# ------------------------------------------------------------------ streams

def sieve_primes(n):
    """First n primes (self-contained sieve)."""
    if n < 1:
        return []
    if n < 8:
        return [2, 3, 5, 7, 11, 13, 17][:n]
    bound = int(n * (math.log(n) + math.log(math.log(n)))) + 16
    while True:
        m = np.ones(bound + 1, dtype=bool)
        m[:2] = False
        m[4::2] = False
        for i in range(3, int(bound ** 0.5) + 1, 2):
            if m[i]:
                m[i * i::i] = False
        ps = np.nonzero(m)[0]
        if len(ps) >= n:
            return [int(x) for x in ps[:n]]
        bound *= 2


def totient(n):
    """The library's 'primes-1 (totient)': t_n = p_n - 1 mod 29, p_n the n-th prime."""
    return [(p - 1) % Q for p in sieve_primes(n)]


def random_stream(n, seed):
    r = random.Random(seed)
    return [r.randrange(Q) for _ in range(n)]


# ------------------------------------------------------------------ English prior

_LOG_F = None


def english_logf():
    """log of the English rune distribution (Self-Reliance via work/sim.py), add-0.5 smoothed."""
    global _LOG_F
    if _LOG_F is None:
        import sim  # repo data: English -> GP runes of the Self-Reliance essay
        cnt = np.bincount(sim.english_runes(), minlength=Q).astype(np.float64) + 0.5
        _LOG_F = np.log(cnt / cnt.sum())
    return _LOG_F


_LS = None


def _ls_matrix(logf):
    """M[v][x] = logf[(x - v) mod 29]: shift scores for the ML column estimate."""
    global _LS
    if _LS is None:
        _LS = np.array([[logf[(x - v) % Q] for x in range(Q)] for v in range(Q)])
    return _LS


_UM = None


def uni_mean_logf():
    """Mean of logf over the UNIFORM letter distribution, (1/29) sum logf: the expected
    per-letter score of a null column under the unigram model (ln of the geometric mean
    of the Emerson frequencies). The truth level is mean(logf) = -H(f) nats per letter;
    the gap (~1.2 nats) is the drift evidence of HYPOTHESES.md:22."""
    global _UM
    if _UM is None:
        _UM = float(np.sum(english_logf())) / Q
    return _UM


# ------------------------------------------------------------------ statistics

def overall_ioc(syms):
    n = len(syms)
    if n < 2:
        return 0.0
    cnt = np.bincount(syms, minlength=Q)
    return float((cnt * (cnt - 1)).sum()) * Q / (n * (n - 1))


def periodic_ioc(plain, ptrs, L):
    """Mean column IoC of the decoded text: columns are the key-pointer phases j(i) mod L
    (HYPOTHESES.md:70-78)."""
    cols = [[] for _ in range(L)]
    for p, j in zip(plain, ptrs):
        cols[j % L].append(p)
    vals = []
    for col in cols:
        if len(col) >= 2:
            cnt = np.bincount(col, minlength=Q)
            vals.append(Q * float((cnt * (cnt - 1)).sum()) / (len(col) * (len(col) - 1)))
    return float(np.mean(vals)) if vals else 0.0


# ------------------------------------------------------------------ EM core

def est_cols(c, ts, ptr, L, logf):
    """ML column shifts: w[col] = argmax_v sum_i logf[(x_i - v) mod 29] over x_i = c_i - t_{j(i)}
    (the distribution-aware modal class of each column)."""
    n = len(c)
    cols = [[] for _ in range(L)]
    for i in range(n):
        cols[ptr[i] % L].append(SUB[c[i]][ts[ptr[i]]])
    M = _ls_matrix(logf)
    wcol = [0] * L
    for col in range(L):
        if cols[col]:
            cnt = np.bincount(cols[col], minlength=Q)
            wcol[col] = int(np.argmax(M @ cnt))
    return wcol


def beam_pass(c, prev, comb, model, litf, beam, logf, abort_at=0, abort_ll=0.0):
    """One beam pass with the fixed combined key comb over the skip branches
    (drift tracking; a skip branch exists only where the collision is consistent,
    exactly work/layer2's outer_cands applied to the combined key).
    States: (pointer j, cumulative plaintext log-likelihood, arena node).
    Returns (best state, plains, parents, js) or None when the abort fires."""
    n = len(c)
    clen = len(comb)
    plains, parents, js = [], [], []
    cur = [(0, 0.0, -1)]
    lf0 = logf[0]
    for i in range(n):
        ci = c[i]
        pv = prev if i == 0 else c[i - 1]
        cand = []
        for j, s, node in cur:
            k0 = comb[j]
            q0 = SUB[ci][k0]
            nj0 = j + 2 if (model == 1 and pv == ci) else j + 1
            plains.append(q0)
            parents.append(node)
            js.append(j)
            cand.append((nj0, s + logf[q0], len(plains) - 1))
            if litf and ci == 0:                       # literal F: no key consumed
                plains.append(0)
                parents.append(node)
                js.append(j)
                cand.append((j, s + lf0, len(plains) - 1))
            if pv >= 0:
                if model == 0:
                    if j + 1 < clen:
                        k1 = comb[j + 1]
                        t1 = SUB[ci][k1]
                        if ADD[t1][k0] == pv:          # one skip is consistent
                            plains.append(t1)
                            parents.append(node)
                            js.append(j + 1)
                            cand.append((j + 2, s + logf[t1], len(plains) - 1))
                        if j + 2 < clen:
                            k2 = comb[j + 2]
                            t2 = SUB[ci][k2]
                            if ADD[t2][k0] == pv and ADD[t2][k1] == pv:   # two skips are consistent
                                plains.append(t2)
                                parents.append(node)
                                js.append(j + 2)
                                cand.append((j + 3, s + logf[t2], len(plains) - 1))
                else:
                    if j + 2 < clen:
                        k2 = comb[j + 2]
                        t2 = SUB[ci][k2]
                        if ADD[t2][k0] == pv:          # the re-draw is consistent
                            plains.append(t2)
                            parents.append(node)
                            js.append(j + 2)
                            cand.append((j + 3, s + logf[t2], len(plains) - 1))
        best = {}
        for nj, s, node in cand:
            b = best.get(nj)
            if b is None or s > b[1]:
                best[nj] = (nj, s, node)
        items = list(best.values())
        if len(items) > beam:
            items.sort(key=lambda t: t[1], reverse=True)
            items = items[:beam]
        if abort_at and i + 1 >= abort_at:
            if not items or max(items, key=lambda t: t[1])[1] < abort_ll:
                return None
        cur = items
    if not cur:
        return None
    best_state = max(cur, key=lambda t: t[1])
    return best_state, plains, parents, js


def traceback(node, plains, parents, js):
    plain, ptrs = [], []
    while node >= 0:
        plain.append(plains[node])
        ptrs.append(js[node])
        node = parents[node]
    plain.reverse()
    ptrs.reverse()
    return plain, ptrs


def path_back(node, ks, parents):
    out = []
    while node >= 0:
        out.append(ks[node])
        node = parents[node]
    out.reverse()
    return out


def beam_coincidence_z(c, prev, ts, L, litf, beam, abort_at=0, abort_z=0.0):
    """DEPRECATED (blocker B, kept for reference/regression comparisons): init pass beam
    over FREE pointer branches (+1/+2/+3 and the literal-F branch), scored by the running
    column-coincidence z = (Q s - d)/sqrt(56 d) (layer2's periodic z). The z is w-free but
    the pass overfits: with free branches the beam routes nearly every rune to a column
    where it matches (z ~ 41 sigma on BOTH the truth plant and random nulls). Do not use.
    decode() uses beam_coincidence_nats instead. Returns (ptrs, z) or None on abort."""
    n = len(c)
    tlen = len(ts)
    cell = L * Q
    ks, parents = [], []
    states = [(0, bytearray(cell), [0] * L, 0, 0, -1)]   # (j, cnt, ncol, s, d, node)
    for i in range(n):
        ci = c[i]
        cand = []
        for j, cnt, ncol, s, d, node in states:
            for kidx in (j, j + 1, j + 2):
                if kidx >= tlen:
                    continue
                q = SUB[ci][ts[kidx]]
                col = kidx % L
                idx = col * Q + q
                cnt2 = bytearray(cnt)
                ncol2 = ncol[:]
                v = cnt2[idx]
                cnt2[idx] = v + 1
                s2 = s + 2 * v
                d2 = d + 2 * ncol2[col]
                ncol2[col] += 1
                ks.append(kidx)
                parents.append(node)
                cand.append((kidx + 1, cnt2, ncol2, s2, d2, len(ks) - 1))
            if litf and ci == 0:
                col = j % L
                idx = col * Q
                cnt2 = bytearray(cnt)
                ncol2 = ncol[:]
                v = cnt2[idx]
                cnt2[idx] = v + 1
                s2 = s + 2 * v
                d2 = d + 2 * ncol2[col]
                ncol2[col] += 1
                ks.append(j)
                parents.append(node)
                cand.append((j, cnt2, ncol2, s2, d2, len(ks) - 1))
        best = {}
        for j, cnt2, ncol2, s2, d2, node in cand:
            z = (Q * s2 - d2) / math.sqrt(56.0 * d2) if d2 else 0.0
            b = best.get(j)
            if b is None or z > b[0]:
                best[j] = (z, cnt2, ncol2, s2, d2, node)
        items = list(best.items())
        if len(items) > beam:
            items.sort(key=lambda t: t[1][0], reverse=True)
            items = items[:beam]
        if abort_at and i + 1 >= abort_at:
            if not items or items[0][1][0] < abort_z:
                return None
        states = [(j, cnt2, ncol2, s2, d2, node) for j, (z, cnt2, ncol2, s2, d2, node) in items]
    if not states:
        return None
    best_state = max(states, key=lambda t: (Q * t[3] - t[4]) / math.sqrt(56.0 * t[4]) if t[4] else 0.0)
    z = (Q * best_state[3] - best_state[4]) / math.sqrt(56.0 * best_state[4]) if best_state[4] else 0.0
    return path_back(best_state[5], ks, parents), z


LN_028 = math.log(0.028)


def beam_coincidence_nats(c, prev, ts, L, litf, beam, logf, abort_at=0, abort_ll=0.0):
    """Init pass (the fixed nats-scored version): a beam over FREE pointer branches
    (+1/+2/+3 per rune, plus the literal-F branch), scored by the per-column
    SHIFT-MARGINALIZED English log-likelihood: each state carries the log-domain column
    products G[col*Q + v] = sum_i logf[(x_i - v) mod 29] over the column's letters, and
    scores sum_col logsumexp_v G[col, v] + skips * ln(0.028). The keyword shift of each
    column is integrated out over the 29 shifts (uniform prior), so the pass is w-free
    (no keyword knowledge); the per-letter gain is bounded by ln(29 f_max) ~ 1.3 nats
    above the uniform-null level while one skip costs ln(1/0.028) = 3.58 nats
    (HYPOTHESES.md:18-20) - the free branches can no longer buy coincidence.
    The beam buys the real skips on truth because they re-align every later rune
    (about 1.2 nats/rune of drift evidence). States: (j, G, Lc, s, node) with
    Lc[col] = logsumexp(G[col]) and s = sum(Lc) + skips*ln(0.028); states are merged per
    pointer j and pruned to `beam` by score. The abort fires ONLY at the abort_at
    checkpoint (the score drops ~3 nats/rune, so a running >= check would abort every
    surviving cell on the next rune). Returns (ptrs, score) or None on abort."""
    n = len(c)
    tlen = len(ts)
    M = _ls_matrix(logf)      # M[v][x] = logf[(x - v) % Q]
    MT = M.T                  # MT[x][v]
    js = [0]
    G = [np.zeros(L * Q)]
    Lc = [np.full(L, math.log(Q))]
    S = [L * math.log(Q)]
    nds = [-1]
    ks_all = []
    parents = []
    for i in range(n):
        ci = c[i]
        W = len(js)
        nb = 3 + (1 if (litf and ci == 0) else 0)
        par = np.repeat(np.arange(W), nb)
        kidx = []
        cost = []
        ql = []
        for w in range(W):
            j = js[w]
            for dk in (0, 1, 2):
                k = j + dk
                if k < tlen:
                    kidx.append(k)
                    cost.append(dk * LN_028)
                    ql.append(SUB[ci][ts[k]])
                else:
                    kidx.append(0)              # pad; killed by the -inf cost below
                    cost.append(float("-inf"))
                    ql.append(0)
            if nb == 4:
                kidx.append(j)
                cost.append(0.0)
                ql.append(0)
        N = len(par)
        kidx = np.array(kidx, dtype=np.int64)
        cost = np.array(cost)
        col = np.array(kidx) % L
        Gmat = np.stack(G)
        Lcm = np.stack(Lc)
        Sm = np.array(S)
        ndm = np.array(nds)
        G2 = Gmat[par]                          # (N, LQ) fresh copies
        rows = np.arange(N)
        idx = col[:, None] * Q + np.arange(Q)[None, :]
        G2[rows[:, None], idx] += MT[np.array(ql)]
        upd = G2[rows[:, None], idx]
        m = upd.max(axis=1)
        lse2 = m + np.log(np.exp(upd - m[:, None]).sum(axis=1))
        lse1 = Lcm[par, col]
        s2 = Sm[par] + (lse2 - lse1) + cost
        nj = kidx + 1
        best = {}
        for t in range(N):
            njv = nj[t]
            b = best.get(njv)
            if b is None or s2[t] > b[0]:
                best[njv] = (s2[t], t)
        items = list(best.items())
        items.sort(key=lambda kv: -kv[1][0])
        if len(items) > beam:
            items = items[:beam]
        if abort_at and i + 1 == abort_at:
            if not items or items[0][1][0] < abort_ll:
                return None
        js2, Gs2, Lc2, S2, nd2 = [], [], [], [], []
        for njv, (s, t) in items:
            lcs = Lcm[par[t]]
            lcs = lcs.copy()
            lcs[col[t]] = lse2[t]
            ks_all.append(int(kidx[t]))
            parents.append(int(ndm[par[t]]))
            js2.append(int(njv))
            Gs2.append(G2[t])
            Lc2.append(lcs)
            S2.append(s)
            nd2.append(len(ks_all) - 1)
        js, G, Lc, S, nds = js2, Gs2, Lc2, S2, nd2
    if not js:
        return None
    best_i = max(range(len(S)), key=lambda k: S[k])
    return path_back(nds[best_i], ks_all, parents), float(S[best_i])


def beam_coincidence_nats_fast(c, prev, ts, L, litf, beam, logf, abort_at=0, abort_ll=0.0):
    """Vectorized twin of beam_coincidence_nats (verified 2026-10-18: same top pointers,
    skips, score within 1e-6 nats, same aborts). Identical scoring and per-pointer merging;
    the inner loop uses preallocated buffers and the log-domain cyclic-correlation identity

        logsumexp_v (g_v + MT[q][v]) = log( sum_v exp(g_v - m) * f[(q - v) mod 29] ) + m

    (m = max_v g_v, f = exp(logf)), so per rune there is one (N,29) gather, one exp, one
    29x29 matmul and one log instead of the slow version's scatter-add + gather +
    logsumexp and Python candidate loop. The per-pointer merge keeps the first maximum
    (dict, strict >) and the truncation sorts stably by score with the candidate-index
    tie-break - exactly the slow version's semantics, so the top path is identical."""
    n = len(c)
    tlen = len(ts)
    MT = _ls_matrix(logf).T              # MT[x][v] = logf[(x - v) mod 29]
    SUBM = np.array(SUB)
    ts_arr = np.asarray(ts, dtype=np.int64)
    B = beam
    Q = 29
    Gmat = np.zeros((B, L, Q))
    Lcm = np.full((B, L), math.log(Q))
    Mmax = np.zeros((B, L))              # per-column max (initial column = zeros -> 0)
    Sm = np.zeros(B)
    ndm = np.full(B, -1, dtype=np.int64)
    Sm[0] = L * math.log(Q)
    js = np.zeros(B, dtype=np.int64)     # js[0] = 0
    W = 1
    NMAX = B * 4
    rows = np.arange(NMAX)
    kidx = np.zeros(NMAX, dtype=np.int64)
    cost = np.zeros(NMAX)
    ql = np.zeros(NMAX, dtype=np.int64)
    s2 = np.zeros(NMAX)
    nj = np.zeros(NMAX, dtype=np.int64)
    CORR = np.zeros((NMAX, Q))
    offs = np.array([0, 1, 2, 0], dtype=np.int64)
    costs = np.array([0.0, LN_028, 2.0 * LN_028, 0.0])
    fvec = np.exp(MT[0])
    C = np.stack([np.roll(fvec, q) for q in range(Q)], axis=1)   # C[v, q] = f[(q-v) mod 29]
    _toff, _costt, _part = {}, {}, {}
    ks_all = []
    parents = []
    for i in range(n):
        ci = c[i]
        nb = 4 if (litf and ci == 0) else 3
        N = W * nb
        kidx[:N] = np.repeat(js[:W], nb)
        kidx[:N] += _toff.setdefault((nb, W), np.tile(offs[:nb], W))
        kk = np.minimum(kidx[:N], tlen - 1)
        col = kk % L
        ql[:N] = SUBM[ci][ts_arr[kk]]
        if nb == 4:
            ql[3::4] = 0                    # the literal-F branch letter (column = j % L)
        cost[:N] = np.where(kidx[:N] < tlen, _costt.setdefault((nb, W), np.tile(costs[:nb], W)),
                            -1e18)
        par = _part.setdefault((nb, W), np.repeat(np.arange(W), nb))
        Gcols = Gmat[par, col]              # (N, Q) parent column vectors (fancy copy)
        mm = Mmax[par, col]
        Gcols -= mm[:, None]
        np.exp(Gcols, out=Gcols)
        np.matmul(Gcols, C, out=CORR[:N])
        np.log(CORR[:N], out=CORR[:N])
        lse2 = CORR[rows[:N], ql[:N]] + mm
        s2v = s2[:N]
        s2v[:] = lse2
        s2v -= Lcm[par, col]
        s2v += Sm[par]
        s2v += cost[:N]
        njv = nj[:N]
        njv[:] = kidx[:N] + 1
        best = {}
        for t in range(N):
            njvv = njv[t]
            b = best.get(njvv)
            if b is None or s2v[t] > b[0]:
                best[njvv] = (s2v[t], t)
        items = list(best.items())
        if len(items) > B:
            items.sort(key=lambda kv: -kv[1][0])
            items = items[:B]
        if abort_at and i + 1 == abort_at:
            if not items or items[0][1][0] < abort_ll:
                return None
        m2 = len(items)
        surv = np.array([it[1][1] for it in items], dtype=np.int64)
        s2s = np.array([it[1][0] for it in items], dtype=np.float64)
        pnodes = ndm[par[surv]]             # parent node ids: read BEFORE ndm is overwritten
        base = len(ks_all)
        ks_all.extend(kidx[surv].tolist())
        parents.extend(pnodes.tolist())
        ndm[:m2] = np.arange(base, base + m2, dtype=np.int64)   # own node ids (slow: len(ks_all)-1)
        js[:m2] = njv[surv]
        Gmat[:m2] = Gmat[par[surv]]         # row copies of the surviving parents
        Lcm[:m2] = Lcm[par[surv]]           # FULL row copies: every column, not just the one
        Mmax[:m2] = Mmax[par[surv]]         # just updated - otherwise lse1/mm at the next rune
        Gmat[rows[:m2], col[surv]] += MT[ql[surv]]
        Lcm[rows[:m2], col[surv]] = lse2[surv]
        Mmax[rows[:m2], col[surv]] = Gmat[rows[:m2], col[surv]].max(axis=1)
        Sm[:m2] = s2s
        W = m2
    if W == 0:
        return None
    best_i = int(np.argmax(Sm[:W]))
    return path_back(int(ndm[best_i]), ks_all, parents), float(Sm[best_i])


def decode(c, prev, tvals, offset, L, model, litf=False, beam=24, max_em=6, logf=None,
           abort_at=0, abort_margin=0.25, out_path=False, beam_a=12, fast_init=False):
    """Decode one window at one (offset, L). Two stages:
      1. nats-scored coincidence init (beam_coincidence_nats by default; fast_init=True
         selects beam_coincidence_nats_fast, whose v3 rewrite is NOT yet verified -
         see FAST_REPORT.md): free pointer branches
         scored by the shift-marginalized unigram log-likelihood minus ln(1/0.028) per
         skip (w-free); early abort when the best mean score at abort_at runes is below
         the unigram-null level (uni_mean_logf) + abort_margin - dead null cells die
         cheaply, the true path passes with a wide margin;
      2. per-column ML shift w, then EM over w: beam over the collision-consistent skip
         branches pruned by the plaintext log-likelihood, re-estimating w until stable
         (the EM's own LL abort is NOT used: on the true path the LL equals mean(logf)
         per rune exactly, so any margin-above-mean threshold would kill the truth plant).
      score = periodic IoC of the final columns.
    Returns (periodic_ioc, info); info is wcol, or a dict with the full path when out_path.
    On abort or short stream: (0.0, None)."""
    n = len(c)
    margin = n // 4 + 32
    if offset < 0 or offset + n + margin > len(tvals):
        return 0.0, None
    ts = tvals[offset:offset + n + margin]
    if logf is None:
        logf = english_logf()
    if L == 0:
        return decode_t_only(c, prev, ts, model, beam)
    abort_ll_init = (abort_at * (uni_mean_logf() + abort_margin) + L * math.log(Q)
                     if abort_at else 0.0)
    init_fn = beam_coincidence_nats_fast if fast_init else beam_coincidence_nats
    a = init_fn(c, prev, ts, L, litf, beam_a, logf, abort_at, abort_ll_init)
    if a is None:
        return 0.0, None
    ptrsA, _llA = a
    wcol = est_cols(c, ts, ptrsA, L, logf)
    last_out = None
    for _ in range(max_em):
        comb = [(ts[j] + wcol[j % L]) % Q for j in range(n + margin)]
        out = beam_pass(c, prev, comb, model, litf, beam, logf, 0, 0.0)
        if out is None:
            break
        last_out = out
        best_state, plains, parents, js = out
        plain, ptrs = traceback(best_state[2], plains, parents, js)
        new_wcol = est_cols(c, ts, ptrs, L, logf)
        changed = new_wcol != wcol
        wcol = new_wcol
        if not changed:
            break
    if last_out is None:
        # the init found no LL-EM path: score the coincidence-init path as-is
        plain = [SUB[c[i]][ts[ptrsA[i]]] for i in range(n)]
        ioc = periodic_ioc(plain, ptrsA, L)
        if out_path:
            return ioc, dict(ioc=ioc, wcol=wcol, plain=plain, ptrs=ptrsA, ll=0.0, overall=overall_ioc(plain))
        return ioc, wcol
    comb = [(ts[j] + wcol[j % L]) % Q for j in range(n + margin)]
    out = beam_pass(c, prev, comb, model, litf, beam, logf, 0, 0.0)
    if out is None:
        out = last_out
    best_state, plains, parents, js = out
    plain, ptrs = traceback(best_state[2], plains, parents, js)
    ioc = periodic_ioc(plain, ptrs, L)
    if out_path:
        info = dict(ioc=ioc, wcol=wcol, plain=plain, ptrs=ptrs, ll=best_state[1] / n,
                    overall=overall_ioc(plain))
        return ioc, info
    return ioc, wcol


def decode_t_only(c, prev, ts, model, beam=32):
    """t alone (L = 0, the blind old-screen view): beam over the skip branches pruned by the
    running IoC of the decoded symbols; returns (final IoC, info)."""
    n = len(c)
    clen = len(ts)
    states = [(0, [0] * Q, 0)]              # (j, counts, used)
    for i in range(n):
        ci = c[i]
        pv = prev if i == 0 else c[i - 1]
        cand = []
        for j, cnt, used in states:
            k0 = ts[j]
            q0 = SUB[ci][k0]
            nj0 = j + 2 if (model == 1 and pv == ci) else j + 1
            cand.append((nj0, q0, cnt, used))
            if pv >= 0:
                if model == 0:
                    if j + 1 < clen:
                        k1 = ts[j + 1]
                        t1 = SUB[ci][k1]
                        if ADD[t1][k0] == pv:
                            cand.append((j + 2, t1, cnt, used))
                        if j + 2 < clen:
                            k2 = ts[j + 2]
                            t2 = SUB[ci][k2]
                            if ADD[t2][k0] == pv and ADD[t2][k1] == pv:
                                cand.append((j + 3, t2, cnt, used))
                else:
                    if j + 2 < clen:
                        k2 = ts[j + 2]
                        t2 = SUB[ci][k2]
                        if ADD[t2][k0] == pv:
                            cand.append((j + 3, t2, cnt, used))
        best = {}
        for nj, q, cnt, used in cand:
            c2 = cnt[:]
            c2[q] += 1
            u2 = used + 1
            sc = Q * float(sum(x * (x - 1) for x in c2)) / (u2 * (u2 - 1)) if u2 > 1 else 0.0
            b = best.get(nj)
            if b is None or sc > b[2]:
                best[nj] = (c2, u2, sc)
        items = list(best.items())
        if len(items) > beam:
            items.sort(key=lambda t: -t[1][2])
            items = items[:beam]
        states = [(nj, c2, u2, sc) for nj, (c2, u2, sc) in items]
    if not states:
        return 0.0, None
    best_sc = max(states, key=lambda t: t[3])[3]
    return best_sc, dict(ioc=best_sc)


# ------------------------------------------------------------------ planting (the two-stack cipher in Python)

def plant(plain, tvals, offset, kw, model, keep=0.19, litf=False, b=0, seed=1):
    """Encrypt plaintext runes with the combined key t + w: the anti-repeat rule of
    work/layer2's plant applied to the combined key, and the literal-F rule (plaintext F is
    written as F and consumes no key value). keep = 1 - q, q = 0.81."""
    rng = random.Random(seed)
    m = len(kw)
    j, prev, out = 0, -1, []
    for p in plain:
        if litf and p == 0:
            y = 0
        else:
            y = (p + tvals[offset + j] + kw[j % m] + b) % Q
            j += 1
            if model == 0:
                tries = 0
                while prev >= 0 and y == prev and rng.random() >= keep and tries < 5:
                    y = (p + tvals[offset + j] + kw[j % m] + b) % Q
                    j += 1
                    tries += 1
            elif prev >= 0 and y == prev:
                j += 1
                if rng.random() >= keep:
                    y = (p + tvals[offset + j] + kw[j % m] + b) % Q
                    j += 1
        out.append(y)
        prev = y
    return out


# ------------------------------------------------------------------ windows and sweeps

def load_windows(path, n=300):
    """kscreen window format (W name prev / R runes): first n runes of each window."""
    wins = []
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    for i, line in enumerate(lines):
        if line.startswith("W "):
            parts = line.split()
            name = parts[1]
            prev = int(parts[2]) if len(parts) > 2 else -1
            runes = [int(x) for x in lines[i + 1][2:].split()][:n]
            wins.append((name, prev, runes))
    return wins


_G = {}


def init_worker(logf, streams, windows, cfg):
    global _G
    _G = dict(logf=logf, streams=streams, windows=windows, cfg=cfg)


def run_chunk(args):
    """One chunk of the (offset, L) grid for one (window, stream, model)."""
    wi, stream_id, model, off0, off1, Ls = args
    c, prev = _G["windows"][wi]
    tvals = _G["streams"][stream_id]
    logf = _G["logf"]
    cfg = _G["cfg"]
    best = (0.0, -1, -1)
    decodes = 0
    for off in range(off0, off1):
        for L in Ls:
            ioc, _ = decode(c, prev, tvals, off, L, model, cfg["litf"], cfg["beam"], cfg["max_em"],
                            logf, cfg["abort_at"], cfg["abort_margin"], False,
                            cfg.get("beam_a", 12))
            decodes += 1
            if ioc > best[0]:
                best = (ioc, off, L)
    return (wi, stream_id, model, best, decodes)


def run_sweep(streams, windows, tasks, cfg, workers=8, label="sweep"):
    """Run task chunks in worker processes. tasks: (wi, stream_id, model, off0, off1, Ls).
    Returns (results, stats) with results[task-index] = (best_ioc, off, L, decodes)."""
    import concurrent.futures as cf
    logf = english_logf()
    t0 = time.time()
    done = 0
    total_dec = 0
    with cf.ProcessPoolExecutor(max_workers=workers, initializer=init_worker,
                                initargs=(logf, streams, windows, cfg)) as ex:
        futs = [ex.submit(run_chunk, t) for t in tasks]
        for fut in cf.as_completed(futs):
            res = fut.result()
            done += 1
            total_dec += res[4]
            el = time.time() - t0
            if el >= 10 and (done % max(1, len(tasks) // 20) == 0 or done == len(tasks)):
                print(f"[{label}] {done}/{len(tasks)} tasks, {total_dec} decodes, "
                      f"{total_dec / el:.0f} decodes/s (wall, {workers} workers), "
                      f"eta {el * (len(tasks) - done) / done:.0f}s", flush=True)
    el = time.time() - t0
    results = [None] * len(tasks)
    for i, fut in enumerate(futs):
        wi, stream_id, model, best, decodes = fut.result()
        results[i] = (wi, stream_id, model, best, decodes)
    stats = dict(secs=el, decodes=total_dec, tasks=len(tasks), workers=workers,
                 rate=total_dec / el if el else 0.0)
    print(f"[{label}] done: {total_dec} decodes in {el:.0f}s = {stats['rate']:.0f} decodes/s wall "
          f"({stats['rate'] / workers:.0f} per core)", flush=True)
    return results, stats


def redecode(c, prev, tvals, offset, L, model, litf=False, beam=64, max_em=10):
    """Verification re-decode of one candidate with a wider beam; returns (ioc, info dict)."""
    logf = english_logf()
    return decode(c, prev, tvals, offset, L, model, litf, beam, max_em, logf, 0, 0.0, True)


def latin_render(plain, limit=160):
    return "".join(LATIN[x] if 0 <= x < Q else "?" for x in plain[:limit])
