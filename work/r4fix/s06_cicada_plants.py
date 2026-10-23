"""R4 repair session s06: would the unchanged mid arc still find R4 plants if Cicada added its literal-F habit (plaintext F written as F, key does not advance)?

Plants only; no LP2 ciphertext is scored. The generator is `make_r4` of work/r4fix/s01_edge_plants.py (mode `any`: null slot 0..L, R4 as FITTED), copied with one
switch, `literal_f`. Imports are read-only (s01, phase 57's plant_mid / lp_pilot_mid).

Literal-F rule as implemented (every choice is documented in work/log/r4fix_s06_cicada_plants.md):
  at a plaintext rune with Gematria 0 (F) the cipher rune is F (0) itself and the key pointer j does not advance (hold and spend alike);
  a literal F is clear text, so it is NOT subject to the anti-repeat check / repair (it is written even when it equals the previous cipher rune);
  it IS a cipher rune for everything downstream: the next rune's collision check sees it as `prev`, the in-word lag-6 repair T(c[-6]) reads it, word flags are unchanged;
  the null is unchanged (uniform, never equal to its left neighbour, may be F by chance); an enciphered non-F rune that happens to equal 0 is an ordinary cipher F.
  The window start is moved forward past nulls AND literal F (the decoder's true offset o_true is the key index at the first window rune, which a literal F does not have).
  With literal_f False the function is byte-identical to s01's make_r4 (mode `any`): the positive control, checked against s01's stored records for seeds 0-2.

    python -B work/r4fix/s06_cicada_plants.py one                     # timing / memory probe
    python -B work/r4fix/s06_cicada_plants.py plants [--workers 3]    # 48 plants: lf / ctl x hold, spend x cicada, english x 6 seeds, n 150 + 300, + matched iid-key nulls
    python -B work/r4fix/s06_cicada_plants.py fshare                  # F share of the plant streams (no search), 150 layouts per source and condition
    python -B work/r4fix/s06_cicada_plants.py summary                 # -> results/r4fix/s06_cicada_plants/summary.txt
"""
import argparse
import concurrent.futures as cf
import json
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import s01_edge_plants as S1  # noqa: E402

X, P, C, LPM = S1.X, S1.P, S1.C, S1.LPM
Q = S1.Q
DEST = ROOT / 'results' / 'r4fix' / 's06_cicada_plants'
CONDS = ('lf', 'ctl')
NSEED = 6
PLANTS = [(ch, src, i) for ch in ('m04', 'spend') for src in ('cicada', 'english') for i in range(NSEED)]
RHO = S1.RHO
LP2_RUNES, LP2_F, LP2_F_EXP = 12956, 458, 447.0     # registry row obs-flat


def make_r4(mode, ch, src, i, pool, words_by_sec, lib, q, rho=RHO, iid_key=False, literal_f=False):
    rng = random.Random(S1.seed_for(mode, ch, src, i))
    e0 = rng.randrange(100)
    sec = P.SECS[rng.randrange(len(P.SECS))]
    wl = words_by_sec[sec]
    w = rng.randrange(len(wl) - 150)
    items, plain_len = [], 0
    while len(items) < e0 + 320 + 40:
        L = wl[w]
        slot = S1.draw_slot(rng, L, mode, rho)
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
    out, used, isnull, wstart, wend, isedge, isF = [], [], [], [], [], [], []
    j, w0, nT, nplainF = off, 0, 0, 0
    for it in items:
        if it[2]:
            w0 = len(out)
        prev = out[-1] if out else None
        if it[0] == 'n':
            v = rng.randrange(Q)
            while v == prev:
                v = rng.randrange(Q)
            out.append(v); used.append(-1); isnull.append(True); wstart.append(it[2]); wend.append(it[3]); isedge.append(it[4]); isF.append(False)
            continue
        if plain[it[1]] == 0:
            nplainF += 1
            if literal_f:
                out.append(0); used.append(-1); isnull.append(False); wstart.append(it[2]); wend.append(it[3]); isedge.append(False); isF.append(True)
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
        out.append(x); used.append(u); isnull.append(False); wstart.append(it[2]); wend.append(it[3]); isedge.append(False); isF.append(False)
    e = e0
    while isnull[e] or isF[e]:
        e += 1
    sl = slice(e, e + 300)
    return dict(name=name, stream_index=si, keyl=keyl, stream_len=len(keyl), offset=off, e=e, mult=mult, true_sign=1 if mult == 1 else -1,
                cipher=[int(x) for x in out[sl]], ws=[int(x) for x in wstart[sl]], we=[int(x) for x in wend[sl]], o_true=int(used[e]),
                nulls_in_window=int(sum(isnull[sl])), T_repairs=nT, sec=sec,
                null_pos=[k for k, v in enumerate(isnull[sl]) if v], edge_pos=[k for k, v in enumerate(isedge[sl]) if v],
                litF_pos=[k for k, v in enumerate(isF[sl]) if v],
                all_len=len(out), all_F=int(sum(1 for x in out if x == 0)), all_litF=int(sum(isF)), all_plainF=nplainF,
                all_nonnull=int(len(out) - sum(isnull)))


def fstats(pl, n):
    return dict(F_cipher=int(sum(1 for x in pl['cipher'][:n] if x == 0)), F_literal=int(sum(1 for k in pl['litF_pos'] if k < n)),
                nulls=int(sum(1 for k in pl['null_pos'] if k < n)))


def run_plant(cond, ch, src, i, ns=(150, 300)):
    t0 = time.perf_counter()
    lf = cond == 'lf'
    q = P._G['q'].get(f'{ch}|{src}|lib', 0.8)
    pl = make_r4('any', ch, src, i, P._G['pool'][src], P._G['words'], P._G['lib'], q, literal_f=lf)
    npl = make_r4('any', ch, src, i + 1000, P._G['pool'][src], P._G['words'], P._G['lib'], q, iid_key=True, literal_f=lf)
    npl['keyl'] = pl['keyl']; npl['o_true'] = -10 ** 6
    pi, L = P._G['pi'], P._G['L']
    dec = P.DECODER[ch]
    rec = {k: v for k, v in pl.items() if k not in ('keyl', 'cipher', 'ws', 'we', 'null_pos', 'edge_pos', 'litF_pos')}
    rec.update(cond=cond, channel=ch, src=src, index=i, q_plant=q, litF_positions=pl['litF_pos'][:60])
    for n in ns:
        rec[str(n)] = X.search(pl, n, dec, 'mid', pi, L)
        rec[str(n)].update(fstats(pl, n))
        rec[f'null{n}'] = X.search(npl, n, dec, 'mid', pi, L)
    rec['seconds'] = time.perf_counter() - t0
    return rec


def one_plant(args):
    cond, ch, src, i = args
    dest = DEST / f'{cond}_{ch}_{src}_{i:02d}.json'
    if dest.exists():
        return dest.name, 0.0
    rec = run_plant(cond, ch, src, i)
    X._save(dest, rec)
    return dest.name, rec['seconds']


def fshare():
    """F share of the generated cipher streams (all runes, nulls included) without any decoder search: 150 layouts per source / condition / channel-less (hold)"""
    S1.init_plants()
    out = ['# F share of the planted cipher streams (R4 any-slot plants, hold, no search); 150 layouts per row, indices 2000..2149 (not used by the searches)',
           'LP2: 458 F in 12,956 runes = %.3f%%, flat expectation 447 (3.45%%)' % (100 * LP2_F / LP2_RUNES)]
    rows = {}
    for cond in CONDS:
        for src in ('cicada', 'english'):
            tot = F = lit = plainF = nonnull = 0
            for i in range(2000, 2150):
                pl = make_r4('any', 'm04', src, i, P._G['pool'][src], P._G['words'], P._G['lib'], 0.807, literal_f=cond == 'lf')
                tot += pl['all_len']; F += pl['all_F']; lit += pl['all_litF']; plainF += pl['all_plainF']; nonnull += pl['all_nonnull']
            sh = F / tot
            rows[(cond, src)] = sh
            sd = (sh * (1 - sh) / tot) ** .5
            # the LP2 comparison: F count expected in 12,956 runes at this share, and the z of LP2's 458 under it (binomial)
            exp = LP2_RUNES * sh
            z = (LP2_F - exp) / (LP2_RUNES * sh * (1 - sh)) ** .5
            out.append(f'{cond:3s} {src:8s}: {tot} cipher runes ({nonnull} non-null), F {F} = {100 * sh:.2f}% +- {100 * sd:.2f}%; plaintext F share {100 * plainF / nonnull:.2f}%, literal F {lit}; '
                       f'expected F in 12,956 runes {exp:.0f}; LP2 458 is z {z:+.1f} from this stream')
    DEST.mkdir(parents=True, exist_ok=True)
    txt = '\n'.join(out) + '\n'
    (DEST / 'fshare.txt').write_text(txt, encoding='utf-8', newline='\n')
    print(txt)


def summary():
    import numpy as np
    recs = [json.loads(p.read_text()) for p in sorted(DEST.glob('*_*_*_*.json')) if not p.name.startswith('probe')]
    out = [f'# R4 repair s06: R4 (any slot, as fitted) plants with Cicada\'s literal-F rule (lf) vs without (ctl); unchanged mid arc, true stream only, T300 = {C.T300:.2f} (n 150 and 300)',
           f'{len(recs)} plant records']
    for cond in CONDS:
        for n in ('150', '300'):
            sel = [r for r in recs if r['cond'] == cond]
            if not sel:
                continue
            for src in ('all', 'cicada', 'english'):
                s2 = [r for r in sel if src == 'all' or r['src'] == src]
                band = sorted(r[n]['band_best'] for r in s2)
                out.append(f'{cond:3s} n {n} {src:8s}: detected {sum(r[n]["detected"] for r in s2)}/{len(s2)}, within 3 nats {sum(r[n]["true_within3"] for r in s2)}/{len(s2)}, '
                           f'band min / median / max {band[0]:.1f} / {band[len(band) // 2]:.1f} / {band[-1]:.1f}, matched iid-key null max {max(r["null" + n]["winner_score"] for r in s2):.1f}, '
                           f'F in window median {int(np.median([r[n]["F_cipher"] for r in s2]))} (literal {int(np.median([r[n]["F_literal"] for r in s2]))})')
            for ch in ('m04', 'spend'):
                s2 = [r for r in sel if r['channel'] == ch]
                out.append(f'      {ch:5s}: detected {sum(r[n]["detected"] for r in s2)}/{len(s2)} band ' + ' '.join(f'{r[n]["band_best"]:.1f}' for r in s2))
        out.append('')
    # dose-response: band against number of literal F in the window, lf only
    for n in ('150', '300'):
        sel = [r for r in recs if r['cond'] == 'lf']
        if sel:
            x = np.array([r[n]['F_literal'] for r in sel], float)
            y = np.array([r[n]['band_best'] for r in sel], float)
            b = np.polyfit(x, y, 1)
            out.append(f'lf n {n}: literal F per window {int(x.min())}-{int(x.max())}; band vs literal F: slope {b[0]:.2f} nats per F, correlation {np.corrcoef(x, y)[0, 1]:+.2f}')
    # pairing: same seed, lf vs ctl band
    out.append('')
    for n in ('150', '300'):
        d = []
        for r in recs:
            if r['cond'] == 'lf':
                c = [q for q in recs if q['cond'] == 'ctl' and (q['channel'], q['src'], q['index']) == (r['channel'], r['src'], r['index'])]
                if c:
                    d.append(r[n]['band_best'] - c[0][n]['band_best'])
        if d:
            out.append(f'paired by seed (same layout, plaintext, key stream and offset), band lf - ctl, n {n}: median {np.median(d):+.1f}, min {min(d):+.1f}, max {max(d):+.1f}, lf lower in {sum(v < 0 for v in d)}/{len(d)}')
    out.append('')
    # reproduction of s01 'any' for seeds 0-2
    ok, mx = 0, 0.0
    for r in recs:
        if r['cond'] == 'ctl' and r['index'] < 3:
            f = S1.DEST / f'any_{r["channel"]}_{r["src"]}_{r["index"]:02d}.json'
            if f.exists():
                o = json.loads(f.read_text())
                ok += 1
                for n in ('150', '300'):
                    mx = max(mx, abs(o[n]['band_best'] - r[n]['band_best']), abs(o['null' + n]['winner_score'] - r['null' + n]['winner_score']))
    out.append(f'ctl seeds 0-2 against s01 `any` records: {ok} compared, max abs difference in band and matched-null score {mx:.3g}')
    out.append('')
    out.append('per plant: cond channel src idx | n | literal F / F in window / nulls, band, winner, detected, within3, matched null')
    for r in recs:
        for n in ('150', '300'):
            d = r[n]
            out.append(f'{r["cond"]:3s} {r["channel"]:5s} {r["src"]:7s} {r["index"]} | {n:3s} | litF {d["F_literal"]:2d} F {d["F_cipher"]:2d} nulls {d["nulls"]:2d} | band {d["band_best"]:7.1f} winner {d["winner_score"]:7.1f} '
                       f'| det {int(d["detected"])} w3 {int(d["true_within3"])} | null {r["null" + n]["winner_score"]:7.1f}')
    txt = '\n'.join(out) + '\n'
    (DEST / 'summary.txt').write_text(txt, encoding='utf-8', newline='\n')
    print(txt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('one', 'plants', 'fshare', 'summary'))
    ap.add_argument('--workers', type=int, default=3)
    ap.add_argument('--cond', default='lf')
    a = ap.parse_args()
    if a.cmd == 'summary':
        return summary()
    if a.cmd == 'fshare':
        return fshare()
    if a.cmd == 'one':
        S1.init_plants()
        rec = run_plant(a.cond, 'm04', 'cicada', 0)
        X._save(DEST / 'probe.json', rec)
        print({k: rec[k] for k in ('cond', 'seconds')}, {n: (rec[n]['band_best'], rec[n]['detected'], rec[n]['F_literal'], rec[n]['F_cipher'], rec[n]['nulls'], rec['null' + n]['winner_score']) for n in ('150', '300')})
        return
    todo = [(c, *p) for c in CONDS for p in PLANTS]
    todo = [t for t in todo if not (DEST / f'{t[0]}_{t[1]}_{t[2]}_{t[3]:02d}.json').exists()]
    print(len(todo), 'tasks', flush=True)
    with cf.ProcessPoolExecutor(max_workers=min(a.workers, 3), initializer=S1.init_plants) as ex:
        for k, f in enumerate(cf.as_completed([ex.submit(one_plant, t) for t in todo]), 1):
            print(f'[{time.strftime("%H:%M:%S")}] {k}/{len(todo)} {f.result()}', flush=True)


if __name__ == '__main__':
    main()
