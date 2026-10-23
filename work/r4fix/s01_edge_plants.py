"""R4 repair session s01: does the unchanged mid-word decoder still find the planted key when R4's nulls are placed as R4 was FITTED (slot 0..L), not interior only?

Plants only; no LP2 ciphertext is scored. The generator is `make_r4` of work/phase57_pilot.py with a slot-mode parameter (copied, not edited; imports read-only):
    interior : slot uniform in 1..L-1 (exactly phase 57, same seeds: the positive control of this harness)
    any      : slot uniform in 0..L  (null before the first rune of the word, between runes, or after the last one; as work/phase57_mechanism.py:77)
    edge     : slot 0 or L only, one of the two with probability 1/2 (stress diagnostic)
A null at slot 0 (L) is the FIRST (LAST) cipher rune of the word, so the word-start flag given to the decoder is on the null (the word-end flag on the last null); the in-word
lag-6 repair counts from the first cipher rune of the word (as the simulation: pos = t - w0, nulls included). For `interior` this equals phase 57's bookkeeping.

    python -B work/r4fix/s01_edge_plants.py one                 # one plant (timing / memory probe): results/r4fix/s01_edge_plants/probe.json
    python -B work/r4fix/s01_edge_plants.py plants [--workers 4] [--modes interior,any,edge]
    python -B work/r4fix/s01_edge_plants.py summary             # -> results/r4fix/s01_edge_plants/summary.txt
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / 'work' / 'chanscreen' / 'v2' / 'step4'))
import plant_mid as X  # noqa: E402
import lp_pilot_mid as LPM  # noqa: E402

P, C = X.P, X.C
Q = X.M.Q
DEST = ROOT / 'results' / 'r4fix' / 's01_edge_plants'
MODES = ('interior', 'any', 'edge')
PLANTS = [(ch, src, i) for ch in ('m04', 'spend') for src in ('cicada', 'english') for i in range(3)]
RHO = 0.45


def seed_for(mode, ch, src, i):
    # interior: phase 57's exact seed string, so its plants reproduce; the other modes get their own documented strings
    s = f'phase57-r4|{ch}|{src}|{i}' if mode == 'interior' else f'r4fix-s01|{mode}|{ch}|{src}|{i}'
    return int.from_bytes(hashlib.sha256(s.encode()).digest()[:8], 'big')


def draw_slot(rng, L, mode, rho):
    """None (no null) or the number of plaintext runes written before the null (0..L); rng call order for `interior` is phase 57's"""
    if not (L >= 2 and rng.random() < rho):
        return None
    if mode == 'interior':
        return rng.randrange(1, L)
    if mode == 'any':
        return rng.randrange(0, L + 1)
    return 0 if rng.random() < 0.5 else L


def make_r4(mode, ch, src, i, pool, words_by_sec, lib, q, rho=RHO, iid_key=False):
    rng = random.Random(seed_for(mode, ch, src, i))
    e0 = rng.randrange(100)
    sec = P.SECS[rng.randrange(len(P.SECS))]
    wl = words_by_sec[sec]
    w = rng.randrange(len(wl) - 150)
    items, plain_len = [], 0     # ('r', plain index, word first, word last, edge null) | ('n', None, word first, word last, edge null)
    while len(items) < e0 + 320 + 40:
        L = wl[w]
        slot = draw_slot(rng, L, mode, rho)
        word = []
        if slot == 0:
            word.append(['n', None, False, False, True])
        for t in range(L):
            word.append(['r', plain_len, False, False, False])
            plain_len += 1
            if slot is not None and slot > 0 and t + 1 == slot:
                word.append(['n', None, False, False, slot == L])
        word[0][2] = True
        word[-1][3] = True
        items.extend(word)
        w += 1
    s0 = rng.randrange(len(pool) - plain_len + 1)
    plain = pool[s0:s0 + plain_len]
    need = P.need_extent(ch, len(items))
    eligible = [k for k, (_, v) in enumerate(lib) if len(v) >= need + 1]
    si = eligible[rng.randrange(len(eligible))]
    name, key = lib[si]
    keyl = [int(x) for x in key]
    off = rng.randrange(len(key) - need + 1)
    mult = 1 if i % 2 == 0 else 28
    if iid_key:
        keyl = [rng.randrange(Q) for _ in range(len(keyl))]
    out, used, isnull, wstart, wend, isedge = [], [], [], [], [], []
    j, w0, nT = off, 0, 0
    for it in items:
        if it[2]:
            w0 = len(out)          # first cipher rune of the word (a null when slot 0)
        prev = out[-1] if out else None
        if it[0] == 'n':
            v = rng.randrange(Q)
            while v == prev:
                v = rng.randrange(Q)
            out.append(v); used.append(-1); isnull.append(True); wstart.append(it[2]); wend.append(it[3]); isedge.append(it[4])
            continue
        x = (plain[it[1]] + mult * keyl[j]) % Q
        u = j
        if prev is not None and x == prev and rng.random() < q:
            tv = (24 - 2 * out[-6]) % Q if len(out) - w0 >= 6 else None
            if tv is not None and tv != prev:
                x, nT = tv, nT + 1
            else:
                r = rng.randrange(Q - 1)
                x = r + 1 if r >= prev else r
            j = j + 1 if ch == 'spend' else j
        else:
            j += 1
        out.append(x); used.append(u); isnull.append(False); wstart.append(it[2]); wend.append(it[3]); isedge.append(False)
    e = e0
    while isnull[e]:
        e += 1
    sl = slice(e, e + 300)
    return dict(name=name, stream_index=si, keyl=keyl, stream_len=len(keyl), offset=off, e=e, mult=mult, true_sign=1 if mult == 1 else -1,
                cipher=[int(x) for x in out[sl]], ws=[int(x) for x in wstart[sl]], we=[int(x) for x in wend[sl]], o_true=int(used[e]),
                nulls_in_window=int(sum(isnull[sl])), T_repairs=nT, sec=sec,
                null_pos=[k for k, v in enumerate(isnull[sl]) if v], edge_pos=[k for k, v in enumerate(isedge[sl]) if v])


def init_plants():
    LPM.lower()
    P._init()


def edge_stats(pl, n):
    ne = [k for k in pl['edge_pos'] if k < n]
    nn = [k for k in pl['null_pos'] if k < n]
    return dict(nulls=len(nn), edge_nulls=len(ne), first_edge=(ne[0] if ne else None), first_null=(nn[0] if nn else None))


def run_plant(mode, ch, src, i, with_null=True, ns=(150, 300)):
    t0 = time.perf_counter()
    q = P._G['q'].get(f'{ch}|{src}|lib', 0.8)
    pl = make_r4(mode, ch, src, i, P._G['pool'][src], P._G['words'], P._G['lib'], q)
    pi, L = P._G['pi'], P._G['L']
    dec = P.DECODER[ch]
    rec = {k: v for k, v in pl.items() if k not in ('keyl', 'cipher', 'ws', 'we', 'null_pos', 'edge_pos')}
    rec.update(mode=mode, channel=ch, src=src, index=i, q_plant=q, null_positions=pl['null_pos'][:80], edge_positions=pl['edge_pos'][:80])
    if with_null:
        npl = make_r4(mode, ch, src, i + 1000, P._G['pool'][src], P._G['words'], P._G['lib'], q, iid_key=True)
        npl['keyl'] = pl['keyl']; npl['o_true'] = -10 ** 6
    for n in ns:
        rec[str(n)] = X.search(pl, n, dec, 'mid', pi, L)
        rec[str(n)].update(edge_stats(pl, n))
        if with_null:
            rec[f'null{n}'] = X.search(npl, n, dec, 'mid', pi, L)
    rec['seconds'] = time.perf_counter() - t0
    return rec


def one_plant(args):
    mode, ch, src, i = args
    dest = DEST / f'{mode}_{ch}_{src}_{i:02d}.json'
    if dest.exists():
        return dest.name, 0.0
    rec = run_plant(mode, ch, src, i)
    X._save(dest, rec)
    return dest.name, rec['seconds']


def summary():
    recs = [json.loads(p.read_text()) for p in sorted(DEST.glob('*_*_*_*.json')) if not p.name.startswith('probe')]
    import numpy as np
    out = [f'# R4 repair s01: R4 plants with the null slot interior / any (0..L) / edge only; unchanged mid arc, true stream only, T300 = {C.T300:.2f} (used at n 150 and 300)']
    for mode in MODES:
        for n in ('150', '300'):
            sel = [r for r in recs if r['mode'] == mode]
            if not sel:
                continue
            band = sorted(r[n]['band_best'] for r in sel)
            out.append(f'{mode:8s} n {n}: detected {sum(r[n]["detected"] for r in sel)}/{len(sel)}, within 3 nats of best {sum(r[n]["true_within3"] for r in sel)}/{len(sel)}, '
                       f'band min / median / max {band[0]:.1f} / {band[len(band) // 2]:.1f} / {band[-1]:.1f}; matched iid-key null max {max(r["null" + n]["winner_score"] for r in sel):.1f}')
            for ch in ('m04', 'spend'):
                s2 = [r for r in sel if r['channel'] == ch]
                out.append(f'    {ch:5s}: detected {sum(r[n]["detected"] for r in s2)}/{len(s2)} band ' + ' '.join(f'{r[n]["band_best"]:.1f}' for r in s2))
    out.append('')
    out.append('per plant: mode channel src idx | n | edge nulls / nulls in window, first edge null position, band score, detected')
    for r in recs:
        for n in ('150', '300'):
            d = r[n]
            out.append(f'{r["mode"]:8s} {r["channel"]:5s} {r["src"]:7s} {r["index"]} | {n:3s} | {d["edge_nulls"]:2d}/{d["nulls"]:2d} first edge {str(d["first_edge"]):>4s} first null {str(d["first_null"]):>4s} | '
                       f'band {d["band_best"]:7.1f} winner {d["winner_score"]:7.1f} | det {int(d["detected"])} w3 {int(d["true_within3"])} | null {r["null" + n]["winner_score"]:7.1f}')
    # detection by number of edge nulls and by first edge null position (any + edge modes pooled)
    out.append('')
    for n in ('150', '300'):
        rows = [(r[n]['edge_nulls'], r[n]['first_edge'], r[n]['band_best'], r[n]['detected'], r['mode']) for r in recs if r['mode'] != 'interior']
        out.append(f'n {n}, modes any + edge pooled, by number of edge nulls in the window:')
        for lo, hi in ((0, 0), (1, 2), (3, 5), (6, 99)):
            sel = [x for x in rows if lo <= x[0] <= hi]
            if sel:
                out.append(f'    edge nulls {lo}-{hi}: n={len(sel)} detected {sum(x[3] for x in sel)} median band {float(np.median([x[2] for x in sel])):.1f}')
        out.append(f'n {n}, by position of the first edge null (index in the window):')
        for lo, hi in ((0, 9), (10, 29), (30, 99), (100, 299)):
            sel = [x for x in rows if x[1] is not None and lo <= x[1] <= hi]
            if sel:
                out.append(f'    first edge null in {lo}-{hi}: n={len(sel)} detected {sum(x[3] for x in sel)} median band {float(np.median([x[2] for x in sel])):.1f}')
    txt = '\n'.join(out) + '\n'
    (DEST / 'summary.txt').write_text(txt, encoding='utf-8', newline='\n')
    print(txt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('one', 'plants', 'summary'))
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--modes', default=','.join(MODES))
    ap.add_argument('--mode', default='interior')
    a = ap.parse_args()
    if a.cmd == 'summary':
        return summary()
    if a.cmd == 'one':
        init_plants()
        rec = run_plant(a.mode, 'm04', 'cicada', 0)
        X._save(DEST / 'probe.json', rec)
        print({k: rec[k] for k in ('mode', 'seconds')}, {n: (rec[n]['band_best'], rec[n]['detected'], rec[n]['edge_nulls'], rec[n]['nulls'], rec['null' + n]['winner_score']) for n in ('150', '300')})
        return
    todo = [(m, *p) for m in a.modes.split(',') for p in PLANTS]
    todo = [t for t in todo if not (DEST / f'{t[0]}_{t[1]}_{t[2]}_{t[3]:02d}.json').exists()]
    print(len(todo), 'tasks', flush=True)
    with cf.ProcessPoolExecutor(max_workers=min(a.workers, 4), initializer=init_plants) as ex:
        for k, f in enumerate(cf.as_completed([ex.submit(one_plant, t) for t in todo]), 1):
            print(f'[{time.strftime("%H:%M:%S")}] {k}/{len(todo)} {f.result()}', flush=True)


if __name__ == '__main__':
    main()
