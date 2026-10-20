"""Does LP2's word segmentation know the rune layer, and does the transformation depend on the position inside a word?

Three keyless tests with planted positive controls and shuffle nulls. They are the experiments an outside analysis put
first (2026-10-19: "preserved segmentation + destroyed symbols"; PLAN.md, 'Segmentation plan').

A  Separator layer vs rune layer. Is a word boundary between rune i and i+1 a function of the ciphertext near the gap?
   Features: c_i, c_i+1, c_i+1 - c_i, c_i+1 + c_i, c_i-1, c_i+2, c_i - c_i-1 (29 levels each) and, for g = 2..8, the number
   (0, 1, 2+) of equal pairs (k, k+g) that straddle the gap (the question 'is the lag-5 echo a placement effect?').
   Statistic: the Pearson chi-square of each feature; combined as the smallest nominal p (continuous, used for the controls)
   and as the family-wise probability (Westfall-Young) of the smallest shuffle p; null: the same runes re-segmented by shuffling
   the order of the word lengths inside each section (2,000 shuffles). Control: iid runes, boundaries put by a rule on c_i or
   on the difference with strength lam (the share of the boundaries that follow the rule), same boundary rate.
   Word-level version: the length of a word against the first rune of the word, its last rune, the last rune of the previous
   word and the first rune of the next word (29 x 10 tables, same null; control: a share lam of the words has the length
   2 + (first rune mod 6), the rest random lengths).
B  Position-stratified differences inside words. For each word length L = 3..8 and position pair i < j, the histogram of
   (c_j - c_i) mod 29 over the words of length L (adjacent pairs without the difference 0: the doublet rule). A key
   'fixed schedule K_j (or K_(L,j)) + a fresh offset per word' turns every histogram into a shifted copy of the plaintext's
   pair histogram, and is invisible to column coincidences between words. Statistic: the mean standardised chi-square over
   the cells; null: the runes shuffled inside each section, same word lengths.
C  Length-stratified columns. For each L = 2..9 and column j < L the equal-pair z of restart_columns on the words of
   length exactly L; statistic: the mean z over the cells (a key by (length, position) is a restart control per cell).

    python work/word_structure.py            # -> results/analysis/word_structure.txt (about 5 minutes)
    python work/word_structure.py --quick
"""
import argparse
import os
import sys
import time
from math import sqrt

import numpy as np
from scipy.stats import chi2, rankdata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lp
import restart_columns as rc
import sim
import stats

N = lp.N
IDX = list(stats.UNSOLVED)
OUT = os.path.join(HERE, "..", "results", "analysis", "word_structure.txt")

LAGS = list(range(2, 9))
LEVELS = [N] * 7 + [3] * len(LAGS)
NAMES = ["c_i", "c_i+1", "c_i+1 - c_i", "c_i+1 + c_i", "c_i-1", "c_i+2", "c_i - c_i-1"] + \
        [f"equal pair at lag {g} straddles the gap" for g in LAGS]


def load_lp2():
    secs = []
    for i in IDX:
        toks = stats.SEGS[i]
        r = lp.runes_of(toks)
        lens = [b - a for _, a, b in lp.word_spans(toks, r)]
        assert sum(lens) == len(r)
        secs.append((np.array(r, dtype=np.int64), np.array(lens, dtype=np.int64)))
    return secs


# ------------------------------------------------------------------------------------------------ A

def gap_features(c):
    """feature index rows for the gaps i = 8 .. n-10 of one section (gap i lies between rune i and rune i+1)"""
    n = len(c)
    if n < 20:
        return None
    i = np.arange(8, n - 9)
    f = [c[i], c[i + 1], (c[i + 1] - c[i]) % N, (c[i + 1] + c[i]) % N, c[i - 1], c[i + 2], (c[i] - c[i - 1]) % N]
    for g in LAGS:
        eq = np.zeros(n, dtype=np.int64)
        eq[: n - g] = c[: n - g] == c[g:]
        cs = np.concatenate([[0], np.cumsum(eq)])
        f.append(np.minimum(cs[i + 1] - cs[i + 1 - g], 2))      # pairs k in [i+1-g, i] straddle the gap
    return np.array(f)


def boundary_vector(lens, n):
    brk = np.zeros(n - 1, dtype=bool)
    brk[np.cumsum(lens)[:-1] - 1] = True
    return brk[8: n - 9]


def family_p(obs, null):
    """shuffle p of every feature, and the probability under the null that the smallest of them is this small
    (Westfall-Young: every null draw gets its own per-feature p from the other draws)"""
    B = null.shape[0]
    p_obs = (1 + (null >= obs).sum(axis=0)) / (B + 1)
    p_null = np.empty_like(null, dtype=float)
    for f in range(null.shape[1]):
        p_null[:, f] = (B - rankdata(null[:, f], method="min") + 1) / (B + 1)      # draws >= this one, itself included
    return p_obs, float((1 + (p_null.min(axis=1) <= p_obs.min()).sum()) / (B + 1))


class GapTest:
    def __init__(self, secs):
        self.secs = secs
        feats, self.keep = [], []
        for k, (c, _) in enumerate(secs):
            f = gap_features(c)
            if f is not None:
                feats.append(f)
                self.keep.append(k)
        self.F = np.concatenate(feats, axis=1)
        self.tot = [np.bincount(self.F[j], minlength=LEVELS[j]).astype(float) for j in range(len(LEVELS))]
        self.df = np.array([k - 1 for k in LEVELS], dtype=float)

    def y_of(self, lens_list):
        return np.concatenate([boundary_vector(lens_list[k], len(self.secs[k][0])) for k in self.keep])

    def chi(self, y):
        p = y.mean()
        w = y.astype(float)
        out = np.empty(len(LEVELS))
        for j, K in enumerate(LEVELS):
            o1 = np.bincount(self.F[j], weights=w, minlength=K)
            t = self.tot[j]
            ok = t > 0
            out[j] = (((o1[ok] - t[ok] * p) ** 2) / (t[ok] * p * (1 - p))).sum()
        return out

    def run(self, nperm, rng):
        lens_list = [lens for _, lens in self.secs]
        y = self.y_of(lens_list)
        obs = self.chi(y)
        null = np.empty((nperm, len(LEVELS)))
        for b in range(nperm):
            null[b] = self.chi(self.y_of([rng.permutation(l) for l in lens_list]))
        p_feat, p_wy = family_p(obs, null)
        lo, ln = -chi2.logsf(obs, self.df) / np.log(10), -chi2.logsf(null, self.df) / np.log(10)
        return {"rate": float(y.mean()), "gaps": int(len(y)), "chi": obs, "nom_p": chi2.sf(obs, self.df),
                "perm_p": p_feat, "p_wy": p_wy, "max_nl10p": float(lo.max()),
                "p_max": float((1 + (ln.max(axis=1) >= lo.max()).sum()) / (1 + nperm))}


WL_NAMES = ["first rune of the word", "last rune of the word", "last rune of the previous word", "first rune of the next word"]


def word_feats(c, lens):
    ends = np.cumsum(lens)
    first, last = c[ends - lens], c[ends - 1]
    lb = np.minimum(lens, 10) - 1                       # length class 0..9 (10 = ten or more)
    return [(first, lb), (last, lb), (last[:-1], lb[1:]), (first[1:], lb[:-1])]


class WordLevel:
    """word length against a rune next to the word: 29 x 10 tables, null = word lengths re-shuffled inside each section"""

    def __init__(self, secs):
        self.secs = secs

    def chis(self, lens_list):
        cols = [([], []) for _ in WL_NAMES]
        for (c, _), lens in zip(self.secs, lens_list):
            for k, (f, lb) in enumerate(word_feats(c, lens)):
                cols[k][0].append(f)
                cols[k][1].append(lb)
        out = []
        for fs, lbs in cols:
            o = np.bincount(np.concatenate(fs) * 10 + np.concatenate(lbs), minlength=N * 10).reshape(N, 10).astype(float)
            e = np.outer(o.sum(1), o.sum(0)) / o.sum()
            ok = e > 0
            out.append((((o - e) ** 2)[ok] / e[ok]).sum())
        return np.array(out)

    def run(self, nperm, rng):
        lens_list = [lens for _, lens in self.secs]
        obs = self.chis(lens_list)
        null = np.array([self.chis([rng.permutation(l) for l in lens_list]) for _ in range(nperm)])
        df = np.full(len(WL_NAMES), (N - 1) * 9.0)
        p_feat, p_wy = family_p(obs, null)
        lo, ln = -chi2.logsf(obs, df) / np.log(10), -chi2.logsf(null, df) / np.log(10)
        return {"chi": obs, "df": df, "nom_p": chi2.sf(obs, df), "perm_p": p_feat, "p_wy": p_wy,
                "p_min": float((1 + (ln.max(axis=1) >= lo.max()).sum()) / (1 + nperm))}


def synth_wordrule(secs, freq, lam, rng):
    """iid runes; a share lam of the words has the length 2 + (first rune mod 6), the others lengths drawn from LP2's"""
    pool = np.concatenate([l for _, l in secs])
    out = []
    for c, _ in secs:
        n, pos, lens = len(c), 0, []
        c = rng.choice(N, size=n, p=freq)
        while pos < n:
            L = 2 + int(c[pos]) % 6 if rng.random() < lam else int(rng.choice(pool))
            L = min(L, n - pos)
            lens.append(L)
            pos += L
        out.append((c, np.array(lens, dtype=np.int64)))
    return out


def synth_rule(secs, freq, rule, lam, rng, size=8):
    """iid runes with LP2's section lengths; a share lam of the boundaries follows a rule on c_i ('R') or on
    c_i+1 - c_i ('D'), the rest is random; the boundary rate is LP2's"""
    nb = sum(len(l) - 1 for _, l in secs) / sum(len(c) - 1 for c, _ in secs)
    chosen = rng.choice(N, size=size, replace=False)
    runes = [rng.choice(N, size=len(c), p=freq) for c, _ in secs]
    feat = [(c[:-1] if rule == "R" else (c[1:] - c[:-1]) % N) for c in runes]
    inS = [np.isin(x, chosen) for x in feat]
    pS = np.concatenate(inS).mean()
    out = []
    for c, ins in zip(runes, inS):
        p = np.minimum(1.0, nb * (lam * ins / pS + (1 - lam)))
        brk = rng.random(len(c) - 1) < p
        lens = np.diff(np.concatenate([[0], np.where(brk)[0] + 1, [len(c)]]))
        out.append((c, lens))
    return out


# ------------------------------------------------------------------------------------------------ B, C

class WordGrid:
    def __init__(self, secs):
        self.slices, pos, rows = [], 0, {}
        for c, lens in secs:
            self.slices.append((pos, pos + len(c)))
            for s, L in zip(np.cumsum(lens) - lens + pos, lens):
                rows.setdefault(int(L), []).append(np.arange(s, s + L))
            pos += len(c)
        self.idx = {L: np.array(r) for L, r in rows.items()}
        self.LB = [L for L in range(3, 9) if len(self.idx.get(L, [])) >= 40]
        self.LC = [L for L in range(2, 11) if len(self.idx.get(L, [])) >= 40]
        self.lens = np.concatenate([l for _, l in secs])
        self.n = pos

    def shuffled(self, G, rng):
        P = G.copy()
        for a, b in self.slices:
            P[a:b] = rng.permutation(G[a:b])
        return P

    def tb(self, G):
        zs = []
        for L in self.LB:
            A = G[self.idx[L]]
            for i in range(L):
                for j in range(i + 1, L):
                    h = np.bincount((A[:, j] - A[:, i]) % N, minlength=N).astype(float)
                    if j == i + 1:
                        h = h[1:]
                    e = h.sum() / len(h)
                    zs.append((((h - e) ** 2).sum() / e - (len(h) - 1)) / sqrt(2 * (len(h) - 1)))
        zs = np.array(zs)
        return float(zs.sum() / sqrt(len(zs))), float(zs.max())

    def zc(self, G, S, T):
        zs = []
        for L in self.LC:
            A = G[self.idx[L]]
            n = A.shape[0]
            pairs = n * (n - 1) / 2
            for j in range(L):
                cnt = np.bincount(A[:, j], minlength=N)
                x = float((cnt * (cnt - 1) // 2).sum())
                zs.append((x - pairs * S) / sqrt(pairs * (S - S * S) + n * (n - 1) * (n - 2) * (T - S * S)))
        zs = np.array(zs)
        return float(zs.sum() / sqrt(len(zs))), float(zs.max())

    def stat(self, G, S, T):
        return self.tb(G) + self.zc(G, S, T)

    def null(self, G, S, T, nperm, rng):
        return np.array([self.stat(self.shuffled(G, rng), S, T) for _ in range(nperm)])


VARIANTS = [("K(j)", "K(j)", 1.0), ("K(L,j)", "K(L,j)", 1.0), ("K(j) + offset per word", "K(j) + offset per word", 1.0),
            ("K(L,j) + offset per word", "K(L,j) + offset per word", 1.0), ("random key (OTP)", "random key (OTP)", 1.0),
            ("K(L,j) + offset, 50% of words", "K(L,j) + offset per word", 0.5),
            ("K(L,j) + offset, 25% of words", "K(L,j) + offset per word", 0.25),
            ("K(L,j) + offset, 10% of words", "K(L,j) + offset per word", 0.10),
            ("K(L,j), 25% of words", "K(L,j)", 0.25), ("K(L,j), 10% of words", "K(L,j)", 0.10)]


def plant(grid, eng, variant, rng, frac=1.0):
    """English runes cut at LP2's word lengths (book order), enciphered by a position schedule and/or a fresh offset per
    word; with frac < 1 only that share of the words is enciphered so, the others get a random key"""
    n = grid.n
    start = int(rng.integers(0, len(eng) - n))
    p = np.array(eng[start:start + n], dtype=np.int64)
    pos = np.concatenate([np.arange(L) for L in grid.lens])
    wl = np.repeat(grid.lens, grid.lens)
    wid = np.repeat(np.arange(len(grid.lens)), grid.lens)
    Kj = rng.integers(0, N, size=80)
    KLj = rng.integers(0, N, size=(80, 80))
    r = rng.integers(0, N, size=len(grid.lens))
    if variant == "K(j)":
        k = Kj[pos]
    elif variant == "K(L,j)":
        k = KLj[wl, pos]
    elif variant == "K(j) + offset per word":
        k = Kj[pos] + r[wid]
    elif variant == "K(L,j) + offset per word":
        k = KLj[wl, pos] + r[wid]
    else:
        k = rng.integers(0, N, size=n)
    c = (p + k) % N
    if frac < 1.0:
        use = (rng.random(len(grid.lens)) < frac)[wid]
        c = np.where(use, c, (p + rng.integers(0, N, size=n)) % N)
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    q = args.quick
    t0 = time.time()
    rng = np.random.default_rng(20261019)
    secs = load_lp2()
    G = np.concatenate([c for c, _ in secs])
    freq = np.bincount(G, minlength=N) / len(G)
    S, T = float((freq ** 2).sum()), float((freq ** 3).sum())
    nwords = sum(len(l) for _, l in secs)
    out = []
    P = out.append
    P(f"LP2 sections 0.{IDX[0]}-0.{IDX[-1]}: {len(G)} runes, {nwords} words; seed 20261019; times in seconds are on one core")
    P("")

    # ---------------------------------------------------------------- A
    P("A. Does the position of a word boundary depend on the ciphertext near the gap?")
    P("   14 features (29 levels for the first seven, 3 for the straddling-pair counts); null: word lengths re-shuffled inside each section")
    gt = GapTest(secs)
    nperm = 300 if q else 2000
    res = gt.run(nperm, rng)
    P(f"   gaps used {res['gaps']}, boundary rate {res['rate']:.4f}, {nperm} shuffles")
    P(f"   {'feature':44s} {'chi2':>8s} {'df':>3s} {'nominal p':>10s} {'shuffle p':>10s}")
    for j, nm in enumerate(NAMES):
        P(f"   {nm:44s} {res['chi'][j]:8.1f} {int(gt.df[j]):3d} {res['nom_p'][j]:10.3g} {res['perm_p'][j]:10.4f}")
    jm = int(np.argmin(res["perm_p"]))
    P(f"   combined (smallest nominal p, 10^-{res['max_nl10p']:.2f}), probability under the shuffle null: {res['p_max']:.4f}   [used for the controls]")
    P(f"   combined (smallest shuffle p, {res['perm_p'][jm]:.4f}: {NAMES[jm]}), family-wise probability under the shuffle null (Westfall-Young): {res['p_wy']:.4f}")
    P("")
    P("   Control (iid runes with LP2's frequencies and section lengths, same boundary rate; a share lam of the boundaries follows a rule")
    P("   on 8 of the 29 values of c_i ('R') or of c_i+1 - c_i ('D'); detection = probability under the shuffle null <= 0.01):")
    reps = 6 if q else 16
    nper = 120 if q else 300
    P(f"   {'rule':5s} {'lam':>5s} {'detected':>9s}")
    nullp = []
    for rule in ("R", "D"):
        for lam in (1.0, 0.5, 0.25, 0.12, 0.06, 0.03, 0.0):
            hit, ps = 0, []
            for _ in range(reps):
                sy = synth_rule(secs, freq, rule, lam, rng)
                r = GapTest(sy).run(nper, rng)
                hit += r["p_max"] <= 0.01
                ps.append(r["p_max"])
            if lam == 0.0:
                nullp += ps
            P(f"   {rule:5s} {lam:5.2f} {hit:6d}/{reps}")
    P(f"   null controls (lam 0, both rules, {len(nullp)} runs): shuffle p <= 0.05 in {sum(p <= 0.05 for p in nullp)}, <= 0.01 in {sum(p <= 0.01 for p in nullp)}")
    P("")
    P("   Word-level: the length of a word (1..9, 10+) against a rune beside the word; 29 x 10 tables, df 252")
    wl = WordLevel(secs)
    nperm = 300 if q else 2000
    r = wl.run(nperm, rng)
    P(f"   {'feature':36s} {'chi2':>8s} {'nominal p':>10s} {'shuffle p':>10s}   ({nperm} shuffles)")
    for j, nm in enumerate(WL_NAMES):
        P(f"   {nm:36s} {r['chi'][j]:8.1f} {r['nom_p'][j]:10.3g} {r['perm_p'][j]:10.4f}")
    P(f"   combined: smallest nominal p, probability under the shuffle null {r['p_min']:.4f}; smallest shuffle p, family-wise (Westfall-Young) {r['p_wy']:.4f}")
    P("   Control: a share lam of the words has length 2 + (first rune mod 6) (iid runes, other lengths drawn from LP2's); detected = p <= 0.01:")
    reps = 6 if q else 16
    nper = 120 if q else 300
    for lam in (1.0, 0.5, 0.25, 0.12, 0.06, 0.0):
        hit = sum(WordLevel(synth_wordrule(secs, freq, lam, rng)).run(nper, rng)["p_min"] <= 0.01 for _ in range(reps))
        P(f"   lam {lam:5.2f}: {hit}/{reps}")
    P("")

    # ---------------------------------------------------------------- B, C
    grid = WordGrid(secs)
    P("B/C. Position- and length-stratified relations inside words")
    P(f"   B cells: word lengths {grid.LB}, all position pairs i < j ({sum(L * (L - 1) // 2 for L in grid.LB)} cells); "
      f"C cells: lengths {grid.LC}, all columns ({sum(grid.LC)} cells)")
    # consistency check of the vectorised column z against restart_columns.column_stats
    chk = []
    for L in grid.LC:
        A = G[grid.idx[L]]
        z_rc, _ = rc.column_stats([list(map(int, w)) for w in A], freq, nj=L)
        pairs = A.shape[0] * (A.shape[0] - 1) / 2
        zv = []
        for j in range(L):
            cnt = np.bincount(A[:, j], minlength=N)
            n = A.shape[0]
            x = float((cnt * (cnt - 1) // 2).sum())
            zv.append((x - pairs * S) / sqrt(pairs * (S - S * S) + n * (n - 1) * (n - 2) * (T - S * S)))
        chk.append(float(np.abs(np.array(zv) - z_rc[:L]).max()))
    P(f"   vectorised column z against restart_columns.column_stats: largest difference {max(chk):.2e}")
    nperm = 300 if q else 2000
    obs = np.array(grid.stat(G, S, T))
    nul = grid.null(G, S, T, nperm, rng)
    names = ["B mean standardised chi2", "B largest cell z", "C mean column z", "C largest column z"]
    P(f"   LP2 against {nperm} within-section rune shuffles:")
    P(f"   {'statistic':28s} {'observed':>9s} {'null mean':>10s} {'null sd':>8s} {'null max':>9s} {'P(null >= obs)':>15s}")
    for k, nm in enumerate(names):
        P(f"   {nm:28s} {obs[k]:9.3f} {nul[:, k].mean():10.3f} {nul[:, k].std():8.3f} {nul[:, k].max():9.3f} "
          f"{(1 + (nul[:, k] >= obs[k]).sum()) / (1 + nperm):15.4f}")
    P("")
    eng = sim.english_runes()
    reps = 4 if q else 8
    nper = 100 if q else 200
    P(f"   Controls: English (Emerson) runes cut at LP2's word lengths and enciphered as stated; {reps} plants per row, "
      f"{nper} within-section shuffles each;")
    P("   cell = plants whose statistic exceeds every shuffle (mean z against the shuffles)")
    P(f"   {'cipher':32s} {'B mean chi2':>14s} {'C mean z':>14s}")
    for v, base, frac in VARIANTS:
        hb = hc = 0
        zb, zc = [], []
        for _ in range(reps):
            Gp = plant(grid, eng, base, rng, frac)
            fp = np.bincount(Gp, minlength=N) / len(Gp)
            Sp, Tp = float((fp ** 2).sum()), float((fp ** 3).sum())
            o = grid.stat(Gp, Sp, Tp)
            nl = grid.null(Gp, Sp, Tp, nper, rng)
            hb += o[0] > nl[:, 0].max()
            hc += o[2] > nl[:, 2].max()
            zb.append((o[0] - nl[:, 0].mean()) / nl[:, 0].std())
            zc.append((o[2] - nl[:, 2].mean()) / nl[:, 2].std())
        P(f"   {v:32s} {hb:3d}/{reps} ({np.mean(zb):6.1f}) {hc:3d}/{reps} ({np.mean(zc):6.1f})")
    P("")
    P(f"   total time {time.time() - t0:.0f} s")
    text = "\n".join(out) + "\n"
    if q:
        print("(quick run: result file not written)")
    else:
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    print(text)


if __name__ == "__main__":
    main()
