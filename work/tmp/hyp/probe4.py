"""Probe 4 (2026-10-17, laptop): missing-key-value test (keyless, any key offset).

H-MISS: the key never takes one value v mod 29. Every prime-based key does: p_n mod 29 is never 0 (n > 10),
phi(p_n) = p_n - 1 is never 28, p_n + b is never b. This holds at ANY offset n, so it covers prime and totient keys
far beyond the 20,000 values in the kscreen library (a key starting at the 10^9-th prime, say).
With c = D(p) + s*k and k uniform on the other 28 values,
    P(c) = (1 - f(D^-1(c - u))) / 28,   u = s*v,
so the rune D(x) + u is deficient in proportion to the plaintext frequency f(x). A matched filter over the 29 rune
counts tests each (u, D) for D = identity and Atbash (Cicada's alphabets; a mixed alphabet cannot be tested this way).
Controls: Emerson enciphered with phi(p_n) at a large offset (n from 10^6) under the skip rule (positive), and with a
uniform random key (null). Expected power for a pure key-without-v: z about 3.6 on 12,956 runes.
"""
import os
import random
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, WORK)
sys.path.insert(0, HERE)
import lp  # noqa: E402
from probe2 import text_runes  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
N = lp.N
LP2 = list(range(7, 16))


def english_freq():
    r = text_runes(os.path.join(WORK, "ref", "emerson_essays1.txt"))
    c = Counter(r)
    return [c[x] / len(r) for x in range(N)]


def matched(counts, f):
    """z for every (u, D): projection of observed deviations on the predicted deficit pattern."""
    n = sum(counts)
    out = []
    for dname, dinv in (("id", lambda y: y), ("atbash", lambda y: N - 1 - y)):
        for u in range(N):
            w = [-(f[dinv((c - u) % N)] - 1 / N) for c in range(N)]   # predicted direction of P(c) - 1/29
            num = sum((counts[c] - n / N) * w[c] for c in range(N))
            den = (sum((n / N) * w[c] ** 2 for c in range(N))) ** 0.5
            out.append((num / den, dname, u))
    return sorted(out, reverse=True)


def primes_from(n0, count):
    """count consecutive primes starting near the n0-th prime (approximate start via a segmented sieve)."""
    import math
    lo = int(n0 * (math.log(n0) + math.log(math.log(n0)) - 1))
    span = int(count * (math.log(lo) + 2)) + 1000
    seg = bytearray([1]) * span
    lim = int(math.isqrt(lo + span)) + 1
    small = bytearray([1]) * (lim + 1)
    small[0:2] = b"\x00\x00"
    for i in range(2, int(lim ** 0.5) + 1):
        if small[i]:
            small[i * i::i] = bytearray(len(small[i * i::i]))
    for p in range(2, lim + 1):
        if small[p]:
            st = max(p * p, (lo + p - 1) // p * p)
            seg[st - lo::p] = bytearray(len(seg[st - lo::p]))
    ps = [lo + i for i in range(span) if seg[i]]
    return ps[:count]


def encrypt(p, key, R, q=0.8, sign=1, atb=False):
    c, j = [], 0
    for x in p:
        x = N - 1 - x if atb else x
        y = (x + sign * key[j]) % N
        j += 1
        while c and y == c[-1] and R.random() < q:
            y = (x + sign * key[j]) % N
            j += 1
        c.append(y)
    return c


def main():
    f = english_freq()
    segs = lp.load_segments()
    lp2 = [x for i in LP2 for x in lp.runes_of(segs[i])]
    cnt = Counter(lp2)
    res = matched([cnt[x] for x in range(N)], f)
    print(f"LP2 ({len(lp2)} runes): top (z, D, u):", ", ".join(f"{z:+.2f} {d} u={u}" for z, d, u in res[:5]))
    print("   58 tests: the maximum of 58 normals is about +2.4 (90%: +2.9)")

    R = random.Random(29)
    emer = text_runes(os.path.join(WORK, "ref", "emerson_essays1.txt"))
    print("\ncontrols (12,956 runes of Emerson, skip rule q = 0.8):")
    ps = primes_from(10 ** 6, 3 * len(lp2) + 100)
    for trial in range(4):
        off = R.randrange(0, len(emer) - len(lp2))
        p = emer[off:off + len(lp2)]
        k0 = R.randrange(0, 1000)
        key = [(q - 1) % N for q in ps[k0:]]                  # phi(p_n): never 28
        sign = R.choice((1, -1))
        atb = R.random() < 0.5
        c = encrypt(p, key, R, sign=sign, atb=atb)
        cc = Counter(c)
        r = matched([cc[x] for x in range(N)], f)
        u_true = (sign * 28) % N
        d_true = "atbash" if atb else "id"
        rank = [(d, u) for _, d, u in r].index((d_true, u_true)) + 1
        z_true = [z for z, d, u in r if d == d_true and u == u_true][0]
        print(f"  plant phi(p_n), n ~ 10^6, sign {sign:+d}, {d_true:6s}: true (u={u_true}) z {z_true:+.2f} rank {rank}; "
              f"max {r[0][0]:+.2f}")
    nulls = []
    for trial in range(200):
        off = R.randrange(0, len(emer) - len(lp2))
        p = emer[off:off + len(lp2)]
        key = [R.randrange(N) for _ in range(3 * len(lp2))]
        c = encrypt(p, key, R)
        cc = Counter(c)
        nulls.append(matched([cc[x] for x in range(N)], f)[0][0])
    nulls.sort()
    print(f"  null (uniform random key), max z over 58 tests, 200 reps: median {nulls[100]:+.2f}, "
          f"95% {nulls[190]:+.2f}, max {nulls[-1]:+.2f}")

    # power: p_n + b at n ~ 10^7, random offset, shift, sign and alphabet
    R = random.Random(7)
    ps = primes_from(10 ** 7, 3 * len(lp2) + 60000)
    zs, ranks = [], []
    for trial in range(40):
        off = R.randrange(0, len(emer) - len(lp2))
        p = emer[off:off + len(lp2)]
        k0 = R.randrange(0, 50000)
        b = R.randrange(N)
        key = [(q + b) % N for q in ps[k0:]]
        sign = R.choice((1, -1))
        atb = R.random() < 0.5
        c = encrypt(p, key, R, sign=sign, atb=atb)
        cc = Counter(c)
        r = matched([cc[x] for x in range(N)], f)
        ut, dt = (sign * b) % N, ("atbash" if atb else "id")
        zs.append([z for z, d, u in r if d == dt and u == ut][0])
        ranks.append([(d, u) for _, d, u in r].index((dt, ut)) + 1)
    zs.sort()
    lp2max = res[0][0]
    print(f"  power, 40 plants of p_n + b (n ~ 10^7): true-cell z median {zs[20]:+.2f}, 10% {zs[4]:+.2f}, min {zs[0]:+.2f}; "
          f"rank 1 in {sum(r == 1 for r in ranks)}/40; plants with z <= LP2's maximum ({lp2max:+.2f}): "
          f"{sum(z <= lp2max for z in zs)}/40")


if __name__ == "__main__":
    main()
