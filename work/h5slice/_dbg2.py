"""Isolate the abort behavior."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h5slice as H
import sim

logf = H.english_logf()
plain = sim.english_runes()[3000:3300]
tvals = H.totient(4000)
OFF = 1234
c = H.plant(plain, tvals, OFF, H.DIVINITY, 0, keep=0.19, litf=False, b=0, seed=42)
ts = tvals[OFF:OFF + 300 + 107]

L = 8
abort_ll = 120 * (H.uni_mean_logf() + 0.15) + L * math.log(29)
print("abort_ll =", abort_ll)

r = H.beam_coincidence_nats(c, -1, ts, L, False, 12, logf, 120, abort_ll)
print("result is None:", r is None)

r2 = H.beam_coincidence_nats(c, -1, ts, L, False,12, logf, 0, 0.0)
print("no-abort result is None:", r2 is None, "score", round(r2[1], 1))

ioc, info = H.decode(c, -1, tvals, OFF, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
                     abort_at=120, abort_margin=0.15)
print("decode abort-on:", ioc)
