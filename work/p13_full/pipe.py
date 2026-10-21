"""Phase 49 task A: full selection pipeline for Mike's period-13 claim, re-implemented (his code was not run).
Statistic per stream: max over paragraphs (>=150 runes) x periods 2..40 of the column IoC x29 of the delta stream
(c[-1]=0 at the paragraph start) with the best choice of up to 5 skipped positions sharing one delta value
(position 0 excluded; skipped positions are dropped and do not advance the column)."""
import os, sys, numpy as np
from numba import njit
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import lp

PERIODS = np.arange(2, 41)
EXACT_MAX_L = 340          # exact exhaustive up to here (308, 333), per-value greedy up to GREEDY_MAX_L, no skips beyond
GREEDY_MAX_L = 1100


def load_paragraphs():
    """Return (list of rune arrays per paragraph, section id per paragraph) for LP2 = segments 0.7-0.15."""
    segs = lp.load_segments(); paras = []; sec = []
    for si in range(7, 16):
        cur = []
        for t in segs[si] + ['&']:
            if isinstance(t, int): cur.append(t)
            elif t == '&' and cur: paras.append(np.array(cur)); sec.append(si); cur = []
    return paras, np.array(sec)


def deltas(c):
    c = np.asarray(c); return np.concatenate([[c[0]], (c[1:] - c[:-1]) % 29]).astype(np.int64)


@njit(cache=True)
def ioc_skip(d, sk, nsk, p):
    """Column IoC x29 with the first nsk entries of sk (sorted) removed."""
    L = len(d); h = np.zeros(p * 29, np.int64); e = 0; j = 0
    for i in range(L):
        if j < nsk and sk[j] == i:
            j += 1; continue
        h[(e % p) * 29 + d[i]] += 1; e += 1
    s = 0
    for x in h: s += x * (x - 1)
    M = e; q = M // p; r = M - q * p
    den = r * (q + 1) * q + (p - r) * q * (q - 1)
    if den <= 0: return 0.0
    return 29.0 * s / den


@njit(cache=True)
def base_ioc(d, p):
    sk = np.zeros(1, np.int64); return ioc_skip(d, sk, 0, p)


@njit(cache=True)
def greedy_best(d, p):
    """Per delta value: add the best skip (of that value) one at a time up to 5; return the best IoC seen."""
    L = len(d); best = ioc_skip(d, np.zeros(1, np.int64), 0, p)
    sk = np.zeros(5, np.int64)
    for v in range(29):
        n = 0
        for step in range(5):
            bi = -1.0; bp = -1
            for i in range(1, L):
                if d[i] != v: continue
                dup = False
                for t in range(n):
                    if sk[t] == i: dup = True
                if dup: continue
                tmp = np.empty(n + 1, np.int64)
                for t in range(n): tmp[t] = sk[t]
                tmp[n] = i; tmp.sort()
                x = ioc_skip(d, tmp, n + 1, p)
                if x > bi: bi = x; bp = i
            if bp < 0: break
            sk[n] = bp; n += 1; sk[:n].sort()
            if bi > best: best = bi
    return best


@njit(cache=True)
def build_tables(d, p, R):
    L = len(d); P = np.zeros((R, L + 1, L + 1), np.int32)
    for r in range(R):
        for i in range(L):
            for j in range(L):
                v = 0
                if i < j and d[i] == d[j] and (j - i - r) % p == 0: v = 1
                P[r, i + 1, j + 1] = v + P[r, i, j + 1] + P[r, i + 1, j] - P[r, i, j]
    return P


@njit(cache=True)
def eval_sk(P, p, L, sk, k):
    lo = np.empty(k + 1, np.int64); hi = np.empty(k + 1, np.int64)
    lo[0] = 0
    for t in range(k):
        hi[t] = sk[t]; lo[t + 1] = sk[t] + 1
    hi[k] = L; U = 0
    for a in range(k + 1):
        for b in range(a, k + 1):
            r = (b - a) % p
            U += P[r, hi[a], hi[b]] - P[r, lo[a], hi[b]] - P[r, hi[a], lo[b]] + P[r, lo[a], lo[b]]
    M = L - k; q = M // p; rem = M - q * p
    den = rem * (q + 1) * q + (p - rem) * q * (q - 1)
    if den <= 0: return 0.0
    return 29.0 * 2 * U / den


@njit(cache=True)
def exact_best(d, p):
    """Exhaustive over all subsets of <=5 positions (>0) sharing one delta value, via 2-D prefix tables."""
    L = len(d); R = min(p, 6); P = build_tables(d, p, R)
    best = eval_sk(P, p, L, np.zeros(1, np.int64), 0)
    for v in range(29):
        cnt = 0
        for i in range(1, L):
            if d[i] == v: cnt += 1
        pos = np.empty(cnt, np.int64); c = 0
        for i in range(1, L):
            if d[i] == v: pos[c] = i; c += 1
        for k in range(1, min(5, cnt) + 1):
            idx = np.arange(k); sk = np.empty(k, np.int64)
            while True:
                for t in range(k): sk[t] = pos[idx[t]]
                x = eval_sk(P, p, L, sk, k)
                if x > best: best = x
                t = k - 1
                while t >= 0 and idx[t] == cnt - k + t: t -= 1
                if t < 0: break
                idx[t] += 1
                for u in range(t + 1, k): idx[u] = idx[u - 1] + 1
    return best


def stream_max(paras_c, exact_max_l=EXACT_MAX_L, periods=PERIODS):
    """Overall maximum of the pipeline over paragraphs >=150 and periods; also returns unskipped maximum and argmax."""
    best = (0.0, None, None); best0 = 0.0
    for gi, c in enumerate(paras_c):
        if len(c) < 150: continue
        d = deltas(c)
        for p in periods:
            b0 = base_ioc(d, int(p)); best0 = max(best0, b0)
            x = exact_best(d, int(p)) if len(d) <= exact_max_l else greedy_best(d, int(p)) if len(d) <= GREEDY_MAX_L else b0
            if x > best[0]: best = (x, gi, int(p))
    return best, best0
