"""Repeated k-grams in LP2 against shuffled LP2.

The only 'repeat' reported in the community (aldegonde's DJU-BEI, a 6-rune repeat at stream offsets 6555 and
12950) is not unusual for 12,956 random runes: the expected number of repeated 6-grams is 0.18 (P(>=1) ~ 0.16).
A reused plaintext phrase under a continuous key would not repeat at all, so no long repeat is the expected result
for OTP-class text and a 7+-rune repeat would have been a real lead.

    python work/repeat_spectrum.py
"""
import collections
import os
import random
import sys

import numpy as np

import lp
import stats

HERE = os.path.dirname(os.path.abspath(__file__))


def repeated_pairs(seq, k):
    c = collections.Counter(tuple(seq[i:i + k]) for i in range(len(seq) - k + 1))
    return sum(v * (v - 1) // 2 for v in c.values())


def main():
    allr = [x for i in stats.UNSOLVED for x in lp.runes_of(stats.SEGS[i])]
    n = len(allr)
    f = np.bincount(allr, minlength=lp.N) / n
    S = float((f ** 2).sum())
    R = random.Random(5)
    shuf = []
    for _ in range(300):
        a = allr[:]
        R.shuffle(a)
        shuf.append(a)
    out = [f"LP2: {n} runes. Repeated k-gram pairs: observed, expected for iid runes, 300 shuffles (mean +- sd), "
           f"P(shuffle >= observed)", "k  observed  expected   shuffles          P"]
    for k in range(3, 11):
        obs = repeated_pairs(allr, k)
        e = (n - k + 1) * (n - k) / 2 * S ** k
        sv = [repeated_pairs(a, k) for a in shuf]
        p = (sum(v >= obs for v in sv) + 1) / (len(sv) + 1)
        out.append(f"{k:2d} {obs:8d} {e:9.2f}   {np.mean(sv):7.2f} +- {np.std(sv):5.2f}   {p:.3f}")
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "repeat_spectrum.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
