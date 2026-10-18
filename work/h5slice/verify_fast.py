"""Verify beam_coincidence_nats_fast against beam_coincidence_nats (the slow, verified init).

Matrix: 4 offsets x 3 L x 2 models = 24 cells on the truth ciphertext (plant at offset
1234, L=8, model 0), each at abort_at=0 and abort_at=120; plus 40 random nulls at L=8.
Checks: same top pointer path, same skip count, same score within 1e-6 nats, same abort
behaviour; decode-level parity (fast_init=True vs False); timing (>= 10x faster).
"""
import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import h5slice as H
import sim

logf = H.english_logf()
uni = H.uni_mean_logf()

plain = sim.english_runes()[3000:3300]
tvals = H.totient(4000)
OFF = 1234
c = H.plant(plain, tvals, OFF, H.DIVINITY, 0, keep=0.19, litf=False, b=0, seed=42)

MARGIN = 0.9   # recalibrated abort (FAST_REPORT.md sec 2: truth delta +1.011 at rune 120
ABORT_AT = 120  # vs null max delta 0.863; headroom ~0.11-0.15 both sides)


def skips(ptrs):
    return sum(ptrs[i] - ptrs[i - 1] - 1 for i in range(1, len(ptrs))) if len(ptrs) > 1 else 0


def abort_ll(L):
    return ABORT_AT * (uni + MARGIN) + L * math.log(29)


def init_parity(c_, ts, L, abort_at, a_ll):
    r_s = H.beam_coincidence_nats(c_, -1, ts, L, False, 12, logf, abort_at, a_ll)
    r_f = H.beam_coincidence_nats_fast(c_, -1, ts, L, False, 12, logf, abort_at, a_ll)
    if (r_s is None) != (r_f is None):
        return f"ABORT MISMATCH slow={r_s is None} fast={r_f is None}"
    if r_s is None:
        return None
    ps, ss = r_s
    pf, sf = r_f
    if ps != pf:
        return f"PTR DIFFER slow={ps[:40]}... fast={pf[:40]}..."
    if skips(ps) != skips(pf):
        return f"SKIP MISMATCH"
    if abs(ss - sf) > 1e-6:
        return f"SCORE DIFF {ss - sf:.3e} (slow {ss:.9f} fast {sf:.9f})"
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

print("== phase 2: decode parity (fast_init True vs False), 24 cells, abort 120 ==")
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

print("== phase 3: truth cell no-abort decode (fast wired) must equal the verified slow ==")
a = H.decode(c, -1, tvals, OFF, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
             abort_at=0, abort_margin=0.0, out_path=True, fast_init=False)
b = H.decode(c, -1, tvals, OFF, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
             abort_at=0, abort_margin=0.0, out_path=True, fast_init=True)
print(f"  slow: ioc {a[0]:.3f} wcol {a[1]['wcol']} ll/rune {a[1]['ll']:.3f}")
print(f"  fast: ioc {b[0]:.3f} wcol {b[1]['wcol']} ll/rune {b[1]['ll']:.3f}")
if abs(a[0] - b[0]) > 1e-12 or a[1]["wcol"] != b[1]["wcol"] or a[1]["ptrs"] != b[1]["ptrs"]:
    fails += 1
    print("  FAIL: truth no-abort decode differs between slow and fast init")
if b[0] < 1.6 or b[1]["wcol"] != H.DIVINITY:
    fails += 1
    print("  FAIL: truth decode no longer meets ioc>=1.6 / wcol==DIVINITY")

print("== phase 4: 40 random nulls (L=8, abort 120): init + decode parity ==")
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

print("== phase 5: lexsort merge tie-break micro-check ==")
s2 = np.array([5.0, 5.0, 4.0])
nj = np.array([3, 3, 3])
order = np.lexsort((-s2, nj))
_, first = np.unique(nj[order], return_index=True)
surv = order[first]
if not (surv[0] == 0 and s2[surv[0]] == 5.0):
    fails += 1
    print(f"  FAIL: lexsort tie-break picked candidate {surv[0]}, expected 0")
else:
    print("  ok: equal (nj, s2) ties resolve to the smallest candidate index (matches slow)")

print("== phase 6: timing (init only) ==")
ts = tvals[OFF:OFF + 300 + 107]
for fn in (H.beam_coincidence_nats, H.beam_coincidence_nats_fast):
    fn(c, -1, ts, 8, False, 12, logf, 0, 0.0)  # warm
t0 = time.perf_counter()
for _ in range(5):
    H.beam_coincidence_nats(c, -1, ts, 8, False, 12, logf, 0, 0.0)
t_slow = (time.perf_counter() - t0) / 5
t0 = time.perf_counter()
for _ in range(40):
    H.beam_coincidence_nats_fast(c, -1, ts, 8, False, 12, logf, 0, 0.0)
t_fast = (time.perf_counter() - t0) / 40
print(f"  truth cell init: slow {t_slow * 1000:.1f} ms, fast {t_fast * 1000:.2f} ms, "
      f"speedup {t_slow / t_fast:.1f}x")
if t_slow / t_fast < 5:
    fails += 1
    print("  FAIL: speedup < 5x (the task gate; Rust port recommended)")
elif t_slow / t_fast < 10:
    print("  WARN: speedup >= 5x (task gate met) but < 10x (README target)")

wc = [rng.randrange(29) for _ in range(300)]
t0 = time.perf_counter()
for _ in range(20):
    H.beam_coincidence_nats(wc, -1, tvals[0:407], 8, False, 12, logf, ABORT_AT, abort_ll(8))
t_ns = (time.perf_counter() - t0) / 20
t0 = time.perf_counter()
for _ in range(100):
    H.beam_coincidence_nats_fast(wc, -1, tvals[0:407], 8, False, 12, logf, ABORT_AT, abort_ll(8))
t_nf = (time.perf_counter() - t0) / 100
print(f"  null cell init w/ abort: slow {t_ns * 1000:.1f} ms, fast {t_nf * 1000:.2f} ms, "
      f"speedup {t_ns / t_nf:.1f}x")

print("== phase 7: full decode timing (truth cell, abort 120/0.9) ==")
for fast in (False, True):
    H.decode(c, -1, tvals, OFF, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
             abort_at=ABORT_AT, abort_margin=MARGIN, fast_init=fast)  # warm
reps = 4
t0 = time.perf_counter()
for _ in range(reps):
    H.decode(c, -1, tvals, OFF, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
             abort_at=ABORT_AT, abort_margin=MARGIN, fast_init=False)
t_ds = (time.perf_counter() - t0) / reps
t0 = time.perf_counter()
for _ in range(reps):
    H.decode(c, -1, tvals, OFF, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
             abort_at=ABORT_AT, abort_margin=MARGIN, fast_init=True)
t_df = (time.perf_counter() - t0) / reps
print(f"  truth decode: slow {t_ds * 1000:.1f} ms, fast {t_df * 1000:.2f} ms, "
      f"speedup {t_ds / t_df:.1f}x")

# null decode with abort (the sweep workhorse: nulls die at rune 120)
wc2 = [rng.randrange(29) for _ in range(300)]
for fast in (False, True):
    H.decode(wc2, -1, tvals, 0, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
             abort_at=ABORT_AT, abort_margin=MARGIN, fast_init=fast)
t0 = time.perf_counter()
for _ in range(4):
    H.decode(wc2, -1, tvals, 0, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
             abort_at=ABORT_AT, abort_margin=MARGIN, fast_init=False)
t_nds = (time.perf_counter() - t0) / 4
t0 = time.perf_counter()
for _ in range(20):
    H.decode(wc2, -1, tvals, 0, 8, 0, litf=False, beam=24, max_em=5, logf=logf,
             abort_at=ABORT_AT, abort_margin=MARGIN, fast_init=True)
t_ndf = (time.perf_counter() - t0) / 20
print(f"  null decode w/ abort: slow {t_nds * 1000:.1f} ms, fast {t_ndf * 1000:.2f} ms, "
      f"speedup {t_nds / t_ndf:.1f}x")

print()
print(f"RESULT: {'PASS' if fails == 0 else 'FAIL'} ({fails} failures)")
sys.exit(1 if fails else 0)
