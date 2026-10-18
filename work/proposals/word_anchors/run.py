"""word_anchors gate: per-word anchor schedules into a key stream (16 schedules).

Run: python run.py   (Windows: run.bat)
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import common  # noqa: E402
from common import N, PRIME, ioc, encrypt_anti, decode_beam, totient_key, words_of, \
    print_verdict


def schedules(words):
    """16 anchor schedules as (name, anchor_fn) with anchor_fn(word_index, G, L)."""
    out = []
    L = 1009  # stream length for the gate (prime, to avoid trivially cycling anchors)
    G = [sum(PRIME[x] for x in w) for w, _ in words]
    out.append(("w mod L", lambda i: i % L))
    out.append(("G mod L", lambda i: G[i] % L))
    out.append(("3301*w mod L", lambda i: (3301 * i) % L))
    out.append(("w^2 mod L", lambda i: (i * i) % L))
    out.append(("1033*w+3301 mod L", lambda i: (1033 * i + 3301) % L))
    out.append(("G*w mod L", lambda i: (G[i] * i) % L))
    out.append(("G+w mod L", lambda i: (G[i] + i) % L))
    out.append(("G*3301 mod L", lambda i: (G[i] * 3301) % L))
    named = []
    for name, fn in out:
        named.append((name + " fwd", fn, +1))
        named.append((name + " back", fn, -1))
    return named


def key_array(words, key, anchor_fn, direction):
    """Per-position key values for a schedule (cycled stream, length 1009)."""
    L = 1009
    arr = []
    for i, (runes, _) in enumerate(words):
        a = anchor_fn(i)
        for j in range(len(runes)):
            arr.append(key[(a + direction * j) % L] % N)
    return arr


def main():
    print("=" * 72)
    print("word_anchors gate: per-word anchor schedules into a key stream (16)")
    print("=" * 72)
    rng = random.Random(20261017)
    words = common.cap_words(words_of(common.CORPUS_B))
    plain = [x for w, _ in words for x in w]
    key = totient_key(1009)  # fixed stream length
    scheds = schedules(words)

    plant = scheds[rng.randrange(len(scheds))]
    print("planted schedule: %s" % plant[0])
    pk = key_array(words, key, plant[1], plant[2])
    c = encrypt_anti(plain, pk, rng=rng)

    blind = decode_beam(c, key)
    ioc_blind = ioc(blind)
    print("blind decode (contiguous key):       IoC %.3f  (must be < 1.3)" % ioc_blind)

    results = []
    for name, fn, dr in scheds:
        arr = key_array(words, key, fn, dr)
        dec = decode_beam(c, arr)
        results.append((ioc(dec), name))
    results.sort(reverse=True)
    for v, nm in results[:5]:
        print("schedule scan: IoC %.3f  %s" % (v, nm))
    rank = [nm for _, nm in results].index(plant[0]) + 1
    print("planted schedule rank: %d of %d, IoC %.3f" % (rank, len(scheds), results[0][0]))

    null_max = 0.0
    for _ in range(5):
        arr = [key[rng.randrange(1009)] % N for _ in plain]
        null_max = max(null_max, ioc(decode_beam(c, arr)))
    print("null (random anchors, 5 draws):      max IoC %.3f  (must be < 1.5)" % null_max)

    ok = (ioc_blind < 1.3) and (rank == 1 and results[0][0] >= 1.5) and (null_max < 1.5)
    return print_verdict("word_anchors", ok,
                         "blind %.2f / planted rank %d IoC %.2f / null %.2f" %
                         (ioc_blind, rank, results[0][0], null_max))


if __name__ == "__main__":
    sys.exit(main())
