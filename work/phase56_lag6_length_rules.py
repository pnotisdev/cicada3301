"""Phase 56: which simple word-level rule gives the lag-6 length profile (absent at 7 letters, ~2x at 8-9)? See work/log/phase56_lag6_length_rules.md.

    python work/phase56_lag6_length_rules.py [--reps 1000]    # -> results/analysis/phase56_lag6_length_rules.txt

English plaintext (digraph runes, LP2's section layout), random flat key c = p + k, repeat-repair with probability Q = 0.81 (as phase 25), then one rule per run:
  M0 baseline repair = uniform other rune; no echo (null reference)
  M1 phase 25 repair: a repaired collision at word position >= 6 writes T(c[-6]) = 24 - 2 c[-6]   (rate fixed by Q, not tuned)
  A  halves: second block of 6 (word positions 6-11) writes T(c[-6]) with rate r_a (independent of collisions, replaces the plaintext rune)
  B  key restart: in a fraction f of words k_i = k_(i-6) for positions >= 6 (gives EQUAL runes at lag 6, not T; shown as a control that it cannot give the relation)
  D  insertion gate: at word positions >= 7 an extra rune T(c[-6]) is inserted at rate r_d (no plaintext consumed): a lag-6 pair needs destination position >= 7 AND the word grows
A, D are tuned (secant on 80 total in-word hits). Score per rule: chi2 of the 4 length-bin hit counts + the 2 doublet rates against the rule's own replicate spread,
Poisson log-likelihood of LP2's bin counts under the rule's mean, G of the word-length histogram.
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

N, Q, LAG = 29, 0.81, 6
BINS = [(7, 7), (8, 8), (9, 9), (10, 99)]
OUT = []


def say(s=""):
    print(s, flush=True)
    OUT.append(s)


def simulate(rule, R, rng, P, ST, NS, sid, rate=0.0, f=0.5):
    n = len(sid)
    secst = np.r_[True, sid[1:] != sid[:-1]]
    off = rng.integers(0, len(P) - n - 3000, R)
    J = off.copy()
    C = np.zeros((R, n), np.int16); K = np.zeros((R, n), np.int16); WS = np.zeros((R, n), bool)
    w0 = np.zeros(R, int)
    bflag = rng.random(R) < f
    ar = np.arange(R)
    for t in range(n):
        if secst[t]:
            J = NS[J]
        new = ST[J]
        w0 = np.where(new, t, w0)
        pos = t - w0
        back = max(t - LAG, 0)
        k = rng.integers(0, N, R)
        if rule == "B":
            k = np.where(bflag & (pos >= LAG), K[:, back], k)
        x = (P[J] + k) % N
        ins = np.zeros(R, bool)
        if t and not secst[t]:
            prev = C[:, t - 1]
            coll = (x == prev) & (rng.random(R) < Q)
            uni = (prev + 1 + rng.integers(0, N - 1, R)) % N
            tb = (24 - 2 * C[:, back].astype(int)) % N
            x = np.where(coll, uni, x)
            if rule == "M1":
                x = np.where(coll & (pos >= LAG), tb, x)
            elif rule == "A":
                x = np.where((pos // LAG == 1) & (rng.random(R) < rate), tb, x)
            elif rule == "D":
                ins = (pos >= LAG + 1) & ~new & (rng.random(R) < rate)
                x = np.where(ins, tb, x)
        C[:, t] = x; K[:, t] = k; WS[:, t] = new & ~ins
        J = J + (~ins)
    return C, WS


def measure(c, ws, sid):
    """per-bin T hits / pairs, in-word and gap doublet rates, word-length histogram for one text"""
    n = len(c)
    s = np.flatnonzero(ws)
    L = np.diff(np.append(s, n))
    wid = np.cumsum(ws) - 1
    wl = L[wid]
    i = np.arange(n - LAG)
    ok = wid[i] == wid[i + LAG]
    i = i[ok]
    hit = c[i + LAG] == (24 - 2 * c[i].astype(int)) % N
    eq = c[i + LAG] == c[i]
    hb, pb = [], []
    for lo, hi in BINS:
        m = (wl[i] >= lo) & (wl[i] <= hi)
        hb.append(int(hit[m].sum())); pb.append(int(m.sum()))
    j = np.arange(1, n)
    same = sid[j] == sid[j - 1]
    d = c[j] == c[j - 1]
    inw = same & ~ws[j]
    gap = same & ws[j]
    return dict(hb=np.array(hb), pb=np.array(pb), eq=int(eq.sum()), din=d[inw].mean(), dgap=d[gap].mean(), hist=M.hist(ws))


def run(rule, R, seed, ctx, rate=0.0, f=0.5, chunk=250):
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(0, R, chunk):
        C, WS = simulate(rule, min(chunk, R), rng, *ctx, rate=rate, f=f)
        rows += [measure(C[r].astype(int), WS[r], ctx[3]) for r in range(len(C))]
    return rows


def summ(rows, lp, tag):
    H = np.array([r["hb"] for r in rows], float)
    mu, sd = H.mean(0), H.std(0) + 1e-9
    din = np.array([r["din"] for r in rows]); dgap = np.array([r["dgap"] for r in rows])
    G = np.array([M.g_test(lp["hist"], r["hist"]) for r in rows])
    zs = lambda h, d1, d2: np.r_[(h - mu) / sd, (d1 - din.mean()) / din.std(), (d2 - dgap.mean()) / dgap.std()]
    chi_lp = float((zs(lp["hb"], lp["din"], lp["dgap"]) ** 2).sum())
    chi_rep = np.array([(zs(H[r], din[r], dgap[r]) ** 2).sum() for r in range(len(rows))])
    p = (1 + (chi_rep >= chi_lp).sum()) / (len(rows) + 1)
    ll = float(sum(o * np.log(max(m, 1e-9)) - m for o, m in zip(lp["hb"], mu)))
    say(f"{tag:22s} hits/bin " + " ".join(f"{m:5.1f}" for m in mu) + f" | total {mu.sum():5.1f} | dbl in {100 * din.mean():.2f}% gap {100 * dgap.mean():.2f}% | eq6 {np.mean([r['eq'] for r in rows]):5.1f} "
        f"| chi2(6) {chi_lp:6.1f} P {p:.3f} | logL {ll:7.2f} | G(wordlen) {G.mean():6.1f}")
    return mu.sum(), chi_lp, p, ll


def main():
    if sys.platform == "win32":                       # below-normal priority
        import ctypes
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=1000)
    reps = ap.parse_args().reps
    c, ws, sid = D.lp2()
    assert len(c) == 12956
    lp = measure(c.astype(int), ws, sid)
    P, ST = D.english(150_000)
    nxt = np.zeros(len(ST), int); last = len(ST) - 1
    for j in range(len(ST) - 1, -1, -1):
        last = j if ST[j] else last
        nxt[j] = last
    ctx = (P.astype(np.int16), ST, nxt, sid)
    say(f"LP2: T hits per word-length bin {BINS}: {lp['hb'].tolist()} of pairs {lp['pb'].tolist()}  (total {lp['hb'].sum()}); equal-at-lag-6 {lp['eq']}; "
        f"doublets in-word {100 * lp['din']:.2f}% gap {100 * lp['dgap']:.2f}%")
    say(f"{reps} replicates per rule (English, flat random key, Q {Q}); columns: mean T hits per bin 7 | 8 | 9 | 10+")
    summ(run("M0", reps, 1, ctx), lp, "M0 no echo")
    summ(run("M1", reps, 2, ctx), lp, "M1 phase-25 repair")
    for rule in ("A", "D"):                           # tune rate: secant on the total, 100 reps
        r = {"A": 0.03, "D": 0.03}[rule]
        base = np.mean([x["hb"].sum() for x in run("M0", 150, 9, ctx)])   # null total
        for it in range(3):
            tot = np.mean([x["hb"].sum() for x in run(rule, 150, 10 + it, ctx, rate=r)])
            r = r * max(lp["hb"].sum() - base, 5) / max(tot - base, 1)
        say(f"tuned {rule}: rate {r:.4f}")
        summ(run(rule, reps, 3 if rule == "A" else 4, ctx, rate=r), lp, f"{rule} {'halves' if rule == 'A' else 'insert gate'} r={r:.3f}")
    summ(run("B", reps, 5, ctx, f=0.5), lp, "B key restart f=0.5")
    with open(os.path.join(HERE, "..", "results", "analysis", "phase56_lag6_length_rules.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
