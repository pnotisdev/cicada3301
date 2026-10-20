"""Phase 22b: a book running key under an ADVERSARIALLY chosen letter->rune table, seen through rune pairs.

book_key_flatness.py shows that a table tuned to flatten the unigrams leaves only ~+2.4 sd at LP2's length. A running
key also leaks through the joint distribution of (c_i, c_(i+d)): it is the 2-D circular convolution of the plaintext's
and the key's lag-d pair distributions, and one table has to flatten both coordinates at once.

Statistic: S = sum over d = 2..DMAX of chi^2 of the 841 lag-d pair counts against uniform (lag 1 is left out because
the anti-repeat rule shapes it). Null: uniform key + skip rule (q = 0.81). Plants: book keys under (a) the unigram-
flattest table and (b) a table searched to minimise the predicted pair excess itself (heuristic adversary).
Usage: python work/book_key_pairs.py [book.txt ...]   (default: the KJV Bible and Paradise Lost)
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lp  # noqa: E402
from book_key_flatness import HERE, N, dist, encrypt_skip, flattest_table, gutenberg_body, to_runes  # noqa: E402

DMAX = 8
LAGS = range(2, DMAX + 1)


def pair_dist(x, d):
    h = np.bincount((x[:-d] % N) * N + x[d:] % N, minlength=N * N).reshape(N, N)
    return h / h.sum()


def stat(c):
    n = len(c)
    s = 0.0
    for d in LAGS:
        h = np.bincount(c[:-d] * N + c[d:], minlength=N * N)
        e = (n - d) / (N * N)
        s += float(((h - e) ** 2 / e).sum())
    return s


def pair_excess(Fp, K2, pi):
    """Predicted sum over lags of (N^2 * sum q^2 - 1) for the ciphertext pair distributions under table pi."""
    tot = 0.0
    for F, k in zip(Fp, K2):
        Kp = k[np.ix_(pi, pi)]
        tot += float((F * np.abs(np.fft.fft2(Kp)) ** 2).sum()) - 1.0
    return tot


def pair_table(P, K, rng, restarts=6):
    Fp = [np.abs(np.fft.fft2(pair_dist(P, d))) ** 2 for d in LAGS]
    K2 = [pair_dist(K, d) for d in LAGS]
    best, best_pi = np.inf, None
    for _ in range(restarts):
        pi = rng.permutation(N)
        cur = pair_excess(Fp, K2, pi)
        improved = True
        while improved:
            improved = False
            for a in range(N):
                for b in range(a + 1, N):
                    pi[a], pi[b] = pi[b], pi[a]
                    v = pair_excess(Fp, K2, pi)
                    if v < cur - 1e-12:
                        cur, improved = v, True
                    else:
                        pi[a], pi[b] = pi[b], pi[a]
        if cur < best:
            best, best_pi = cur, pi.copy()
    return best, best_pi


def main(paths):
    rng = np.random.default_rng(29)
    segs = lp.load_segments()
    lp2 = np.array([r for s in segs[7:16] for r in lp.runes_of(s)])
    n = len(lp2)
    P = to_runes(open(os.path.join(HERE, "ref", "emerson_essays1.txt"), encoding="utf-8", errors="ignore").read())

    def plant(K, inv):
        o = rng.integers(0, len(K) - 2 * n - 200)
        po = rng.integers(0, len(P) - n - 1)
        return stat(encrypt_skip(P[po:po + n], inv[K[o:]], rng))

    null = np.array([stat(encrypt_skip(P[o:o + n], rng.integers(0, N, 2 * n + 100), rng))
                     for o in rng.integers(0, len(P) - n - 1, 100)])
    mu, sd = null.mean(), null.std(ddof=1)
    s_lp2 = stat(lp2)
    print(f"S = sum_d=2..{DMAX} chi^2(lag-d pairs, 840 df each), n = {n}")
    print(f"NULL uniform key + skip (100): {mu:.1f} +- {sd:.1f}, max {null.max():.1f};  LP2 {s_lp2:.1f} (z {(s_lp2 - mu) / sd:+.2f})")

    for path in paths:
        K = to_runes(gutenberg_body(path))
        name = os.path.basename(path)
        _, pi1 = flattest_table(dist(P), dist(K), rng, restarts=20)
        ex2, pi2 = pair_table(P, K, rng)
        for label, pi in (("unigram-flattest table", pi1), ("pair-flattest table", pi2)):
            inv = np.argsort(pi)
            s = np.array([plant(K, inv) for _ in range(30)])
            ioc1 = lp.ioc(list(encrypt_skip(P[:n], inv[K[1000:]], rng)))
            print(f"{name:12s} {label:24s}: S {s.mean():.1f} +- {s.std(ddof=1):.1f}, min {s.min():.1f} "
                  f"(z of min {(s.min() - mu) / sd:+.1f}); {int((s > null.max()).sum())}/30 above the null max; "
                  f"unigram IoC of one plant {ioc1:.4f}")
        print(f"{'':12s} pair-table predicted excess {ex2:.4f} (summed over lags)", flush=True)


if __name__ == "__main__":
    c = os.path.join(HERE, "ref", "corpora")
    main(sys.argv[1:] or [os.path.join(c, "pg10.txt"), os.path.join(c, "pg26.txt")])
