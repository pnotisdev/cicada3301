"""Diagnostic: null vs truth init score distributions at checkpoints 120 and 200 (L=2..20)."""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h5slice as H
import sim

logf = H.english_logf()
uni = H.uni_mean_logf()
plain = sim.english_runes()[3000:3300]
tvals = H.totient(4000)
c = H.plant(plain, tvals, 1234, H.DIVINITY, 0, keep=0.19, litf=False, b=0, seed=42)

# truth per-rune score at checkpoints 120 and 200 (L=8, and the truth offset)
for nrunes in (120, 200, 300):
    ts = tvals[1234:1234 + 407]
    r = H.beam_coincidence_nats(c[:nrunes], -1, ts, 8, False, 12, logf, 0, 0.0)
    sc = r[1]
    print(f"truth L=8 at {nrunes}: score {sc:.1f} ({sc/nrunes:+.3f}/rune, "
          f"delta vs uni {sc/nrunes - uni:+.3f})")

# null distributions at 120 and 200 for L in {2, 8, 12, 16, 20}
for nrunes in (120, 200):
    for L in (2, 8, 12, 16, 20):
        rng = random.Random(1000 + L)
        scores = []
        for k in range(30):
            ws = H.random_stream(3400, 2000 + 30 * L + k)
            wc = [rng.randrange(29) for _ in range(nrunes)]
            off = rng.randrange(1800)
            r = H.beam_coincidence_nats(wc, -1, ws[off:off + 407], L, False, 12, logf, 0, 0.0)
            scores.append(r[1])
        mean = sum(scores) / len(scores)
        mx = max(scores)
        sd = (sum((s - mean) ** 2 for s in scores) / (len(scores) - 1)) ** 0.5
        print(f"null L={L:2d} at {nrunes}: mean {mean:8.1f} sd {sd:5.1f} max {mx:8.1f} "
              f"(delta/rune {mean/nrunes - uni:+.3f}, max-delta {mx/nrunes - uni:+.3f})")
