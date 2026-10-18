"""Numba port of the H5 first-slice coincidence init (beam_coincidence_nats).

Exact same scoring/merge/abort semantics as h5slice.beam_coincidence_nats (the slow,
verified reference): free +1/+2/+3 pointer branches plus the literal-F branch, states
carry the log-domain column products G[col,v] = sum_i logf[(x_i - v) mod 29], scored
sum_col logsumexp_v G[col,v] + skips*ln(0.028); per-pointer merge keeps the FIRST strict
maximum; truncation is a stable sort by -score; the abort fires only at the abort_at
checkpoint. The only intended differences are last-ulp rounding of exp/log (numba libm
vs numpy's vectorized exp), far inside the 1e-6-nats parity tolerance.

Optional dependency: numba. h5slice falls back to the numpy corr-trick init
(beam_coincidence_nats_fast) when this module cannot be imported.
"""
import numpy as np
from numba import njit

import h5slice as H

SUBM = np.asarray(H.SUB, dtype=np.int64)


@njit(cache=True)
def _kernel(c, ts, SUBM, MT, L, litf, beam, abort_at, abort_ll, ln028, n, tlen):
    B = beam
    LQ = L * 29
    G = np.zeros(B * LQ)                    # flat: G[p*LQ + col*29 + v]
    G2 = np.zeros(B * LQ)
    Lc = np.full((B, L), np.log(29.0))
    Lc2 = np.full((B, L), np.log(29.0))
    S = np.zeros(B)
    S2 = np.zeros(B)
    js = np.zeros(B, np.int64)
    js2 = np.zeros(B, np.int64)
    nds = np.full(B, -1, np.int64)
    nds2 = np.full(B, -1, np.int64)
    S[0] = L * np.log(29.0)
    W = 1
    max_nodes = 1 + n * B * 4
    ks_all = np.zeros(max_nodes, np.int64)
    parents = np.full(max_nodes, -1, np.int64)
    n_nodes = 1
    NMAX = B * 4
    par = np.zeros(NMAX, np.int64)
    kidx = np.zeros(NMAX, np.int64)
    cost = np.zeros(NMAX)
    q = np.zeros(NMAX, np.int64)
    col = np.zeros(NMAX, np.int64)
    lse2 = np.zeros(NMAX)
    s2 = np.zeros(NMAX)
    nj = np.zeros(NMAX, np.int64)
    nju = np.zeros(NMAX, np.int64)
    s2u = np.zeros(NMAX)
    tu = np.zeros(NMAX, np.int64)
    for i in range(n):
        ci = c[i]
        nb = 4 if (litf and ci == 0) else 3
        N = 0
        for w in range(W):
            j = js[w]
            for dk in range(3):
                k = j + dk
                if k < tlen:
                    kk = k
                else:
                    kk = tlen - 1
                par[N] = w
                kidx[N] = k
                if k < tlen:
                    cost[N] = dk * ln028
                else:
                    cost[N] = -1e18
                q[N] = SUBM[ci, ts[kk]]
                col[N] = kk % L
                N += 1
            if nb == 4:
                par[N] = w
                kidx[N] = j
                cost[N] = 0.0
                q[N] = 0
                col[N] = j % L
                N += 1
        for t in range(N):
            p = par[t]
            gbase = p * LQ + col[t] * 29
            qv = q[t]
            m = -1e300
            for v in range(29):
                u = G[gbase + v] + MT[qv, v]
                if u > m:
                    m = u
            acc = 0.0
            for v in range(29):
                acc += np.exp(G[gbase + v] + MT[qv, v] - m)
            lse2[t] = m + np.log(acc)
            s2[t] = S[p] + (lse2[t] - Lc[p, col[t]]) + cost[t]
            nj[t] = kidx[t] + 1
        # merge: first strict maximum per nj, first-appearance order
        ucount = 0
        for t in range(N):
            found = -1
            for u in range(ucount):
                if nju[u] == nj[t]:
                    found = u
                    break
            if found < 0:
                nju[ucount] = nj[t]
                s2u[ucount] = s2[t]
                tu[ucount] = t
                ucount += 1
            else:
                if s2[t] > s2u[found]:
                    s2u[found] = s2[t]
                    tu[found] = t
        # stable sort by -score (insertion sort) ALWAYS, exactly like the slow version's
        # unconditional items.sort: the abort check below reads s2u[0] as the max, and in
        # the unsorted case s2u[0] is the first-inserted nj's score, not the max.
        for a in range(1, ucount):
            xnj = nju[a]
            xs = s2u[a]
            xt = tu[a]
            b = a - 1
            while b >= 0 and s2u[b] < xs:
                nju[b + 1] = nju[b]
                s2u[b + 1] = s2u[b]
                tu[b + 1] = tu[b]
                b -= 1
            nju[b + 1] = xnj
            s2u[b + 1] = xs
            tu[b + 1] = xt
        if ucount > B:
            ucount = B
        if abort_at and i + 1 == abort_at:
            if ucount == 0 or s2u[0] < abort_ll:
                return None
        # survivors (each survivor's row is rebuilt from its parent + the new letter)
        for ii in range(ucount):
            t = tu[ii]
            p = par[t]
            node = n_nodes
            ks_all[node] = kidx[t]
            parents[node] = nds[p]
            for v in range(LQ):
                G2[ii * LQ + v] = G[p * LQ + v]
            gbase = ii * LQ + col[t] * 29
            for v in range(29):
                G2[gbase + v] += MT[q[t], v]
            for cc in range(L):
                Lc2[ii, cc] = Lc[p, cc]
            Lc2[ii, col[t]] = lse2[t]
            S2[ii] = s2[t]
            js2[ii] = nj[t]
            nds2[ii] = node
            n_nodes += 1
        m2 = ucount
        for r in range(m2):
            for v in range(LQ):
                G[r * LQ + v] = G2[r * LQ + v]
            for cc in range(L):
                Lc[r, cc] = Lc2[r, cc]
            S[r] = S2[r]
            js[r] = js2[r]
            nds[r] = nds2[r]
        W = m2
    if W == 0:
        return None
    best = 0
    for r in range(1, W):
        if S[r] > S[best]:
            best = r
    node = nds[best]
    ptrs = np.zeros(n, np.int64)
    for i in range(n - 1, -1, -1):
        ptrs[i] = ks_all[node]
        node = parents[node]
    return ptrs, S[best]


def beam_coincidence_nats_numba(c, prev, ts, L, litf, beam, logf, abort_at=0,
                                abort_ll=0.0):
    """Numba init; returns (ptrs list, score float) or None on abort - same contract as
    h5slice.beam_coincidence_nats."""
    c_arr = np.asarray(c, dtype=np.int64)
    ts_arr = np.asarray(ts, dtype=np.int64)
    MT = H._ls_matrix(logf).T.astype(np.float64)
    r = _kernel(c_arr, ts_arr, SUBM, MT, L, bool(litf), int(beam), int(abort_at),
                float(abort_ll), float(H.LN_028), len(c), len(ts_arr))
    if r is None:
        return None
    ptrs, score = r
    return ptrs.tolist(), float(score)
