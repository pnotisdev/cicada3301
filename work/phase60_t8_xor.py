"""Phase 60 T8, XOR conventions on DATA/560.13: the key-class coincidence screen of phase60_t7b_xor_classes.py (strict alignment, R4-free; power 5-8 of 8 plants without insertions, 0 of 8 with),
partitions byte & 31 (X1, X3) and byte & 127 (X2); start region = the first 30,000 offsets forwards and the last 30,000 backwards (every window), sampled = 30 blocks of 300,000 offsets forwards
(9.0 M of 118.8 M offsets, 7.6%). Hit rule fixed in advance: z >= 7.5.
    python work/phase60_t8_xor.py run [--workers N]"""
import argparse, concurrent.futures as cf, json, random, sys, time
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase60_t7b_xor_classes as T  # noqa: E402

F560 = HERE / 'ref' / 'cicados_iso' / '560.13'
N = T.N


def task(args):
    kind, d, part, lo, hi = args
    b = np.fromfile(F560, dtype=np.uint8)
    b = b[::-1] if d == 'rev' else b
    K = (b & (31 if part == 'and31' else 127)).astype(np.int32)[lo:hi + N]
    best = (-99, None)
    for wn, c in T.windows():
        z = T.zscores(c, K)
        if z.max() > best[0]:
            best = (float(z.max()), (wn, lo + int(np.argmax(z))))
    return f'{kind} {d} {part}', best, int((len(K) - N + 1) * len(T.windows()))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('--workers', type=int, default=3)
    a = ap.parse_args()
    n = F560.stat().st_size
    rng = random.Random(7560)
    pos = sorted(rng.randrange(30000, n - 300000 - 400) for _ in range(30))
    tasks = [('start', d, p, 0, 30000) for d in ('fwd', 'rev') for p in ('and31', 'and127')]
    tasks += [(f'block@{x}', 'fwd', p, x, x + 300000) for x in pos for p in ('and31', 'and127')]
    res, trials, t0 = {}, {}, time.time()
    with cf.ProcessPoolExecutor(max_workers=a.workers) as ex:
        for i, f in enumerate(cf.as_completed([ex.submit(task, t) for t in tasks]), 1):
            key, best, nt = f.result()
            k2 = key.split()[0].split('@')[0] + ' ' + ' '.join(key.split()[1:])
            if best[0] > res.get(k2, (-99, None))[0]:
                res[k2] = best
            trials[k2] = trials.get(k2, 0) + nt
            if i % 10 == 0:
                print(f'[{time.time() - t0:.0f}s] {i}/{len(tasks)}', flush=True)
    out = {k: dict(best=v, trials=trials[k]) for k, v in res.items()}
    p = HERE.parent / 'results' / 'analysis' / 'phase60_t8_560_13_xor.json'
    p.write_text(json.dumps(out))
    L = ['# Phase 60 T8: DATA/560.13 as XOR key (key-class coincidences, strict alignment, 8 section windows); hit rule z >= 7.5']
    L += [f'{k}: best z {v["best"][0]:.2f} ({v["best"][1]}), {v["trials"]:,} offset-window trials' for k, v in sorted(out.items())]
    t = chr(10).join(L) + chr(10)
    (HERE.parent / 'results' / 'analysis' / 'phase60_t8_560_13_xor.txt').write_text(t); print(t)
