"""Quick smoke test of the nats init (scratch, not committed)."""
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h5slice as H
import sim

logf = H.english_logf()
print("uni_mean %.4f f_mean %.4f" % (H.uni_mean_logf(), float(logf.mean())))

plain = sim.english_runes()[3000:3300]
tvals = H.totient(4000)
OFF = 1234
c = H.plant(plain, tvals, OFF, H.DIVINITY, 0, keep=0.19, litf=False, b=0, seed=42)

t0 = time.time()
ioc, info = H.decode(c, -1, tvals, OFF, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
                     abort_at=0, abort_margin=0.0, out_path=True)
t1 = time.time()
wcol = info["wcol"]
print("truth no-abort: ioc %.3f wcol=%s ==DIVINITY %s  %.1f ms"
      % (ioc, wcol, wcol == H.DIVINITY, 1000 * (t1 - t0)))

ioc2, _ = H.decode(c, -1, tvals, OFF, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
                   abort_at=120, abort_margin=0.15)
print("truth abort-on : ioc %.3f (0 = aborted)" % ioc2)

# init-only: does the nats init find the true pointers?
ts = tvals[OFF:OFF + 300 + 107]
t0 = time.time()
ptrs, sc = H.beam_coincidence_nats(c, -1, ts, 8, False, 12, logf, 0, 0.0)
t1 = time.time()
skips = sum(ptrs[i] - ptrs[i - 1] - 1 for i in range(1, len(ptrs))) if len(ptrs) > 1 else 0
print("init: skips=%d score=%.1f score/rune=%.3f  %.1f ms" % (skips, sc, sc / 300, 1000 * (t1 - t0)))

# nulls
rng = random.Random(7)
t0 = time.time()
null_iocs = []
ab = 0
for k in range(40):
    ws = H.random_stream(3400, 100 + k)
    wc = [rng.randrange(29) for _ in range(300)]
    off = rng.randrange(1800)
    iocn, _ = H.decode(wc, -1, ws, off, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
                       abort_at=120, abort_margin=0.15)
    if iocn == 0.0:
        ab += 1
    else:
        null_iocs.append(iocn)
t1 = time.time()
print("nulls: 40 decodes, %d aborted, non-aborted ioc mean %.3f max %.3f, %.1f ms/decode"
      % (ab, sum(null_iocs) / len(null_iocs), max(null_iocs), 1000 * (t1 - t0) / 40))
