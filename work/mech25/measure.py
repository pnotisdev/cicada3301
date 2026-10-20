"""Phase 25: the anomaly statistics of LP2, computed the same way on LP2 and on any simulated cipher text.

Each statistic follows the repository's own definition:
  doublets      adjacent equal pairs / adjacent pairs, inside sections; split in-word / across a word gap (obs-doublets)
  lag6, lag5    within-word pairs (i - L, i), hits of c_i = 24 - 2 c_(i-L) (lag 6) or c_i = c_(i-L) (lag 5), expected =
                pairs * sum_x f(x) f(rel(x)) with f the section's unigram frequencies (the shuffle mean of
                work/families/echo_position.py up to O(1/T)), z = excess / sqrt(expected); also the same for pairs across a
                word gap (the out-of-sample check) and by the word position of the earlier rune
  S5            lag-5 within-word hits whose rune is S (15)
  flat          unigram chi2 (df 28), bigram chi2 (29 x 29 adjacent pairs inside sections, df 812, doublet cells excluded
                because the anti-repeat rule removes them by design), max |z| of the coincidence rate at lags 2..60
  wordlen       G of LP2's word-length histogram against the simulated histogram as the model (work/wordlen.py bins
                1..11, 12+); for a simulation the G of its OWN histogram against English is reported too

    python work/mech25/measure.py      # LP2's values (the calibration of this module against the logged numbers)
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "families"))
import fam_data as D  # noqa: E402

N = 29
S = 15
T6 = (24 - 2 * np.arange(N)) % N
EQ = np.arange(N)
BINS = 12


def wordinfo(start):
    T = len(start)
    idx = np.arange(T)
    wid = np.cumsum(start)
    loc = idx - np.maximum.accumulate(np.where(start, idx, 0))
    return wid, loc


def _expect(c, sid, i, sel, rel):
    """sum over selected pairs of P(c_i = rel(c_(i-L))) under shuffles inside sections"""
    e = 0.0
    for k in np.unique(sid):
        m = sid == k
        f = np.bincount(c[m], minlength=N) / m.sum()
        e += sel[sid[i] == k].sum() * float((f * f[rel]).sum())
    return e


def relation(c, start, sid, L, rel):
    wid, loc = wordinfo(start)
    T = len(c)
    i = np.arange(L, T)
    ok = sid[i] == sid[i - L]
    same = ok & (wid[i] == wid[i - L])
    cross = ok & ~same
    hit = c[i] == rel[c[i - L]]
    out = {}
    for name, sel in (("in", same), ("x", cross)):
        h = int((hit & sel).sum())
        e = _expect(c, sid, i, sel, rel)
        out[name] = (int(sel.sum()), h, e, (h - e) / np.sqrt(max(e, 1e-9)))
    pos = loc[i - L]
    out["bypos"] = []
    for p in range(5):
        sel = same & ((pos == p) if p < 4 else (pos >= 4))
        h = int((hit & sel).sum())
        e = _expect(c, sid, i, sel, rel)
        out["bypos"].append((int(sel.sum()), h, e))
    out["S"] = int((hit & same & (c[i] == S)).sum())
    return out


def doublets(c, start, sid):
    i = np.arange(1, len(c))
    ok = sid[i] == sid[i - 1]
    eq = c[i] == c[i - 1]
    inw = ok & ~start[i]
    gap = ok & start[i]
    return (eq & ok).sum() / ok.sum(), (eq & inw).sum() / inw.sum(), (eq & gap).sum() / gap.sum()


def flatness(c, sid):
    f = np.bincount(c, minlength=N)
    e = len(c) / N
    uni = float(((f - e) ** 2 / e).sum())
    i = np.arange(1, len(c))
    ok = sid[i] == sid[i - 1]
    B = np.zeros((N, N))
    np.add.at(B, (c[i - 1][ok], c[i][ok]), 1)
    off = ~np.eye(N, dtype=bool)
    p = f / f.sum()
    E = np.outer(p, p)[off]
    E = E / E.sum() * B[off].sum()
    bi = float(((B[off] - E) ** 2 / E).sum())
    zmax, lagmax = 0.0, 0
    S2 = float((p * p).sum())
    for L in range(2, 61):
        j = np.arange(L, len(c))
        okL = sid[j] == sid[j - L]
        n = okL.sum()
        h = (c[j] == c[j - L])[okL].sum()
        z = (h - n * S2) / np.sqrt(n * S2 * (1 - S2))
        if abs(z) > abs(zmax):
            zmax, lagmax = float(z), L
    return uni, bi, zmax, lagmax


def hist(start):
    s = np.flatnonzero(start)
    L = np.diff(np.append(s, len(start)))
    h = np.bincount(np.minimum(L, BINS), minlength=BINS + 1)[1:].astype(float)
    return h


def g_test(obs, model):
    p = np.clip(model, 1e-9, None)
    p = p / p.sum()
    e = obs.sum() * p
    m = obs > 0
    return 2 * float((obs[m] * np.log(obs[m] / e[m])).sum())


def all_stats(c, start, sid):
    d = doublets(c, start, sid)
    r6 = relation(c, start, sid, 6, T6)
    r5 = relation(c, start, sid, 5, EQ)
    uni, bi, zmax, lagmax = flatness(c, sid)
    return {"dbl": d[0], "dbl_in": d[1], "dbl_gap": d[2],
            "l6_in": r6["in"], "l6_x": r6["x"], "l6_pos": r6["bypos"],
            "l5_in": r5["in"], "l5_x": r5["x"], "l5_pos": r5["bypos"], "S5": r5["S"],
            "uni": uni, "bi": bi, "lagz": zmax, "lag": lagmax, "hist": hist(start)}


def lp2_stats():
    c, start, sid = D.lp2()
    return all_stats(c, start, sid), (c, start, sid)


if __name__ == "__main__":
    st, _ = lp2_stats()
    for k, v in st.items():
        print(k, v)
