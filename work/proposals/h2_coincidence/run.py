"""h2_coincidence gate: tableau-invariant coincidence statistic (H2 screen).

Run: python run.py   (Windows: run.bat)
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import common  # noqa: E402
from common import N, ioc, decode_beam, totient_key, to_runes, print_verdict


def coincidence(c, k):
    """# pairs i < i' with k_i == k_i' and c_i == c_i'. O(n^2), n <= ~2000."""
    n = len(c)
    cnt = 0
    for i in range(n):
        ki = k[i]
        ci = c[i]
        for j in range(i + 1, n):
            if k[j] == ki and c[j] == ci:
                cnt += 1
    return cnt


def z_of(v, nulls):
    mu = sum(nulls) / len(nulls)
    var = sum((x - mu) ** 2 for x in nulls) / max(1, len(nulls) - 1)
    return (v - mu) / (var ** 0.5) if var > 0 else 0.0


def main():
    print("=" * 72)
    print("h2_coincidence gate: tableau-invariant statistic (H2)")
    print("=" * 72)
    rng = random.Random(20261017)
    plain = to_runes(common.CORPUS_A + " " + common.CORPUS_B)[:1600]
    n = len(plain)
    key = totient_key(n)

    # Plant: random tableau T[k] = permutation of 0..28 per key class.
    T = [list(range(N)) for _ in range(N)]
    for row in T:
        rng.shuffle(row)
    c = [T[key[i]][plain[i]] for i in range(n)]

    # 1. statistic at the true offset vs random offsets of the same stream.
    true = coincidence(c, key)
    offs = []
    for _ in range(20):
        d = rng.randrange(1, n)
        offs.append(coincidence(c, key[d:] + key[:d]))
    z_off = z_of(true, offs)
    print("coincidence at true offset: %d  vs null offsets mean %.1f sd %.1f -> z %.1f (need >= 5)"
          % (true, sum(offs) / len(offs), (sum((x - sum(offs) / len(offs)) ** 2
             for x in offs) / (len(offs) - 1)) ** 0.5, z_off))

    # 2. shuffled ciphertext at the true offset.
    sh = []
    for _ in range(20):
        cs = c[:]
        rng.shuffle(cs)
        sh.append(coincidence(cs, key))
    z_sh = z_of(true, sh)
    print("shuffled-ciphertext null: mean %.1f sd %.1f -> z %.1f (need >= 5)"
          % (sum(sh) / len(sh), (sum((x - sum(sh) / len(sh)) ** 2 for x in sh) / (len(sh) - 1)) ** 0.5, z_sh))

    # 3. blindness: additive decode must stay flat.
    dec = decode_beam(c, key)
    print("additive decode on the plant: IoC %.3f  (must be < 1.3: kscreen is blind here)" % ioc(dec))

    # 4. informational: LP2 segment 0.7 with the totient stream at offset 0.
    segs = common.lp.load_segments()
    runes = [t for t in segs[7] if isinstance(t, int)][:1600]
    lp2_z = z_of(coincidence(runes, key[:len(runes)]),
                 [coincidence(runes, key[d:d + len(runes)]) for d in range(20, 40)])
    print("LP2 0.7, totient at offset 0: z %.1f (informational only; the campaign scans the library)" % lp2_z)

    ok = (z_off >= 5) and (z_sh >= 5) and (ioc(dec) < 1.3)
    return print_verdict("h2_coincidence", ok,
                         "z_off %.1f / z_sh %.1f / blind IoC %.2f" % (z_off, z_sh, ioc(dec)))


if __name__ == "__main__":
    sys.exit(main())
