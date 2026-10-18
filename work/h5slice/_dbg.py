"""Debug the init beam trajectory on the truth plant."""
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import h5slice as H
import sim

logf = H.english_logf()
plain = sim.english_runes()[3000:3300]
tvals = H.totient(4000)
OFF = 1234
c = H.plant(plain, tvals, OFF, H.DIVINITY, 0, keep=0.19, litf=False, b=0, seed=42)
ts = tvals[OFF:OFF + 300 + 107]

# replicate the init loop with instrumentation
Q = 29
n = 300
tlen = len(ts)
L = 8
beam = 12
LN_028 = H.LN_028
M = H._ls_matrix(logf)
MT = M.T
js = [0]
G = [np.zeros(L * Q)]
Lc = [np.full(L, math.log(Q))]
S = [L * math.log(Q)]
nds = [-1]
ks_all = []
parents = []

t0 = time.time()
for i in range(n):
    ci = c[i]
    W = len(js)
    nb = 3
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
                ql.append(H.SUB[ci][ts[k]])
            else:
                kidx.append(0)
                cost.append(float("-inf"))
                ql.append(0)
    N = len(par)
    kidx = np.array(kidx, dtype=np.int64)
    cost = np.array(cost)
    col = np.array(kidx) % L
    Gmat = np.stack(G)
    Lcm = np.stack(Lc)
    Sm = np.array(S)
    ndm = np.array(nds)
    G2 = Gmat[par]
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
    if (i + 1) in (30, 60, 90, 120, 150, 200, 250, 299, 300):
        print("i=%3d states=%d best=%.1f (%.3f/rune) worst=%.1f js=%s"
              % (i + 1, len(js), max(S), max(S) / (i + 1), min(S), sorted(js)))
t1 = time.time()
print("total init %.1f ms" % (1000 * (t1 - t0)))
best_i = max(range(len(S)), key=lambda k: S[k])
ptrs = H.path_back(nds[best_i], ks_all, parents)
print("final ptrs skips =", sum(ptrs[i] - ptrs[i - 1] - 1 for i in range(1, len(ptrs))))
print("null level check: uni_mean*300+8*ln29 =", 300 * H.uni_mean_logf() + 8 * np.log(29))
print("threshold at 120, margin 0.15 =", 120 * (H.uni_mean_logf() + 0.15) + L * np.log(29))
