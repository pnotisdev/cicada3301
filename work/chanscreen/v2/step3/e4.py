"""E4: 200 library-scale plants (mid-text windows) searched over their own stream, plus prefix plants for the clause scan.

    python e4.py run [--workers N] [--viterbi]       # one JSON per plant in results/chanscreen/e4/ (resumable)
    python e4.py summary                             # results/chanscreen/e4_summary.txt (+ .json)

Protocol: PROTOCOL.md section E4. Plants use the independent v1 encryptors (work/m04/m04.py), a uniformly drawn library
stream and offset, an encrypted plaintext of 300 + e runes (e in 0..99) and the window of the 300 ciphertext runes after
the first e, so the decoder gets no previous ciphertext rune. Only the planted stream is searched.
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

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import m04 as M  # noqa: E402
import run_baseline as B  # noqa: E402

DEST = C.OUT / 'e4'
PER_CHANNEL = 50
PLANT_CHANNELS = ('m04', 'spend', 'skip', 'coin')          # encryptor names
DECODER = {'m04': 'hold', 'spend': 'spend', 'skip': 'skip5', 'coin': 'coin'}
PREFIXES = (60, 80, 100, 150, 200)
_G = {}


def _init():
    _G['lib'] = C.read_library()
    _G['pi'], _G['L'] = C.model()
    _G['q'] = json.loads((C.V1 / 'frozen.json').read_text())['q']
    _G['pool'] = {s: B.pool('held', s) for s in ('cicada', 'english')}


def plant_list():
    out = []
    for ch in PLANT_CHANNELS:
        for i in range(PER_CHANNEL):
            out.append((ch, 'cicada' if i % 2 == 0 else 'english', i))
    return out


def seed(ch, src, i):
    return int.from_bytes(hashlib.sha256(f'chanscreen-step3-plant|{ch}|{src}|{i}'.encode()).digest()[:8], 'big')


def need_extent(ch, n):
    return {'m04': 1, 'spend': 1, 'skip': 6, 'coin': 3}[ch] * n + 16


def encrypt(ch, plain, key, off, q, rng, mult):
    if ch == 'm04':
        return M.enc_m04(plain, key, off, q, rng, mult)
    if ch == 'spend':
        return M.enc_spend(plain, key, off, q, rng, mult)
    if ch == 'skip':
        return M.enc_skip(plain, key, off, rng, mult=mult)
    return M.enc_coin(plain, key, off, rng, mult=mult)


def search(c, key, true_sign, true_ch, o_true, n_label):
    """all 8 passes over the planted stream; returns the summary dict for this window length"""
    pi, L = _G['pi'], _G['L']
    logW = C.log_common(c, C.Q_DECODER, C.Q)
    best = (-math.inf, None)
    band_best = -math.inf
    exact = -math.inf
    null_counts = {t: 0 for t in (0, 5, 10)}
    n_null = 0
    per = {}
    for sign in C.SIGNS:
        for ch in C.CHANNELS:
            sg, s = C.guard_scores(c, key, sign, ch, C.Q_DECODER, pi, L, logW)
            lo, hi = max(0, o_true - C.ALIAS_K), min(len(sg), o_true + C.ALIAS_K + 1)
            mask = np.ones(len(sg), dtype=bool)
            if sign == true_sign:
                mask[lo:hi] = False
            for t in null_counts:
                null_counts[t] += int(np.count_nonzero(sg[mask] >= t))
            n_null += int(mask.sum())
            k = int(np.argmax(sg))
            if sg[k] > best[0]:
                best = (float(sg[k]), (sign, ch, k))
            if sign == true_sign and ch == true_ch:
                b0, b1 = max(0, o_true - 3), min(len(sg), o_true + 4)
                band_best = float(np.max(sg[b0:b1]))
                exact = float(sg[o_true]) if o_true < len(sg) else -math.inf
            per[f'{sign}|{ch}'] = (float(sg[k]), k)
    w = best[1]
    return dict(n=n_label, detected=bool(band_best >= C.T300), band_best=band_best, exact=exact, winner_score=best[0],
                winner=dict(sign=w[0], channel=w[1], offset=w[2]) if w else None,
                winner_is_true=bool(w and w[0] == true_sign and w[1] == true_ch and abs(w[2] - o_true) <= 3),
                winner_sign_ok=bool(w and w[0] == true_sign), winner_channel_ok=bool(w and w[1] == true_ch),
                null_counts=null_counts, n_null=n_null, expected_null={t: n_null * math.exp(-t) for t in null_counts})


def one(args):
    ch, src, i, viterbi = args
    dest = DEST / f'{ch}_{src}_{i:02d}.json'
    if dest.exists():
        return str(dest.name), 0.0
    t0 = time.perf_counter()
    rng = random.Random(seed(ch, src, i))
    lib = _G['lib']
    e = rng.randrange(100)
    n_total = 300 + e
    plain_pool = _G['pool'][src]
    s = rng.randrange(len(plain_pool) - n_total + 1)
    plain = plain_pool[s:s + n_total]
    need = need_extent(ch, n_total)
    eligible = [k for k, (_, v) in enumerate(lib) if len(v) >= need + 1]
    si = eligible[rng.randrange(len(eligible))]
    name, key = lib[si]
    off = rng.randrange(len(key) - need + 1)
    mult = 1 if i % 4 < 2 else 28
    true_sign = 1 if mult == 1 else -1
    qplant = _G['q'].get(f'{ch}|{src}|lib', 0.8)
    keyl = [int(x) for x in key]
    out, used, rep = encrypt(ch, plain, keyl, off, qplant, rng, mult)
    cwin = [int(x) for x in out[e:e + 300]]
    o_true = int(used[e])
    rec = dict(channel=ch, src=src, index=i, stream=name, stream_index=si, stream_len=len(key), offset=off, e=e, mult=mult, q_plant=qplant,
               true_offset=o_true, repairs=int(sum(rep[e:e + 300])), doublets=M.doublets(cwin))
    true_dec = DECODER[ch]
    rec['full'] = search(cwin, key, true_sign, true_dec, o_true, 300)
    rec['prefix'] = {str(n): search(cwin[:n], key, true_sign, true_dec, o_true, n) for n in PREFIXES}
    if viterbi and rec['full']['detected']:
        from reconstruct import viterbi as vit
        w = rec['full']['winner']
        kind = w['channel']
        ext = {'hold': 1, 'spend': 1, 'skip5': 6, 'coin': 3}[kind] * 300 + 16
        sl = keyl[w['offset']:w['offset'] + ext]
        pp, jj, v = vit(cwin, sl, 0, w['sign'], C.Q_DECODER, kind, _G['pi'], _G['L'])
        truth = plain[e:e + 300]
        rec['viterbi_accuracy'] = (sum(a == b for a, b in zip(pp, truth)) / 300) if pp else None
    rec['seconds'] = time.perf_counter() - t0
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix('.tmp')
    tmp.write_text(json.dumps(rec, indent=1, allow_nan=True))
    os.replace(tmp, dest)
    return str(dest.name), rec['seconds']


def run(workers, viterbi):
    todo = [(ch, src, i, viterbi) for ch, src, i in plant_list() if not (DEST / f'{ch}_{src}_{i:02d}.json').exists()]
    print(f'{len(todo)} plants to do', flush=True)
    t0 = time.perf_counter()
    with cf.ProcessPoolExecutor(max_workers=workers, initializer=_init) as ex:
        futs = [ex.submit(one, a) for a in todo]
        for k, f in enumerate(cf.as_completed(futs), 1):
            n, dt = f.result()
            print(f'[{time.strftime("%H:%M:%S")}] {k}/{len(todo)} {n} {dt:.1f}s', flush=True)


def summary():
    recs = [json.loads(p.read_text()) for p in sorted(DEST.glob('*.json'))]
    L = [f'# E4 (step3): {len(recs)} library-scale plants, T300 = {C.T300:.4f} nats, alias band +-{C.ALIAS_K}, decoder q = {C.Q_DECODER}', '']
    def rate(sel, key):
        return sum(1 for r in sel if r[key]['detected']) if key == 'full' else None
    L.append('1. Detection at 300 runes (true cell within +-3 offsets, true sign and channel, S_guard >= T)')
    tot = 0
    for ch in PLANT_CHANNELS:
        for src in ('cicada', 'english'):
            sel = [r for r in recs if r['channel'] == ch and r['src'] == src]
            d = sum(r['full']['detected'] for r in sel)
            tot += d
            L.append(f'   {DECODER[ch]:6s} {src:8s} {d:3d} / {len(sel)}   winner = true cell (+-3) {sum(r["full"]["winner_is_true"] for r in sel):3d}   winner sign ok {sum(r["full"]["winner_sign_ok"] for r in sel):3d}')
        sel = [r for r in recs if r['channel'] == ch]
        L.append(f'   {DECODER[ch]:6s} all      {sum(r["full"]["detected"] for r in sel):3d} / {len(sel)}')
    L.append(f'   pooled {tot} / {len(recs)}')
    L.append('')
    L.append('2. Detection of prefixes (windows shorter than 300 runes; the power of the clause scan)')
    for n in PREFIXES:
        row = '   n=%3d: ' % n
        for ch in PLANT_CHANNELS:
            sel = [r for r in recs if r['channel'] == ch]
            row += f'{DECODER[ch]} {sum(r["prefix"][str(n)]["detected"] for r in sel):2d}/{len(sel)}  '
        row += f'pooled {sum(r["prefix"][str(n)]["detected"] for r in recs)}/{len(recs)}'
        L.append(row)
    L.append('')
    L.append('3. Wrong-offset exceedances outside the alias band (null cells), against N_null e^-t (a diagnostic, not a stop)')
    for t in ('0', '5', '10'):
        obs = sum(r['full']['null_counts'][t] for r in recs)
        exp = sum(r['full']['expected_null'][t] for r in recs)
        L.append(f'   t = {t:>2s}: observed {obs} in {sum(r["full"]["n_null"] for r in recs)} cells, expected at most {exp:.2f}')
    L.append('')
    acc = [r['viterbi_accuracy'] for r in recs if r.get('viterbi_accuracy') is not None]
    if acc:
        L.append(f'4. Viterbi plaintext accuracy of the winner of detected plants: n={len(acc)}, mean {np.mean(acc):.4f}, >= .95 in {sum(a >= .95 for a in acc)}')
    L.append('')
    L.append('5. Window starts: first-rune repair (the decoder assumes none): ' + str(sum(1 for r in recs if r['repairs'] and False)) + ' (not separately tracked)')
    (C.OUT / 'e4_summary.txt').write_text('\n'.join(L) + '\n')
    (C.OUT / 'e4_summary.json').write_text(json.dumps(recs, indent=1))
    print('\n'.join(L))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('run', 'summary'))
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--viterbi', action='store_true')
    a = ap.parse_args()
    if a.cmd == 'run':
        run(a.workers, a.viterbi)
    else:
        summary()
