"""The statistical fingerprint of LP2, computed the same way for the real text and for every simulated replicate.

Pairs never cross a section. Statistics (all pooled over the text):
  ioc      normalised index of coincidence of the runes (1 = flat, English runes ~ 1.8)
  dbl_in   adjacent equal runes inside words, %            (LP2: 0.63; chance 3.5)
  dbl_seam adjacent equal runes across a word seam, %      (LP2: 0.79)
  z5       within-word lag-5 coincidences, z against S = sum f^2      (LP2: +3.7)
  zoth     largest |z| of the within-word lags 2,3,4,6,7,8,9 (a periodic-5 structure leaves the neighbours at chance)
  maxz5    largest per-rune Poisson z of the within-word lag-5 coincidences (LP2: rune S, 11 against 2.3 expected)
  rep      word types of 3+ runes that occur at least twice (LP2: 16 by this count, murphy's repo 16 against 11.0 +- 3.1 for random)
  dioc     largest IoC of the lag-m differences c_i - c_{i-m}, m = 1..8 (a ciphertext autokey leaks the plaintext here)
  lagz     largest z of the equal-rune count at lags 2..40, whole sections (a periodic key of period p shows at lag p)
  first    IoC of the first runes of words (a per-word state shows here)
"""
import numpy as np

N = 29
NAMES = ["ioc", "dbl_in", "dbl_seam", "z5", "zoth", "maxz5", "rep", "dioc", "lagz", "first"]


def _ioc(x):
    n = len(x)
    c = np.bincount(x, minlength=N)
    return float((c * (c - 1)).sum() / (n * (n - 1) / N))


def fingerprint(C, start, sid):
    """C (T,) cipher runes, start (T,) bool word starts, sid (T,) section ids -> dict of the statistics above"""
    n = len(C)
    wid = np.cumsum(start)
    f = np.bincount(C, minlength=N) / n
    S = float((f ** 2).sum())
    out = {"ioc": _ioc(C)}
    same = sid[1:] == sid[:-1]
    eq = C[1:] == C[:-1]
    inw = same & (wid[1:] == wid[:-1])
    seam = same & ~(wid[1:] == wid[:-1])
    out["dbl_in"] = 100 * float(eq[inw].mean()); out["dbl_seam"] = 100 * float(eq[seam].mean())
    z, hits = {}, None
    for d in range(2, 10):
        v = (wid[d:] == wid[:-d]) & (sid[d:] == sid[:-d])
        e = (C[d:] == C[:-d]) & v
        m = int(v.sum())
        z[d] = (int(e.sum()) - m * S) / np.sqrt(m * S * (1 - S))
        if d == 5:
            hits = C[:-d][e]
            tot = len(hits)
    out["z5"] = float(z[5])
    out["zoth"] = float(max(abs(z[d]) for d in (2, 3, 4, 6, 7, 8, 9)))
    k = np.bincount(hits, minlength=N)
    ex = tot * f ** 2 / S
    out["maxz5"] = float(((k - ex) / np.sqrt(np.maximum(ex, 0.5))).max()) if tot else 0.0
    ws = np.flatnonzero(start)
    we = np.append(ws[1:], n)
    seen = {}
    for a, b in zip(ws, we):
        if b - a >= 3:
            w = C[a:b].tobytes()
            seen[w] = seen.get(w, 0) + 1
    out["rep"] = sum(v >= 2 for v in seen.values())
    best = 0.0
    for m in range(1, 9):
        ok = sid[m:] == sid[:-m]
        best = max(best, _ioc(((C[m:] - C[:-m]) % N)[ok]))
    out["dioc"] = best
    out["lagz"] = max(float((((C[d:] == C[:-d]) & (sid[d:] == sid[:-d])).sum() - (sid[d:] == sid[:-d]).sum() * S) / np.sqrt((sid[d:] == sid[:-d]).sum() * S * (1 - S)))
                      for d in range(2, 41))
    out["first"] = _ioc(C[ws])
    return out


def many(C, start, sid):
    """fingerprints of the R replicates of C (R, T): array (R, len(NAMES))"""
    st = np.broadcast_to(start, C.shape) if start.ndim == 1 else start
    return np.array([[fingerprint(C[r], st[r], sid)[k] for k in NAMES] for r in range(len(C))])
