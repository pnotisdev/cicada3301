"""Replica of the echo_nulls gate criterion on RANDOM keys (what their gate
actually plants), using my own reimplementation.  Criterion per their gate():
  margin = max S over (item 0, offset 3, true mult, true atb, either rho)
           - max S over everything else (2 keys x 8 offsets x 8 variants)
  pass iff margin >= 10 nats (plus their accuracy/null-recall checks).
Shows whether the gate would pass on its own terms and how the margin depends
on the plant's first hidden redraw position."""
import random
import sys
import time

sys.path.insert(0, "work/tmp")
from ind_review_claim3 import (Q, RHO, SKIP_Q, VARIANTS, forward, layout_starts,
                               reference_logs)

sys.path.insert(0, "work")
import lp

logs, _ = reference_logs()
n = 300
starts = layout_starts(7, n)
solved = [p for s in sorted(lp.KNOWN)
          for p in lp.KNOWN[s][1](lp.runes_of(lp.load_segments()[s]))]

t0 = time.time()
for rep in range(6):
    rng = random.Random(330100 + rep)
    keys = [(f"k{k}", [rng.randrange(Q) for _ in range(n * 4 + 64)]) for k in range(2)]
    mult = 1 if rep % 2 == 0 else 28
    atb = bool((rep // 2) % 2)
    plain = [solved[(rep * 53 + i) % len(solved)] for i in range(n)]

    # instrumented plant (same draw order as ind_review_claim3.plant)
    seed = rep * 10000
    rng2 = random.Random(seed)
    c, j, first_redraw, was_null, at = [], 3, None, False, 0
    for i in range(n):
        may = i - starts[i] >= 6 and (24 - 2 * c[i - 6]) % Q != c[i - 1]
        if may and not was_null and rng2.random() < RHO:
            c.append((24 - 2 * c[i - 6]) % Q)
            was_null = True
            continue
        p = plain[at]
        at += 1
        raw = Q - 1 - p if atb else p
        while True:
            y = (raw + mult * keys[0][1][j]) % Q
            j += 1
            if not c or y != c[-1] or rng2.random() >= SKIP_Q:
                break
            if first_redraw is None:
                first_redraw = i
        c.append(y)
        was_null = False

    rows = []
    for item, (_, key) in enumerate(keys):
        for off, m, a, rho in VARIANTS:
            s = forward(c, starts, key, off, m, a, rho, logs)["score_nats"]
            rows.append((item, off, m, a, rho, s))
    true = [r for r in rows if r[0] == 0 and r[1] == 3 and r[2] == mult and r[3] == atb]
    wrong = [r for r in rows if r not in true]
    margin = max(r[5] for r in true) - max(r[5] for r in wrong)
    best_wrong = max(wrong, key=lambda r: r[5])
    print(f"rep {rep}: mult={mult} atb={atb} first_redraw={first_redraw} "
          f"S_true={max(r[5] for r in true):+.1f} best_wrong={best_wrong[5]:+.1f} "
          f"at {best_wrong[:5]} margin={margin:+.1f} nats  gate10: {'PASS' if margin >= 10 else 'FAIL'}")
print(f"wall {time.time() - t0:.0f} s")
