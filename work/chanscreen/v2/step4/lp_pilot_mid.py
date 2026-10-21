"""Phase 51 ONE-window LP2 pilot of the mid-word arc (not the campaign): section 0.7 @ 0 (300 runes) against the full library, hold/spend/skip5/coin, both signs, every offset,
word-start flags from the page-safe LP2 mask of lp_mask.py, decoder nu = 0.42. Any cell >= 10 is recomputed in a fresh call and scored against the base engine (+-3 offsets, 4 channels).
Below-normal priority. python -B lp_pilot_mid.py run [--workers 4] | summary"""
import argparse, concurrent.futures as cf, json, math, os, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import plant_mid as X
import lp_mask as LM
import numpy as np
P, C = X.P, X.C
DEST = C.OUT / 'mid_lp_pilot'
SEC, START, N = 7, 0, 300
_W = {}


def lower():
    if os.name == 'nt':
        import ctypes
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)   # BELOW_NORMAL


def init():
    lower()
    _W['lib'] = C.read_library()
    _W['pi'], _W['L'] = C.model()
    runes, brk = LM.section_edges(SEC)
    _W['c'] = [int(x) for x in runes[START:START + N]]
    _W['ws'] = [1] + [1 if brk[START + i] else 0 for i in range(1, N)]
    _W['chunks'] = C.chunks([len(v) for _, v in _W['lib']])


def task(ci):
    dest = DEST / f'mid_c{ci:02d}.json'
    if dest.exists():
        return dest.name, 0.0
    t0 = time.perf_counter()
    c, mk = _W['c'], dict(wstart=_W['ws'])
    lo, hi = _W['chunks'][ci]
    logW = C.log_common(c, C.Q_DECODER, C.Q)
    pi, L = _W['pi'], _W['L']
    best = (-math.inf, None)
    cnt = {t: 0 for t in (0, 5, 10, 20)}
    cells, hits = 0, []
    for si in range(lo, hi):
        name, key = _W['lib'][si]
        for sign in C.SIGNS:
            for pc in C.CHANNELS:
                sg = X.guard(c, key, sign, pc, pi, L, logW, 'mid', mk, X.RHO)
                cells += len(sg)
                for t in cnt:
                    cnt[t] += int(np.count_nonzero(sg >= t))
                k = int(np.argmax(sg))
                if sg[k] > best[0]:
                    best = (float(sg[k]), dict(stream=si, name=name, sign=sign, channel=pc, offset=k))
                for o in np.flatnonzero(sg >= 10):
                    o = int(o)
                    sg2 = X.guard(c, key, sign, pc, pi, L, logW, 'mid', mk, X.RHO)
                    bs = max(float(np.max(X.guard(c, key, sign, bc, pi, L, logW, 'base', {}, 0.0)[max(0, o - 3):o + 4])) for bc in C.CHANNELS)
                    hits.append(dict(stream=si, name=name, sign=sign, channel=pc, offset=o, score=float(sg[o]), recomputed=float(sg2[o]), base_best_pm3=bs))
    rec = dict(chunk=ci, streams=[lo, hi], cells=cells, best=best[0], argmax=best[1], counts=cnt, hits=hits, seconds=time.perf_counter() - t0)
    X._save(dest, rec)
    return dest.name, rec['seconds']


def summary():
    recs = [json.loads(p.read_text()) for p in sorted(DEST.glob('*.json'))]
    b = max(recs, key=lambda r: r['best'])
    L = [f'# Phase 51 mid-word arc, LP2 pilot: section 0.7 @ 0, 300 runes, {len(recs)} tasks, {sum(r["cells"] for r in recs):,} cells, T300 = {C.T300:.4f}',
         f'max S_guard {b["best"]:.2f} ({b["argmax"]}); ' + ', '.join(f'>= {t}: {sum(r["counts"][str(t)] for r in recs)}' for t in (0, 5, 10, 20)) + f'; hits >= 10: {sum(len(r["hits"]) for r in recs)}']
    for r in recs:
        for h in r['hits']:
            L.append(f'   {h}')
    (C.OUT / 'mid_lp_pilot_summary.txt').write_text('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=('run', 'summary')); ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()
    if a.cmd == 'summary':
        summary()
    else:
        nch = len(C.chunks([len(v) for _, v in C.read_library()]))
        todo = [ci for ci in range(nch) if not (DEST / f'mid_c{ci:02d}.json').exists()]
        print(len(todo), 'tasks', flush=True)
        with cf.ProcessPoolExecutor(max_workers=a.workers, initializer=init) as ex:
            for n, f in enumerate(cf.as_completed([ex.submit(task, ci) for ci in todo]), 1):
                print(f'[{time.strftime("%H:%M:%S")}] {n}/{len(todo)} {f.result()}', flush=True)
