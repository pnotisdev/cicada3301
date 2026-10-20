"""Phase 22: can ANY book (any language, any letter->rune mapping, any multiplier or sign) be LP2's running key?

Keyless test. For c = p + m*k (mod 29) the ciphertext unigram distribution is the circular convolution of the
plaintext distribution P with the key distribution K, so

    29 * sum_c (P*K)(c)^2 = 1 + sum_{f != 0} |P^(f)|^2 |K^(f)|^2      (P^, K^ = DFT over Z_29)

and, for EVERY relabelling of the key alphabet (any letter->rune table, multiplier m, sign),

    IoC_c - 1 >= min_{f != 0} |P^(f)|^2 * (29 * sum K^2 - 1) = min|P^|^2 * (IoC_k - 1).

The bound depends on the key only through its own IoC, which no relabelling changes. If even the bound sits
many null sd above LP2's IoC, every letter-wise book key is excluded, whatever book it is.

Controls: running-key encryptions WITH the anti-repeat skip rule (q = 0.81, as the repo's sim.py) at LP2's length
(positive), and uniform random keys with the same rule (null). Usage: python work/book_key_flatness.py
"""
import glob
import os
import re
import sys
import unicodedata

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lp  # noqa: E402

N = lp.N
HERE = os.path.dirname(os.path.abspath(__file__))
DIGRAPHS = ("TH", "EO", "NG", "OE", "AE", "IA", "EA", "ING")
ALIAS = {"V": 1, "K": 5, "Z": 15, "Q": 5}      # as work/prime_sums.py (the solved pages' spelling)


def to_runes(text, letters=False):
    """Latin-script text -> GP indices; digraph runes greedy (TH, ING, EA, ...) unless letters=True."""
    text = unicodedata.normalize("NFKD", text)
    w = re.sub(r"[^A-Za-z ]", " ", "".join(ch for ch in text if not unicodedata.combining(ch)))
    w = w.upper().replace("QU", "CW")
    order = sorted(range(N), key=lambda i: -len(lp.LATIN[i]))
    if letters:
        order = [i for i in order if len(lp.LATIN[i]) == 1]
    out = []
    for word in w.split():
        while word:
            for i in order:
                if word.startswith(lp.LATIN[i]):
                    out.append(i)
                    word = word[len(lp.LATIN[i]):]
                    break
            else:
                out.append(ALIAS.get(word[0], 0))
                word = word[1:]
    return np.array(out, dtype=np.int64)


def gutenberg_body(path):
    t = open(path, encoding="utf-8", errors="ignore").read()
    a, b = t.find("*** START"), t.find("*** END")
    return t[t.find("\n", a) + 1:b] if a >= 0 and b > a else t


def dist(x):
    return np.bincount(x % N, minlength=N) / len(x)


def ioc_dist(h):
    return float(N * (h ** 2).sum())


def ioc_runes(x):
    return lp.ioc(list(x))


def flattest_table(P, K, rng, restarts=40):
    """Search the letter->rune table (a permutation of the key's 29 values) that makes P*K flattest.

    Swap hill-climbing from random starts: a heuristic upper bound on the true minimum, not a proof."""
    Fp = np.abs(np.fft.fft(P)) ** 2
    best, best_pi = np.inf, None
    for _ in range(restarts):
        pi = rng.permutation(N)
        cur = float((Fp * np.abs(np.fft.fft(K[pi])) ** 2).sum())
        improved = True
        while improved:
            improved = False
            for a in range(N):
                for b in range(a + 1, N):
                    pi[a], pi[b] = pi[b], pi[a]
                    v = float((Fp * np.abs(np.fft.fft(K[pi])) ** 2).sum())
                    if v < cur - 1e-15:
                        cur, improved = v, True
                    else:
                        pi[a], pi[b] = pi[b], pi[a]
        if cur < best:
            best, best_pi = cur, pi.copy()
    return best, best_pi     # best = 29 * sum (P*K_pi)^2 = predicted ciphertext IoC; K_pi = K[pi]


def encrypt_skip(p, k, rng, q=0.81, m=1):
    """c_i = p_i + m*k_j; if c_i == c_(i-1), with prob. q take the next key value (repeat while it collides)."""
    c = np.empty(len(p), dtype=np.int64)
    j, prev = 0, -1
    for i, pi in enumerate(p):
        ci = (pi + m * k[j]) % N
        while ci == prev and rng.random() < q:
            j += 1
            ci = (pi + m * k[j]) % N
        c[i], prev, j = ci, ci, j + 1
    return c


def main():
    rng = np.random.default_rng(3301)
    segs = lp.load_segments()
    lp2 = np.array([r for s in segs[7:16] for r in lp.runes_of(s)])
    sec = [np.array(lp.runes_of(s)) for s in segs[7:16]]
    n = len(lp2)
    print(f"LP2: {n} runes (sections 0.7-0.15), IoC {ioc_runes(lp2):.5f}")
    assert n == 12956, n

    # plaintext models: solved-pages spelling of Emerson (digraph runes) and the same letter by letter
    em = open(os.path.join(HERE, "ref", "emerson_essays1.txt"), encoding="utf-8", errors="ignore").read()
    Pd, Pl = to_runes(em), to_runes(em, letters=True)
    print(f"plaintext pools: Emerson digraph {len(Pd)} runes IoC {ioc_runes(Pd):.3f}; "
          f"letter-spelled {len(Pl)} IoC {ioc_runes(Pl):.3f}")

    def minP(P):
        F = np.abs(np.fft.fft(dist(P))) ** 2
        return float(F[1:].min()), int(np.argmin(F[1:]) + 1)

    for name, P in (("digraph", Pd), ("letters", Pl)):
        mp, f = minP(P)
        print(f"  min_f |P^(f)|^2 over f != 0, {name}: {mp:.5f} (f = {f})")

    # null sd of LP2-length IoC (uniform random key, skip rule) and of each section
    def sim_ioc(P, key_fn, length, reps):
        out = []
        for _ in range(reps):
            o = rng.integers(0, len(P) - length - 1)
            out.append(ioc_runes(encrypt_skip(P[o:o + length], key_fn(length), rng)))
        return np.array(out)

    uni = lambda L: rng.integers(0, N, 2 * L + 100)  # noqa: E731
    null = sim_ioc(Pd, uni, n, 200)
    mu, sd = null.mean(), null.std(ddof=1)
    print(f"\nNULL (uniform key, skip q=0.81, n={n}, 200 reps): IoC {mu:.5f} +- {sd:.5f}, "
          f"max {null.max():.5f}; LP2 z = {(ioc_runes(lp2) - mu) / sd:+.2f}")

    # books as keys
    books = sorted(glob.glob(os.path.join(HERE, "ref", "corpora", "*.txt")))
    print(f"\n{'key text':46s} {'IoC_k':>6s} {'pred GP':>8s} {'sim mean':>9s} {'sim min':>8s} {'sim z min':>9s}"
          f" {'Fourier bound':>13s} {'flattest table':>14s} {'z':>6s}")
    rows = []
    for path in books + [os.path.join(HERE, "ref", "emerson_essays1.txt")]:
        raw = open(path, encoding="utf-8", errors="ignore").read()
        title = (re.search(r"Title:\s*(.+)", raw) or re.search(r"(.{0,40})", raw)).group(1).strip()[:36]
        for letters in (False, True):
            K = to_runes(gutenberg_body(path), letters=letters)
            ik = ioc_dist(dist(K))
            # positive control: real running-key encryptions with the skip rule, GP table, four multipliers
            sims = []
            for m in (1, 28, 3, 17):
                for _ in range(5):
                    o = rng.integers(0, len(K) - 2 * n - 200)
                    po = rng.integers(0, len(Pd) - n - 1)
                    sims.append(ioc_runes(encrypt_skip(Pd[po:po + n], K[o:], rng, m=m)))
            pred = ioc_dist(np.real(np.fft.ifft(np.fft.fft(dist(Pd)) * np.fft.fft(dist(K)))))
            for pname, P in (("digraph", Pd), ("letters", Pl)):
                flat, pi = flattest_table(dist(P), dist(K), rng)
                rows.append((title, letters, pname, flat, pi, K))
            fl = min(rows[-2:], key=lambda r: r[3])
            title_s = f"{title} ({'letters' if letters else 'digraph'})"
            print(f"{title_s:46s} {ik:6.3f} {pred:8.4f} {np.mean(sims):9.4f} {np.min(sims):8.4f} "
                  f"{(np.min(sims) - mu) / sd:+9.1f} {1 + minP(Pd)[0] * (ik - 1):13.5f} {fl[3]:14.5f} "
                  f"{(fl[3] - mu) / sd:+6.1f}", flush=True)

    worst = min(rows, key=lambda r: r[3])
    title, letters, pname, flat, pi, K = worst
    print(f"\nFLATTEST over all books, key spellings, plaintext spellings and tables: predicted IoC {flat:.5f} "
          f"({title}, key {'letters' if letters else 'digraph'}, plaintext {pname}) = {(flat - mu) / sd:+.1f} null sd; "
          f"LP2 {(ioc_runes(lp2) - mu) / sd:+.2f}")
    print(f"  table (rune value r <- key symbol pi[r]): {pi.tolist()}")

    # positive control AT that table, with the skip rule: does the predicted excess survive real encryption?
    inv = np.argsort(pi)
    P = Pd if pname == "digraph" else Pl
    sims = []
    for _ in range(40):
        o = rng.integers(0, len(K) - 2 * n - 200)
        po = rng.integers(0, len(P) - n - 1)
        sims.append(ioc_runes(encrypt_skip(P[po:po + n], inv[K[o:]], rng)))
    sims = np.array(sims)
    print(f"  plants at that table (40, skip q=0.81, n={n}): IoC {sims.mean():.5f} +- {sims.std(ddof=1):.5f}, "
          f"min {sims.min():.5f}; {int((sims > null.max()).sum())}/40 above the null maximum {null.max():.5f}; "
          f"LP2 {ioc_runes(lp2):.5f}")

    # per section: the flattest table's excess against each section's own null sd
    print("\nper section (flattest table's predicted IoC, z against a uniform-key null of that length):")
    for i, s in enumerate(sec):
        ns = sim_ioc(Pd, uni, len(s), 200)
        print(f"  0.{i + 7:<3d} {len(s):5d} runes  IoC {ioc_runes(s):.4f}  null {ns.mean():.4f} +- {ns.std(ddof=1):.4f}"
              f"  flattest-table z {(flat - ns.mean()) / ns.std(ddof=1):+.1f}  LP2 z {(ioc_runes(s) - ns.mean()) / ns.std(ddof=1):+.2f}")


if __name__ == "__main__":
    main()
