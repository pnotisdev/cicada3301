"""Quick parity + timing check of the numba init vs the slow reference (scratch)."""
import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h5slice as H
import h5slice_nb as N
import sim

logf = H.english_logf()
uni = H.uni_mean_logf()
plain = sim.english_runes()[3000:3300]
tvals = H.totient(4000)
c = H.plant(plain, tvals, 1234, H.DIVINITY, 0, keep=0.19, litf=False, b=0, seed=42)


def check(label, c_, ts, L, abort_at, a_ll):
    r_s = H.beam_coincidence_nats(c_, -1, ts, L, False, 12, logf, abort_at, a_ll)
    r_n = N.beam_coincidence_nats_numba(c_, -1, ts, L, False, 12, logf, abort_at, a_ll)
    if (r_s is None) != (r_n is None):
        print(f"FAIL {label}: abort mismatch slow={r_s is None} nb={r_n is None}")
        return False
    if r_s is None:
        print(f"ok   {label}: both abort")
        return True
    ps, ss = r_s
    pn, sn = r_n
    ok = ps == pn and abs(ss - sn) <= 1e-6
    print(f"{'ok  ' if ok else 'FAIL'} {label}: ptr_eq={ps == pn} "
          f"score {ss:.6f} vs {sn:.6f} d={ss-sn:.2e}")
    if not ok and ps != pn:
        for i in range(min(len(ps), len(pn))):
            if ps[i] != pn[i]:
                print(f"     first ptr diff at {i}: slow {ps[i]} nb {pn[i]}")
                break
    return ok


allok = True
for desc, off, L in [("truth", 1234, 8), ("wrongoff", 1000, 8), ("wrongL7", 1234, 7),
                     ("wrongL9", 1234, 9), ("wrongL16", 1234, 16), ("L1", 1234, 1),
                     ("L20", 1500, 20)]:
    ts = tvals[off:off + 407]
    a_ll = 120 * (uni + 0.9) + L * math.log(29)
    allok &= check(desc + " a0", c, ts, L, 0, 0.0)
    allok &= check(desc + " a120", c, ts, L, 120, a_ll)

rng = random.Random(123)
for k in range(8):
    ws = H.random_stream(3400, 3000 + k)
    wc = [rng.randrange(29) for _ in range(300)]
    off = rng.randrange(1800)
    L = (2, 8, 12, 16, 20, 8, 3, 5)[k]
    a_ll = 120 * (uni + 0.9) + L * math.log(29)
    allok &= check(f"null{k} L={L} a120", wc, ws[off:off + 407], L, 120, a_ll)

# timing
ts = tvals[1234:1234 + 407]
H.beam_coincidence_nats(c, -1, ts, 8, False, 12, logf, 0, 0.0)
N.beam_coincidence_nats_numba(c, -1, ts, 8, False, 12, logf, 0, 0.0)
t0 = time.perf_counter()
for _ in range(5):
    H.beam_coincidence_nats(c, -1, ts, 8, False, 12, logf, 0, 0.0)
t_s = (time.perf_counter() - t0) / 5
t0 = time.perf_counter()
for _ in range(40):
    N.beam_coincidence_nats_numba(c, -1, ts, 8, False, 12, logf, 0, 0.0)
t_n = (time.perf_counter() - t0) / 40
print(f"timing init truth: slow {t_s*1000:.1f} ms, numba {t_n*1000:.2f} ms, "
      f"speedup {t_s/t_n:.1f}x")

wc = [rng.randrange(29) for _ in range(300)]
a_ll = 120 * (uni + 0.9) + 8 * math.log(29)
t0 = time.perf_counter()
for _ in range(5):
    H.beam_coincidence_nats(wc, -1, tvals[0:407], 8, False, 12, logf, 120, a_ll)
t_s = (time.perf_counter() - t0) / 5
t0 = time.perf_counter()
for _ in range(100):
    N.beam_coincidence_nats_numba(wc, -1, tvals[0:407], 8, False, 12, logf, 120, a_ll)
t_n = (time.perf_counter() - t0) / 100
print(f"timing init null (aborts at 120): slow {t_s*1000:.1f} ms, numba {t_n*1000:.2f} ms, "
      f"speedup {t_s/t_n:.1f}x")

print("NB QUICK RESULT:", "PASS" if allok else "FAIL")
