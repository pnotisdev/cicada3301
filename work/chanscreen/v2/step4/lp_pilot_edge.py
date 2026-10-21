"""Phase 24 ONE-window LP2 pilot of the edge arc (not the campaign): window 0.7 @ 0 (300 runes) against the full library, kinds nullf / nulli / adv,
channels hold/spend/skip5/coin, both signs, every offset, with the page-safe LP2 word-edge mask of lp_mask.py and the pre-registered hit rule of hit_rule.py
(any cell >= 10 nats is recomputed in a fresh call, scored against the base engine on the same stream and sign (all four base channels, +-3 offsets), aliases collapsed).
    python -B lp_pilot_edge.py run [--workers 2]     python -B lp_pilot_edge.py summary
"""
import argparse, concurrent.futures as cf, json, math, os, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import plant_edge as P
import lp_mask as LM
import hit_rule as H
import numpy as np
C = P.C
DEST = C.OUT / 'edge_lp_pilot'
SEC, START, N = 7, 0, 300
KINDS = ('nullf', 'nulli', 'adv')
_W = {}


def init():
    _W['lib'] = C.read_library()
    _W['pi'], _W['L'] = C.model()
    runes, _ = LM.section_edges(SEC)
    _W['c'] = [int(x) for x in runes[START:START + N]]
    fin, ini = LM.window_masks(SEC, START, N)
    _W['cand'] = {'nullf': fin, 'nulli': ini, 'adv': ini}
    _W['chunks'] = C.chunks([len(v) for _, v in _W['lib']])


def task(a):
    kind, ci = a
    dest = DEST / f'{kind}_c{ci:02d}.json'
    if dest.exists():
        return dest.name, 0.0
    t0 = time.perf_counter()
    c, cand, ek = _W['c'], _W['cand'][kind], P.KINDS[kind]
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
                sg, _ = P.guard(c, key, sign, pc, C.Q_DECODER, pi, L, logW, ek, cand, P.RHO)
                cells += len(sg)
                for t in cnt:
                    cnt[t] += int(np.count_nonzero(sg >= t))
                k = int(np.argmax(sg))
                if sg[k] > best[0]:
                    best = (float(sg[k]), dict(stream=si, name=name, sign=sign, channel=pc, offset=k))
                for o in np.flatnonzero(sg >= 10):
                    o = int(o)
                    sg2, _ = P.guard(c, key, sign, pc, C.Q_DECODER, pi, L, logW, ek, cand, P.RHO)   # fresh recomputation
                    bs = max(float(np.max(P.guard(c, key, sign, bc, C.Q_DECODER, pi, L, logW, 0, None, 0.0)[0][max(0, o - 3):o + 4])) for bc in C.CHANNELS)
                    hits.append(dict(stream=si, name=name, sign=sign, channel=pc, offset=o, score=float(sg[o]), recomputed=float(sg2[o]), base_best_pm3=bs, margin=float(sg[o]) - bs))
    rec = dict(kind=kind, chunk=ci, streams=[lo, hi], cells=cells, best=best[0], argmax=best[1], counts=cnt, hits=hits, seconds=time.perf_counter() - t0)
    DEST.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix('.tmp'); tmp.write_text(json.dumps(rec, indent=1)); os.replace(tmp, dest)
    return dest.name, rec['seconds']


def run(workers):
    lib = C.read_library()
    nch = len(C.chunks([len(v) for _, v in lib]))
    todo = [(k, ci) for k in KINDS for ci in range(nch) if not (DEST / f'{k}_c{ci:02d}.json').exists()]
    print(len(todo), 'tasks', flush=True)
    with cf.ProcessPoolExecutor(max_workers=workers, initializer=init) as ex:
        futs = [ex.submit(task, a) for a in todo]
        for n, f in enumerate(cf.as_completed(futs), 1):
            nm, dt = f.result(); print(f'[{time.strftime("%H:%M:%S")}] {n}/{len(todo)} {nm} {dt:.0f}s', flush=True)


def summary():
    recs = [json.loads(p.read_text()) for p in sorted(DEST.glob('*.json'))]
    nulls = {k: [json.loads(p.read_text())['best'] for p in sorted((C.OUT / 'edge_null').glob(f'{k}_w0_c*.json'))] for k in KINDS}
    L = [f'# Phase 24 LP2 pilot of the edge arc: window 0.{SEC}@{START} (n = {N}), {len(recs)} tasks, {sum(r["cells"] for r in recs):,} cells, T300 = {C.T300:.4f}', '']
    for k in KINDS:
        sel = [r for r in recs if r['kind'] == k]
        if not sel:
            continue
        b = max(sel, key=lambda r: r['best'])
        L.append(f'{k}: tasks {len(sel)}/14, cells {sum(r["cells"] for r in sel):,}, max S_guard {b["best"]:.2f} ({b["argmax"]}); null-scan max {max(nulls[k]):.2f}; '
                 + ', '.join(f'>= {t}: {sum(r["counts"][str(t)] for r in sel)}' for t in (0, 5, 10, 20)))
        for r in sel:
            for h in r['hits']:
                L.append(f'    hit candidate {h}')
    (C.OUT / 'edge_lp_pilot_summary.txt').write_text('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=('run', 'summary')); ap.add_argument('--workers', type=int, default=2)
    a = ap.parse_args()
    run(a.workers) if a.cmd == 'run' else summary()
