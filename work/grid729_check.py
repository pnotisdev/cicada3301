"""Does the 27 x 27 layout of section 0.7 (729 runes) carry structure? A third-party claim (a "729 matrix", mirrored 3-rune nodes read along rows, columns and
diagonals) arranges the first LP2 section into 27 columns. Two keyless tests with shuffle nulls and a planted control:

1. Lag spectrum of section 0.7 alone, lags 1..60: equal-rune pairs (c_i == c_{i+L}) against the expectation from the rune frequencies. A cipher whose encryption
   order is the COLUMN order of a width-27 grid would show the anti-repeat deficit at lag 27 instead of lag 1.
2. Mirrored triples a-b-a (equal outer runes at equal distance d from the centre) along rows, columns and both diagonals of the width-w grid, w = 20..34: observed
   count against 300 shuffles of the same 729 runes. In the linear stream a mirrored triple is an equal pair at lag 2d (row), 2dw (column), 2d(w+1) and
   2d(w-1) (diagonals), so this is a restatement of lag coincidences; a layout with hidden mirrors would show up at w = 27 only.
Planted control: the same runes with 40, 100 and 200 mirrored triples forced along random lines of the 27-grid, to show how many hidden mirrors the count can see.

    python work/grid729_check.py          # -> results/analysis/grid729_check.txt
"""
import os
import sys

import numpy as np

import lp
import stats

HERE = os.path.dirname(os.path.abspath(__file__))
N = lp.N


def mirrors(grid, w):
    """number of triples (a, b, c) with a == c, a at distance d on each side of b, along rows, columns, both diagonals (a, c inside the grid)"""
    h = len(grid) // w
    g = grid[:h * w].reshape(h, w)
    n = 0
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        for d in range(1, max(h, w)):
            for r in range(h):
                for c in range(w):
                    r1, c1, r2, c2 = r - dr * d, c - dc * d, r + dr * d, c + dc * d
                    if 0 <= r1 < h and 0 <= r2 < h and 0 <= c1 < w and 0 <= c2 < w and g[r1, c1] == g[r2, c2]:
                        n += 1
    return n


def mirrors_fast(grid, w):
    """the same count as mirrors(), through index arrays (checked against it in main)"""
    h = len(grid) // w
    total = 0
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        for d in range(1, max(h, w)):
            step = dr * w + dc
            lag = 2 * d * step
            if lag <= 0:
                continue
            # centre cells (r, c) with the two outer cells inside the grid
            for r in range(h):
                if not (0 <= r - dr * d and r + dr * d < h):
                    continue
                cs = np.arange(w)
                ok = (cs - dc * d >= 0) & (cs - dc * d < w) & (cs + dc * d >= 0) & (cs + dc * d < w)
                cs = cs[ok]
                if len(cs) == 0:
                    continue
                a = (r - dr * d) * w + cs - dc * d
                b = (r + dr * d) * w + cs + dc * d
                total += int((grid[a] == grid[b]).sum())
    return total


def main():
    c = np.array(lp.runes_of(stats.SEGS[7]))
    assert len(c) == 729, len(c)
    rng = np.random.default_rng(7)
    out = [f"section 0.7: {len(c)} runes = 27 x 27", ""]
    f = np.bincount(c, minlength=N) / len(c)
    S = float((f ** 2).sum())
    out.append("1. equal pairs at lag L inside section 0.7 (expected = (729 - L) * S, S = %.4f):" % S)
    rows = []
    for L in range(1, 61):
        eq = int((c[:-L] == c[L:]).sum())
        e = (len(c) - L) * S
        rows.append((L, eq, e, (eq - e) / np.sqrt(e)))
    out.append("   lag: obs / exp (z)   " + "  ".join(f"{L}: {eq}/{e:.0f} ({z:+.1f})" for L, eq, e, z in rows if L in (1, 2, 3, 26, 27, 28, 54, 56)))
    zs = np.array([z for _, _, _, z in rows])
    out.append("   lags with |z| > 2.5: " + ", ".join(f"{L} ({z:+.1f}, {eq}/{e:.0f})" for L, eq, e, z in rows if L > 1 and abs(z) > 2.5))
    out.append(f"   most extreme z over lags 2..60: {zs[1:].min():+.1f} .. {zs[1:].max():+.1f} (lag 1: {zs[0]:+.1f}); the maximum of 59 normal z-scores exceeds 2.9 about 5% of the time")
    Lm = 2 + int(np.argmax(zs[1:]))
    po = pe = 0.0
    for si in range(8, 16):                                             # replication of the largest lag in the other LP2 sections
        d = np.array(lp.runes_of(stats.SEGS[si]))
        if len(d) > 100:
            fd = np.bincount(d, minlength=N) / len(d)
            po += int((d[:-Lm] == d[Lm:]).sum()); pe += (len(d) - Lm) * float((fd ** 2).sum())
    out.append(f"   the largest lag in 0.7 is {Lm}; the same lag in sections 0.8-0.15 together: {po:.0f} equal pairs against {pe:.1f} expected, z {(po - pe) / np.sqrt(pe):+.1f}")
    out.append("")
    out.append("2. mirrored triples (equal outer runes at equal distance) in the width-w grid, observed / mean of 300 shuffles (z):")
    res = {}
    for w in range(20, 35):
        obs = mirrors_fast(c, w)
        null = np.array([mirrors_fast(rng.permutation(c), w) for _ in range(300)])
        res[w] = (obs, null.mean(), (obs - null.mean()) / null.std())
    out.append("   " + "   ".join(f"w={w}: {o}/{m:.0f} ({z:+.1f})" for w, (o, m, z) in res.items()))
    assert mirrors(c, 27) == mirrors_fast(c, 27), "fast counter differs from the reference"
    # controls: force n mirrored triples along random lines of the 27-grid
    for n in (40, 100, 200):
        g = c.copy()
        for _ in range(n):
            dr, dc = ((0, 1), (1, 0), (1, 1), (1, -1))[int(rng.integers(4))]
            d = int(rng.integers(1, 6))
            r, cc = int(rng.integers(d, 27 - d)), int(rng.integers(d, 27 - d))
            g[(r - dr * d) * 27 + cc - dc * d] = g[(r + dr * d) * 27 + cc + dc * d]
        ob = mirrors_fast(g, 27)
        nl = np.array([mirrors_fast(rng.permutation(g), 27) for _ in range(300)])
        out.append(f"   control ({n} forced mirrors, w = 27): {ob} against shuffled mean {nl.mean():.0f}, z {(ob - nl.mean()) / nl.std():+.1f}"
                   f"{' (the real section: z %+.1f)' % res[27][2] if n == 40 else ''}")
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "grid729_check.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
