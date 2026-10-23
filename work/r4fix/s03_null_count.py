"""s03 (R4 repair): does LP2 prefer a mixture with some two-null words?  Keyless simulation only, no LP2 decryption.

    python -B work/r4fix/s03_null_count.py [--reps 500] [--workers 2]   # -> results/r4fix/s03_null_count/summary.txt

The simulator is phase 57's R4 (work/phase57_mechanism.py: q 0.81, T repair, checked null) with ONE change: a multi-rune word
carries 0, 1 or 2 nulls with probabilities (1 - r1 - r2, r1, r2).  rate = r1 + r2 (share of multi-rune words with any null),
f2 = r2 / (r1 + r2).  Each null has its own slot, drawn independently and uniformly (slots 'any' = 0..L, 'interior' = 1..L-1);
two nulls on the same slot are adjacent.  Every null is checked against the rune on its left (re-drawn if equal), exactly as
phase 57's `check=True`.  For each f2 the rate is tuned (phase 57's secant rule, 3 steps of 100 replicates) so the mean word
count equals LP2's 2,896.  Measurement, the nine statistics, z, combined chi2 and P are phase 57's own functions, imported
read-only (`phase57_mechanism.measure`, `.STATS`); the simulator below is a copy of `phase57_mechanism.simulate` (attribution:
phase 57) with the null-slot logic generalised to two slots.  work/r4fix/r4sim.py was not used (a per-word python simulator,
about 100x slower for 500 replicates x 14 settings).
"""
import argparse
import os
import pickle
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "work"))
sys.path.insert(0, os.path.join(ROOT, "work", "families"))
sys.path.insert(0, os.path.join(ROOT, "work", "mech25"))
import phase57_mechanism as P57  # noqa: E402  (read-only import; main() is guarded)
import fam_data as D  # noqa: E402
import measure as M  # noqa: E402

N, LAG = 29, 6
T = P57.T
STATS = P57.STATS
F2_GRID = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30]
F2_EXTRA = [0.50]          # extra points beyond the brief's grid, for the upper bound of the accepted range
OUTDIR = os.path.join(ROOT, "results", "r4fix", "s03_null_count")
Q = 0.81
CTX = None


def build_ctx():
    c, ws, sid = D.lp2()
    assert len(c) == 12956
    P, ST = D.english(150_000)
    nxt = np.zeros(len(ST), int); last = len(ST) - 1
    for j in range(len(ST) - 1, -1, -1):
        last = j if ST[j] else last
        nxt[j] = last
    s = np.flatnonzero(ST)
    WL = np.zeros(len(ST), int)
    WL[s] = np.diff(np.append(s, len(ST)))
    return (P.astype(np.int16), nxt, WL, sid), (c, ws, sid)


def simulate(R, rng, ctx, rate, f2, slots="any", q=Q, want_null=False):
    """phase 57 `simulate` with R4's settings (rep='T', ins='word', check=True, blind=False) and 0/1/2 nulls per multi-rune word."""
    P, NS, WL, sid = ctx
    n = len(sid)
    secst = np.r_[True, sid[1:] != sid[:-1]]
    J = rng.integers(0, len(P) - n - 5000, R)
    C = np.zeros((R, n), np.int16)
    WS = np.zeros((R, n), bool)
    IS = np.zeros((R, n), bool)
    off = np.zeros(R, int); L = np.zeros(R, int); w0 = np.zeros(R, int)
    s1 = np.full(R, -1); s2 = np.full(R, -1)
    lo = 0 if slots == "any" else 1
    for t in range(n):
        if secst[t]:
            J = NS[J]
            new = np.ones(R, bool)
        else:
            new = (off >= L) & (s1 != off) & (s2 != off)
        if new.any():
            Ln = WL[J]
            L = np.where(new, Ln, L)
            off = np.where(new, 0, off)
            draw = new & (Ln >= 2) & (rng.random(R) < rate)
            two = draw & (rng.random(R) < f2)
            hi = Ln + 1 if slots == "any" else Ln          # slot s in lo..hi-1
            a = rng.integers(lo, np.maximum(hi, lo + 1))
            b = rng.integers(lo, np.maximum(hi, lo + 1))
            s1 = np.where(new, np.where(draw, a, -1), s1)
            s2 = np.where(new, np.where(two, b, -1), s2)
        w0 = np.where(new, t, w0)
        cont = not secst[t]
        prev = C[:, t - 1].astype(int) if t else np.full(R, -1)
        tb = T(C[:, max(t - LAG, 0)].astype(int))
        pos = t - w0
        tok = pos >= LAG
        uni = (prev + 1 + rng.integers(0, N - 1, R)) % N
        insnow = (s1 == off) | (s2 == off)
        p = P[J]
        x = (p + rng.integers(0, N, R)) % N
        coll = (x == prev) & (rng.random(R) < q) & cont
        fix = np.where(tok & (tb != prev), tb, uni)
        x = np.where(coll, fix, x)
        v = rng.integers(0, N, R)
        if cont:
            v = np.where(v == prev, uni, v)
        x = np.where(insnow, v, x)
        C[:, t] = x
        WS[:, t] = new
        IS[:, t] = insnow
        J = J + ~insnow
        off = off + ~insnow
        # clear exactly one used slot (slots are compared with the OLD off; off did not move because insnow keeps it)
        c1 = insnow & (s1 == off)
        c2 = insnow & ~c1 & (s2 == off)
        s1 = np.where(c1, -1, s1)
        s2 = np.where(c2, -1, s2)
    return (C, WS, IS) if want_null else (C, WS)


def extra_stats(row, ws_hist):
    h = ws_hist
    nw = h.sum()
    row["share2"] = float(h[1] / nw)
    row["share3"] = float(h[2] / nw)
    return row


def run(R, seed, ctx, rate, f2, slots, chunk=250):
    rng = np.random.default_rng(seed)
    rows = []
    for k in range(0, R, chunk):
        C, WS = simulate(min(chunk, R - k), rng, ctx, rate, f2, slots)
        for r in range(len(C)):
            m = P57.measure(C[r].astype(np.int16), WS[r], ctx[3])
            rows.append(extra_stats(m, m["hist"]))
    return rows


def tune(ctx, f2, slots, target, r0, base):
    r = r0
    for it in range(3):
        nw = np.mean([x["nw"] for x in run(100, 20 + it, ctx, r, f2, slots)])
        r = r * (target - base) / (nw - base)
    return float(r)


def selftest(ctx):
    """planted controls on the structure: q 0, rate 1: exactly k nulls in every multi-rune word (k 1 for f2 0, 2 for f2 1);
    no section/word is lost; rate 0 gives no nulls; interior slots never put a null at a word edge."""
    for slots in ("any", "interior"):
        for f2, k in ((0.0, 1), (1.0, 2)):
            C, WS, IS = simulate(2, np.random.default_rng(3), ctx, 1.0, f2, slots, q=0.0, want_null=True)
            for r in range(2):
                wid = np.cumsum(WS[r]) - 1
                nn = np.bincount(wid, weights=IS[r].astype(float))
                ln = np.bincount(wid)
                real = ln - nn
                sidr = ctx[3]
                secend = np.flatnonzero(np.r_[sidr[1:] != sidr[:-1], True])
                cut = np.zeros(len(ln), bool); cut[wid[secend]] = True     # words cut by a section end are incomplete
                multi = (real >= 2) & ~cut
                assert (nn[multi] == k).all(), (slots, f2, np.bincount(nn[multi].astype(int)))
                assert (nn[(real < 2) & ~cut] == 0).all()
                if slots == "interior":
                    st = np.flatnonzero(WS[r])
                    assert not IS[r][st].any()                        # no null at slot 0 of any word
                    en = (np.r_[st[1:], len(wid)] - 1)[~cut]
                    assert not IS[r][en].any()                        # none at the last cipher rune (slot L)
    C, WS, IS = simulate(2, np.random.default_rng(4), ctx, 0.0, 0.5, "any", want_null=True)
    assert IS.sum() == 0
    # f2 = 0 vs f2 = 1 at the same rate: more nulls per word, fewer words
    a = simulate(3, np.random.default_rng(5), ctx, 0.4, 0.0)[1].sum()
    b = simulate(3, np.random.default_rng(5), ctx, 0.4, 1.0)[1].sum()
    assert b < a, (a, b)
    # share of two-null words among null words at f2 = 0.3 (any slot): about 0.3
    C, WS, IS = simulate(20, np.random.default_rng(6), ctx, 0.5, 0.3, "any", want_null=True)
    cnt = np.zeros(3)
    for r in range(20):
        wid = np.cumsum(WS[r]) - 1
        nn = np.bincount(wid, weights=IS[r].astype(float)).astype(int)
        cnt += np.bincount(nn, minlength=3)[:3]
    assert abs(cnt[2] / (cnt[1] + cnt[2]) - 0.3) < 0.03, cnt


def task(arg):
    kind, f2, slots, reps, seed, rate0 = arg
    global CTX
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    if CTX is None:
        CTX = build_ctx()
    ctx, (c, ws, sid) = CTX
    t0 = time.process_time()
    if kind == "p57r4":                                   # phase 57's own R4 simulator and tuned rate, as the null control
        kw = dict(q=0.81, rep="T", ins="word", check=True)
        rate = rate0
        rows = P57.run(reps, 104, ctx, kw, rate=rate)
        for m in rows:
            extra_stats(m, m["hist"])
        return dict(kind=kind, f2=f2, slots=slots, rate=rate, rows=rows, cpu=time.process_time() - t0)
    base = np.mean([x["nw"] for x in run(100, 7, ctx, 0.0, 0.0, slots)])
    rate = tune(ctx, f2, slots, 2896, 0.45 / (1 + f2), base)
    rows = run(reps, seed, ctx, rate, f2, slots)
    return dict(kind=kind, f2=f2, slots=slots, rate=rate, rows=rows, cpu=time.process_time() - t0)


def zscores(rows, lp):
    """phase 57 `score`, for one 'LP2' dict: z of each statistic, combined chi2, P, word-length G (pooled histogram of the rows)"""
    pooled = np.sum([r["hist"] for r in rows], 0)
    lp = dict(lp)
    lp["G"] = M.g_test(lp["hist"], pooled)
    for r in rows:
        r["G"] = M.g_test(r["hist"], pooled)
    X = np.array([[r[s] for s in STATS] for r in rows], float)
    mu, sd = X.mean(0), X.std(0) + 1e-9
    zl = (np.array([lp[s] for s in STATS]) - mu) / sd
    chi_rep = (((X - mu) / sd) ** 2).sum(1)
    chi = float((zl ** 2).sum())
    P = (1 + (chi_rep >= chi).sum()) / (len(rows) + 1)
    return dict(mu=mu, sd=sd, z=zl, chi=chi, P=P, G=lp["G"])


def main():
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=500)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--npseudo", type=int, default=20)
    a = ap.parse_args()
    os.makedirs(OUTDIR, exist_ok=True)
    out = []

    def say(s=""):
        print(s, flush=True)
        out.append(s)

    ctx, (c, ws, sid) = build_ctx()
    t0 = time.process_time()
    selftest(ctx)
    say(f"selftest passed ({time.process_time() - t0:.0f} CPU s)")
    lp = P57.measure(c.astype(np.int16), ws, sid)
    extra_stats(lp, lp["hist"])
    say("LP2: " + " ".join(f"{k} {lp[k]:.1f}" for k in STATS if k != "G") + f" dju {lp['dju']} words {lp['nw']}; share of 2-rune words {lp['share2']:.4f}, 3-rune {lp['share3']:.4f}")
    cache = os.path.join(OUTDIR, "rows.pkl")
    if os.path.exists(cache) and os.environ.get("S03_REUSE"):
        res = pickle.load(open(cache, "rb"))
    else:
        tasks = [("p57r4", 0.0, "any", a.reps, 0, 0.448)]
        i = 0
        for slots in ("any", "interior"):
            for f2 in F2_GRID + (F2_EXTRA if slots == "any" else []):
                tasks.append(("sim", f2, slots, a.reps, 1000 + i, 0))
                i += 1
        with Pool(a.workers) as pool:
            res = pool.map(task, tasks, chunksize=1)
        pickle.dump(res, open(cache, "wb"))
    cpu = sum(r["cpu"] for r in res)
    say(f"{a.reps} replicates per setting, q {Q}, T repair, checked null; worker CPU {cpu / 60:.1f} min for the grid")
    say("Columns: statistic mean (z of LP2 against the setting's own replicates); chi2/P over the nine statistics (phase 57 definitions)")

    def line(r, sc, tag):
        rows = r["rows"]
        nw = np.mean([x["nw"] for x in rows])
        s2 = np.mean([x["share2"] for x in rows]); s3 = np.mean([x["share3"] for x in rows])
        say(f"{tag:22s} rate {r['rate']:.3f} nw {nw:6.1f} | " + " ".join(f"{s} {m:6.1f}({z:+5.1f})" for s, m, z in zip(STATS, sc["mu"], sc["z"]))
            + f" | chi2 {sc['chi']:6.1f} P {sc['P']:.3f} | G(LP2) {sc['G']:.1f} zG {sc['z'][STATS.index('G')]:+.1f} | 2-rune {100 * s2:.2f}% 3-rune {100 * s3:.2f}%")
        return nw

    table = {}
    say(f"\nLP2 word shares: 2-rune {100 * lp['share2']:.2f}%, 3-rune {100 * lp['share3']:.2f}%")
    for slots in ("any", "interior"):
        say(f"\n== slots {slots} ==")
        for r in res:
            if r["kind"] != "sim" or r["slots"] != slots:
                continue
            sc = zscores(r["rows"], lp)
            table[(slots, r["f2"])] = (r, sc)
            line(r, sc, f"{slots} f2 {r['f2']:.2f}")
        say("  accepted (P > 0.05): " + ", ".join(f"{f:.2f}" for (s, f), (r, sc) in sorted(table.items()) if s == slots and sc["P"] > 0.05))
        say("  chi2 by f2: " + ", ".join(f"{f:.2f}: {sc['chi']:.1f}" for (s, f), (r, sc) in sorted(table.items()) if s == slots))

    # null control: phase 57's own R4 vs f2 = 0 (any slots)
    say("\n== null control: f2 = 0 against phase 57's own R4 simulator (same rate 0.448, 500 replicates, seed of phase 57) ==")
    r57 = [r for r in res if r["kind"] == "p57r4"][0]
    sc57 = zscores(r57["rows"], lp)
    line(r57, sc57, "phase57 R4 (own code)")
    r0, sc0 = table[("any", 0.0)]
    X57 = np.array([[x[s] for s in STATS[:5] + STATS[6:]] for x in r57["rows"]], float)
    X0 = np.array([[x[s] for s in STATS[:5] + STATS[6:]] for x in r0["rows"]], float)
    d = (X0.mean(0) - X57.mean(0)) / np.sqrt(X0.var(0) / len(X0) + X57.var(0) / len(X57))
    say("  difference of means / MC s.e. (G excluded): " + " ".join(f"{s} {v:+.1f}" for s, v in zip(STATS[:5] + STATS[6:], d))
        + f"; nw {np.mean([x['nw'] for x in r0['rows']]):.1f} vs {np.mean([x['nw'] for x in r57['rows']]):.1f}; G of the replicates (own pooled): {np.mean([x['G'] for x in r0['rows']]):.1f} vs {np.mean([x['G'] for x in r57['rows']]):.1f}")
    say(f"  phase 57 log, R4 row: rate 0.448, chi2 6.7 P 0.643, z din +0.4 dgap +1.5 t6 +0.3 oth -0.3 G +0.2 lagz +1.9; here (own code): chi2 {sc57['chi']:.1f} P {sc57['P']:.3f}; f2 = 0: chi2 {sc0['chi']:.1f} P {sc0['P']:.3f}")

    # positive controls: pseudo-LP2 generated at a true f2, fitted against every grid setting (slots any)
    say("\n== recovery control: pseudo-LP2 from the simulator (any slots, the setting's tuned rate), fitted against the f2 grid (any slots) ==")
    grid = sorted(f for (s, f) in table if s == "any")
    rec = {}
    for true in (0.15, 0.0):
        r, _ = table[("any", true)]
        rng = np.random.default_rng({0.15: 31337, 0.0: 4242}[true])
        C, WS = simulate(max(a.npseudo, 1), rng, ctx, r["rate"], true, "any")
        ps = []
        for k in range(len(C)):
            m = P57.measure(C[k].astype(np.int16), WS[k], ctx[3])
            ps.append(extra_stats(m, m["hist"]))
        rec[true] = ps
        for tag, pl in (("primary (seed fixed, replicate 0)", ps[:1]), (f"all {len(ps)} pseudo replicates", ps)):
            say(f"  true f2 {true:.2f}, {tag}: ")
            Ps, chis, bests, accs = [], [], [], []
            for k, p in enumerate(pl):
                row = [zscores(table[("any", f)][0]["rows"], p) for f in grid]
                Pv = np.array([x["P"] for x in row]); ch = np.array([x["chi"] for x in row])
                acc = [f for f, x in zip(grid, row) if x["P"] > 0.05]
                Ps.append(Pv); chis.append(ch); bests.append(grid[int(np.argmin(ch))]); accs.append(acc)
                if len(pl) == 1:
                    say(f"    pseudo nw {p['nw']}, din {p['din']}, dgap {p['dgap']}, t6 {p['t6']}, share2 {100 * p['share2']:.2f}%; fit rows (f2: chi2 / P / zG): "
                        + "; ".join(f"{f:.2f}: {x['chi']:.1f}/{x['P']:.3f}/{x['z'][STATS.index('G')]:+.1f}" for f, x in zip(grid, row)))
                    say(f"    best f2 (min chi2) {bests[-1]:.2f}; accepted (P > 0.05): {acc}; true value accepted: {true in acc}")
            if len(pl) > 1:
                bests = np.array(bests)
                say(f"    best f2 (min chi2): mean {bests.mean():.3f}, median {np.median(bests):.2f}, histogram " + str({f: int((bests == f).sum()) for f in grid}))
                say(f"    true value accepted (P > 0.05) in {sum(true in x for x in accs)} of {len(pl)}; mean P by grid f2: " + ", ".join(f"{f:.2f}: {np.mean([p[i] for p in Ps]):.2f}" for i, f in enumerate(grid)))
                lowacc = np.array([min(x) if x else np.nan for x in accs]); hiacc = np.array([max(x) if x else np.nan for x in accs])
                say(f"    accepted range per pseudo replicate: lowest accepted median {np.nanmedian(lowacc):.2f}, highest accepted median {np.nanmedian(hiacc):.2f}; "
                    f"f2 = 0 rejected in {sum(0.0 not in x for x in accs)}, f2 = 0.30 rejected in {sum(0.30 not in x for x in accs)}, f2 = 0.50 rejected in {sum(0.50 not in x for x in accs)}")
                # word-length statistic alone: z of G
                zg = np.array([[zscores(table[('any', f)][0]['rows'], p)['z'][STATS.index('G')] for f in grid] for p in pl])
                say("    zG of the pseudo against each grid f2 (mean over pseudo replicates): " + ", ".join(f"{f:.2f}: {zg[:, i].mean():+.2f}" for i, f in enumerate(grid)))

    # can G alone distinguish f2?  mean of the replicate G (each against its setting's pooled histogram is ~ chi2 df) and its separation
    say("\n== can the word-length statistic distinguish f2?  mean word-length histogram per setting (any slots), as % of words, bins 1..11, 12+ ==")
    for f in grid:
        r, _ = table[("any", f)]
        h = np.mean([x["hist"] for x in r["rows"]], 0)
        say(f"  f2 {f:.2f}: " + " ".join(f"{100 * v / h.sum():5.2f}" for v in h) + f"   (LP2: " + " ".join(f"{100 * v / lp['hist'].sum():5.2f}" for v in lp["hist"]) + ")" if f == grid[0] else
            f"  f2 {f:.2f}: " + " ".join(f"{100 * v / h.sum():5.2f}" for v in h))
    base = np.mean([x["hist"] for x in table[("any", 0.0)][0]["rows"]], 0); base = base / base.sum()
    sdG = {}
    for f in grid:
        r, _ = table[("any", f)]
        # G of each setting's mean histogram (as 2,896 words) against f2 = 0's, versus the sampling spread of a single replicate's G
        h = np.mean([x["hist"] for x in r["rows"]], 0)
        sdG[f] = M.g_test(h, base)
    say("  G of the setting's mean histogram (about 2,896 words) against the f2 = 0 histogram: " + ", ".join(f"{f:.2f}: {g:.1f}" for f, g in sdG.items())
        + f"   (a single replicate's G against its own pooled histogram: mean {np.mean([x['G'] for x in table[('any', 0.0)][0]['rows']]):.1f}, sd {np.std([x['G'] for x in table[('any', 0.0)][0]['rows']]):.1f}, df 10)")

    with open(os.path.join(OUTDIR, "summary.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
