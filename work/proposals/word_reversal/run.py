"""word_reversal gate: per-word plaintext reversal, detectable only by boundary-aware LL.

Run: python run.py   (Windows: run.bat)
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import common  # noqa: E402
from common import N, ioc, encrypt_anti, decode_beam, totient_key, words_of, print_verdict

B = N  # boundary token index (one above the runes)


def boundary_table():
    """Bigram log-probabilities over 30 symbols (29 runes + word boundary), trained on
    CORPUS_A with a boundary inserted between words."""
    words = words_of(common.CORPUS_A)
    seq = []
    for runes, _ in words:
        seq.extend(runes)
        seq.append(B)
    cnt = [[1.0] * (N + 1) for _ in range(N + 1)]
    for a, b in zip(seq, seq[1:]):
        cnt[a][b] += 1.0
    tot = [sum(row) for row in cnt]
    return [[math.log(cnt[a][b] / tot[a]) for b in range(N + 1)] for a in range(N + 1)]


def seq_with_boundaries(letters, word_lens):
    out, i = [], 0
    for L in word_lens:
        out.extend(letters[i:i + L])
        out.append(B)
        i += L
    return out


def ll_bound(letters, word_lens, tab):
    seq = seq_with_boundaries(letters, word_lens)
    return sum(tab[a][b] for a, b in zip(seq, seq[1:]))


def main():
    print("=" * 72)
    print("word_reversal gate: per-word plaintext reversal (LL-detectable, IoC-blind)")
    print("=" * 72)
    rng = random.Random(20261017)
    words = words_of(common.CORPUS_B)
    wlens = [len(r) for r, _ in words]
    plain = [x for w, _ in words for x in w]
    key = totient_key(len(plain) * 2)
    tab = boundary_table()

    def run_case(reversed_plant):
        if reversed_plant:
            rev = []
            for r, _ in words:
                rev.extend(reversed(r))
            c = encrypt_anti(rev, key, rng=rng)
        else:
            c = encrypt_anti(plain, key, rng=rng)
        dec = decode_beam(c, key)
        ll_as_is = ll_bound(dec, wlens, tab)
        unreversed = []
        i = 0
        for L in wlens:
            unreversed.extend(reversed(dec[i:i + L]))
            i += L
        ll_rev = ll_bound(unreversed, wlens, tab)
        return ll_as_is, ll_rev, ioc(dec)

    # Planted reversed: un-reversing must win.
    a1, r1, i1 = run_case(reversed_plant=True)
    print("planted REVERSED:  as-is LL %.1f | un-reversed LL %.1f -> %s (IoC %.3f, orientation-blind)"
          % (a1, r1, "un-reversed wins" if r1 > a1 else "FAILS", i1))
    # Control: planted straight: as-is must win.
    a2, r2, i2 = run_case(reversed_plant=False)
    print("planted STRAIGHT:  as-is LL %.1f | un-reversed LL %.1f -> %s (IoC %.3f)"
          % (a2, r2, "as-is wins" if a2 > r2 else "FAILS", i2))

    ok = (r1 > a1) and (a2 > r2)
    return print_verdict("word_reversal", ok,
                         "reversed: un-reversed wins by %.1f nats | straight: as-is wins "
                         "by %.1f nats" % (r1 - a1, a2 - r2))


if __name__ == "__main__":
    sys.exit(main())
