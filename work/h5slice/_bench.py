"""Micro-benchmark the per-rune numpy ops of the fast init to find the real cost driver."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import h5slice as H
import sim

logf = H.english_logf()
M = H._ls_matrix(logf)
MT = M.T
SUBM = np.array(H.SUB)
Q = 29
L = 8
B = 12
N = 3 * B

rng = np.random.default_rng(0)
Gmat = rng.standard_normal((B, L * Q))
Lcm = rng.standard_normal((B, L))
Sm = rng.standard_normal(B)
ndm = np.arange(B)
js = list(range(B))
kidx = np.zeros(B * 4, dtype=np.int64)
cost = np.zeros(B * 4)
ql = np.zeros(B * 4, dtype=np.int64)
G2 = np.zeros((B * 4, L * Q))
rows = np.arange(B * 4)
offs = np.array([0, 1, 2, 0])
costs = np.array([0.0, H.LN_028, 2.0 * H.LN_028, 0.0])
ts_arr = np.random.default_rng(1).integers(0, Q, 5000)


def bench(label, fn, reps):
    fn()
    t0 = time.perf_counter()
    for _ in range(reps):
        fn()
    t1 = time.perf_counter()
    us = (t1 - t0) / reps * 1e6
    print(f"{label:52s} {us:8.1f} us")
    return us


def f1():
    kidx[:N] = np.repeat(np.asarray(js), 3) + np.tile(offs[:3], B)
    valid = kidx[:N] < 5000
    cost[:N] = np.where(valid, np.tile(costs[:3], B), -1e18)
    kk = np.minimum(np.maximum(kidx[:N], 0), 4999)
    ql[:N] = SUBM[0][ts_arr[kk]]
    return valid


def f2():
    par = np.repeat(np.arange(B), 3)
    G2[:N] = Gmat[par]


def f3():
    par = np.repeat(np.arange(B), 3)
    col = kidx[:N] % L
    G2[:N] = Gmat[par]
    idx = col[:, None] * Q + np.arange(Q)[None, :]
    G2[rows[:N, None], idx] += MT[ql[:N]]
    upd = G2[rows[:N, None], idx]
    return upd


def f4():
    upd = f3()
    m = upd.max(axis=1)
    lse2 = m + np.log(np.exp(upd - m[:, None]).sum(axis=1))
    return lse2


def f5():
    s2 = rng.standard_normal(N)
    nj = kidx[:N] + 1
    order = np.lexsort((-s2, nj))
    _, first = np.unique(nj[order], return_index=True)
    surv = order[first]
    if surv.size > B:
        surv = np.sort(surv)
        surv = surv[np.argsort(-s2[surv], kind="stable")[:B]]
    return surv


C = np.stack([np.roll(np.exp(MT[0]), q) for q in range(Q)])


def f6():
    par = np.repeat(np.arange(B), 3)
    col = kidx[:N] % L
    Gcols = Gmat.reshape(B, L, Q)[par, col]
    mm = Gcols.max(axis=1)
    E = np.exp(Gcols - mm[:, None])
    corr = E @ C
    lse2 = np.log(corr[rows[:N], ql[:N]]) + mm
    return lse2


def f6b():
    # direct version: gather MT[ql] instead of matmul
    par = np.repeat(np.arange(B), 3)
    col = kidx[:N] % L
    Gcols = Gmat.reshape(B, L, Q)[par, col]
    mm = Gcols.max(axis=1)
    terms = np.exp(Gcols - mm[:, None] + MT[ql[:N]])
    lse2 = np.log(terms.sum(axis=1)) + mm
    return lse2


m2 = 12
def f7():
    par = np.repeat(np.arange(B), 3)
    col = kidx[:N] % L
    surv = np.arange(m2)
    Gmat[:m2] = Gmat[par[surv]]
    idx = col[surv][:, None] * Q + np.arange(Q)[None, :]
    Gmat[rows[:m2, None], idx] += MT[ql[surv]]
    upd = Gmat[rows[:m2, None], idx]
    m = upd.max(axis=1)


bench("candidate build (tile/repeat/where/gather)", f1, 2000)
bench("row copy G2[:N] = Gmat[par]", f2, 2000)
bench("scatter-add + gather (current hot path)", f3, 2000)
bench("logsumexp (N,29) after scatter", f4, 2000)
bench("merge lexsort+unique+stable-truncate", f5, 2000)
bench("corr-trick lse2 (E@C matmul)", f6, 2000)
bench("direct lse2 (exp-sum, no matmul)", f6b, 2000)
bench("survivor update m2=12 (full)", f7, 2000)

# exactness of the corr trick vs slow formula on random columns
for trial in range(5):
    g = rng.standard_normal(Q)
    q = int(rng.integers(0, Q))
    upd = g + MT[q]
    m = upd.max()
    slow_lse = m + np.log(np.exp(upd - m).sum())
    E = np.exp(g - g.max())
    corr = E @ C
    fast_lse = np.log(corr[q]) + g.max()
    print(f"trial {trial}: slow {slow_lse:.12f} fast {fast_lse:.12f} diff {slow_lse - fast_lse:.3e}")
