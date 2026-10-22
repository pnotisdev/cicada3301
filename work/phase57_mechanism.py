"""Phase 57: which simple encryption rule reproduces ALL of LP2's anomalies at once? See work/log/phase57_mechanism.md.

    python work/phase57_mechanism.py [--reps 500]     # -> results/analysis/phase57_mechanism.txt

English plaintext (digraph runes, `fam_data.english`), LP2's section layout (12,956 runes), flat random key c = p + k. One simulator, nine rules (R0-R8, table RULES):
  q      probability that a would-be doublet (c == previous c, same section) is repaired
  rep    'uni' repair = uniform other rune | 'T' repair writes T(c[-6]) = 24 - 2 c[-6] when the rune 6 back is in the same word (else uniform)
         | 'Tnull' the repair rune is a NULL (plaintext not consumed, re-encrypted with the next key)
  ins    extra null runes: 'word' one per word (words of >= 2 plaintext runes) with probability r at a uniform slot 0..L | 'edge' same, slot L (check rune at the end)
         | 'rune' before any plaintext rune with probability r (a key-value event, e.g. an inverted F-skip)
  insval value of the inserted null: 'uni' or 'T' (T(c[-6]) when 6 back is in the word, else uniform);  check: the null is re-drawn if it equals the previous rune
  blind  the nulls are added in a later pass: the anti-repeat check compares with the last REAL rune (phase 47 / 51 semantics); else with the previous rune
  frule  plaintext F at word position >= 6 is written as T(c[-6]) (LP1's special F, inverted)
Insertion rates are tuned (secant) so the number of words matches LP2's 2,896; everything else is fixed. Score: 9 statistics (doublets in-word / gap, lag-6 T hits in-word / across gaps,
best other affine lag-6 form, word-length G, unigram chi2, bigram chi2, max |z| equality at lags 2-12), z against each rule's own replicates, combined chi2, P = share of replicates
with a combined chi2 >= LP2's. Reported, not scored: T hits by word length, per section, at lag 7 and ending a word; repeated adjacent word pairs (DJU BEI type).
"""
import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "families"))
sys.path.insert(0, os.path.join(HERE, "mech25"))
import fam_data as D  # noqa: E402
import measure as M  # noqa: E402

N, LAG = 29, 6
OUT = []
STATS = ["din", "dgap", "t6", "t6x", "oth", "G", "uni", "bi", "lagz"]
RULES = [
    ("R0 uniform repair (reference)", dict(q=0.81, rep="uni")),
    ("R1 repair writes T(c-6)", dict(q=0.81, rep="T")),
    ("R2 collision -> null T(c-6)", dict(q=0.81, rep="Tnull")),
    ("R3 q1 T-repair + word null", dict(q=1.0, rep="T", ins="word", blind=True)),
    ("R4 T-repair + checked word null", dict(q=0.81, rep="T", ins="word", check=True)),
    ("R5 q1 + word null = T(c-6)", dict(q=1.0, rep="uni", ins="word", insval="T", blind=True)),
    ("R6 T-repair + per-rune null", dict(q=0.81, rep="T", ins="rune", check=True)),
    ("R7 T-repair + end check rune", dict(q=0.81, rep="T", ins="edge", check=True)),
    ("R8 plaintext F -> T(c-6)", dict(q=0.81, rep="uni", frule=True)),
]


def say(s=""):
    print(s, flush=True)
    OUT.append(s)


def T(x):
    return (24 - 2 * x) % N


def simulate(R, rng, ctx, q, rep, ins=None, insval="uni", check=False, frule=False, blind=False, rate=0.0, want=False):
    P, NS, WL, sid = ctx
    n = len(sid)
    secst = np.r_[True, sid[1:] != sid[:-1]]
    J = rng.integers(0, len(P) - n - 5000, R)
    C = np.zeros((R, n), np.int16)
    WS = np.zeros((R, n), bool)
    off = np.zeros(R, int); L = np.zeros(R, int); slot = np.full(R, -1); w0 = np.zeros(R, int); lastins = np.zeros(R, bool); lastreal = np.full(R, -1)
    RH = np.zeros((R, n), np.int16); nreal = np.zeros(R, int); ar = np.arange(R)
    RT = np.zeros((R, n), bool); RA = np.zeros((R, n), bool)   # want=True: T-valued / all repairs (phase 61)
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
                s = rng.integers(0, Ln + 1) if ins == "word" else Ln
                slot = np.where(new, np.where(draw, s, -1), slot)
        w0 = np.where(new, t, w0)
        pos = t - w0
        cont = not secst[t]
        prev = C[:, t - 1].astype(int) if t else np.full(R, -1)
        prevc = lastreal if blind else prev           # blind: nulls added in a later pass, the anti-repeat check sees only real runes
        tb = T(C[:, max(t - LAG, 0)].astype(int))
        tok = pos >= LAG
        if blind:                                     # the repair looks 6 back in the REAL stream (nulls come later)
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
        RA[:, t] = coll & ~insnow
        RT[:, t] = coll & ~insnow & tokr & (tbr != prevc)
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
    return (C, WS, RT, RA) if want else (C, WS)


def measure(c, ws, sid):
    n = len(c)
    wid = np.cumsum(ws) - 1
    j = np.arange(1, n)
    same = sid[j] == sid[j - 1]
    d = c[j] == c[j - 1]
    i = np.arange(n - LAG)
    s6 = sid[i] == sid[i + LAG]
    inw = wid[i] == wid[i + LAG]
    a, b = c[i][inw], c[i + LAG][inw]
    oth = 0
    for m in range(1, N):
        h = np.bincount((b - m * a) % N, minlength=N)
        if m == N - 2:
            h[24] = 0                                   # the T form itself
        oth = max(oth, int(h.max()))
    f = np.bincount(c, minlength=N)
    e = n / N
    B = np.bincount(c[j - 1][same] * N + c[j][same], minlength=N * N).reshape(N, N)
    pr = f / n
    E = np.outer(pr, pr) * same.sum()
    offd = ~np.eye(N, dtype=bool)                       # doublets are scored separately
    E = E[offd] / E[offd].sum() * B[offd].sum()
    S2 = float((pr * pr).sum())
    lagz = 0.0
    for lg in range(2, 13):
        k = np.arange(lg, n)
        ok = sid[k] == sid[k - lg]
        h = (c[k] == c[k - lg])[ok].sum()
        lagz = max(lagz, abs((h - ok.sum() * S2) / np.sqrt(ok.sum() * S2 * (1 - S2))))
    wl = np.diff(np.append(np.flatnonzero(ws), n))[wid[i][inw]]
    th = b == T(a)
    tb = [int(th[(wl >= lo) & (wl <= hi)].sum()) for lo, hi in ((7, 7), (8, 8), (9, 9), (10, 99))]
    hs = np.bincount(sid[i][inw][th], minlength=sid.max() + 1).astype(float); ns = np.bincount(sid[i][inw], minlength=sid.max() + 1).astype(float)
    ex = ns * hs.sum() / ns.sum()
    tsec = float(((hs - ex)[ns > 0] ** 2 / ex[ns > 0]).sum())   # section heterogeneity of the T hits (phase 54: LP2 28.8)
    lastw = np.r_[ws[1:], True]
    tend = int((th & lastw[i + LAG][inw]).sum())                 # T hits ending on the word's last rune (phase 54: LP2 32 vs 20.1); an end check rune cannot be one
    i7 = np.arange(n - 7)
    w7 = wid[i7] == wid[i7 + 7]
    t7 = int((c[i7 + 7][w7] == T(c[i7][w7])).sum())             # R3 prediction: T pairs that straddle a later-pass null sit at lag 7
    # repeated adjacent word pairs (combined length >= 5), as DJU BEI
    st = np.flatnonzero(ws)
    words = [c[s:e2].tobytes() for s, e2 in zip(st, np.append(st[1:], n))]
    seen, rep = {}, 0
    for w1, w2, s1, s2 in zip(words, words[1:], st, st[1:]):
        if sid[s1] == sid[s2] and len(w1) + len(w2) >= 10:     # int16 runes: 10 bytes = 5 runes
            key = (w1, w2)
            seen[key] = seen.get(key, 0) + 1
            rep += seen[key] == 2
    return dict(din=int((d & same & ~ws[j]).sum()), dgap=int((d & same & ws[j]).sum()), t6=int((b == T(a)).sum()),
                t6x=int(((c[i + LAG] == T(c[i])) & s6 & ~inw).sum()), oth=oth, uni=float(((f - e) ** 2 / e).sum()),
                bi=float(((B[offd] - E) ** 2 / E).sum()), lagz=lagz, dju=rep, tbins=tb, t7=t7, tend=tend, tsec=tsec, nw=int(ws.sum()), hist=M.hist(ws))


def run(R, seed, ctx, kw, rate=0.0, chunk=250):
    rng = np.random.default_rng(seed)
    rows = []
    for k in range(0, R, chunk):
        C, WS = simulate(min(chunk, R - k), rng, ctx, rate=rate, **kw)
        rows += [measure(C[r].astype(np.int16), WS[r], ctx[3]) for r in range(len(C))]
    return rows


def score(rows, lp, tag, rate):
    pooled = np.sum([r["hist"] for r in rows], 0)
    for r in rows + [lp]:
        r["G"] = M.g_test(r["hist"], pooled)
    X = np.array([[r[s] for s in STATS] for r in rows], float)
    mu, sd = X.mean(0), X.std(0) + 1e-9
    zl = (np.array([lp[s] for s in STATS]) - mu) / sd
    chi_rep = (((X - mu) / sd) ** 2).sum(1)
    chi = float((zl ** 2).sum())
    P = (1 + (chi_rep >= chi).sum()) / (len(rows) + 1)
    pct = [(X[:, k] < lp[s]).mean() + 0.5 * (X[:, k] == lp[s]).mean() for k, s in enumerate(STATS)]
    dj = np.array([r["dju"] for r in rows])
    say(f"{tag:34s} r={rate:.3f} | " + " ".join(f"{s} {m:6.1f}({z:+5.1f})" for s, m, z in zip(STATS, mu, zl))
        + f" | chi2 {chi:7.1f} P {P:.3f} | worst {STATS[int(np.argmax(np.abs(zl)))]} | P(dju>=1) {np.mean(dj >= lp['dju']):.3f}")
    tb = np.mean([r["tbins"] for r in rows], 0); ts = np.array([r["tsec"] for r in rows])
    say(f"{'':34s} unscored: T hits by word length 7/8/9/10+ " + "/".join(f"{x:.1f}" for x in tb) + f" (LP2 {'/'.join(map(str, lp['tbins']))}); "
        f"section chi2 of T hits {ts.mean():.1f} (LP2 {lp['tsec']:.1f}, P {np.mean(ts >= lp['tsec']):.3f}); "
        f"lag-7 T hits {np.mean([r['t7'] for r in rows]):.1f} +- {np.std([r['t7'] for r in rows]):.1f} (LP2 {lp['t7']}); "
        f"T hits ending a word {np.mean([r['tend'] for r in rows]):.1f} +- {np.std([r['tend'] for r in rows]):.1f} (LP2 {lp['tend']})")
    return dict(tag=tag, rate=rate, mu=mu, z=zl, chi=chi, P=P, pct=pct, dju=float(np.mean(dj >= lp["dju"])))


def tune(ctx, kw, target, r0):
    """secant on the number of words (LP2 2,896), 100 replicates per step"""
    r = r0
    base = np.mean([x["nw"] for x in run(100, 7, ctx, kw, rate=0.0)])
    for it in range(3):
        nw = np.mean([x["nw"] for x in run(100, 20 + it, ctx, kw, rate=r)])
        r = r * (target - base) / (nw - base)
    return float(r)


def selftest(ctx):
    """planted controls: q 1 / no insertion gives no in-word doublets; rule R1 with q 1 lifts T hits; word nulls at r 1 add one rune to every multi-rune word"""
    rng = np.random.default_rng(0)
    C, WS = simulate(4, rng, ctx, q=1.0, rep="uni")
    m = measure(C[0].astype(np.int16), WS[0], ctx[3])
    assert m["din"] + m["dgap"] == 0, m
    C, WS = simulate(4, rng, ctx, q=1.0, rep="T")
    assert measure(C[0].astype(np.int16), WS[0], ctx[3])["t6"] > 60
    C0, W0 = simulate(4, np.random.default_rng(1), ctx, q=0.0, rep="uni")
    C1, W1 = simulate(4, np.random.default_rng(1), ctx, q=0.0, rep="uni", ins="word", rate=1.0)
    assert W1.sum() < W0.sum() * 0.85                  # longer words -> fewer words in the same runes


def main():
    if sys.platform == "win32":                       # below-normal priority
        import ctypes
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=500)
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    c, ws, sid = D.lp2()
    assert len(c) == 12956
    lp = measure(c.astype(np.int16), ws, sid)
    P, ST = D.english(150_000)
    nxt = np.zeros(len(ST), int); last = len(ST) - 1
    for j in range(len(ST) - 1, -1, -1):
        last = j if ST[j] else last
        nxt[j] = last
    s = np.flatnonzero(ST)
    WL = np.zeros(len(ST), int)
    WL[s] = np.diff(np.append(s, len(ST)))
    ctx = (P.astype(np.int16), nxt, WL, sid)
    selftest(ctx)
    say("LP2: " + " ".join(f"{k} {lp[k]:.1f}" for k in STATS if k != "G") + f" dju {lp['dju']} words {lp['nw']}")
    say(f"{a.reps} replicates per rule; columns: rule mean (z of LP2 against the rule's replicates)")
    res = []
    for ix, (tag, kw) in enumerate(RULES):
        if a.only and not tag.startswith(a.only):
            continue
        rate = 0.0
        if kw.get("ins"):
            rate = tune(ctx, kw, lp["nw"], 0.08 if kw["ins"] == "rune" else 0.4)
        res.append(score(run(a.reps, 100 + ix, ctx, kw, rate=rate), lp, tag, rate))
    say("\nranked by combined chi2 (9 statistics; P = share of the rule's own replicates at least as far from its mean):")
    for r in sorted(res, key=lambda r: r["chi"]):
        say(f"  {r['tag']:34s} chi2 {r['chi']:7.1f}  P {r['P']:.3f}  |z|>2: " + ", ".join(f"{s} {z:+.1f}" for s, z in zip(STATS, r["z"]) if abs(z) > 2))
    if not a.only:
        with open(os.path.join(HERE, "..", "results", "analysis", "phase57_mechanism.txt"), "w", newline="\n", encoding="utf-8") as fh:
            fh.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
