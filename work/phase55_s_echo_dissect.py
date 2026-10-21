"""Phase 55: dissect the lag-5 S echo of LP2 (segments 7-15) against nulls, with the solved pages 0-6 as a negative control.

    python work/phase55_s_echo_dissect.py [--reps 10000]     # -> results/analysis/phase55_s_echo_dissect.txt

Nulls: W = runes shuffled inside each word (word composition kept), X = runes shuffled across a section (word lengths kept).
Per rune (29) every test gets an empirical two-sided-by-statistic p; the corrected P is the share of null draws whose
smallest per-rune p over the 29 runes (and 7 lags for the lag test) is <= the observed smallest p.
"""
import argparse
import os
import sys

import numpy as np

import lp

HERE = os.path.dirname(os.path.abspath(__file__))
N = lp.N
SEGS = lp.load_segments()
LAGS = range(2, 9)
LBINS = [2, 3, 4, 5, 6, 7, 8]  # word length bins; last = 8+ ; length 1 left out (no neighbours)
CLASS = ["first", "second", "middle", "penult", "last"]


def corpus(seg_ids):
    """flat runes, word id, position in word, word length, section id (words never span segments)"""
    r, wid, pos, ln, sec = [], [], [], [], []
    w = 0
    for s in seg_ids:
        c = lp.runes_of(SEGS[s])
        for _, a, b in lp.word_spans(SEGS[s], c):
            r += c[a:b]; wid += [w] * (b - a); pos += list(range(b - a)); ln += [b - a] * (b - a); sec += [s] * (b - a)
            w += 1
    return [np.array(x) for x in (r, wid, pos, ln, sec)]


def lagcounts(r, wid, masks):
    """[lag][rune] in-word coincidences"""
    out = np.zeros((len(masks), N), dtype=np.int32)
    for k, (g, m) in enumerate(masks.items()):
        e = (r[:-g] == r[g:]) & m
        out[k] = np.bincount(r[:-g][e], minlength=N)
    return out


def classes(pos, ln):
    c = np.where(pos == 0, 0, np.where(pos == 1, 1, np.where(pos == ln - 1, 4, np.where(pos == ln - 2, 3, 2))))
    return np.where(ln >= 5, c, -1)


def tab(r, cl, bins_arr):
    """(29 x 5 position-class counts, 29 x len-bin counts)"""
    a = np.zeros((N, 5)); b = np.zeros((N, len(LBINS)))
    ok = cl >= 0
    np.add.at(a, (r[ok], cl[ok]), 1)
    ok = bins_arr >= 0
    np.add.at(b, (r[ok], bins_arr[ok]), 1)
    return a, b


def chi2(o, mu):
    return ((o - mu) ** 2 / np.maximum(mu, 1e-9)).sum(1)


def run(name, seg_ids, reps, rng, out, sites=None):
    P = out.append
    r, wid, pos, ln, sec = corpus(seg_ids)
    n = len(r)
    masks = {g: wid[:-g] == wid[g:] for g in LAGS}
    cl = classes(pos, ln)
    lb = np.where(ln >= 2, np.minimum(ln, 8) - 2, -1)
    obs_l = lagcounts(r, wid, masks)
    obs_p, obs_b = tab(r, cl, lb)
    nw = wid.max() + 1
    P(f"== {name}: {n} runes, {nw} words, S share {100 * (r == 15).mean():.2f}% ==")
    # null draws
    nl_W = np.zeros((reps, len(LAGS), N), dtype=np.int32)
    nl_X = np.zeros_like(nl_W)
    chi_pos = np.zeros((reps, N)); chi_len = np.zeros((reps, N))
    mu_p = np.zeros((N, 5))
    ok = cl >= 0
    # expected counts analytically: position classes under W (uniform inside word), length bins under X (proportional to bin size)
    # W expected position-class counts: each rune in a word of length L>=5 lands in class k with prob size_k / L
    sz = np.stack([np.ones(n), np.ones(n), ln - 4.0, np.ones(n), np.ones(n)], 1) / ln[:, None]
    # mu for rune x = sum over words containing x of count_x(word) * class prob -> equals sum over runes of that rune of sz
    for k in range(5):
        mu_p[:, k] = np.bincount(r[ok], weights=sz[ok, k], minlength=N)
    binshare = np.bincount(lb[lb >= 0], minlength=len(LBINS)) / (lb >= 0).sum()
    tot = np.bincount(r[lb >= 0], minlength=N)
    mu_b = tot[:, None] * binshare[None, :]
    for d in range(reps):
        k = np.argsort(wid + rng.random(n))
        rw = r[k]                           # W: positions shuffled inside each word
        k = np.argsort(sec * 2.0 + rng.random(n))
        rx = r[k]                           # X: runes shuffled across the section
        nl_W[d] = lagcounts(rw, wid, masks)
        nl_X[d] = lagcounts(rx, wid, masks)
        a, _ = tab(rw, cl, lb); chi_pos[d] = chi2(a, mu_p)
        _, b = tab(rx, cl, lb); chi_len[d] = chi2(b, mu_b)
    res = {}
    for nm, nl in (("W", nl_W), ("X", nl_X)):
        # upper-tail p of count per (lag, rune), +1 smoothing
        pv = ((nl >= obs_l[None]).sum(0) + 1) / (reps + 1)
        # null min-p (leave-in) over lags x runes
        rank = np.empty_like(nl, dtype=float)
        for g_i in range(len(LAGS)):
            for x in range(N):
                col = np.sort(nl[:, g_i, x])
                rank[:, g_i, x] = (reps - np.searchsorted(col, nl[:, g_i, x], side="left")) / reps
        minp = rank.reshape(reps, -1).min(1)
        res[nm] = (pv, (minp <= pv.min()).mean())
    op = chi2(obs_p, mu_p); ol = chi2(obs_b, mu_b)
    def minp_corr(nullchi, obschi):
        ranks = np.empty_like(nullchi)
        for x in range(N):
            col = np.sort(nullchi[:, x])
            ranks[:, x] = (reps - np.searchsorted(col, nullchi[:, x], side="left")) / reps
        m = ranks.min(1)
        p = ((nullchi >= obschi[None]).sum(0) + 1) / (reps + 1)
        return p, (m <= p.min()).mean()
    pp, Ppos = minp_corr(chi_pos, op)
    pl, Plen = minp_corr(chi_len, ol)
    L5 = list(LAGS).index(5)
    for nm in ("W", "X"):
        pv, Pc = res[nm]
        P(f"-- lag test, null {nm} ({reps} draws): lag-5 coincidences S obs {obs_l[L5, 15]}, null mean {(nl_W if nm == 'W' else nl_X)[:, L5, 15].mean():.2f}, p {pv[L5, 15]:.4f}")
        P(f"   best (lag, rune) cell: lag {list(LAGS)[np.unravel_index(pv.argmin(), pv.shape)[0]]}, rune {lp.LATIN[np.unravel_index(pv.argmin(), pv.shape)[1]]}, p {pv.min():.4f};"
          f" corrected over 7 lags x 29 runes (7 x 29 = 203 cuts): P {Pc:.4f}")
        row = sorted(((pv[L5, x], lp.LATIN[x], obs_l[L5, x]) for x in range(N)))[:4]
        P("   lag 5, four smallest p over runes: " + ", ".join(f"{b}:{c} (p {a:.4f})" for a, b, c in row))
    P(f"-- word-position classes (words >= 5 runes; W null): S chi2 {op[15]:.1f} p {pp[15]:.4f}; best rune {lp.LATIN[pp.argmin()]} p {pp.min():.4f}; corrected over 29 runes P {Ppos:.4f}")
    P(f"   S counts first/second/middle/penult/last {obs_p[15].astype(int).tolist()} expected {np.round(mu_p[15], 1).tolist()}")
    P(f"-- word-length bins 2..7,8+ (X null): S chi2 {ol[15]:.1f} p {pl[15]:.4f}; best rune {lp.LATIN[pl.argmin()]} p {pl.min():.4f}; corrected over 29 runes P {Plen:.4f}")
    P(f"   S counts by length {obs_b[15].astype(int).tolist()} expected {np.round(mu_b[15], 1).tolist()}")
    # sites
    e = (r[:-5] == r[5:]) & masks[5] & (r[:-5] == 15)
    a = np.flatnonzero(e)
    P(f"-- S,S lag-5 sites: {len(a)}")
    if len(a):
        L = ln[a]; p0 = pos[a]
        P("   word length / first-S position: " + ", ".join(f"{l}/{p}" for l, p in zip(L, p0)))
        allw = ln[np.r_[0, np.flatnonzero(np.diff(wid)) + 1]]
        # windows are proportional to (L-5) among words of length >= 6
        wts = np.maximum(allw - 5, 0)
        P(f"   site-word mean length {L.mean():.2f}; expected for lag-5 windows {np.average(allw, weights=wts):.2f}; LP2 mean word length {allw.mean():.2f}")
        # neighbours: slots -1 (before first S), +1..+4 (between), +6 (after second S)
        P("   runes before/between/after (offsets -1,1,2,3,4,6 from first S):")
        for off in (-1, 1, 2, 3, 4, 6):
            vals = [lp.LATIN[r[i + off]] if 0 <= i + off < n and wid[i + off] == wid[i] else "." for i in a]
            P(f"     {off:+d}: " + " ".join(vals))
        eq = {off: sum(1 for i in a if 0 <= i + off and i + off + 5 < n and wid[i + off] == wid[i] and wid[i + off + 5] == wid[i] and r[i + off] == r[i + off + 5]) for off in (-1, 1, 2, 3, 4)}
        P(f"   lag-5 echo at neighbouring offsets (same-word pairs equal): {eq} of {len(a)} sites")
    return r, wid, a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=10000)
    args = ap.parse_args()
    rng = np.random.default_rng(55)
    out = []
    out.append("Phase 55: dissection of the lag-5 S echo. Cuts: 7 lags x 29 runes for the lag test (203), 29 runes for each of the position and length tests.")
    run("LP2 (segments 7-15)", range(7, 16), args.reps, rng, out)
    run("solved ciphertext (segments 0-6), negative control", range(0, 7), args.reps, rng, out)
    txt = "\n".join(out)
    print(txt)
    with open(os.path.join(HERE, "..", "results", "analysis", "phase55_s_echo_dissect.txt"), "w", encoding="utf-8") as f:
        f.write(txt + "\n")


if __name__ == "__main__":
    main()
