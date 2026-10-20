"""Phase 28: does ONE rule over Cicada numbers generate the 0.6 square's seeds {809, 434, 312, 966, 1311, 204} and t = 1246?

Preregistered family (frozen before any target is scored; see work/log/phase28_square_seeds.md):
  a RULE is (source sequence X, stride s in 1..6, offset o, op = op2 o op1 from a fixed list of 14 unary ops, with the
  identity among them).  It outputs the 7 numbers op(X[o + s*i]), i = 0..6.  A target 7-set T = {m, a, b, c, e, f, t}
  is scored by hits(rule) = |T intersect outputs(rule)|; a rule that "explains" T has hits = 7.
  Sources: Gematria-prime sums of the words, clauses and paragraphs of each solved/plain text (segments 0-6, 16, 17,
  decrypted with the library's keys), the printed numbers, the first 600 primes, naturals, Fibonacci, triangular numbers.
Calibration: the same family against 2000 random 7-sets of the same size range, and against the known 0.2 grid.
Usage: python work/phase28_square_seeds.py [out.txt]
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lp  # noqa: E402

OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


LIM = 200000
sv = np.ones(LIM + 1, bool)
sv[:2] = False
for i in range(2, int(LIM ** .5) + 1):
    if sv[i]:
        sv[i * i::i] = False
PR = np.nonzero(sv)[0]
PI = np.cumsum(sv)
phi = np.arange(LIM + 1, dtype=np.int64)
for p in PR:
    phi[p::p] -= phi[p::p] // p
sigma = np.zeros(LIM + 1, np.int64)
tau = np.zeros(LIM + 1, np.int64)
for d in range(1, LIM + 1):
    sigma[d::d] += d
    tau[d::d] += 1


def nextprime(n):
    return PR[np.searchsorted(PR, n, side="right")]


def prevprime(n):
    j = np.searchsorted(PR, n, side="left") - 1
    return PR[np.maximum(j, 0)]


# unary ops on int arrays (input in 0..LIM, output -1 when undefined / out of table)
def safe(f):
    def g(x):
        x = np.asarray(x, np.int64)
        ok = (x >= 1) & (x <= LIM)
        out = np.full(x.shape, -1, np.int64)
        out[ok] = f(x[ok])
        out[(out > LIM) | (out < 0)] = -1
        return out
    return g


OPS = {
    "id": lambda x: x,
    "phi": safe(lambda x: phi[x]),
    "sigma": safe(lambda x: sigma[x]),
    "tau": safe(lambda x: tau[x]),
    "p_n": safe(lambda x: np.where(x <= len(PR), PR[np.minimum(x - 1, len(PR) - 1)], -1)),
    "pi": safe(lambda x: PI[x]),
    "nextp": safe(lambda x: nextprime(x)),
    "prevp": safe(lambda x: prevprime(x)),
    "+1": safe(lambda x: x + 1),
    "-1": safe(lambda x: x - 1),
    "x2": safe(lambda x: 2 * x),
    "half": safe(lambda x: np.where(x % 2 == 0, x // 2, -1)),
    "3301-": safe(lambda x: np.where(x < 3301, 3301 - x, -1)),
    "1033-": safe(lambda x: np.where(x < 1033, 1033 - x, -1)),
}
OPN = list(OPS)
OP2 = [(a, b) for a in OPN for b in OPN if not (a == "id" and b == "id") or True]
OP2 = [(a, b) for (a, b) in OP2 if not (a == "id" and b != "id") or True]


def fib(n):
    a, b, out = 1, 2, []
    while len(out) < n:
        out.append(a)
        a, b = b, a + b
    return out


segs = lp.load_segments()
SEQ = {}
for i in (0, 1, 2, 3, 4, 5, 6, 16, 17):
    plain = lp.KNOWN[i][1](lp.runes_of(segs[i]))
    it = iter(plain)
    words, clauses, paras, nums = [], [], [], []
    cw = cc = cp = 0
    cur = 0
    for t in segs[i]:
        if isinstance(t, int):
            cur += lp.PRIME[next(it)]
        else:
            if t in (" ", ".", "&") or t.startswith("#"):
                if cur:
                    words.append(cur)
                    cc += cur
                    cp += cur
                    cur = 0
            if t == "." and cc:
                clauses.append(cc)
                cc = 0
            if t == "&" and cp:
                paras.append(cp)
                cp = 0
            if t.startswith("#") and t[1:].isdigit():
                nums.append(int(t[1:]))
    if cur:
        words.append(cur)
        cc += cur
        cp += cur
    if cc:
        clauses.append(cc)
    if cp:
        paras.append(cp)
    if i == 2:                          # the grid itself (words and numbers after CNOW THIS) is the TARGET, not an input
        words, clauses, paras, nums = words[:21], clauses[:5], [], []
    if i == 6:
        nums = []                       # the 25 printed numbers are the 0.6 square
    SEQ[f"s{i}.words"] = words
    SEQ[f"s{i}.clauses"] = clauses
    if len(paras) >= 2:
        SEQ[f"s{i}.paras"] = paras
    if len(nums) >= 7:
        SEQ[f"s{i}.numbers"] = nums
allw = [v for i in (0, 1, 2, 3, 4, 5, 6, 16, 17) for v in SEQ[f"s{i}.words"]]
SEQ["solved.words"] = allw
SEQ["solved.clauses"] = [v for i in (0, 1, 2, 3, 4, 5, 6, 16, 17) for v in SEQ[f"s{i}.clauses"]]
SEQ["solved.sections"] = [sum(SEQ[f"s{i}.words"]) for i in (0, 1, 2, 3, 4, 5, 6, 16, 17)]
SEQ["solved.cumwords"] = list(np.cumsum(allw))
SEQ["primes600"] = [int(p) for p in PR[:600]]
SEQ["naturals"] = list(range(1, 1500))
SEQ["fibonacci"] = fib(24)
SEQ["triangular"] = [k * (k + 1) // 2 for k in range(1, 400)]
SEQ["gp_primes"] = [int(p) for p in lp.PRIME]
SEQ["cicada"] = [3301, 1033, 29, 464, 174, 3300, 1032, 3299, 1034, 58, 87, 116, 348, 45415, 2, 3, 5, 7, 11, 13]
STRIDES = (1, 2, 3, 4, 5, 6)

# ------------------------------------------------------------ build the rule table
VALS = []
META = []
for name, seq in SEQ.items():
    x = np.array(seq, np.int64)
    L = len(x)
    for a, b in OP2:
        y = OPS[b](OPS[a](x))
        for s in STRIDES:
            n = L - 6 * s
            if n <= 0:
                continue
            idx = np.arange(n)[:, None] + s * np.arange(7)[None, :]
            W = y[idx]
            VALS.append(W.astype(np.int32))
            META.append((name, a, b, s, n))
VALS_ALL = np.concatenate(VALS)
NRULES = len(VALS_ALL)
say(f"== family size: {len(SEQ)} source sequences x 196 op pairs x strides 1..6 x offsets = {NRULES:,} rules ==")
say("   sources: " + ", ".join(f"{k}({len(v)})" for k, v in SEQ.items()))
OFFS = np.cumsum([0] + [m[4] for m in META])


def hits(target):
    """max over rules of |target intersect outputs|, with arg and count at the max."""
    cov = np.zeros(NRULES, np.int8)
    for v in target:
        cov += (VALS_ALL == v).any(1)
    mx = cov.max()
    return int(mx), int((cov == mx).sum()), cov


def describe(cov, mx, limit=4):
    out = []
    for r in np.nonzero(cov == mx)[0][:limit]:
        j = np.searchsorted(OFFS, r, side="right") - 1
        nm, a, b, s, n = META[j]
        o = r - OFFS[j]
        out.append(f"{nm} stride {s} offset {o} op {b}({a}(x)) -> {VALS_ALL[r].tolist()}")
    return out


# ------------------------------------------------------------ targets
T6 = [809, 434, 312, 966, 1311, 204, 1246]
T2 = [91, 272, 138, 341, 151, 366, 471]
say("\n== real targets ==")
for nm, T in (("0.6 seeds + t", T6), ("0.2 seeds + t", T2)):
    mx, cnt, cov = hits(T)
    say(f"  {nm} {T}: best rule explains {mx}/7 numbers ({cnt} rules tie)")
    for d in describe(cov, mx):
        say("     " + d)
    hist = np.bincount(cov, minlength=8)
    say(f"     rules by hits 0..7: {hist.tolist()}")

# ------------------------------------------------------------ calibration
rng = np.random.default_rng(28)
say("\n== calibration: random 7-sets of the same size range ==")
for nm, lo, hi_seed, hi_t, real in (("0.6-like (seeds 90..1400, t 100..1650)", 90, 1400, 1650, T6),
                                   ("0.2-like (seeds 18..400, t 100..520)", 18, 400, 520, T2)):
    mxs = []
    for _ in range(300):
        seeds = rng.choice(np.arange(lo, hi_seed), 6, replace=False)
        t = rng.integers(100, hi_t)
        mx, _, _ = hits([*seeds, t])
        mxs.append(mx)
    mxs = np.array(mxs)
    rm, _, _ = hits(real)
    say(f"  {nm}: best-rule hits over 300 random sets: distribution {np.bincount(mxs, minlength=8).tolist()}; "
        f"P(max >= {rm}) = {(mxs >= rm).mean():.3f}; P(max >= 5) = {(mxs >= 5).mean():.3f}; real best = {rm}")

# ------------------------------------------------------------ positive control: a planted rule
say("\n== positive control: a target generated by a rule from the family ==")
ok = 0
for k in range(20):
    r = rng.integers(NRULES)
    row = VALS_ALL[r]
    if (row < 0).any() or len(set(row.tolist())) < 7:
        continue
    mx, _, _ = hits(row.tolist())
    ok += mx == 7
say(f"  planted rules recovered with 7/7: {ok} of the valid draws (of 20)")

if len(sys.argv) > 1:
    open(sys.argv[1], "w", encoding="utf-8").write("\n".join(OUT) + "\n")
