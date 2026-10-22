"""Phase 57: decryption search implied by the best-fitting rule (R4: collision repair writes T(c[-6]) = 24 - 2 c[-6], plus one null in ~45% of words). See work/log/phase57_mechanism.md.

The search is the existing chanscreen v2 mid-word arc (work/chanscreen/v2/step4, phase 51): library key streams, hold / spend repair, one interior null per word. Its repair rune is
modelled as a uniform other rune, so a T-valued repair costs it nothing; R4's null is CHECKED (never equals the previous rune) and visible to the anti-repeat rule, which the engine does not model.
    python -B work/phase57_pilot.py plants [--workers 4]   # positive control: R4 plants (library key, hold / spend, cicada / english plaintext), n 150 and 300, + matched iid-key nulls
    python -B work/phase57_pilot.py pilot [--workers 4]    # LP2 window 0.15 @ 0, n 150, full library, both signs, hold / spend / skip5 / coin, below-normal priority
    python -B work/phase57_pilot.py summary                # -> results/analysis/phase57_pilot.txt
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
sys.path.insert(0, str(HERE / 'chanscreen' / 'v2' / 'step4'))
import plant_mid as X  # noqa: E402
import lp_pilot_mid as LPM  # noqa: E402

P, C = X.P, X.C
Q = X.M.Q
DEST_P = C.OUT / 'phase57_plants'
DEST_L = C.OUT / 'phase57_lp_pilot'
SEC, START, NWIN = 15, 0, 150
PLANTS = [(ch, src, i) for ch in ('m04', 'spend') for src in ('cicada', 'english') for i in range(3)]


def make_r4(ch, src, i, pool, words_by_sec, lib, q, rho=0.45, iid_key=False):
    """R4 as a plant: X.make_plant's word layout and key choice, but the repair writes T(c[-6]) when 6 back is in the word, and the null is checked and visible to the anti-repeat rule"""
    rng = random.Random(int.from_bytes(hashlib.sha256(f'phase57-r4|{ch}|{src}|{i}'.encode()).digest()[:8], 'big'))
    e0 = rng.randrange(100)
    sec = P.SECS[rng.randrange(len(P.SECS))]
    wl = words_by_sec[sec]
    w = rng.randrange(len(wl) - 150)
    items, plain_len = [], 0
    while len(items) < e0 + 320 + 40:
        L = wl[w]
        slot = rng.randrange(1, L) if (L >= 2 and rng.random() < rho) else 0
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
    mult = 1 if i % 2 == 0 else 28
    if iid_key:
        keyl = [rng.randrange(Q) for _ in range(len(keyl))]
    out, used, isnull, wstart, wend = [], [], [], [], []
    j, w0, nT = off, 0, 0
    for it in items:
        if it[0] == 'r' and it[2]:
            w0 = len(out)
        prev = out[-1] if out else None
        if it[0] == 'n':
            v = rng.randrange(Q)
            while v == prev:
                v = rng.randrange(Q)
            out.append(v); used.append(-1); isnull.append(True); wstart.append(False); wend.append(False)
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
        out.append(x); used.append(u); isnull.append(False); wstart.append(it[2]); wend.append(it[3])
    e = e0
    while isnull[e]:
        e += 1
    sl = slice(e, e + 300)
    return dict(name=name, stream_index=si, keyl=keyl, stream_len=len(keyl), offset=off, e=e, mult=mult, true_sign=1 if mult == 1 else -1,
                cipher=[int(x) for x in out[sl]], ws=[int(x) for x in wstart[sl]], we=[int(x) for x in wend[sl]], o_true=int(used[e]),
                nulls_in_window=int(sum(isnull[sl])), T_repairs=nT, sec=sec)


def init_plants():
    LPM.lower()
    P._init()


def one_plant(args):
    ch, src, i = args
    dest = DEST_P / f'r4_{ch}_{src}_{i:02d}.json'
    if dest.exists():
        return dest.name, 0.0
    t0 = time.perf_counter()
    q = P._G['q'].get(f'{ch}|{src}|lib', 0.8)
    pl = make_r4(ch, src, i, P._G['pool'][src], P._G['words'], P._G['lib'], q)
    npl = make_r4(ch, src, i + 1000, P._G['pool'][src], P._G['words'], P._G['lib'], q, iid_key=True)
    npl['keyl'] = pl['keyl']; npl['o_true'] = -10 ** 6
    pi, L = P._G['pi'], P._G['L']
    dec = P.DECODER[ch]
    rec = {k: v for k, v in pl.items() if k not in ('keyl', 'cipher', 'ws', 'we')}
    rec.update(channel=ch, src=src, index=i, q_plant=q)
    for n in (150, 300):
        rec[str(n)] = X.search(pl, n, dec, 'mid', pi, L)
        rec[f'null{n}'] = X.search(npl, n, dec, 'mid', pi, L)
    rec['seconds'] = time.perf_counter() - t0
    X._save(dest, rec)
    return dest.name, rec['seconds']


def init_pilot():
    LPM.SEC, LPM.START, LPM.N, LPM.DEST = SEC, START, NWIN, DEST_L
    LPM.init()


def summary():
    out = [f'# Phase 57 planted control (R4 plants, chanscreen v2 mid arc, T300 = {C.T300:.2f} nats used at n 150 and 300)']
    recs = [json.loads(p.read_text()) for p in sorted(DEST_P.glob('*.json'))]
    for n in ('150', '300'):
        det = sum(r[n]['detected'] for r in recs)
        w3 = sum(r[n]['true_within3'] for r in recs)
        band = sorted(r[n]['band_best'] for r in recs)
        nm = max(r[f'null{n}']['winner_score'] for r in recs)
        out.append(f'n {n}: detected {det}/{len(recs)}, true within 3 of best {w3}/{len(recs)}, band min / median {band[0]:.1f} / {band[len(band) // 2]:.1f}; '
                   f'matched iid-key null (same layout, true stream searched, every offset / sign / channel): max {nm:.1f}')
    out.append('T-valued repairs per plant: ' + ' '.join(str(r['T_repairs']) for r in recs) + '; nulls in the 300 window: ' + ' '.join(str(r['nulls_in_window']) for r in recs))
    lrec = [json.loads(p.read_text()) for p in sorted(DEST_L.glob('*.json'))]
    if lrec:
        b = max(lrec, key=lambda r: r['best'])
        out.append(f'# LP2 pilot: section 0.{SEC} @ {START}, n {NWIN}, {len(lrec)} chunks, {sum(r["cells"] for r in lrec):,} cells, CPU {sum(r["seconds"] for r in lrec) / 3600:.2f} h')
        out.append(f'max S_guard {b["best"]:.2f} ({b["argmax"]}); ' + ', '.join(f'>= {t}: {sum(r["counts"][str(t)] for r in lrec)}' for t in (0, 5, 10, 20))
                   + f'; hits >= 10: {sum(len(r["hits"]) for r in lrec)}')
        for r in lrec:
            for h in r['hits']:
                out.append(f'   {h}')
    txt = '\n'.join(out) + '\n'
    (HERE.parent / 'results' / 'analysis' / 'phase57_pilot.txt').write_text(txt, encoding='utf-8', newline='\n')
    print(txt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('plants', 'pilot', 'summary'))
    ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()
    if a.cmd == 'summary':
        return summary()
    if a.cmd == 'plants':
        todo, fn, ini = PLANTS, one_plant, init_plants
    else:
        nch = len(C.chunks([len(v) for _, v in C.read_library()]))
        todo, fn, ini = [ci for ci in range(nch) if not (DEST_L / f'mid_c{ci:02d}.json').exists()], LPM.task, init_pilot
    print(len(todo), 'tasks', flush=True)
    with cf.ProcessPoolExecutor(max_workers=min(a.workers, 4), initializer=ini) as ex:
        for k, f in enumerate(cf.as_completed([ex.submit(fn, t) for t in todo]), 1):
            print(f'[{time.strftime("%H:%M:%S")}] {k}/{len(todo)} {f.result()}', flush=True)


if __name__ == '__main__':
    main()
