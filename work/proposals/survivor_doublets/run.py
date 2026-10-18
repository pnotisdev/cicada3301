"""survivor_doublets: per-word-length distribution of the surviving doublets, with a
synthetic control that must identify the planted model before LP2 is read.

Run: python run.py   (Windows: run.bat)
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import common  # noqa: E402
from common import N, encrypt_anti, totient_key, markov, print_verdict


def word_doublet_bins(runes, word_spans, max_len=8):
    """Per word-length bin: number of words, adjacent pairs inside words, and doublets
    fully inside words. Returns (n_words, n_pairs, n_doublets) per length bin 2..max_len+."""
    nw = [0] * max_len
    np_ = [0] * max_len
    nd = [0] * max_len
    for a, b in word_spans:
        L = b - a
        if L < 2:
            continue
        bin_ = min(L, max_len) - 1
        nw[bin_] += 1
        np_[bin_] += L - 1
        for i in range(a, b - 1):
            if runes[i] == runes[i + 1]:
                nd[bin_] += 1
    return nw, np_, nd


def g_test(nd, pred, pred2):
    """G statistic of observed doublet counts against two predictions (normalised)."""
    g1 = g2 = 0.0
    tot = sum(nd)
    s1, s2 = sum(pred), sum(pred2)
    for o, e1, e2 in zip(nd, pred, pred2):
        e1n = tot * e1 / s1 if s1 else 0.0
        e2n = tot * e2 / s2 if s2 else 0.0
        if o > 0 and e1n > 0:
            g1 += o * math.log(o / e1n)
        if o > 0 and e2n > 0:
            g2 += o * math.log(o / e2n)
    return 2 * g1, 2 * g2


def synthetic(rng, kind):
    """A synthetic 'section' with a planted survivor process.
    kind='coin': survivors come from the anti-repeat coin rule (81% enforcement).
    kind='ditto': survivors are placed deliberately in long words only (non-coin
    structure the G-test must reject under both predictions)."""
    runes = markov(8000, rng)
    words = []
    a = 0
    while a < 8000:
        L = rng.randrange(4, 8)
        if a + L > 8000:
            break
        words.append((a, a + L))
        a += L
    key = [rng.randrange(N) for _ in range(9000)]
    if kind == "coin":
        c = encrypt_anti(runes, key, rng=rng)
    else:
        c = [(p + rng.randrange(N)) % N for p in runes]
        for (a, b) in words:
            if b - a >= 7:  # ditto: doublets only in long words, at a high rate
                for i in range(a, b - 1):
                    if rng.random() < 0.02:
                        c[i + 1] = c[i]
    return word_doublet_bins(c, words)


def main():
    print("=" * 72)
    print("survivor_doublets: per-word-length distribution of the surviving doublets")
    print("=" * 72)
    rng = random.Random(20261017)

    # Synthetic control: the test must accept the planted coin model and reject a
    # deliberately non-coin (ditto) process.
    def model_g(bins):
        nw, np_, nd = bins
        pred_coin = np_          # survivors proportional to adjacent pairs
        pred_unif = [nw[i] * (i + 2) for i in range(len(nw))]  # proportional to runes
        return g_test(nd, pred_coin, pred_unif)

    g_coin_coin, g_coin_unif = model_g(synthetic(random.Random(1), "coin"))
    g_ditto_coin, g_ditto_unif = model_g(synthetic(random.Random(2), "ditto"))
    control_ok = (g_coin_coin < g_coin_unif) and (g_ditto_coin > g_coin_coin + 5)
    print("synthetic control: planted coin -> G(coin %.1f) < G(uniform %.1f): %s"
          % (g_coin_coin, g_coin_unif, g_coin_coin < g_coin_unif))
    print("                   planted ditto -> G(coin %.1f) (rejected, must exceed %.1f): %s"
          % (g_ditto_coin, g_coin_coin + 5, g_ditto_coin > g_coin_coin + 5))

    # LP2: the real numbers.
    segs = common.lp.load_segments()
    runes, spans = [], []
    for s in range(7, 16):
        toks = segs[s]
        base = len(runes)
        runes.extend(t for t in toks if isinstance(t, int))
        for _, a, b in common.lp.word_spans(toks, [0] * sum(1 for t in toks if isinstance(t, int))):
            spans.append((base + a, base + b))
    bins = word_doublet_bins(runes, spans)
    nw, np_, nd = bins
    g_coin, g_unif = g_test(nd, np_, [nw[i] * (i + 2) for i in range(len(nw))])
    print("LP2: %d in-word doublets over %d words" % (sum(nd), sum(nw)))
    for i in range(len(nw)):
        if nw[i]:
            print("   length %d: %5d words, %5d pairs, %3d doublets" %
                  (i + 2, nw[i], np_[i], nd[i]))
    print("LP2: G(coin %.1f) vs G(uniform %.1f): %s" %
          (g_coin, g_unif, "coin model fits better" if g_coin < g_unif
           else "uniform model fits better"))

    return print_verdict("survivor_doublets", control_ok,
                         "synthetic control: coin accepted, ditto rejected: %s | LP2: "
                         "G(coin %.1f) vs G(uniform %.1f) -> %s" %
                         (control_ok, g_coin, g_unif,
                          "coin" if g_coin < g_unif else "uniform"))


if __name__ == "__main__":
    sys.exit(main())
