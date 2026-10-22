"""Word-frequency (Zipf) checks on LP2's ciphertext words, keyless.

    python work/zipf_check.py

(1) Repeated word tokens per word length in LP2 against the same word lengths filled with LP2's own runes shuffled
    (200 draws): a word-level code or a key fixed per plaintext word would repeat frequent words (THE is 46 of 739 words
    in the solved plaintext). (2) The 83 one-rune words of LP2 against a uniform spread over 29 runes (chi-square and
    the largest count, 20,000 random draws): sorted counts always fall off, so the comparison is with sorted random counts.
Words are cut at word / clause / paragraph marks and numerals only (line and page breaks fall inside words).
"""
import collections
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lp  # noqa: E402
from discord_cumulative_check import words  # noqa: E402

LP2, SOLVED = range(7, 16), [0, 1, 2, 3, 4, 5, 6, 16, 17]


def repeats(ws):
    rep = collections.Counter()
    for w, n in collections.Counter(ws).items():
        if n > 1:
            rep[len(w)] += n - 1
    return rep


def main():
    segs = lp.load_segments()
    W = [tuple(w) for i in LP2 for w in words(segs[i])]
    rep = repeats(W)
    print(f"LP2: {len(W)} words, {len(set(W))} distinct; most frequent: "
          + ", ".join(f"{''.join(lp.LATIN[x] for x in w)} {n}" for w, n in collections.Counter(W).most_common(6)))
    runes, rng, null = [x for w in W for x in w], random.Random(1), collections.defaultdict(list)
    for _ in range(200):
        rng.shuffle(runes)
        it = iter(runes)
        r = repeats([tuple(next(it) for _ in w) for w in W])
        for L in range(1, 7):
            null[L].append(r[L])
    print("(1) repeated word tokens by length: LP2 vs shuffled runes (mean +- sd, 200 draws)")
    for L in range(1, 7):
        v = null[L]
        m = sum(v) / len(v)
        sd = (sum((x - m) ** 2 for x in v) / len(v)) ** 0.5
        print(f"    length {L}: {rep[L]} vs {m:.1f} +- {sd:.1f}")
    P = []
    for i in SOLVED:
        it = iter(x for x in lp.KNOWN[i][1](lp.runes_of(segs[i])) if isinstance(x, int))
        P += [tuple(w) for w in words([next(it) if isinstance(t, int) else t for t in segs[i]])]
    print(f"    solved plaintext for comparison: {len(P)} words, {len(set(P))} distinct; most frequent: "
          + ", ".join(f"{''.join(lp.LATIN[x] for x in w)} {n}" for w, n in collections.Counter(P).most_common(5)))
    one = [w[0] for w in W if len(w) == 1]
    n, c = len(one), collections.Counter(one)
    srt = sorted((c.get(k, 0) for k in range(29)), reverse=True)
    chi = sum((c.get(k, 0) - n / 29) ** 2 / (n / 29) for k in range(29))
    rng, C, M, S = random.Random(3301), [], [], []
    for _ in range(20000):
        d = collections.Counter(rng.randrange(29) for _ in range(n))
        s = sorted((d.get(k, 0) for k in range(29)), reverse=True)
        S.append(s)
        M.append(s[0])
        C.append(sum((d.get(k, 0) - n / 29) ** 2 / (n / 29) for k in range(29)))
    mean = [sum(s[r] for s in S) / len(S) for r in range(6)]
    print(f"(2) LP2 one-rune words: {n}; sorted counts {srt[:8]} ...; random sorted mean {[round(x, 1) for x in mean]} ...")
    print(f"    chi-square vs uniform {chi:.1f} (df 28), P {sum(x >= chi for x in C) / len(C):.3f}; "
          f"largest count {srt[0]}, P(max >= it) {sum(x >= srt[0] for x in M) / len(M):.3f}")
    assert len(W) == 2896 and n == 83, (len(W), n)  # the word and one-rune counts the registry cites


if __name__ == "__main__":
    main()
