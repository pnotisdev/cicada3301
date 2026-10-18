"""Verify the numba init (h5slice_nb.beam_coincidence_nats_numba) against the slow,
verified init - the same gates the v3 rewrite passed in verify_fast.py:

  * phase 1: 48 init-parity cells (offsets {1234,1000,1500,777} x L {7,8,12} x
    models {0,1}, each at abort 0 and 120): exact pointer-list equality, same skip
    count, score within 1e-6 nats, same abort decisions;
  * phase 2: 24 decode-parity cells (decode(fast_init=True) vs False, abort 120/0.9);
  * phase 3: truth cell no-abort: IoC 1.986, wcol == DIVINITY exactly, 8 skips;
  * phase 4: 40 random nulls (L=8, abort 120/0.9): init + decode parity and 40/40
    aborts through decode(fast_init=True);
  * phase 5: timing: truth init, null init w/ abort, full truth decode, null decode
    w/ abort; the >= 5x speedup gate on the init timings.
"""
import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import h5slice as H
import h5slice_nb as N
import sim

logf = H.english_logf()
uni = H.uni_mean_logf()

plain = sim.english_runes()[3000:3300]
tvals = H.totient(4000)
OFF = 1234
c = H.plant(plain, tvals, OFF, H.DIVINITY, 0, keep=0.19, litf=False, b=0, seed=42)

MARGIN = 0.9    # recalibrated abort (FAST_REPORT.md sec 2)
ABORT_AT = 120


def skips(ptrs):
    return sum(ptrs[i] - ptrs[i - 1] - 1 for i in range(1, len(ptrs))) if len(ptrs) > 1 else 0


def abort_ll(L):
    return ABORT_AT * (uni + MARGIN) + L * math.log(29)


def init_parity(c_, ts, L, abort_at, a_ll):
    r_s = H.beam_coincidence_nats(c_, -1, ts, L, False, 12, logf, abort_at, a_ll)
    r_n = N.beam_coincidence_nats_numba(c_, -1, ts, L, False, 12, logf, abort_at, a_ll)
    if (r_s is None) != (r_n is None):
        return f"ABORT MISMATCH slow={r_s is None} nb={r_n is None}"
    if r_s is None:
        return None
    ps, ss = r_s
    pn, sn = r_n
    if ps != pn:
        i = next((i for i in range(min(len(ps), len(pn))) if ps[i] != pn[i]), -1)
        return f"PTR DIFFER at {i}: slow {ps[i] if i >= 0 else ps[:10]} nb {pn[i] if i >= 0 else pn[:10]}"
    if skips(ps) != skips(pn):
        return "SKIP MISMATCH"
    if abs(ss - sn) > 1e-6:
        return f"SCORE DIFF {ss - sn:.3e} (slow {ss:.9f} nb {sn:.9f})"
    return None


fails = 0
checks = 0
print("== phase 1: init parity, 24 cells x {abort 0, 120} ==")
for off in (1234, 1000, 1500, 777):
    for L in (7, 8, 12):
        for model in (0, 1):
            ts = tvals[off:off + 300 + 107]
            for abort_at, a_ll in ((0, 0.0), (ABORT_AT, abort_ll(L))):
                err = init_parity(c, ts, L, abort_at, a_ll)
                checks += 1
                if err:
                    fails += 1
                    print(f"  FAIL ({off},{L},m{model},abort={abort_at}): {err}")
print(f"  init parity: {checks} checks, {fails} fails")

print("== phase 2: decode parity (fast_init True -> numba, vs False), 24 cells, abort 120 ==")
d_checks = 0
for off in (1234, 1000, 1500, 777):
    for L in (7, 8, 12):
        for model in (0, 1):
            a = H.decode(c, -1, tvals, off, L, model, litf=False, beam=24, max_em=5, logf=logf,
                         abort_at=ABORT_AT, abort_margin=MARGIN, fast_init=False)
            b = H.decode(c, -1, tvals, off, L, model, litf=False, beam=24, max_em=5, logf=logf,
                         abort_at=ABORT_AT, abort_margin=MARGIN, fast_init=True)
            d_checks += 1
            if (a[1] is None) != (b[1] is None) or abs(a[0] - b[0]) > 1e-12 or a[1] != b[1]:
                fails += 1
                print(f"  FAIL decode ({off},{L},m{model}): slow={a} fast={b}")
print(f"  decode parity: {d_checks} cells, {fails} total fails so far")

print("== phase 3: truth cell no-abort decode (numba wired) must equal the verified slow ==")
a = H.decode(c, -1, tvals, OFF, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
             abort_at=0, abort_margin=0.0, out_path=True, fast_init=False)
b = H.decode(c, -1, tvals, OFF, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
             abort_at=0, abort_margin=0.0, out_path=True, fast_init=True)
print(f"  slow: ioc {a[0]:.3f} wcol {a[1]['wcol']} skips {skips(a[1]['ptrs'])} ll/rune {a[1]['ll']:.3f}")
print(f"  numba: ioc {b[0]:.3f} wcol {b[1]['wcol']} skips {skips(b[1]['ptrs'])} ll/rune {b[1]['ll']:.3f}")
if abs(a[0] - b[0]) > 1e-12 or a[1]["wcol"] != b[1]["wcol"] or a[1]["ptrs"] != b[1]["ptrs"]:
    fails += 1
    print("  FAIL: truth no-abort decode differs between slow and numba init")
if b[0] < 1.6 or b[1]["wcol"] != H.DIVINITY:
    fails += 1
    print("  FAIL: truth decode no longer meets ioc>=1.6 / wcol==DIVINITY")
if skips(b[1]["ptrs"]) != 8:
    fails += 1
    print(f"  FAIL: truth decode skips = {skips(b[1]['ptrs'])}, expected 8 (the plant's true count)")

print("== phase 4: 40 random nulls (L=8, abort 120/0.9): init + decode parity, 40/40 abort ==")
rng = random.Random(7)
n_checks = 0
aborts = 0
for k in range(40):
    ws = H.random_stream(3400, 100 + k)
    wc = [rng.randrange(29) for _ in range(300)]
    off = rng.randrange(1800)
    ts = ws[off:off + 300 + 107]
    err = init_parity(wc, ts, 8, ABORT_AT, abort_ll(8))
    n_checks += 1
    if err:
        fails += 1
        print(f"  FAIL null init k={k}: {err}")
    a = H.decode(wc, -1, ws, off, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
                 abort_at=ABORT_AT, abort_margin=MARGIN, fast_init=False)
    b = H.decode(wc, -1, ws, off, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
                 abort_at=ABORT_AT, abort_margin=MARGIN, fast_init=True)
    n_checks += 1
    if a[0] != b[0] or a[1] != b[1]:
        fails += 1
        print(f"  FAIL null decode k={k}: slow={a} fast={b}")
    if b[0] == 0.0:
        aborts += 1
print(f"  nulls: {n_checks} checks, {aborts}/40 aborted (both versions agree)")
if aborts != 40:
    fails += 1
    print("  FAIL: not 40/40 aborts at (120, 0.9)")

print("== phase 5: timing (the >= 5x gate) ==")
ts = tvals[OFF:OFF + 300 + 107]
H.beam_coincidence_nats(c, -1, ts, 8, False, 12, logf, 0, 0.0)   # warm
N.beam_coincidence_nats_numba(c, -1, ts, 8, False, 12, logf, 0, 0.0)


def timeit(fn, reps):
    best = None
    for _ in range(3):
        t0 = time.perf_counter()
        for _ in range(reps):
            fn()
        el = (time.perf_counter() - t0) / reps
        best = el if best is None else min(best, el)
    return best


t_s = timeit(lambda: H.beam_coincidence_nats(c, -1, ts, 8, False, 12, logf, 0, 0.0), 5)
t_n = timeit(lambda: N.beam_coincidence_nats_numba(c, -1, ts, 8, False, 12, logf, 0, 0.0), 40)
print(f"  truth cell init (300 runes): slow {t_s*1000:.1f} ms, numba {t_n*1000:.2f} ms, "
      f"speedup {t_s/t_n:.1f}x")
sp1 = t_s / t_n

wc = [rng.randrange(29) for _ in range(300)]
t_s = timeit(lambda: H.beam_coincidence_nats(wc, -1, tvals[0:407], 8, False, 12, logf,
                                             ABORT_AT, abort_ll(8)), 10)
t_n = timeit(lambda: N.beam_coincidence_nats_numba(wc, -1, tvals[0:407], 8, False, 12, logf,
                                                   ABORT_AT, abort_ll(8)), 100)
print(f"  null cell init w/ abort (120 runes): slow {t_s*1000:.1f} ms, numba {t_n*1000:.2f} ms, "
      f"speedup {t_s/t_n:.1f}x")
sp2 = t_s / t_n

print("  -- full decode timings (reported for the task; the gate is on the init above) --")
t_s = timeit(lambda: H.decode(c, -1, tvals, OFF, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
                              abort_at=ABORT_AT, abort_margin=MARGIN, fast_init=False), 4)
t_n = timeit(lambda: H.decode(c, -1, tvals, OFF, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
                              abort_at=ABORT_AT, abort_margin=MARGIN, fast_init=True), 8)
print(f"  truth full decode: slow {t_s*1000:.1f} ms, numba {t_n*1000:.2f} ms, "
      f"speedup {t_s/t_n:.1f}x")
sp3 = t_s / t_n

wc2 = [rng.randrange(29) for _ in range(300)]
t_s = timeit(lambda: H.decode(wc2, -1, tvals, 0, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
                              abort_at=ABORT_AT, abort_margin=MARGIN, fast_init=False), 4)
t_n = timeit(lambda: H.decode(wc2, -1, tvals, 0, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
                              abort_at=ABORT_AT, abort_margin=MARGIN, fast_init=True), 20)
print(f"  null decode w/ abort: slow {t_s*1000:.1f} ms, numba {t_n*1000:.2f} ms, "
      f"speedup {t_s/t_n:.1f}x")
sp4 = t_s / t_n

if sp1 < 5 or sp2 < 5:
    fails += 1
    print(f"  FAIL: init speedup < 5x (truth {sp1:.1f}x, null {sp2:.1f}x) - "
          f"per the task STOP here and recommend the Rust port")
if sp3 < 5 or sp4 < 5:
    print(f"  WARN: a full-decode speedup is below 5x (truth {sp3:.1f}x, null {sp4:.1f}x); "
          f"the task's 5x gate is on the init, the sweep workhorse is the null w/ abort")

print()
print(f"RESULT: {'PASS' if fails == 0 else 'FAIL'} ({fails} failures)")
sys.exit(1 if fails else 0)
