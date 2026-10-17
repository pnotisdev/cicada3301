"""Does the KEY obey a sparse linear recurrence?  k_i = a k_(i-d1) + b k_(i-d2) + beta  (mod 29), taps at two distances d1 < d2 (a LFSR / lagged-Fibonacci key with sparse taps).

If c_i = p_i + k_i (the skip rule moves the key pointer now and then), then r_i = c_i - a c_(i-d1) - b c_(i-d2) = (p_i - a p_(i-d1) - b p_(i-d2)) + beta: the key cancels and what is left is a mix of
three plaintext letters, whose distribution is peaked (English), whereas for the wrong (a, b) or a key without that recurrence r is uniform. The statistic is the index of coincidence of r
(shift invariant, so beta is free). The earlier recurrence screens (kscreen-recurrences) covered orders up to 3 (contiguous taps) by decoding; the taps of the two within-word effects of LP2 are
at distance 5 (equality) and 6 (c' = 24 - 2c), which a contiguous order-3 recurrence does not reach.

Pre-specified family: every tap pair 1 <= d1 < d2 <= 12 (66 pairs) and every (a, b) in Z29 x Z29 except (0, 0) (840): 55,440 forms (those with a = 0 or b = 0 are the two-term relations). Two position sets:
(A) all positions of a section, (B) positions whose taps lie inside the same word. z = (IoC - 1) / sd, the null being the same scan on 40 shuffles of LP2's runes inside sections (the maximum over all forms).
Control: English plaintext (the LP2 section structure) under a key with a planted recurrence and the skip rule (restart of the alphabet pointer at a collision, 81% of the time): the planted (a, b) must come out first.

    python work/families/tap_recurrence.py          # -> results/analysis/tap_recurrence.txt
"""
import os
import sys
import time

import numpy as np

import fam_data as D

HERE = os.path.dirname(os.path.abspath(__file__))
N = D.N
OUT = []
TAPS = [(d1, d2) for d1 in range(1, 13) for d2 in range(d1 + 1, 13)]


def say(s=""):
    print(s)
    OUT.append(s)


def scan(C, start, sid, within):
    """IoC of the residual for every tap pair and (a, b): array (len(TAPS), 29, 29); (0, 0) is left at 1.0"""
    wid = np.cumsum(start)
    res = np.ones((len(TAPS), N, N))
    for t, (d1, d2) in enumerate(TAPS):
        v = sid[d2:] == sid[:-d2]
        if within:
            v &= wid[d2:] == wid[:-d2]
        z, x, y = C[d2:][v], C[d2 - d1:-d1][v], C[:-d2][v]
        n = len(z)
        if n < 200:
            continue
        for a in range(N):
            za = (z - a * x) % N
            for b in range(N):
                if a == 0 and b == 0:
                    continue
                h = np.bincount((za - b * y) % N, minlength=N)
                res[t, a, b] = (h * (h - 1)).sum() / (n * (n - 1) / N)
    return res


def zscores(res, within, C, start, sid):
    """z of each form from the analytic sd of the IoC of n uniform draws (the shuffles check the maximum)"""
    wid = np.cumsum(start)
    z = np.zeros_like(res)
    for t, (d1, d2) in enumerate(TAPS):
        v = sid[d2:] == sid[:-d2]
        if within:
            v &= wid[d2:] == wid[:-d2]
        n = int(v.sum())
        sd = np.sqrt(2.0 * (N - 1)) / n if n > 1 else 1.0          # sd of the normalised IoC of n uniform runes (chi-square with N - 1 df, divided by n): 0.0006 at n = 12,956
        z[t] = (res[t] - 1.0) / sd
    return z


def planted(rng, runes, start, sid, d1, d2, a, b, q=0.81):
    """English under c_i = p_i + k_j with k obeying k_j = a k_(j-d1) + b k_(j-d2) + 7 and the skip rule (the pointer j advances at a collision with probability q)"""
    eng = D.english(120_000)
    P, st = D.windows(eng, len(runes), 1, rng, False, start, np.append(True, sid[1:] != sid[:-1]))
    P = P[0]
    k = list(rng.integers(0, N, d2))
    while len(k) < 3 * len(runes):
        k.append((a * k[-d1] + b * k[-d2] + 7) % N)
    k = np.array(k)
    c, j = np.empty(len(P), int), 0
    for i, p in enumerate(P):
        y = (p + k[j]) % N
        j += 1
        if i and y == c[i - 1] and rng.random() < q:
            y = (p + k[j]) % N
            j += 1
        c[i] = y
    return c


def main():
    runes, start, sid = D.lp2()
    rng = np.random.default_rng(5)
    for within in (False, True):
        t0 = time.time()
        res = scan(runes, start, sid, within)
        z = zscores(res, within, runes, start, sid)
        flat = np.dstack(np.unravel_index(np.argsort(-z, axis=None), z.shape))[0][:4]
        null = []
        for _ in range(40):
            Cp = runes.copy()
            for k in np.unique(sid):
                m = sid == k
                Cp[m] = rng.permutation(Cp[m])
            null.append(zscores(scan(Cp, start, sid, within), within, Cp, start, sid).max())
        null = np.array(null)
        top = z.max()
        say(f"positions {'inside one word' if within else 'anywhere in a section'}: best of {len(TAPS) * 840:,} forms z {top:+.2f}; shuffle null of the best: median {np.median(null):+.2f}, max {null.max():+.2f}, "
            f"P(null best >= observed) = {(null >= top).mean():.2f}  ({time.time() - t0:.0f} s)")
        say("   top forms: " + "; ".join(f"taps {TAPS[t]} a={a} b={b} (IoC {res[t, a, b]:.3f}, z {z[t, a, b]:+.1f})" for t, a, b in flat))
        # the two-term forms of the within-word effects, for reference
        t5 = TAPS.index((5, 6))
        say(f"   taps (5, 6): a = 1, b = 0 (lag-5 equality) IoC {res[t5, 1, 0]:.3f} z {z[t5, 1, 0]:+.1f}; a = 0, b = -2 (lag-6 relation) IoC {res[t5, 0, N - 2]:.3f} z {z[t5, 0, N - 2]:+.1f}")
    say("")
    say("control (a planted recurrence, English plaintext with LP2's section structure, skip rule): z of the planted form and its rank among all forms; null max of the real scan above")
    for (d1, d2, a, b) in ((5, 6, 3, 2), (2, 7, 5, 1), (4, 9, 1, 1), (5, 6, 1, 0)):
        c = planted(rng, runes, start, sid, d1, d2, a, b)
        res = scan(c, start, sid, False)
        z = zscores(res, False, c, start, sid)
        t = TAPS.index((d1, d2))
        rank = int((z > z[t, a, b]).sum()) + 1
        say(f"   taps ({d1}, {d2}) a={a} b={b}: planted z {z[t, a, b]:+.1f} (IoC {res[t, a, b]:.3f}), rank {rank} of {len(TAPS) * 840:,}; best other form z {np.sort(z.ravel())[-2 if rank == 1 else -1]:+.1f}")
    dest = os.path.join(HERE, "..", "..", "results", "analysis")
    with open(os.path.join(dest, "tap_recurrence.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    sys.exit(main())
