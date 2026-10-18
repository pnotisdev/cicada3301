#!/usr/bin/env python
"""Diagnose the top LP2 sweep setting (d=1, a=1): what IS the lag-1
first-difference signal? Characterizes the residual histogram, digrams,
position profile, per-section profile, cross-boundary profile, and
shuffle-null baselines for that specific setting."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "work"))

import lp  # noqa: E402
import numpy as np  # noqa: E402

N = 29
SEED = 3301


def main():
    segs = lp.load_segments()
    lp2 = segs[7:16]

    # within-word lag-1 pairs + per-section + per word-position bucket
    prev, cur, per_sec, per_pos = [], [], {i: ([], []) for i in range(9)}, {p: ([], []) for p in range(1, 8)}
    for si, seg in enumerate(lp2):
        c = [t for t in seg if isinstance(t, int)]
        for _w, s, e in lp.word_spans(seg, c):
            for i in range(s + 1, e):
                prev.append(c[i - 1])
                cur.append(c[i])
                per_sec[si][0].append(c[i - 1])
                per_sec[si][1].append(c[i])
                p = min(i - s, 7)
                per_pos[p][0].append(c[i - 1])
                per_pos[p][1].append(c[i])
    prev = np.array(prev, dtype=np.int32)
    cur = np.array(cur, dtype=np.int32)
    n = len(prev)
    r = (cur - prev) % N
    H = np.bincount(r, minlength=N)
    e = n / N
    contrib = (H - e) ** 2 / e
    order = np.argsort(-H)
    L = ["=== top setting (d=1, a=1) residual histogram r = (c_i - c_{i-1}) mod 29, "
         f"within-word pairs n={n} ===",
         f"chi2 = {contrib.sum():.2f}, IoC (lp.ioc normalised) = {lp.ioc([int(v) for v in r]):.4f}",
         "top bins:"]
    for j in order[:12]:
        L.append(f"  r={j:2d} ({lp.LATIN[j]:>3s}) count={H[j]:5d} expected={e:6.1f} "
                 f"excess={H[j]-e:+7.1f} contrib={contrib[j]:7.1f}")
    rest = contrib.copy()
    rest[order[:12]] = 0.0
    L.append(f"  (sum of other 17 bins contrib = {rest.sum():.1f})")
    # digrams
    dig = {}
    for x, y in zip(prev.tolist(), cur.tolist()):
        dig[(x, y)] = dig.get((x, y), 0) + 1
    L.append("\ntop within-word adjacent digrams (observed vs 10,060/841 = 11.96 expected if uniform):")
    for (x, y), c in sorted(dig.items(), key=lambda kv: -kv[1])[:10]:
        L.append(f"  {lp.LATIN[x]}-{lp.LATIN[y]:<3s} count={c}")
    # doubles
    L.append("\ndoubles (c_i == c_{i-1}) within words: "
             f"{int(H[0])} of {n} (expected {e:.1f}, z={(H[0]-e)/(e*(1-1/N))**0.5:+.2f})")
    # per position bucket chi2
    L.append("\nchi2 by word position of the LATER rune (p = i - word_start):")
    for p in range(1, 8):
        pv = np.array(per_pos[p][0], dtype=np.int32)
        cv = np.array(per_pos[p][1], dtype=np.int32)
        if len(pv) == 0:
            continue
        rr = (cv - pv) % N
        Hp = np.bincount(rr, minlength=N)
        ep = len(pv) / N
        L.append(f"  p={str(p) if p < 7 else '7+':>3s} n={len(pv):5d} chi2={((Hp-ep)**2/ep).sum():7.2f}")
    # per-section chi2
    L.append("\nchi2 by section (0.7..0.15):")
    for si in range(9):
        pv = np.array(per_sec[si][0], dtype=np.int32)
        cv = np.array(per_sec[si][1], dtype=np.int32)
        rr = (cv - pv) % N
        Hp = np.bincount(rr, minlength=N)
        ep = len(pv) / N
        L.append(f"  0.{si+7} n={len(pv):5d} chi2={((Hp-ep)**2/ep).sum():7.2f}")

    # cross-word-boundary pairs at lag 1
    cp, cc = [], []
    for seg in lp2:
        c = [t for t in seg if isinstance(t, int)]
        for _w, s, e in lp.word_spans(seg, c):
            if s >= 1:
                cp.append(c[s - 1])
                cc.append(c[s])
    cp = np.array(cp, dtype=np.int32)
    cc = np.array(cc, dtype=np.int32)
    rc = (cc - cp) % N
    Hc = np.bincount(rc, minlength=N)
    ec = len(rc) / N
    L.append(f"\ncross-word-boundary pairs at lag 1: n={len(rc)}, chi2={((Hc-ec)**2/ec).sum():.2f}")
    L.append(f"  cross doubles (r=0): {int(Hc[0])} of {len(rc)} (expected {ec:.1f})")
    L.append("  top cross bins:")
    for j in np.argsort(-Hc)[:8]:
        L.append(f"    r={j:2d} ({lp.LATIN[j]:>3s}) count={Hc[j]:5d} expected={ec:6.1f} excess={Hc[j]-ec:+7.1f}")

    # null baselines for the SPECIFIC setting (1,1): within and cross, 200 shuffles
    lens = [len([t for t in s if isinstance(t, int)]) for s in lp2]
    offsets = np.cumsum([0] + lens)
    C = np.concatenate([np.array([t for t in s if isinstance(t, int)], dtype=np.int16) for s in lp2])
    # within-word lag-1 positions, global
    wprev, wcur = [], []
    for si, seg in enumerate(lp2):
        c = [t for t in seg if isinstance(t, int)]
        base = int(offsets[si])
        for _w, s, e in lp.word_spans(seg, c):
            for i in range(s + 1, e):
                wprev.append(base + i - 1)
                wcur.append(base + i)
    wprev = np.array(wprev, dtype=np.int32)
    wcur = np.array(wcur, dtype=np.int32)
    # cross lag-1 positions, global
    kprev, kcur = [], []
    for si, seg in enumerate(lp2):
        c = [t for t in seg if isinstance(t, int)]
        base = int(offsets[si])
        for _w, s, e in lp.word_spans(seg, c):
            if s >= 1:
                kprev.append(base + s - 1)
                kcur.append(base + s)
    kprev = np.array(kprev, dtype=np.int32)
    kcur = np.array(kcur, dtype=np.int32)
    rng = np.random.default_rng(SEED)
    wnull, knull = [], []
    for _ in range(200):
        Cs = C.copy()
        for si in range(len(lens)):
            sl = slice(int(offsets[si]), int(offsets[si + 1]))
            Cs[sl] = rng.permutation(Cs[sl])
        rw = (Cs[wcur].astype(np.int32) - Cs[wprev].astype(np.int32)) % N
        Hw = np.bincount(rw, minlength=N)
        ew = len(rw) / N
        wnull.append(float(((Hw - ew) ** 2 / ew).sum()))
        rk = (Cs[kcur].astype(np.int32) - Cs[kprev].astype(np.int32)) % N
        Hk = np.bincount(rk, minlength=N)
        ek = len(rk) / N
        knull.append(float(((Hk - ek) ** 2 / ek).sum()))
    ws = sorted(wnull)
    ks = sorted(knull)
    L.append(f"\nspecific-setting shuffle nulls (200 shuffles, same word cuts):")
    L.append(f"  within (n={n}):      real chi2 = {contrib.sum():.2f} | null mean={sum(wnull)/200:.2f} "
             f"p99={ws[min(199, 198)]:.2f} max={ws[-1]:.2f}")
    L.append(f"  cross  (n={len(rc)}): real chi2 = {((Hc-ec)**2/ec).sum():.2f} | null mean={sum(knull)/200:.2f} "
             f"p99={ks[min(199, 198)]:.2f} max={ks[-1]:.2f}")

    # distinct (d,a) top table over word scope d 1..8 (collapse b)
    L.append("\ndistinct (d,a) maxima, word scope, d 1..8 (chi2 is b-invariant):")
    rows = []
    for d in range(1, 9):
        pv = np.array(per_d_pos(d, lp2, offsets), dtype=np.int32)
        cv = np.array(per_d_cur(d, lp2, offsets), dtype=np.int32)
        a = np.arange(1, N, dtype=np.int16)[:, None]
        t = (C[cv][None, :].astype(np.int16) - a * C[pv][None, :].astype(np.int16)) % N
        idx = t + N * np.arange(N - 1, dtype=np.int16)[:, None]
        Hm = np.bincount(idx.ravel(), minlength=(N - 1) * N).reshape(N - 1, N)
        ee = len(pv) / N
        chi2 = ((Hm - ee) ** 2 / ee).sum(axis=1)
        ioc = (Hm * (Hm - 1)).sum(axis=1) / (len(pv) * (len(pv) - 1) / N)
        for ai in range(N - 1):
            rows.append((d, ai + 1, float(chi2[ai]), float(ioc[ai])))
    rows.sort(key=lambda r: -r[2])
    seen = set()
    for d, a, c2, ic in rows:
        if (d, a) in seen:
            continue
        seen.add((d, a))
        L.append(f"  d={d} a={a:2d} chi2={c2:8.2f} ioc={ic:.4f}")
        if len(seen) >= 12:
            break
    text = "\n".join(L)
    with open(os.path.join(HERE, "lag_feedback_diag_1_1_0.txt"), "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print(text)


def per_d_pos(d, lp2, offsets):
    out = []
    for si, seg in enumerate(lp2):
        c = [t for t in seg if isinstance(t, int)]
        base = int(offsets[si])
        for _w, s, e in lp.word_spans(seg, c):
            for i in range(s + d, e):
                out.append(base + i - d)
    return out


def per_d_cur(d, lp2, offsets):
    out = []
    for si, seg in enumerate(lp2):
        c = [t for t in seg if isinstance(t, int)]
        base = int(offsets[si])
        for _w, s, e in lp.word_spans(seg, c):
            for i in range(s + d, e):
                out.append(base + i)
    return out


if __name__ == "__main__":
    main()
