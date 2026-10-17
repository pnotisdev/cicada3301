#!/usr/bin/env python3
"""Verify the best candidates of a step-domain seed sweep (step.py sweep ... out.tsv): regenerate each seed's keys with the Rust
engine (any length), decode the section from the start of the winning window to its end with the winning setting, and report the
index of coincidence of the decoded classes inside the window and beyond it. A true seed keeps about 1.8 beyond the window; a
chance maximum falls back to 1.0.

    python work/phpmt/step_verify.py <sweep.tsv> --gen <gen> [--top 10]
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
sys.path.insert(0, str(WORK))
sys.path.insert(0, str(WORK / "kscreen"))
import lp  # noqa: E402
import stats  # noqa: E402
import step28  # noqa: E402

EXE = "phpmt.exe" if os.name == "nt" else "phpmt"
_CAND = [p for p in (HERE / "target" / "release" / EXE, HERE / "target_gen" / "release" / EXE) if p.exists()]
BIN = max(_CAND, key=lambda p: p.stat().st_mtime) if _CAND else HERE / "target" / "release" / EXE   # the newest build has keysn
NS = 240


def rust_keys(gen, seed, km, count):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "k.txt")
        subprocess.run([str(BIN), "keysn", gen, str(seed), str(seed + 1), out, str(km), str(count)], check=True, capture_output=True)
        v = [int(x) for x in Path(out).read_text().split()]
    return [np.array(v[1:1 + count]), np.array(v[1 + count:])]


def ioc_of(d):
    d = d[d >= 0]
    n = len(d)
    return step28.NC * (int((np.bincount(d, minlength=step28.NC) ** 2).sum()) - n) / (n * (n - 1)) if n > 1 else float("nan")


def verify(gen, seed, window, variant, mp, mode, m):
    sec, start = map(int, re.match(r"sec0\.(\d+)@(\d+)", window).groups())
    c = np.array(lp.runes_of(stats.SEGS[sec]))
    prev = int(c[start - 1]) if start else (int(lp.runes_of(stats.SEGS[sec - 1])[-1]) if sec > 7 else -1)
    J = step28.step_classes(c[start:], prev, variant)
    count = len(J) + 50
    if variant == "A":
        key = rust_keys(gen, seed, 28, count)[mp]
    else:
        k = rust_keys(gen, seed, 29, count)[mp]
        key = step28.LOG2[k[k != 0]]
    idx = step28.key_index(J, mode)
    ok = (J != 255) & (idx < len(key))
    dec = np.full(len(J), -1)
    dec[ok] = (J[ok] - (m * key[idx[ok]]) % step28.NC) % step28.NC
    return ioc_of(dec[:NS]), ioc_of(dec[NS:]), int((dec[NS:] >= 0).sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tsv")
    ap.add_argument("--gen", required=True)
    ap.add_argument("--top", type=int, default=10)
    a = ap.parse_args()
    rows = [l.split("\t") for l in Path(a.tsv).read_text(encoding="utf-8").splitlines()[1:] if l.strip()]
    print(f"# step-domain verification of the {min(a.top, len(rows))} best candidates of {a.gen} "
          f"({os.path.relpath(a.tsv, WORK.parent).replace(os.sep, '/')}); IoC inside the window / beyond it to the end of the section")
    if not rows:
        print("no candidate reached the sweep's floor")
        return 0
    for ioc, seed, window, variant, mp, mode, m in rows[:a.top]:
        w, beyond, n = verify(a.gen, int(seed), window, variant, int(mp), mode, int(m))
        print(f"{ioc}\tseed {seed}\t{window} {variant} map {mp} {mode} m={m}: window {w:.3f}, beyond ({n} steps) {beyond:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
