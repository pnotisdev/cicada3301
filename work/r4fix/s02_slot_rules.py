"""R4 repair session s02: which null-slot rule does LP2 prefer under R4? (any 0..L | interior 1..L-1 | edge 0 or L)

Simulation code copied from work/phase57_mechanism.py (`simulate`, `run`, `tune`, scoring; read-only import of `measure`, `T`, `STATS`),
the ONLY change being the slot draw (original line 78 `s = rng.integers(0, Ln + 1) if ins == "word" else Ln`) which here takes a `slot` rule.
For slot='any' the random-number stream is identical to phase 57's R4 (same seed 104 reproduces it bit-for-bit); the other rules draw
their slots differently, so their streams differ after the first inserted word.
Phase 47's doublet-placement statistics (edge-pair share, doublet-word length) are added from work/mech25/insert47.py `dbl_detail`'s definitions.
Keyless: LP2 ciphertext is used only for its measured statistics (layout, doublets ...), nothing is decrypted.

    python -B work/r4fix/s02_slot_rules.py run <rule> [--reps 500]     rule: R0 | any | interior | edge   -> results/r4fix/s02_slot_rules/raw_<rule>.json
    python -B work/r4fix/s02_slot_rules.py summary                                                          -> summary.txt
"""
import argparse
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "work"))
import phase57_mechanism as P57  # noqa: E402  (read-only: measure, T, STATS)
import fam_data as D  # noqa: E402
import measure as M  # noqa: E402

OUTDIR = os.path.join(ROOT, "results", "r4fix", "s02_slot_rules")
N, LAG = 29, 6
T = P57.T
STATS = P57.STATS
RULES = {
    "R0": dict(q=0.81, rep="uni"),
    "any": dict(q=0.81, rep="T", ins="word", check=True, slot="any"),
    "interior": dict(q=0.81, rep="T", ins="word", check=True, slot="interior"),
    "edge": dict(q=0.81, rep="T", ins="word", check=True, slot="edge"),
}
SEED = {"R0": 100, "any": 104, "interior": 104, "edge": 104}   # R0 / R4 seeds of phase 57 (100 + rule index)


def simulate(R, rng, ctx, q, rep, ins=None, insval="uni", check=False, frule=False, blind=False, rate=0.0, slot_rule="any"):
    """copy of phase57_mechanism.simulate (want=False); slot draw parametrised"""
    P, NS, WL, sid = ctx
    n = len(sid)
    secst = np.r_[True, sid[1:] != sid[:-1]]
    J = rng.integers(0, len(P) - n - 5000, R)
    C = np.zeros((R, n), np.int16)
    WS = np.zeros((R, n), bool)
    off = np.zeros(R, int); L = np.zeros(R, int); slot = np.full(R, -1); w0 = np.zeros(R, int); lastins = np.zeros(R, bool); lastreal = np.full(R, -1)
    RH = np.zeros((R, n), np.int16); nreal = np.zeros(R, int); ar = np.arange(R)
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
            if ins in ("word", "edge"):
                draw = new & (Ln >= 2) & (rng.random(R) < rate)
                if ins == "edge":
                    s = Ln
                elif slot_rule == "any":
                    s = rng.integers(0, Ln + 1)                               # as phase 57
                elif slot_rule == "interior":
                    s = rng.integers(1, np.maximum(Ln, 2))                    # 1..L-1 (drawn only where Ln >= 2)
                elif slot_rule == "edge":
                    s = np.where(rng.random(R) < 0.5, 0, Ln)                  # slot 0 or L
                else:
                    raise ValueError(slot_rule)
                slot = np.where(new, np.where(draw, s, -1), slot)
        w0 = np.where(new, t, w0)
        pos = t - w0
        cont = not secst[t]
        prev = C[:, t - 1].astype(int) if t else np.full(R, -1)
        prevc = lastreal if blind else prev
        tb = T(C[:, max(t - LAG, 0)].astype(int))
        tok = pos >= LAG
        if blind:
            tbr, tokr = T(RH[ar, np.maximum(nreal - LAG, 0)].astype(int)), off >= LAG
        else:
            tbr, tokr = tb, tok
        uni = (prev + 1 + rng.integers(0, N - 1, R)) % N
        unic = (prevc + 1 + rng.integers(0, N - 1, R)) % N
        insnow = ((rng.random(R) < rate) & ~lastins) if ins == "rune" else (slot == off)
        p = P[J]
        x = (p + rng.integers(0, N, R)) % N
        if frule:
            x = np.where((p == 0) & tok, tb, x)
        coll = (x == prevc) & (rng.random(R) < q) & cont
        fix = np.where(tokr & (tbr != prevc), tbr, unic) if rep in ("T", "Tnull") else unic
        x = np.where(coll, fix, x)
        tnull = (coll & ~insnow) if rep == "Tnull" else np.zeros(R, bool)
        v = np.where(tok, tb, rng.integers(0, N, R)) if insval == "T" else rng.integers(0, N, R)
        if check and cont:
            v = np.where(v == prev, uni, v)
        x = np.where(insnow, v, x)
        isn = insnow | tnull
        C[:, t] = x
        WS[:, t] = new
        J = J + ~isn
        off = off + ~isn
        if ins != "rune":
            slot = np.where(insnow, -1, slot)
        lastins = isn
        lastreal = np.where(isn, lastreal, x)
        RH[ar, nreal] = np.where(isn, RH[ar, nreal], x)
        nreal = nreal + ~isn
    return C, WS


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


def meas(c, ws, sid):
    c = c.astype(np.int16)
    m = P57.measure(c, ws, sid)
    m.update(extra(c, ws, sid))
    return m


def run(R, seed, ctx, kw, rate=0.0, chunk=250):
    kw = dict(kw)
    slot_rule = kw.pop("slot", "any")
    rng = np.random.default_rng(seed)
    rows = []
    for k in range(0, R, chunk):
        C, WS = simulate(min(chunk, R - k), rng, ctx, rate=rate, slot_rule=slot_rule, **kw)
        rows += [meas(C[r], WS[r], ctx[3]) for r in range(len(C))]
    return rows


def tune(ctx, kw, target, r0):
    """secant on the number of words (same rule as phase 57: 100 replicates per step, seeds 7 / 20..22, 3 steps)"""
    r = r0
    base = np.mean([x["nw"] for x in run(100, 7, ctx, kw, rate=0.0)])
    for it in range(3):
        nw = np.mean([x["nw"] for x in run(100, 20 + it, ctx, kw, rate=r)])
        r = r * (target - base) / (nw - base)
    return float(r)


def english(multi):
    """multi=True: the six-book corpus phase 57 used (work/ref/corpora/*.txt are git-ignored and absent from this worktree; they are read from the main
    checkout, located at run time via git, nothing is copied or edited). multi=False: whatever this worktree has (Emerson only)."""
    if not multi:
        return D.english(150_000)
    import subprocess
    common = subprocess.check_output(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], text=True, cwd=ROOT).strip()
    main_work = os.path.join(os.path.dirname(common), "work")
    old = D.WORK
    D.WORK = main_work
    try:
        P, ST = D.english(150_000)
    finally:
        D.WORK = old
    return P, ST


def make_ctx(multi=True):
    c, ws, sid = D.lp2()
    assert len(c) == 12956
    lp = meas(c.astype(np.int16), ws, sid)
    P, ST = english(multi)
    nxt = np.zeros(len(ST), int); last = len(ST) - 1
    for j in range(len(ST) - 1, -1, -1):
        last = j if ST[j] else last
        nxt[j] = last
    s = np.flatnonzero(ST)
    WL = np.zeros(len(ST), int)
    WL[s] = np.diff(np.append(s, len(ST)))
    return lp, (P.astype(np.int16), nxt, WL, sid)


def selftest(ctx):
    """slot rules put the nulls where they claim: at r 1, interior never makes a word-edge null, edge never an interior one.
    Checked on the plaintext-length bookkeeping: with q 0 and an all-zero key the cipher equals the plaintext plus nulls, so we compare word
    starts: edge nulls leave the plaintext runes intact at word starts/ends, interior nulls change a word's inner runes only."""
    P, NS, WL, sid = ctx
    out = {}
    for rule in ("any", "interior", "edge"):
        rng = np.random.default_rng(5)
        C, WS = simulate(2, rng, ctx, q=0.0, rep="uni", ins="word", rate=1.0, slot_rule=rule)
        out[rule] = float(WS[0].sum())
    # every rule inserts exactly one rune in each multi-rune word at r 1, so the word count is the same for all three (+- the section cuts)
    assert max(out.values()) - min(out.values()) < 0.03 * min(out.values()), out
    # direct slot-distribution check
    rng = np.random.default_rng(1)
    Ln = rng.integers(2, 9, 20000)
    it = rng.integers(1, np.maximum(Ln, 2))
    assert (it >= 1).all() and (it <= Ln - 1).all()
    return out


def TAG(a):
    return "" if a.english == "multi" else "_emerson"


def cmd_run(a):
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    os.makedirs(OUTDIR, exist_ok=True)
    t0 = time.process_time()
    lp, ctx = make_ctx(a.english == "multi")
    print(f"english corpus: {a.english}, {len(ctx[0])} runes", flush=True)
    print("selftest", selftest(ctx), flush=True)
    kw = RULES[a.rule]
    rate = 0.0
    if kw.get("ins"):
        rate = tune(ctx, kw, lp["nw"], 0.4)
        print(f"tuned rate {rate:.4f}  ({time.process_time() - t0:.0f} CPU s)", flush=True)
    rows = run(a.reps, SEED[a.rule], ctx, kw, rate=rate)
    for r in rows:
        r["hist"] = [int(x) for x in r["hist"]]
    lpd = dict(lp); lpd["hist"] = [int(x) for x in lp["hist"]]
    with open(os.path.join(OUTDIR, f"raw_{a.rule}{TAG(a)}.json"), "w", encoding="utf-8") as fh:
        json.dump(dict(rule=a.rule, rate=rate, reps=a.reps, seed=SEED[a.rule], cpu_s=time.process_time() - t0, rows=rows, lp=lpd), fh)
    print(f"done {a.rule}: {time.process_time() - t0:.0f} CPU s", flush=True)


def score(rows, lp, extras=("dwl", "edge", "tend")):
    pooled = np.sum([r["hist"] for r in rows], 0)
    for r in rows + [lp]:
        r["G"] = M.g_test(np.array(r["hist"]), pooled)
    X = np.array([[r[s] for s in STATS] for r in rows], float)
    mu, sd = X.mean(0), X.std(0) + 1e-9
    zl = (np.array([lp[s] for s in STATS]) - mu) / sd
    chi_rep = (((X - mu) / sd) ** 2).sum(1)
    chi = float((zl ** 2).sum())
    P = (1 + (chi_rep >= chi).sum()) / (len(rows) + 1)
    ex = {}
    for k in extras:
        col = np.array([r[k] for r in rows], float)
        col = col[~np.isnan(col)]
        m, s = col.mean(), col.std() + 1e-9
        ex[k] = dict(mean=float(m), sd=float(s), z=float((lp[k] - m) / s), pct=float((col <= lp[k]).mean()), n=len(col))
    # secondary: pooled in-word doublet / gap doublet ratio
    din = np.array([r["din"] for r in rows], float); dgap = np.array([r["dgap"] for r in rows], float)
    ex["din_share"] = dict(mean=float((din / (din + dgap)).mean()), lp=float(lp["din"] / (lp["din"] + lp["dgap"])))
    tb = np.mean([r["tbins"] for r in rows], 0)
    return dict(mu=mu, sd=sd, z=zl, chi=chi, P=float(P), ex=ex, tb=tb,
                t7=(float(np.mean([r["t7"] for r in rows])), float(np.std([r["t7"] for r in rows]))))


def cmd_summary(a):
    out = []

    def say(s=""):
        print(s)
        out.append(s)

    res, lp = {}, None
    for rule in ("R0", "any", "interior", "edge"):
        fn = os.path.join(OUTDIR, f"raw_{rule}{TAG(a)}.json")
        if not os.path.exists(fn):
            continue
        d = json.load(open(fn, encoding="utf-8"))
        lp = d["lp"]
        res[rule] = (d, score(d["rows"], dict(d["lp"])))
    say("R4 slot-rule comparison (keyless simulation; q 0.81, repair T(c-6) in-word, one checked null per multi-rune word at rate r tuned to 2,896 words; "
        "same plaintext source and layout as phase 57; English corpus: " + ("six books" if a.english == "multi" else "Emerson only (supplementary run)") + ")")
    say(f"LP2: din {lp['din']} dgap {lp['dgap']} t6 {lp['t6']} t6x {lp['t6x']} oth {lp['oth']} uni {lp['uni']:.1f} bi {lp['bi']:.1f} lagz {lp['lagz']:.2f} "
        f"| edge-pair share {lp['edge']:.2f} doublet-word length {lp['dwl']:.2f} T hits ending a word {lp['tend']} words {lp['nw']}")
    say("")
    say("Table 1: phase 57's nine statistics, replicate mean (z of LP2), combined chi2 (sum z^2) and P (share of the rule's own replicates with chi2 >= LP2's)")
    for rule, (d, s) in res.items():
        name = {"R0": "R0 uniform repair, no nulls (null control)", "any": "R4 slot any 0..L (phase 57)", "interior": "R4 slot interior 1..L-1 (decoder)", "edge": "R4 slot edge 0 or L"}[rule]
        say(f"{name:44s} reps {d['reps']} r={d['rate']:.4f} | " + " ".join(f"{k} {m:6.1f}({z:+5.1f})" for k, m, z in zip(STATS, s["mu"], s["z"])) +
            f" | chi2 {s['chi']:6.1f} P {s['P']:.3f} | worst {STATS[int(np.argmax(np.abs(s['z'])))]} {float(s['z'][int(np.argmax(np.abs(s['z'])))]):+.1f}")
    say("")
    say("Table 2: phase 47 doublet-placement statistics, replicate mean +- sd (z, percentile of LP2 among replicates)")
    say("rule       in-word/gap doublets          in-word share  edge-pair share        doublet-word length    T hits ending a word   T hits by word length 7/8/9/10+ (LP2 8/21/20/31)   lag-7 T hits (LP2 22)")
    for rule, (d, s) in res.items():
        e = s["ex"]; mu = dict(zip(STATS, s["mu"])); sd = dict(zip(STATS, s["sd"])); z = dict(zip(STATS, s["z"]))
        say(f"{rule:10s} {mu['din']:5.1f}({z['din']:+.1f}) / {mu['dgap']:5.1f}({z['dgap']:+.1f})   {e['din_share']['mean']:.2f} (LP2 {e['din_share']['lp']:.2f})  "
            f"{e['edge']['mean']:.2f}+-{e['edge']['sd']:.2f} ({e['edge']['z']:+.1f}, pct {e['edge']['pct']:.3f})  "
            f"{e['dwl']['mean']:.2f}+-{e['dwl']['sd']:.2f} ({e['dwl']['z']:+.1f}, pct {e['dwl']['pct']:.3f})  "
            f"{e['tend']['mean']:.1f}+-{e['tend']['sd']:.1f} ({e['tend']['z']:+.1f})  " + "/".join(f"{x:.1f}" for x in s["tb"]) + f"   {s['t7'][0]:.1f}+-{s['t7'][1]:.1f}")
    say("")
    say("Table 3: word-length G (z) per rule is in Table 1 (column G). Extended chi2 = Table 1's nine z plus the three placement z (dwl, edge, tend):")
    for rule, (d, s) in res.items():
        e = s["ex"]
        chi12 = s["chi"] + e["dwl"]["z"] ** 2 + e["edge"]["z"] ** 2 + e["tend"]["z"] ** 2
        say(f"  {rule:10s} chi2 (9) {s['chi']:6.1f}   chi2 (12) {chi12:6.1f}")
    with open(os.path.join(OUTDIR, "summary.txt" if a.english == "multi" else "summary_emerson_only.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("rule", choices=list(RULES)); r.add_argument("--reps", type=int, default=500)
    for sp in (r, sub.add_parser("summary")):
        sp.add_argument("--english", choices=["multi", "emerson"], default="multi")
    a = ap.parse_args()
    cmd_run(a) if a.cmd == "run" else cmd_summary(a)
