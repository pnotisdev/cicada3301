"""Phase 51: mid-word-null plants (E4 style), power ladder and blindness for the mid-word arc of chanscreen v2. No LP2 ciphertext is scored here.

    python -B plant_mid.py run [--workers N] [--per N]        # n = 300, plant rate 0.42: mid / base / nullf / nulli / adv decoders + matched iid-key null (mid)
    python -B plant_mid.py ladder [--workers N] [--per N]     # plant rate 0.1 / 0.2 / 0.42 / 0.6 x n = 150 / 300, mid decoder + matched null
    python -B plant_mid.py summary

A plant = held plaintext cut into words at LP2's word lengths (as plant_edge.py), enciphered with the m04 encryptors (plant_edge.step: last REAL cipher rune),
and per multi-rune word with probability RHO ONE keyless uniform null rune after plaintext rune s, s uniform in 1..L-1 (an interior slot of the L+1 cipher runes).
The decoder gets only word-start flags (mid) or the phase-24 edge masks (nullf / nulli / adv); never which words carry a null. Only the planted stream is searched.
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import math
import os
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import plant_edge as P  # noqa: E402  (read-only reuse: _init, _G, step, need_extent, lp_words, constants)
import numpy as np  # noqa: E402
from engine_mid import all_offsets_mid  # noqa: E402
C, M = P.C, P.M
DEST = C.OUT / 'mid'
DEST_L = C.OUT / 'mid_ladder'
RHO = 0.42
NUS = (0.1, 0.2, 0.42, 0.6)
NS = (150, 300)
# decoder name -> (engine kind, mask used). 'mid' = kind 3 with word starts; the others are the phase-24 arcs / the base engine
DECODERS = {'mid': 3, 'base': 0, 'nullf': 1, 'nulli': 1, 'adv': 2}


def make_plant(ch, src, i, pool, words_by_sec, lib, q, rho=RHO, iid_key=False):
    rng = random.Random(int.from_bytes(hashlib.sha256(f'phase51-mid-plant|{ch}|{src}|{i}'.encode()).digest()[:8], 'big'))
    e0 = rng.randrange(100)
    sec = P.SECS[rng.randrange(len(P.SECS))]
    wl = words_by_sec[sec]
    w0 = rng.randrange(len(wl) - 150)
    items, plain_len, w = [], 0, w0       # ('r', plain index, word start, word end) | ('n', False, False)
    while len(items) < e0 + 320 + 40:
        L = wl[w]
        slot = rng.randrange(1, L) if (L >= 2 and rng.random() < rho) else 0   # null after the slot-th plaintext rune of the word
        for t in range(L):
            items.append(('r', plain_len, t == 0, t == L - 1))
            plain_len += 1
            if slot and t + 1 == slot:
                items.append(('n', False, False))
        w += 1
    s0 = rng.randrange(len(pool) - plain_len + 1)
    plain = pool[s0:s0 + plain_len]
    need = P.need_extent(ch, len(items))
    eligible = [k for k, (_, v) in enumerate(lib) if len(v) >= need + 1]
    si = eligible[rng.randrange(len(eligible))]
    name, key = lib[si]
    keyl = [int(x) for x in key]
    off = rng.randrange(len(key) - need + 1)
    mult = 1 if i % 4 < 2 else 28
    if iid_key:
        keyl = [rng.randrange(M.Q) for _ in range(len(keyl))]
    out, used, isnull, wstart, wend = [], [], [], [], []
    j, ell = off, None
    for it in items:
        if it[0] == 'n':
            out.append(rng.randrange(M.Q)); used.append(-1); isnull.append(True); wstart.append(False); wend.append(False)
            continue
        x, u, j = P.step(ch, plain[it[1]], keyl, j, ell, mult, q, rng)
        out.append(x); used.append(u); isnull.append(False); wstart.append(it[2]); wend.append(it[3])
        ell = x
    e = e0
    while isnull[e]:
        e += 1
    sl = slice(e, e + 300)
    cw, ws, we = out[sl], [int(x) for x in wstart[sl]], [int(x) for x in wend[sl]]
    return dict(name=name, stream_index=si, keyl=keyl, stream_len=len(keyl), offset=off, e=e, mult=mult, true_sign=1 if mult == 1 else -1, cipher=[int(x) for x in cw],
                ws=ws, we=we, o_true=int(used[e]), nulls_in_window=int(sum(isnull[sl])), words_in_window=int(sum(we)), sec=sec)


def masks(pl, n):
    ws, we = pl['ws'][:n], pl['we'][:n]
    return dict(mid=dict(wstart=ws), base={}, nullf=dict(cand=we), nulli=dict(cand=[1 if (x and t >= 1) else 0 for t, x in enumerate(ws)]),
                adv=dict(cand=[1 if (x and t >= 1) else 0 for t, x in enumerate(ws)]))


def guard(c, key, sign, ch, pi, L, logW, dec, mk, nu):
    out = all_offsets_mid(c, key, sign, C.Q_DECODER, ch, pi, L, DECODERS[dec], nu=0.0 if dec == 'base' else nu, **mk)
    l, u = out[:, 0], out[:, 1]
    if np.any(np.isnan(l)) or np.any(np.isposinf(l)) or np.any(l > 1e-9):
        raise ValueError('invalid log likelihood')
    with np.errstate(invalid='ignore'):
        s = np.where(np.isfinite(l) & np.isfinite(u), l - u, -np.inf)
        sw = np.where(np.isfinite(l) & np.isfinite(logW), l - logW, -np.inf)
    return np.minimum(s, sw)


def search(plant, n, true_ch, dec, pi, L):
    """8 passes over the planted stream with decoder dec; true-cell band, global best, wrong-cell maximum"""
    c, key = plant['cipher'][:n], plant['keyl']
    mk = masks(plant, n)[dec]
    logW = C.log_common(c, C.Q_DECODER, C.Q)
    ot, ts = plant['o_true'], plant['true_sign']
    best = (-math.inf, None)
    band_best, null_max = -math.inf, -math.inf
    t0 = time.perf_counter()
    for sign in C.SIGNS:
        for ch in C.CHANNELS:
            sg = guard(c, key, sign, ch, pi, L, logW, dec, mk, RHO)
            mask = np.ones(len(sg), dtype=bool)
            if sign == ts:
                mask[max(0, ot - C.ALIAS_K):min(len(sg), ot + C.ALIAS_K + 1)] = False
            if mask.any():
                null_max = max(null_max, float(np.max(sg[mask])))
            k = int(np.argmax(sg))
            if sg[k] > best[0]:
                best = (float(sg[k]), (sign, ch, k))
            if sign == ts and ch == true_ch and ot >= 0:
                band_best = float(np.max(sg[max(0, ot - 3):min(len(sg), ot + 4)]))
    return dict(detected=bool(band_best >= C.T300), band_best=band_best, winner_score=best[0], true_within3=bool(band_best >= best[0] - 3.0),
                winner_is_true=bool(best[1] and best[1][0] == ts and best[1][1] == true_ch and abs(best[1][2] - ot) <= 3), winner=best[1], null_max=null_max,
                seconds=time.perf_counter() - t0)


def _save(dest, rec):
    DEST_PARENT = dest.parent
    DEST_PARENT.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix('.tmp')
    tmp.write_text(json.dumps(rec, indent=1, allow_nan=True))
    os.replace(tmp, dest)


def one(args):
    ch, src, i = args
    dest = DEST / f'mid_{ch}_{src}_{i:02d}.json'
    if dest.exists():
        return dest.name, 0.0
    t0 = time.perf_counter()
    q = P._G['q'].get(f'{ch}|{src}|lib', 0.8)
    pl = make_plant(ch, src, i, P._G['pool'][src], P._G['words'], P._G['lib'], q)
    pi, L = P._G['pi'], P._G['L']
    rec = {k: v for k, v in pl.items() if k not in ('keyl', 'cipher', 'ws', 'we')}
    rec.update(channel=ch, src=src, index=i, q_plant=q, rho=RHO)
    dec = P.DECODER[ch]
    for d in DECODERS:
        rec[d] = search(pl, 300, dec, d, pi, L)
    npl = make_plant(ch, src, i + 1000, P._G['pool'][src], P._G['words'], P._G['lib'], q, iid_key=True)
    npl['keyl'] = pl['keyl']; npl['o_true'] = -10 ** 6
    rec['null_mid'] = search(npl, 300, dec, 'mid', pi, L)
    rec['seconds'] = time.perf_counter() - t0
    _save(dest, rec)
    return dest.name, rec['seconds']


def one_ladder(args):
    ch, src, i, ni = args
    dest = DEST_L / f'mid_{ch}_{src}_{i:02d}_nu{ni}.json'
    if dest.exists():
        return dest.name, 0.0
    t0 = time.perf_counter()
    nu = NUS[ni]
    q = P._G['q'].get(f'{ch}|{src}|lib', 0.8)
    pl = make_plant(ch, src, i + 100 * (ni + 1), P._G['pool'][src], P._G['words'], P._G['lib'], q, rho=nu)
    npl = make_plant(ch, src, i + 100 * (ni + 1) + 1000, P._G['pool'][src], P._G['words'], P._G['lib'], q, rho=nu, iid_key=True)
    npl['keyl'] = pl['keyl']; npl['o_true'] = -10 ** 6
    pi, L = P._G['pi'], P._G['L']
    dec = P.DECODER[ch]
    rec = dict(channel=ch, src=src, index=i, nu_plant=nu, stream=pl['name'], stream_len=pl['stream_len'], o_true=pl['o_true'])
    for n in NS:
        r = search(pl, n, dec, 'mid', pi, L)
        rn = search(npl, n, dec, 'mid', pi, L)
        rec[str(n)] = dict(detected=r['detected'], band_best=r['band_best'], winner_score=r['winner_score'], true_within3=r['true_within3'], null_winner=rn['winner_score'],
                           nulls_in_window=int(pl['nulls_in_window']))
    rec['seconds'] = time.perf_counter() - t0
    _save(dest, rec)
    return dest.name, rec['seconds']


def _pool_run(fn, todo, workers):
    print(len(todo), 'to do', flush=True)
    with cf.ProcessPoolExecutor(max_workers=workers, initializer=P._init) as ex:
        futs = [ex.submit(fn, a) for a in todo]
        for n, f in enumerate(cf.as_completed(futs), 1):
            nm, dt = f.result()
            print(f'[{time.strftime("%H:%M:%S")}] {n}/{len(todo)} {nm} {dt:.0f}s', flush=True)


def summary():
    recs = [json.loads(p.read_text()) for p in sorted(DEST.glob('mid_*.json'))]
    L = [f'# Phase 51 mid-word plants: {len(recs)} plants (n = 300, plant rate {RHO}), T300 = {C.T300:.4f}, decoder nu = {RHO}', '']
    L.append('channel src      | mid: detected within3 median-band | base: detected | nullf | nulli | adv  (detected counts; median band score) | matched-null max (mid)')
    for ch in P.PLANT_CHANNELS:
        sel = [r for r in recs if r['channel'] == ch]
        if not sel:
            continue
        row = f'{P.DECODER[ch]:6s} n={len(sel):2d} | '
        for d in DECODERS:
            row += f'{d} {sum(r[d]["detected"] for r in sel)}/{len(sel)}' + (f' w3 {sum(r[d]["true_within3"] for r in sel)}' if d == 'mid' else '') + f' med {np.median([r[d]["band_best"] for r in sel]):.1f} | '
        nm = [r['null_mid']['winner_score'] for r in sel]
        L.append(row + f'null max {max(nm):.2f} ({sum(x >= C.T300 for x in nm)} >= T300)')
    L.append('')
    L.append('All channels pooled:')
    for d in DECODERS:
        L.append(f'  {d:5s}: detected {sum(r[d]["detected"] for r in recs)}/{len(recs)}, true within 3 nats of best {sum(r[d]["true_within3"] for r in recs)}/{len(recs)}, '
                 f'median band {np.median([r[d]["band_best"] for r in recs]):.1f}, median (mid band - this decoder band) {np.median([r["mid"]["band_best"] - r[d]["band_best"] for r in recs]):.1f}')
    L.append(f'  matched nulls (mid decoder, iid key): max winner score {max(r["null_mid"]["winner_score"] for r in recs):.2f}, >= T300: {sum(r["null_mid"]["winner_score"] >= C.T300 for r in recs)}')
    L.append(f'  nulls in the 300-rune windows: median {np.median([r["nulls_in_window"] for r in recs]):.0f}, words {np.median([r["words_in_window"] for r in recs]):.0f}')
    (C.OUT / 'mid_summary.txt').write_text('\n'.join(L) + '\n')
    print('\n'.join(L))
    recs = [json.loads(p.read_text()) for p in sorted(DEST_L.glob('*.json'))]
    if not recs:
        return
    L = [f'# Phase 51 power ladder (mid decoder nu = {RHO}, T300 = {C.T300:.2f} used for every n), {len(recs)} plants', '',
         'detected / true within 3 nats of the global best / median band score / matched-null max, by plant rate (rows) and n (columns)']
    for nu in NUS:
        row = f'  rate {nu:4.2f}: '
        for n in NS:
            sel = [r for r in recs if r['nu_plant'] == nu]
            if sel:
                row += f'n={n}: {sum(r[str(n)]["detected"] for r in sel)}/{len(sel)} {sum(r[str(n)]["true_within3"] for r in sel)}/{len(sel)} med {np.median([r[str(n)]["band_best"] for r in sel]):6.1f} null max {max(r[str(n)]["null_winner"] for r in sel):7.1f} | '
        L.append(row)
    L.append('')
    L.append('By channel (n=300 / n=150 detected, all rates pooled): ' + '; '.join(
        f'{P.DECODER[ch]} ' + '/'.join(f'{sum(r[str(n)]["detected"] for r in recs if r["channel"] == ch)}/{sum(1 for r in recs if r["channel"] == ch)}' for n in (300, 150)) for ch in P.PLANT_CHANNELS))
    (C.OUT / 'mid_ladder_summary.txt').write_text('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('run', 'ladder', 'summary'))
    ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--per', type=int, default=6)
    a = ap.parse_args()
    if a.cmd == 'run':
        todo = [(ch, s, i) for ch in P.PLANT_CHANNELS for i in range(a.per) for s in ('cicada', 'english')]
        _pool_run(one, [t for t in todo if not (DEST / f'mid_{t[0]}_{t[1]}_{t[2]:02d}.json').exists()], a.workers)
    elif a.cmd == 'ladder':
        todo = [(ch, s, i, ni) for ch in P.PLANT_CHANNELS for s in ('cicada', 'english') for i in range(a.per) for ni in range(len(NUS))]
        _pool_run(one_ladder, [t for t in todo if not (DEST_L / f'mid_{t[0]}_{t[1]}_{t[2]:02d}_nu{t[3]}.json').exists()], a.workers)
    else:
        summary()
