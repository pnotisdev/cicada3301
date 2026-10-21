"""Phase 24: measured cost of one n300 window pass of the edge arc vs the base engine (single core, process CPU time (not wall: the PC is shared), 3 repetitions after a warmup).
    python -B cost.py      -> results/chanscreen/edge/cost.json
Synthetic inputs only (a plant window, LP2-like candidate density 1 per word, and the worst case: every position a candidate).
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import plant_edge as P  # noqa: E402
import numpy as np  # noqa: E402
from engine import all_offsets  # noqa: E402
from engine_edge import all_offsets_edge  # noqa: E402

P._init()
pi, L = P._G['pi'], P._G['L']
q0 = 0.81
pl = P.make_plant('nullf', 'm04', 'cicada', 3, P._G['pool']['cicada'], P._G['words'], P._G['lib'], 0.8)
c = pl['cipher']
cand_word = pl['cand']
cand_all = [1] * len(c)
rng = np.random.default_rng(24)
rows = []
for m in (2000, 20000, 100):
    key = rng.integers(0, 29, size=m).astype(np.int32)
    for ch in ('hold', 'spend', 'skip5', 'coin'):
        cases = [('base', None), ('null@words', (1, cand_word)), ('adv@words', (2, cand_word))]
        if m == 100 and ch == 'hold':
            cases.append(('null@all', (1, cand_all)))   # dmax = 299 trailing-null states: only measured at m = 100, not usable at scale
        if m == 100 and ch != 'hold':
            continue
        for name, spec in cases:
            def run():
                if spec is None:
                    return all_offsets(c, key, 1, q0, ch, pi, L)
                return all_offsets_edge(c, key, 1, q0, ch, pi, L, spec[0], spec[1], 0.42)
            run()
            ts = []
            for _ in range(3):
                t0 = time.process_time()
                run()
                ts.append(time.process_time() - t0)
            med = sorted(ts)[1]
            rows.append(dict(m=m, channel=ch, variant=name, seconds=ts, median=med, us_per_offset=med / m * 1e6))
            print(f'm={m:6d} {ch:6s} {name:10s} {med:8.3f}s  {med / m * 1e6:7.2f} us/offset', flush=True)
(P.DEST).mkdir(parents=True, exist_ok=True)
(P.DEST / 'cost.json').write_text(json.dumps(rows, indent=1))
