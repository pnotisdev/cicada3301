"""Phase 60 T6: the megabyte Cicada OS files (DATA/560.17, DATA/_560.00) as keys under R4, phase 59 engine and channels unchanged (mid-word arc, hold / spend, both signs).
Offsets are independent in the engine, so a stream is screened in contiguous chunks of offsets; the cost is 0.15 ms per offset and window and (sign, channel). Full cost for
8 streams x 8 section windows x 4 cells would be about 28 CPU-hours, so ONE window is screened over ALL offsets of ALL streams (both signs, hold and spend):
the window is the first n300 window of 0.7 (section start); a key that applies to that window at any offset is found (power 1 for that window, 0 for the other 47).
    python -B work/phase60_t6_blobs_r4.py control | scan [--workers 5] | summary
"""
import argparse, concurrent.futures as cf, json, math, os, random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase59_keywords_r4 as P59  # noqa: E402
import numpy as np  # noqa: E402

X, C, P, LM, LPM, P57 = P59.X, P59.C, P59.P, P59.LM, P59.LPM, P59.P57
OUT = C.OUT / 'phase60_t6'
ARCH = HERE.parent / 'Other repositories and work' / 'The-Complete-Cicada3301-Archive' / 'assets' / '2013' / 'cicados' / 'DATA'
FILES = ('560.17', '_560.00')
CHUNK = 100_000
SEC, START = 7, 0
_W = {}


def streams():
    out = {}
    for f in FILES:
        b = np.frombuffer((ARCH / f).read_bytes(), np.uint8)
        for mode, v in (('mod', b % 29), ('rej', b[b < 232] % 29)):
            v = v.astype(np.int64)
            out[f'{f} {mode} fwd'] = v
            out[f'{f} {mode} rev'] = v[::-1].copy()
    return out


def init():
    LPM.lower()
    _W['pi'], _W['L'] = C.model()
    _W['S'] = streams()
    runes, brk = LM.section_edges(SEC)
    c = [int(x) for x in runes[START:START + 300]]
    ws = [1] + [1 if brk[START + i] else 0 for i in range(1, 300)]
    _W['c'], _W['ws'], _W['logW'] = c, ws, C.log_common(c, C.Q_DECODER, C.Q)


def chunk_task(args):
    name, k = args
    dest = OUT / 'scan' / f'{name.replace(" ", "_")}_{k:04d}.json'
    if dest.exists():
        return dest.name, 0.0
    t0 = time.perf_counter()
    S = _W['S'][name]
    o0 = k * CHUNK
    M = min(CHUNK, len(S) - o0)
    best, hot = (-math.inf, None), []
    for ch in P59.CH:
        ext = P.need_extent(P59.PLCH[ch], 300)
        key = [int(x) for x in S[o0:o0 + M + ext]]
        if len(key) < ext + 1:
            continue
        for sign in C.SIGNS:
            sg = X.guard(_W['c'], key, sign, ch, _W['pi'], _W['L'], _W['logW'], 'mid', dict(wstart=_W['ws']), X.RHO)[:M]
            o = int(np.argmax(sg))
            if sg[o] > best[0]:
                best = (float(sg[o]), (sign, ch, o0 + o))
            for o2 in np.flatnonzero(sg >= 20):
                hot.append((float(sg[o2]), sign, ch, o0 + int(o2)))
    X._save(dest, dict(name=name, chunk=k, offsets=M, best=best[0], argmax=list(best[1]) if best[1] else None, hot=hot[:50], n_hot=len(hot), seconds=time.perf_counter() - t0))
    return dest.name, time.perf_counter() - t0


def cmd_scan(w, reverse=False):
    init_names = streams()
    todo = [(n, k) for n, v in init_names.items() for k in range(-(-len(v) // CHUNK))]
    todo = [t for t in todo if not (OUT / 'scan' / f'{t[0].replace(" ", "_")}_{t[1]:04d}.json').exists()]
    todo = todo[::-1] if reverse else todo
    print(len(todo), 'chunks of', CHUNK, 'offsets', flush=True)
    with cf.ProcessPoolExecutor(max_workers=w, initializer=init) as ex:
        for n, f in enumerate(cf.as_completed([ex.submit(chunk_task, t) for t in todo]), 1):
            print(f'[{time.strftime("%H:%M:%S")}] {n}/{len(todo)} {f.result()}', flush=True)


def cmd_control():
    """R4 plants whose key is a 560.17 / _560.00 stream (random true offset in the whole stream); only a 20,000-offset chunk around the truth is searched (offsets are independent)"""
    LPM.lower(); P._init(); init()
    S = _W['S']
    lib = [(n, v.tolist()) for n, v in S.items() if 'rej fwd' in n]
    rows = []
    for ch in P59.CH:
        for src in ('cicada', 'english'):
            for i in range(2):
                pl = P57.make_r4(P59.PLCH[ch], src, i + 60, P._G['pool'][src], P._G['words'], lib, P._G['q'].get(f'{P59.PLCH[ch]}|{src}|lib', 0.8))
                n, v = pl['name'], pl['keyl']
                c, ws = pl['cipher'], pl['ws']
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
                rows.append(dict(ch=ch, src=src, i=i, stream=n, true_off=o_t, true_sign=pl['true_sign'], best=best[0], cell=best[1], found=bool(best[0] >= C.T300 and best[1][0] == pl['true_sign'] and abs(best[1][1] - o_t) <= 3)))
                print(rows[-1], flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'control.json').write_text(json.dumps(rows))
    print('control found', sum(r['found'] for r in rows), '/', len(rows))


def summary():
    rows = [json.loads(p.read_text()) for p in sorted((OUT / 'scan').glob('*.json'))]
    ctl = json.loads((OUT / 'control.json').read_text()) if (OUT / 'control.json').exists() else []
    tot = sum(r['offsets'] for r in rows)
    L = [f'# Phase 60 T6: Cicada OS 560.17 / _560.00 under R4 (phase 59 engine, hold / spend, both signs, window {SEC}@{START} n300 only, all offsets), T300 = {C.T300:.2f}']
    L.append(f'chunks {len(rows)}, offsets screened {tot:,} of the 8 streams (full: {sum(len(v) for v in streams().values()):,}); CPU {sum(r["seconds"] for r in rows) / 3600:.2f} h')
    if rows:
        b = max(rows, key=lambda r: r['best'])
        L.append(f'max S_guard {b["best"]:.2f} ({b["name"]}, {b["argmax"]}); cells >= 20: {sum(r["n_hot"] for r in rows)}; chunks with a cell >= T300: {sum(r["best"] >= C.T300 for r in rows)}')
        for r in rows:
            for h in r['hot'][:3]:
                L.append(f'   {r["name"]}: score {h[0]:.1f} sign {h[1]} {h[2]} offset {h[3]}')
    if ctl:
        L.append(f'control: {sum(r["found"] for r in ctl)}/{len(ctl)} R4 plants (key = a stream of these files at a random offset) found at the right sign and offset (+-3), score min {min(r["best"] for r in ctl):.1f}')
    t = chr(10).join(L) + chr(10)
    (HERE.parent / 'results' / 'analysis' / 'phase60_t6_blobs_r4.txt').write_text(t, encoding='utf-8'); print(t)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=('control', 'scan', 'summary')); ap.add_argument('--workers', type=int, default=5); ap.add_argument('--reverse', action='store_true')
    a = ap.parse_args()
    {'control': cmd_control, 'scan': lambda: cmd_scan(a.workers, a.reverse), 'summary': summary}[a.cmd]()
