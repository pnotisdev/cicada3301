"""Phase 54: where does the within-word lag-6 relation c' = 24 - 2c (mod 29) live? See work/log/phase54_lag6_dissect.md.

    python work/phase54_lag6_dissect.py     # -> results/analysis/phase54_lag6_dissect.txt
Null: within-word rune shuffles (word lengths and word memberships kept), NDRAW draws; plus the exact expectation under independence.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lp  # noqa: E402
import stats  # noqa: E402

N, LAG, S, NDRAW = lp.N, 6, 15, 10000
OUT = []


def say(s=""):
    print(s)
    OUT.append(s)


def load(ids):
    """runes, word id, position in word, word length, section, page for the given segments (words as lp.word_spans cuts them)"""
    R, W, P, L, SEC, PG = [], [], [], [], [], []
    w = 0
    for k, i in enumerate(ids):
        toks = stats.SEGS[i]
        r = lp.runes_of(toks)
        page, pg = [], 0
        pos = 0
        for t in toks:                      # page number of each rune
            if isinstance(t, int):
                page.append(pg); pos += 1
            elif t == "%":
                pg += 1
        for _, a, b in lp.word_spans(toks, r):
            R += r[a:b]; W += [w] * (b - a); P += range(b - a); L += [b - a] * (b - a)
            SEC += [k] * (b - a); PG += page[a:b]
            w += 1
    return [np.array(x) for x in (R, W, P, L, SEC, PG)]


def sites(C, W):
    i = np.arange(len(C) - LAG)
    i = i[W[i] == W[i + LAG]]
    return i


def hits(C, i):
    return C[i + LAG] == (24 - 2 * C[i]) % N


def shuffle_batch(C, W, B, rng):
    """B within-word shuffles at once: sort by (word, random key)"""
    out = np.empty((B, len(C)), C.dtype)
    base = np.lexsort((np.arange(len(C)), W))     # words are contiguous already, base = identity
    for b in range(B):
        k = rng.random(len(C))
        out[b] = C[np.lexsort((k, W))]
    return out


def expected_indep(C, i):
    """exact expectation: pairs (i, i+6) inside words, runes drawn independently from the pooled frequencies of the first/second members"""
    f = np.bincount(C, minlength=N) / len(C)
    return len(i) * float(sum(f[c] * f[(24 - 2 * c) % N] for c in range(N)))


class Cut:
    """collect (name, real value, null array) and report p-values with a count of cuts"""
    def __init__(self):
        self.rows = []

    def add(self, name, real, null, two=False):
        null = np.asarray(null, float)
        p = (1 + np.sum(null >= real)) / (len(null) + 1)
        self.rows.append((name, real, null.mean(), p))


def main():
    rng = np.random.default_rng(54)
    C, W, P, L, SEC, PG = load(stats.UNSOLVED)
    i = sites(C, W)
    h = hits(C, i)
    say(f"LP2 sections 0.7-0.15: {len(C)} runes, {len(i)} within-word pairs at lag {LAG}, hits {h.sum()}  (expected under independence {expected_indep(C, i):.2f})")
    assert len(C) == 12956
    # null draws: per-draw hit mask on the same site set (word memberships fixed, so the sites are the same)
    B = 500
    nulls = []
    for _ in range(NDRAW // B):
        X = shuffle_batch(C, W, B, rng)
        nulls.append((X[:, i + LAG] == (24 - 2 * X[:, i]) % N))
    H = np.concatenate(nulls)                         # (NDRAW, nsites) bool
    tot = H.sum(1)
    say(f"within-word shuffle null ({NDRAW}): mean {tot.mean():.2f} sd {tot.std():.2f}; real {h.sum()} -> z {(h.sum() - tot.mean()) / tot.std():+.2f}, p {(1 + np.sum(tot >= h.sum())) / (NDRAW + 1):.4f}")
    say("")
    cuts = []                                         # (cut name, real, null array)

    def cut(name, mask_fn):
        """mask_fn(array of site indices (or bool mask over sites)) -> statistic; evaluated on real hits and on every null draw"""
        cuts.append((name, mask_fn(h), np.array([mask_fn(x) for x in H])))

    # (1) word length and position
    Li, Pi = L[i], P[i]
    for lo, hi in ((7, 7), (8, 8), (9, 9), (10, 11), (12, 99)):
        m = (Li >= lo) & (Li <= hi)
        cut(f"word length {lo}-{hi} (pairs {m.sum()})", lambda x, m=m: x[m].sum())
    for p0 in range(5):
        m = Pi == p0
        cut(f"pair starts at word position {p0} (pairs {m.sum()})", lambda x, m=m: x[m].sum())
    m = (Li - Pi - LAG - 1) == 0
    cut(f"pair ends at the last rune (pairs {m.sum()})", lambda x, m=m: x[m].sum())
    # (2) which runes
    cnt = lambda x: np.bincount(C[i][x], minlength=N)
    cut("max over c of hits(c): dominance of one source rune", lambda x: cnt(x).max())
    cut("sum over c of hits(c)^2 (spread)", lambda x: (cnt(x) ** 2).sum())
    cut("share of hits with c' = S (15)", lambda x: (C[i + LAG][x] == S).sum())
    cut("share of hits with c = S", lambda x: (C[i][x] == S).sum())
    # (3) neighbours of the sites: offsets d from i; equal to c, to c', to T(c)
    Cc, Cp = C[i], C[i + LAG]
    for d in (-1, 1, 2, 3, 4, 5, 7):
        ok = (i + d >= 0) & (i + d < len(C))
        j = np.clip(i + d, 0, len(C) - 1)
        ok &= W[j] == W[i]                                    # neighbour in the same word
        # neighbours move with the shuffle, so recompute from the shuffled text: see separate loop below
    # (4) sections / pages
    exp_sec = np.array([(SEC[i] == k).sum() for k in range(9)])
    for name, key, n in (("section", SEC[i], 9), ("page", PG[i] + 100 * SEC[i], None)):
        ids = np.unique(key)
        M = np.array([key == u for u in ids])             # (units, sites)
        mu = H.mean(0) @ M.T
        chi = lambda x: float((((x.astype(float) @ M.T) - mu) ** 2 / np.maximum(mu, 1e-9)).sum())
        cut(f"{name} heterogeneity chi2 over {len(ids)} units", chi)
    # (5) overlap with doublets / S: a doublet inside the 7-rune window, S anywhere in the window
    win_dbl = np.array([(C[a:a + LAG] == C[a + 1:a + LAG + 1]).any() for a in i])
    win_S = np.array([(C[a:a + LAG + 1] == S).any() for a in i])
    cut(f"hits in windows with a doublet (windows {win_dbl.sum()})", lambda x: x[win_dbl].sum())
    cut(f"hits in windows containing an S (windows {win_S.sum()})", lambda x: x[win_S].sum())
    report(cuts, "single-rune and site cuts")
    say("hits per section (sites): " + ", ".join(f"0.{7 + k}: {h[SEC[i] == k].sum()}/{(SEC[i] == k).sum()}" for k in range(9)))
    top = np.bincount(C[i][h], minlength=N)
    say("hits per source rune c (Latin): " + ", ".join(f"{lp.LATIN[c]}->{lp.LATIN[(24 - 2 * c) % N]}:{top[c]}" for c in np.argsort(-top) if top[c]))
    pg = [(int(SEC[i][h][j]), int(PG[i][h][j])) for j in range(h.sum())]
    from collections import Counter
    say("pages with >= 4 hits (section, page): " + str([(k, v) for k, v in Counter(pg).items() if v >= 4]))
    say()
    # (3) neighbour relations need the shuffled texts (neighbours are re-drawn with each shuffle): rerun a smaller null
    nb = []
    Bn = 500
    rng = np.random.default_rng(55)
    rel_real = neighbour_counts(C, i, h, W)
    rel_null = []
    for _ in range(NDRAW // Bn):
        X = shuffle_batch(C, W, Bn, rng)
        for x in X:
            rel_null.append(neighbour_counts(x, i, hits(x, i), W))
    rel_null = np.array(rel_null)
    cuts3 = [(f"c[i{d:+d}] == {t}", rel_real[k], rel_null[:, k]) for k, (d, t) in enumerate(NB)]
    report(cuts3, "neighbour cuts (fraction of hit sites where the neighbour equals c or c')")
    ncut = len(cuts) + len(cuts3)
    say(f"Total cuts looked at: {ncut}; Bonferroni threshold p < {0.05 / ncut:.5f} (min possible p at {NDRAW} draws = {1 / (NDRAW + 1):.5f})")
    say("")
    # (6) solved pages 0.0-0.6 negative control
    Cs, Ws, *_ = load(list(range(7)))
    isv = sites(Cs, Ws)
    hs = hits(Cs, isv).sum()
    ns = []
    rng = np.random.default_rng(56)
    for _ in range(NDRAW // B):
        X = shuffle_batch(Cs, Ws, B, rng)
        ns.append((X[:, isv + LAG] == (24 - 2 * X[:, isv]) % N).sum(1))
    ns = np.concatenate(ns)
    say(f"Negative control, segments 0.0-0.6 ({len(Cs)} runes, {len(isv)} pairs): hits {hs}, shuffle null {ns.mean():.2f} +/- {ns.std():.2f}, "
        f"z {(hs - ns.mean()) / ns.std():+.2f}, p {(1 + np.sum(ns >= hs)) / (NDRAW + 1):.4f}; independence expectation {expected_indep(Cs, isv):.2f}")
    os.makedirs(os.path.join(HERE, "..", "results", "analysis"), exist_ok=True)
    with open(os.path.join(HERE, "..", "results", "analysis", "phase54_lag6_dissect.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(OUT) + "\n")


NB = [(d, t) for d in (-1, 1, 2, 3, 4, 5, 7) for t in ("c", "c'")]


def neighbour_counts(C, i, h, W):
    out = []
    for d, t in NB:
        j = i + d
        ok = h & (j >= 0) & (j < len(C))
        j = np.clip(j, 0, len(C) - 1)
        ok &= W[j] == W[i]
        ref = C[i] if t == "c" else C[i + LAG]
        out.append(int((ok & (C[j] == ref)).sum()))
    return out


def report(cuts, title):
    say(f"-- {title}: real, null mean, one-sided p")
    for name, real, null in cuts:
        null = np.asarray(null, float)
        p = (1 + np.sum(null >= real)) / (len(null) + 1)
        say(f"  {name:62s} {real:8.2f} {null.mean():8.2f}  p {p:.4f}")
    say()


if __name__ == "__main__":
    main()
