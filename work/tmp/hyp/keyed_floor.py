"""Can a keyed alphabet escape the doublet floor? (follow-up to notebook_checks.py, section 3)

With c = s(p) + k, s an arbitrary rune permutation (keyed alphabet) and key increments independent of the text, the lag-1
ciphertext difference histogram is r = p_s (*) q: the plaintext increment distribution under s, circularly convolved with
the key-increment distribution q. For the standard order p_s has min 1.6% (floor 207 doublets); a keyed alphabet can push
one difference bin down to 0.15% (the cheapest 29-cycle of English bigrams), so the floor alone does not exclude it.
LP2 also needs the other 28 bins flat. This searches alphabets s (swap hill-climbing, restarts) and, for each, the best
q >= 0 (weighted NNLS on Neyman chi-square over the 29 bins). It is a search, not a proof.

Controls: planted family members (English window, random s, random sparse q, key = random walk with steps ~ q) must be
fitted to chi-square ~ 28; collision-rule texts (English + uniform key + 81% repeat re-draw, the model that matches LP2)
are run through the same search; then LP2.

    python work/tmp/hyp/keyed_floor.py   -> appended to results/analysis/cicadanotebook_checks_2026-10-17.txt
"""
import glob
import os
import sys

import numpy as np
from scipy.optimize import nnls

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import notebook_checks as nc  # noqa: E402

N = 29
IDX = (np.arange(N)[:, None] - np.arange(N)[None, :]) % N      # A[d, j] = p((d - j) mod N)
RNG = np.random.default_rng(29)


def bigrams(p):
    B = np.zeros((N, N))
    np.add.at(B, (p[:-1], p[1:]), 1)
    return B / B.sum()


def p_sigma(B, s):
    D = (s[None, :] - s[:, None]) % N
    return np.bincount(D.ravel(), weights=B.ravel(), minlength=N)


def fit(B, s, h):
    """(chi-square, q) of the best q >= 0, sum 1, for the histogram h under alphabet s"""
    T = h.sum()
    A = p_sigma(B, s)[IDX]
    w = T / np.sqrt(np.maximum(h, 1))
    M = np.vstack([A * w[:, None], 1e4 * np.ones(N)])
    b = np.concatenate([np.sqrt(np.maximum(h, 1)), [1e4]])
    q, res = nnls(M, b)
    return res ** 2, q


def search(B, h, restarts=12, starts=()):
    best = (np.inf, None, None)
    inits = [np.array(x) for x in starts] + [RNG.permutation(N) for _ in range(restarts)]
    for s in inits:
        cur, q = fit(B, s, h)
        improved = True
        while improved:
            improved = False
            for i in range(N):
                for j in range(i + 1, N):
                    t = s.copy()
                    t[i], t[j] = t[j], t[i]
                    c, qq = fit(B, t, h)
                    if c < cur - 1e-9:
                        s, cur, q, improved = t, c, qq, True
        if cur < best[0]:
            best = (cur, s.copy(), q)
    return best


def hist(streams):
    h = np.zeros(N)
    for c in streams:
        h += np.bincount((c[1:] - c[:-1]) % N, minlength=N)
    return h


def encrypt_walk(p, s, q):
    steps = RNG.choice(N, size=len(p), p=q)
    k = np.cumsum(steps) % N
    return (s[p] + k) % N


def encrypt_collision(p, rate=0.81):
    c = np.empty(len(p), dtype=np.int64)
    prev = -1
    for i, x in enumerate(p):
        y = (x + RNG.integers(N)) % N
        while y == prev and RNG.random() < rate:
            y = (x + RNG.integers(N)) % N
        c[i] = prev = y
    return c


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    eng = []
    for path in sorted(glob.glob(os.path.join(nc.WORK, "ref", "corpora", "pg*.txt"))):
        lang, r = nc.corpus(path)
        if lang == "English":
            eng.append(r)
    pooled = np.concatenate(eng)
    B = bigrams(pooled)
    lens = [len(nc.section(i)) for i in nc.LP2]
    L = sum(lens)
    lines = ["", "== 3b. Keyed alphabets: c = s(p) + k with key increments independent of the text (keyed_floor.py)"]

    def say(x):
        print(x)
        lines.append(x)

    ident = np.arange(N)
    real = hist([nc.section(i) for i in nc.LP2])
    c0, _ = fit(B, ident, real)
    say(f"   standard order, best q: chi-square {c0:.1f} on 29 bins (LP2 h[0] = {real[0]:.0f})")
    for t in range(3):
        off = int(RNG.integers(0, len(pooled) - L))
        p = pooled[off:off + L]
        s = RNG.permutation(N)
        q = np.zeros(N)
        sup = RNG.choice(N, size=int(RNG.integers(3, 8)), replace=False)
        q[sup] = RNG.random(len(sup))
        q /= q.sum()
        h = hist([encrypt_walk(p, s, q)])
        truth, _ = fit(B, s, h)
        found, _, _ = search(B, h)
        say(f"   planted family member {t + 1}: doublets {h[0]:.0f}; chi-square at the planted alphabet {truth:.1f}, "
            f"found by the search {found:.1f}")
    for t in range(2):
        off = int(RNG.integers(0, len(pooled) - L))
        h = hist([encrypt_collision(pooled[off:off + L])])
        found, _, q = search(B, h)
        say(f"   collision-rule text {t + 1} (81% re-draw): doublets {h[0]:.0f}; best keyed-alphabet fit chi-square {found:.1f}")
    found, s, q = search(B, real, restarts=24)
    r = nc.lp.LATIN
    order = sorted(range(N), key=lambda a: s[a])
    say(f"   LP2: best keyed-alphabet fit chi-square {found:.1f} on 29 bins; alphabet {' '.join(r[a] for a in order)}; "
        f"model doublets {real.sum() * (p_sigma(B, s)[IDX] @ q)[0]:.1f}")
    with open(nc.OUT, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
