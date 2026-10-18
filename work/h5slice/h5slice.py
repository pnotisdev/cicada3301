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
   * estimate the L column shifts w by the maximum-likelihood shift under the English rune
     distribution (the distribution-aware modal class) from p_i = c_i - t_{j(i)};
   * re-decode with a beam over the skip branches (drift tracking; a skip branch exists only
     where the collision is consistent with the combined key, as in work/kscreen), pruning
     the beam by the plaintext log-likelihood (about 0.4 nats/rune on truth, the information
     budget of HYPOTHESES.md:18-24);
   * re-estimate w from the best path; repeat until w is stable.
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


def beam_coincidence(c, prev, ts, L, litf, beam, abort_at=0, abort_z=0.0):
    """Init pass: beam over FREE pointer branches (+1/+2/+3 and the literal-F branch), scored
    by the running column-coincidence z = (Q s - d)/sqrt(56 d) (layer2's periodic z). The z is
    w-free (shift-invariant within a column), so the true pointer alignment is found before the
    keyword columns are known; the LL-EM then starts from its per-column estimate.
    Returns (ptrs, z) for the best state, or None when the abort fires."""
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


def decode(c, prev, tvals, offset, L, model, litf=False, beam=24, max_em=6, logf=None,
           abort_at=0, abort_margin=0.0, out_path=False, beam_a=12, abort_z=1.8):
    """Decode one window at one (offset, L). Two stages:
      1. coincidence init: free-branch beam scored by the w-free column z -> pointer alignment
         -> per-column ML shift w (the distribution-aware modal class);
      2. EM over w: beam over the collision-consistent skip branches (layer2's outer_cands on
         the combined key t + w), pruned by the plaintext log-likelihood, re-estimating w from
         the best path until it is stable; score = periodic IoC of the final columns.
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
    a = beam_coincidence(c, prev, ts, L, litf, beam_a, abort_at, abort_z)
    if a is None:
        return 0.0, None
    ptrsA, _zA = a
    wcol = est_cols(c, ts, ptrsA, L, logf)
    abort_ll = abort_at * (float(np.mean(logf)) + abort_margin) if abort_at else 0.0
    last_out = None
    for _ in range(max_em):
        comb = [(ts[j] + wcol[j % L]) % Q for j in range(n + margin)]
        out = beam_pass(c, prev, comb, model, litf, beam, logf, abort_at, abort_ll)
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
        # the LL-EM aborted (its evidence is noise): score the coincidence-init path as-is
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
                            cfg.get("beam_a", 12), cfg.get("abort_z", 1.8))
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
