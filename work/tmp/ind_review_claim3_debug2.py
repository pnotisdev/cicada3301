"""Debug 2: skip-plant (q=0.81) ciphertext, decode at offsets 3/4/5/6.
Trace and compare against the planted plaintext."""
import sys
sys.path.insert(0, "work/tmp")
from ind_review_claim3 import (Q, forward, layout_starts, plant,
                               reference_logs, totient_key)

sys.path.insert(0, "work")
import lp

logs, _ = reference_logs()
n = 300
starts = layout_starts(7, n)
plain = lp.KNOWN[1][1](lp.runes_of(lp.load_segments()[1]))[:n]
key = totient_key(4 * n + 64)

c, aligned = plant(plain, starts, key, 3, 1, False, 0.0, 20000, q=0.81)
doublets = [i for i in range(1, n) if c[i] == c[i - 1]]
print(f"skip plant: {len(doublets)} ciphertext doublets at {doublets[:20]}")

for off in (3, 4, 5, 6):
    r = forward(c, starts, key, off, 1, False, 0.0, logs, q=0.81, trace=True)
    match = sum(a == b for a, b in zip(aligned, r["aligned"]))
    print(f"offset {off}: S={r['score_nats']:+.2f}  match={match}/{n}  "
          f"peak_states={r['peak_states']}  deleted={r['deleted'][:6]}")

# what does the offset-4 Viterbi actually read?  compare to plain and to p-gap
r4 = forward(c, starts, key, 4, 1, False, 0.0, logs, q=0.81, trace=True)
r3 = forward(c, starts, key, 3, 1, False, 0.0, logs, q=0.81, trace=True)
d4 = [(i, p, d) for i, (p, d) in enumerate(zip(plain, r4["aligned"])) if p != d]
print(f"offset 4: {len(d4)}/{n} differ; first 10 (i, plain, decoded): {d4[:10]}")
d3 = [(i, p, d) for i, (p, d) in enumerate(zip(plain, r3["aligned"])) if p != d]
print(f"offset 3: {len(d3)}/{n} differ; first 10: {d3[:10]}")

# decode the SAME skip ciphertext with q=0 (no skip freedom) for comparison
for off in (3, 4):
    r = forward(c, starts, key, off, 1, False, 0.0, logs, q=0.0, trace=True)
    match = sum(a == b for a, b in zip(aligned, r["aligned"]))
    print(f"q=0 decoder, offset {off}: S={r['score_nats']:+.2f}  match={match}/{n}")
