"""Phase 47: do inserted runes (the '+1 rune in ~42% of words' fit) explain LP2's doublets, and where do they sit? One core, mech25 style.

Plaintext: English rune words (fam_data.english, digraph spelling), LP2's section layout, c_i = p_i + k_i with k iid uniform (key consumes plaintext runes only).
Step 1 (anti-repeat, on the plaintext-length stream): a would-be repeat c_i = c_(i-1) (adjacent in the section, gaps included) is repaired with prob q
        (to a uniform other rune; 'echo' variants: to 24 - 2 c_(i-6) when the rune 6 back is in the same word).
Step 2 (insertion, after step 1, no key used): in a multi-rune word, with prob pins(L) one uniform rune is inserted at slot j of 0..L ('any': uniform over the
        L+1 slots, word edges included; 'edge': slot 0 or L). Sections are cut to LP2's length.
  A  q=0.81, no insertion (the repo's current model)      B  q=1, pins=0.42, any slot      C  q=1, pins=0.42, edge slots only
  D  q=1, pins(L) = clip(a + b (L-2), 0, 1) fitted to LP2's word-length histogram, any slot      F  as D with the slope forced so the doublet-word length is 6.08 (the reviewer's repair; a refitted by G)
  E (extra)  q=1, pins(L) = c (L-1)... (fitted), any slot
  +6 suffix: the same with the echo repair (A6 = q 0.81)

    python work/mech25/insert47.py [--reps 300]   -> results/analysis/insert47.txt
"""
import argparse
import os
import sys

import numpy as np
from scipy.optimize import minimize
from scipy.stats import chi2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "families"))
import fam_data as D  # noqa: E402
import measure as M  # noqa: E402

N = 29
BINS = 12


def lens_of(start):
    s = np.flatnonzero(start)
    return np.diff(np.append(s, len(start)))


def dbl_detail(c, start, sid):
    """(n_in, n_gap, lengths of the word holding each in-word doublet, edge flags, relative positions)"""
    i = np.arange(1, len(c))
    ok = sid[i] == sid[i - 1]
    eq = (c[i] == c[i - 1]) & ok
    inw = eq & ~start[i]
    gap = eq & start[i]
    wid = np.cumsum(start) - 1
    L = lens_of(start)
    first = np.flatnonzero(start)
    loc = np.arange(len(c)) - first[wid]
    ii = i[inw]
    wl = L[wid[ii]]
    edge = (loc[ii - 1] == 0) | (loc[ii] == wl - 1)
    rel = (loc[ii - 1] + 0.5) / (wl - 1)   # pair midpoint over the span of pair slots, 0..1
    return int(inw.sum()), int(gap.sum()), wl, edge, rel


def pins_fn(kind, par):
    if kind == "const":
        return lambda L: np.where(L >= 2, par[0], 0.0)
    if kind == "lin":
        return lambda L: np.where(L >= 2, np.clip(par[0] + par[1] * (L - 2), 0, 1), 0.0)
    if kind == "prop":
        return lambda L: np.where(L >= 2, np.clip(par[0] * (L - 1), 0, 1), 0.0)
    return lambda L: np.zeros(len(L))


def shifted(base, pins):
    """expected length histogram (bins 1..12+) of words of English histogram `base` (by length 1..12+) after +1 with prob pins(L)"""
    Ls = np.arange(1, BINS + 1)
    p = np.asarray(pins(Ls), float)
    q = base * (1 - p)
    q[1:] += base[:-1] * p[:-1]
    q[-1] += base[-1] * p[-1]
    return q / q.sum()


def gtest(obs, p):
    p = np.clip(p, 1e-12, None); p = p / p.sum()
    e = obs.sum() * p
    m = obs > 0
    return 2 * float((obs[m] * np.log(obs[m] / e[m])).sum())


def encrypt(P, st, sid, rng, q, echo, pins, mode):
    out_c, out_s = [], []
    pos = 0
    for k in np.unique(sid):
        n = int((sid == k).sum())
        p = P[pos:pos + n]; s = st[pos:pos + n].copy(); s[0] = True
        pos += n
        key = rng.integers(N, size=n); u = rng.random(n); alt = rng.integers(1, N, size=n)
        c = np.empty(n, int)
        w0 = 0
        for j in range(n):
            if s[j]:
                w0 = j
            x = (p[j] + key[j]) % N
            if j and x == c[j - 1] and u[j] < q:
                x = (24 - 2 * c[j - 6]) % N if (echo and j - 6 >= w0) else (c[j - 1] + alt[j]) % N
                if x == c[j - 1]:
                    x = (c[j - 1] + alt[j]) % N
            c[j] = x
        # step 2: insertion
        first = np.flatnonzero(s); Lw = np.diff(np.append(first, n))
        ins = rng.random(len(Lw)) < pins(Lw)
        slot = rng.integers(0, Lw + 1) if mode == "any" else np.where(rng.random(len(Lw)) < 0.5, 0, Lw)
        vals = rng.integers(N, size=len(Lw))
        cc, ss = [], []
        for w in range(len(Lw)):
            seg = list(c[first[w]:first[w] + Lw[w]])
            sg = [False] * Lw[w]; sg[0] = True
            if ins[w]:
                seg.insert(slot[w], int(vals[w])); sg = [True] + [False] * Lw[w]
            cc += seg; ss += sg
        out_c += cc[:n]; out_s += ss[:n]
        if len(cc) < n:
            raise RuntimeError("too short")
    return np.array(out_c), np.array(out_s, bool)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=300)
    ap.add_argument("--tag", default="")
    ap.add_argument("--models", default="A,B,C,D,E,F,A6,B6,C6")
    args = ap.parse_args()
    out = []

    def say(x=""):
        print(x, flush=True); out.append(x)

    c0, s0, sid = D.lp2()
    n = len(c0)
    obs = M.hist(s0)
    L2 = lens_of(s0)
    nin, ngap, wl, edge, rel = dbl_detail(c0, s0, sid)
    r6 = M.relation(c0, s0, sid, 6, M.T6)["in"]; r5 = M.relation(c0, s0, sid, 5, M.EQ)["in"]
    say(f"LP2: {n} runes, {len(L2)} words (mean {L2.mean():.2f}); doublets {nin + ngap} = in-word {nin} + across-gap {ngap}; mean length of the word holding an in-word doublet "
        f"{wl.mean():.2f} (n {len(wl)}, s.e. {wl.std(ddof=1) / np.sqrt(len(wl)):.2f}); share of in-word doublets at a word edge pair {edge.mean():.2f} ({edge.sum()}/{len(edge)}); "
        f"lag6 in-word z {r6[3]:+.2f}, lag5 z {r5[3]:+.2f}")

    P0, st0 = D.english(150_000)
    eh = M.hist(st0); eh = eh / eh.sum()
    # --- reviewer's numbers
    Ls = L2
    say("\n## Reviewer's numbers, reproduced")
    say(f"words x 0.42 x 2/29 = {len(L2)} x 0.42 x 2/29 = {len(L2) * .42 * 2 / 29:.1f} (reviewer: 2,813 words -> 81; LP2's word count by this repo's segmentation is {len(L2)}).")
    say(f"mean LP2 word length weighted by adjacent pairs, sum L(L-1)/sum(L-1) = {(Ls * (Ls - 1)).sum() / (Ls - 1).sum():.2f} (reviewer 6.02).")
    # expected doublet-word length under B: weight = number of unchecked in-word neighbours of the inserted rune, on LP2-like (post-insertion) lengths
    base = eh
    pB = pins_fn("const", [0.42])
    Lg = np.arange(1, BINS + 1)
    pb = np.asarray(pB(Lg), float)
    # inserted-word of final length L+1: in-word neighbours = 2 for L-1 mid slots of (L+1), 1 for the two edge slots: mean (2(L-1)+2)/(L+1)
    w = base * pb * (2 * Lg) / (Lg + 1)   # in-word-neighbour weight
    mean_final = (w * (Lg + 1)).sum() / w.sum()
    say(f"analytic B: doublet-holding word's final length, weighting inserted words by in-word neighbour count 2L/(L+1): {mean_final:.2f}; "
        f"unweighted mean final length of inserted words {((base * pb) * (Lg + 1)).sum() / (base * pb).sum():.2f} (reviewer 5.45 likely one of these; 'edge' slots excluded would be lower). "
        f"Final in-word share of B doublets analytic: {(w.sum()) / (base * pb * 2).sum():.2f} (LP2 {nin / (nin + ngap):.2f}).")

    # --- fits to LP2 hist (analytic, English hist eh)
    G = lambda p: gtest(obs, p)
    r = minimize(lambda x: G(shifted(eh, pins_fn("const", x))), [0.4], method="Nelder-Mead")
    say(f"\n## Word-length fits to LP2 (English histogram from the simulation corpus, G on LP2's {int(obs.sum())} words, 12 bins)")
    say(f"A (no insertion): G {G(eh):.1f} (df 11); B constant: fitted r {r.x[0]:.3f}, G {r.fun:.1f} (df 10); at r = 0.42: G {G(shifted(eh, pB)):.1f}")
    best = None
    for st_ in ([0.2, 0.02], [0.1, 0.05], [0.3, -0.01], [0.0, 0.08]):
        f = minimize(lambda x: G(shifted(eh, pins_fn("lin", x))), st_, method="Nelder-Mead")
        if best is None or f.fun < best.fun:
            best = f
    say(f"D linear a + b (L-2): a {best.x[0]:.3f}, b {best.x[1]:+.4f}, G {best.fun:.1f} (df 9); pins at L=2..8: " + " ".join(f"{float(pins_fn('lin', best.x)(np.array([L]))[0]):.2f}" for L in range(2, 9)))
    e = minimize(lambda x: G(shifted(eh, pins_fn("prop", x))), [0.05], method="Nelder-Mead")
    say(f"E proportional c (L-1): c {e.x[0]:.4f}, G {e.fun:.1f} (df 10); pins at L=2..8: " + " ".join(f"{float(pins_fn('prop', e.x)(np.array([L]))[0]):.2f}" for L in range(2, 9)))
    # slope scan: refit a for each slope b; analytic mean final length of the doublet-holding word (weight 2L/(L+1), any slot)
    say("slope scan, pins(L) = a + b (L-2), a refitted by G: b, a, G, analytic doublet-word length (LP2 6.08, A-like 6.0, B 5.4)")
    Lg1 = np.arange(1, BINS + 1)
    scan = []
    for b_ in (-0.01, 0.0, 0.01, 0.02, 0.03, 0.04, 0.06, 0.08, 0.10):
        f = minimize(lambda x: G(shifted(eh, pins_fn("lin", [x[0], b_]))), [0.3], method="Nelder-Mead")
        pv = np.asarray(pins_fn("lin", [f.x[0], b_])(Lg1), float)
        ww = eh * pv * (2 * Lg1) / (Lg1 + 1)
        scan.append((b_, f.x[0], f.fun, (ww * (Lg1 + 1)).sum() / ww.sum()))
        say(f"  b {b_:+.2f}  a {f.x[0]:.3f}  G {f.fun:6.1f}  doublet-word len {scan[-1][3]:.2f}")
    sel = min(scan, key=lambda r: abs(r[3] - 6.08))
    # Emerson-only English as in work/wordlen.py (the repo's G 16.5)
    import wordlen as W
    ew = [len(__import__("lp").word_to_key(w.replace("IO", "IA"))) for w in W.emerson_words()]
    eh_em = np.array(M.hist(np.concatenate([[True] + [False] * (x - 1) for x in ew if x]).astype(bool)), float); eh_em /= eh_em.sum()
    fe = minimize(lambda x: gtest(obs, shifted(eh_em, pins_fn("const", x))), [0.4], method="Nelder-Mead")
    say(f"check, Emerson-only English (work/wordlen.py): A G {gtest(obs, eh_em):.1f}; B fitted r {fe.x[0]:.3f} G {fe.fun:.1f} (repo: 16.5 at 42%). The multi-book English of the simulation fits worse (G {r.fun:.1f}): corpus floor, not the model.")
    # constrained: what pins(L) makes the doublet-word length 6.08? one-parameter family slope b with a refit by G is already D; report D's expectation below by simulation
    mods = {"A": (0.81, False, ("none", []), "any"), "B": (1.0, False, ("const", [0.42]), "any"), "C": (1.0, False, ("const", [0.42]), "edge"),
            "D": (1.0, False, ("lin", best.x), "any"), "E": (1.0, False, ("prop", e.x), "any"), "F": (1.0, False, ("lin", [sel[1], sel[0]]), "any"),
            "C90": (0.90, False, ("const", [0.42]), "edge"), "C95": (0.95, False, ("const", [0.42]), "edge"), "B90": (0.90, False, ("const", [0.42]), "any"),
            "A6": (0.81, True, ("none", []), "any"), "B6": (1.0, True, ("const", [0.42]), "any"), "C6": (1.0, True, ("const", [0.42]), "edge")}
    fitted = {"A": 0, "B": 1, "C": 1, "D": 2, "E": 1, "F": 1, "C90": 1, "C95": 1, "B90": 1, "A6": 0, "B6": 1, "C6": 1}
    rng = np.random.default_rng(4747)
    sec_rows = {}
    hdr = "model  dbl tot [95%]       in-word [95%]     gap [95%]        in-share   doublet-word len [95%]  edge-pair share [95%]  lag6 z [95%]   lag5 z    mean word len   G(LP2|pooled) df p"
    say("\n## Simulation (reps per model: %d)" % args.reps)
    say(hdr)
    res = {}
    for name in args.models.split(","):
        q, echo, (kind, par), mode = mods[name]
        pins = pins_fn(kind, par)
        rows, H = [], np.zeros(BINS)
        for _ in range(args.reps):
            a = int(rng.integers(0, len(P0) - n - 3000))
            a += int(np.flatnonzero(st0[a:])[0])
            c, s = encrypt(P0[a:a + n + 2000], st0[a:a + n + 2000], sid, rng, q, echo, pins, mode)
            ni, ng, w_, ed, rl = dbl_detail(c, s, sid)
            rr = M.relation(c, s, sid, 6, M.T6)["in"][3]; r5_ = M.relation(c, s, sid, 5, M.EQ)["in"][3]
            h = M.hist(s); H += h
            rows.append((ni + ng, ni, ng, ni / max(ni + ng, 1), w_.mean() if len(w_) else np.nan, ed.mean() if len(ed) else np.nan, rr, r5_, n / s.sum(), ni, w_, ed))
        R = np.array([x[:9] for x in rows], float)
        res[name] = (R, rows)
        def iv(j, f="{:.0f}"):
            col = R[:, j]; col = col[~np.isnan(col)]
            return (f + " [" + f + "," + f + "]").format(col.mean(), *np.percentile(col, [2.5, 97.5]))
        g = gtest(obs, H)
        df = 11 - fitted[name]
        say(f"{name:4s} {iv(0):18s} {iv(1):17s} {iv(2):15s} {R[:, 3].mean():.2f}      {iv(4, '{:.2f}'):22s}  {iv(5, '{:.2f}'):20s}  {iv(6, '{:+.1f}'):14s} {R[:, 7].mean():+.1f}    {R[:, 8].mean():.2f}            {g:6.1f} {df:2d} {chi2.sf(g, df):.2g}")
    say(f"LP2  {nin + ngap:<18d} {nin:<17d} {ngap:<15d} {nin / (nin + ngap):.2f}      {wl.mean():.2f}                    {edge.mean():.2f}                  {r6[3]:+.1f}           {r5[3]:+.1f}    {n / len(L2):.2f}")

    say("\n## Per-statistic position of LP2 inside each model's replicate distribution (fraction of reps <= LP2; 2.5%-97.5% is 'inside'), and joint check")
    say("model  dbl tot   in-word   gap   in-share   doublet-word len   edge share   lag6 z  | inside all 4 of (in-word, gap, word len, edge)  | joint Mahalanobis p (in-word, gap, word len)")
    obsv = {1: nin, 2: ngap, 4: wl.mean(), 5: edge.mean(), 0: nin + ngap, 3: nin / (nin + ngap), 6: r6[3]}
    for name, (R, rows) in res.items():
        pct = []
        for j in (0, 1, 2, 3, 4, 5, 6):
            col = R[:, j]; col = col[~np.isnan(col)]
            pct.append((col <= obsv[j]).mean())
        ins4 = all(0.025 <= pct[j] <= 0.975 for j in (1, 2, 4, 5))
        X = R[:, [1, 2, 4]]; X = X[~np.isnan(X).any(1)]
        mu = X.mean(0); C = np.cov(X.T) + 1e-9 * np.eye(3); Ci = np.linalg.inv(C)
        d2 = lambda v: float((v - mu) @ Ci @ (v - mu))
        dd = np.array([d2(v) for v in X]); do = d2(np.array([nin, ngap, wl.mean()]))
        pm = (dd >= do).mean()
        say(f"{name:4s}   " + "   ".join(f"{p:5.3f}" for p in pct) + f"   | {'YES' if ins4 else 'no '} | {pm:.3f}")

    # doublet position inside words (pooled over reps), against LP2
    say("\n## In-word doublet position (pooled reps): share at a word-edge pair, and distribution of the pair's relative position in 5 bins (0 = first pair slot, 1 = last)")
    say(f"LP2 (n {len(rel)}): edge {edge.mean():.2f}; rel-position bins " + " ".join(f"{x:.2f}" for x in np.histogram(rel, bins=5, range=(0, 1))[0] / len(rel)))
    for name, (R, rows) in res.items():
        ed = np.concatenate([x[11] for x in rows]) if rows else []
        wlr = np.concatenate([x[10] for x in rows])
        say(f"{name:4s} (n {len(ed)}): edge {np.mean(ed):.2f}; mean doublet-word len {wlr.mean():.2f}")

    dest = os.path.join(HERE, "..", "..", "results", "analysis")
    with open(os.path.join(dest, f"insert47{args.tag}.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
