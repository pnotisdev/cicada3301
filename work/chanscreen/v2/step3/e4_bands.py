"""Amendment 2 (post hoc diagnostic, written after E4): how far from the true offset do high-scoring cells reach?

The same 200 plants as E4 are rebuilt from their seeds (no new randomness) and the cells with S_guard >= 10 are counted outside
bands of +-20, 40, 60, 100, 200 offsets around the true offset, separately for the true sign (all four channels) and for the
other sign (a genuine null: a different key), against the Markov bound N e^-10. The hold likelihood sums over paths that may
re-synchronise by holding the pointer (about -6 nats per hold), so aliases of a strong true cell reach tens of offsets.

    python e4_bands.py run [--workers N]    ->  results/chanscreen/e4_bands.json, e4_bands.txt
"""
import argparse
import concurrent.futures as cf
import json
import math
import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import e4  # noqa: E402

BANDS = (20, 40, 60, 100, 200)


def one(args):
    ch, src, i = args
    G = e4._G
    rng = random.Random(e4.seed(ch, src, i))
    lib = G['lib']
    e = rng.randrange(100)
    n_total = 300 + e
    pool = G['pool'][src]
    s = rng.randrange(len(pool) - n_total + 1)
    plain = pool[s:s + n_total]
    need = e4.need_extent(ch, n_total)
    eligible = [k for k, (_, v) in enumerate(lib) if len(v) >= need + 1]
    si = eligible[rng.randrange(len(eligible))]
    name, key = lib[si]
    off = rng.randrange(len(key) - need + 1)
    mult = 1 if i % 4 < 2 else 28
    q = G['q'].get(f'{ch}|{src}|lib', 0.8)
    out, used, rep = e4.encrypt(ch, plain, [int(x) for x in key], off, q, rng, mult)
    cwin = [int(x) for x in out[e:e + 300]]
    o_true = int(used[e])
    true_sign = 1 if mult == 1 else -1
    logW = C.log_common(cwin, C.Q_DECODER, C.Q)
    row = dict(channel=ch, src=src, index=i, stream=name, stream_len=len(key), true_sign=true_sign,
               true_band={}, other_sign={}, cells=0, max_distance_true_sign=0)
    for b in BANDS:
        row['true_band'][b] = 0
    row['other_sign'] = 0
    for sign in C.SIGNS:
        for chn in C.CHANNELS:
            sg, _ = C.guard_scores(cwin, key, sign, chn, C.Q_DECODER, G['pi'], G['L'], logW)
            idx = np.flatnonzero(sg >= 10)
            row['cells'] += len(sg)
            if sign != true_sign:
                row['other_sign'] += len(idx)
            else:
                d = np.abs(idx - o_true)
                for b in BANDS:
                    row['true_band'][b] += int(np.count_nonzero(d > b))
                if len(d):
                    row['max_distance_true_sign'] = max(row['max_distance_true_sign'], int(d.max()))
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('run',))
    ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()
    todo = e4.plant_list()
    with cf.ProcessPoolExecutor(max_workers=a.workers, initializer=e4._init) as ex:
        rows = list(ex.map(one, todo))
    (C.OUT / 'e4_bands.json').write_text(json.dumps(rows, indent=1))
    L = ['# E4 amendment 2: cells with S_guard >= 10 away from the true offset (same 200 plants rebuilt from their seeds)', '']
    long_ = [r for r in rows if r['stream_len'] >= 10000]
    short = [r for r in rows if r['stream_len'] < 10000]
    for name, sel in (('all 200 plants', rows), ('106 long (>= 10,000 values, non-periodic hash/number streams)', long_), ('94 short (about 2,000 values: keyword and short periodic streams)', short)):
        L.append(name)
        for b in BANDS:
            L.append(f'   true sign, distance > {b:3d}: {sum(r["true_band"][b] for r in sel):8d} cells')
        L.append(f'   other sign (null): {sum(r["other_sign"] for r in sel):8d} cells of {sum(r["cells"] for r in sel) // 2:,}; Markov bound at t = 10: {sum(r["cells"] for r in sel) // 2 * math.exp(-10):.1f}')
        L.append(f'   largest distance of a cell >= 10 from the true offset (true sign): {max(r["max_distance_true_sign"] for r in sel)}')
        L.append('')
    (C.OUT / 'e4_bands.txt').write_text('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
