"""Control: regenerated cal windows 0..4 reproduce v1's stored per-record maxima (1,024 cells each)."""
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
import e3s
from e3s import *
import run_baseline as B
import m04 as M
from engine import all_offsets

model = np.load(V1 / 'model.npz')
qf = json.loads((V1 / 'frozen.json').read_text())['q']
stored = json.loads((V1 / 'threshold.json').read_text())['null_bests']
res = []
for i in range(5):
    rng = random.Random(B.seed_of('cal', 'cicada', 'iid', i))
    plain, start = B.window('train', 'cicada', rng)
    drawn = [M.draw_stream(rng, 'iid') for _ in range(8)]
    ti, off = rng.randrange(8), rng.randrange(M.OFFSETS)
    cipher, _, _ = B.encrypt('m04', plain, drawn[ti][1], off, qf['m04|cicada|iid'], rng)
    bank = [M.draw_stream(rng, 'iid') for _ in range(8)]
    best = -1e300
    for _, key in bank:
        for sign in (-1, 1):
            for dec in CH:
                label = {'hold': 'm04'}.get(dec, dec)
                q = qf.get(f'{label}|cicada|iid', .81)
                o = all_offsets(cipher, key, sign, q, dec, model['pi'], model['L'])[:16]
                ok = np.isfinite(o[:, 1])
                if ok.any():
                    best = max(best, float(np.max(o[ok, 0] - o[ok, 1])))
    d = min(abs(best - s) for s in stored)
    res.append((i, best, d))
    print(i, best, 'nearest stored diff', d, flush=True)
assert all(d < 1e-7 for _, _, d in res), res
print('PASS: all five regenerated windows reproduce a stored v1 maximum')
