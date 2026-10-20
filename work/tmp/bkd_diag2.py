"""Phase 23 diagnostic 2: beam width x histories per pointer -> path accuracy and search errors (truth outscoring beam)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bkd_diag import P, MT, Kb, table, d, path_score, rng
for n in (300, 729):
    for beam, h in ((24, 1), (64, 8), (256, 16), (1024, 32)):
        acc, err = [], 0
        for r in range(16):
            c, o, used, _ = d.plant(P, Kb, n, rng, table)
            s, path = d.beam_decode(c, Kb, o, MT, beam, d.LN_SKIP, h)
            acc.append((path == o + used).mean())
            err += path_score(c, Kb, o + used, MT) > s + 1e-6
        print(f"n {n} beam {beam:4d} per_ptr {h:2d}: acc mean {np.mean(acc):.3f} min {np.min(acc):.3f} <0.5: {sum(a < 0.5 for a in acc)}/16 search errors {err}/16", flush=True)
