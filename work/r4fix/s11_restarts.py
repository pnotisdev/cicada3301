"""R4 repair s11 (round 2, idea 13): does a Cicada-named key stream that RESTARTS at a page start or a clause start decode LP2 under R4?

Nothing in LP2 is solved.  Decoder: the gated union arc (work/r4fix/s08_engine_union.py, place 'any', nu 0.42, q 0.81), hold and spend, both signs,
key index 0 at the window start; scored offsets 0..28 (offset 0 = the restart; 1..28 = a shifted start, the cheap extra).  Hit threshold T300 = 29.80
(work/chanscreen/v2/step4/hit_rule.py, S_guard = min(log Z_L - log Z_U, log Z_L - log W)).

    python -B work/r4fix/s11_restarts.py list                    # the streams, the windows, the cell counts
    python -B work/r4fix/s11_restarts.py selftest                # ws[0] equivalence, timing of one window
    python -B work/r4fix/s11_restarts.py plants [--workers 4]    # controls: R4 plants + matched iid-key plants (BEFORE LP2)
    python -B work/r4fix/s11_restarts.py psummary                # gate on the controls
    python -B work/r4fix/s11_restarts.py run [--workers 4]       # LP2 windows x (named streams + random-stream null)
    python -B work/r4fix/s11_restarts.py summary                 # -> results/r4fix/s11_restarts/summary.txt

Word-start flags: derived from the transcription's real word boundaries (lp_mask.section_edges: ' ', '.', '&' separate words; line breaks and page marks are
transparent), so a window that starts mid-word is flagged correctly (flag i >= 1 = a separator lies before rune start+i).  Flag 0 is passed as 1 because the
engine treats position 0 as a word start whatever it is (s08_backward_union.rs line 48); `selftest` shows the output is identical for flag 0 = 0 or 1.
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import math
import os
import random
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'work' / 'chanscreen' / 'v2' / 'step4'))
sys.path.insert(0, str(ROOT / 'work' / 'chanscreen' / 'v2'))
import numpy as np  # noqa: E402
import plant_mid as X  # noqa: E402
import lp_pilot_mid as LPM  # noqa: E402
import lp_mask as LM  # noqa: E402
from s08_engine_union import all_offsets_union  # noqa: E402
import r4sim  # noqa: E402

P, C = X.P, X.C
Q = X.M.Q
OUT = ROOT / 'results' / 'r4fix' / 's11_restarts'
DATA = ROOT / 'work' / 'kscreen' / 'data'
NU_DEC, Q_DEC = 0.42, 0.81
RHO_PLANT = 0.45
NOFF = 29
CHS = ('hold', 'spend')
SIGNS = (1, -1)
NRAND = 100
MINLEN = 150
T300 = C.T300

# ---- the named streams (exact library names): why each is here ------------------------------------------------------------------------------------------
CORE20 = ["primes", "primes-1 (totient)", "primes+1", "phi(n)", "sigma(n)", "n", "n^2", "triangular", "fibonacci", "lucas",
          "pi digits (base 10)", "pi digits (base 29)", "e digits (base 10)", "e digits (base 29)", "phi digits (base 29)",
          "sqrt2 digits (base 29)", "primes from 3301", "3301*n", "cumulative prime sum", "gematria primes cycle"]      # work/layer2/export.py CORE20
EXTRA_MATH = ["prime counting pi(n)", "n^3", "pell", "sqrt3 digits (base 29)", "ln2 digits (base 29)"]   # pi(n), n^3, Pell; sqrt3 and ln2 base 29 (brief's list)
CICADA_NUM = ["1033*n", "3301^n", "3301 digits", "1033 digits", "1/3301 digits (base 29)", "sqrt3301 digits (base 29)", "ln3301 digits (base 29)",
              "3301 * p_n", "p_n mod 3301", "1033 square rows", "page-30 grid primes (3301-x)", "An End hash bytes", "An End hash nibbles"]  # 1033 / 3301 families
HASH_STRINGS = ["an end", "welcome", "instar", "3301", "Cicada 3301"]            # hash chains of Cicada strings already in the library
HASH_KINDS = ["sha256-ctr mod", "sha256-ctr reject", "sha256-chain mod", "sha256-chain reject"]
PAYLOAD = ["sha256-chain mod :<256 bytes cbe7a7ba>", "sha256-chain reject :<256 bytes cbe7a7ba>", "payload bytes mod 29 (cycled)"]   # the corrected 256-byte payload
NAMED = CORE20 + EXTRA_MATH + CICADA_NUM + [f'{k} :{s}' for s in HASH_STRINGS for k in HASH_KINDS] + PAYLOAD

_G = {}


# ---- setup -----------------------------------------------------------------------------------------------------------------------------------------------
def init():
    LPM.lower()
    P._init()
    _setup()


def _setup():
    lib = P._G['lib']
    idx = {n: i for i, (n, _) in enumerate(lib)}
    missing = [n for n in NAMED if n not in idx]
    assert not missing, missing
    assert len(set(NAMED)) == len(NAMED)
    _G['named_idx'] = [idx[n] for n in NAMED]
    _G['keys'] = [np.asarray(lib[i][1], dtype=np.int32) for i in _G['named_idx']]
    rng = np.random.default_rng(int.from_bytes(hashlib.sha256(b'r4fix-s11|random streams').digest()[:8], 'big'))
    _G['rand'] = [rng.integers(0, Q, size=420).astype(np.int32) for _ in range(NRAND)]
    _G['edges'] = {}
    _G['pi'], _G['L'] = P._G['pi'], P._G['L']


def edges(sec):
    if sec not in _G['edges']:
        _G['edges'][sec] = LM.section_edges(sec)
    return _G['edges'][sec]


# ---- windows -----------------------------------------------------------------------------------------------------------------------------------------------
def page_starts():
    out = []
    for line in open(DATA / 'pages.txt', encoding='utf-8'):
        if line.startswith('W '):
            m = re.match(r'page(\d+)_0\.(\d+)@(\d+)', line.split()[1])
            out.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
    return out


def build_windows():
    """list of dict(label, kind, sec, start, variant, n): variant 'A' = the brief (n = min(300, runes to the section end)), 'B' = bounded (n = min(300, runes to the
    next restart point of the same kind)).  Windows under MINLEN runes are listed as skipped."""
    pages = page_starts()
    ends = {}
    for sec in (7, 8, 9, 11, 12, 13, 14, 15):
        ends[sec] = len(edges(sec)[0])
    wins, skipped = [], []
    for k, (pg, sec, st) in enumerate(pages):
        nxt = [s for (_, s2, s) in pages if s2 == sec and s > st]
        nb = min(nxt) if nxt else ends[sec]
        for var, n in (('A', min(300, ends[sec] - st)), ('B', min(300, nb - st))):
            rec = dict(label=f'page{pg}_0.{sec}@{st}', kind='page', sec=sec, start=st, variant=var, n=n, mid_word=not edges(sec)[1][st])
            (wins if n >= MINLEN else skipped).append(rec)
    cw = C.clause_windows(60)
    for w in cw:
        sec, st, L = w['sec'], w['start'], len(w['cipher'])
        for var, n in (('A', min(300, ends[sec] - st)), ('B', min(300, L))):
            rec = dict(label=w['name'], kind='clause', sec=sec, start=st, variant=var, n=n, mid_word=not edges(sec)[1][st] and st > 0, clause_len=L)
            (wins if n >= MINLEN else skipped).append(rec)
    return wins, skipped


def flags(sec, start, n):
    runes, brk = edges(sec)
    return [int(runes[start + i]) for i in range(n)], [1] + [1 if brk[start + i] else 0 for i in range(1, n)]


# ---- the driver -------------------------------------------------------------------------------------------------------------------------------------------
def guard(c, key, sign, ch, ws, logW):
    out = all_offsets_union(c, key, sign, Q_DEC, ch, _G['pi'], _G['L'], NU_DEC, ws, 'any')
    l, u = out[:NOFF, 0], out[:NOFF, 1]
    if np.any(np.isnan(l)) or np.any(np.isposinf(l)) or np.any(l > 1e-9):
        raise ValueError('invalid log likelihood')
    with np.errstate(invalid='ignore'):
        s = np.where(np.isfinite(l) & np.isfinite(u), l - u, -np.inf)
        sw = np.where(np.isfinite(l) & np.isfinite(logW), l - logW, -np.inf)
    return np.minimum(s, sw)


def drive(c, ws, keys):
    """S_guard[stream, sign, channel, offset 0..28] of the window c against each key (key index 0 at the window start)"""
    n = len(c)
    logW = C.log_common(c, Q_DEC, C.Q)
    res = np.full((len(keys), 2, len(CHS), NOFF), -np.inf, dtype=np.float32)
    for si, key in enumerate(keys):
        kk = np.ascontiguousarray(key[:n + 16 + NOFF - 1])
        for a, sign in enumerate(SIGNS):
            for b, ch in enumerate(CHS):
                res[si, a, b, :] = guard(c, kk, sign, ch, ws, logW)
    return res


# ---- LP2 scan ------------------------------------------------------------------------------------------------------------------------------------------------
def task_file(sec, start, n):
    return OUT / 'win' / f'w_{sec}_{start}_{n}.npz'


def lp2_task(args):
    sec, start, n = args
    dest = task_file(sec, start, n)
    if dest.exists():
        return dest.name, 0.0
    t0 = time.process_time()
    c, ws = flags(sec, start, n)
    res = drive(c, ws, _G['keys'] + _G['rand'])
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix('.tmp.npz')
    np.savez_compressed(tmp, S=res, sec=sec, start=start, n=n, cpu=time.process_time() - t0)
    os.replace(tmp, dest)
    return dest.name, time.process_time() - t0


def unique_tasks():
    wins, _ = build_windows()
    return sorted({(w['sec'], w['start'], w['n']) for w in wins})


def cmd_run(a):
    P._init()      # the window list needs the section edges in the parent too (the pool initializer only runs in the workers)
    _setup()
    tasks = [t for t in unique_tasks() if not task_file(*t).exists()]
    print(len(tasks), 'tasks', flush=True)
    with cf.ProcessPoolExecutor(max_workers=min(a.workers, 4), initializer=init) as ex:
        for k, f in enumerate(cf.as_completed([ex.submit(lp2_task, t) for t in tasks]), 1):
            print(f'[{time.strftime("%H:%M:%S")}] {k}/{len(tasks)} {f.result()[0]} {f.result()[1]:.1f} cpu-s', flush=True)


# ---- plants (controls) ---------------------------------------------------------------------------------------------------------------------------------------
PLANT_CELLS = [(ch, src) for ch in ('m04', 'spend') for src in ('cicada', 'english')]
NPLANT_PER = 7           # per (channel, source): 28 plants (the run was paused after 7 per cell; indices 0-2 of each cell = the brief's first 12)


def seed_for(ch, src, idx):
    return int.from_bytes(hashlib.sha256(f'r4fix-s11|{ch}|{src}|{idx}'.encode()).digest()[:8], 'big')


def make_plant(ch, src, i, iid=False):
    """R4 plant: LP2 word layout from a random page start with >= 340 runes to the section end (first word = the rest of the word at the page start when it starts mid-word),
    held plaintext, a named stream restarted (key_start 0), r4sim R4 (slots any, q 0.81, nu 0.45, T repair, checked + visible nulls)"""
    rng = random.Random(seed_for(ch, src, i))
    pages = [p for p in page_starts() if len(edges(p[1])[0]) - p[2] >= 340]
    pg, sec, st = pages[rng.randrange(len(pages))]
    runes, brk = edges(sec)
    lens, cur = [], 0
    for r in range(st, len(runes)):
        if r > st and brk[r]:
            lens.append(cur)
            cur = 0
        cur += 1
    lens.append(cur)
    pool = P._G['pool'][src]
    tot, wl = 0, []
    for L in lens:
        if tot >= 330:
            break
        wl.append(L)
        tot += L
    s0 = rng.randrange(len(pool) - tot + 1)
    flat = pool[s0:s0 + tot]
    words, p = [], 0
    for L in wl:
        words.append([int(x) for x in flat[p:p + L]])
        p += L
    si = rng.randrange(len(NAMED))
    key = [int(x) for x in _G['keys'][si]]
    sign = 1 if i % 2 == 0 else -1
    if iid:
        key = [rng.randrange(Q) for _ in range(len(key))]
    res = r4sim.encrypt_r4(words, key, rng, q=Q_DEC, repair='T', lag=6, nu=RHO_PLANT, slots='any', null_check='left', null_visible=True, lag_basis='cipher',
                           channel='hold' if ch == 'm04' else 'spend', sign=sign, key_start=0, n_cipher=300)
    assert len(res.cipher) == 300, len(res.cipher)
    ws = [int(x) for x in res.word_start]
    ws[0] = 1
    edge = res.is_null & (res.word_start | res.word_end)
    return dict(stream=si, name=NAMED[si], sign=sign, page=f'{pg}_0.{sec}@{st}', mid_word=not brk[st], key=key, cipher=[int(x) for x in res.cipher], ws=ws,
                nulls=[int(x) for x in res.is_null], edge_nulls=[int(x) for x in edge], T_repairs=int(res.repair_is_T.sum()))


def plant_task(args):
    ch, src, i = args
    dest = OUT / 'plants' / f'p_{ch}_{src}_{i:02d}.json'
    if dest.exists():
        return dest.name, 0.0
    t0 = time.process_time()
    pl = make_plant(ch, src, i)
    npl = make_plant(ch, src, i + 1000, iid=True)     # matched iid-key plant (its own layout), searched with the SAME named streams
    rec = dict(channel=ch, src=src, index=i, stream=pl['stream'], name=pl['name'], sign=pl['sign'], page=pl['page'], mid_word=pl['mid_word'],
               true_ch=CHS.index('hold' if ch == 'm04' else 'spend'), T_repairs=pl['T_repairs'])
    for n in (150, 300):
        for tag, plant in (('plant', pl), ('null', npl)):
            S = drive(plant['cipher'][:n], plant['ws'][:n], _G['keys'])
            a = SIGNS.index(plant['sign'])
            r = dict(nulls=sum(plant['nulls'][:n]), edge_nulls=sum(plant['edge_nulls'][:n]), max_off0=float(S[:, :, :, 0].max()), max_off028=float(S.max()))
            if tag == 'plant':
                s_true = float(S[pl['stream'], a, rec['true_ch'], 0])
                wrong = S.copy()
                wrong[pl['stream'], a, rec['true_ch'], 0] = -np.inf
                r.update(s_true=s_true, band03=float(S[pl['stream'], a, rec['true_ch'], :4].max()), detected=bool(s_true >= T300),
                         true_within3=bool(s_true >= float(S[:, :, :, 0].max()) - 3.0), wrong_max_off0=float(wrong[:, :, :, 0].max()),
                         true_ch_best_other_ch=float(S[pl['stream'], a, 1 - rec['true_ch'], 0]))
            rec[f'{tag}{n}'] = r
    rec['cpu_seconds'] = time.process_time() - t0
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix('.tmp')
    tmp.write_text(json.dumps(rec, indent=1, allow_nan=True), encoding='utf-8', newline='\n')
    os.replace(tmp, dest)
    return dest.name, rec['cpu_seconds']


def cmd_plants(a):
    todo = [(ch, src, i) for i in range(NPLANT_PER) for (ch, src) in PLANT_CELLS if not (OUT / 'plants' / f'p_{ch}_{src}_{i:02d}.json').exists()]
    print(len(todo), 'plants', flush=True)
    with cf.ProcessPoolExecutor(max_workers=min(a.workers, 4), initializer=init) as ex:
        for k, f in enumerate(cf.as_completed([ex.submit(plant_task, t) for t in todo]), 1):
            print(f'[{time.strftime("%H:%M:%S")}] {k}/{len(todo)} {f.result()[0]} {f.result()[1]:.1f} cpu-s', flush=True)


def pwrong_task(args):
    """other-STREAM maximum for one plant at n 300 (plant_task's wrong_max_off0 also contains the other channel of the true stream, an alias, so it is not a null)"""
    ch, src, i = args
    dest = OUT / 'plants' / f'w_{ch}_{src}_{i:02d}.json'
    if dest.exists():
        return dest.name, 0.0
    t0 = time.process_time()
    pl = make_plant(ch, src, i)
    S = drive(pl['cipher'], pl['ws'], _G['keys'])
    a = SIGNS.index(pl['sign'])
    o = np.delete(S, pl['stream'], axis=0)
    rec = dict(channel=ch, src=src, index=i, name=pl['name'], other_streams_max_off0=float(o[:, :, :, 0].max()), other_streams_max_off028=float(o.max()),
               true_stream_other_sign_max=float(S[pl['stream'], 1 - a, :, 0].max()), true_stream_other_channel=float(S[pl['stream'], a, 1 - CHS.index('hold' if ch == 'm04' else 'spend'), 0]),
               cpu_seconds=time.process_time() - t0)
    tmp = dest.with_suffix('.tmp')
    tmp.write_text(json.dumps(rec, indent=1), encoding='utf-8', newline='\n')
    os.replace(tmp, dest)
    return dest.name, rec['cpu_seconds']


def cmd_pwrong(a):
    todo = [(ch, src, i) for i in range(NPLANT_PER) for (ch, src) in PLANT_CELLS if not (OUT / 'plants' / f'w_{ch}_{src}_{i:02d}.json').exists()]
    print(len(todo), 'plants', flush=True)
    with cf.ProcessPoolExecutor(max_workers=min(a.workers, 4), initializer=init) as ex:
        for k, f in enumerate(cf.as_completed([ex.submit(pwrong_task, t) for t in todo]), 1):
            print(f'[{time.strftime("%H:%M:%S")}] {k}/{len(todo)} {f.result()[0]} {f.result()[1]:.1f} cpu-s', flush=True)


def load_plants():
    return [json.loads(p.read_text(encoding='utf-8')) for p in sorted((OUT / 'plants').glob('p_*.json'))]


def load_pwrong():
    return [json.loads(p.read_text(encoding='utf-8')) for p in sorted((OUT / 'plants').glob('w_*.json'))]


def cmd_psummary(a=None):
    recs = load_plants()
    out = [f'# s11 controls: R4 plants (slots any, q {Q_DEC}, nu {RHO_PLANT}, T repair) on a named stream restarted at an LP2 page start; same driver (union arc nu {NU_DEC}, hold + spend, both signs, '
           f'{len(NAMED)} named streams, offsets 0..28); detected = S_guard at (true stream, sign, channel, offset 0) >= T300 = {T300:.2f}', '']
    gate = {}
    for n in ('150', '300'):
        sel = [r for r in recs]
        first = [r for r in recs if r['index'] < 3]
        det = sum(r[f'plant{n}']['detected'] for r in sel)
        d1 = sum(r[f'plant{n}']['detected'] for r in first)
        w3 = sum(r[f'plant{n}']['true_within3'] for r in sel)
        sc = sorted(r[f'plant{n}']['s_true'] for r in sel)
        nm0 = max(r[f'null{n}']['max_off0'] for r in sel)
        nm28 = max(r[f'null{n}']['max_off028'] for r in sel)
        wm0 = max(r[f'plant{n}']['wrong_max_off0'] for r in sel)
        out.append(f'n {n}: detected {det}/{len(sel)} (first 12: {d1}/{len(first)}), true within 3 nats of the best cell {w3}/{len(sel)}, true-cell score min / median / max '
                   f'{sc[0]:.1f} / {sc[len(sc) // 2]:.1f} / {sc[-1]:.1f}; wrong-stream max over the plant searches (offset 0) {wm0:.1f}; matched iid-key plants searched with the same {len(NAMED)} '
                   f'streams: max {nm0:.1f} (offset 0), {nm28:.1f} (offsets 0..28), >= T300: {sum(r[f"null{n}"]["max_off028"] >= T300 for r in sel)}/{len(sel)}')
        for ch in ('m04', 'spend'):
            for src in ('cicada', 'english'):
                s2 = [r for r in sel if r['channel'] == ch and r['src'] == src]
                out.append(f'    {ch:5s} {src:8s} detected {sum(r[f"plant{n}"]["detected"] for r in s2)}/{len(s2)}')
        mid = [r for r in sel if r['mid_word']]
        out.append(f'    plants whose page start is mid-word: {len(mid)}, detected {sum(r[f"plant{n}"]["detected"] for r in mid)}')
        gate[n] = (d1, len(first), det, len(sel))
    out.append('')
    out.append('per plant (n 300): channel src idx | stream | sign | page | true-cell score | nulls (edge) in 300 | best wrong | matched-null max (0..28)')
    for r in recs:
        p = r['plant300']
        out.append(f'{r["channel"]:5s} {r["src"]:8s} {r["index"]:2d} | {r["name"][:34]:34s} | {r["sign"]:+d} | {r["page"]:12s}{" mid-word" if r["mid_word"] else "         "} | {p["s_true"]:7.1f} | '
                   f'{p["nulls"]:2d} ({p["edge_nulls"]:2d}) | {p["wrong_max_off0"]:6.1f} | {r["null300"]["max_off028"]:7.1f}')
    out.append(f'\nCPU seconds (plants + nulls, both n): total {sum(r["cpu_seconds"] for r in recs):.0f}')
    txt = '\n'.join(out) + '\n'
    (OUT / 'plants_summary.txt').write_text(txt, encoding='utf-8', newline='\n')
    print(txt)
    return gate


# ---- summary of the LP2 scan --------------------------------------------------------------------------------------------------------------------------------
def cmd_summary(a=None):
    P._init()
    _setup()
    wins, skipped = build_windows()
    nn = len(NAMED)
    res = {}
    cpu = 0.0
    for f in sorted((OUT / 'win').glob('w_*.npz')):
        z = np.load(f)
        res[(int(z['sec']), int(z['start']), int(z['n']))] = z['S']
        cpu += float(z['cpu'])
    out = [f'# s11 LP2 scan: restart windows x {nn} named streams (+ {NRAND} random streams as the null of the maximum); union arc nu {NU_DEC}, q {Q_DEC}, hold + spend, both signs, offsets 0..28; T300 = {T300:.2f}',
           f'windows: {len(wins)} (page / clause x variant A: n = min(300, runes to the section end), variant B: n = min(300, runes to the next restart point)); {len(res)} unique (section, start, n) scored; '
           f'skipped under {MINLEN} runes: {len(skipped)}', '']
    cells_named = len(res) * nn * 2 * len(CHS) * NOFF
    cells_rand = len(res) * NRAND * 2 * len(CHS) * NOFF
    out.append(f'cells scored: {cells_named:,} named (of which offset 0: {cells_named // NOFF:,}) + {cells_rand:,} random-stream null; CPU in the scan {cpu / 3600:.2f} h')
    hits = []
    rows = {}
    for w in wins:
        k = (w['sec'], w['start'], w['n'])
        if k not in res:
            continue
        S = res[k]
        Sn, Sr = S[:nn], S[nn:]
        rows.setdefault((w['kind'], w['variant']), []).append((w, Sn, Sr))
    out.append('')
    out.append('per window type: windows | named best at offset 0 | named best over offsets 0..28 | random-stream null max (offset 0 / 0..28), per-window max over 200 random streams: median / max | counts >= 0, 5, 10, 20 (named, offset 0)')
    for (kind, var), lst in sorted(rows.items()):
        b0 = max(((float(Sn[:, :, :, 0].max()), w, Sn) for w, Sn, Sr in lst), key=lambda t: t[0])
        b28 = max(((float(Sn.max()), w, Sn) for w, Sn, Sr in lst), key=lambda t: t[0])
        r0 = [float(Sr[:, :, :, 0].max()) for w, Sn, Sr in lst]
        r28 = [float(Sr.max()) for w, Sn, Sr in lst]

        def where(S, off0_only):
            A = S[:, :, :, 0] if off0_only else S
            ix = np.unravel_index(int(np.argmax(A)), A.shape)
            return f'{NAMED[ix[0]]!r} sign {SIGNS[ix[1]]:+d} {CHS[ix[2]]}' + ('' if off0_only else f' offset {ix[3]}')
        cnt = {t: int(sum((Sn[:, :, :, 0] >= t).sum() for _, Sn, _ in lst)) for t in (0, 5, 10, 20)}
        out.append(f'  {kind} {var}: {len(lst)} windows | offset 0 best {b0[0]:.2f} ({b0[1]["label"]} n {b0[1]["n"]}; {where(b0[2], True)}) | 0..28 best {b28[0]:.2f} ({b28[1]["label"]} n {b28[1]["n"]}; {where(b28[2], False)}) | '
                   f'random max {max(r0):.2f} / {max(r28):.2f}, per-window median {float(np.median(r0)):.2f} / {float(np.median(r28)):.2f} | counts ' + ', '.join(f'>= {t}: {v}' for t, v in cnt.items()))
        for w, Sn, Sr in lst:
            for X0, nm in ((Sn, 'named'), (Sr, 'random')):
                for ix in zip(*np.nonzero(X0 >= T300)):
                    hits.append((float(X0[ix]), nm, w['label'], w['n'], ix))
    allrand = [float(Sr.max()) for _, Sr in ((k, S[nn:]) for k, S in res.items())]
    allrand0 = [float(S[nn:, :, :, 0].max()) for S in res.values()]
    allnamed0 = [float(S[:nn, :, :, 0].max()) for S in res.values()]
    allnamed28 = [float(S[:nn].max()) for S in res.values()]
    out.append('')
    out.append(f'random-stream null of the maximum (all {len(res)} windows): max over offset 0 {max(allrand0):.2f}, over offsets 0..28 {max(allrand):.2f}; named streams: max offset 0 {max(allnamed0):.2f}, offsets 0..28 {max(allnamed28):.2f}')
    out.append(f'cells >= T300 {T300:.2f}: {len(hits)}')
    for h in sorted(hits, key=lambda t: -t[0])[:40]:
        out.append(f'   {h}')
    txt = '\n'.join(out) + '\n'
    (OUT / 'summary.txt').write_text(txt, encoding='utf-8', newline='\n')
    print(txt)


# ---- list / selftest -----------------------------------------------------------------------------------------------------------------------------------------
def cmd_list(a=None):
    P._init()
    _setup()
    lib = P._G['lib']
    tsv = {}
    for line in open(DATA / 'library.tsv', encoding='utf-8').read().split('\n')[1:]:
        f = line.split('\t')
        if len(f) >= 5:
            tsv[f[0]] = f
    out = [f'{len(NAMED)} named streams (library index | name | length | period | flat-IoC-excluded):']
    for i, nm in zip(_G['named_idx'], NAMED):
        f = tsv.get(nm, ['', '', '', '', ''])
        out.append(f'  {i:4d} | {nm} | {f[1]} | {f[2]} | {f[4]}')
    wins, skipped = build_windows()
    out.append('')
    for kind in ('page', 'clause'):
        for var in ('A', 'B'):
            ws_ = [w for w in wins if w['kind'] == kind and w['variant'] == var]
            sk = [w for w in skipped if w['kind'] == kind and w['variant'] == var]
            out.append(f'{kind} {var}: {len(ws_)} windows >= {MINLEN} runes (n: min {min(w["n"] for w in ws_)}, mean {np.mean([w["n"] for w in ws_]):.0f}, n=300: {sum(w["n"] == 300 for w in ws_)}), '
                       f'skipped {len(sk)}: ' + ', '.join(f'{w["label"]}(n {w["n"]})' for w in sk))
    out.append(f'unique (section, start, n) tasks: {len(unique_tasks())}')
    out.append(f'page starts mid-word: {sum(w["mid_word"] for w in wins if w["kind"] == "page" and w["variant"] == "A")} of {sum(1 for w in wins if w["kind"] == "page" and w["variant"] == "A")} (A windows); '
               f'clause starts mid-word: {sum(w["mid_word"] for w in wins if w["kind"] == "clause" and w["variant"] == "A")}')
    txt = '\n'.join(out) + '\n'
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'streams_and_windows.txt').write_text(txt, encoding='utf-8', newline='\n')
    print(txt)


def cmd_selftest(a=None):
    LPM.lower()
    P._init()
    _setup()
    pl = make_plant('m04', 'cicada', 0)
    c, ws = pl['cipher'][:150], pl['ws'][:150]
    ws0 = list(ws)
    ws0[0] = 0
    k = _G['keys'][pl['stream']]
    logW = C.log_common(c, Q_DEC, C.Q)
    a1 = guard(c, np.ascontiguousarray(k[:150 + 16 + NOFF - 1]), pl['sign'], 'hold', ws, logW)
    a0 = guard(c, np.ascontiguousarray(k[:150 + 16 + NOFF - 1]), pl['sign'], 'hold', ws0, logW)
    print('ws[0] 1 vs 0 identical:', bool(np.array_equal(a1, a0)), 'plant stream', pl['name'], 'S at offset 0', a1[0])
    sec, st, n = 15, 2829, 300
    t0 = time.process_time()
    cc, w2 = flags(sec, st, n)
    drive(cc, w2, _G['keys'][:5])
    dt = (time.process_time() - t0) / 5
    print(f'one window n {n}, one stream, 4 passes x 29 offsets: {dt:.3f} cpu-s; whole task ({len(NAMED)} named + {NRAND} random): {dt * (len(NAMED) + NRAND):.0f} cpu-s')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('list', 'selftest', 'plants', 'pwrong', 'psummary', 'run', 'summary'))
    ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()
    {'list': cmd_list, 'selftest': cmd_selftest, 'plants': cmd_plants, 'pwrong': cmd_pwrong, 'psummary': cmd_psummary, 'run': cmd_run, 'summary': cmd_summary}[a.cmd](a)
