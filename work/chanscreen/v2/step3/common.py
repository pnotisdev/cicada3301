"""Shared pieces of step3 (campaign, E3 nulls, E4 plants, clause scan). Read-only imports of v1 / v2 / m04 / lp code."""
import os
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_v] = '1'
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
V2 = HERE.parent
V1 = V2.parent
ROOT = V1.parent.parent
for p in (V2, V1, V2 / 'step2' / 'followup', ROOT / 'work', ROOT / 'work' / 'm04'):
    sys.path.insert(0, str(p))

import lp  # noqa: E402
from engine import all_offsets  # noqa: E402
from proposal import log_common  # noqa: E402

Q = 29
CHANNELS = ('hold', 'spend', 'skip5', 'coin')
SIGNS = (1, -1)
Q_DECODER = 0.81
ALIAS_K = 20
THRESHOLDS = json.loads((V2 / 'step2' / 'thresholds.json').read_text())
T300 = THRESHOLDS['inventory']['300']['T_nats']
COUNT_AT = (0.0, 5.0, 10.0, 15.0, 20.0)
NULL_RECORDS = (0, 50, 100, 150, 175)
NULL_RECORDS2 = (10, 30, 110, 130, 145)
LIB_PATH = ROOT / 'work' / 'kscreen' / 'data' / 'library.ksb'
OUT = ROOT / 'results' / 'chanscreen'


def model():
    z = np.load(V1 / 'model.npz')
    return z['pi'], z['L']


def read_library(path=LIB_PATH):
    import struct
    d = open(path, 'rb').read()
    assert d[:4] == b'KSB1'
    n = struct.unpack_from('<I', d, 4)[0]
    pos, out = 8, []
    for _ in range(n):
        ln = struct.unpack_from('<H', d, pos)[0]
        pos += 2
        name = d[pos:pos + ln].decode('utf-8', 'replace')
        pos += ln
        m = struct.unpack_from('<I', d, pos)[0]
        pos += 4
        out.append((name, np.frombuffer(d, dtype=np.uint8, count=m, offset=pos).astype(np.int32)))
        pos += m
    return out


def chunks(lengths, target=1_000_000):
    out, s, acc = [], 0, 0
    for i, n in enumerate(lengths):
        acc += n
        if acc >= target:
            out.append((s, i + 1))
            s, acc = i + 1, 0
    if s < len(lengths):
        out.append((s, len(lengths)))
    return out


def n300_windows():
    segs = lp.load_segments()
    out = []
    for sec, starts in THRESHOLDS['inventory']['300']['windows'].items():
        sec = int(sec)
        r = lp.runes_of(segs[sec])
        for s in starts:
            out.append(dict(name=f'0.{sec}@{s}', sec=sec, start=s, cipher=[int(x) for x in r[s:s + 300]]))
    return out


def clause_windows(minlen=60):
    """LP2 clauses (text between '.' marks and '&' breaks; a page break does not end a clause) of at least minlen runes"""
    segs = lp.load_segments()
    out = []
    for sec in (7, 8, 9, 11, 12, 13, 14, 15):
        r = lp.runes_of(segs[sec])
        idx = start = 0
        for t in segs[sec]:
            if isinstance(t, int):
                idx += 1
            elif t in ('.', '&'):
                if idx - start >= minlen:
                    out.append(dict(name=f'0.{sec}c@{start}+{idx - start}', sec=sec, start=start, cipher=[int(x) for x in r[start:idx]]))
                start = idx
        if idx - start >= minlen:
            out.append(dict(name=f'0.{sec}c@{start}+{idx - start}', sec=sec, start=start, cipher=[int(x) for x in r[start:idx]]))
    return out


def null_windows(records=None):
    out = []
    for i in (records or NULL_RECORDS):
        r = json.loads((V1 / 'raw' / 'cal' / f'{i:03d}.json').read_text())
        out.append(dict(name=f'cal{i:03d}', sec=-1, start=0, cipher=[int(x) for x in r['cipher']]))
    return out


def windows(kind):
    return {'n300': n300_windows, 'clause': clause_windows, 'null': null_windows, 'null2': lambda: null_windows(NULL_RECORDS2)}[kind]()


def guard_scores(c, key, sign, ch, q, pi, L, logW):
    """S_guard and S (log Z_L - log Z_U) for every offset 0..len(key); -inf where the cell has no support"""
    out = all_offsets(c, key, sign, q, ch, pi, L)
    l, u = out[:, 0], out[:, 1]
    if np.any(np.isnan(l)) or np.any(np.isposinf(l)) or np.any(l > 1e-9):
        raise ValueError('invalid log likelihood')
    if np.any(np.isfinite(l) & np.isneginf(u)):
        raise ValueError('L support outside U')
    with np.errstate(invalid='ignore'):
        s = np.where(np.isfinite(l) & np.isfinite(u), l - u, -np.inf)
        sw = np.where(np.isfinite(l) & np.isfinite(logW), l - logW, -np.inf)
    return np.minimum(s, sw), s
