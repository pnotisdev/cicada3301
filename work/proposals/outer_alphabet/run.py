"""outer_alphabet gate: keyword-mixed outer alphabet around an additive key.

Run: python run.py   (Windows: run.bat)
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import common  # noqa: E402
from common import N, LATIN, ioc, encrypt_anti, decode_beam, totient_key, words_of, \
    print_verdict

KEYWORDS = ["DIVINITY", "FIRFUMFERENFE", "CIRCUMFERENCE", "INTUS", "INSTAR", "EMERGENCE",
            "PRIMALITY", "TOTIENT", "PILGRIM", "WELCOME"]


def keyed_alphabet(keyword):
    """sigma: rune -> rune, keyword letters first (deduplicated) then the rest in GP order."""
    order = []
    for ch in keyword.upper():
        if ch in LATIN and ch not in order:
            order.append(ch)
    for ch in LATIN:
        if ch not in order:
            order.append(ch)
    sigma = [LATIN.index(ch) for ch in order]
    inv = [0] * N
    for i, x in enumerate(sigma):
        inv[x] = i
    return sigma, inv


def main():
    print("=" * 72)
    print("outer_alphabet gate: keyword-mixed alphabet, c = sigma^-1(sigma(p) + k)")
    print("=" * 72)
    rng = random.Random(20261017)
    words = common.cap_words(words_of(common.CORPUS_B))
    plain = [x for w, _ in words for x in w]
    key = totient_key(len(plain) * 2)

    kw = KEYWORDS[rng.randrange(len(KEYWORDS))]
    sigma, inv = keyed_alphabet(kw)
    print("planted keyword: %s" % kw)

    # c = sigma^-1((sigma(p) + k) mod 29), with anti-repeat on the final rune.
    c = encrypt_anti([sigma[p] for p in plain], key, rng=rng)
    c = [inv[x] for x in c]

    # 1. blindness: identity alphabet.
    blind = decode_beam(c, key)
    ioc_blind = ioc(blind)
    print("identity-alphabet decode:           IoC %.3f  (must be < 1.3)" % ioc_blind)

    # 2. recovery: apply sigma to the ciphertext, then decode additively.
    rec = decode_beam([sigma[x] for x in c], key)
    ioc_rec = ioc(rec)
    print("sigma(c) decode (true alphabet):    IoC %.3f  (must be >= 1.5)" % ioc_rec)

    # 3. enumeration of the 10 lore alphabets.
    results = []
    for cand in KEYWORDS:
        s2, _ = keyed_alphabet(cand)
        dec = decode_beam([s2[x] for x in c], key)
        results.append((ioc(dec), cand))
    results.sort(reverse=True)
    for v, nm in results[:5]:
        print("alphabet scan: IoC %.3f  %s" % (v, nm))
    rank = [nm for _, nm in results].index(kw) + 1
    print("planted alphabet rank: %d of %d, IoC %.3f" % (rank, len(KEYWORDS), results[0][0]))

    # 4. null: a random alphabet.
    rnd = list(range(N))
    rng.shuffle(rnd)
    null = decode_beam([rnd[x] for x in c], key)
    print("random alphabet decode:             IoC %.3f  (must be < 1.5)" % ioc(null))

    ok = (ioc_blind < 1.3) and (ioc_rec >= 1.5) and (rank == 1 and results[0][0] >= 1.5) \
        and (ioc(null) < 1.5)
    return print_verdict("outer_alphabet", ok,
                         "blind %.2f / true %.2f / planted rank %d / random %.2f" %
                         (ioc_blind, ioc_rec, rank, ioc(null)))


if __name__ == "__main__":
    sys.exit(main())
