"""Phase 24 edge-arc LP2 campaign driver (NOT launched by the session that wrote it; the user decides: ~285-400 CPU-hours).

    python -B edge_campaign.py plan  <set>
    python -B edge_campaign.py run   <set> --kind nullf|nulli|adv [--workers N] [--windows a:b]
    python -B edge_campaign.py summary <set>
    sets: n300 (the 82 LP2 windows of step2/thresholds.json), clause (LP2 clauses >= 60 runes, as step3; NO calibrated threshold at those lengths: see the phase 24 log)

One task = (kind, window, chunk of ~1M key values) -> results/chanscreen/edge_<set>/<kind>_w<WWW>_c<CC>.json, written once (atomic rename); a restart skips finished tasks.
Masks come from lp_mask.py (page-safe). Every cell with S_guard >= 10 is recomputed in a fresh call and scored against the base engine (hit_rule.py); aliases are
collapsed in the summary. Tier-1 = fresh score >= T_edge = ln(3 N / 0.001) (three kinds), N = windows x 13,326,835 x 8 for the set (n300: T300 + ln 3 = 30.90) AND
edge - base >= 20 nats; the whole-section verification chain of docs/CAMPAIGNS.md / step3/PROTOCOL.md follows for any tier-1 cell.
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
KINDS = ('nullf', 'nulli', 'adv')
_W = {}


def wins(sset):
    return C.n300_windows() if sset == 'n300' else C.clause_windows()


def t_edge(sset, nwin):
    return C.T300 + math.log(3) if sset == 'n300' else math.log(3 * nwin * 13_326_835 * 8 / 0.001)


def init(sset):
    _W['lib'] = C.read_library()
    _W['pi'], _W['L'] = C.model()
    _W['win'] = wins(sset)
    _W['chunks'] = C.chunks([len(v) for _, v in _W['lib']])


def task(a):
    sset, kind, wi, ci = a
    dest = C.OUT / f'edge_{sset}' / f'{kind}_w{wi:03d}_c{ci:02d}.json'
    if dest.exists():
        return dest.name, 0.0
    t0 = time.perf_counter()
    w = _W['win'][wi]
    c = w['cipher']
    fin, ini = LM.window_masks(w['sec'], w['start'], len(c))
    cand = fin if kind == 'nullf' else ini
    ek = P.KINDS[kind]
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
                    sg2, _ = P.guard(c, key, sign, pc, C.Q_DECODER, pi, L, logW, ek, cand, P.RHO)
                    bs = max(float(np.max(P.guard(c, key, sign, bc, C.Q_DECODER, pi, L, logW, 0, None, 0.0)[0][max(0, o - 3):o + 4])) for bc in C.CHANNELS)
                    hits.append(dict(stream=si, name=name, sign=sign, channel=pc, offset=o, score=float(sg[o]), recomputed=float(sg2[o]), base_best_pm3=bs, margin=float(sg[o]) - bs))
    rec = dict(set=sset, kind=kind, window=wi, wname=w['name'], chunk=ci, cells=cells, best=best[0], argmax=best[1], counts=cnt, hits=hits, seconds=time.perf_counter() - t0)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix('.tmp'); tmp.write_text(json.dumps(rec)); os.replace(tmp, dest)
    return dest.name, rec['seconds']


def tasks(sset, kinds, a, b):
    nch = len(C.chunks([len(v) for _, v in C.read_library()]))
    nw = len(wins(sset))
    return [(sset, k, wi, ci) for k in kinds for wi in range(a, min(b, nw)) for ci in range(nch)]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=('plan', 'run', 'summary')); ap.add_argument('sset', choices=('n300', 'clause'))
    ap.add_argument('--kind', choices=KINDS); ap.add_argument('--workers', type=int, default=2); ap.add_argument('--windows', default='0:1000')
    a = ap.parse_args()
    lo, hi = (int(x) for x in a.windows.split(':'))
    kinds = (a.kind,) if a.kind else KINDS
    if a.cmd == 'plan':
        t = tasks(a.sset, KINDS, 0, 10 ** 6)
        print(a.sset, len(wins(a.sset)), 'windows,', len(t), 'tasks (all kinds), T_edge =', round(t_edge(a.sset, len(wins(a.sset))), 3))
    elif a.cmd == 'run':
        todo = [x for x in tasks(a.sset, kinds, lo, hi) if not (C.OUT / f'edge_{a.sset}' / f'{x[1]}_w{x[2]:03d}_c{x[3]:02d}.json').exists()]
        print(len(todo), 'tasks to do', flush=True)
        with cf.ProcessPoolExecutor(max_workers=a.workers, initializer=init, initargs=(a.sset,)) as ex:
            futs = [ex.submit(task, x) for x in todo]
            for n, f in enumerate(cf.as_completed(futs), 1):
                nm, dt = f.result(); print(f'[{time.strftime("%H:%M:%S")}] {n}/{len(todo)} {nm} {dt:.0f}s', flush=True)
    else:
        recs = [json.loads(p.read_text()) for p in sorted((C.OUT / f'edge_{a.sset}').glob('*.json'))]
        nw = len(wins(a.sset)); T = t_edge(a.sset, nw)
        L = [f'# edge-arc LP2 campaign {a.sset}: {len(recs)} tasks of {nw * 14 * 3}, {sum(r["cells"] for r in recs):,} cells, T_edge = {T:.3f}', '']
        for k in KINDS:
            sel = [r for r in recs if r['kind'] == k]
            if sel:
                b = max(sel, key=lambda r: r['best'])
                L.append(f'{k}: tasks {len(sel)}, max S_guard {b["best"]:.2f} ({b["wname"]} {b["argmax"]}), ' + ', '.join(f'>= {t}: {sum(r["counts"][str(t)] for r in sel)}' for t in (0, 5, 10, 20)))
        hits = [dict(h, kind=r['kind'], wname=r['wname']) for r in recs for h in r['hits']]
        tier1 = [h for h in hits if h['recomputed'] >= T and abs(h['recomputed'] - h['score']) < 1e-6 and h['margin'] >= H.MARGIN_NATS]
        L.append(f'cells >= 10 (recomputed): {len(hits)}; not reproduced: {sum(abs(h["recomputed"] - h["score"]) >= 1e-6 for h in hits)}; tier-1 (>= T, reproduced, edge-base >= {H.MARGIN_NATS}): {len(tier1)} (aliases NOT yet collapsed: compare key windows with hit_rule.collapse_hits)')
        for h in tier1:
            L.append(f'    TIER-1 CANDIDATE {h}')
        (C.OUT / f'edge_{a.sset}_summary.txt').write_text('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
