"""R4 repair session s04: how is R4's null "checked", and is the check visible to the anti-repeat rule?  (idea 7 of work/laptop_review/11_next_100.md)

Nothing in LP2 is solved.  Keyless simulation: LP2's ciphertext is used only for its measured statistics (section layout, doublets, word lengths);
nothing is decrypted.

Simulation code copied from work/phase57_mechanism.py (`simulate`, `tune`, `run`, `score`; read-only import of `measure`, `T`, `STATS`) with these changes only:
  null_check  'left'  the null is redrawn if it equals the previous cipher rune (phase 57 R4 `check=True`; this branch is the original code, so with
                      vis=True and the same seed the output is bit-identical to phase 57's R4: tested in `selftest`)
              'both'  additionally the null is redrawn if it equals the NEXT real cipher rune (pre-repair: plaintext rune + the key that rune will use; the key of
                      the next real rune is drawn one step ahead).  The cases the lookahead cannot know (next element is another null; the real rune is later
                      repaired to the null's value) are fixed afterwards by redrawing the earlier null in place (as work/r4fix/r4sim.py does).
              'none'  no check at all
  vis         True    the anti-repeat rule compares the next real rune with the previous cipher rune, a null included (phase 57 R4, blind=False)
              False   it compares with the last REAL rune (the phase 51 decoder's assumption; phase 57 R3 `blind`), but the T repair still looks 6 back in the
                      CIPHER word as in R4 (lag_basis 'cipher'), so only "visible" differs from R4.
  ground truth of every null position is returned (RN), for the doublet rates on null-involving pairs.
  Two extra statistics from phase 47: mean length of the word holding an in-word doublet, share of in-word doublets on a word-edge pair.

    python -B work/r4fix/s04_null_check.py selftest
    python -B work/r4fix/s04_null_check.py run <setting> [<setting> ...] [--reps 500]   -> results/r4fix/s04_null_check/raw_<setting>.json
    python -B work/r4fix/s04_null_check.py report                                       -> results/r4fix/s04_null_check/summary.txt
settings: left-visible (= phase 57 R4), left-invisible, both-visible, both-invisible, none-visible, none-invisible
"""
import argparse
import json
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "work"))
import phase57_mechanism as P57  # noqa: E402  (read-only: measure, T, STATS, simulate for the bit-identity test)
import fam_data as D  # noqa: E402
import measure as M  # noqa: E402

OUTDIR = os.path.join(ROOT, "results", "r4fix", "s04_null_check")
N, LAG = 29, 6
T = P57.T
STATS = P57.STATS
SETTINGS = ["left-visible", "left-invisible", "both-visible", "both-invisible", "none-visible", "none-invisible"]
SEED, QSEED, PSEUDO_SEED = 104, 204, {"both-invisible": 4242, "left-visible": 4343}
Q0 = 0.81
LP2_DOUBLETS = 86


def simulate(R, rng, ctx, q, rate, chk="left", vis=True):
    """copy of phase57_mechanism.simulate for rule R4 (rep='T', ins='word', slot uniform 0..L) with the null-check / visibility settings; returns C, WS, RN"""
    P, NS, WL, sid = ctx
    n = len(sid)
    both = chk == "both"
    secst = np.r_[True, sid[1:] != sid[:-1]]
    secnext = np.r_[secst[1:], True]                       # the next element is in another section (or there is none)
    J = rng.integers(0, len(P) - n - 5000, R)
    C = np.zeros((R, n), np.int16)
    WS = np.zeros((R, n), bool)
    RN = np.zeros((R, n), bool)
    off = np.zeros(R, int); L = np.zeros(R, int); slot = np.full(R, -1); w0 = np.zeros(R, int); lastins = np.zeros(R, bool); lastreal = np.full(R, -1)
    knext = rng.integers(0, N, R) if both else None
    for t in range(n):
        if secst[t]:
            J = NS[J]
            new = np.ones(R, bool)
        else:
            new = (off >= L) & (slot != off)
        if new.any():
            Ln = WL[J]
            L = np.where(new, Ln, L)
            off = np.where(new, 0, off)
            draw = new & (Ln >= 2) & (rng.random(R) < rate)
            s = rng.integers(0, Ln + 1)
            slot = np.where(new, np.where(draw, s, -1), slot)
        w0 = np.where(new, t, w0)
        pos = t - w0
        cont = not secst[t]
        prev = C[:, t - 1].astype(int) if t else np.full(R, -1)
        prevc = prev if vis else lastreal                   # invisible: the anti-repeat rule sees only real runes
        tb = T(C[:, max(t - LAG, 0)].astype(int))
        tok = pos >= LAG
        uni = (prev + 1 + rng.integers(0, N - 1, R)) % N
        unic = (prevc + 1 + rng.integers(0, N - 1, R)) % N
        insnow = slot == off
        p = P[J]
        kt = knext if both else rng.integers(0, N, R)
        x = (p + kt) % N
        coll = (x == prevc) & (rng.random(R) < q) & cont
        fix = np.where(tok & (tb != prevc), tb, unic)
        x = np.where(coll, fix, x)
        v = rng.integers(0, N, R)
        if chk in ("left", "both") and cont:
            v = np.where(v == prev, uni, v)
        if both:
            nx = (P[J] + knext) % N                         # the next real rune before any repair (J has not moved on a null)
            hasnx = not secnext[t]
            for _ in range(14):
                bad = insnow & hasnx & ((v == nx) | (cont & (v == prev)))
                if not bad.any():
                    break
                v = np.where(bad, rng.integers(0, N, R), v)
        x = np.where(insnow, v, x)
        if both and cont and t:
            # the previous element was a null equal to this element: redraw that null in place (!= this element, != its own left neighbour)
            fixp = lastins & (C[:, t - 1] == x)
            if fixp.any():
                c2 = C[:, t - 2].astype(int) if (t >= 2 and not secst[t - 1]) else np.full(R, -1)
                nv = C[:, t - 1].astype(int)
                for _ in range(14):
                    bad = fixp & ((nv == x) | (nv == c2))
                    if not bad.any():
                        break
                    nv = np.where(bad, rng.integers(0, N, R), nv)
                C[:, t - 1] = np.where(fixp, nv, C[:, t - 1])
        isn = insnow
        C[:, t] = x
        WS[:, t] = new
        RN[:, t] = isn
        J = J + ~isn
        off = off + ~isn
        slot = np.where(insnow, -1, slot)
        lastins = isn
        lastreal = np.where(isn, lastreal, x)
        if both:
            knext = np.where(~isn, rng.integers(0, N, R), knext)
    return C, WS, RN


def extra(c, ws, sid):
    """phase 47 doublet placement: mean length of the word holding an in-word doublet, share of in-word doublets on a word-edge pair"""
    n = len(c)
    i = np.arange(1, n)
    ok = sid[i] == sid[i - 1]
    inw = (c[i] == c[i - 1]) & ok & ~ws[i]
    wid = np.cumsum(ws) - 1
    first = np.flatnonzero(ws)
    Lw = np.diff(np.append(first, n))
    loc = np.arange(n) - first[wid]
    ii = i[inw]
    if len(ii) == 0:
        return dict(dwl=float("nan"), edge=float("nan"))
    wl = Lw[wid[ii]]
    edge = (loc[ii - 1] == 0) | (loc[ii] == wl - 1)
    return dict(dwl=float(wl.mean()), edge=float(edge.mean()))


def nullpairs(c, ws, sid, rn):
    """doublets / adjacent same-section pairs, split by whether the pair involves a ground-truth null.  nl = the null is the right element of the pair (the
    doublet is 'null equals its left neighbour'); nr = the null is the left element and the right element is real ('null equals its right neighbour')."""
    j = np.arange(1, len(c))
    same = sid[j] == sid[j - 1]
    d = c[j] == c[j - 1]
    inw = ~ws[j]
    inv = rn[j] | rn[j - 1]
    out = {}
    for tag, sel in (("n_in", same & inw & inv), ("m_in", same & inw & ~inv), ("n_gap", same & ~inw & inv), ("m_gap", same & ~inw & ~inv),
                     ("nl", same & rn[j]), ("nr", same & rn[j - 1] & ~rn[j])):
        out["p_" + tag] = int(sel.sum())
        out["d_" + tag] = int((sel & d).sum())
    out["nnull"] = int(rn.sum())
    return out


def meas(c, ws, sid, rn=None):
    c = c.astype(np.int16)
    m = P57.measure(c, ws, sid)
    m.update(extra(c, ws, sid))
    if rn is not None:
        m.update(nullpairs(c, ws, sid, rn))
    m["hist"] = [int(x) for x in m["hist"]]
    return m


def run(R, seed, ctx, rate, q, chk, vis, chunk=250):
    rng = np.random.default_rng(seed)
    rows = []
    for k in range(0, R, chunk):
        C, WS, RN = simulate(min(chunk, R - k), rng, ctx, q=q, rate=rate, chk=chk, vis=vis)
        rows += [meas(C[r], WS[r], ctx[3], RN[r]) for r in range(len(C))]
    return rows


def nw_of(R, seed, ctx, rate, q, chk, vis):
    rng = np.random.default_rng(seed)
    C, WS, RN = simulate(R, rng, ctx, q=q, rate=rate, chk=chk, vis=vis)
    return float(WS.sum(1).mean())


def tune(ctx, q, chk, vis, target, r0=0.4):
    """secant on the number of words (LP2 2,896): phase 57's rule (100 replicates per step, seeds 7 / 20..22, 3 steps)"""
    base = nw_of(100, 7, ctx, 0.0, q, chk, vis)
    r = r0
    for it in range(3):
        nw = nw_of(100, 20 + it, ctx, r, q, chk, vis)
        r = r * (target - base) / (nw - base)
    return float(r)


def total_doublets(R, seed, ctx, rate, q, chk, vis):
    rng = np.random.default_rng(seed)
    C, WS, RN = simulate(R, rng, ctx, q=q, rate=rate, chk=chk, vis=vis)
    sid = ctx[3]
    same = sid[1:] == sid[:-1]
    return float(((C[:, 1:] == C[:, :-1]) & same).sum(1).mean())


def fit_q(ctx, rate, chk, vis, target=LP2_DOUBLETS):
    """q (repair probability) at which the mean total doublet count equals LP2's 86: secant on 100 replicates per step, clipped to [0, 1]"""
    qs, fs = [], []
    for q in (0.81, 1.0):
        qs.append(q); fs.append(total_doublets(100, 300, ctx, rate, q, chk, vis))
    for it in range(3):
        a, b = qs[-2], qs[-1]
        fa, fb = fs[-2], fs[-1]
        qn = b - (fb - target) * (b - a) / (fb - fa) if fb != fa else b
        qn = float(min(1.0, max(0.0, qn)))
        if abs(qn - b) < 1e-3:
            break
        qs.append(qn); fs.append(total_doublets(100, 301 + it, ctx, rate, qn, chk, vis))
    best = min(range(len(qs)), key=lambda i: abs(fs[i] - target))
    return float(qs[best]), [(float(a), float(b)) for a, b in zip(qs, fs)]


def english_multi():
    """the six-book corpus of phase 57 (git-ignored work/ref/corpora is absent from this worktree: read from the main checkout, located at run time)"""
    common = subprocess.check_output(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], text=True, cwd=ROOT).strip()
    old = D.WORK
    D.WORK = os.path.join(os.path.dirname(common), "work")
    try:
        return D.english(150_000)
    finally:
        D.WORK = old


def make_ctx():
    c, ws, sid = D.lp2()
    assert len(c) == 12956
    lp = meas(c.astype(np.int16), ws, sid)
    P, ST = english_multi()
    assert len(P) == 607561, len(P)   # phase 57's six-book corpus (Emerson alone would silently give a different word-length fit and r 0.399)
    nxt = np.zeros(len(ST), int); last = len(ST) - 1
    for j in range(len(ST) - 1, -1, -1):
        last = j if ST[j] else last
        nxt[j] = last
    s = np.flatnonzero(ST)
    WL = np.zeros(len(ST), int)
    WL[s] = np.diff(np.append(s, len(ST)))
    return lp, (P.astype(np.int16), nxt, WL, sid)


def parse(setting):
    chk, vis = setting.split("-")
    return chk, vis == "visible"


def low_priority():
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)


def selftest(ctx, rate=0.448):
    """(1) left+visible is bit-identical to phase 57's R4 for the same seed; (2) at q 1 the null-involving doublet types behave as each setting says;
    (3) at rate 1 each multi-rune word gets a null (word count falls)."""
    r = {}
    for R in (6,):
        a = P57.simulate(R, np.random.default_rng(104), ctx, q=0.81, rep="T", ins="word", check=True, rate=rate)
        b = simulate(R, np.random.default_rng(104), ctx, q=0.81, rate=rate, chk="left", vis=True)
        assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1]), "left+visible differs from phase 57 R4"
        r["bit_identical_to_phase57_R4"] = True
    sid = ctx[3]
    for setting in SETTINGS:
        chk, vis = parse(setting)
        C, WS, RN = simulate(40, np.random.default_rng(3), ctx, q=1.0, rate=0.6, chk=chk, vis=vis)
        tot = dict(nl=0, nr=0, pl=0, pr=0, dm=0, pm=0)
        for k in range(len(C)):
            m = nullpairs(C[k], WS[k], sid, RN[k])
            tot["nl"] += m["d_nl"]; tot["nr"] += m["d_nr"]; tot["pl"] += m["p_nl"]; tot["pr"] += m["p_nr"]
            tot["dm"] += m["d_m_in"] + m["d_m_gap"]; tot["pm"] += m["p_m_in"] + m["p_m_gap"]
        r[setting] = tot
        if setting in ("both-visible", "both-invisible"):
            assert tot["nl"] == 0 and (tot["nr"] == 0), (setting, tot)        # 'both' leaves no doublet with a null at all (repair-to-null rare: see below)
        if chk == "left":
            assert tot["nl"] == 0, (setting, tot)
        if chk == "none":
            assert tot["nl"] > 0.5 * tot["pl"] / 29, (setting, tot)             # positive control: unchecked nulls repeat their left neighbour at 1/29
        if vis:
            assert tot["nr"] == 0 or chk == "none", (setting, tot)            # a visible null is never repeated by the next real rune, whatever the check
        else:
            assert tot["nr"] > 0.5 * tot["pr"] / 29 or chk == "both", (setting, tot)   # invisible: the next real rune repeats the null at 1/29
        assert tot["dm"] <= 0 or tot["pm"] > 0
    C0, W0, _ = simulate(6, np.random.default_rng(1), ctx, q=0.0, rate=0.0)
    C1, W1, _ = simulate(6, np.random.default_rng(1), ctx, q=0.0, rate=1.0)
    assert W1.sum() < W0.sum() * 0.85
    r["words_rate0_rate1"] = (int(W0.sum()), int(W1.sum()))
    return r


def cmd_selftest(a):
    low_priority()
    t0 = time.process_time()
    lp, ctx = make_ctx()
    print("LP2:", {k: lp[k] for k in ("din", "dgap", "dwl", "edge", "nw")}, flush=True)
    print("selftest:", selftest(ctx), f"({time.process_time() - t0:.0f} CPU s)", flush=True)


def cmd_run(a):
    low_priority()
    os.makedirs(OUTDIR, exist_ok=True)
    lp, ctx = make_ctx()
    assert selftest(ctx)["bit_identical_to_phase57_R4"]
    for setting in a.settings:
        t0 = time.process_time()
        chk, vis = parse(setting)
        rate = tune(ctx, Q0, chk, vis, lp["nw"])
        print(f"{setting}: tuned rate {rate:.4f} ({time.process_time() - t0:.0f} CPU s)", flush=True)
        rows = run(a.reps, SEED, ctx, rate, Q0, chk, vis)
        print(f"{setting}: primary run done ({time.process_time() - t0:.0f} CPU s)", flush=True)
        qfit, qlog = fit_q(ctx, rate, chk, vis)
        qrows = run(a.reps, QSEED, ctx, rate, qfit, chk, vis)
        print(f"{setting}: q fitted to 86 doublets = {qfit:.3f}, run done ({time.process_time() - t0:.0f} CPU s)", flush=True)
        out = dict(setting=setting, rate=rate, q=Q0, reps=a.reps, seed=SEED, rows=rows, qfit=qfit, qlog=qlog, qrows=qrows, lp=lp)
        if setting in PSEUDO_SEED:      # pseudo-LP2s of this setting at the primary parameters: replicate 0 = the single fixed-seed one, then 30 more
            s = PSEUDO_SEED[setting]
            out["pseudo_single"] = run(1, s, ctx, rate, Q0, chk, vis)[0]
            out["pseudo_more"] = run(30, s + 1, ctx, rate, Q0, chk, vis)
        out["cpu_s"] = time.process_time() - t0
        with open(os.path.join(OUTDIR, f"raw_{setting}.json"), "w", encoding="utf-8") as fh:
            json.dump(out, fh)
        print(f"{setting}: saved ({out['cpu_s']:.0f} CPU s)", flush=True)


EXT = STATS + ["dwl", "edge"]


def score(rows, lp, keys=STATS):
    rows = [dict(r) for r in rows]
    lp = dict(lp)
    pooled = np.sum([r["hist"] for r in rows], 0)
    for r in rows + [lp]:
        r["G"] = M.g_test(np.array(r["hist"]), pooled)
    ok = [r for r in rows if not any(np.isnan(r[k]) for k in keys)]
    X = np.array([[r[s] for s in keys] for r in ok], float)
    mu, sd = X.mean(0), X.std(0) + 1e-9
    zl = (np.array([lp[s] for s in keys]) - mu) / sd
    chi_rep = (((X - mu) / sd) ** 2).sum(1)
    chi = float((zl ** 2).sum())
    P = (1 + (chi_rep >= chi).sum()) / (len(ok) + 1)
    return dict(mu=mu, sd=sd, z=zl, chi=chi, P=float(P), n=len(ok))


def cmd_report(a):
    raws = {s: json.load(open(os.path.join(OUTDIR, f"raw_{s}.json"), encoding="utf-8")) for s in SETTINGS if os.path.exists(os.path.join(OUTDIR, f"raw_{s}.json"))}
    lp = next(iter(raws.values()))["lp"]
    out = []

    def say(s=""):
        print(s, flush=True)
        out.append(s)

    def mean(rows, k):
        return float(np.mean([r[k] for r in rows]))

    def rate(rows, d, p):
        return sum(r[d] for r in rows) / max(1, sum(r[p] for r in rows))

    say("R4 null-check / visibility settings (session s04). Keyless simulation; nothing in LP2 is solved.")
    say(f"LP2: " + " ".join(f"{k} {lp[k]:.2f}" for k in STATS if k != "G") + f" | doublet-word length {lp['dwl']:.2f}, edge-pair share {lp['edge']:.2f}, words {lp['nw']}")
    say("Setting = (null check) x (anti-repeat rule sees the null?); q 0.81, T repair, slots 0..L, 500 replicates, rate tuned to 2,896 words.")
    say("Columns: replicate mean (z of LP2 against the setting's own replicates). Combined chi2 = sum of z^2 over the nine statistics; P = share of replicates at least as far out.")

    def table(title, key, keys):
        say("")
        say(title)
        for s in SETTINGS:
            if s not in raws:
                continue
            rw = raws[s]
            rows = rw[key]
            sc = score(rows, lp, keys)
            q = rw["q"] if key == "rows" else rw["qfit"]
            say(f"{s:15s} r={rw['rate']:.3f} q={q:.3f} | " + " ".join(f"{k} {m:6.1f}({z:+5.1f})" for k, m, z in zip(keys, sc["mu"], sc["z"]))
                + f" | chi2 {sc['chi']:7.1f} P {sc['P']:.3f}")

    table("A. NINE phase-57 statistics (primary: q 0.81)", "rows", STATS)
    table("A2. the nine plus doublet-word length and edge-pair share (11 statistics; P from the 11-dimensional chi2)", "rows", EXT)
    say("")
    say("B. doublet structure at q 0.81 (replicate means; LP2: in-word 63, gap 23, doublet-word length 6.08, edge-pair share 0.48)")
    say(f"{'setting':15s} {'in-word':>8s} {'gap':>6s} {'total':>6s} {'dbl-word len':>12s} {'edge share':>10s} | rate per pair involving a null (in-word / gap) | rate per pair without a null (in-word / gap) | null==left | null==right")
    for s in SETTINGS:
        if s not in raws:
            continue
        rows = raws[s]["rows"]
        say(f"{s:15s} {mean(rows, 'din'):8.1f} {mean(rows, 'dgap'):6.1f} {mean(rows, 'din') + mean(rows, 'dgap'):6.1f} {np.nanmean([r['dwl'] for r in rows]):12.2f} "
            f"{np.nanmean([r['edge'] for r in rows]):10.2f} | {rate(rows, 'd_n_in', 'p_n_in'):.4f} / {rate(rows, 'd_n_gap', 'p_n_gap'):.4f} "
            f"| {rate(rows, 'd_m_in', 'p_m_in'):.4f} / {rate(rows, 'd_m_gap', 'p_m_gap'):.4f} | {rate(rows, 'd_nl', 'p_nl'):.4f} | {rate(rows, 'd_nr', 'p_nr'):.4f}  (nulls per replicate {mean(rows, 'nnull'):.0f})")
    say("(1/29 = 0.0345 is the rate of an unchecked pair; 0.0066 is LP2's overall doublet rate.)")
    say("")
    say("C. P-values per statistic group: share of each setting's replicates with din / dgap / dwl / edge as extreme as LP2 (two-sided, 2*min(tail))")
    for s in SETTINGS:
        if s not in raws:
            continue
        rows = raws[s]["rows"]
        bits = []
        for k in ("din", "dgap", "dwl", "edge"):
            col = np.array([r[k] for r in rows], float)
            col = col[~np.isnan(col)]
            lo = (col <= lp[k]).mean(); hi = (col >= lp[k]).mean()
            bits.append(f"{k} {min(1.0, 2 * min(lo, hi)):.3f}")
        say(f"{s:15s} " + "  ".join(bits))
    table("D. q REFITTED so that the mean total doublet count is LP2's 86 (secondary; q capped to [0, 1]; rate as in A)", "qrows", STATS)
    say("q-fit log (q, mean total doublets, 100 replicates each step): " + "; ".join(f"{s}: " + " ".join(f"({a:.2f}, {b:.1f})" for a, b in raws[s]["qlog"]) for s in SETTINGS if s in raws))
    say("")
    # positive control: left-visible vs phase 57's R4 row (published)
    if "left-visible" in raws:
        rw = raws["left-visible"]
        pub = dict(din=60.1, dgap=16.9, t6=76.6, t6x=400.0, oth=67.0, G=30.9, uni=26.4, bi=756.0, lagz=1.9)
        sc = score(rw["rows"], lp)
        sd = dict(zip(STATS, sc["sd"]))
        say(f"POSITIVE CONTROL: left+visible (seed 104, rate {rw['rate']:.4f}; phase 57's R4 tuned 0.448) against phase 57's published R4 row (500 replicates; difference in units of the replicate-mean s.e. sd/sqrt(500)):")
        say("  " + " ".join(f"{k} {m:.1f} vs {pub[k]:.1f} ({(m - pub[k]) / (sd[k] / np.sqrt(500)):+.1f})" for k, m in zip(STATS, sc["mu"])) + f" | chi2 {sc['chi']:.1f} (published 6.7) P {sc['P']:.3f} (0.643)")
        say("  the simulator is also bit-identical to work/phase57_mechanism.py `simulate` for this setting and seed (selftest assertion, 6 replicates).")
    # discrimination
    say("")
    say("DISCRIMINATION CHECK: pseudo-LP2 generated from both+invisible (seed 4242, one replicate), scored against all six settings (nine statistics / eleven)")
    if "both-invisible" in raws:
        ps = raws["both-invisible"]["pseudo_single"]
        say(f"  pseudo-LP2: din {ps['din']} dgap {ps['dgap']} t6 {ps['t6']} words {ps['nw']} dwl {ps['dwl']:.2f} edge {ps['edge']:.2f}")
        for keys, nm in ((STATS, "nine"), (EXT, "eleven")):
            res = {s: score(raws[s]["rows"], ps, keys) for s in SETTINGS if s in raws}
            say(f"  {nm}: " + " | ".join(f"{s} chi2 {res[s]['chi']:.1f} P {res[s]['P']:.3f}" for s in res)
                + f" | lowest chi2: {min(res, key=lambda s: res[s]['chi'])}; accepted (P>0.05): {[s for s in res if res[s]['P'] > 0.05]}")
        for tag in ("both-invisible", "left-visible"):
            if tag not in raws:
                continue
            ps_rows = raws[tag]["pseudo_more"]
            for keys, nm in ((STATS, "nine"), (EXT, "eleven")):
                best, acc, rej = {}, {s: 0 for s in SETTINGS}, 0
                for pr in ps_rows:
                    res = {s: score(raws[s]["rows"], pr, keys) for s in SETTINGS if s in raws}
                    b = min(res, key=lambda s: res[s]["chi"])
                    best[b] = best.get(b, 0) + 1
                    for s in res:
                        acc[s] += res[s]["P"] > 0.05
                say(f"  extra: {len(ps_rows)} pseudo-LP2 from {tag} ({nm} statistics): setting with the lowest chi2 -> {best}; times accepted (P>0.05) -> {acc}")
    say("")
    say("CPU s per setting: " + ", ".join(f"{s} {raws[s]['cpu_s']:.0f}" for s in SETTINGS if s in raws))
    with open(os.path.join(OUTDIR, "summary.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest")
    r = sub.add_parser("run")
    r.add_argument("settings", nargs="+", choices=SETTINGS)
    r.add_argument("--reps", type=int, default=500)
    sub.add_parser("report")
    a = ap.parse_args()
    {"selftest": cmd_selftest, "run": cmd_run, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
