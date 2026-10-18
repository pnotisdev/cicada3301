"""Quick v3-fix sanity check: slow vs fast init on truth cell and null cells (scratch)."""
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


def check(label, c_, ts, L, abort_at, a_ll):
    r_s = H.beam_coincidence_nats(c_, -1, ts, L, False, 12, logf, abort_at, a_ll)
    r_f = H.beam_coincidence_nats_fast(c_, -1, ts, L, False, 12, logf, abort_at, a_ll)
    if (r_s is None) != (r_f is None):
        print(f"FAIL {label}: abort mismatch slow={r_s is None} fast={r_f is None}")
        return False
    if r_s is None:
        print(f"ok   {label}: both abort")
        return True
    ps, ss = r_s
    pf, sf = r_f
    ok = ps == pf and abs(ss - sf) <= 1e-6
    print(f"{'ok  ' if ok else 'FAIL'} {label}: ptr_eq={ps == pf} skips_s={sum(ps[i]-ps[i-1]-1 for i in range(1,len(ps)))} "
          f"score {ss:.6f} vs {sf:.6f} d={ss-sf:.2e}")
    if not ok:
        for i in range(min(len(ps), len(pf))):
            if ps[i] != pf[i]:
                print(f"     first ptr diff at {i}: slow {ps[i]} fast {pf[i]}")
                break
    return ok


allok = True
for desc, off, L in [("truth", 1234, 8), ("wrongoff", 1000, 8), ("wrongL7", 1234, 7),
                     ("wrongL16", 1234, 16)]:
    ts = tvals[off:off + 407]
    a_ll = 120 * (uni + 0.9) + L * math.log(29)
    allok &= check(desc + " a0", c, ts, L, 0, 0.0)
    allok &= check(desc + " a120", c, ts, L, 120, a_ll)

rng = random.Random(123)
for k in range(6):
    ws = H.random_stream(3400, 3000 + k)
    wc = [rng.randrange(29) for _ in range(300)]
    off = rng.randrange(1800)
    L = (2, 8, 12, 16, 20, 8)[k]
    a_ll = 120 * (uni + 0.9) + L * math.log(29)
    allok &= check(f"null{k} L={L} a120", wc, ws[off:off + 407], L, 120, a_ll)

print("QUICK RESULT:", "PASS" if allok else "FAIL")
