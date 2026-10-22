"""Phase 60 T8 under R4: DATA/560.13 (118,818,811 bytes of uniformly random data) as a key under the phase 59 engine and channels (mid-word arc, hold / spend, both signs), unchanged.
Full cost: 0.62 ms per offset and window -> 20 CPU-h for ONE window and ONE map over all 118.8 M offsets, so:
  start: the first 30,000 offsets of bytes mod 29 and of the rejection map, every one of the 48 n300 windows (a pad read from its start: LP2 is 12,956 runes, LP1 3.4 k);
  blocks: window 0.7@0 only, 58 blocks of 100,000 offsets of the mod-29 map at fixed random positions (5.8 M offsets = 4.9% of the file).
    python -B work/phase60_t8_r4.py control | start [--workers N] | blocks [--workers N] | summary
"""
import argparse, concurrent.futures as cf, json, math, random, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase59_keywords_r4 as P59  # noqa: E402

X, C, P, LM, LPM, P57 = P59.X, P59.C, P59.P, P59.LM, P59.LPM, P59.P57
OUT = C.OUT / 'phase60_t8_r4'
F560 = HERE / 'ref' / 'cicados_iso' / '560.13'
START, BLOCK, NBLK = 30000, 100_000, 58
_W = {}


def keyvals(m):
    b = np.fromfile(F560, dtype=np.uint8)
    return (b % 29).astype(np.uint8) if m == 'mod' else (b[b < 232] % 29).astype(np.uint8)


def init():
    LPM.lower()
    _W['pi'], _W['L'] = C.model()
    _W['k'] = {m: keyvals(m) for m in ('mod', 'rej')}


def window(sec, st):
    runes, brk = LM.section_edges(sec)
    c = [int(x) for x in runes[st:st + 300]]
    ws = [1] + [1 if brk[st + i] else 0 for i in range(1, 300)]
    return c, ws, C.log_common(c, C.Q_DECODER, C.Q)


def scan(c, ws, logW, S, o0, M):
    best, hot = (-math.inf, None), []
    for ch in P59.CH:
        ext = P.need_extent(P59.PLCH[ch], 300)
        key = [int(x) for x in S[o0:o0 + M + ext]]
        if len(key) < ext + 1:
            continue
        for sign in C.SIGNS:
            sg = X.guard(c, key, sign, ch, _W['pi'], _W['L'], logW, 'mid', dict(wstart=ws), X.RHO)[:M]
            o = int(np.argmax(sg))
            if sg[o] > best[0]:
                best = (float(sg[o]), (sign, ch, o0 + o))
            for o2 in np.flatnonzero(sg >= 20):
                hot.append((float(sg[o2]), sign, ch, o0 + int(o2)))
    return best, hot


def start_task(args):
    sec, st, m = args
    dest = OUT / 'start' / f'{m}_{sec:02d}_{st:05d}.json'
    if dest.exists():
        return dest.name, 0.0
    t0 = time.perf_counter()
    c, ws, logW = window(sec, st)
    best, hot = scan(c, ws, logW, _W['k'][m], 0, START)
    X._save(dest, dict(sec=sec, start=st, map=m, best=best[0], argmax=list(best[1]) if best[1] else None, hot=hot[:20], n_hot=len(hot), seconds=time.perf_counter() - t0))
    return dest.name, time.perf_counter() - t0


def positions(n):
    rng = random.Random(13560)
    return sorted(rng.randrange(START, n - BLOCK - 400) for _ in range(NBLK))


def block_task(args):
    k, pos = args
    dest = OUT / 'blocks' / f'b{k:03d}_{pos}.json'
    if dest.exists():
        return dest.name, 0.0
    t0 = time.perf_counter()
    if 'w' not in _W:
        _W['w'] = window(7, 0)
    c, ws, logW = _W['w']
    best, hot = scan(c, ws, logW, _W['k']['mod'], pos, BLOCK)
    X._save(dest, dict(block=k, pos=pos, best=best[0], argmax=list(best[1]) if best[1] else None, hot=hot[:20], n_hot=len(hot), seconds=time.perf_counter() - t0))
    return dest.name, time.perf_counter() - t0


def run(tasks, fn, w):
    print(len(tasks), 'tasks', flush=True)
    with cf.ProcessPoolExecutor(max_workers=w, initializer=init) as ex:
        for n, f in enumerate(cf.as_completed([ex.submit(fn, t) for t in tasks]), 1):
            print(f'[{time.strftime("%H:%M:%S")}] {n}/{len(tasks)} {f.result()}', flush=True)


def cmd_control():
    """R4 plants whose key is a 2 M-term slice of the mod map (random true offset in it); a 20,000-offset chunk around the truth is searched (offsets are independent)"""
    LPM.lower(); P._init(); init()
    mod = _W['k']['mod']
    lib = [('b13 slice', mod[5_000_000:7_000_000].tolist())]
    rows = []
    for ch in P59.CH:
        for src in ('cicada', 'english'):
            for i in range(2):
                pl = P57.make_r4(P59.PLCH[ch], src, i + 90, P._G['pool'][src], P._G['words'], lib, P._G['q'].get(f'{P59.PLCH[ch]}|{src}|lib', 0.8))
                v = pl['keyl']; c, ws = pl['cipher'], pl['ws']
                logW = C.log_common(c, C.Q_DECODER, C.Q)
                o_t = pl['o_true']; o0 = max(0, o_t - 10000)
                ext = P.need_extent(P59.PLCH[ch], len(c))
                kk = [int(x) for x in v[o0:o0 + 20000 + ext]]
                best = (-math.inf, None)
                for sign in C.SIGNS:
                    sg = X.guard(c, kk, sign, ch, _W['pi'], _W['L'], logW, 'mid', dict(wstart=ws), X.RHO)[:20000]
                    o = int(np.argmax(sg))
                    if sg[o] > best[0]:
                        best = (float(sg[o]), (sign, o0 + o))
                rows.append(dict(ch=ch, src=src, i=i, true_off=o_t, true_sign=pl['true_sign'], best=best[0], cell=best[1], found=bool(best[0] >= C.T300 and best[1][0] == pl['true_sign'] and abs(best[1][1] - o_t) <= 3)))
                print(rows[-1], flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'control.json').write_text(json.dumps(rows))
    print('control found', sum(r['found'] for r in rows), '/', len(rows))


def summary():
    L = [f'# Phase 60 T8 under R4: DATA/560.13 (118,818,811 random bytes), phase 59 engine, hold / spend, both signs, T300 = {C.T300:.2f}']
    st = [json.loads(p.read_text()) for p in sorted((OUT / 'start').glob('*.json'))]
    bl = [json.loads(p.read_text()) for p in sorted((OUT / 'blocks').glob('*.json'))]
    ctl = json.loads((OUT / 'control.json').read_text()) if (OUT / 'control.json').exists() else []
    if st:
        b = max(st, key=lambda r: r['best'])
        L.append(f'start region (offsets 0..{START}, maps mod / rej, {len(st)} window-map tasks of 96): max S_guard {b["best"]:.2f} (map {b["map"]}, {b["sec"]} @ {b["start"]}, {b["argmax"]}); cells >= 20: {sum(r["n_hot"] for r in st)}; at T300: {sum(r["best"] >= C.T300 for r in st)}; CPU {sum(r["seconds"] for r in st) / 3600:.2f} h')
    if bl:
        b = max(bl, key=lambda r: r['best'])
        L.append(f'sampled blocks (window 7@0, mod map, {len(bl)} blocks of {BLOCK:,} offsets = {len(bl) * BLOCK:,} of 118.8 M): max S_guard {b["best"]:.2f} ({b["argmax"]}); cells >= 20: {sum(r["n_hot"] for r in bl)}; at T300: {sum(r["best"] >= C.T300 for r in bl)}; CPU {sum(r["seconds"] for r in bl) / 3600:.2f} h')
    if ctl:
        L.append(f'control: {sum(r["found"] for r in ctl)}/{len(ctl)} R4 plants with a 560.13 key found at the right sign and offset, score min {min(r["best"] for r in ctl):.1f}')
    t = chr(10).join(L) + chr(10)
    (HERE.parent / 'results' / 'analysis' / 'phase60_t8_560_13_r4.txt').write_text(t, encoding='utf-8'); print(t)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=('control', 'start', 'blocks', 'summary')); ap.add_argument('--workers', type=int, default=3)
    a = ap.parse_args()
    if a.cmd == 'control':
        cmd_control()
    elif a.cmd == 'start':
        run([(s, st, m) for (s, st) in P59.windows() for m in ('mod', 'rej')], start_task, a.workers)
    elif a.cmd == 'blocks':
        n = int((np.fromfile(F560, dtype=np.uint8) % 29).shape[0])
        run(list(enumerate(positions(n))), block_task, a.workers)
    else:
        summary()
