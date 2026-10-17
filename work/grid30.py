"""The page-30 4x4 number grid and its caption (segment 0.10).

Finding: every cell is |3301 - p_k| where p_k is the k-th prime, k = 1, 2, 3, 4, 6, 9, 14, 22, ...
(consecutive differences are Fibonacci numbers 1, 1, 1, 2, 3, 5, 8, ...), written as a clockwise
spiral starting in the cell right of centre... see spiral_order().

    python grid30.py            # verify the reconstruction and run the follow-up tests
"""
import itertools
import sys
from collections import Counter

import numpy as np
import sympy

import lp
import stats

N = lp.N
S = stats.SEGS


def grid_values():
    return [int(t[1:]) for t in S[10] if isinstance(t, str) and t.startswith("#")][:16]


def fib_indices(n):
    """k_1..k_n: 1, 2, 3, 4, 6, 9, 14, ... (differences 1, 1, 1, 2, 3, 5, ...)."""
    f = [1, 1]
    while len(f) < n:
        f.append(f[-1] + f[-2])
    k = [1]
    for i in range(n - 1):
        k.append(k[-1] + ([1] + f)[i])
    return k


def spiral_order():
    """Cell (row, col) for sequence positions 0..15 in the 4x4 grid: start at (1,1), then right,
    down, left, left, up, up, right x3, down x2, then along the bottom row right to left."""
    return [(1, 1), (1, 2), (2, 2), (2, 1), (2, 0), (1, 0), (0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 3),
            (3, 3), (3, 2), (3, 1), (3, 0)]


def reconstruct():
    ks = fib_indices(16)
    ps = [sympy.prime(k) for k in ks]
    grid = [[None] * 4 for _ in range(4)]
    for (r, c), p in zip(spiral_order(), ps):
        grid[r][c] = abs(3301 - p)
    return ks, ps, [v for row in grid for v in row]


def verify():
    ks, ps, rec = reconstruct()
    g = grid_values()
    print("prime indices:", ks)
    print("primes:       ", ps)
    print("grid (page):  ", g)
    print("reconstructed:", rec)
    print("match:", rec == g)
    return rec == g


# ---------------------------------------------------------------- follow-up tests

def caption_tests():
    """Decrypt the caption ᚠᚢᛚᛗ ᚪᛠᚣᛟᚪ with keys built from the grid sequence."""
    cap = lp.runes_of(S[10])
    ks, ps, _ = reconstruct()
    g = grid_values()
    words = (4, 5)
    keys = {
        "primes p_k": ps, "indices k": ks, "grid values": g, "grid spiral order": [abs(3301 - p) for p in ps],
        "primes p_k - 1": [p - 1 for p in ps], "fibonacci": [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144],
        "3301 digits": [3, 3, 0, 1] * 3,
    }
    hits = []
    for name, key in keys.items():
        for start in range(len(key) - len(cap) + 1):
            for sign in (1, -1):
                for atb in (False, True):
                    for b in range(N):
                        p = [((c - sign * (key[start + i] + b)) % N) for i, c in enumerate(cap)]
                        if atb:
                            p = [N - 1 - x for x in p]
                        w1 = "".join(lp.LATIN[x] for x in p[:4])
                        w2 = "".join(lp.LATIN[x] for x in p[4:])
                        s1 = lp.COMMON_N.get(lp.normalize(w1), 0)
                        s2 = lp.COMMON_N.get(lp.normalize(w2), 0)
                        if s1 and s2:
                            hits.append((s1 + s2, name, start, sign, atb, b, w1, w2))
    hits.sort(reverse=True)
    trials = sum((len(k) - len(cap) + 1) * 4 * N for k in keys.values())
    print(f"caption: {trials} key placements tried; {len(hits)} give two dictionary words")
    for h in hits[:10]:
        print(f"  {h[6]} {h[7]}   ({h[1]} start {h[2]} sign {h[3]:+d} atbash {h[4]} b {h[5]})")
    # chance level: random 4- and 5-rune strings
    R = np.random.default_rng(0)
    rnd = 0
    for _ in range(20000):
        p = R.integers(0, N, 9)
        w1 = "".join(lp.LATIN[x] for x in p[:4])
        w2 = "".join(lp.LATIN[x] for x in p[4:])
        rnd += bool(lp.COMMON_N.get(lp.normalize(w1)) and lp.COMMON_N.get(lp.normalize(w2)))
    print(f"  chance that a random 4+5 rune pair is two dictionary words: {rnd / 20000:.4f} "
          f"-> expected {trials * rnd / 20000:.1f} hits by chance")
    return hits


def hill_tests():
    """Grid as a 4x4 Hill-cipher matrix mod 29 on the unsolved segments (blocks of 4 runes)."""
    g = grid_values()
    ks, ps, _ = reconstruct()
    mats = {"grid": g, "grid transposed": [g[c * 4 + r] for r in range(4) for c in range(4)],
            "primes in spiral cells": None}
    grid_p = [[0] * 4 for _ in range(4)]
    for (r, c), p in zip(spiral_order(), ps):
        grid_p[r][c] = p
    mats["primes in spiral cells"] = [v for row in grid_p for v in row]
    res = []
    for name, vals in mats.items():
        M = sympy.Matrix(4, 4, [v % N for v in vals])
        for use_inverse in (True, False):
            try:
                K = M.inv_mod(N) if use_inverse else M
            except ValueError:
                print(f"  {name}: not invertible mod 29")
                break
            K = np.array(K.tolist(), dtype=np.int64) % N
            for i in stats.UNSOLVED:
                toks = S[i]
                c = np.array(lp.runes_of(toks))
                if len(c) < 100:
                    continue
                for off in range(4):
                    cc = c[off:]
                    n4 = len(cc) // 4 * 4
                    blocks = cc[:n4].reshape(-1, 4)
                    for side in ("left", "right"):
                        pb = (blocks @ K.T) % N if side == "left" else (blocks @ K) % N
                        plain = list(c[:off]) + list(pb.ravel()) + list(cc[n4:])
                        res.append((lp.word_score(toks, plain), name, "inverse" if use_inverse else "matrix",
                                    i, off, side))
    res.sort(reverse=True)
    print(f"Hill 4x4: {len(res)} variants; best dictionary scores (real English ~0.7, noise ~0.05):")
    for r in res[:5]:
        print(f"  {r[0]:.3f}  {r[1]} ({r[2]}) seg 0.{r[3]} offset {r[4]} {r[5]}")
    return res


def gematria_search():
    """Do the grid numbers or the sequence primes occur as Gematria sums of unsolved units more
    often than other numbers of similar size?"""
    _, ps, _ = reconstruct()
    targets = set(grid_values()) | set(ps) | {3301, 1033}
    sums = Counter()
    units = Counter()
    for i in stats.UNSOLVED:
        toks = S[i]
        word, line, page, clause = [], [], [], []
        # a bare line or page break is a wrap inside a word (lp.word_spans), so it ends lines and pages but not words or
        # clauses; "$end" closes every unit at the end of the segment
        for t in toks + ["$end"]:
            if isinstance(t, int):
                v = lp.PRIME[t]
                word.append(v); line.append(v); page.append(v); clause.append(v)
                continue
            if t in (" ", ".", "&", "$end") or t.startswith("#"):
                if word:
                    sums[("word", sum(word))] += 1; word = []
            if t in (".", "&", "$end"):
                if clause:
                    sums[("clause", sum(clause))] += 1; clause = []
            if t in ("\n", "%", "&", "$end"):
                if line:
                    sums[("line", sum(line))] += 1; line = []
            if t in ("%", "$end"):
                if page:
                    sums[("page", sum(page))] += 1; page = []
    for kind in ("word", "clause", "line", "page"):
        vals = [v for (k, v), c in sums.items() if k == kind for _ in range(c)]
        hit = [v for v in vals if v in targets]
        # chance: how many values land in a random set of the same size and similar magnitudes
        R = np.random.default_rng(1)
        ctrl = []
        tl = sorted(targets)
        for _ in range(200):
            fake = {int(x * R.uniform(0.9, 1.1)) for x in tl}
            ctrl.append(sum(v in fake for v in vals))
        print(f"  {kind:6s}: {len(vals):5d} units, {len(hit)} sums equal a grid number/prime {sorted(set(hit))[:8]}; "
              f"random target sets give {np.mean(ctrl):.1f} ± {np.std(ctrl):.1f}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ok = verify()
    print()
    caption_tests()
    print()
    hill_tests()
    print()
    print("Gematria sums:")
    gematria_search()
