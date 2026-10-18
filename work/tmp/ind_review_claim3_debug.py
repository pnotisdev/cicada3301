"""Debug: why does offset 4 nearly tie offset 3 on the totient key?

No-skips (q=0), no-null plant: c_i = p_i + k[3+i]. Decode at offsets 3 and 4.
Oracle S of the true plaintext vs S of the decodes. Uses ind_review_claim3's
own routines (importing my own scratch file, not the reviewed folder)."""
import sys
sys.path.insert(0, "work/tmp")
from ind_review_claim3 import (Q, LOG_Q, forward, layout_starts, plant,
                               reference_logs, totient_key)

sys.path.insert(0, "work")
import lp
import math

logs, _ = reference_logs()
n = 300
starts = layout_starts(7, n)
plain = lp.KNOWN[1][1](lp.runes_of(lp.load_segments()[1]))[:n]
key = totient_key(4 * n + 64)

c, aligned = plant(plain, starts, key, 3, 1, False, 0.0, 20000, q=0)
assert aligned == plain

for off in (3, 4, 5, 6):
    r = forward(c, starts, key, off, 1, False, 0.0, logs, q=0, trace=True)
    print(f"offset {off}: S={r['score_nats']:+.2f}  aligned==plain? "
          f"{r['aligned'] == plain}")

# oracle: S of the true plaintext under the same model
S = sum(logs[a][b] + LOG_Q for a, b in zip([Q] + plain[:-1], plain))
print(f"oracle S(plain) = {S:+.2f}")

# what does offset 4 actually decode?
r4 = forward(c, starts, key, 4, 1, False, 0.0, logs, q=0, trace=True)
diff = [(a, b) for a, b in zip(plain, r4["aligned"]) if a != b]
print(f"offset 4: {len(diff)}/{n} positions differ from plain; first 12 diffs "
      f"(true,decoded)={diff[:12]}")
# gaps: k[3+i]-k[4+i] = -(p_{4+i}-p_{3+i}) = -prime gap
gaps = [(key[3 + i] - key[4 + i]) % Q for i in range(6)]
print("k[3+i]-k[4+i] first 6:", gaps)
