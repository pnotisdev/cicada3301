#!/usr/bin/env python3
"""Whole-section check of the best rows of a prng-time sweep (`prngx bgsweep java|pymt` over millisecond timestamps).

    python work/prngx/time_verify.py <sweep.tsv> --gen java|pymt [--top 10] [--controls 8]

The candidate's keys are rebuilt by code independent of the Rust engine (CPython's own random.Random for pymt; the
java.util.Random specification of ref/gen_vectors.py for java), the WHOLE section is decoded with the boundary-free
bigram beam (work/phpmt/bg.py::ref_decode, the decoder the Rust bgsweep mirrors) and compared with the same decode under
`--controls` random timestamps of the same month. A true key keeps about +10 per rune; a wrong one about -10.5.
A row is a candidate when it keeps at least +2.0 per rune and beats every control by 5.
"""
import argparse
import os
import random
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "ref"))
sys.path.insert(0, WORK)
sys.path.insert(0, os.path.join(WORK, "phpmt"))
import bg  # noqa: E402
import lp  # noqa: E402
import stats  # noqa: E402
from gen_vectors import JavaRandom  # noqa: E402

PASS_SCORE, PASS_MARGIN = 2.0, 5.0


def java_keys(seed, mp, n):
    j, out = JavaRandom(seed), []
    while len(out) < n:
        if mp == 0:
            out.append(j.next_int(29))
        elif mp == 1:
            out.append(int(j.next_double() * 29))
        else:
            out.append(abs(j.next_int()) % 29)
    return out


def pymt_keys(seed, mp, n):
    r, out = random.Random(seed), []
    while len(out) < n:
        x = r.getrandbits(32)
        if mp == 0:
            out.append(x % 29)
        elif mp == 1:
            out.append((x * 29) >> 32)
        elif mp == 2:
            if x >> 27 < 29:
                out.append(x >> 27)
        elif mp == 3:
            if x & 31 < 29:
                out.append(x & 31)
        elif mp == 4:
            out.append((x >> 1) % 29)
        else:
            y = r.getrandbits(32)
            out.append(((((x >> 5) << 26) | (y >> 6)) * 29) >> 53)
    return out


def keys(gen, seed, mp, n):
    return np.array(java_keys(seed, mp, n) if gen == "java" else pymt_keys(seed, mp, n))


def plant_windows(gen, seed, mp, model, sign, atb, keep, plain_path, coin_seed=3):
    """Encrypt every window of a plaintext windows file with the keys of `seed`, built by the independent code above (not by the
    engine), under the anti-repeat rule of the engine's `plant` mode: model 0 re-draws (up to 5 times) and model 1 spends one key value
    as a coin, each with probability 1 - keep per collision. Returns the windows file text ('W planted_<name> -1', R, L)."""
    rng = random.Random(coin_seed)
    out = []
    with open(plain_path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    for i, line in enumerate(lines):
        if not line.startswith("W "):
            continue
        name = line.split()[1]
        runes = [int(x) for x in lines[i + 1][2:].split()]
        lens = lines[i + 2][2:] if i + 2 < len(lines) and lines[i + 2].startswith("L ") else ""
        key = keys(gen, seed, mp, 4 * len(runes) + 64)
        j, prev, c = 0, -1, []
        for p in runes:
            t = 28 - p if atb else p
            y = (t + sign * int(key[j])) % 29
            j += 1
            if model == 0:
                tries = 0
                while prev >= 0 and y == prev and rng.random() >= keep and tries < 5:
                    y = (t + sign * int(key[j])) % 29
                    j += 1
                    tries += 1
            elif prev >= 0 and y == prev:
                j += 1                                   # the coin value
                if rng.random() >= keep:
                    y = (t + sign * int(key[j])) % 29
                    j += 1
            c.append(y)
            prev = y
        out += [f"W planted_{name} -1", "R " + " ".join(map(str, c)), "L " + lens]
    return "\n".join(out) + "\n"


def month_bounds(seed):
    """[first ms, last ms + 1) of the UTC month that contains the timestamp `seed`"""
    import datetime as dt
    t = dt.datetime.fromtimestamp(seed / 1000, dt.timezone.utc)
    a = dt.datetime(t.year, t.month, 1, tzinfo=dt.timezone.utc)
    b = dt.datetime(t.year + (t.month == 12), t.month % 12 + 1, 1, tzinfo=dt.timezone.utc)
    return int(a.timestamp() * 1000), int(b.timestamp() * 1000)


def window_runes(window, plant=None):
    """(runes, previous rune) of an LP2 section window 'seg0.N', or of a window of a planted file (controls)"""
    if plant:
        with open(plant, encoding="utf-8") as f:
            lines = f.read().splitlines()
        for i, l in enumerate(lines):
            if l.startswith("W ") and l.split()[1] == window:
                return np.array([int(x) for x in lines[i + 1][2:].split()]), int(l.split()[2])
        raise KeyError(window)
    sec = int(re.match(r"seg0\.(\d+)", window).group(1))
    prev = int(lp.runes_of(stats.SEGS[sec - 1])[-1]) if sec > 7 else -1
    return np.array(lp.runes_of(stats.SEGS[sec])), prev


def verify(tsv, gen, top=10, controls=8, out=print, plant=None):
    tbl = bg.load_table()
    with open(tsv, encoding="utf-8") as f:
        rows = [l.rstrip("\n").split("\t") for l in f.read().splitlines()[1:] if l.strip()]
    out(f"# whole-section check of the best {min(top, len(rows))} rows of {os.path.basename(tsv)} ({gen}): bigram score per rune over the "
        f"whole section; {controls} random timestamps of the same month as controls; candidate = >= {PASS_SCORE:+.1f} and >= control max + {PASS_MARGIN}")
    if not rows:
        out("no row reached the sweep's floor (score >= 0): nothing to verify")
        out("0 candidates")
        return 0
    rng = random.Random(1033)
    seen, n_pass, k = set(), 0, 0
    for score, seed, window, model, mp, sign, atb in (r[:7] for r in rows):
        key = (seed, model, mp, sign, atb)
        if key in seen:
            continue
        seen.add(key)
        k += 1
        if k > top:
            break
        c, prev = window_runes(window, plant)
        n = 3 * len(c) + 60

        def whole(sd):
            s, _ = bg.ref_decode(c, prev, keys(gen, sd, int(mp), n), int(sign), int(atb), int(model), tbl)
            return s / len(c)

        real = whole(int(seed))
        lo, hi = month_bounds(int(seed))
        ctl = [whole(rng.randrange(lo, hi)) for _ in range(controls)]
        ok = real >= PASS_SCORE and real >= max(ctl) + PASS_MARGIN
        n_pass += ok
        out(f"{'CANDIDATE' if ok else 'noise    '}  screen {score}  seed {seed}  {window} model {model} map {mp} sign {sign} atb {atb}: "
            f"{real:+.2f} per rune over {len(c)} runes (controls {np.mean(ctl):+.2f}, max {max(ctl):+.2f})")
    out(f"{n_pass} candidates")
    return n_pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tsv")
    ap.add_argument("--gen", required=True, choices=["java", "pymt"])
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--controls", type=int, default=8)
    ap.add_argument("--plant", help="windows file of a planted sweep (positive control) instead of the LP2 sections")
    ap.add_argument("--out", help="also write the report to this file")
    a = ap.parse_args()
    lines = []

    def out(s):
        print(s)
        lines.append(s)

    verify(a.tsv, a.gen, a.top, a.controls, out, a.plant)
    if a.out:
        with open(a.out, "w", newline="\n", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
