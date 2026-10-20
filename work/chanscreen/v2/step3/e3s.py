"""Step3 E3' sanity null: v1 calibration windows (wrong-key Cicada-iid ciphertext) against the
FULL 1,439-stream library, four channels x two signs x every offset, scored with S_guard.

Commands (repository root, python -B):
  e3s.py prep                      regenerate cal windows 0..4, check against stored v1 inputs
  e3s.py run WINDOW BUDGET_SEC     resumable; <=4 workers; write-once block checkpoints
  e3s.py summary                   per-window maxima, T check, alias-collapsed exceedance counts
No LP2 ciphertext is read. T300 is the frozen step2 value, unchanged.
"""
import os
for x in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[x] = '1'
import sys
sys.dont_write_bytecode = True
from pathlib import Path
HERE = Path(__file__).resolve().parent
V2 = HERE.parent
V1 = V2.parent
ROOT = V1.parent.parent
sys.path[:0] = [str(V2), str(V2 / 'step2' / 'followup'), str(V1), str(ROOT / 'work' / 'm04'), str(ROOT / 'work')]
import json, math, random, time
import concurrent.futures as CF
import numpy as np

CH = ('hold', 'spend', 'skip5', 'coin')
Q = 29
QDEC = .81
BLOCK = 48
K_ALIAS = 15  # frozen before any LP2 scoring: the saved aliases all lie within +-15
TS = (0, 5, 10)
T300 = 29.799206297530528


def windows():
    import run_baseline as B
    import m04 as M
    qf = json.loads((V1 / 'frozen.json').read_text())['q']
    out = {}
    for i in range(5):
        rng = random.Random(B.seed_of('cal', 'cicada', 'iid', i))
        plain, start = B.window('train', 'cicada', rng)
        drawn = [M.draw_stream(rng, 'iid') for _ in range(8)]
        ti, off = rng.randrange(8), rng.randrange(M.OFFSETS)
        cipher, _, _ = B.encrypt('m04', plain, drawn[ti][1], off, qf['m04|cicada|iid'], rng)
        out[i] = [int(v) for v in cipher]
    return out


def prep():
    w = windows()
    d = np.load(V1 / 'gpu_parity.npz')
    pool = {tuple(int(v) for v in r[:n]) for r, n in zip(d['cipher'], d['n']) if n == 300}
    found = {i: tuple(c) in pool for i, c in w.items()}
    assert all(len(c) == 300 for c in w.values())
    with (HERE / 'windows.json').open('x', encoding='utf-8', newline='\n') as f:
        json.dump(dict(windows=w, found_in_v1_stored_inputs=found), f)
    print('prep', found)


def library():
    import m04 as M
    lib = M.read_ksb(ROOT / 'work' / 'kscreen' / 'data' / 'library.ksb')
    assert len(lib) == 1439
    return [list(k) for _, k in lib]


def work(args):
    wi, b = args
    from engine import all_offsets
    from guard import guarded
    dest = HERE / 'blocks' / f'w{wi}_b{b:03d}.json'
    if dest.exists():
        return 0.
    t0 = time.perf_counter()
    c = json.loads((HERE / 'windows.json').read_text())['windows'][str(wi)]
    model = np.load(V1 / 'model.npz')
    lib = library()[b * BLOCK:(b + 1) * BLOCK]
    rows = []
    for si, key in enumerate(lib, b * BLOCK):
        for ch in CH:
            for sign in (-1, 1):
                o = all_offsets(c, key, sign, QDEC, ch, model['pi'], model['L'])
                l, u = o[:, 0], o[:, 1]
                ok = np.isfinite(u)
                s = np.full(len(o), -math.inf)
                s[ok] = l[ok] - u[ok]
                g, _ = guarded(l, u, c, QDEC, Q)
                fin = np.isfinite(g)
                rows.append(dict(stream=si, channel=ch, sign=sign, m=len(key),
                                 max_S=float(np.max(s)) if np.isfinite(s).any() else None,
                                 max_G=float(np.max(g)) if fin.any() else None,
                                 argmax_G=int(np.argmax(g)) if fin.any() else None,
                                 hits={str(t): [int(x) for x in np.flatnonzero(g >= t)] for t in TS}))
    dest.parent.mkdir(exist_ok=True)
    with dest.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(dict(window=wi, block=b, seconds=time.perf_counter() - t0, rows=rows), f, allow_nan=False)
    return time.perf_counter() - t0


def run(wi, budget):
    nb = math.ceil(1439 / BLOCK)
    todo = [(wi, b) for b in range(nb) if not (HERE / 'blocks' / f'w{wi}_b{b:03d}.json').exists()]
    t0 = time.time()
    done = 0
    with CF.ProcessPoolExecutor(max_workers=4) as ex:
        it = iter(todo)
        pend = set()
        while True:
            while len(pend) < 4 and time.time() - t0 < budget:
                try:
                    pend.add(ex.submit(work, next(it)))
                except StopIteration:
                    break
            if not pend:
                break
            fin, pend = CF.wait(pend, return_when=CF.FIRST_COMPLETED)
            for f in fin:
                f.result()
                done += 1
    print(f'window {wi}: ran {done} blocks, {len(todo) - done} left, {time.time() - t0:.0f}s', flush=True)


def collapse(idx, k=K_ALIAS):
    n, last = 0, None
    for x in sorted(idx):
        if last is None or x - last > k:
            n += 1
        last = x
    return n


def summary():
    thr = json.loads((V2 / 'step2' / 'thresholds.json').read_text())['inventory']['300']
    assert thr['T_nats'] == T300
    res = {}
    for wi in range(5):
        files = sorted((HERE / 'blocks').glob(f'w{wi}_b*.json'))
        rows = [r for f in files for r in json.loads(f.read_text())['rows']]
        if not rows:
            continue
        best = max((r for r in rows if r['max_G'] is not None), key=lambda r: r['max_G'])
        res[wi] = dict(blocks=len(files), of=math.ceil(1439 / BLOCK), streams=len({r['stream'] for r in rows}),
                       max_G=best['max_G'], max_S=max(r['max_S'] for r in rows if r['max_S'] is not None),
                       where=dict(stream=best['stream'], channel=best['channel'], sign=best['sign'], offset=best['argmax_G']),
                       below_T300=best['max_G'] < T300,
                       raw_hits={str(t): sum(len(r['hits'][str(t)]) for r in rows) for t in TS},
                       alias_classes={str(t): sum(collapse(r['hits'][str(t)]) for r in rows) for t in TS})
    out = dict(T300=T300, k_alias=K_ALIAS, windows=res)
    (HERE / 'summary.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'prep':
        prep()
    elif cmd == 'run':
        run(int(sys.argv[2]), float(sys.argv[3]))
    else:
        summary()
