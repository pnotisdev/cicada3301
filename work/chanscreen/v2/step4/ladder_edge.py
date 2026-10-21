"""Phase 24 power ladder for the edge arc: window length n (60/150/300) x plant event rate nu_plant (0.1/0.2/0.42/0.6) against the decoder's fixed nu = 0.42.
(nu_plant 0.1 and 0.2 are 'events on a quarter / half of the words' at the 0.42 rate: eligibility and event are independent, so the rate is the product.)
Kinds nullf and adv, 4 channels, 2 sources, PER plants per cell; edge decoder on the planted stream + a matched iid-key null in the same stream.
    python -B ladder_edge.py run [--workers 2] [--per 3]     python -B ladder_edge.py summary
"""
import argparse, concurrent.futures as cf, json, math, os, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import plant_edge as P
import numpy as np
DEST = P.C.OUT / 'edge_ladder'
NS = (60, 150, 300)
NUS = (0.1, 0.2, 0.42, 0.6)
KINDS = ('nullf', 'adv')


def cut(pl, n):
    d = dict(pl); d['cipher'] = pl['cipher'][:n]; d['cand'] = pl['cand'][:n]; return d


def one(a):
    kind, ch, src, i, ni = a
    nu = NUS[ni]
    dest = DEST / f'{kind}_{ch}_{src}_{i:02d}_nu{ni}.json'
    if dest.exists():
        return dest.name, 0.0
    t0 = time.perf_counter()
    q = P._G['q'].get(f'{ch}|{src}|lib', 0.8)
    pl = P.make_plant(kind, ch, src, i + 100 * (ni + 1), P._G['pool'][src], P._G['words'], P._G['lib'], q, rho=nu)
    npl = P.make_plant(kind, ch, src, i + 100 * (ni + 1) + 1000, P._G['pool'][src], P._G['words'], P._G['lib'], q, rho=nu, iid_key=True)
    npl['keyl'] = pl['keyl']; npl['o_true'] = -10 ** 6
    pi, L = P._G['pi'], P._G['L']
    dec, ek = P.DECODER[ch], P.KINDS[kind]
    rec = dict(kind=kind, channel=ch, src=src, index=i, nu_plant=nu, stream=pl['name'], stream_len=pl['stream_len'], o_true=pl['o_true'])
    for n in NS:
        r = P.search(cut(pl, n), dec, ek, P.RHO, pi, L)
        rn = P.search(cut(npl, n), dec, ek, P.RHO, pi, L)
        rec[str(n)] = dict(detected=r['detected'], band_best=r['band_best'], winner_score=r['winner_score'], true_within3=r['true_within3'],
                           null_winner=rn['winner_score'])
        rec[str(n)]['events_in_window'] = pl['nulls_in_window'] + pl['adv_in_window']
    rec['seconds'] = time.perf_counter() - t0
    DEST.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix('.tmp'); tmp.write_text(json.dumps(rec, indent=1)); os.replace(tmp, dest)
    return dest.name, rec['seconds']


def run(workers, per):
    todo = [(k, ch, s, i, ni) for k in KINDS for ch in P.PLANT_CHANNELS for s in ('cicada', 'english') for i in range(per) for ni in range(len(NUS))]
    todo = [a for a in todo if not (DEST / f'{a[0]}_{a[1]}_{a[2]}_{a[3]:02d}_nu{a[4]}.json').exists()]
    print(len(todo), 'to do', flush=True)
    with cf.ProcessPoolExecutor(max_workers=workers, initializer=P._init) as ex:
        futs = [ex.submit(one, a) for a in todo]
        for n, f in enumerate(cf.as_completed(futs), 1):
            nm, dt = f.result(); print(f'[{time.strftime("%H:%M:%S")}] {n}/{len(todo)} {nm} {dt:.0f}s', flush=True)


def summary():
    recs = [json.loads(p.read_text()) for p in sorted(DEST.glob('*.json'))]
    L = [f'# Phase 24 power ladder (edge decoder nu = {P.RHO}, T300 = {P.C.T300:.2f} used for every n), {len(recs)} plants', '']
    for kind in KINDS:
        L.append(f'{kind}: detected / true within 3 nats of the global best / median band score / matched-null max, by plant nu (rows) and n (columns)')
        for ni, nu in enumerate(NUS):
            row = f'  nu_plant {nu:4.2f}: '
            for n in NS:
                sel = [r for r in recs if r['kind'] == kind and r['nu_plant'] == nu]
                if not sel: continue
                d = sum(r[str(n)]['detected'] for r in sel); w = sum(r[str(n)]['true_within3'] for r in sel)
                row += f'n={n}: {d}/{len(sel)} {w}/{len(sel)} med {np.median([r[str(n)]["band_best"] for r in sel]):6.1f} null max {max(r[str(n)]["null_winner"] for r in sel):7.1f} | '
            L.append(row)
    L.append('')
    L.append('By channel (n=300 / n=150 / n=60 detected, all nu pooled):')
    for kind in KINDS:
        for ch in P.PLANT_CHANNELS:
            sel = [r for r in recs if r['kind'] == kind and r['channel'] == ch]
            L.append(f'  {kind:5s} {P.DECODER[ch]:6s} ' + ' / '.join(f'{sum(r[str(n)]["detected"] for r in sel)}/{len(sel)}' for n in (300, 150, 60)))
    (P.C.OUT / 'edge_ladder_summary.txt').write_text('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=('run', 'summary')); ap.add_argument('--workers', type=int, default=1); ap.add_argument('--per', type=int, default=3)
    a = ap.parse_args()
    run(a.workers, a.per) if a.cmd == 'run' else summary()
