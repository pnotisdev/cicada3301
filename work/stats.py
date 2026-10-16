"""Phase 3: statistical characterisation of the unsolved Liber Primus text.

    python stats.py doublets     # doublet anomaly: where, which runes, which lags
    python stats.py diffs        # distribution of c[i+1]-c[i] mod 29
"""
import math
import sys
from collections import Counter

import lp

N = lp.N
SEGS = lp.load_segments()
UNSOLVED = list(range(7, 16))


def stream(seg_ids=UNSOLVED, segs=SEGS):
    """Rune indices of the given segments, concatenated (segments are independent texts,
    so callers that care about boundaries should iterate per segment)."""
    return [x for i in seg_ids for x in lp.runes_of(segs[i])]


def adjacent_pairs(toks):
    """Yield (a, b, boundary) for consecutive runes; boundary is the strongest separator
    between them: '' (same word), ' ' word, '.' clause, '\\n' line only, '%' page, '&' paragraph, '#' numeral."""
    prev, sep = None, ""
    rank = {"": 0, "\n": 1, " ": 2, ".": 3, "#": 4, "&": 5, "%": 6}
    for t in toks:
        if isinstance(t, int):
            if prev is not None:
                yield prev, t, sep
            prev, sep = t, ""
        else:
            k = "#" if t.startswith("#") else t
            if rank[k] > rank[sep]:
                sep = k


def binom_sf(k, n, p):
    """P(X <= k) for X ~ Binomial(n, p) (lower tail), via log-space sum."""
    total = 0.0
    for i in range(k + 1):
        total += math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
                          + i * math.log(p) + (n - i) * math.log1p(-p))
    return total


def doublets():
    print("== Doublets by segment")
    for i in range(len(SEGS)):
        pairs = list(adjacent_pairs(SEGS[i]))
        d = sum(a == b for a, b, _ in pairs)
        tag = "unsolved" if i in UNSOLVED else ""
        print(f"0.{i:<3} pairs={len(pairs):5d} doublets={d:4d} rate={100 * d / max(1, len(pairs)):5.2f}%  {tag}")

    pairs = [p for i in UNSOLVED for p in adjacent_pairs(SEGS[i])]
    n, d = len(pairs), sum(a == b for a, b, _ in pairs)
    print(f"\nunsolved: {d} doublets in {n} pairs = {100 * d / n:.2f}% (random {100 / N:.2f}%, "
          f"expected {n / N:.0f}); P(X<={d}) = {binom_sf(d, n, 1 / N):.1e}")

    print("\n== By boundary type (unsolved)")
    names = {"": "inside word", "\n": "line break only", " ": "word gap", ".": "clause",
             "#": "numeral", "&": "paragraph", "%": "page"}
    by = Counter(s for _, _, s in pairs)
    dby = Counter(s for a, b, s in pairs if a == b)
    for s in names:
        if by[s]:
            print(f"  {names[s]:16s} pairs={by[s]:5d} doublets={dby[s]:3d} rate={100 * dby[s] / by[s]:5.2f}%")

    print("\n== Which runes double (unsolved)")
    freq = Counter(stream())
    dr = Counter(a for a, b, _ in pairs if a == b)
    tot = sum(freq.values())
    rows = []
    for r in range(N):
        exp = sum(1 for a, b, _ in pairs if a == r) * freq[r] / tot
        rows.append((dr[r], exp, r))
    print("  " + "  ".join(f"{lp.GP[r][0]}{lp.LATIN[r]}:{o}/{e:.0f}" for o, e, r in rows))

    print("\n== Coincidence rate at lag k (unsolved, within each segment)")
    for k in list(range(1, 13)) + [20, 29, 50, 100]:
        hit = tot_k = 0
        for i in UNSOLVED:
            c = lp.runes_of(SEGS[i])
            hit += sum(c[j] == c[j + k] for j in range(len(c) - k))
            tot_k += len(c) - k
        print(f"  lag {k:3d}: {100 * hit / tot_k:5.2f}%")


def diffs():
    print("== d = c[i+1] - c[i] mod 29, unsolved, within words and across all gaps")
    cnt = Counter()
    for i in UNSOLVED:
        c = lp.runes_of(SEGS[i])
        cnt.update((b - a) % N for a, b in zip(c, c[1:]))
    n = sum(cnt.values())
    e = n / N
    chi = sum((cnt[d] - e) ** 2 / e for d in range(N))
    chi_wo0 = sum((cnt[d] - e) ** 2 / e for d in range(1, N))
    for d in range(N):
        bar = "#" * int(60 * cnt[d] / max(cnt.values()))
        print(f"  d={d:2d} {cnt[d]:4d} ({(cnt[d] - e) / math.sqrt(e):+5.1f} sd) {bar}")
    print(f"  chi2 all 29 bins = {chi:.1f} (df 28, 99.9% crit 56.9); without d=0: {chi_wo0:.1f} (df 27, crit 55.5)")


if __name__ == "__main__":
    {"doublets": doublets, "diffs": diffs}[sys.argv[1]]()


# ---------------------------------------------------------------- residual / structure tests

def _streams(segs=SEGS, ids=UNSOLVED):
    return [lp.runes_of(segs[i]) for i in ids if len(lp.runes_of(segs[i])) > 100]


def residual_sweep(top=8):
    """IoC of r_i = c_i - a*F(c_{i-1}) - b*G(i) for simple F, G. English plaintext would
    give ~1.7; anything above ~1.03 deserves a look. Returns sorted results."""
    ps = lp.primes(4000)
    fib = [0, 1]
    while len(fib) < 4000:
        fib.append((fib[-1] + fib[-2]) % N)
    Fs = {"c": lambda x: x, "prime(c)": lambda x: lp.PRIME[x], "28-c": lambda x: N - 1 - x}
    Gs = {"0": lambda i: 0, "i": lambda i: i, "p_i": lambda i: ps[i], "p_i-1": lambda i: ps[i] - 1,
          "fib": lambda i: fib[i], "i^2": lambda i: i * i}
    res = []
    streams = _streams()
    for fn, F in Fs.items():
        for gn, G in Gs.items():
            for a in range(N):
                for b in ([0] if gn == "0" else range(1, N)):
                    num = den = 0.0
                    for c in streams:
                        r = [(c[i] - a * F(c[i - 1]) - b * G(i)) % N for i in range(1, len(c))]
                        num += lp.ioc(r) * len(r)
                        den += len(r)
                    res.append((num / den, f"c_i - {a}*{fn} - {b}*{gn}"))
    res.sort(reverse=True)
    return res[:top]


def transition_chi2(c_streams):
    """Chi-square of the 29x29 table of consecutive pairs, off-diagonal cells only,
    against expectation from rune frequencies (diagonal excluded and renormalised)."""
    tab = Counter()
    freq = Counter()
    for c in c_streams:
        tab.update(zip(c, c[1:]))
        freq.update(c)
    tot = sum(freq.values())
    P = {r: freq[r] / tot for r in range(N)}
    off = sum(v for (a, b), v in tab.items() if a != b)
    norm = sum(P[a] * P[b] for a in range(N) for b in range(N) if a != b)
    chi = 0.0
    for a in range(N):
        for b in range(N):
            if a != b:
                e = off * P[a] * P[b] / norm
                chi += (tab[(a, b)] - e) ** 2 / e
    return chi
