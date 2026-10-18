"""Calibration: truth plant decode, null decode distribution, abort behavior, timing."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h5slice as H

import sim

logf = H.english_logf()
unif = float(logf.mean())
print(f"unif mean logf = {unif:.4f}")

plain_all = sim.english_runes()
plain = plain_all[3000:3300]
print(f"plain IoC {H.overall_ioc(plain):.3f}, F count {plain.count(0)}")

tvals = H.totient(4000)
OFF = 1234
c = H.plant(plain, tvals, OFF, H.DIVINITY, 0, keep=0.19, litf=False, b=0, seed=42)
print(f"planted cipher IoC {H.overall_ioc(c):.3f}, doublets {sum(a == b for a, b in zip(c, c[1:]))}")

# truth decode, no abort
t0 = time.time()
ioc, info = H.decode(c, -1, tvals, OFF, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
                     abort_at=0, abort_margin=0.0, out_path=True)
t1 = time.time()
print(f"truth: ioc {ioc:.3f}, overall {info['overall']:.3f}, ll/rune {info['ll']:.3f}, "
      f"wcol {info['wcol']} vs DIVINITY {H.DIVINITY}, time {(t1 - t0) * 1000:.1f} ms")
print(f"kw match exact: {info['wcol'] == H.DIVINITY}")

# truth decode with abort on
ioc2, _ = H.decode(c, -1, tvals, OFF, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
                   abort_at=120, abort_margin=0.15)
print(f"truth with abort: ioc {ioc2:.3f} (aborted if 0)")

# t-alone (blindness)
iocb, _ = H.decode_t_only(c, -1, tvals[OFF:OFF + 300 + 107], 0, beam=32)
print(f"t-alone IoC: {iocb:.3f}")

# nulls: random windows, random streams, random offsets
import random
rng = random.Random(7)
t0 = time.time()
null_iocs = []
aborted = 0
N = 200
for k in range(N):
    ws = H.random_stream(3400, 100 + k)
    wc = [rng.randrange(29) for _ in range(300)]
    off = rng.randrange(1800)
    iocn, _ = H.decode(wc, -1, ws, off, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
                       abort_at=120, abort_margin=0.15)
    null_iocs.append(iocn)
    if iocn == 0.0:
        aborted += 1
t1 = time.time()
null_iocs = [x for x in null_iocs if x > 0]
print(f"null: {N} decodes, {aborted} aborted, non-aborted ioc mean {sum(null_iocs)/len(null_iocs):.3f} "
      f"max {max(null_iocs):.3f}, time {(t1 - t0) / N * 1000:.1f} ms/decode")

# wrong offset / wrong L at truth
for desc, off, L in [("wrongL7", OFF, 7), ("wrongL9", OFF, 9), ("wrongL16", OFF, 16),
                     ("off-1", OFF - 1, 8), ("off+1", OFF + 1, 8), ("off+100", OFF + 100, 8)]:
    io, _ = H.decode(c, -1, tvals, off, L, 0, litf=False, beam=24, max_em=5, logf=logf,
                     abort_at=120, abort_margin=0.15)
    print(f"{desc}: ioc {io:.3f}")

# litf plant
c5 = H.plant(plain, tvals, 987, H.DIVINITY, 0, keep=0.19, litf=True, b=0, seed=7)
ioc5, info5 = H.decode(c5, -1, tvals, 987, 8, 0, litf=True, beam=24, max_em=5, logf=logf,
                       abort_at=120, abort_margin=0.15, out_path=True)
print(f"litf truth: ioc {ioc5:.3f}, wcol {info5['wcol']} vs {H.DIVINITY}")
