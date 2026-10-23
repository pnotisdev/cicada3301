"""G4 of the union null arc (R4 repair s08): R4 plants with the null slot uniform over 0..L, union arc vs mid arc. Plants only; no LP2 ciphertext is scored
(LP2 word LENGTHS lay out the plants, as in every earlier plant).

    python -B work/r4fix/s08_power_union.py one                # one plant (timing probe)
    python -B work/r4fix/s08_power_union.py run [--workers 2]  # 6 plants x {hold, spend} (3 Cicada + 3 English held plaintext, signs alternate)
    python -B work/r4fix/s08_power_union.py summary            # -> results/r4fix/s08_union_arc/g4_summary.txt

Plant = r4sim.encrypt_r4 (work/r4fix/r4sim.py, tests pass: see the log) with slots='any' (0..L, word edges included), nu 0.45 of multi-rune words, one null, uniform value never equal to its
left neighbour and visible to the anti-repeat rule (null_check 'left', null_visible True, as phase 57 R4), repair writes T(c[-6]) = 24 - 2c in-word (lag_basis 'cipher'), q from frozen.json,
channel hold (m04) or spend, library key at a random offset, sign +1 / -1 alternating, held plaintext cut at LP2 word lengths of a random section (plaintext length = LP2 word length, as phase 57/s01).
Window: 300 cipher runes starting at the first real rune at or after a random item e0 (0..99); n 150 and 300 are prefixes of it. Decoders: union arc (place 'any', nu 0.42) and mid arc (kind 3, nu 0.42),
both given only word-start flags, all four decoder channels, both signs, every offset of the planted stream. Detected = S_guard of the true cell (plant's channel and sign, +-3 offsets) >= T300 = 29.80.
Null control: a matched plant with an iid random key (same generator, index i + 1000: its own words and layout), searched in the TRUE plant's stream, union arc.
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
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'work' / 'chanscreen' / 'v2' / 'step4'))
sys.path.insert(0, str(ROOT / 'work' / 'chanscreen' / 'v2'))
import numpy as np  # noqa: E402
import plant_mid as X  # noqa: E402  (read-only: plant_edge's library/model/pool loaders)
import lp_pilot_mid as LPM  # noqa: E402  (read-only: lower())
from engine_mid import all_offsets_mid  # noqa: E402
from s08_engine_union import all_offsets_union  # noqa: E402
import r4sim  # noqa: E402

P, C = X.P, X.C
Q = X.M.Q
DEST = ROOT / 'results' / 'r4fix' / 's08_union_arc'
PLANTS = [(ch, src, i) for ch in ('m04', 'spend') for i, src in enumerate(('cicada', 'cicada', 'cicada', 'english', 'english', 'english'))]
RHO_PLANT, NU_DEC = 0.45, 0.42


def seed_for(ch, src, i):
    return int.from_bytes(hashlib.sha256(f'r4fix-s08|{ch}|{src}|{i}'.encode()).digest()[:8], 'big')


def make_plant(ch, src, i, idx, pool, words_by_sec, lib, q, iid_key=False):
    """idx = plant index for the seed (i for the plant, i + 1000 for the matched null); i alternates the sign"""
    rng = random.Random(seed_for(ch, src, idx))
    e0 = rng.randrange(100)
    sec = P.SECS[rng.randrange(len(P.SECS))]
    wl = words_by_sec[sec]
    w0 = rng.randrange(len(wl) - 150)
    ncip = e0 + 320 + 40
    lens, tot, w = [], 0, w0
    while tot < ncip + 20:
        lens.append(wl[w])
        tot += wl[w]
        w += 1
    s0 = rng.randrange(len(pool) - tot + 1)
    flat = pool[s0:s0 + tot]
    words, p = [], 0
    for L in lens:
        words.append([int(x) for x in flat[p:p + L]])
        p += L
    need = P.need_extent(ch, ncip)
    eligible = [k for k, (_, v) in enumerate(lib) if len(v) >= need + 1]
    si = eligible[rng.randrange(len(eligible))]
    name, key = lib[si]
    keyl = [int(x) for x in key]
    off = rng.randrange(len(key) - need + 1)
    sign = 1 if i % 2 == 0 else -1
    if iid_key:
        keyl = [rng.randrange(Q) for _ in range(len(keyl))]
    res = r4sim.encrypt_r4(words, keyl, rng, q=q, repair='T', lag=6, nu=RHO_PLANT, slots='any', null_check='left', null_visible=True, lag_basis='cipher',
                           channel='hold' if ch == 'm04' else 'spend', sign=sign, key_start=off, n_cipher=ncip)
    e = e0
    while res.is_null[e]:
        e += 1
    sl = slice(e, e + 300)
    ws = [int(x) for x in res.word_start[sl]]
    ws[0] = 1
    edge = (res.is_null & (res.word_start | res.word_end))[sl]
    return dict(name=name, stream_index=si, keyl=keyl, stream_len=len(keyl), offset=off, e=e, true_sign=sign, cipher=[int(x) for x in res.cipher[sl]], ws=ws,
                o_true=int(res.key_index[e]), nulls=[int(x) for x in res.is_null[sl]], edge_nulls=[int(x) for x in edge], T_repairs=int(res.repair_is_T[sl].sum()), sec=sec)


def guard(c, key, sign, ch, pi, L, logW, dec, ws):
    if dec == 'union':
        out = all_offsets_union(c, key, sign, C.Q_DECODER, ch, pi, L, NU_DEC, ws, 'any')
    else:
        out = all_offsets_mid(c, key, sign, C.Q_DECODER, ch, pi, L, 3, None, NU_DEC, ws)
    l, u = out[:, 0], out[:, 1]
    if np.any(np.isnan(l)) or np.any(np.isposinf(l)) or np.any(l > 1e-9):
        raise ValueError('invalid log likelihood')
    with np.errstate(invalid='ignore'):
        s = np.where(np.isfinite(l) & np.isfinite(u), l - u, -np.inf)
        sw = np.where(np.isfinite(l) & np.isfinite(logW), l - logW, -np.inf)
    return np.minimum(s, sw)


def search(plant, n, true_ch, dec, pi, L):
    """8 passes over the planted stream: true-cell band, global best, wrong-cell maximum"""
    c, key, ws = plant['cipher'][:n], plant['keyl'], plant['ws'][:n]
    logW = C.log_common(c, C.Q_DECODER, C.Q)
    ot, ts = plant['o_true'], plant['true_sign']
    best = (-math.inf, None)
    band_best, null_max = -math.inf, -math.inf
    t0 = time.process_time()
    for sign in C.SIGNS:
        for ch in C.CHANNELS:
            sg = guard(c, key, sign, ch, pi, L, logW, dec, ws)
            mask = np.ones(len(sg), dtype=bool)
            if sign == ts and ot >= 0:
                mask[max(0, ot - C.ALIAS_K):min(len(sg), ot + C.ALIAS_K + 1)] = False
            if mask.any():
                null_max = max(null_max, float(np.max(sg[mask])))
            k = int(np.argmax(sg))
            if sg[k] > best[0]:
                best = (float(sg[k]), (sign, ch, k))
            if sign == ts and ch == true_ch and ot >= 0:
                band_best = float(np.max(sg[max(0, ot - 3):min(len(sg), ot + 4)]))
    return dict(detected=bool(band_best >= C.T300), band_best=band_best, winner_score=best[0], true_within3=bool(band_best >= best[0] - 3.0),
                winner=best[1], null_max=null_max, cpu_seconds=time.process_time() - t0)


def init():
    LPM.lower()
    P._init()


def run_plant(ch, src, i, ns=(150, 300)):
    t0 = time.process_time()
    q = P._G['q'].get(f'{ch}|{src}|lib', 0.8)
    pl = make_plant(ch, src, i, i, P._G['pool'][src], P._G['words'], P._G['lib'], q)
    npl = make_plant(ch, src, i, i + 1000, P._G['pool'][src], P._G['words'], P._G['lib'], q, iid_key=True)
    npl['keyl'] = pl['keyl']
    npl['o_true'] = -10 ** 6
    pi, L = P._G['pi'], P._G['L']
    dec = P.DECODER[ch]
    rec = {k: v for k, v in pl.items() if k not in ('keyl', 'cipher', 'ws', 'nulls', 'edge_nulls')}
    rec.update(channel=ch, src=src, index=i, q_plant=q, rho_plant=RHO_PLANT, nu_decoder=NU_DEC)
    for n in ns:
        rec[str(n)] = dict(nulls=sum(pl['nulls'][:n]), edge_nulls=sum(pl['edge_nulls'][:n]), union=search(pl, n, dec, 'union', pi, L), mid=search(pl, n, dec, 'mid', pi, L),
                           null_union=search(npl, n, dec, 'union', pi, L))
    rec['cpu_seconds'] = time.process_time() - t0
    return rec


def one_plant(args):
    ch, src, i = args
    dest = DEST / f'g4_{ch}_{src}_{i}.json'
    if dest.exists():
        return dest.name, 0.0
    rec = run_plant(ch, src, i)
    DEST.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix('.tmp')
    tmp.write_text(json.dumps(rec, indent=1, allow_nan=True), encoding='utf-8', newline='\n')
    os.replace(tmp, dest)
    return dest.name, rec['cpu_seconds']


def summary():
    recs = [json.loads(p.read_text(encoding='utf-8')) for p in sorted(DEST.glob('g4_*.json'))]
    out = [f'# R4 repair s08 G4: R4 plants (null slot 0..L), union arc vs mid arc, {len(recs)} plants, T300 = {C.T300:.2f} (used at n 150 and 300), decoder nu {NU_DEC}, plant rate {RHO_PLANT}']
    for n in ('150', '300'):
        out.append(f'\nn {n}')
        for ch in ('m04', 'spend'):
            sel = [r for r in recs if r['channel'] == ch]
            if not sel:
                continue
            for dec in ('union', 'mid'):
                b = sorted(r[n][dec]['band_best'] for r in sel)
                out.append(f'  {ch:5s} {dec:5s}: detected {sum(r[n][dec]["detected"] for r in sel)}/{len(sel)}, true within 3 nats of best {sum(r[n][dec]["true_within3"] for r in sel)}/{len(sel)}, '
                           f'band min / median / max {b[0]:.1f} / {b[len(b) // 2]:.1f} / {b[-1]:.1f}')
            nm = [r[n]['null_union']['winner_score'] for r in sel]
            out.append(f'  {ch:5s} matched iid-key null (union): max winner {max(nm):.1f}, >= T300: {sum(x >= C.T300 for x in nm)}/{len(sel)}')
        d = {dec: [r[n][dec]['band_best'] for r in recs] for dec in ('union', 'mid')}
        out.append(f'  pooled: union detected {sum(r[n]["union"]["detected"] for r in recs)}/{len(recs)}, mid detected {sum(r[n]["mid"]["detected"] for r in recs)}/{len(recs)}; '
                   f'median band union {float(np.median(d["union"])):.1f} mid {float(np.median(d["mid"])):.1f}; median (union - mid) {float(np.median(np.array(d["union"]) - np.array(d["mid"]))):.1f}; '
                   f'union >= mid in {sum(u >= m_ for u, m_ in zip(d["union"], d["mid"]))}/{len(recs)}')
    out.append('\nper plant: channel src idx | n | nulls (edge) in window | union band / winner / within3 | mid band / winner / within3 | null union winner')
    for r in recs:
        for n in ('150', '300'):
            u, m_, nu_ = r[n]['union'], r[n]['mid'], r[n]['null_union']
            out.append(f'{r["channel"]:5s} {r["src"]:7s} {r["index"]} | {n:3s} | {r[n]["nulls"]:2d} ({r[n]["edge_nulls"]:2d}) | union {u["band_best"]:7.1f} {u["winner_score"]:7.1f} {int(u["true_within3"])} | '
                       f'mid {m_["band_best"]:7.1f} {m_["winner_score"]:7.1f} {int(m_["true_within3"])} | null {nu_["winner_score"]:7.1f}')
    out.append(f'\nCPU seconds per plant (all searches): ' + ' '.join(f'{r["cpu_seconds"]:.0f}' for r in recs) + f'; total {sum(r["cpu_seconds"] for r in recs):.0f}')
    txt = '\n'.join(out) + '\n'
    (DEST / 'g4_summary.txt').write_text(txt, encoding='utf-8', newline='\n')
    print(txt)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('one', 'run', 'summary'))
    ap.add_argument('--workers', type=int, default=2)
    a = ap.parse_args()
    if a.cmd == 'summary':
        summary()
    elif a.cmd == 'one':
        init()
        t0 = time.process_time()
        rec = run_plant('m04', 'cicada', 0)
        DEST.mkdir(parents=True, exist_ok=True)
        (DEST / 'probe.json').write_text(json.dumps(rec, indent=1, allow_nan=True), encoding='utf-8', newline='\n')
        print(json.dumps({k: v for k, v in rec.items()}, indent=1, allow_nan=True)[:3000])
    else:
        todo = [t for t in PLANTS if not (DEST / f'g4_{t[0]}_{t[1]}_{t[2]}.json').exists()]
        print(len(todo), 'plants to do', flush=True)
        with cf.ProcessPoolExecutor(max_workers=min(a.workers, 2), initializer=init) as ex:
            futs = [ex.submit(one_plant, t) for t in todo]
            for k, f in enumerate(cf.as_completed(futs), 1):
                nm, dt = f.result()
                print(f'[{time.strftime("%H:%M:%S")}] {k}/{len(todo)} {nm} {dt:.0f} cpu-s', flush=True)
