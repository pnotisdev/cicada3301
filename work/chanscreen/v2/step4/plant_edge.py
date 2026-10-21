"""Phase 24: word-edge plants (E4 style) for the edge arc of chanscreen v2. No LP2 ciphertext is scored here.

    python -B plant_edge.py run [--workers N] [--per N] [--kinds nullf,nulli,adv,none]
    python -B plant_edge.py summary
    python -B plant_edge.py time                      # cost per window, writes results/chanscreen/edge/cost.json

A plant = held plaintext (Cicada / Emerson pools of E4, digraph runes) cut into words at LP2's word lengths (a random
stretch of a random LP2 section 0.7-0.15), enciphered with the independent encryptors of work/m04/m04.py rewritten with
a 'last real ciphertext rune' (so a keyless null is invisible to the anti-repeat rule), and, per word, with probability
RHO (0.42): a keyless uniform null rune after the word (nullf), before it (nulli), or an extra key advance before the
word (adv). 'none' = same words, no edge events. The window is the 300 ciphertext runes after the first e (0..99) runes,
starting at a real rune; its candidate mask is what the decoder knows: word-final positions (nullf), word-initial
positions i>=1 (nulli, adv). Only the planted stream is searched (E4' protocol), 4 channels x 2 signs x every offset.
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
sys.path.insert(0, str(HERE.parent / 'step3'))
sys.path.insert(0, str(HERE.parent))
import common as C  # noqa: E402  (read-only: paths, model, T300, library reader, log_common)
import numpy as np  # noqa: E402
import m04 as M  # noqa: E402
import run_baseline as B  # noqa: E402
from engine_edge import all_offsets_edge  # noqa: E402

DEST = C.OUT / 'edge'
RHO = 0.42                   # plant rate and decoder nu
KINDS = {'nullf': 1, 'nulli': 1, 'adv': 2, 'none': 0}
PLANT_CHANNELS = ('m04', 'spend', 'skip', 'coin')
DECODER = {'m04': 'hold', 'spend': 'spend', 'skip': 'skip5', 'coin': 'coin'}
SECS = (7, 8, 9, 11, 12, 13, 14, 15)
_G = {}


def _init():
    _G['lib'] = C.read_library()
    _G['pi'], _G['L'] = C.model()
    _G['q'] = json.loads((C.V1 / 'frozen.json').read_text())['q']
    _G['pool'] = {s: B.pool('held', s) for s in ('cicada', 'english')}
    _G['words'] = lp_words()


def lp_words():
    """word lengths (runes between ' ', '.', '&', '%') of each LP2 section"""
    segs = C.lp.load_segments()
    out = {}
    for sec in SECS:
        w, cur = [], 0
        for t in segs[sec]:
            if isinstance(t, int):
                cur += 1
            elif t in (' ', '.', '&', '%'):
                if cur:
                    w.append(cur)
                cur = 0
        if cur:
            w.append(cur)
        out[sec] = w
    return out


def seed(kind, ch, src, i):
    return int.from_bytes(hashlib.sha256(f'phase24-edge-plant|{kind}|{ch}|{src}|{i}'.encode()).digest()[:8], 'big')


def need_extent(ch, n):
    return {'m04': 1, 'spend': 1, 'skip': 6, 'coin': 3}[ch] * n + 16


def step(ch, p, key, j, ell, mult, q, rng):
    """one real emission; returns (cipher rune, key index used, new pointer). Mirrors m04.enc_* with ell = last REAL cipher rune"""
    x = (p + mult * key[j]) % M.Q
    if ch in ('m04', 'spend'):
        if ell is not None and x == ell and rng.random() < q:
            r = rng.randrange(M.Q - 1)
            return (r + 1 if r >= ell else r), j, (j + 1 if ch == 'spend' else j)
        return x, j, j + 1
    j += 1
    if ch == 'skip':
        tries = 0
        while ell is not None and x == ell and rng.random() >= M.KEEP and tries < 5:
            x = (p + mult * key[j]) % M.Q
            j += 1
            tries += 1
        return x, j - 1, j
    if ell is not None and x == ell:       # coin
        j += 1
        if rng.random() >= M.KEEP:
            x = (p + mult * key[j]) % M.Q
            j += 1
    return x, j - 1, j


def make_plant(kind, ch, src, i, pool, words_by_sec, lib, q, rho=RHO, iid_key=False):
    """returns dict(cipher window, cand, o_true, ...) or the same with an iid key (matched null)"""
    rng = random.Random(seed(kind, ch, src, i))
    e0 = rng.randrange(100)
    sec = SECS[rng.randrange(len(SECS))]
    wl = words_by_sec[sec]
    w0 = rng.randrange(len(wl) - 150)
    # cipher stream layout: items = ('r', plain index, wstart, wend) | ('n', wstart, wend) ; adv flag per word start
    items, plain_len, w = [], 0, w0
    while len(items) < e0 + 320 + 40:
        L = wl[w]
        ev = kind != 'none' and rng.random() < rho
        if ev and kind == 'nulli':
            items.append(('n', True, False))
        for t in range(L):
            items.append(('r', plain_len, t == 0 and not (ev and kind == 'nulli'), t == L - 1 and not (ev and kind == 'nullf'), ev and kind == 'adv' and t == 0 and w > w0))
            plain_len += 1
        if ev and kind == 'nullf':
            items.append(('n', False, True))
        w += 1
    s0 = rng.randrange(len(pool) - plain_len + 1)
    plain = pool[s0:s0 + plain_len]
    nadv = sum(1 for it in items if it[0] == 'r' and it[4])
    need = need_extent(ch, len(items)) + nadv
    eligible = [k for k, (_, v) in enumerate(lib) if len(v) >= need + 1]
    si = eligible[rng.randrange(len(eligible))]
    name, key = lib[si]
    keyl = [int(x) for x in key]
    off = rng.randrange(len(key) - need + 1)
    mult = 1 if i % 4 < 2 else 28
    true_sign = 1 if mult == 1 else -1
    if iid_key:
        keyl = [rng.randrange(M.Q) for _ in range(len(keyl))]
    out, used, isnull, wstart, wend = [], [], [], [], []
    j, ell = off, None
    for it in items:
        if it[0] == 'n':
            out.append(rng.randrange(M.Q)); used.append(-1); isnull.append(True); wstart.append(it[1]); wend.append(it[2])
            continue
        _, pi_, ws, we, adv = it
        if adv:
            j += 1
        x, u, j = step(ch, plain[pi_], keyl, j, ell, mult, q, rng)
        out.append(x); used.append(u); isnull.append(False); wstart.append(ws); wend.append(we)
        ell = x
    e = e0
    while isnull[e]:
        e += 1
    cw = out[e:e + 300]
    wsw, wew = wstart[e:e + 300], wend[e:e + 300]
    if kind == 'nullf':
        cand = [1 if x else 0 for x in wew]
    elif kind in ('nulli', 'adv'):
        cand = [1 if (x and t >= 1) else 0 for t, x in enumerate(wsw)]
    else:   # none: the decoder is still handed word-final candidates (what it would be given for LP2)
        cand = [1 if x else 0 for x in wew]
    nn = sum(isnull[e:e + 300])
    return dict(name=name, stream_index=si, keyl=keyl, stream_len=len(keyl), offset=off, e=e, mult=mult, true_sign=true_sign, cipher=[int(x) for x in cw], cand=cand,
                o_true=int(used[e]), nulls_in_window=int(nn), adv_in_window=int(sum(1 for it in items[e:e + 300] if it[0] == 'r' and it[4])),
                doublets=M.doublets(cw), words_in_window=int(sum(wew)), sec=sec)


def guard(c, key, sign, ch, q, pi, L, logW, kind, cand, nu):
    out = all_offsets_edge(c, key, sign, q, ch, pi, L, kind, cand, nu)
    l, u = out[:, 0], out[:, 1]
    if np.any(np.isnan(l)) or np.any(np.isposinf(l)) or np.any(l > 1e-9):
        raise ValueError('invalid log likelihood')
    with np.errstate(invalid='ignore'):
        s = np.where(np.isfinite(l) & np.isfinite(u), l - u, -np.inf)
        sw = np.where(np.isfinite(l) & np.isfinite(logW), l - logW, -np.inf)
    return np.minimum(s, sw), s


def search(plant, true_ch, dkind, nu, pi, L):
    """all 8 passes over the planted stream with decoder kind dkind (0 = base engine, 1/2 = edge arc); stats of the true cell and the null cells"""
    c, key, cand = plant['cipher'], plant['keyl'], plant['cand']
    logW = C.log_common(c, C.Q_DECODER, C.Q)
    ot, ts = plant['o_true'], plant['true_sign']
    best = (-math.inf, None)
    band_best = -math.inf
    null_counts = {t: 0 for t in (0, 5, 10)}
    n_null = 0
    null_max = -math.inf
    secs = {}
    for sign in C.SIGNS:
        for ch in C.CHANNELS:
            t0 = time.perf_counter()
            sg, s = guard(c, key, sign, ch, C.Q_DECODER, pi, L, logW, dkind, cand, nu)
            secs[f'{sign}|{ch}'] = time.perf_counter() - t0
            mask = np.ones(len(sg), dtype=bool)
            if sign == ts:
                mask[max(0, ot - C.ALIAS_K):min(len(sg), ot + C.ALIAS_K + 1)] = False
            for t in null_counts:
                null_counts[t] += int(np.count_nonzero(sg[mask] >= t))
            n_null += int(mask.sum())
            if mask.any():
                null_max = max(null_max, float(np.max(sg[mask])))
            k = int(np.argmax(sg))
            if sg[k] > best[0]:
                best = (float(sg[k]), (sign, ch, k))
            if sign == ts and ch == true_ch:
                band_best = float(np.max(sg[max(0, ot - 3):min(len(sg), ot + 4)])) if ot >= 0 else -math.inf
    w = best[1]
    return dict(detected=bool(band_best >= C.T300), band_best=band_best, winner_score=best[0], true_within3=bool(band_best >= best[0] - 3.0),
                winner=dict(sign=w[0], channel=w[1], offset=w[2]) if w else None,
                winner_is_true=bool(w and w[0] == ts and w[1] == true_ch and abs(w[2] - ot) <= 3),
                null_counts=null_counts, n_null=n_null, null_max=null_max, seconds=secs)


def one(args):
    kind, ch, src, i = args
    dest = DEST / f'{kind}_{ch}_{src}_{i:02d}.json'
    if dest.exists():
        return dest.name, 0.0
    t0 = time.perf_counter()
    q = _G['q'].get(f'{ch}|{src}|lib', 0.8)
    plant = make_plant(kind, ch, src, i, _G['pool'][src], _G['words'], _G['lib'], q)
    pi, L = _G['pi'], _G['L']
    dec = DECODER[ch]
    ek = KINDS['nullf' if kind == 'none' else kind] or 1
    rec = {k: v for k, v in plant.items() if k not in ('keyl', 'cipher', 'cand')}
    rec.update(kind=kind, channel=ch, src=src, index=i, q_plant=q, rho=RHO)
    rec['edge'] = search(plant, dec, ek, RHO, pi, L)
    rec['base'] = search(plant, dec, 0, 0.0, pi, L)
    if kind != 'none':        # matched null: iid key, same words/events/channel, searched in the same stream
        nplant = make_plant(kind, ch, src, i + 1000, _G['pool'][src], _G['words'], _G['lib'], q, iid_key=True)
        nplant['keyl'] = plant['keyl']; nplant['o_true'] = -10**6
        rec['null_edge'] = search(nplant, dec, ek, RHO, pi, L)
    rec['seconds'] = time.perf_counter() - t0
    DEST.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix('.tmp')
    tmp.write_text(json.dumps(rec, indent=1, allow_nan=True))
    os.replace(tmp, dest)
    return dest.name, rec['seconds']


def plan(per, kinds):
    return [(k, ch, src, i) for k in kinds for ch in PLANT_CHANNELS for i in range(per) for src in ('cicada', 'english')]


def run(workers, per, kinds):
    todo = [a for a in plan(per, kinds) if not (DEST / f'{a[0]}_{a[1]}_{a[2]}_{a[3]:02d}.json').exists()]
    print(f'{len(todo)} plants to do', flush=True)
    with cf.ProcessPoolExecutor(max_workers=workers, initializer=_init) as ex:
        futs = [ex.submit(one, a) for a in todo]
        for n, f in enumerate(cf.as_completed(futs), 1):
            nm, dt = f.result()
            print(f'[{time.strftime("%H:%M:%S")}] {n}/{len(todo)} {nm} {dt:.1f}s', flush=True)


def summary():
    recs = [json.loads(p.read_text()) for p in sorted(DEST.glob('*_*_*_*.json'))]
    L = [f'# Phase 24 word-edge plants: {len(recs)} plants, T300 = {C.T300:.4f} nats, nu = decoder = plant rate {RHO}, alias band +-{C.ALIAS_K}', '']
    L.append('kind    channel  n   edge-decoder detected   winner=true(+-3)   base-engine detected   median band_best (edge / base)   null_edge max S_guard (matched null)  [>= T300]')
    for kind in ('nullf', 'nulli', 'adv', 'none'):
        for ch in PLANT_CHANNELS:
            sel = [r for r in recs if r['kind'] == kind and r['channel'] == ch]
            if not sel:
                continue
            nm = [r['null_edge']['null_max'] for r in sel if 'null_edge' in r]
            nm = [x for x in nm if math.isfinite(x)]
            nx = [r['null_edge']['winner_score'] for r in sel if 'null_edge' in r]
            L.append(f'{kind:6s}  {DECODER[ch]:6s} {len(sel):3d}   {sum(r["edge"]["detected"] for r in sel):3d}   {sum(r["edge"]["winner_is_true"] for r in sel):3d}   {sum(r["base"]["detected"] for r in sel):3d}   '
                     f'{np.median([r["edge"]["band_best"] for r in sel]):9.1f} / {np.median([r["base"]["band_best"] for r in sel]):9.1f}   '
                     + (f'{max(nx):8.2f} ({sum(x >= C.T300 for x in nx)}/{len(nx)})' if nx else '-'))
    L.append('')
    L.append('Wrong-offset exceedances of the true plants (outside the +-20 alias band, edge decoder), diagnostic:')
    for t in ('0', '5', '10'):
        obs = sum(r['edge']['null_counts'][t] for r in recs)
        L.append(f'   t = {t:>2s}: observed {obs} in {sum(r["edge"]["n_null"] for r in recs)} cells')
    (C.OUT / 'edge_summary.txt').write_text('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('run', 'summary', 'time'))
    ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--per', type=int, default=5)
    ap.add_argument('--kinds', default='nullf,nulli,adv,none')
    a = ap.parse_args()
    if a.cmd == 'run':
        run(a.workers, a.per, a.kinds.split(','))
    elif a.cmd == 'summary':
        summary()
