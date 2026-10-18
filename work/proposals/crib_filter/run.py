"""crib_filter gate: apostrophe / n't / one-rune-word decode filters, planted control +
the real LP2 constraint table.

Run: python run.py   (Windows: run.bat)
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import common  # noqa: E402
from common import N, LATIN, ioc, encrypt_anti, decode_beam, totient_key, words_of, \
    print_verdict

S, D, T, A, I, NN = (LATIN.index(x) for x in "SDTAIN")

# The four lone ticks in the unsolved images (work/ref/tick_marks.tsv, ticks=1):
# segment, rune index k of the tick; the crib applies to rune k+1 (after the tick).
APOSTROPHES = [(8, 381), (11, 1526), (14, 464), (15, 449)]
NT_SITES = [(8, 381), (15, 449)]   # 3-rune stems: N at k, T at k+1


def apply_filter(decoded, apos, nt, one_rune_pos):
    """Returns the list of failed checks for a decoded rune list."""
    fails = []
    for k in apos:
        if decoded[k + 1] not in (S, D, T):
            fails.append(("tail", k))
    for k in nt:
        if decoded[k] != NN or decoded[k + 1] != T:
            fails.append(("nt", k))
    for pos in one_rune_pos:
        if decoded[pos] not in (A, I):
            fails.append(("one-rune", pos))
    return fails


def main():
    print("=" * 72)
    print("crib_filter gate: apostrophe / n't / one-rune-word decode filters")
    print("=" * 72)
    rng = random.Random(20261017)
    words = words_of(common.CORPUS_B)
    plain = [x for w, _ in words for x in w]
    key = totient_key(len(plain) * 2)

    # Designated constraint sites in the plant (chosen where the plaintext fits).
    apos, nt, one_rune = [], [], []
    for i in range(len(plain) - 1):
        if plain[i + 1] in (S, D, T) and len(apos) < 4:
            apos.append(i)
        elif plain[i] == NN and plain[i + 1] == T and len(nt) < 2:
            nt.append(i)
    one_rune = [sum(len(w[0]) for w in words[:wi]) for wi, (w, _) in enumerate(words)
                if len(w) == 1][:4]
    print("planted constraints: %d apostrophe tails, %d n't sites, %d one-rune words"
          % (len(apos), len(nt), len(one_rune)))

    c = encrypt_anti(plain, key, rng=rng)

    # True decode must pass everything.
    true = decode_beam(c, key)
    fails_true = apply_filter(true, apos, nt, one_rune)
    print("true-key decode:     IoC %.3f, %d of %d checks failed (must be 0)"
          % (ioc(true), len(fails_true), len(apos) + len(nt) + len(one_rune)))

    # Wrong-key decode must fail most checks.
    wrong = decode_beam(c, key[7:])
    fails_wrong = apply_filter(wrong, apos, nt, one_rune)
    total_checks = len(apos) + len(nt) + len(one_rune)
    print("wrong-key decode:    IoC %.3f, %d of %d checks failed (must be >= 60%%)"
          % (ioc(wrong), len(fails_wrong), total_checks))

    # Real LP2 constraint table (informational: the filters ready for any verifier).
    segs = common.lp.load_segments()
    runes = {s: [t for t in segs[s] if isinstance(t, int)] for s in range(7, 16)}
    print("LP2 constraint table (ready for verifiers):")
    for seg, k in APOSTROPHES:
        stem = "n't (N,T)" if (seg, k) in NT_SITES else "tail S/D/T"
        print("   segment 0.%d, tick at rune %d: %s at %d, %d" %
              (seg, k, stem, k, k + 1))
    one_pos = []
    for s in range(7, 16):
        runes_s = [t for t in segs[s] if isinstance(t, int)]
        for w, a, b in common.lp.word_spans(segs[s], [0] * len(runes_s)):
            if b - a == 1:
                one_pos.append((s, a))
    print("   one-rune words: %d positions (must decode to A or I)" % len(one_pos))

    ok = (len(fails_true) == 0) and (len(fails_wrong) >= 0.6 * total_checks)
    return print_verdict("crib_filter", ok,
                         "true %d/%d failed / wrong %d/%d failed" %
                         (len(fails_true), total_checks, len(fails_wrong), total_checks))


if __name__ == "__main__":
    sys.exit(main())
