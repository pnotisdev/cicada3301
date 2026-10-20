"""ARCHIVED SCRATCH (laptop, 2026-10-20): E4-style plant pipeline, superseded by the desktop's `work/chanscreen/v2/step3/e4.py`
(origin/main 134fdd5). Only `smoke` was ever run (16 plants on non-protocol seeds `e4-smoke`, records in `records/`); the `run` and
`summary` commands were never used and the draft protocol (E4_PROTOCOL_draft.md) was never frozen for a run. Paths were adjusted for
this folder; the logic is unchanged. See README.md here.

  python -B e4_smoke.py smoke      16 plants, pipeline check only (not a result); write-once, so an existing records/ is just printed
No LP2 ciphertext is read.
"""
import os
for x in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[x] = '1'
import sys
sys.dont_write_bytecode = True
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
V1 = ROOT / 'work' / 'chanscreen'
V2 = V1 / 'v2'
sys.path[:0] = [str(V2), str(V2 / 'step2' / 'followup'), str(V1), str(ROOT / 'work' / 'm04'), str(ROOT / 'work')]
import functools, json, math, random, time
import concurrent.futures as CF
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

CH = ('hold', 'spend', 'skip5', 'coin')
N, Q, QDEC, K = 300, 29, .81, 15
T300 = 29.799206297530528
TS = (0, 5, 10)
NEED = {'hold': 1, 'spend': 1, 'skip5': 6, 'coin': 3}
REACH = {'hold': lambda n: n + 2, 'spend': lambda n: n + 2, 'skip5': lambda n: 6 * n + 6, 'coin': lambda n: 3 * n + 3}
BINS = (0, 1, 2, 3, 4, 8, 16, 64, 256, 1024)  # lower edges of the distance bins; the last is open


@functools.lru_cache(maxsize=None)
def library():
    import m04 as M
    lib = M.read_ksb(ROOT / 'work' / 'kscreen' / 'data' / 'library.ksb')
    assert len(lib) == 1439
    return [k for _, k in lib]


@functools.lru_cache(maxsize=None)
def model():
    m = np.load(V1 / 'model.npz')
    return m['pi'], m['L']


def fl(x):
    x = float(x)
    return x if math.isfinite(x) else None


def make_plant(prefix, channel, index):
    import run_baseline as B
    import m04 as M
    seed = B.seed_of(prefix, channel, N, index)
    rng = random.Random(seed)
    src = 'cicada' if index < 12 else 'english'
    plain, start = B.window('held', src, rng)
    plain = [int(v) for v in plain]
    lib = library()
    need = NEED[channel] * N
    elig = [i for i, k in enumerate(lib) if len(k) >= need]
    si = elig[rng.randrange(len(elig))]
    key = lib[si]
    off = rng.randrange(len(key) - need + 1)
    sign = 1 if index % 2 == 0 else -1
    qf = json.loads((V1 / 'frozen.json').read_text())['q']
    if channel == 'hold':
        cipher, used, rep = M.enc_m04(plain, key, off, qf[f'm04|{src}|lib'], rng, mult=sign)
    elif channel == 'spend':
        cipher, used, rep = M.enc_spend(plain, key, off, qf[f'spend|{src}|lib'], rng, mult=sign)
    elif channel == 'skip5':
        cipher, used, rep = M.enc_skip(plain, key, off, rng, mult=sign)
    else:
        cipher, used, rep = M.enc_coin(plain, key, off, rng, mult=sign)
    return dict(seed=seed, src=src, start=int(start), stream=si, m=len(key), off=off, sign=sign, plain=plain,
                cipher=[int(c) for c in cipher], doublets=M.doublets(cipher), repairs=int(sum(rep)),
                key_used=int(max(used)) - off + 1)


def equiv_offsets(key, off, span):
    """Offsets whose `span`-value key slice equals the true one: exact copies of the true cell for any decoder."""
    a = np.frombuffer(key, dtype=np.uint8)
    return np.flatnonzero((sliding_window_view(a, span) == a[off:off + span]).all(axis=1))


def all_passes(p):
    from engine import all_offsets
    from guard import guarded
    pi, L = model()
    key, c = library()[p['stream']], p['cipher']
    out = []
    for ch in CH:
        for sign in (-1, 1):
            o = all_offsets(c, key, sign, QDEC, ch, pi, L)
            l, u = o[:, 0], o[:, 1]
            ok = np.isfinite(u)
            S = np.full(len(o), -np.inf)
            S[ok] = l[ok] - u[ok]
            g, _ = guarded(l, u, c, QDEC, Q)
            out.append((ch, sign, S, g))
    return out


def pass_record(ch, sign, S, g, off, eqmask):
    dist = np.abs(np.arange(len(g)) - off)
    fin = np.isfinite(g)
    am = int(np.argmax(g)) if fin.any() else None
    near = dist <= K
    far = ~near & ~eqmask
    return dict(channel=ch, sign=sign, n_offsets=len(g), n_outside=int(far.sum()),
                max_G=fl(g[am]) if am is not None else None, argmax=am,
                max_S=fl(np.max(S)) if np.isfinite(S).any() else None,
                counts={str(t): dict(all=int((g >= t).sum()), outside=int(((g >= t) & far).sum()),
                                     copies=int(((g >= t) & eqmask & ~near).sum())) for t in TS + (T300,)},
                hist={str(t): np.bincount(np.digitize(dist[(g >= t) & ~eqmask], BINS[1:]), minlength=len(BINS)).tolist()
                      for t in (10, T300)})


def decode(p, ch, sign, o):
    from reconstruct import viterbi
    pi, L = model()
    n = len(p['cipher'])
    sl = list(library()[p['stream']][o:o + REACH[ch](n)])
    plain, _, v = viterbi(p['cipher'], sl, 0, sign, QDEC, ch, pi, L)
    if not plain:
        return dict(accuracy=None, log_joint=None)
    return dict(accuracy=sum(a == b for a, b in zip(plain, p['plain'])) / n, log_joint=fl(v))


def job(args):
    prefix, channel, index, outdir = args
    dest = Path(outdir) / f'{channel}_{index:02d}.json'
    if dest.exists():
        return str(dest), 0.
    t0 = time.perf_counter()
    p = make_plant(prefix, channel, index)
    eq = equiv_offsets(library()[p['stream']], p['off'], p['key_used'])
    eqmask = np.zeros(p['m'] + 1, bool)
    eqmask[eq] = True
    recs, true = [], None
    for ch, sign, S, g in all_passes(p):
        recs.append(pass_record(ch, sign, S, g, p['off'], eqmask))
        if ch == channel and sign == p['sign']:
            gt = g[p['off']]
            true = dict(G=fl(gt), S=fl(S[p['off']]), rank=int((g > gt + 1e-6).sum()) if np.isfinite(gt) else None)
    win = max((r for r in recs if r['max_G'] is not None), key=lambda r: r['max_G'])
    wcell, tcell = (win['channel'], win['sign'], win['argmax']), (channel, p['sign'], p['off'])
    dw = decode(p, *wcell)
    dt = dw if tcell == wcell else (decode(p, *tcell) if true['G'] is not None else dict(accuracy=None, log_joint=None))
    rec = dict(prefix=prefix, channel=channel, index=index, **p, passes=recs, true=true,
               n_copies=int(len(eq)), n_copies_beyond_15=int((np.abs(eq - p['off']) > K).sum()),
               detected=true['G'] is not None and true['G'] >= T300,
               winner=dict(channel=win['channel'], sign=win['sign'], offset=win['argmax'], G=win['max_G'],
                           copy_of_truth=bool(win['channel'] == channel and win['sign'] == p['sign'] and eqmask[win['argmax']])),
               winner_decode=dw, true_decode=dt, seconds=time.perf_counter() - t0)
    dest.parent.mkdir(exist_ok=True)
    with dest.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(rec, f, allow_nan=False)
    return str(dest), rec['seconds']


def run(prefix, outdir, indices, workers):
    jobs = [(prefix, ch, i, str(outdir)) for ch in CH for i in indices]
    t0 = time.time()
    with CF.ProcessPoolExecutor(max_workers=workers) as ex:
        for k, (_, s) in enumerate(ex.map(job, jobs), 1):
            if k % 10 == 0 or k == len(jobs):
                print(f'{k}/{len(jobs)} plants, {time.time() - t0:.0f}s', flush=True)


def load(d):
    return [json.loads(f.read_text()) for f in sorted(Path(d).glob('*.json'))]


def smoke():
    d = HERE / 'records'
    run('e4-smoke', d, (0, 1, 12, 13), 4)
    for r in load(d):
        w = r['winner']
        far10 = sum(p['counts']['10']['outside'] for p in r['passes'])
        print(r['channel'], r['index'], 'sign', r['sign'], 'm', r['m'], 'off', r['off'], 'true G', round(r['true']['G'], 2),
              'det', r['detected'], 'winner', w['channel'], w['sign'], w['offset'], 'copy', w['copy_of_truth'],
              'copies', r['n_copies'], 'acc', r['winner_decode']['accuracy'], 'outside>=10:', far10, f"{r['seconds']:.1f}s")


def summary():
    recs = load(HERE / 'e4_records')
    assert len(recs) == 100, len(recs)
    out = dict(T300=T300, k_alias=K, plants=len(recs))
    pct = lambda x, n: dict(detected=int(x), of=n)
    out['pooled'] = pct(sum(r['detected'] for r in recs), len(recs))
    out['by_channel'] = {ch: pct(sum(r['detected'] for r in recs if r['channel'] == ch), 25) for ch in CH}
    out['by_source'] = {s: pct(sum(r['detected'] for r in recs if r['src'] == s), sum(r['src'] == s for r in recs)) for s in ('cicada', 'english')}
    out['by_sign'] = {str(s): pct(sum(r['detected'] for r in recs if r['sign'] == s), sum(r['sign'] == s for r in recs)) for s in (-1, 1)}
    det = [r for r in recs if r['detected']]
    acc = [r['winner_decode']['accuracy'] for r in det if r['winner_decode']['accuracy'] is not None]
    out['winner_accuracy_ge_95'] = dict(count=sum(a >= .95 for a in acc), of_detected=len(det), mean=float(np.mean(acc)) if acc else None)
    out['true_G'] = dict(min=min(r['true']['G'] for r in recs if r['true']['G'] is not None),
                         median=float(np.median([r['true']['G'] for r in recs if r['true']['G'] is not None])))
    ex = lambda r, d: (r['winner']['channel'] == r['channel'] and r['winner']['sign'] == r['sign'] and abs(r['winner']['offset'] - r['off']) <= d)
    out['winner'] = {f'channel+sign+offset within {d}': sum(ex(r, d) for r in recs) for d in (0, 3, K)}
    out['winner']['channel+sign right and the cell is an exact copy of the true cell (equal key slice)'] = sum(r['winner']['copy_of_truth'] for r in recs)
    out['winner']['true cell is the winner (rank 0 within 1e-6)'] = sum(r['true']['rank'] == 0 for r in recs)
    out['winner']['any channel or sign, offset within 15'] = sum(abs(r['winner']['offset'] - r['off']) <= K for r in recs)
    out['plants_with_exact_copies_beyond_15'] = sum(r['n_copies_beyond_15'] > 0 for r in recs)
    out['exact_copy_offsets_beyond_15'] = dict(total=sum(r['n_copies_beyond_15'] for r in recs), max=max(r['n_copies_beyond_15'] for r in recs))
    g4 = {}
    for t in map(str, TS):
        obs = sum(p['counts'][t]['outside'] for r in recs for p in r['passes'])
        bound = sum(p['n_outside'] * math.exp(-float(t)) for r in recs for p in r['passes'])
        g4[t] = dict(observed=obs, bound=bound, ok=obs <= bound)
    out['wrong_offset_count_outside_15_and_not_a_copy'] = g4
    out['wrong_offset_count_all_offsets_except_true'] = {t: sum(p['counts'][t]['all'] for r in recs for p in r['passes']) for t in map(str, TS)}
    out['cells_that_are_exact_copies_beyond_15'] = {t: sum(p['counts'][t]['copies'] for r in recs for p in r['passes']) for t in map(str, TS)}
    prof = {}
    for t in ('10', str(T300)):
        tp = np.zeros(len(BINS), int)
        al = np.zeros(len(BINS), int)
        for r in recs:
            for p in r['passes']:
                al += p['hist'][t]
                if p['channel'] == r['channel'] and p['sign'] == r['sign']:
                    tp += p['hist'][t]
        prof[t] = dict(bin_lower_edges=list(BINS), true_channel_and_sign_passes=tp.tolist(), all_passes=al.tolist())
    out['alias_profile_cells_at_threshold'] = prof
    out['seconds'] = dict(total_cpu=sum(r['seconds'] for r in recs), mean_per_plant=float(np.mean([r['seconds'] for r in recs])))
    out['gate'] = dict(G1_pooled_ge_90=out['pooled']['detected'] >= 90,
                       G2_each_channel_ge_20=all(v['detected'] >= 20 for v in out['by_channel'].values()),
                       G3_more_than_half_winners_ge_95=out['winner_accuracy_ge_95']['count'] * 2 > len(det),
                       G4_wrong_offset_counts=all(v['ok'] for v in g4.values()))
    out['gate']['PASS'] = all(out['gate'].values())
    (HERE / 'e4_summary.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'smoke':
        smoke()
    elif cmd == 'run':
        run('chanscreen-step2-plant', HERE / 'e4_records', range(25), int(sys.argv[2]))
    else:
        summary()
