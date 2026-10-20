"""Phase 23 diagnostic 3: drift error (decoded pointer - true pointer) along failed paths."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bkd_diag import P, MT, Kb, table, d, rng
for r in range(30):
    c, o, used, _ = d.plant(P, Kb, 300, rng, table)
    s, path = d.beam_decode(c, Kb, o, MT, 64, d.LN_SKIP, 8)
    e = path - (o + used)
    if (e == 0).mean() < 0.6:
        print(f"acc {(e == 0).mean():.2f}", " ".join(f"{v:+d}" for v in e[::15]))
