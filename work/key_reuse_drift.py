"""Drift-aware two-time-pad test: do two sections (or pages) share a key that restarts at their start?

The earlier "no key reuse between segments" result came from FFT lag scans, which assume the key pointer stays
aligned with the rune index. Under the anti-repeat skip rule the pointer gains one position at every skip
(about 0.028 per rune), so two texts enciphered with the same key from index 0 drift apart by a random walk
(standard deviation ~14 positions after 3,000 runes) and a fixed-lag scan sees only a small part of the aligned pairs.

This script aligns the two ciphertexts with a banded dynamic program (key indices advance for both texts; each text
may skip a key index at cost g = log(s/(1-s))), scoring every aligned pair by the log-likelihood ratio of the English
plaintext difference, w(d) = log(29 Q(d)) with Q(d) = sum_x f(x) f(x-d) (f: English rune frequencies, Emerson). The
alignment starts at (0, 0) (both keys restart) and may end anywhere. Calibration: the same score for a against b[k:]
at many random offsets k (key not shared); z = (S - mean) / sd of those.

Controls: two English texts of the same lengths enciphered with the SAME random key from index 0 under the skip rule
(independent skips) must give z >> 5; texts with different keys must give |z| < 3.

    python work/key_reuse_drift.py segments      # all pairs of unsolved sections (>= 400 runes)
    python work/key_reuse_drift.py pages         # all pairs of pages (starts of pages) of the unsolved sections
"""
import argparse
import os
import random
import sys

import numpy as np

import lp
import sim
import stats

N = lp.N
HERE = os.path.dirname(os.path.abspath(__file__))
S_SKIP = 0.03
G = float(np.log(S_SKIP / (1 - S_SKIP)))
BAND = 40
NEG = -1e9


def make_w():
    f = np.bincount(sim.english_runes(), minlength=N).astype(float)
    f /= f.sum()
    q = np.array([sum(f[x] * f[(x - d) % N] for x in range(N)) for d in range(N)])
    return np.log(N * q)


W = make_w()


def align(a, b, band=BAND):
    """best anchored-start banded alignment score of integer arrays a, b (end free)"""
    n, m = len(a), len(b)
    prev = np.full(m + 1, NEG)
    hi0 = min(m, band)
    prev[:hi0 + 1] = G * np.arange(hi0 + 1)
    best = float(prev.max())
    for i in range(1, n + 1):
        lo, hi = max(0, i - band), min(m, i + band)
        if lo > hi:
            break
        cur = np.full(m + 1, NEG)
        mm = np.arange(lo, hi + 1)
        diag = np.full(len(mm), NEG)
        ok = mm >= 1
        diag[ok] = prev[mm[ok] - 1] + W[(a[i - 1] - b[mm[ok] - 1]) % N]
        up = prev[mm] + G
        x = np.maximum(diag, up)
        run = np.maximum.accumulate(x - G * mm)
        cur[mm] = run + G * mm
        best = max(best, float(cur[lo:hi + 1].max()))
        prev = cur
    return best


def zscore(a, b, rng, nulls=40, band=BAND):
    obs = align(a, b, band)
    ns = []
    room = len(b) - len(a)
    for _ in range(nulls):
        # null: b shifted by k (key not shared); b may be shorter than a, so shift a instead in that case
        if room > 3 * band:
            k = rng.randrange(2 * band + 50, len(b) - min(len(a), len(b)) // 2)
            ns.append(align(a, b[k:], band))
        else:
            k = rng.randrange(2 * band + 50, max(2 * band + 51, len(a) - len(b) // 2))
            ns.append(align(a[k:], b, band))
    ns = np.array(ns)
    return obs, (obs - ns.mean()) / (ns.std() + 1e-9)


def english_pair(n1, n2, rng, same_key, q=0.82, start=3000):
    eng = sim.english_runes()
    pa, pb = eng[start:start + n1], eng[start + 20000:start + 20000 + n2]
    kl = max(n1, n2) * 2 + 200

    def enc(p, key):
        out, j, prev = [], 0, -1
        for t in p:
            y = (t + key[j]) % N
            j += 1
            while y == prev and rng.random() < q:
                y = (t + key[j]) % N
                j += 1
            out.append(y)
            prev = y
        return out
    k1 = [rng.randrange(N) for _ in range(kl)]
    k2 = k1 if same_key else [rng.randrange(N) for _ in range(kl)]
    return np.array(enc(pa, k1)), np.array(enc(pb, k2))


def run_controls(rng, lens):
    out = []
    for same in (True, False):
        for n1, n2 in lens:
            a, b = english_pair(n1, n2, rng, same)
            obs, z = zscore(a, b, rng)
            out.append(f"   control {'SAME key' if same else 'different keys'} ({n1}, {n2} runes): S = {obs:.1f}, z = {z:+.1f}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["segments", "pages"])
    ap.add_argument("--nulls", type=int, default=40)
    args = ap.parse_args()
    rng = random.Random(5)
    segs = stats.SEGS
    units = []
    if args.what == "segments":
        for i in stats.UNSOLVED:
            r = lp.runes_of(segs[i])
            if len(r) >= 400:
                units.append((f"0.{i}", np.array(r)))
    else:
        import red_runs
        offs = red_runs.page_seg_offsets()
        starts = {}
        for page, (seg, pos) in offs.items():
            if seg in stats.UNSOLVED:
                starts.setdefault(seg, set()).add(pos)
        for seg in sorted(starts):
            r = lp.runes_of(segs[seg])
            cuts = sorted(starts[seg]) + [len(r)]
            for x, y in zip(cuts, cuts[1:]):
                if y - x >= 150:
                    units.append((f"0.{seg}@{x}", np.array(r[x:y])))
    out = []
    P = out.append
    P(f"{len(units)} units ({args.what}); band {BAND}, skip prior {S_SKIP}, {args.nulls} offset nulls per pair")
    lens = [(1500, 1500), (700, 1000)] if args.what == "segments" else [(260, 260), (260, 150)]
    P("controls (English, restart-aligned vs independent keys):")
    for line in run_controls(rng, lens):
        P(line)
        print(line, flush=True)
    rows = []
    for x in range(len(units)):
        for y in range(x + 1, len(units)):
            (na, a), (nb, b) = units[x], units[y]
            obs, z = zscore(a, b, rng, args.nulls)
            rows.append((z, na, nb, obs))
        print(f"  {units[x][0]} done", flush=True)
    rows.sort(reverse=True)
    zs = np.array([r[0] for r in rows])
    P("")
    P(f"{len(rows)} pairs: z mean {zs.mean():+.2f}, sd {zs.std():.2f}, max {zs.max():+.2f}; top 8:")
    for z, na, nb, obs in rows[:8]:
        P(f"   {na:12s} vs {nb:12s} S = {obs:6.1f}  z = {z:+.2f}")
    P(f"expected max z among {len(rows)} null pairs ~ {np.sqrt(2 * np.log(len(rows))):.1f}")
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, f"key_reuse_drift_{args.what}.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
