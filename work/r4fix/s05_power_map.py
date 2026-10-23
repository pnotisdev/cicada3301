"""R4 repair s05: power map of the unchanged mid arc (chanscreen v2 kind 3) for R4 plants with slot rule `any` (0..L) and `interior` (1..L-1).

Plants only; no LP2 ciphertext is scored. Factors (one at a time around the base cell: decoder nu 0.42, plant q = frozen ~0.81, plant null rate 0.45):
    n           window length (prefix of one 450-rune plant window): 100 150 200 300 450
    nu_dec      decoder's per-word null probability: 0.30 / 0.42 / 0.55 (same plants as base)
    q_plant     repair probability of the plant: 0.70 / frozen (~0.81) / 0.95 (same seeds as base: same words, key, offset, plaintext; paired)
    slot mode   any (main) / interior (reference)
Plant generator = `make_r4` of work/r4fix/s01_edge_plants.py with a window-length parameter and an explicit seed (copied, not edited; with W = 300 and s01's seed it reproduces
s01's plants bit for bit: `control` checks this). Search = `plant_mid.search` with the decoder nu as a parameter (the original hard-codes 0.42), 8 passes over the planted stream.

    python -B work/r4fix/s05_power_map.py plan                       # stream length / predicted cost of every plant
    python -B work/r4fix/s05_power_map.py control [--workers 3]      # positive control against s01's records (exact) + generator identity
    python -B work/r4fix/s05_power_map.py run --variants base --modes any --ns 100,150 [--nulls] [--workers 3]
    python -B work/r4fix/s05_power_map.py summary
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import math
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / 'work' / 'chanscreen' / 'v2' / 'step4'))
sys.path.insert(0, str(HERE))
import plant_mid as X  # noqa: E402
import lp_pilot_mid as LPM  # noqa: E402
import numpy as np  # noqa: E402

P, C = X.P, X.C
Q = X.M.Q
HIT_EXT = {'hold': 1, 'spend': 1, 'skip5': 6, 'coin': 3}   # work/chanscreen/v2/step4/hit_rule.py: EXT
S01 = ROOT / 'results' / 'r4fix' / 's01_edge_plants'
DEST = ROOT / 'results' / 'r4fix' / 's05_power_map'
REC = DEST / 'rec'
RHO = 0.45
W = 450
CHS = ('m04', 'spend')
SRCS = ('cicada', 'english')
SEEDS = tuple(range(6))
NS_ALL = (100, 150, 200, 300, 450)
# variant -> (decoder nu, plant q override or None)
VARIANTS = {'base': (0.42, None), 'nu030': (0.30, None), 'nu055': (0.55, None), 'q070': (0.42, 0.70), 'q095': (0.42, 0.95)}


def set_low_priority():
    try:
        import ctypes
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)   # BELOW_NORMAL
    except Exception:
        pass


def seed_for(mode, ch, src, i):
    return int.from_bytes(hashlib.sha256(f'r4fix-s05|{mode}|{ch}|{src}|{i}'.encode()).digest()[:8], 'big')


def s01_seed(mode, ch, src, i):
    s = f'phase57-r4|{ch}|{src}|{i}' if mode == 'interior' else f'r4fix-s01|{mode}|{ch}|{src}|{i}'
    return int.from_bytes(hashlib.sha256(s.encode()).digest()[:8], 'big')


def draw_slot(rng, L, mode, rho):
    if not (L >= 2 and rng.random() < rho):
        return None
    if mode == 'interior':
        return rng.randrange(1, L)
    if mode == 'any':
        return rng.randrange(0, L + 1)
    raise ValueError(mode)


def make_r4(mode, seed, ch, pool, words_by_sec, lib, q, i, win=W, rho=RHO, iid_key=False):
    """s01's make_r4 with an explicit integer seed and window length win (items target e0 + win + 60 as s01's e0 + 320 + 40 for win 300)"""
    rng = random.Random(seed)
    e0 = rng.randrange(100)
    sec = P.SECS[rng.randrange(len(P.SECS))]
    wl = words_by_sec[sec]
    w = rng.randrange(len(wl) - 150)
    items, plain_len = [], 0
    while len(items) < e0 + win + 20 + 40:
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
            w0 = len(out)
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
    sl = slice(e, e + win)
    return dict(name=name, stream_index=si, keyl=keyl, stream_len=len(keyl), offset=off, e=e, mult=mult, true_sign=1 if mult == 1 else -1,
                cipher=[int(x) for x in out[sl]], ws=[int(x) for x in wstart[sl]], we=[int(x) for x in wend[sl]], o_true=int(used[e]),
                nulls_in_window=int(sum(isnull[sl])), T_repairs=nT, sec=sec,
                null_pos=[k for k, v in enumerate(isnull[sl]) if v], edge_pos=[k for k, v in enumerate(isedge[sl]) if v])


def search(plant, n, true_ch, pi, L, nu):
    """plant_mid.search with the decoder nu as a parameter (decoder 'mid', kind 3)"""
    c, key = plant['cipher'][:n], plant['keyl']
    mk = X.masks(plant, n)['mid']
    logW = C.log_common(c, C.Q_DECODER, C.Q)
    ot, ts = plant['o_true'], plant['true_sign']
    best = (-math.inf, None)
    band_best, null_max, na_max = -math.inf, -math.inf, -math.inf
    t0 = time.perf_counter()
    karr = np.asarray(key)
    for sign in C.SIGNS:
        for ch in C.CHANNELS:
            sg = X.guard(c, key, sign, ch, pi, L, logW, 'mid', mk, nu)
            mask = np.ones(len(sg), dtype=bool)
            if sign == ts:
                mask[max(0, ot - C.ALIAS_K):min(len(sg), ot + C.ALIAS_K + 1)] = False
            if mask.any():
                null_max = max(null_max, float(np.max(sg[mask])))
            # non-alias wrong cells: also drop every offset whose key window equals the true one (periodic / repeated streams), true sign only
            mna = mask.copy()
            if sign == ts and ot >= 0:
                ext = HIT_EXT[ch] * n + 16
                tw = karr[ot:ot + ext]
                m = min(len(sg), len(karr))
                for o in np.flatnonzero(mna[:m] & (karr[:m] == tw[0])):
                    seg = karr[o:o + ext]
                    if np.array_equal(seg, tw[:len(seg)]):   # also windows truncated by the end of the stream
                        mna[max(0, o - C.ALIAS_K):o + C.ALIAS_K + 1] = False   # the alias's own +-ALIAS_K band too (first version of this line missed the band)
            if mna.any():
                na_max = max(na_max, float(np.max(sg[mna])))
            k = int(np.argmax(sg))
            if sg[k] > best[0]:
                best = (float(sg[k]), (sign, ch, k))
            if sign == ts and ch == true_ch and ot >= 0:
                band_best = float(np.max(sg[max(0, ot - 3):min(len(sg), ot + 4)]))
    return dict(detected=bool(band_best >= C.T300), band_best=band_best, winner_score=best[0], true_within3=bool(band_best >= best[0] - 3.0),
                wrong_best=null_max, wrong_nonalias3=na_max, within3_nonalias3=bool(band_best >= na_max - 3.0), winner=best[1], seconds=time.perf_counter() - t0)


def init_plants():
    set_low_priority()
    LPM.lower()
    P._init()


def plant_for(mode, ch, src, i, q, win=W, iid_key=False, seed=None):
    seed = seed_for(mode, ch, src, i + (1000 if iid_key else 0)) if seed is None else seed
    return make_r4(mode, seed, ch, P._G['pool'][src], P._G['words'], P._G['lib'], q, i, win=win, iid_key=iid_key)


def q_for(ch, src, qover):
    return P._G['q'].get(f'{ch}|{src}|lib', 0.8) if qover is None else qover


def run_task(t):
    """t = (variant, mode, ch, src, i, n, kind) kind 'plant' | 'null'; writes one record, returns (name, seconds)"""
    variant, mode, ch, src, i, n, kind = t
    dest = REC / f'{variant}_{mode}_{ch}_{src}_{i}_n{n}_{kind}.json'
    if dest.exists():
        return dest.name, 0.0
    nu, qover = VARIANTS[variant]
    q = q_for(ch, src, qover)
    pi, L = P._G['pi'], P._G['L']
    dec = P.DECODER[ch]
    pl = plant_for(mode, ch, src, i, q)
    if kind == 'null':
        npl = plant_for(mode, ch, src, i, q, iid_key=True)
        npl['keyl'] = pl['keyl']; npl['o_true'] = -10 ** 6
        r = search(npl, n, dec, pi, L, nu)
        pl_use = npl
    else:
        r = search(pl, n, dec, pi, L, nu)
        pl_use = pl
    ne = [k for k in pl_use['edge_pos'] if k < n]
    nn = [k for k in pl_use['null_pos'] if k < n]
    r.update(variant=variant, mode=mode, channel=ch, src=src, index=i, n=n, kind=kind, q_plant=q, nu_dec=nu, stream_len=pl['stream_len'], stream=pl['name'],
             nulls=len(nn), edge_nulls=len(ne), T_repairs=pl['T_repairs'])
    X._save(dest, r)
    return dest.name, r['seconds']


def specs(modes, seeds):
    return [(m, ch, src, i) for m in modes for ch in CHS for src in SRCS for i in seeds]


def run_pool(tasks, workers):
    tasks = [t for t in tasks if not (REC / f'{t[0]}_{t[1]}_{t[2]}_{t[3]}_{t[4]}_n{t[5]}_{t[6]}.json').exists()]
    print(len(tasks), 'tasks', flush=True)
    with cf.ProcessPoolExecutor(max_workers=min(workers, 3), initializer=init_plants) as ex:
        futs = [ex.submit(run_task, t) for t in tasks]
        for k, f in enumerate(cf.as_completed(futs), 1):
            print(f'[{time.strftime("%H:%M:%S")}] {k}/{len(tasks)} {f.result()}', flush=True)


# ---------- controls ----------
def control_task(a):
    """rerun one s01 plant with this script's generator (window 300, s01's seed) and search; compare with s01's record"""
    mode, ch, src, i = a
    old = json.loads((S01 / f'{mode}_{ch}_{src}_{i:02d}.json').read_text())
    q = P._G['q'].get(f'{ch}|{src}|lib', 0.8)
    pi, L = P._G['pi'], P._G['L']
    import s01_edge_plants as S1
    mine = make_r4(mode, s01_seed(mode, ch, src, i), ch, P._G['pool'][src], P._G['words'], P._G['lib'], q, i, win=300)
    ref = S1.make_r4(mode, ch, src, i, P._G['pool'][src], P._G['words'], P._G['lib'], q)
    same = all(mine[k] == ref[k] for k in ('cipher', 'ws', 'we', 'keyl', 'offset', 'e', 'o_true', 'name'))
    out = dict(mode=mode, channel=ch, src=src, index=i, generator_identical=same, stream_len=mine['stream_len'])
    for n in (150, 300):
        r = search(mine, n, P.DECODER[ch], pi, L, 0.42)
        o = old[str(n)]
        out[str(n)] = dict(new_band=r['band_best'], old_band=o['band_best'], new_winner=r['winner_score'], old_winner=o['winner_score'], new_detected=r['detected'], old_detected=o['detected'],
                           new_within3=r['true_within3'], old_within3=o['true_within3'], absdiff=abs(r['band_best'] - o['band_best']), seconds=r['seconds'])
    return out


def control(workers):
    # choose the four s01 plants (per mode) with the shortest planted streams, at least one hold and one spend
    cand = []
    for mode in ('any', 'interior'):
        for ch in CHS:
            for src in SRCS:
                for i in range(3):
                    old = json.loads((S01 / f'{mode}_{ch}_{src}_{i:02d}.json').read_text())
                    cand.append((old['stream_len'], mode, ch, src, i))
    pick = []
    for mode in ('any', 'interior'):
        c = sorted(x for x in cand if x[1] == mode)
        sel = [x for x in c if x[2] == 'm04'][:2] + [x for x in c if x[2] == 'spend'][:2]
        pick += [x[1:] for x in sel]
    print('control plants (mode, channel, src, idx, stream len):', [(*p, next(x[0] for x in cand if x[1:] == p)) for p in pick], flush=True)
    res = []
    with cf.ProcessPoolExecutor(max_workers=min(workers, 3), initializer=init_plants) as ex:
        for f in cf.as_completed([ex.submit(control_task, p) for p in pick]):
            res.append(f.result()); print(res[-1], flush=True)
    X._save(DEST / 'control_s01.json', res)


# ---------- summary ----------
def wilson(k, n, z=1.96):
    if n == 0:
        return (float('nan'), float('nan'))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def load_recs():
    return [json.loads(p.read_text()) for p in sorted(REC.glob('*.json'))]


def summary():
    recs = load_recs()
    pl = [r for r in recs if r['kind'] == 'plant']
    nl = [r for r in recs if r['kind'] == 'null']
    out = [f'# R4 repair s05: power map of the unchanged mid arc on R4 plants (plants only; T300 = {C.T300:.2f} used at every n; "lo" = Wilson 95% lower bound, "hi" = upper)',
           '# columns: detected k/N (lo-hi) | true within 3 nats of the global best | band min / median / max | wrong-cell best (median of undetected-or-all) | matched null max']
    names = {'base': 'decoder nu 0.42, plant q frozen (~0.81)', 'nu030': 'decoder nu 0.30', 'nu055': 'decoder nu 0.55', 'q070': 'plant q 0.70 (decoder nu 0.42)', 'q095': 'plant q 0.95 (decoder nu 0.42)'}
    for variant in VARIANTS:
        for mode in ('any', 'interior'):
            ns = sorted({r['n'] for r in pl if r['variant'] == variant and r['mode'] == mode})
            if not ns:
                continue
            out.append('')
            out.append(f'## {variant}: {names[variant]}, slot mode {mode}')
            for n in ns:
                sel = [r for r in pl if r['variant'] == variant and r['mode'] == mode and r['n'] == n]
                k = sum(r['detected'] for r in sel)
                lo, hi = wilson(k, len(sel))
                band = sorted(r['band_best'] for r in sel)
                nsel = [r for r in nl if r['variant'] == variant and r['mode'] == mode and r['n'] == n]
                nm = f'{max(r["winner_score"] for r in nsel):.1f} (N={len(nsel)})' if nsel else '-'
                out.append(f'n {n:3d}: detected {k:2d}/{len(sel):2d} ({100 * lo:3.0f}-{100 * hi:3.0f}%) | within3 {sum(r["true_within3"] for r in sel):2d}/{len(sel)} | '
                           f'band {band[0]:6.1f} / {float(np.median(band)):6.1f} / {band[-1]:6.1f} | wrong-cell best median {float(np.median([r["wrong_best"] for r in sel])):6.1f} | null max {nm}')
                na = [r for r in sel if 'wrong_nonalias3' in r]
                if na:
                    out.append(f'        non-alias view ({len(na)} plants): within3 {sum(r["within3_nonalias3"] for r in na)}/{len(na)}, best wrong cell outside the true key window (median / max) '
                               f'{float(np.median([r["wrong_nonalias3"] for r in na])):.1f} / {max(r["wrong_nonalias3"] for r in na):.1f}')
                for ch in CHS:
                    s2 = [r for r in sel if r['channel'] == ch]
                    for src in SRCS:
                        s3 = [r for r in s2 if r['src'] == src]
                        out.append(f'        {ch:5s} {src:7s}: {sum(r["detected"] for r in s3)}/{len(s3)} bands ' + ' '.join(f'{r["band_best"]:.1f}' for r in sorted(s3, key=lambda r: r['index'])))
                bad = [r for r in sel if not r['detected']]
                for r in bad:
                    out.append(f'        UNDETECTED {r["channel"]} {r["src"]} {r["index"]}: true cell {r["band_best"]:.1f}, best wrong cell {r["wrong_best"]:.1f} (non-alias {r.get("wrong_nonalias3", float("nan")):.1f}), global winner {r["winner_score"]:.1f}, edge nulls {r["edge_nulls"]}/{r["nulls"]}, stream len {r["stream_len"]}')
    out.append('')
    out.append('## paired comparison on the same 24 plants (seeds 0-5), any mode: detected / median band / median change of the true-cell score against base (nats) / plants whose detection changed (lost, gained)')
    key = lambda r: (r['channel'], r['src'], r['index'], r['n'])
    base24 = {key(r): r for r in pl if r['variant'] == 'base' and r['mode'] == 'any' and r['index'] < 6}
    for n in NS_ALL:
        b = [r for r in base24.values() if r['n'] == n]
        if not b:
            continue
        for variant in VARIANTS:
            sel = [r for r in pl if r['variant'] == variant and r['mode'] == 'any' and r['n'] == n and r['index'] < 6]
            if len(sel) != len(b):
                continue
            d = [r['band_best'] - base24[key(r)]['band_best'] for r in sel]
            lost = sum(1 for r in sel if base24[key(r)]['detected'] and not r['detected'])
            gained = sum(1 for r in sel if not base24[key(r)]['detected'] and r['detected'])
            k = sum(r['detected'] for r in sel)
            lo, hi = wilson(k, len(sel))
            out.append(f'n {n:3d} {variant:6s}: detected {k:2d}/{len(sel)} ({100 * lo:3.0f}-{100 * hi:3.0f}%) median band {float(np.median([r["band_best"] for r in sel])):6.1f}, '
                       f'median change {float(np.median(d)):+6.2f} (min {min(d):+.1f}, max {max(d):+.1f}), lost {lost}, gained {gained}')
    out.append('')
    out.append('## band score (true cell) by n, base, any mode, all plants: median / per-rune slope; and interior reference')
    for mode in ('any', 'interior'):
        row = []
        for n in NS_ALL:
            sel = [r for r in pl if r['variant'] == 'base' and r['mode'] == mode and r['n'] == n]
            if sel:
                row.append(f'n {n}: {float(np.median([r["band_best"] for r in sel])):.1f}')
        out.append(f'{mode:8s}: ' + ' | '.join(row))
    out.append('')
    out.append('## matched iid-key nulls (same layout, random key, true stream searched at every offset / sign / channel), max winner score by variant / mode / n')
    for variant in VARIANTS:
        for mode in ('any', 'interior'):
            row = []
            for n in NS_ALL:
                nsel = [r for r in nl if r['variant'] == variant and r['mode'] == mode and r['n'] == n]
                if nsel:
                    row.append(f'n {n}: {max(r["winner_score"] for r in nsel):.1f} (N={len(nsel)})')
            if row:
                out.append(f'{variant:6s} {mode:8s}: ' + ' | '.join(row))
    txt = '\n'.join(out) + '\n'
    (DEST / 'summary.txt').write_text(txt, encoding='utf-8', newline='\n')
    print(txt)


def plan(args):
    init_plants()
    tot = 0.0
    for mode in args.modes.split(','):
        for ch, src in [(c, s) for c in CHS for s in SRCS]:
            row = []
            for i in SEEDS:
                pl = plant_for(mode, ch, src, i, q_for(ch, src, None))
                row.append(pl['stream_len'])
            print(mode, ch, src, row)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('plan', 'control', 'run', 'summary', 'redo'))
    ap.add_argument('--workers', type=int, default=3)
    ap.add_argument('--variants', default='base')
    ap.add_argument('--modes', default='any')
    ap.add_argument('--ns', default='100,150,200,300')
    ap.add_argument('--seeds', default='0,1,2,3,4,5')
    ap.add_argument('--nulls', action='store_true', help='also run matched iid-key null plants (seed indices given by --null-seeds)')
    ap.add_argument('--null-seeds', default='0,1,2')
    a = ap.parse_args()
    DEST.mkdir(parents=True, exist_ok=True)
    REC.mkdir(parents=True, exist_ok=True)
    if a.cmd == 'summary':
        return summary()
    if a.cmd == 'plan':
        return plan(a)
    if a.cmd == 'redo':
        # rerun (with the fixed non-alias columns) the records of the given variant / n that were undetected; the old record moves to rec_first_pass2
        old = DEST / 'rec_first_pass2'
        old.mkdir(exist_ok=True)
        tasks = []
        for p in sorted(REC.glob(f'{a.variants}_*_plant.json')):
            r = json.loads(p.read_text())
            if r['n'] in [int(x) for x in a.ns.split(',')] and 'wrong_nonalias3' not in r:
                p.replace(old / p.name)
                tasks.append((r['variant'], r['mode'], r['channel'], r['src'], r['index'], r['n'], 'plant'))
        return run_pool(tasks, a.workers)
    if a.cmd == 'control':
        return control(a.workers)
    ns = [int(x) for x in a.ns.split(',')]
    seeds = [int(x) for x in a.seeds.split(',')]
    nseeds = [int(x) for x in a.null_seeds.split(',')]
    tasks = []
    for n in ns:     # cheapest n first
        for v in a.variants.split(','):
            for (m, ch, src, i) in specs(a.modes.split(','), seeds):
                tasks.append((v, m, ch, src, i, n, 'plant'))
                if a.nulls and i in nseeds:
                    tasks.append((v, m, ch, src, i, n, 'null'))
    run_pool(tasks, a.workers)


if __name__ == '__main__':
    main()
