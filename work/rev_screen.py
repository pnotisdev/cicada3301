"""Reverse-direction screen: the key runs from the END of each segment backwards.

The reversed rune stream is decoded with a forward keystream and scored against a dictionary of
words spelt backwards. Covers every number keystream at every start offset (sliding, like screen
2), all keyword keys at the segment end, and the random controls.

    python rev_screen.py
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


def reversed_inputs():
    segs = lp.load_segments()
    inputs = {}
    for i in attack.SCREEN_SEGS:
        toks = segs[i][::-1]
        T = attack.Text(toks)
        inputs[i] = (np.array(T.c[:attack.SCREEN_RUNES]), [w for w in T.words if w[1] <= attack.SCREEN_RUNES])
    return inputs


def _init():
    _W["num"] = keystreams.number_keystreams()
    _W["kw"] = keystreams.keywords()
    R = random.Random(4242)
    for r in range(4):
        _W["num"][f"CONTROL random {r}"] = np.array([R.randrange(N) for _ in range(keystreams.LEN)])
    _W["inp"] = reversed_inputs()


def _one(name):
    if name in _W["num"]:
        ks = _W["num"][name]
        p = keystreams.period(ks)
        limit = (p + attack.STEP) if p else len(ks) - attack.SCREEN_RUNES - 30
        offsets = np.arange(0, limit, attack.STEP)
    else:
        ks = _W["kw"][name]
        offsets = np.arange(0, min(len(ks) - 400, 30), attack.STEP)  # keyword period is short: b + offsets cover it
    best = []
    for seg, (c, words) in _W["inp"].items():
        for sign in (1, -1):
            for atb in (False, True):
                for o0 in range(0, len(offsets), 128):
                    offs = offsets[o0:o0 + 128]
                    S = attack.fast_screen_batch(c, words, ks, offs, sign, atb, reverse=True)
                    m = S.max(axis=1)
                    k = int(m.argmax())
                    best.append((float(m[k]), name, seg, int(offs[k]), sign, atb, int(S[k].argmax())))
    best.sort(reverse=True)
    return best[:5]


if __name__ == "__main__":
    names = list(keystreams.number_keystreams()) + [f"CONTROL random {r}" for r in range(4)] + \
        list(keystreams.keywords())
    t0 = time.time()
    rows = []
    with Pool(initializer=_init) as pool:
        for k, r in enumerate(pool.imap_unordered(_one, names)):
            rows += r
            if k % 100 == 0:
                print(f"{k}/{len(names)} {time.time() - t0:.0f}s", flush=True)
    rows.sort(reverse=True)
    ctrl = max(r[0] for r in rows if r[1].startswith("CONTROL"))
    print(f"\nreverse direction: {len(names)} keystreams; control max {ctrl:.3f}")
    for r in [r for r in rows if not r[1].startswith("CONTROL")][:15]:
        print(f"  {r[0]:.3f}  {r[1][:36]:36s} seg 0.{r[2]} off={r[3]} sign={r[4]:+d} atb={r[5]} b={r[6]}")
    os.makedirs(os.path.join(HERE, "tmp", "phase4"), exist_ok=True)
    with open(os.path.join(HERE, "tmp", "phase4", "rev_screen.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f)
