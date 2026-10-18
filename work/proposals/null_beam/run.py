"""null_beam gate: unkeyed per-word null runes, null-aware vs null-blind beam.

Run: python run.py   (Windows: run.bat)
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import common  # noqa: E402
from common import N, ioc, encrypt_anti, decode_beam, totient_key, words_of, bigram_table, \
    print_verdict


def plant_nulls(words, p_null, rng):
    """Expanded rune list with nulls (uniform runes at random inner positions),
    per-position is-null flags, and per-word has-null booleans. Nulls consume NO key."""
    out, flags, has = [], [], []
    for runes, _ in words:
        h = len(runes) > 1 and rng.random() < p_null
        has.append(h)
        if not h:
            out.extend(runes)
            flags.extend([False] * len(runes))
        else:
            pos = rng.randrange(1, len(runes))  # inner slot only
            out.extend(runes[:pos])
            out.append(rng.randrange(N))       # the null rune
            out.extend(runes[pos:])
            flags.extend([False] * pos + [True] + [False] * (len(runes) - pos))
    return out, flags, has


def encrypt_with_nulls(expanded, flags, key, rng=None, coin=0.81):
    """Anti-repeat encryptor whose key pointer HOLDS at null runes."""
    rng = rng or random.Random(0)
    c, j, prev = [], 0, -1
    L = len(key)
    for rune, isnull in zip(expanded, flags):
        if isnull:
            c.append(rune)
            prev = rune
            continue
        x = (rune + key[j % L]) % N
        j += 1
        if x == prev and rng.random() < coin:
            x = (rune + key[j % L]) % N
            j += 1
        c.append(x)
        prev = x
    return c


def decode_null(c, key, wlens, beam=96):
    """Null-aware beam: per cipher rune either a plaintext letter (key consumed;
    a redraw is allowed only where the skip check holds) or a null (pointer stays,
    at most one per word at an inner slot). Returns (letters with None for nulls,
    null count)."""
    bg = bigram_table()
    L = len(key)
    lnN = math.log(1.0 / N)
    lnnull = math.log(0.094)   # prior: ~42% of multi-rune words / mean word length
    states = {(0, -1, 0, 0, 0): (0.0, [])}
    prev = -1
    for i, x in enumerate(c):
        new = {}
        for (ptr, last, used, wi, wpos), (sc, letters) in states.items():
            wl = wlens[wi]
            if wpos == 0:
                used = 0
            nwi, nwpos = wi, wpos + 1
            if nwpos == wl:
                nwi, nwpos = wi + 1 if wi + 1 < len(wlens) else wi, 0
            # A: plaintext letter (key consumed)
            p0 = (x - key[ptr % L]) % N
            s = sc + (bg[last][p0] if last >= 0 else lnN)
            k2 = (ptr + 1, p0, used, nwi, nwpos)
            if k2 not in new or s > new[k2][0]:
                new[k2] = (s, letters + [p0])
            # A-skip: redraw, only where key and ciphertext are consistent
            if prev >= 0 and (key[(ptr + 1) % L] - key[ptr % L]) % N == (x - prev) % N:
                p1 = (x - key[(ptr + 1) % L]) % N
                s = sc + (bg[last][p1] if last >= 0 else lnN) + math.log(0.81)
                k2 = (ptr + 2, p1, used, nwi, nwpos)
                if k2 not in new or s > new[k2][0]:
                    new[k2] = (s, letters + [p1])
            # B: null (inner slot, first null of this word)
            if wpos >= 1 and used == 0 and wpos + 1 < wl:
                s = sc + lnN + lnnull
                k2 = (ptr, last, 1, nwi, nwpos)
                if k2 not in new or s > new[k2][0]:
                    new[k2] = (s, letters + [None])
        states = dict(sorted(new.items(), key=lambda kv: kv[1][0], reverse=True)[:beam])
        prev = x
    _, letters = max(states.values(), key=lambda v: v[0])
    return letters, sum(1 for p in letters if p is None)


def main():
    print("=" * 72)
    print("null_beam gate: unkeyed per-word null runes")
    print("=" * 72)
    rng = random.Random(20261017)
    words = common.cap_words(words_of(common.CORPUS_B))
    plain = [x for w, _ in words for x in w]
    key = totient_key(len(plain) * 2)

    # Plant with nulls (unkeyed: the pointer holds at a null).
    expanded, flags, has = plant_nulls(words, 0.42, rng)
    c = encrypt_with_nulls(expanded, flags, key, rng=rng)
    cwl = [len(runes) + (1 if h else 0) for (runes, _), h in zip(words, has)]
    n_null_words = sum(has)
    print("planted nulls: %d of %d words (%.0f%%), expanded %d -> %d runes"
          % (n_null_words, len(words), 100 * n_null_words / len(words), len(plain), len(c)))

    # 1. blind decode must fail.
    blind = decode_beam(c, key)
    print("null-blind decode:     IoC %.3f  (must be < 1.3)" % ioc(blind))

    # 2. null-aware decode must recover.
    letters, nnull = decode_null(c, key, cwl)
    pl = [p for p in letters if p is not None]
    print("null-aware decode:     IoC %.3f, nulls found %d (planted %d)"
          % (ioc(pl), nnull, n_null_words))

    # 3. self-consistency: ciphertext word lengths vs plaintext.
    frac = sum(1 for (r, _), h, l in zip(words, has, cwl) if l - len(r) == (1 if h else 0)) / len(words)
    print("word-length signature: %.0f%% consistent with the plant" % (100 * frac))

    # 4. control: no nulls planted -> decoder must not hallucinate.
    c0 = encrypt_anti(plain, key, rng=rng)
    wl0 = [len(r) for r, _ in words]
    letters0, nnull0 = decode_null(c0, key, wl0)
    pl0 = [p for p in letters0 if p is not None]
    print("no-null control:       IoC %.3f, nulls hallucinated %d (must be ~0)"
          % (ioc(pl0), nnull0))

    ok = (ioc(blind) < 1.3) and (ioc(pl) >= 1.5) and (abs(nnull - n_null_words) <= 0.2 * n_null_words) \
        and (nnull0 <= 2) and (frac > 0.9)
    return print_verdict("null_beam", ok,
                         "blind %.2f / aware %.2f / nulls %d vs %d / hallucinated %d" %
                         (ioc(blind), ioc(pl), nnull, n_null_words, nnull0))


if __name__ == "__main__":
    sys.exit(main())
