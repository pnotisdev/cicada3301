"""Apply the crib solver to the strongest periodic / key-reuse hypotheses from crib.scan()."""
import json
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import attack  # noqa: E402
import crib  # noqa: E402
import cribsolve as cs  # noqa: E402
import lp  # noqa: E402
import stats  # noqa: E402

S = stats.SEGS
OUT = {}


def slice_tokens(toks, lo, hi):
    """Tokens whose runes fall in [lo, hi), keeping separators; words cut at the edges are dropped."""
    out, k, cur = [], 0, []
    for t in toks + [" "]:
        if isinstance(t, int):
            cur.append((k, t))
            k += 1
        elif t in ("\n", "%"):                    # a bare line or page break is a wrap inside a word (lp.word_spans)
            continue
        else:
            if cur and cur[0][0] >= lo and cur[-1][0] < hi:
                out += [x for _, x in cur]
            if cur:
                out.append(" ")
            cur = []
    return out


def per_rune(prob, res):
    n = sum(len(cw) for w, (pos, cw) in enumerate(prob.words) if w in prob.linked)
    return res["score"] / max(1, n)


# ---- baselines on synthetic text (same sizes as the real runs)
R = random.Random(1)
pt = attack.synthetic_tokens(600, start=40000)
key = [R.randrange(29) for _ in range(101)]
ct = cs._encrypt(pt, lambda i: key[i % 101])
true_p = cs.periodic_problem(ct, 101)
tr = true_p.solve(time_limit=30)
wrong_p = cs.periodic_problem(ct, 97)
wr = wrong_p.solve(time_limit=30)
print(f"baseline periodic L=101 (600 runes): true {per_rune(true_p, tr):.2f}/rune, wrong period {per_rune(wrong_p, wr):.2f}/rune")
OUT["baseline_periodic"] = [per_rune(true_p, tr), per_rune(wrong_p, wr)]

pa, pb = attack.synthetic_tokens(400, start=50000), attack.synthetic_tokens(400, start=60000)
k = [R.randrange(29) for _ in range(500)]
ca, cb = cs._encrypt(pa, lambda i: k[i]), cs._encrypt(pb, lambda i: k[i])
tp = cs.depth_problem(ca, cb, 0)
tres = tp.solve_beam(width=200)
wp = cs.depth_problem(ca, cs._encrypt(pb, lambda i: k[i + 7]), 0)
wres = wp.solve_beam(width=200)
print(f"baseline depth (400+400 runes): true {per_rune(tp, tres):.2f}/rune, wrong offset {per_rune(wp, wres):.2f}/rune")
OUT["baseline_depth"] = [per_rune(tp, tres), per_rune(wp, wres)]

# ---- periodic hypotheses: top lags from the lag scan, first 600 runes of each segment
streams = [lp.runes_of(S[i]) for i in stats.UNSOLVED if len(lp.runes_of(S[i])) > 100]
seg_ids = [i for i in stats.UNSOLVED if len(lp.runes_of(S[i])) > 100]
h, t = crib.lag_scan(streams, 6000, 1)
z = crib.zscores(h, t)
z[:2] = -np.inf
z[t < 150] = -np.inf
top_lags = [int(L) for L in np.argsort(z)[-8:][::-1]]
print("top lags:", top_lags)
rows = []
for L in top_lags:
    for i in seg_ids:
        toks = slice_tokens(S[i], 0, 600)
        for atb in (False, True):
            p = cs.periodic_problem(toks, L, atbash=atb)
            if not p.linked:
                continue
            r = p.solve(time_limit=15, node_limit=50000)
            if r["assign"] is None:
                continue
            rows.append((per_rune(p, r), L, i, atb, p.render(r["assign"])[:100]))
rows.sort(reverse=True)
print("periodic, best per-rune scores:")
for r in rows[:6]:
    print(f"  {r[0]:.2f}/rune  L={r[1]} seg 0.{r[2]} atbash={r[3]}  {r[4]}")
OUT["periodic"] = rows[:20]

# ---- key-reuse hypotheses: top pairs from the cross scan
best, _ = crib.scan()
drows = []
for zz, x, y, d, rate, ov in best[:6]:
    ia, ib = seg_ids[x], seg_ids[y]
    na, nb = len(lp.runes_of(S[ia])), len(lp.runes_of(S[ib]))
    # overlap: a[i + d] aligns with b[i]
    lo_b, hi_b = max(0, -d), min(nb, na - d)
    hi_b = min(hi_b, lo_b + 400)
    ta = slice_tokens(S[ia], lo_b + d, hi_b + d)
    tb = slice_tokens(S[ib], lo_b, hi_b)
    # rebase so position j of B uses the key of position j of A
    for atb in (False, True):
        p = cs.depth_problem(ta, tb, 0, atbash=atb)
        r = p.solve_beam(width=200)
        drows.append((per_rune(p, r), ia, ib, d, atb, p.render(r["assign"])[:100]))
drows.sort(reverse=True)
print("key reuse, best per-rune scores:")
for r in drows[:6]:
    print(f"  {r[0]:.2f}/rune  0.{r[1]} vs 0.{r[2]} offset {r[3]:+d} atbash={r[4]}  {r[5]}")
OUT["depth"] = drows

os.makedirs(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tmp", "phase4"), exist_ok=True)
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "phase4", "crib_apply.json"), "w", encoding="utf-8") as f:
    json.dump(OUT, f)
