"""Profile the v3 fast init per statement group (scratch)."""
import cProfile
import io
import math
import os
import pstats
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h5slice as H
import sim

logf = H.english_logf()
plain = sim.english_runes()[3000:3300]
tvals = H.totient(4000)
c = H.plant(plain, tvals, 1234, H.DIVINITY, 0, keep=0.19, litf=False, b=0, seed=42)
ts = tvals[1234:1234 + 407]

# warm
H.beam_coincidence_nats_fast(c, -1, ts, 8, False, 12, logf, 0, 0.0)

pr = cProfile.Profile()
pr.enable()
for _ in range(3):
    H.beam_coincidence_nats_fast(c, -1, ts, 8, False, 12, logf, 0, 0.0)
pr.disable()
s = io.StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
ps.print_stats(28)
print(s.getvalue())
