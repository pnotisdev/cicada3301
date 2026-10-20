"""Phase 23 diagnostic 4: beam path vs beam + hard-EM (exact Viterbi) path accuracy on plants."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bkd_diag import P, MT, Kb, table, d, rng
for n in (300, 729):
    for beam, h in ((24, 1), (64, 8)):
        a0, a1 = [], []
        for r in range(20):
            c, o, used, _ = d.plant(P, Kb, n, rng, table)
            _, p0 = d.beam_decode(c, Kb, o, MT, beam, d.LN_SKIP, h)
            sb, se, p1, s = d.decode(c, Kb, o, MT, beam, h)
            a0.append((p0 == o + used).mean()); a1.append((p1 == o + used).mean())
        a0, a1 = np.array(a0), np.array(a1)
        print(f"n {n} beam {beam} per_ptr {h}: beam acc {a0.mean():.3f} (<0.5: {(a0 < .5).sum()}/20)  EM acc {a1.mean():.3f} "
              f"(<0.5: {(a1 < .5).sum()}/20, >0.95: {(a1 > .95).sum()}/20)", flush=True)
