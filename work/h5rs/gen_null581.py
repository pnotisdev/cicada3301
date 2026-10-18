"""Generate the null-size justification asset: null581.ksb = 581 uniform replicate
streams (h5rs splitmix64, seeds 9000..9580 inclusive, 2407 values each - the REAL
campaign size for the per-window matched-null maximum, task 2 of the pre-launch review).
Reuses gen_nulls.py's bit-exact generator.

Writes work/h5rs/data/null581.ksb (~1.4 MB).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_nulls

gen_nulls.build(range(9000, 9581), os.path.join(HERE, "data", "null581.ksb"))
