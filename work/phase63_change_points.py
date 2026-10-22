"""Phase 63: change points of LP2's doublet / lag-6 / word-length rates along the book. See work/log/phase63_change_points.md.

    python work/phase63_change_points.py [--perm 2000] [--sims 200]     # -> results/analysis/phase63_change_points.txt
"""
import argparse
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "families"))
import fam_data as D  # noqa: E402
import phase57_mechanism as PM  # noqa: E402
import stats  # noqa: E402

M = 29
OUT = []
SERIES = ["din", "dgap", "lag6", "wlen"]
GROUP_A = (0, 1, 2, 3, 4)          # section order in D.lp2(): 0.7 0.8 0.9 caption 0.11


def say(s=""):
    print(s, flush=True)
    OUT.append(s)


def page_index():
    """page of every LP2 rune (same order as D.lp2()) and the (segment, page in segment) of each page; a segment start is a page start"""
    pg, lab, k = [], [], -1
    for i in stats.UNSOLVED:
        new, pin = True, 0
        for t in stats.SEGS[i]:
            if isinstance(t, int):
                if new:
                    k += 1
                    lab.append((i, pin))
                    new = False
                pg.append(k)
            elif t == "%" and not new:
                new, pin = True, pin + 1
    return np.array(pg), lab


def measure(c, ws, sid, pg, U):
    """per-page (x, e) pairs: in-word doublets, gap doublets, lag-6 hits / expectation, word length sum / word count"""
    n = len(c)
    c = c.astype(int)
    j = np.arange(1, n)
    same = sid[j] == sid[j - 1]
    dd = c[j] == c[j - 1]
    inw, gap = same & ~ws[j], same & ws[j]

    def bc(m):
        return np.bincount(pg[j][m], minlength=U).astype(float)
    r = dict(din=(bc(inw & dd), bc(inw)), dgap=(bc(gap & dd), bc(gap)))
    wid = np.cumsum(ws) - 1
    i = np.arange(n - 6)
    ok = wid[i] == wid[i + 6]
    hit = c[i + 6] == (24 - 2 * c[i]) % M
    f = np.zeros((U, M))
    np.add.at(f, (pg, c), 1)
    f /= np.maximum(f.sum(1, keepdims=True), 1)
    pm = (f * f[:, (24 - 2 * np.arange(M)) % M]).sum(1)
    sites = np.bincount(pg[i + 6][ok], minlength=U).astype(float)
    r["lag6"] = (np.bincount(pg[i + 6][ok & hit], minlength=U).astype(float), sites * pm)
    st = np.flatnonzero(ws)
    ln = np.diff(np.append(st, n))
    r["wlen"] = (np.bincount(pg[st], weights=ln, minlength=U), np.bincount(pg[st], minlength=U).astype(float))
    return r


def ll_matrix(x, e, kind, s2=1.0):
    """LL[a, b] of the unit block a..b-1 at its own MLE (constants dropped)"""
    X, E = np.r_[0, np.cumsum(x)], np.r_[0, np.cumsum(e)]
    dX, dE = X[None, :] - X[:, None], E[None, :] - E[:, None]
    with np.errstate(divide="ignore", invalid="ignore"):
        if kind == "pois":
            ll = np.where(dX > 0, dX * np.log(dX / dE), 0.0)
        else:
            ll = np.where(dE > 0, dX * dX / dE / (2 * s2), 0.0)
    return np.where(np.isfinite(ll), ll, 0.0)


def changepoints(x, e, kind, s2=1.0):
    """(L1, t1, L2, (s, t)): 2 x LL gain of the best 1 and 2 change points over one setting; a change at t lies between unit t-1 and t"""
    U = len(x)
    L = ll_matrix(x, e, kind, s2)
    one = L[0, 1:U] + L[1:U, U]
    t1 = int(np.argmax(one)) + 1
    s, t = np.arange(1, U)[:, None], np.arange(1, U)[None, :]
    two = np.where(s < t, L[0, 1:U][:, None] + L[1:U, 1:U] + L[1:U, U][None, :], -np.inf)
    k = np.unravel_index(np.argmax(two), two.shape)
    return 2 * (one.max() - L[0, U]), t1, 2 * (two.max() - L[0, U]), (int(k[0]) + 1, int(k[1]) + 1)


def stats_of(r, s2):
    return {k: changepoints(*r[k], "norm" if k == "wlen" else "pois", s2) for k in SERIES}


def group_rates(r, pgA):
    out = {}
    for tag, m in (("A", pgA), ("B", ~pgA)):
        dx = r["din"][0][m].sum() + r["dgap"][0][m].sum()
        de = r["din"][1][m].sum() + r["dgap"][1][m].sum()
        out[tag] = (dx / de, r["lag6"][0][m].sum() / r["lag6"][1][m].sum())
    return out


def rank_p(arr, v):
    return (1 + (arr >= v).sum()) / (len(arr) + 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--perm", type=int, default=2000)
    ap.add_argument("--sims", type=int, default=200)
    a = ap.parse_args()
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    t0 = time.process_time()
    c, ws, sid = D.lp2()
    pg, lab = page_index()
    assert len(pg) == len(c), (len(pg), len(c))
    U = int(pg.max()) + 1
    assert len(lab) == U
    pgA = np.isin(sid[np.searchsorted(pg, np.arange(U))], GROUP_A)
    real = measure(c, ws, sid, pg, U)
    st = np.flatnonzero(ws)
    s2 = float(np.diff(np.append(st, len(c))).var())
    say("# Phase 63: change points of LP2's machine settings along the book (2026-10-23). Nothing in LP2 is solved.")
    say(f"{U} pages (units) in book order; word-length variance {s2:.2f}")
    say()
    say("## Per segment (LP2 observed; 10 is the caption)")
    say("segment | pages | in-word doublets / pairs | gap doublets / pairs | lag-6 hits / expected | mean word length")
    for sg in dict.fromkeys(s for s, _ in lab):
        us = [u for u in range(U) if lab[u][0] == sg]
        r = lambda k, i: real[k][i][us].sum()  # noqa: E731
        say(f"{sg:7d} | {len(us):3d} | {r('din', 0):.0f} / {r('din', 1):.0f} ({100 * r('din', 0) / max(r('din', 1), 1):.2f}%) | {r('dgap', 0):.0f} / {r('dgap', 1):.0f} | {r('lag6', 0):.0f} / {r('lag6', 1):.1f} | {r('wlen', 0) / max(r('wlen', 1), 1):.3f}")
    obs = stats_of(real, s2)
    rng = np.random.default_rng(63)
    pn = {k: [] for k in SERIES}
    for _ in range(a.perm):
        p = rng.permutation(U)
        for k, v in stats_of({k: (real[k][0][p], real[k][1][p]) for k in SERIES}, s2).items():
            pn[k].append((v[0], v[2]))
    pn = {k: np.array(v) for k, v in pn.items()}
    P, ST = D.english(150_000)
    nxt = np.zeros(len(ST), int)
    last = len(ST) - 1
    for j in range(len(ST) - 1, -1, -1):
        last = j if ST[j] else last
        nxt[j] = last
    s_ = np.flatnonzero(ST)
    WL = np.zeros(len(ST), int)
    WL[s_] = np.diff(np.append(s_, len(ST)))
    ctx = (P.astype(np.int16), nxt, WL, sid)
    kw = dict(q=0.81, rep="T", ins="word", check=True)
    rng = np.random.default_rng(630)
    sn = {k: [] for k in SERIES}
    grp = []
    for k0 in range(0, a.sims, 100):
        C, WS = PM.simulate(min(100, a.sims - k0), rng, ctx, rate=0.448, **kw)
        for q in range(len(C)):
            r = measure(C[q].astype(np.int16), WS[q], sid, pg, U)
            for k, v in stats_of(r, s2).items():
                sn[k].append((v[0], v[2]))
            grp.append(group_rates(r, pgA))
    sn = {k: np.array(v) for k, v in sn.items()}
    # positive control: q 0.83 up to 0.11, q 0.75 from 0.12 (the equivalent q of the two LP2 groups), spliced per page
    rng = np.random.default_rng(6300)
    cut = int(np.flatnonzero(~pgA)[0])
    pl = []
    for k0 in range(0, 100, 50):
        C1, W1 = PM.simulate(50, rng, ctx, rate=0.448, **dict(kw, q=0.83))
        C2, W2 = PM.simulate(50, rng, ctx, rate=0.448, **dict(kw, q=0.75))
        for q in range(50):
            r1, r2 = measure(C1[q].astype(np.int16), W1[q], sid, pg, U), measure(C2[q].astype(np.int16), W2[q], sid, pg, U)
            r = {k: (np.r_[r1[k][0][:cut], r2[k][0][cut:]], np.r_[r1[k][1][:cut], r2[k][1][cut:]]) for k in SERIES}
            v = stats_of(r, s2)["din"]
            pl.append((v[0], v[1]))
    pl = np.array(pl)
    thr = np.percentile(sn["din"][:, 0], 95)
    say(f"positive control (q 0.83 before page {cut}, 0.75 after, 100 splices): in-word doublet L1 median {np.median(pl[:, 0]):.2f}, share above the R4-null 95th percentile ({thr:.2f}): {(pl[:, 0] > thr).mean():.2f}; located at page {cut} +-3 in {(np.abs(pl[:, 1] - cut) <= 3).mean():.2f}")
    say()
    say("## Change-point statistics (2 x log-likelihood gain over one setting; change at t = between page t-1 and t; P = share of null replicates at least as large)")
    say("series | L1 (t) | P perm | P R4 | L2 (s, t) | P perm | P R4 | BIC choice (0/1/2 change points)")
    pen = 2 * np.log(U)
    for k in SERIES:
        L1, t1, L2, (s, t) = obs[k]
        bic = "0" if max(L1, L2) < pen else ("1" if L1 - pen >= L2 - 2 * pen else "2")
        say(f"{k:5s} | {L1:6.2f} ({t1}) | {rank_p(pn[k][:, 0], L1):.3f} | {rank_p(sn[k][:, 0], L1):.3f} | {L2:6.2f} ({s}, {t}) | {rank_p(pn[k][:, 1], L2):.3f} | {rank_p(sn[k][:, 1], L2):.3f} | {bic}")
    minp = lambda i, o: min(min(rank_p(pn[k][:, 0], v[0]), rank_p(pn[k][:, 1], v[1])) for k in SERIES for v in [o(k, i)])  # noqa: E731
    mp = min(min(rank_p(pn[k][:, 0], obs[k][0]), rank_p(pn[k][:, 1], obs[k][2])) for k in SERIES)
    null_min = np.array([minp(i, lambda k, i: pn[k][i]) for i in range(min(len(pn["din"]), 500))])
    say(f"smallest P over 4 series x (1, 2 change points) = {mp:.4f}; share of permutation replicates with a smaller-or-equal minimum (first 500): {(1 + (null_min <= mp).sum()) / (len(null_min) + 1):.3f}")
    say()
    say("## One R4 setting for both doublet rates? (group A = 0.7, 0.8, 0.9, caption, 0.11; group B = 0.12-0.15)")
    ra = group_rates(real, pgA)
    g = np.array([[x["A"][0], x["B"][0], x["A"][1], x["B"][1]] for x in grp])
    dd, d_obs = g[:, 1] - g[:, 0], ra["B"][0] - ra["A"][0]
    ld, l_obs = g[:, 3] - g[:, 2], ra["B"][1] - ra["A"][1]
    say(f"LP2: doublet rate A {100 * ra['A'][0]:.3f}%  B {100 * ra['B'][0]:.3f}%  (B - A = {100 * d_obs:+.3f} points); lag-6 hits / expected A {ra['A'][1]:.3f}  B {ra['B'][1]:.3f}")
    say(f"R4 (q 0.81, {len(g)} sims): doublet rate A {100 * g[:, 0].mean():.3f}% (sd {100 * g[:, 0].std():.3f})  B {100 * g[:, 1].mean():.3f}% (sd {100 * g[:, 1].std():.3f}); B - A mean {100 * dd.mean():+.3f}, sd {100 * dd.std():.3f}")
    say(f"P(|B - A - R4 mean| >= LP2's) = {(1 + (np.abs(dd - dd.mean()) >= abs(d_obs - dd.mean())).sum()) / (len(dd) + 1):.3f}; P(B - A >= LP2's) = {(1 + (dd >= d_obs).sum()) / (len(dd) + 1):.3f}")
    say(f"lag-6 ratio B - A: LP2 {l_obs:+.3f}; R4 mean {ld.mean():+.3f} sd {ld.std():.3f}; P(two-sided) = {(1 + (np.abs(ld - ld.mean()) >= abs(l_obs - ld.mean())).sum()) / (len(ld) + 1):.3f}")
    r0 = (g[:, 0].mean() + g[:, 1].mean()) / 2
    say(f"equivalent repair probability (rate ~ 1 - q, anchored at q 0.81 -> R4 mean rate {100 * r0:.3f}%): A q = {1 - 0.19 * ra['A'][0] / r0:.3f}, B q = {1 - 0.19 * ra['B'][0] / r0:.3f}")
    say(f"correlation across R4 replicates of (B - A doublet rate) with (B - A lag-6 ratio): {np.corrcoef(dd, ld)[0, 1]:+.2f}")
    say()
    say(f"CPU time {time.process_time() - t0:.0f} s")
    with open(os.path.join(HERE, "..", "results", "analysis", "phase63_change_points.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
