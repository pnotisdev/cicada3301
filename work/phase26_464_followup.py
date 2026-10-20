"""Phase 26, part 2: (i) selection-corrected null for R, (ii) calibration of the passage-removal and
question-construction percentages, (iii) a preregistered two-panel pairing test on the 928 rune-words of LP2
segments 12-14 with a positive control (planted pairing) and a null.
Usage: python work/phase26_464_followup.py [out.txt]   (single core, ~3 min)
"""
import itertools
import os
import sys

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lp  # noqa: E402
import phase26_words as pw  # noqa: E402

OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


def R_of(L, w):
    L = np.asarray(L, float)
    m = len(L) // w
    L = L[: m * w]
    cm = L.reshape(m, w).mean(0)
    return cm.var(ddof=1) / (L.var(ddof=1) / m)


def R_batch(X, w):
    B, n = X.shape
    m = n // w
    X = X[:, : m * w].astype(np.float64)
    cm = X.reshape(B, m, w).mean(1)
    return cm.var(1, ddof=1) / (X.var(1, ddof=1) / m)


rng = np.random.default_rng(2626)
segs = lp.load_segments()
SECT = [0, 1, 2, 3, 4, 5, 6, 16, 17]
SL = {i: np.array([len(w) for w in pw.seg_words(segs, i)]) for i in SECT}
L464 = np.concatenate([SL[0], SL[1], SL[3], SL[5]])
r_obs = R_of(L464, 16)

# ---------------------------------------------------------------- (i) selection-corrected null
say("== A. Is the chi-square approximation to the permutation p-value usable? ==")
for w in (4, 8, 16, 29):
    X = rng.permuted(np.tile(L464.astype(np.int8), (200000, 1)), axis=1)
    rr = R_batch(X, w)
    ro = R_of(L464, w)
    say(f"  w={w}: R_obs {ro:.4f}; simulated P(R<=obs) = {(rr <= ro + 1e-12).mean():.2e}; chi2_{w - 1} approx = {stats.chi2.cdf(ro * (w - 1), w - 1):.2e}")


def pval(R, w):
    return stats.chi2.cdf(R * (w - 1), w - 1)


subsets = [s for k in range(1, 10) for s in itertools.combinations(SECT, k)]


def family_cells(pool, widths_fn):
    """pool: dict sec->lengths. yields (subset, w, p)."""
    res = []
    for sub in subsets:
        L = np.concatenate([pool[i] for i in sub])
        n = len(L)
        for w in widths_fn(n):
            res.append((sub, w, pval(R_of(L, w), w)))
    return res


fam_A = lambda n: [w for w in range(4, 65) if n % w == 0 and n // w >= 4]
fam_B = lambda n: [16] if n >= 100 else []
fam_C = lambda n: list(range(8, 33)) if n >= 100 else []
obs = {}
for name, fn in (("A (all subsets x divisor widths 4..64)", fam_A), ("B (all subsets with >=100 words, w=16)", fam_B),
                 ("C (all subsets >=100 words x w=8..32, remainder dropped)", fam_C)):
    cells = family_cells(SL, fn)
    ps = np.array([c[2] for c in cells])
    j = int(ps.argmin())
    obs[name] = (ps.min(), len(cells))
    say(f"  family {name}: {len(cells)} cells; observed min p = {ps.min():.2e} at sections {cells[j][0]} w={cells[j][1]}")
chosen_p = pval(r_obs, 16)
say(f"  chosen cell (sections 0,1,3,5; w=16): chi2-approx p = {chosen_p:.2e}")

say("\n== B. Selection null: shuffle word lengths inside each section, repeat the whole family search ==")
REPS = 250
minp = {k: [] for k in obs}
cnt_chosen = 0
fam_defs = (("A (all subsets x divisor widths 4..64)", fam_A), ("B (all subsets with >=100 words, w=16)", fam_B),
            ("C (all subsets >=100 words x w=8..32, remainder dropped)", fam_C))
for rep in range(REPS):
    pool = {i: rng.permutation(SL[i]) for i in SECT}
    for name, fn in fam_defs:
        cells = family_cells(pool, fn)
        minp[name].append(min(c[2] for c in cells))
for name in obs:
    m = np.array(minp[name])
    say(f"  family {name}: null min-p median {np.median(m):.2e}, 5% quantile {np.quantile(m, .05):.2e}; "
        f"P(null min p <= observed {obs[name][0]:.2e}) = {(m <= obs[name][0] + 1e-15).mean():.4f} ({(m <= obs[name][0] + 1e-15).sum()}/{REPS}); "
        f"P(null min p <= chosen-cell p {chosen_p:.2e}) = {(m <= chosen_p + 1e-15).mean():.4f}")

# ---------------------------------------------------------------- (ii) removal calibration
say("\n== C. Passage-removal percentages (koan-passage-removal-assessment.txt) ==")
n, w = 464, 16
starts = np.arange(0, 449)
idx = starts[:, None] + ((np.arange(16)[None, :] - starts[:, None]) % 16)


def removal_R(X):
    """X: (B,464) -> (B,449) R after removing each 16-word block (28 rows kept)."""
    B = X.shape[0]
    Xf = X.astype(np.float64)
    colsum = Xf.reshape(B, 29, 16).sum(1)
    tot, tot2 = Xf.sum(1), (Xf ** 2).sum(1)
    rem = Xf[:, idx]                      # (B,449,16)
    cs = colsum[:, None, :] - rem
    s_rem, s2_rem = rem.sum(2), (rem ** 2).sum(2)
    N2 = 448
    sum_ = tot[:, None] - s_rem
    sq_ = tot2[:, None] - s2_rem
    var = (sq_ - sum_ ** 2 / N2) / (N2 - 1)
    vcm = (cs / 28).var(2, ddof=1)
    return vcm / (var / 28)


Ro = removal_R(L464[None, :])[0]
t0 = 298
say(f"  reproduced: R after removing words 299-314 = {Ro[t0]:.6f} (claim 0.390274); starts with a higher R: {(Ro > Ro[t0] + 1e-12).sum()} (claim 13)")
koan = np.arange(169, 169 + 193)   # starts wholly inside A Koan (0-based 169..), claim 193
say(f"  within A Koan (193 starts): higher R: {(Ro[koan] > Ro[t0] + 1e-12).sum()} (claim 3); frac of koan starts that raise R at all: {(Ro[koan] > r_obs).mean():.3f} (claim 0.751)")
# null: permuted sequences conditioned on low R (selection), plus unconditioned
spans = [170, 172, 182, 190, 201, 208, 221, 232, 244, 256, 264, 270, 278, 287, 299, 315, 325, 333, 338, 356, 370, 372]
sidx = np.array([s - 1 for s in spans if s - 1 <= 448])
Xs = rng.permuted(np.tile(L464.astype(np.int8), (400000, 1)), axis=1)
rr = R_batch(Xs, 16)
low = Xs[rr <= float(r_obs) + 1e-12]
say(f"  {len(low)} of {len(Xs)} random permutations have R <= {r_obs:.4f} (these are the 'selected' look-alikes)")
Rl = np.concatenate([removal_R(low[i:i + 500]) for i in range(0, len(low), 500)])
Ru = np.concatenate([removal_R(Xs[i:i + 500]) for i in range(0, 4000, 500)])
say(f"  in R<=0.2515 look-alikes: median R after removing a random 16-block = {np.median(Rl):.3f} "
    f"(real table: {np.median(Ro):.3f}); fraction of starts raising R at all {(Rl > r_obs).mean():.3f}")
say(f"  look-alikes: median over sequences of the BEST single removal R = {np.median(Rl.max(1)):.3f} (real table max {Ro.max():.3f}); "
    f"fraction of sequences whose R after removal at the 22 clause-aligned starts reaches >= {Ro[t0]:.3f} at least once: "
    f"{(Rl[:, sidx].max(1) >= Ro[t0]).mean():.3f}")
# percentile rank of the best clause-aligned removal (retrospective choice among 22)
real_rank = (Ro > Ro[sidx].max() + 1e-12).mean()
null_rank = (Rl[:, None, :] > Rl[:, sidx].max(1)[:, None, None]).mean(2)[:, 0] if False else \
    np.array([(Rl[i] > Rl[i, sidx].max() + 1e-12).mean() for i in range(len(Rl))])
say(f"  best-of-22 clause-aligned removal: real table is top {real_rank:.3%} of all 449 starts; in R<=0.2515 look-alikes the best clause-aligned "
    f"start is top {np.median(null_rank):.3%} (median), and the real value is exceeded (rank <= {real_rank:.3%}) in {(null_rank <= real_rank + 1e-12).mean():.3f} of look-alikes")
say("  -> compare with the report's 3.12% (fraction of starts), which treats the passage as pre-chosen")

# ---------------------------------------------------------------- (ii b) construction share
say("\n== D. Question-construction: one clause carries 67.76% of the net Welcome x man/master residual dot ==")
W_len, K_len = SL[1].astype(float), SL[3].astype(float)
colK = (45 + np.arange(len(W_len))) % 16          # Welcome starts at 0-based word 45
colKo = (45 + 124 + np.arange(len(K_len))) % 16   # koan starts at 169
Wres = np.zeros(16)
cnt = np.zeros(16)
for c, l in zip(colK, W_len):
    Wres[c] += l
    cnt[c] += 1
Wres = Wres - cnt * W_len.mean()
contrib = (K_len - K_len.mean()) * Wres[colKo]
net = contrib.sum()
say(f"  Welcome residual col 1 = {Wres[0]:.4f} (claim -9.2258); net dot = {net:.4f} (claim -17195/62 = {-17195 / 62:.4f})")
# clause spans from the report's ledger (1-based, within the 464 order)
led = [(170, 171), (172, 181), (182, 189), (190, 200), (201, 207), (208, 220), (221, 231), (232, 243), (244, 255), (256, 263),
       (264, 269), (270, 277), (278, 286), (287, 298), (299, 314), (315, 324), (325, 332), (333, 337), (338, 355), (356, 369),
       (370, 371), (372, 377)]
sizes = [b - a + 1 for a, b in led]
assert sum(sizes) == 208
bounds = np.cumsum([0] + sizes)
cl = np.array([contrib[bounds[i]:bounds[i + 1]].sum() for i in range(len(sizes))])
share = cl / net
say(f"  clause 0.2.0.14 contribution {cl[14]:.3f} (claim -187.935); share {share[14]:.4f} (claim 0.6776); max share {share.max():.4f}")
perm_share_max, perm_net = [], []
NPERM = 100000
for _ in range(NPERM):
    kp = rng.permutation(K_len)
    ct = (kp - kp.mean()) * Wres[colKo]
    nt = ct.sum()
    sh = np.array([ct[bounds[i]:bounds[i + 1]].sum() for i in range(len(sizes))]) / nt
    perm_share_max.append(sh.max())
    perm_net.append(nt)
perm_share_max, perm_net = np.array(perm_share_max), np.array(perm_net)
neg = perm_net < 0
say(f"  null (koan lengths shuffled, clause sizes kept): net dot mean {perm_net.mean():.1f}, sd {perm_net.std():.1f}; observed net {net:.1f} -> "
    f"P(net <= obs) = {(perm_net <= net).mean():.4f}")
say(f"  null: max single-clause share (same sign as net): median {np.median(perm_share_max):.3f}; P(max share >= 0.6776) = {(perm_share_max >= 0.6776).mean():.3f}; "
    f"among nulls with |net| >= observed: {(perm_share_max[np.abs(perm_net) >= abs(net)] >= .6776).mean():.3f} (n={int((np.abs(perm_net) >= abs(net)).sum())})")

# ---------------------------------------------------------------- (iii) two-panel pairing test
say("\n== E. Two-panel pairing test on the 928 rune-words of LP2 segments 12-14 ==")
C = []
for i in (12, 13, 14):
    C += pw.seg_words(segs, i)
Cs = [tuple(x) for x in C]
P1, P2 = Cs[:464], Cs[464:]
Lc = np.array([len(x) for x in C])


def variants():
    """Index maps: for each variant, a list perm[j] = index in P2 paired with P1 cell j (P1 laid 29 rows x 16 cols)."""
    out = {}
    base = np.arange(464).reshape(29, 16)
    for nm, f in (("id", lambda a: a), ("hflip", lambda a: a[:, ::-1]), ("vflip", lambda a: a[::-1, :]), ("rot180", lambda a: a[::-1, ::-1])):
        out["29x16 " + nm] = f(base).reshape(-1)
    g = np.arange(464).reshape(16, 29)     # P2 laid 16 x 29, transposed onto 29 x 16
    gt = g.T
    for nm, f in (("id", lambda a: a), ("hflip", lambda a: a[:, ::-1]), ("vflip", lambda a: a[::-1, :]), ("rot180", lambda a: a[::-1, ::-1])):
        out["16x29^T " + nm] = f(gt).reshape(-1)
    return out


V = variants()


def stats_for(p1, p2, perm):
    a = np.array([len(x) for x in p1], float)
    b = np.array([len(p2[j]) for j in perm], float)
    corr = np.corrcoef(a, b)[0, 1]
    eq = sum(1 for k in range(464) if p1[k] == p2[perm[k]])
    return corr, eq


NR = 3000
obs_stats = {k: stats_for(P1, P2, v) for k, v in V.items()}
null_c = {k: np.zeros(NR) for k in V}
null_e = {k: np.zeros(NR) for k in V}
for r in range(NR):
    sh = [P2[j] for j in rng.permutation(464)]
    for k, v in V.items():
        c, e = stats_for(P1, sh, v)
        null_c[k][r], null_e[k][r] = c, e
say(f"  {NR} null shuffles of panel 2; {len(V)} pairings x 2 statistics = {2 * len(V)} tests (Bonferroni alpha = {0.05 / (2 * len(V)):.4f})")
pm = []
for k in V:
    c, e = obs_stats[k]
    pc = ((null_c[k] >= c).sum() + 1) / (NR + 1)
    pe = ((null_e[k] >= e).sum() + 1) / (NR + 1)
    pm.append(min(pc, pe))
    say(f"  {k:18s}: corr(lengths) {c:+.3f} (p {pc:.3f}); identical rune-word pairs {e} (null mean {null_e[k].mean():.1f}, p {pe:.3f})")
thr = 0.05 / (2 * len(V))
say(f"  smallest p = {min(pm):.4f}; threshold {thr:.4f}; any detection: {min(pm) <= thr}")
# positive control: plant the pairing (a fraction q of panel-2 cells replaced by the paired panel-1 word)
say("  positive control (plant pairing, random variant, fraction q of cells copied) / null calibration:")
for q in (0.05, 0.10, 0.25):
    det = 0
    T = 100
    for t in range(T):
        k = list(V)[rng.integers(len(V))]
        v = V[k]
        P2p = list(P2)
        mask = rng.random(464) < q
        for j in np.nonzero(mask)[0]:
            P2p[v[j]] = P1[j]
        best = 1.0
        for kk, vv in V.items():
            c, e = stats_for(P1, P2p, vv)
            pc = ((null_c[kk] >= c).sum() + 1) / (NR + 1)
            pe = ((null_e[kk] >= e).sum() + 1) / (NR + 1)
            best = min(best, pc, pe)
        det += best <= thr
    say(f"    q = {q:.2f}: detected {det}/{T}")
det = 0
T = 300
for t in range(T):
    sh = [P2[j] for j in rng.permutation(464)]
    best = 1.0
    for kk, vv in V.items():
        c, e = stats_for(P1, sh, vv)
        pc = ((null_c[kk] >= c).sum() + 1) / (NR + 1)
        pe = ((null_e[kk] >= e).sum() + 1) / (NR + 1)
        best = min(best, pc, pe)
    det += best <= thr
say(f"    null (shuffled panel 2, same decision rule): false positives {det}/{T}")

if len(sys.argv) > 1:
    open(sys.argv[1], "w", encoding="utf-8").write("\n".join(OUT) + "\n")
