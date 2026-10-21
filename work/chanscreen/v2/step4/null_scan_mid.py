"""Phase 51 E3-style null scan of the mid-word arc: a matched iid-key ciphertext window (same words / null placement / channel as the plants, key NOT in the library)
searched against the WHOLE library (1,439 streams, every offset, both signs, the four channels) with the mid-word decoder (nu = 0.42).
    python -B null_scan_mid.py run [--workers 4] [--windows 1] [--limit-chunks K]     python -B null_scan_mid.py summary
One window = 106.6M cells. Resumable: one result file per (window, chunk). Scored value S_guard as in the frozen contract; no threshold is changed.
Any cell >= 10 nats is recomputed in a fresh call (campaign hit rule).
"""
import argparse, concurrent.futures as cf, json, math, os, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import plant_mid as X
import numpy as np
P, C = X.P, X.C
DEST = C.OUT / 'mid_null'
_W = {}


def window(w):
    ch = P.PLANT_CHANNELS[w % 4]
    src = ('cicada', 'english')[(w // 4) % 2]
    q = _W['q'].get(f'{ch}|{src}|lib', 0.8)
    pl = X.make_plant(ch, src, 5000 + w, _W['pool'][src], _W['words'], _W['lib'], q, iid_key=True)
    return pl['cipher'], pl['ws'], ch, src, pl['nulls_in_window']


def init():
    _W['lib'] = C.read_library()
    _W['pi'], _W['L'] = C.model()
    _W['q'] = json.loads((C.V1 / 'frozen.json').read_text())['q']
    _W['pool'] = {s: P.B.pool('held', s) for s in ('cicada', 'english')}
    _W['words'] = P.lp_words()
    _W['chunks'] = C.chunks([len(v) for _, v in _W['lib']])


def task(a):
    w, ci = a
    dest = DEST / f'mid_w{w}_c{ci:02d}.json'
    if dest.exists():
        return dest.name, 0.0
    t0 = time.perf_counter()
    c, ws, ch, src, nn = window(w)
    lo, hi = _W['chunks'][ci]
    logW = C.log_common(c, C.Q_DECODER, C.Q)
    pi, L = _W['pi'], _W['L']
    mk = dict(wstart=ws)
    best = (-math.inf, None)
    cnt = {t: 0 for t in (0, 5, 10, 20)}
    cells, flagged = 0, []
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
                if sg[k] >= 10:
                    sg2 = X.guard(c, key, sign, pc, pi, L, logW, 'mid', mk, X.RHO)
                    flagged.append(dict(stream=si, sign=sign, channel=pc, offset=k, score=float(sg[k]), recomputed=float(sg2[k])))
    rec = dict(window=w, chunk=ci, window_channel=ch, window_src=src, nulls_in_window=nn, streams=[lo, hi], cells=cells, best=best[0], argmax=best[1], counts=cnt, flagged=flagged,
               seconds=time.perf_counter() - t0)
    X._save(dest, rec)
    return dest.name, rec['seconds']


def run(workers, windows, limit):
    lib = C.read_library()
    nch = len(C.chunks([len(v) for _, v in lib]))
    todo = [(w, ci) for w in range(windows) for ci in range(nch)]
    if limit:
        todo = todo[:limit]
    todo = [a for a in todo if not (DEST / f'mid_w{a[0]}_c{a[1]:02d}.json').exists()]
    print(len(todo), 'tasks of', nch, 'chunks per window', flush=True)
    with cf.ProcessPoolExecutor(max_workers=workers, initializer=init) as ex:
        futs = [ex.submit(task, a) for a in todo]
        for n, f in enumerate(cf.as_completed(futs), 1):
            nm, dt = f.result(); print(f'[{time.strftime("%H:%M:%S")}] {n}/{len(todo)} {nm} {dt:.0f}s', flush=True)


def summary():
    recs = [json.loads(p.read_text()) for p in sorted(DEST.glob('*.json'))]
    L = [f'# Phase 51 mid-word-arc null scan: {len(recs)} tasks, {sum(r["cells"] for r in recs):,} cells, T300 = {C.T300:.4f}', '']
    for w in sorted(set(r['window'] for r in recs)):
        sel = [r for r in recs if r['window'] == w]
        b = max(sel, key=lambda r: r['best'])
        L.append(f'window {w} ({sel[0]["window_channel"]}, {sel[0]["window_src"]}, {sel[0]["nulls_in_window"]} nulls): tasks {len(sel)}, cells {sum(r["cells"] for r in sel):,}, max S_guard {b["best"]:.2f} ({b["argmax"]}), '
                 + ', '.join(f'>= {t}: {sum(r["counts"][str(t)] for r in sel)}' for t in (0, 5, 10, 20)) + f', flagged (>= 10, recomputed): {sum(len(r["flagged"]) for r in sel)}')
        for r in sel:
            for f in r['flagged']:
                L.append(f'    flagged {f}')
    L.append(f'tasks with a maximum >= T300: {sum(1 for r in recs if r["best"] >= C.T300)}')
    (C.OUT / 'mid_null_summary.txt').write_text('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=('run', 'summary')); ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--windows', type=int, default=1); ap.add_argument('--limit-chunks', type=int, default=0)
    a = ap.parse_args()
    run(a.workers, a.windows, a.limit_chunks) if a.cmd == 'run' else summary()
