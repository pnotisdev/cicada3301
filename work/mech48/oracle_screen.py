"""Phase 48 step 4 prototype: A/I oracle as a screen statistic over (stream, offset). Pointer-set DP, no language model.

State after i runes: weight w[d] for pointer j = o + i + d (d = accumulated skip drift). Transitions per rune are the
engine's model 0 (normal; skip-1 / skip-2 when the skipped key value would have reproduced the previous ciphertext).
Score = sum over one-rune words of the weight-averaged indicator (decoded value in {A, I})."""
import sys, struct, time
import numpy as np
from numba import njit
sys.path.insert(0, "work")
import lp
Q = 29; A_, I_ = 24, 10

def load_ksb(path):
    b = open(path, "rb").read(); assert b[:4] == b"KSB1"
    n = struct.unpack_from("<I", b, 4)[0]; p = 8; out = []
    for _ in range(n):
        ln = struct.unpack_from("<H", b, p)[0]; name = b[p+2:p+2+ln].decode("utf-8", "replace"); p += 2 + ln
        kl = struct.unpack_from("<I", b, p)[0]; out.append((name, np.frombuffer(b, np.uint8, kl, p + 4))); p += 4 + kl
    return out

@njit(cache=True)
def oracle(c, isone, key, off, D, limit):
    """c: ciphertext runes (int64), isone: 1 where a one-rune word sits, key: multiplied key (uint8). Returns (score, words scored)."""
    n = min(len(c), limit)
    w = np.zeros(D); w[0] = 1.0
    nw = np.zeros(D)
    score = 0.0; cnt = 0
    for i in range(n):
        pv = c[i-1] if i > 0 else -1
        nw[:] = 0.0
        ai = 0.0; tot = 0.0
        for d in range(D):
            if w[d] == 0.0: continue
            j = off + i + d
            if j + 3 >= len(key): continue
            t0 = (c[i] - key[j]) % Q
            nw[d] += w[d]                       # normal: pointer j -> j+1, drift unchanged
            if isone[i] and (t0 == A_ or t0 == I_): ai += w[d]
            tot += w[d]
            if pv >= 0:
                t1 = (c[i] - key[j+1]) % Q
                if (t1 + key[j]) % Q == pv and d + 1 < D:
                    nw[d+1] += w[d]
                    if isone[i] and (t1 == A_ or t1 == I_): ai += w[d]
                    tot += w[d]
                t2 = (c[i] - key[j+2]) % Q
                if (t2 + key[j]) % Q == pv and (t2 + key[j+1]) % Q == pv and d + 2 < D:
                    nw[d+2] += w[d]
                    if isone[i] and (t2 == A_ or t2 == I_): ai += w[d]
                    tot += w[d]
        s = nw.sum()
        if s == 0.0: break
        w[:] = nw / s
        if isone[i] and tot > 0:
            score += ai / tot; cnt += 1
    return score, cnt

def encrypt(p, key, off):
    """Model-0 encryptor: skip a key value while it would reproduce the previous ciphertext (always-skip)."""
    c, j, pv = [], off, -1
    for t in p:
        while (t + key[j]) % Q == pv: j += 1
        x = (t + key[j]) % Q; c.append(x); j += 1; pv = x
    return np.array(c, dtype=np.int64)

def windows():
    segs = lp.load_segments(); W = {}
    for i in range(7, 16):
        r = np.array(lp.runes_of(segs[i]), dtype=np.int64)
        isone = np.zeros(len(r), dtype=np.int64)
        for w, a, b in lp.word_spans(segs[i], r.tolist()):
            if b - a == 1: isone[a] = 1
        W[i] = (r, isone)
    return segs, W

@njit(cache=True)
def oracle_max(c, isone, key, off, D, limit):
    """Viterbi variant: best A/I count over all pointer paths consistent with model 0 (same transitions as `oracle`)."""
    n = min(len(c), limit)
    NEG = -1
    f = np.full(D, NEG); f[0] = 0
    g = np.full(D, NEG)
    words = 0
    for i in range(n):
        pv = c[i-1] if i > 0 else -1
        g[:] = NEG
        for d in range(D):
            if f[d] < 0: continue
            j = off + i + d
            if j + 3 >= len(key): continue
            t0 = (c[i] - key[j]) % Q
            hit = 1 if (isone[i] and (t0 == A_ or t0 == I_)) else 0
            if f[d] + hit > g[d]: g[d] = f[d] + hit
            if pv >= 0:
                t1 = (c[i] - key[j+1]) % Q
                if (t1 + key[j]) % Q == pv and d + 1 < D:
                    h1 = 1 if (isone[i] and (t1 == A_ or t1 == I_)) else 0
                    if f[d] + h1 > g[d+1]: g[d+1] = f[d] + h1
                t2 = (c[i] - key[j+2]) % Q
                if (t2 + key[j]) % Q == pv and (t2 + key[j+1]) % Q == pv and d + 2 < D:
                    h2 = 1 if (isone[i] and (t2 == A_ or t2 == I_)) else 0
                    if f[d] + h2 > g[d+2]: g[d+2] = f[d] + h2
        if isone[i]: words += 1
        f[:] = g
        if f.max() < 0: break
    return float(f.max()), words
