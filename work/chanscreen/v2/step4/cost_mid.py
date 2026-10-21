"""Phase 51: measured cost of one n300 window pass of the mid-word arc vs the base engine and the edge arc (single core, process CPU time, median of 3 after a warmup).
    python -B cost_mid.py      -> results/chanscreen/mid/cost.json
Synthetic keys, a plant window (LP2 word lengths), m = 20,000 / 2,000; per sign and channel, microseconds per offset. Run while other jobs load the PC (numbers are CPU time, not wall).
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import plant_mid as X  # noqa: E402
import numpy as np  # noqa: E402
P = X.P
P._init()
pi, L = P._G['pi'], P._G['L']
pl = X.make_plant('m04', 'cicada', 3, P._G['pool']['cicada'], P._G['words'], P._G['lib'], 0.8)
c = pl['cipher']
mk = X.masks(pl, 300)
rng = np.random.default_rng(51)
rows = []
for m in (20000, 2000):
    key = rng.integers(0, 29, size=m).astype(np.int32)
    for ch in ('hold', 'spend', 'skip5', 'coin'):
        for dec in ('base', 'nullf', 'mid'):
            def run():
                return X.all_offsets_mid(c, key, 1, 0.81, ch, pi, L, X.DECODERS[dec], nu=0.0 if dec == 'base' else 0.42, **mk[dec])
            run()
            ts = []
            for _ in range(3):
                t0 = time.process_time()
                run()
                ts.append(time.process_time() - t0)
            med = sorted(ts)[1]
            rows.append(dict(m=m, channel=ch, decoder=dec, seconds=ts, median=med, us_per_offset=med / m * 1e6))
            print(f'm={m:6d} {ch:6s} {dec:6s} {med:8.3f}s  {med / m * 1e6:7.2f} us/offset', flush=True)
X.DEST.mkdir(parents=True, exist_ok=True)
(X.DEST / 'cost.json').write_text(json.dumps(rows, indent=1))
for dec in ('base', 'nullf', 'mid'):
    tot = sum(r['us_per_offset'] for r in rows if r['m'] == 20000 and r['decoder'] == dec)
    print(f'{dec}: sum over 4 channels {tot:.0f} us per offset per sign')
