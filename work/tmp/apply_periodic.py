"""Periodic-key hypotheses on full segments, with calibrated true/wrong baselines.
Metric: share of linked words the solver had to leave unexplained (wildcards), and score per rune."""
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


def metrics(prob, res):
    linked = prob.linked
    n = sum(len(prob.words[w][1]) for w in linked)
    wild = sum(1 for w in linked if res["words"] and res["words"].get(w, 0) is None)
    return res["score"] / max(1, n), wild / max(1, len(linked)), len(linked)


def run(prob):
    res = prob.solve_beam(width=100, per_state=20)
    if res["assign"] is None:
        return None
    return metrics(prob, res) + (prob.render(res["assign"])[:90],)


rows = {"baseline": [], "real": []}
R = random.Random(11)
for L in ((99, 333, 568) if __name__ == "__main__" else ()):
    n = max(3 * L, 1200)
    pt = attack.synthetic_tokens(n, start=R.randrange(5000, 60000))
    key = [R.randrange(29) for _ in range(L)]
    ct = cs._encrypt(pt, lambda i: key[i % L])
    for name, LL in (("true", L), ("wrong", L + 2)):
        m = run(cs.periodic_problem(ct, LL))
        rows["baseline"].append((L, name, m))
        print(f"baseline L={L} {name:5s}: " + (f"{m[0]:.2f}/rune, unexplained {100 * m[1]:.0f}% of {m[2]} linked words"
                                               if m else "no solution"), flush=True)

streams = [lp.runes_of(S[i]) for i in stats.UNSOLVED if len(lp.runes_of(S[i])) > 100]
h, t = crib.lag_scan(streams, 6000, 1)
z = crib.zscores(h, t)
z[:2] = -np.inf
z[t < 150] = -np.inf
lags = [int(L) for L in np.argsort(z)[-12:][::-1]]
print("candidate lags:", lags)
tasks = [(L, i, atb) for L in lags for i in stats.UNSOLVED if len(lp.runes_of(S[i])) >= 2 * L for atb in (False, True)]


def one(task):
    L, i, atb = task
    return (L, i, atb, run(cs.periodic_problem(S[i], L, atbash=atb)))


if __name__ == "__main__":
    from multiprocessing import Pool
    with Pool() as pool:
        for L, i, atb, m in pool.imap_unordered(one, tasks):
            rows["real"].append((L, i, atb, m))
            print(f"  L={L:4d} seg 0.{i:<2} atbash={atb!s:5s}: {m[0]:.2f}/rune, unexplained {100 * m[1]:.0f}% "
                  f"of {m[2]} linked words  {m[3][:60]}", flush=True)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "phase4", "crib_periodic.json"), "w",
              encoding="utf-8") as f:
        json.dump(rows, f)
