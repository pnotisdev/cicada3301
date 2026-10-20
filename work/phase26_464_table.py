"""Phase 26: calibrate the community's "464-word table" claim (column word-length balance R = 0.2515).

R = sample variance of the c column means / (pooled sample variance / m)   (m = rows). E[R] = 1 under a random
permutation of the lengths (exactly). Nulls: (a) permutation; (b) look-elsewhere over section subsets and widths;
(b2) 464-word slices of English prose spelled in GP runes (work/book_key_flatness.to_runes);
(c) row-composition null (permute words WITHIN each row of the table) which separates "rows are locally homogeneous"
from "columns are arranged"; plus the same statistic on the 928 rune-words of LP2 segments 12-14 as two panels.
Usage: python work/phase26_464_table.py [out.txt]   (single core, a few minutes)
"""
import itertools
import os
import re
import sys
from fractions import Fraction

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lp  # noqa: E402
import phase26_words as pw  # noqa: E402
import book_key_flatness as bk  # noqa: E402

OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


def R_of(L, w):
    """R for lengths L laid row-major in w columns; trailing partial row dropped."""
    L = np.asarray(L, float)
    m = len(L) // w
    L = L[: m * w]
    if m < 2:
        return np.nan
    cm = L.reshape(m, w).mean(0)
    return cm.var(ddof=1) / (L.var(ddof=1) / m)


def R_batch(X, w):
    """X: (B, n) lengths."""
    B, n = X.shape
    m = n // w
    X = X[:, : m * w].astype(np.float64)
    cm = X.reshape(B, m, w).mean(1)
    return cm.var(1, ddof=1) / (X.var(1, ddof=1) / m)


def exact_R(L, w):
    L = [int(x) for x in L]
    m = len(L) // w
    cm = [Fraction(sum(L[c::w]), m) for c in range(w)]
    mu = sum(cm) / w
    v = sum((x - mu) ** 2 for x in cm) / (w - 1)
    n = m * w
    mean = Fraction(sum(L), n)
    s2 = sum((x - mean) ** 2 for x in L) / (n - 1)
    return v / (s2 / m)


rng = np.random.default_rng(26)
segs = lp.load_segments()
SECT = {0: "A Warning", 1: "Welcome", 2: "Some Wisdom", 3: "A Koan", 4: "Loss of Divinity", 5: "Koan 2",
        6: "An Instruction", 16: "An End", 17: "Parable"}
SL = {i: [len(w) for w in pw.seg_words(segs, i)] for i in SECT}

say("== 1. Facts reproduced from work/lp.py + work/ref/lp_verified.txt ==")
for i in SECT:
    say(f"  segment {i:2d} {SECT[i]:18s} words {len(SL[i]):4d} runes {sum(SL[i]):5d}")
L464 = SL[0] + SL[1] + SL[3] + SL[5]
say(f"  4 sections (Warning, Welcome, Koan, Koan 2): words {len(L464)}, runes {sum(L464)}  (claim: 464, 1796)")
npi = sum(1 for n in range(2, 3302) if all(n % d for d in range(2, int(n ** .5) + 1)))
say(f"  pi(3301) = {npi};  16*29 = {16 * 29}")
r16 = exact_R(L464, 16)
say(f"  R(16 columns, 29 rows) = {r16} = {float(r16):.12f}   (claim 77321/307435 = 0.251503569860)")
r16f = float(r16)
say(f"  R at 29 columns x 16 rows = {R_of(L464, 29):.4f}; at 8 cols = {R_of(L464, 8):.4f}; 58 cols = {R_of(L464, 58):.4f}")

C = []
for i in (12, 13, 14):
    C += pw.seg_words(segs, i)
say(f"  segments 12-14 rune-words {[len(pw.seg_words(segs, i)) for i in (12, 13, 14)]} total {len(C)} "
    f"(claim 224/349/355 = 928), runes {sum(map(len, C))} (claim 4134), number tokens "
    f"{sum(1 for i in (12, 13, 14) for t in segs[i] if isinstance(t, str) and t.startswith('#'))} (claim 5)")
g = lambda k: "".join(lp.GP[c][0] for c in C[k - 1])
say(f"  word 464 = {g(464)} ({len(C[463])} runes), word 465 = {g(465)} ({len(C[464])} runes)  (claim ᛋᚠᚾ / ᚢᚦᛟᚷᛖᚪᛟᛇᛇ)")
t13 = segs[13]
cnt, cur, pos = 0, False, {}
for j, x in enumerate(t13):
    if isinstance(x, int):
        if not cur:
            cnt += 1
            cur = True
            pos[cnt] = j
    elif x in (" ", ".", "&") or x.startswith("#"):
        cur = False
a, b = pos[240], pos[241]       # word 464 = 240th word of segment 13 (224 + 240)
between = t13[a + len(C[463]):b]
say(f"  tokens between word 464 and 465: {between}  (a plain word separator only -> no printed panel boundary)")

# ------------------------------------------------------------------ (a) permutation
say("\n== 2a. Permutation null (same 464 lengths shuffled; 16 columns) ==")
NP = 4_000_000
arr = np.array(L464, dtype=np.int8)
cnt_le, tot, first = 0, 0, None
chunk = 40000
for _ in range(NP // chunk):
    X = rng.permuted(np.tile(arr, (chunk, 1)), axis=1)
    r = R_batch(X, 16)
    if first is None:
        first = r
    cnt_le += int((r <= r16f + 1e-12).sum())
    tot += chunk
say(f"  {tot} permutations: mean R = {first.mean():.4f} (theory 1), sd {first.std():.4f}; "
    f"P(R <= {r16f:.4f}) = {cnt_le}/{tot} = {cnt_le / tot:.2e}  (plus-one: {(cnt_le + 1) / (tot + 1):.2e})")
say(f"  chi2_15/15 approximation: P = {stats.chi2.cdf(r16f * 15, 15):.2e}")

# ------------------------------------------------------------------ (c) mechanism
say("\n== 2c. Where does a low R come from? ==")
Lm = np.array(L464, dtype=float).reshape(29, 16)
within = ((Lm - Lm.mean(1, keepdims=True)) ** 2).sum() / (Lm.size - 29)
tot_var = Lm.var(ddof=1)
say(f"  within-row variance / total variance = {within / tot_var:.4f}  (random expectation ~ 1)")
x = np.array(L464, float) - np.mean(L464)
acf = [float((x[:-k] * x[k:]).sum() / (x * x).sum()) for k in range(1, 17)]
say("  ACF lags 1..16 of the 464 lengths: " + " ".join(f"{a:+.2f}" for a in acf))
B = 200000
Xr = rng.permuted(np.tile(Lm, (B, 1, 1)), axis=2).reshape(B, 464)
rr = R_batch(Xr, 16)
say(f"  row-composition null (words shuffled inside their own row): mean R = {rr.mean():.3f}, sd {rr.std():.3f}; "
    f"P(R <= {r16f:.4f}) = {(rr <= r16f + 1e-12).mean():.4f}")
say(f"  shuffling whole rows leaves R unchanged: {R_of(Lm[rng.permutation(29)].reshape(-1), 16):.6f}")


def clause_units(i):
    """List of clauses; each a list of word lengths (clause = text between '.' / '&' marks)."""
    units, ws, cur = [], [], 0
    for t in segs[i]:
        if isinstance(t, int):
            cur += 1
        else:
            if t in (" ", ".", "&") or t.startswith("#"):
                if cur:
                    ws.append(cur)
                    cur = 0
            if t in (".", "&") and ws:
                units.append(ws)
                ws = []
    if cur:
        ws.append(cur)
    if ws:
        units.append(ws)
    return units


units = []
for i in (0, 1, 3, 5):
    units += clause_units(i)
assert sum(len(u) for u in units) == 464, sum(len(u) for u in units)
say(f"  clause units in the 464 table: {len(units)} (mean {464 / len(units):.1f} words)")
cp = np.array([R_of([v for k in rng.permutation(len(units)) for v in units[k]], 16) for _ in range(50000)])
say(f"  clause-order shuffle (clauses intact, order random): mean R = {cp.mean():.3f}, sd {cp.std():.3f}, "
    f"P(R <= 0.2515) = {(cp <= r16f + 1e-12).mean():.4f}")

# ------------------------------------------------------------------ (b) look-elsewhere on the solved text
say("\n== 2b. Look-elsewhere on the solved LP text ==")
ids = list(SECT)
fam = []
for k in range(1, len(ids) + 1):
    for sub in itertools.combinations(ids, k):
        L = [v for i in sub for v in SL[i]]
        for w in range(4, 65):
            if len(L) % w == 0 and len(L) // w >= 4:
                fam.append((sub, w, len(L), R_of(L, w)))
Rf = np.array([f[3] for f in fam])
say(f"  family A: every non-empty subset of the 9 solved sections x every width 4..64 dividing n (>=4 rows): {len(fam)} cells")
say("    R quantiles 1/5/25/50/75/95%: " + " ".join(f"{np.quantile(Rf, q):.3f}" for q in (.01, .05, .25, .5, .75, .95)))
say(f"    cells with R <= 0.2515: {(Rf <= r16f + 1e-9).sum()} ({(Rf <= r16f + 1e-9).mean():.3%}); R <= 0.5: {(Rf <= 0.5).sum()}")
for f in sorted(fam, key=lambda f: f[3])[:6]:
    say(f"    lowest: sections {f[0]} w={f[1]} n={f[2]} R={f[3]:.4f}")
bookrun = [f for f in fam if list(f[0]) == [i for i in ids if f[0][0] <= i <= f[0][-1]]]
say(f"  family A2 (contiguous runs of whole sections in book order only): {len(bookrun)} cells, "
    f"min R = {min(f[3] for f in bookrun):.4f}, cells <= 0.2515: {sum(1 for f in bookrun if f[3] <= r16f + 1e-9)}")
fb = []
for k in range(1, len(ids) + 1):
    for sub in itertools.combinations(ids, k):
        L = [v for i in sub for v in SL[i]]
        if len(L) < 100:
            continue
        for w in range(8, 33):
            fb.append((sub, w, len(L), R_of(L, w)))
Rb = np.array([f[3] for f in fb])
say(f"  family B: subsets with >=100 words x every w in 8..32 (trailing partial row dropped): {len(fb)} cells; "
    f"quantiles 1/5/25/50% {' '.join(f'{np.quantile(Rb, q):.3f}' for q in (.01, .05, .25, .5))}; "
    f"cells <= 0.2515: {(Rb <= r16f + 1e-9).sum()} ({(Rb <= r16f + 1e-9).mean():.3%})")
w16 = [f for f in fb if f[1] == 16]
say(f"  family B at w=16 only: {len(w16)} subsets, median R {np.median([f[3] for f in w16]):.3f}, "
    f"fraction <= 0.2515: {np.mean([f[3] <= r16f + 1e-9 for f in w16]):.3%}; rank of the chosen 4-section subset "
    f"{1 + sum(1 for f in w16 if f[3] < r16f - 1e-9)} of {len(w16)}")
say("  R(w=16) of named selections:")
for sub in [(0, 1, 3, 5), (0, 1, 2, 3, 4, 5, 6), (0, 1, 2, 3, 4, 5, 6, 16, 17), (1, 3, 5), (0, 1, 3), (3,), (1,), (3, 5)]:
    L = [v for i in sub for v in SL[i]]
    say(f"    sections {sub}: n={len(L)} R16={R_of(L, 16):.3f}")

# ------------------------------------------------------------------ English slices
say("\n== 2b2. 464-word slices of English prose in GP-rune spelling (stride 8 words) ==")
cache = {}


def wlen(word):
    v = cache.get(word)
    if v is None:
        v = len(bk.to_runes(word))
        cache[word] = v
    return v


def corpus_lengths(path):
    t = bk.gutenberg_body(path)
    words = re.findall(r"[A-Za-z]+", t)
    return np.array([wlen(w) for w in words if wlen(w) > 0], dtype=np.int8)


EN = {"emerson": os.path.join(HERE, "ref", "emerson_essays1.txt")}
for n_, f_ in (("kjv", "pg10"), ("republic", "pg1497"), ("zarathustra", "pg1998"), ("origin", "pg2009"),
               ("walden", "pg205"), ("parlost", "pg26"), ("meditations", "pg2680"), ("ethics", "pg3800"),
               ("bge", "pg4363")):
    EN[n_] = os.path.join(HERE, "ref", "corpora", f_ + ".txt")
allr, ALLw = {}, {}
for name, path in EN.items():
    Ls = corpus_lengths(path)
    ALLw[name] = Ls
    starts = np.arange(0, len(Ls) - 464, 8)
    X = np.stack([Ls[s:s + 464] for s in starts])
    for w in (8, 16, 29, 58):
        allr.setdefault(w, []).append(R_batch(X, w))
    r = R_batch(X, 16)
    say(f"  {name:12s} {len(Ls):7d} words, {len(starts):5d} slices: mean word length {Ls.mean():.2f}; w=16 R mean {r.mean():.3f} "
        f"sd {r.std():.3f}, 1%/5% quantile {np.quantile(r, .01):.3f}/{np.quantile(r, .05):.3f}, frac<=0.2515 {(r <= 0.2515).mean():.4f}")
for w in (8, 16, 29, 58):
    r = np.concatenate(allr[w])
    say(f"  ALL English, w={w}: {len(r)} slices; mean R {r.mean():.3f}, median {np.median(r):.3f}, frac <= 0.2515: {(r <= 0.2515).mean():.4f}")
R4 = np.stack([np.concatenate(allr[w]) for w in (8, 16, 29, 58)])
say(f"  min over the 4 divisor widths (8,16,29,58) <= 0.2515: {(R4.min(0) <= 0.2515).mean():.4f}")
for name in ("emerson", "kjv", "origin"):
    Ls = ALLw[name].astype(float)[:200000]
    x = Ls - Ls.mean()
    say(f"  ACF {name}: lags1-6 " + " ".join(f"{(x[:-k] * x[k:]).mean() / x.var():+.3f}" for k in range(1, 7))
        + f" | lag 16: {(x[:-16] * x[16:]).mean() / x.var():+.3f}")
sl = ALLw["emerson"]
st = np.arange(0, len(sl) - 464, 8)
X = np.stack([sl[s:s + 464] for s in st]).astype(float)
Xr3 = X.reshape(len(st), 29, 16)
ratio = ((Xr3 - Xr3.mean(2, keepdims=True)) ** 2).sum((1, 2)) / (464 - 29) / X.var(1, ddof=1)
r = R_batch(X, 16)
say(f"  Emerson slices: corr(R, within-row/total variance) = {np.corrcoef(r, ratio)[0, 1]:.3f}; "
    f"mean ratio {ratio.mean():.3f} (table: {within / tot_var:.3f})")
# English slices: row-composition p-value distribution (is a slice's R low for the same reason?)
pv = []
for k in range(0, len(st), max(1, len(st) // 300)):
    Xk = rng.permuted(np.tile(X[k].reshape(29, 16), (2000, 1, 1)), axis=2).reshape(2000, 464)
    pv.append((R_batch(Xk, 16) <= r[k] + 1e-12).mean())
say(f"  Emerson slices, row-composition p-value of each slice's own R: median {np.median(pv):.3f}, "
    f"fraction < 0.05 = {np.mean(np.array(pv) < .05):.3f}  (table: {(rr <= r16f + 1e-12).mean():.4f})")

# ------------------------------------------------------------------ the 928 carrier
say("\n== 2d. The same statistic on the 928 rune-words of LP2 segments 12-14 (two panels) ==")
LC = [len(w) for w in C]
for lab, sl_ in (("panel 1 (words 1-464)", LC[:464]), ("panel 2 (words 465-928)", LC[464:])):
    say(f"  {lab}: " + "  ".join(f"R(w={w})={R_of(sl_, w):.3f}" for w in (16, 29)))
    for w in (16, 29):
        a_ = np.array(sl_, dtype=np.int8)
        X = rng.permuted(np.tile(a_, (20000, 1)), axis=1)
        er = np.concatenate(allr[w])
        o = R_of(sl_, w)
        say(f"    w={w}: permutation P(R<=obs) = {(R_batch(X, w) <= o + 1e-12).mean():.4f}; "
            f"English-slice fraction <= obs = {(er <= o + 1e-12).mean():.4f}")
EN16 = np.concatenate(allr[16])
say(f"  English 464-slice w=16: 1% quantile {np.quantile(EN16, .01):.3f}, 5% {np.quantile(EN16, .05):.3f}, median {np.median(EN16):.3f}")
for w in (16, 29):
    rv = np.array([R_of(LC[s:s + 464], w) for s in range(0, len(LC) - 463)])
    say(f"  all {len(rv)} start offsets of a 464-window inside the 928: w={w}: min R {rv.min():.3f} at start {int(rv.argmin()) + 1}, "
        f"median {np.median(rv):.3f}; English fraction <= that min: {(np.concatenate(allr[w]) <= rv.min()).mean():.4f}")

if len(sys.argv) > 1:
    open(sys.argv[1], "w", encoding="utf-8").write("\n".join(OUT) + "\n")
