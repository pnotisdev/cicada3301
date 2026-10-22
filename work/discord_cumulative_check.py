"""Two Discord proposals (CicadaSolvers, 2026-10-22) checked against LP2.

    python work/discord_cumulative_check.py

(1) avaster's "circumference" cipher: c[i] = c[i-1] + a[i] * (p[i] - 21) mod 29, a[i] = prime[s+i] (or prime-1) mod 29,
    0 -> 1. A doublet c[i] = c[i-1] happens exactly when p[i] = 21 (the NG rune), whatever the key. Two tests:
    (a) structural: doublets would sit only where the plaintext has NG, which almost never starts a word, so LP2's
        doublets across word gaps should be about zero; compare the solved plaintext's NG rate and position;
    (b) direct: decrypt every LP2 section with the prime and totient streams at offsets 0..OFFSETS-1 (the shift 21
        does not change the IoC), with a planted control and a random-multiplier null.
(2) DCPH's "book key + skip on doublet with probability 0.78" is the skip/coin model of phase 25 with a book running
    key, already excluded by flatness (registry rows obs-flat, book-running-key, mech25); not re-run here.
"""
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lp  # noqa: E402

M, NG, OFFSETS, W = 29, 21, 20000, 300
LP2 = range(7, 16)
SOLVED = [0, 1, 2, 3, 4, 5, 6, 16, 17]


def words(toks):
    # bare line ('\n') and page ('%') breaks fall inside words in LP; only word / clause / paragraph marks and numerals cut
    w, cur = [], []
    for t in toks:
        if isinstance(t, int):
            cur.append(t)
        elif t in ("\n", "%"):
            continue
        elif cur:
            w.append(cur)
            cur = []
    return w + ([cur] if cur else [])


def doublets(toks):
    inside = gap = 0
    for wd_prev, wd in zip([None] + words(toks), words(toks)):
        inside += sum(a == b for a, b in zip(wd, wd[1:]))
        gap += wd_prev is not None and wd_prev[-1] == wd[0]
    return inside, gap


def ioc_rows(p):  # IoC of every row of an int array, normalised like lp.ioc
    n = p.shape[1]
    cnt = np.stack([(p == k).sum(1) for k in range(M)], 1)
    return (cnt * (cnt - 1)).sum(1) / (n * (n - 1) / M)


PR = np.array(lp.primes(OFFSETS + W + 10)[:OFFSETS + W + 10])
INV = np.array([0] + [pow(a, -1, M) for a in range(1, M)])


def scan(c, stream):
    """best IoC over offsets: p = (c[i]-c[i-1]) * inv(a[s+i])"""
    c = np.array(c[:W])
    d = (c - np.concatenate([[0], c[:-1]])) % M
    idx = np.arange(OFFSETS)[:, None] + np.arange(len(c))[None, :]
    a = stream[idx] % M
    a[a == 0] = 1
    io = ioc_rows((d[None, :] * INV[a]) % M)
    return io.max(), int(io.argmax())


def encrypt(p, stream, s):
    prev, out = 0, []
    for i, x in enumerate(p):
        a = int(stream[s + i]) % M or 1
        prev = (prev + a * (x - NG)) % M
        out.append(prev)
    return out


if __name__ == "__main__":
    segs = lp.load_segments()
    print("(a) doublets inside words / across word gaps")
    for name, ids in (("LP2 ciphertext", LP2),):
        ins = sum(doublets(segs[i])[0] for i in ids)
        gp = sum(doublets(segs[i])[1] for i in ids)
        print(f"  {name}: {ins} inside, {gp} across gaps")
    plain = []
    for i in SOLVED:
        try:
            plain.append([x for x in lp.KNOWN[i][1](lp.runes_of(segs[i])) if isinstance(x, int)])
        except Exception:
            pass
    ng = [sum(x == NG for x in p) for p in plain]
    tot = sum(len(p) for p in plain)
    print(f"  solved plaintext: NG rate {sum(ng) / tot:.4f} ({sum(ng)}/{tot}); avaster's cipher puts every doublet on a "
          f"plaintext NG, so its doublet rate equals that rate")
    print("(b) direct decryption, best IoC over offsets 0..%d on the first %d runes" % (OFFSETS - 1, W))
    rng = random.Random(3301)
    english = [x for p in plain for x in p]
    for name, stream in (("prime", PR), ("totient", PR - 1)):
        ct = encrypt(english[:W], stream, 1234)
        bc, oc = scan(ct, stream)
        print(f"  {name}: planted control best {bc:.3f} at offset {oc} (truth 1234)")
        null = max(scan(ct, np.array([rng.randrange(1, M) for _ in range(OFFSETS + W + 10)]))[0] for _ in range(3))
        best = max((scan(lp.runes_of(segs[i]), stream) + (i,) for i in LP2 if len(lp.runes_of(segs[i])) >= W))
        print(f"  {name}: LP2 best {best[0]:.3f} (section index {best[2]}, offset {best[1]}); "
              f"random-multiplier null on the control text {null:.3f}; screen line 1.40")
