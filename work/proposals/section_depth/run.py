"""section_depth gate: shared pad at section starts, power of the difference statistic.

Run: python run.py   (Windows: run.bat)
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import common  # noqa: E402
from common import N, ioc, encrypt_anti, totient_key, markov, print_verdict

NUN = 4000


def diff_model(rng):
    """Empirical bigram model of the difference of two corpus-consistent streams:
    log P(d_i | d_{i-1}), add-1 smoothed, from a long simulated pair."""
    m = 40000
    a = markov(m, rng)
    b = markov(m, rng)
    cnt = [[1.0] * N for _ in range(N)]
    for i in range(1, m):
        d0 = (a[i - 1] - b[i - 1]) % N
        d1 = (a[i] - b[i]) % N
        cnt[d0][d1] += 1.0
    tot = [sum(row) for row in cnt]
    return [[math.log(cnt[x][y] / tot[x]) for y in range(N)] for x in range(N)]


def ll_excess(diff, model):
    """Bigram log-likelihood of the difference stream per rune, minus log(1/N)
    (the flat-model baseline). Reported relative to the independent-pad null."""
    s = 0.0
    for i in range(1, len(diff)):
        s += model[diff[i - 1]][diff[i]] - math.log(1.0 / N)
    return s / (len(diff) - 1)


def diff_of(c1, c2):
    return [(a - b) % N for a, b in zip(c1, c2)]


def shared_noskip(p1, p2, key):
    L = len(key)
    c1 = [(p + key[i % L]) % N for i, p in enumerate(p1)]
    c2 = [(p + key[i % L]) % N for i, p in enumerate(p2)]
    return diff_of(c1, c2)


def independent_noskip(p1, p2, rng):
    c1 = [(p + rng.randrange(N)) % N for p in p1]
    c2 = [(p + rng.randrange(N)) % N for p in p2]
    return diff_of(c1, c2)


def main():
    print("=" * 72)
    print("section_depth gate: shared pad at section starts (power curve)")
    print("=" * 72)
    rng = random.Random(20261017)
    model = diff_model(rng)
    p1 = markov(NUN, rng)
    p2 = markov(NUN, rng)
    key = totient_key(NUN)

    # No-skip: shared vs 10 independent draws.
    shared = shared_noskip(p1, p2, key)
    s_ex = ll_excess(shared, model)
    inds = [ll_excess(independent_noskip(p1, p2, rng), model) for _ in range(10)]
    mu = sum(inds) / len(inds)
    sd = (sum((x - mu) ** 2 for x in inds) / (len(inds) - 1)) ** 0.5
    gain = s_ex - mu
    z = gain / sd if sd > 0 else 0.0
    print("no anti-repeat: shared LL %.4f | independent %.4f +/- %.4f nats/rune -> gain %.4f, z %.1f (need >= 5)"
          % (s_ex, mu, sd, gain, z))
    print("               unigram IoC for honesty: shared %.3f | independent %.3f (near-powerless by design)"
          % (ioc(shared), ioc(diff_of([(p + key[i]) % N for i, p in enumerate(p1)],
                                      [(p + rng.randrange(N)) % N for p in p2]))))

    # With the anti-repeat rule: the same pad, each section drifts after ~36 runes.
    c1a = encrypt_anti(p1, key, rng=rng)
    c2a = encrypt_anti(p2, key, rng=rng)
    d_full = diff_of(c1a, c2a)
    w_ex = ll_excess(d_full, model)
    inds2 = []
    for _ in range(10):
        ind2 = encrypt_anti(p2, [rng.randrange(N) for _ in range(NUN)], rng=rng)
        inds2.append(ll_excess(diff_of(c1a, ind2), model))
    mu2 = sum(inds2) / len(inds2)
    sd2 = (sum((x - mu2) ** 2 for x in inds2) / (len(inds2) - 1)) ** 0.5
    gain2 = w_ex - mu2
    win_ex = ll_excess(d_full[:36], model)
    collapse = gain2 / gain if gain > 0 else 1.0
    print("with anti-repeat: shared LL %.4f | independent %.4f +/- %.4f nats/rune -> gain %.4f"
          % (w_ex, mu2, sd2, gain2))
    print("                 first-36-rune window (the only aligned part): %.4f nats/rune"
          % win_ex)
    print("                 collapse: %.0f%% of the clean gain retained (must be <= 25%%)"
          % (100 * collapse))

    ok = (z >= 5) and (collapse <= 0.25)
    return print_verdict(
        "section_depth", ok,
        "clean gain %.4f nats/rune (z %.1f) | with skip gain %.4f (collapse %.0f%%) -> the LM "
        "drift-tracking beam is required for the real campaign" %
        (gain, z, gain2, 100 * collapse))


if __name__ == "__main__":
    sys.exit(main())
