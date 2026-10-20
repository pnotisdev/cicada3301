"""Phase 23 diagnostic 5: exact Viterbi with the TRUE table (upper bound) and with shifts from the TRUE path."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bkd_diag import P, MT, Kb, table, d, rng
for PERM in (False, True):
 for n in (300, 729):
        a, b, sk = [], [], []
        for r in range(20):
            c, o, used, _ = d.plant(P, Kb, n, rng, table)
            D = int(3 * n / 29)
            _, p1 = d.viterbi_fixed(c, -1, Kb, o, table, MT, D, np.log(.81), np.log(.19))
            s_hat = d.shifts_of(c, Kb, o + used, MT, perm=PERM)
            _, p2 = d.viterbi_fixed(c, -1, Kb, o, s_hat, MT, D, np.log(.81), np.log(.19))
            a.append((p1 == o + used).mean()); b.append((p2 == o + used).mean()); sk.append((s_hat == table).mean())
        print(f"perm {PERM} n {n}: true-table Viterbi acc {np.mean(a):.3f} min {np.min(a):.3f}; shifts-from-truth acc {np.mean(b):.3f} "
              f"min {np.min(b):.3f} (shift agreement {np.mean(sk):.2f})")
