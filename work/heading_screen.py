"""Screen every keystream from each mid-segment heading / paragraph start (key-restart hypothesis).

Windows: red headings found by OCR (red_runs.py) and '&' paragraph starts inside the unsolved
segments. Number keystreams are slid over all start offsets (step 12, 24-shift window); keyword
keys over one period. Random controls run the same slide.

    python heading_screen.py
"""
import json
import os
import random
import time
from multiprocessing import Pool

import numpy as np

import attack
import keystreams
import lp

N = lp.N
HERE = os.path.dirname(os.path.abspath(__file__))
_W = {}


def windows():
    path = os.path.join(HERE, "ref", "restart_windows.json")      # committed copy of red_runs.py's output
    if not os.path.exists(path):
        path = os.path.join(HERE, "tmp", "phase4", "restart_windows.json")
    raw = json.load(open(path))
    seen, out = set(), []
    for seg, start, _ in raw:
        if any(s == seg and abs(start - k) <= 2 for s, k in seen):
            continue
        seen.add((seg, start))
        out.append((seg, start))
    return out


def window_inputs():
    segs = lp.load_segments()
    inputs = {}
    for seg, start in windows():
        T = attack.Text(segs[seg])
        hi = start + attack.SCREEN_RUNES
        c = np.array(T.c[start:hi])
        words = [(a - start, b - start) for a, b in T.words if a >= start and b <= hi]
        inputs[(seg, start)] = (c, words)
    return inputs


def _init():
    _W["num"] = keystreams.number_keystreams()
    _W["kw"] = keystreams.keywords()
    R = random.Random(777)
    for r in range(4):
        _W["num"][f"CONTROL random {r}"] = np.array([R.randrange(N) for _ in range(keystreams.LEN)])
    _W["inp"] = window_inputs()


def _one(name):
    if name in _W["num"]:
        ks = _W["num"][name]
        p = keystreams.period(ks)
        limit = (p + attack.STEP) if p else len(ks) - attack.SCREEN_RUNES - 30
        offsets = np.arange(0, limit, attack.STEP)
    else:
        ks = _W["kw"][name]
        offsets = np.arange(0, 30, attack.STEP)
    best = []
    for (seg, start), (c, words) in _W["inp"].items():
        for sign in (1, -1):
            for atb in (False, True):
                for o0 in range(0, len(offsets), 128):
                    offs = offsets[o0:o0 + 128]
                    S = attack.fast_screen_batch(c, words, ks, offs, sign, atb)
                    m = S.max(axis=1)
                    k = int(m.argmax())
                    best.append((float(m[k]), name, seg, start, int(offs[k]), sign, atb, int(S[k].argmax())))
    best.sort(reverse=True)
    return best[:5]


if __name__ == "__main__":
    names = list(keystreams.number_keystreams()) + [f"CONTROL random {r}" for r in range(4)] + \
        list(keystreams.keywords())
    print("windows:", windows(), flush=True)
    t0 = time.time()
    rows = []
    with Pool(initializer=_init) as pool:
        for k, r in enumerate(pool.imap_unordered(_one, names)):
            rows += r
            if k % 100 == 0:
                print(f"{k}/{len(names)} {time.time() - t0:.0f}s", flush=True)
    rows.sort(reverse=True)
    ctrl = max(r[0] for r in rows if r[1].startswith("CONTROL"))
    print(f"\nheading restarts: {len(names)} keystreams; control max {ctrl:.3f}")
    for r in [r for r in rows if not r[1].startswith("CONTROL")][:15]:
        print(f"  {r[0]:.3f}  {r[1][:36]:36s} 0.{r[2]}@{r[3]} off={r[4]} sign={r[5]:+d} atb={r[6]} b={r[7]}")
    with open(os.path.join(HERE, "tmp", "phase4", "heading_screen.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f)
