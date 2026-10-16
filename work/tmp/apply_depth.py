"""Key-reuse hypotheses from crib.scan(), solved with absolute positions (fixed alignment)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import crib  # noqa: E402
import cribsolve as cs  # noqa: E402
import lp  # noqa: E402
import stats  # noqa: E402

S = stats.SEGS
seg_ids = [i for i in stats.UNSOLVED if len(lp.runes_of(S[i])) > 100]


def per_rune(prob, res):
    n = sum(len(cw) for w, (pos, cw) in enumerate(prob.words) if w in prob.linked)
    return res["score"] / max(1, n)


best, _ = crib.scan()
rows = []
seen = set()
for zz, x, y, d, rate, ov in best[:10]:
    ia, ib = seg_ids[x], seg_ids[y]
    if (ib, ia, -d) in seen:  # same hypothesis seen from the other side
        continue
    seen.add((ia, ib, d))
    na, nb = len(lp.runes_of(S[ia])), len(lp.runes_of(S[ib]))
    lo_b, hi_b = max(0, -d), min(nb, na - d)       # a[i + d] aligns with b[i]
    hi_b = min(hi_b, lo_b + 400)
    for atb in (False, True):
        p = cs.depth_problem(S[ia], S[ib], d, atbash=atb, range_a=(lo_b + d, hi_b + d), range_b=(lo_b, hi_b))
        r = p.solve_beam(width=200)
        rows.append((per_rune(p, r), ia, ib, d, atb, zz, p.render(r["assign"])[:110]))
        print(f"  {rows[-1][0]:.2f}/rune  0.{ia} vs 0.{ib} offset {d:+d} atbash={atb} (scan z={zz:+.1f})  {rows[-1][6][:90]}",
              flush=True)
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "phase4", "crib_depth.json"), "w", encoding="utf-8") as f:
    json.dump(rows, f)
