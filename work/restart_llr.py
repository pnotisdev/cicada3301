"""Key-restart test with the full plaintext-difference likelihood ratio (more powerful than equal-pair counting).

restart_columns.py counts equal pairs in each column of "unit start + j" runes. If all units share a key from their
start, any two runes of a column differ by a plaintext difference p - p' with distribution Q(d) = sum_x f(x) f(x-d)
(English letter frequencies f), and Q is far from uniform at many d, not just d = 0. The log-likelihood-ratio
statistic T_j = sum over pairs w(c_u - c_v), w(d) = log(29 Q(d)), uses all of that: about 4x more information per pair
than counting equal runes (KL(Q||uniform) 0.04 nats against 0.009 for the equality indicator). That matters most for
the unit types with few units (9 sections, 16 paragraphs).

z_j = (T_j - E0)/sd0 with E0, sd0 from Monte Carlo draws of n_j runes from LP2's own rune distribution (the null that
all runes are independent). Z_sum = sum_{j<J0} z_j / sqrt(J0). Positive control: English (Emerson) enciphered with one
random key restarted at every unit under the skip rule, using LP2's real unit lengths.

    python work/restart_llr.py                  # -> results/analysis/restart_llr.txt
"""
import os
import random
import sys

import numpy as np

import lp
import sim
import stats
from restart_columns import units_of, simulate_units

N = lp.N
HERE = os.path.dirname(os.path.abspath(__file__))
J = 60
J0 = 20
MC = 2000


def make_wm():
    f = np.bincount(sim.english_runes(), minlength=N).astype(float)
    f /= f.sum()
    q = np.array([sum(f[x] * f[(x - d) % N] for x in range(N)) for d in range(N)])
    w = np.log(N * q)
    return np.array([[w[(x - y) % N] for y in range(N)] for x in range(N)]), w


WM, W = make_wm()


def stat_T(col):
    n = np.bincount(col, minlength=N).astype(float)
    return 0.5 * (n @ WM @ n - n.sum() * WM[0, 0])


def column_z(units, freq, rng, reverse=False, nj=J):
    zs = []
    for j in range(nj):
        col = np.array([(u[::-1] if reverse else u)[j] for u in units if len(u) > j], dtype=int)
        n = len(col)
        if n < 4:
            zs.append(0.0)
            continue
        sims = np.array([stat_T(rng.choice(N, size=n, p=freq)) for _ in range(MC)])
        zs.append((stat_T(col) - sims.mean()) / (sims.std() + 1e-12))
    return np.array(zs)


def summ(z):
    return float(z.max()), float(z[:J0].sum() / np.sqrt(J0))


def main():
    segs = stats.SEGS
    idxs = list(stats.UNSOLVED)
    allr = np.array([x for i in idxs for x in lp.runes_of(segs[i])])
    freq = np.bincount(allr, minlength=N) / len(allr)
    eng = sim.english_runes()
    rng = np.random.default_rng(3)
    prng = random.Random(21)
    out = []
    P = out.append
    P(f"LP2: {len(allr)} runes. Log-likelihood-ratio column test, first {J} columns, Z_sum over the first {J0}.")
    P(f"{'unit':10s} {'n':>5s} {'dir':>5s} {'max z':>6s} {'Z_sum':>6s}   control (restart): Z_sum mean / min over 6    "
      f"null (continuous key): max z over 6 / |Z_sum| max")
    for kind in ("segment", "paragraph", "page", "sentence"):    # lines: see restart_columns.py (594 units, control Z ~170)
        units = units_of(kind, segs, idxs)
        lengths = [len(u) for u in units]
        for rev in (False, True):
            z = column_z(units, freq, rng, reverse=rev)
            mx, zs = summ(z)
            c_rst, c_null_mx, c_null_zs = [], [], []
            reps = 6
            for r in range(reps):
                st = 1000 + (31000 * r) % 200000
                u1 = simulate_units(lengths, True, eng, prng, start=st, backward=rev)
                f1 = np.bincount([x for u in u1 for x in u], minlength=N) / sum(lengths)
                c_rst.append(summ(column_z(u1, f1, rng, reverse=rev))[1])
                u0 = simulate_units(lengths, False, eng, prng, start=st, backward=rev)
                f0 = np.bincount([x for u in u0 for x in u], minlength=N) / sum(lengths)
                a, b = summ(column_z(u0, f0, rng, reverse=rev))
                c_null_mx.append(a)
                c_null_zs.append(abs(b))
            line = (f"{kind:10s} {len(units):5d} {'end' if rev else 'start':>5s} {mx:6.2f} {zs:6.2f}   "
                    f"{np.mean(c_rst):9.1f} / {np.min(c_rst):7.1f}   {max(c_null_mx):12.2f} / {max(c_null_zs):6.2f}")
            P(line)
            print(line, flush=True)
    P("")
    P("Reading: a restart would give Z_sum like the control column. LP2 shows nothing at any unit type. For the 9 sections "
      "the control Z_sum shows how much power the test has (equal-pair counting gave ~2.5 in restart_columns.py).")
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "restart_llr.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    sys.exit(main())
