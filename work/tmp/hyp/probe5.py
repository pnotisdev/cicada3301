"""Probe 5 (2026-10-17, laptop): two keyless checks on the surviving doublets and the lag-5 echo.

H-DITTO: the 86 surviving doublets are a "ditto" code for one plaintext letter X (the rune is repeated instead of
enciphering X). Then the doublets' second runes sit where X sits in words, and X occurs at 86/12,956 = 0.66%.
Compare the word-position classes of the doublets (1-rune word, initial, final, medial) with every English letter.

Quotes: is the within-word lag-5 echo concentrated in quoted speech (the spans between the tick-mark pairs of
work/ref/tick_marks.tsv), which would point to a different treatment of dialogue?
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, WORK)
sys.path.insert(0, HERE)
import lp  # noqa: E402
from probe1 import english_words, words_of  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
N = lp.N
LP2 = list(range(7, 16))
CLASSES = ("one", "ini", "fin", "med")
# quote spans (segment -> [(first, last) rune index]) from the tick pairs in work/ref/tick_marks.tsv, paired in order
SPANS = {8: [(930, 948)], 11: [(1847, 1866)], 15: [(75, 87), (171, 229), (571, 639), (2882, 2952)]}


def cls(L, j):
    return "one" if L == 1 else ("ini" if j == 0 else ("fin" if j == L - 1 else "med"))


def ditto():
    segs = lp.load_segments()
    obs = dict.fromkeys(CLASSES, 0)
    for si in LP2:
        stream = [(x, cls(len(w), j)) for w in words_of(segs[si]) for j, x in enumerate(w)]
        for i in range(1, len(stream)):
            if stream[i][0] == stream[i - 1][0]:
                obs[stream[i][1]] += 1
    tot = sum(obs.values())
    print(f"H-DITTO: doublets by the class of their second rune {obs} (total {tot})")
    ew = english_words()
    n = sum(map(len, ew))
    rows = []
    for X in range(N):
        prof = dict.fromkeys(CLASSES, 0)
        for w in ew:
            for j, x in enumerate(w):
                if x == X:
                    prof[cls(len(w), j)] += 1
        k = sum(prof.values())
        if not k:
            continue
        sh = [prof[c] / k for c in CLASSES]
        g = sum(2 * o * math.log(o / (tot * s)) if s > 0 else float("inf") for o, s in zip([obs[c] for c in CLASSES], sh) if o > 0)
        rows.append((g, lp.LATIN[X], 100 * k / n, sh))
    rows.sort()
    print("  best positional fits (G, 3 df) and their frequency (a ditto letter needs about 0.66%):")
    for g, lat, f, sh in rows[:4]:
        print(f"    X = {lat:3s} G = {g:6.1f}  frequency {f:.2f}%")
    print("  letters with frequency 0.3-1.2%:")
    for g, lat, f, sh in sorted(rows, key=lambda r: r[2]):
        if 0.3 <= f <= 1.2:
            print(f"    X = {lat:3s} G = {g:6.1f}  frequency {f:.2f}%  shares one/ini/fin/med "
                  + "/".join(f"{100 * s:.1f}" for s in sh))


def quotes():
    segs = lp.load_segments()
    inside = tot = cover = 0
    for si in LP2:
        pos, words, cur = 0, [], []
        for t in segs[si] + [" "]:
            if isinstance(t, int):
                cur.append(pos)
                pos += 1
            elif t == "\n":
                continue
            elif cur:
                words.append(cur)
                cur = []
        r = lp.runes_of(segs[si])
        for w in words:
            for a in range(len(w) - 5):
                if r[w[a]] == r[w[a + 5]]:
                    tot += 1
                    inside += any(lo <= w[a] < hi for lo, hi in SPANS.get(si, []))
        cover += sum(hi - lo for lo, hi in SPANS.get(si, []))
    print(f"\nquotes: within-word lag-5 coincidences {tot}, inside the quote spans {inside}; the spans cover "
          f"{100 * cover / 12956:.1f}% of LP2, so {tot * cover / 12956:.1f} are expected")


def restart_score(stream, starts, T=30):
    """coincidences c[i+t] == c[j+t], t = 1..T, over all pairs of start points (a key restarting at each start point
    puts the same key value at equal t, so the plaintext's coincidence rate shows until skips desynchronise)"""
    n, co, pairs = len(stream), 0, 0
    for a in range(len(starts)):
        for b in range(a + 1, len(starts)):
            i, j = starts[a], starts[b]
            for t in range(1, T + 1):
                if i + t < n and j + t < n:
                    pairs += 1
                    co += stream[i + t] == stream[j + t]
    e = pairs / N
    return (co - e) / (e * (1 - 1 / N)) ** 0.5, co, pairs


def doublet_restart():
    import random
    from probe2 import text_runes
    segs = lp.load_segments()
    stream = [x for i in LP2 for x in lp.runes_of(segs[i])]
    n = len(stream)
    dbl = [i for i in range(1, n) if stream[i] == stream[i - 1]]
    z, co, pairs = restart_score(stream, dbl)
    print(f"\nH-DRST (the key restarts after each surviving doublet): {co} coincidences in {pairs} aligned pairs "
          f"({100 * co / pairs:.2f}%, uniform 3.45%), z {z:+.2f}")
    R = random.Random(5)
    zs = sorted(restart_score(stream, sorted(R.sample(range(1, n - 1), len(dbl))))[0] for _ in range(20))
    print(f"  null: 86 random restart points, 20 replicates: z median {zs[10]:+.2f}, max {zs[-1]:+.2f}")
    emer = text_runes(os.path.join(WORK, "ref", "emerson_essays1.txt"))
    for trial in range(3):
        p = emer[5000 + trial * 13000:5000 + trial * 13000 + n]
        pts = sorted(R.sample(range(1, n - 1), 86))
        key = [R.randrange(N) for _ in range(20000)]
        c, j, ps = [], 0, set(pts)
        for i, x in enumerate(p):
            if i in ps:
                j = 0
            y = (x + key[j]) % N
            j += 1
            while c and y == c[-1] and R.random() < 0.8:
                y = (x + key[j]) % N
                j += 1
            c.append(y)
        print(f"  plant {trial}: English, key restarting at 86 known points (skip rule): z {restart_score(c, pts)[0]:+.2f}")


if __name__ == "__main__":
    ditto()
    quotes()
    doublet_restart()
