"""Resumable full-bank scan of a window set against the 1,439-stream library with the step3 rule (S_guard >= T).

    python campaign.py plan  <set>                   # tasks, windows, estimated work
    python campaign.py run   <set> [--workers N] [--max-tasks K] [--windows a:b]
    sets: null (E3, five v1 wrong-key windows), n300 (the 82 LP2 windows), clause (LP2 clauses of >= 60 runes)

A task is (window, chunk of streams ~1M key values). Each writes results/chanscreen/<set>/w<window>_c<chunk>.npz once
(atomic rename); a finished task is skipped on a restart. Per (stream, sign, channel): best S_guard, its offset, the
original score S there, and the number of offsets with S_guard >= 0, 5, 10, 15, 20, T. Cells with S_guard >= T are stored.
"""
import argparse
import concurrent.futures as cf
import os
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

_G = {}


def _init(kind):
    _G['lib'] = C.read_library()
    _G['pi'], _G['L'] = C.model()
    _G['win'] = C.windows(kind)
    _G['chunks'] = C.chunks([len(k) for _, k in _G['lib']])
    _G['T'] = threshold(kind, len(_G['win']))


def threshold(kind, nwin):
    if kind in ('n300', 'null', 'null2'):
        return C.T300
    import math
    n = nwin * 13_326_835 * 8
    return math.log(n / 0.001)


def task(args):
    kind, wi, ci = args
    dest = C.OUT / kind / f'w{wi:03d}_c{ci:02d}.npz'
    if dest.exists():
        return wi, ci, 0.0, 0
    t0 = time.perf_counter()
    lib, pi, L, w, T = _G['lib'], _G['pi'], _G['L'], _G['win'][wi], _G['T']
    c = w['cipher']
    logW = C.log_common(c, C.Q_DECODER, C.Q)
    a, b = _G['chunks'][ci]
    ns = b - a
    res = np.full((ns, len(C.SIGNS) * len(C.CHANNELS), 9 + 0), -np.inf)
    cand = []
    for si in range(a, b):
        key = lib[si][1]
        for gi, sign in enumerate(C.SIGNS):
            for hi, ch in enumerate(C.CHANNELS):
                sg, s = C.guard_scores(c, key, sign, ch, C.Q_DECODER, pi, L, logW)
                k = int(np.argmax(sg))
                row = res[si - a, gi * len(C.CHANNELS) + hi]
                row[0] = sg[k]
                row[1] = k if np.isfinite(sg[k]) else -1
                row[2] = s[k]
                for j, t in enumerate(C.COUNT_AT):
                    row[3 + j] = np.count_nonzero(sg >= t)
                row[8] = np.count_nonzero(sg >= T)
                if row[8]:
                    for o in np.flatnonzero(sg >= T):
                        cand.append((si, sign, hi, int(o), float(sg[o]), float(s[o])))
    tmp = dest.with_suffix('.tmp.npz')
    dest.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(tmp, res=res, cand=np.array(cand, dtype=np.float64).reshape(-1, 6), window=wi, chunk=ci, first_stream=a, T=T, logW=logW)
    os.replace(tmp, dest)
    return wi, ci, time.perf_counter() - t0, len(cand)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('plan', 'run'))
    ap.add_argument('kind', choices=('null', 'null2', 'n300', 'clause'))
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--max-tasks', type=int, default=0)
    ap.add_argument('--windows', default='')
    args = ap.parse_args()
    if args.cmd == 'run' and args.kind in ('n300', 'clause'):
        import json
        gate = C.OUT / 'e3b_gate.json'
        if not gate.exists() or json.loads(gate.read_text())['status'] != 'PASS':
            sys.exit('refused: results/chanscreen/e3b_gate.json is missing or not PASS (PROTOCOL.md amendment 1)')
    _init(args.kind)
    wins, chunks = _G['win'], _G['chunks']
    lo, hi = (0, len(wins)) if not args.windows else tuple(int(x) for x in args.windows.split(':'))
    tasks = [(args.kind, wi, ci) for wi in range(lo, hi) for ci in range(len(chunks))]
    todo = [t for t in tasks if not (C.OUT / args.kind / f'w{t[1]:03d}_c{t[2]:02d}.npz').exists()]
    lens = [len(w['cipher']) for w in wins[lo:hi]]
    print(f'{args.kind}: {len(wins)} windows (lengths {min(lens)}-{max(lens)}), {len(chunks)} chunks, T = {_G["T"]:.4f} nats; '
          f'{len(tasks)} tasks, {len(todo)} to do', flush=True)
    if args.cmd == 'plan':
        return
    if args.max_tasks:
        todo = todo[:args.max_tasks]
    t0 = time.perf_counter()
    done = 0
    with cf.ProcessPoolExecutor(max_workers=args.workers, initializer=_init, initargs=(args.kind,)) as ex:
        futs = [ex.submit(task, t) for t in todo]
        for f in cf.as_completed(futs):
            wi, ci, dt, nc = f.result()
            done += 1
            el = time.perf_counter() - t0
            eta = el / done * (len(todo) - done)
            print(f'[{time.strftime("%H:%M:%S")}] {done}/{len(todo)} w{wi:03d}c{ci:02d} {dt:6.1f}s cand={nc} elapsed {el/60:5.1f} min eta {eta/60:6.1f} min', flush=True)


if __name__ == '__main__':
    main()
