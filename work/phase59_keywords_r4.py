"""Phase 59: keyword (short periodic) keys under R4. Cicada's demonstrated key type (DIVINITY, FIRFUMFERENFE) never met the phase-51 mid-word arc, and every earlier
periodic test assumed no inserted runes. A keyword stream has L offsets, so the chanscreen v2 mid arc (hold / spend repair, one interior null per word) screens it cheaply.
    python -B work/phase59_keywords_r4.py keys                 # build + count the keyword set
    python -B work/phase59_keywords_r4.py control [--workers 4]  # R4 plants with a keyword key, + random-keyword nulls
    python -B work/phase59_keywords_r4.py scan [--workers 4] [--limit N]   # LP2 windows, below-normal priority
    python -B work/phase59_keywords_r4.py summary              # -> results/analysis/phase59_keywords_r4.txt
Keys: every word / clause / 2-3-word phrase of the solved pages, titles and 2014 signed messages (phase 50 sources, spelling variants C->F, ING->N G, IA->I O, plus 2-3-word phrases
inside signed lines), lengths 3-30, deduplicated up to rotation and repetition (all L offsets are screened, so a rotation is the same key).
"""
import argparse, concurrent.futures as cf, hashlib, json, math, os, random, re, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'chanscreen' / 'v2' / 'step4'))
sys.path.insert(0, str(HERE / 'phase50'))
import plant_mid as X  # noqa: E402
import lp_mask as LM  # noqa: E402
import lp_pilot_mid as LPM  # noqa: E402
import phase57_pilot as P57  # noqa: E402
import numpy as np  # noqa: E402
P, C = X.P, X.C
Q = 29
OUT = C.OUT / 'phase59'
CH = ('hold', 'spend')            # key advances once per real rune; coin / skip5 are number-stream channels (extent 3x / 6x) and are not run
PLCH = {'hold': 'm04', 'spend': 'spend'}
MINL, MAXL = 3, 30
SECS = range(7, 16)


def canon(v):
    """primitive period, least rotation"""
    n = len(v)
    for d in range(1, n):
        if n % d == 0 and v == v[:d] * (n // d):
            v = v[:d]; break
    return min(v[i:] + v[:i] for i in range(len(v)))


def keyset():
    import phrase_keys as PK
    lp = PK.lp
    keys = {}
    def add(runes, tag):
        for v in PK.variants(runes):
            if MINL <= len(v) <= MAXL:
                k = canon(tuple(v))
                if len(k) >= 2 and k not in keys:
                    keys[k] = tag
    for kind, text, runes in PK.sources():
        add(runes, f'{kind}:{text[:30].replace(" ", "_")}')
    # 2-3-word phrases inside each signed line (phase 50 had words and whole lines only)
    import glob
    for f in sorted(glob.glob(str(PK.R.ROOT / 'results' / 'outguess' / 'payload_1[0-3].txt') if hasattr(PK.R.ROOT, 'joinpath') else os.path.join(PK.R.ROOT, 'results', 'outguess', 'payload_1[0-3].txt'))):
        body = open(f, encoding='utf-8', errors='replace').read().split('-----BEGIN PGP SIGNATURE-----')[0].split('Hash: SHA1')[-1]
        for line in body.splitlines():
            ws = re.findall(r'[A-Za-z]+', line)
            if not re.search(r'\d', line):
                for n in (2, 3):
                    for k in range(len(ws) - n + 1):
                        add(lp.word_to_key(''.join(ws[k:k + n]).upper()), 'signed-phrase:' + '_'.join(ws[k:k + n])[:30])
    return keys


def windows():
    """every n300 start of each LP2 section: 0, 300, ... plus the last full window; the two DJU BEI copies' windows are added"""
    out = []
    for s in SECS:
        n = len(LM.section_edges(s)[0])
        if n < 300:
            continue
        st = list(range(0, n - 299, 300))
        if st[-1] != n - 300:
            st.append(n - 300)
        out += [(s, a) for a in st]
    return out


def stream(k, ch, nwin=300):
    ext = P.need_extent(PLCH[ch], nwin)
    reps = (ext + len(k)) // len(k) + 1
    return (list(k) * reps)[:ext + len(k)]


def scan_window(c, ws, keys, pi, L, logW):
    """-> list of (score, key index, sign, channel, offset) best per key plus all >= 20"""
    best, hot = [], []
    for ki, k in enumerate(keys):
        bk = (-math.inf, None)
        for ch in CH:
            s = stream(k, ch, len(c))
            for sign in C.SIGNS:
                sg = X.guard(c, s, sign, ch, pi, L, logW, 'mid', dict(wstart=ws), X.RHO)[:len(k)]
                o = int(np.argmax(sg))
                if sg[o] > bk[0]:
                    bk = (float(sg[o]), (sign, ch, o))
                for o2 in np.flatnonzero(sg >= 20):
                    hot.append((float(sg[o2]), ki, sign, ch, int(o2)))
        best.append((bk[0], ki) + bk[1])
    return best, hot


_W = {}


def init():
    LPM.lower()
    _W['pi'], _W['L'] = C.model()
    _W['keys'] = [list(k) for k in json.loads((OUT / 'keys.json').read_text())['keys']]


def win_task(args):
    sec, st = args
    dest = OUT / 'scan' / f'w{sec:02d}_{st:05d}.json'
    if dest.exists():
        return dest.name, 0.0
    t0 = time.perf_counter()
    runes, brk = LM.section_edges(sec)
    c = [int(x) for x in runes[st:st + 300]]
    ws = [1] + [1 if brk[st + i] else 0 for i in range(1, 300)]
    logW = C.log_common(c, C.Q_DECODER, C.Q)
    keys = [tuple(k) for k in _W['keys']]
    best, hot = scan_window(c, ws, keys, _W['pi'], _W['L'], logW)
    top = sorted(best, reverse=True)[:10]
    hot2 = []
    for sc, ki, sign, ch, o in sorted(hot, reverse=True)[:200]:      # fresh recomputation (the engine shows rare transient faults)
        sg2 = X.guard(c, stream(keys[ki], ch), sign, ch, _W['pi'], _W['L'], logW, 'mid', dict(wstart=ws), X.RHO)[o]
        hot2.append([sc, ki, sign, ch, o, float(sg2)])
    X._save(dest, dict(sec=sec, start=st, n_keys=len(keys), best=max(b[0] for b in best), top=[list(t) for t in top],
                       hot=hot2, n_hot=len(hot), seconds=time.perf_counter() - t0))
    return dest.name, time.perf_counter() - t0


def cmd_keys():
    OUT.mkdir(parents=True, exist_ok=True)
    keys = keyset()
    kl = list(keys)
    (OUT / 'keys.json').write_text(json.dumps(dict(keys=[list(k) for k in kl], tags=[keys[k] for k in kl]), indent=0))
    lens = [len(k) for k in kl]
    print(len(kl), 'keywords (canonical rotation), period', min(lens), '..', max(lens), 'median', sorted(lens)[len(lens) // 2], 'windows', len(windows()))


def phi_task(args):
    """phi(prime) = the library stream 'primes-1 (totient)', all 4 channels, both signs, every offset (the literal-F skip variant is not a channel of the engine and is not run)"""
    sec, st = args
    dest = OUT / 'phi' / f'w{sec:02d}_{st:05d}.json'
    if dest.exists():
        return dest.name, 0.0
    t0 = time.perf_counter()
    lib = _W.setdefault('lib', C.read_library())
    key = next(v for n, v in lib if n == 'primes-1 (totient)')
    runes, brk = LM.section_edges(sec)
    c = [int(x) for x in runes[st:st + 300]]
    ws = [1] + [1 if brk[st + i] else 0 for i in range(1, 300)]
    logW = C.log_common(c, C.Q_DECODER, C.Q)
    best = (-math.inf, None)
    for sign in C.SIGNS:
        for ch in C.CHANNELS:
            sg = X.guard(c, key, sign, ch, _W['pi'], _W['L'], logW, 'mid', dict(wstart=ws), X.RHO)
            o = int(np.argmax(sg))
            if sg[o] > best[0]:
                best = (float(sg[o]), [sign, ch, o])
    X._save(dest, dict(sec=sec, start=st, best=best[0], argmax=best[1], seconds=time.perf_counter() - t0))
    return dest.name, time.perf_counter() - t0


def ctl_init():
    LPM.lower(); P._init(); init()


def ctl_task(args):
    """plant: keyword key through R4 (phase 57 planter, stream = canonical rotation repeated); search the true keyword + 150 set keywords + 150 random same-length keywords, 2 signs"""
    ki, ch, src, i = args
    dest = OUT / 'control' / f'c{ki:04d}_{ch}_{src}_{i}.json'
    if dest.exists():
        return dest.name, 0.0
    t0 = time.perf_counter()
    keys = [tuple(k) for k in _W['keys']]
    rng = random.Random(f'p59|{ki}|{ch}|{src}|{i}')
    k = keys[ki]
    pc = PLCH[ch]
    q = P._G['q'].get(f'{pc}|{src}|lib', 0.8)
    plk = (list(k) * ((P.need_extent(pc, 700) + 4 * len(k)) // len(k) + 2))
    pl = P57.make_r4(pc, src, i, P._G['pool'][src], P._G['words'], [('kw', plk)], q)
    npl = P57.make_r4(pc, src, i + 1000, P._G['pool'][src], P._G['words'], [('kw', plk)], q, iid_key=True)
    pi, L = _W['pi'], _W['L']
    rec = dict(key_index=ki, keyword_len=len(k), channel=ch, src=src, index=i, o_true=pl['o_true'], phase=pl['o_true'] % len(k), true_sign=pl['true_sign'], nulls=pl['nulls_in_window'])

    def run(plant, cands):
        c, ws = plant['cipher'], plant['ws']
        logW = C.log_common(c, C.Q_DECODER, C.Q)
        out = []
        for name, kk in cands:
            bk = (-math.inf, None)
            for sign in C.SIGNS:
                sg = X.guard(c, stream(kk, ch), sign, ch, pi, L, logW, 'mid', dict(wstart=ws), X.RHO)[:len(kk)]
                o = int(np.argmax(sg))
                if sg[o] > bk[0]:
                    bk = (float(sg[o]), [sign, o])
            out.append((name, bk[0], bk[1]))
        return out
    others = [keys[j] for j in rng.sample(range(len(keys)), 151) if j != ki][:150]
    rnd = [tuple(rng.randrange(Q) for _ in range(len(kk))) for kk in others]
    res = run(pl, [('true', k)] + [('set', kk) for kk in others] + [('rand', kk) for kk in rnd])
    t = res[0]
    rec['true_score'] = t[1]; rec['true_cell'] = t[2]
    rec['true_found'] = bool(t[1] >= C.T300 and t[2][0] == pl['true_sign'] and (t[2][1] - rec['phase']) % len(k) in (0, 1, len(k) - 1))   # +-1: window-start null / repeat shifts the pointer
    rec['decoy_set_max'] = max(r[1] for r in res if r[0] == 'set'); rec['decoy_rand_max'] = max(r[1] for r in res if r[0] == 'rand')
    rec['iid_key_plant_true_keyword_score'] = run(npl, [('true', k)])[0][1]
    rec['seconds'] = time.perf_counter() - t0
    X._save(dest, rec)
    return dest.name, rec['seconds']


def cmd_control(w):
    keys = [tuple(k) for k in json.loads((OUT / 'keys.json').read_text())['keys']]
    import phrase_keys as PK
    named = [canon(tuple(PK.lp.word_to_key(n))) for n in ('DIVINITY', 'FIRFUMFERENFE', 'CIRCUMFERENCE')]
    idx = [keys.index(k) for k in named if k in keys]
    nm = len(idx)
    idx += random.Random(59).sample(range(len(keys)), 5)
    todo = [(ki, ch, src, i) for n, ki in enumerate(idx) for ch in CH for src in ("cicada", "english") for i in range(2 if n < nm else 1)]   # i odd = sign -1
    print(len(todo), 'plants', flush=True)
    with cf.ProcessPoolExecutor(max_workers=w, initializer=ctl_init) as ex:
        for n, f in enumerate(cf.as_completed([ex.submit(ctl_task, t) for t in todo]), 1):
            print(f'[{time.strftime("%H:%M:%S")}] {n}/{len(todo)} {f.result()}', flush=True)


def cmd_scan(w, limit, phi):
    wl = windows()[:limit or None]
    todo = [x for x in wl if not (OUT / ('phi' if phi else 'scan') / f'w{x[0]:02d}_{x[1]:05d}.json').exists()]
    print(len(todo), 'windows', flush=True)
    with cf.ProcessPoolExecutor(max_workers=w, initializer=init) as ex:
        for n, f in enumerate(cf.as_completed([ex.submit(phi_task if phi else win_task, t) for t in todo]), 1):
            print(f'[{time.strftime("%H:%M:%S")}] {n}/{len(todo)} {f.result()}', flush=True)


def summary():
    d = json.loads((OUT / 'keys.json').read_text()); keys, tags = d['keys'], d['tags']
    L = [f'# Phase 59 keyword keys under R4 (chanscreen v2 mid arc, hold / spend, both signs, T300 = {C.T300:.2f})', f'{len(keys)} keywords (up to rotation / repetition, length 3-30, variants included)']
    cr = [json.loads(p.read_text()) for p in sorted((OUT / 'control').glob('*.json'))]
    if cr:
        srt = sorted(r['true_score'] for r in cr)
        L.append(f'control: {sum(r["true_found"] for r in cr)}/{len(cr)} planted keyword texts recovered at the right keyword, sign and phase (score >= T300); true score min / median '
                 f'{srt[0]:.1f} / {srt[len(srt) // 2]:.1f}; wrong-keyword max: set keywords {max(r["decoy_set_max"] for r in cr):.1f}, random same-length {max(r["decoy_rand_max"] for r in cr):.1f}; '
                 f'iid-key plant searched with the true keyword: max {max(r["iid_key_plant_true_keyword_score"] for r in cr):.1f}')
        for r in cr:
            L.append(f'   key#{r["key_index"]} len {r["keyword_len"]} {r["channel"]} {r["src"]} {r["index"]}: true {r["true_score"]:.1f} cell {r["true_cell"]} want sign {r["true_sign"]} phase {r["phase"]} found {r["true_found"]}')
    sr = [json.loads(p.read_text()) for p in sorted((OUT / 'scan').glob('*.json'))]
    if sr:
        b = max(sr, key=lambda r: r['best'])
        L.append(f'scan: {len(sr)}/{len(windows())} windows x {len(keys)} keywords, CPU {sum(r["seconds"] for r in sr) / 3600:.2f} h; max S_guard {b["best"]:.2f} (section {b["sec"]} @ {b["start"]}, keyword #{b["top"][0][1]} '
                 f'{tags[b["top"][0][1]]}); cells >= 20: {sum(r["n_hot"] for r in sr)}; windows >= T300: {sum(r["best"] >= C.T300 for r in sr)}')
        for r in sr:
            for h in r['hot'][:5]:
                L.append(f'   sec {r["sec"]} @ {r["start"]}: score {h[0]:.1f} (fresh {h[5]:.1f}) keyword #{h[1]} {tags[h[1]]} sign {h[2]} {h[3]} offset {h[4]}')
    pr = [json.loads(p.read_text()) for p in sorted((OUT / 'phi').glob('*.json'))]
    if pr:
        b = max(pr, key=lambda r: r['best'])
        L.append(f'phi(prime) stream (primes-1), hold/spend/skip5/coin, {len(pr)} windows: max S_guard {b["best"]:.2f} (section {b["sec"]} @ {b["start"]} {b["argmax"]})')
    t = '\n'.join(L) + '\n'
    (HERE.parent / 'results' / 'analysis' / 'phase59_keywords_r4.txt').write_text(t, encoding='utf-8'); print(t)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=('keys', 'control', 'scan', 'phi', 'summary'))
    ap.add_argument('--workers', type=int, default=4); ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args()
    if a.cmd == 'keys':
        cmd_keys()
    elif a.cmd == 'control':
        cmd_control(a.workers)
    elif a.cmd in ('scan', 'phi'):
        cmd_scan(a.workers, a.limit, a.cmd == 'phi')
    else:
        summary()
