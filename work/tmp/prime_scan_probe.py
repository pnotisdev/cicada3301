"""Probe: verify API, segment sizes, pair counts, P29 marginals before the full sweep."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

import lp

segs = lp.load_segments()
print("segments:", len(segs))
tot = 0
for i in range(7, 16):
    r = lp.runes_of(segs[i])
    tot += len(r)
    print(f"seg {i}: runes={len(r)} ioc={lp.ioc(r):.3f}")
print("LP2 total runes:", tot)

for i in (1, 5, 16):
    r = lp.runes_of(segs[i])
    p = lp.KNOWN[i][1](r)
    print(f"KNOWN[{i}] {lp.KNOWN[i][0]}: cipher={len(r)} plain={len(p)}")
    print("   plaintext head:", lp.render(segs[i], p)[:70].replace("\n", " | "))

# word spans / pair counts per lag for LP2
P29 = [p % 29 for p in lp.PRIME]
runs = []
spans = []
off = 0
for i in range(7, 16):
    toks = segs[i]
    rs = lp.runes_of(toks)
    for w, s, e in lp.word_spans(toks, rs):
        spans.append((off + s, off + e))
    runs += rs
    off += len(rs)
print("LP2 words:", len(spans), "max word len:", max(e - s for s, e in spans))

for d in (1, 2, 3, 4, 5, 6, 7, 8):
    pairs = [(s + k, s + k + d) for s, e in spans for k in range(e - s - d)]
    print(f"lag {d}: pairs={len(pairs)}")

# marginal non-uniformity of P29 over LP2 (drives the a=0 chi2)
from collections import Counter
c = Counter(P29[r] for r in runs)
n = len(runs)
chi2_marg = sum((v - n / 29.0) ** 2 for v in c.values()) / (n / 29.0)
print(f"P29 marginal chi2={chi2_marg:.0f}  chi2/n={chi2_marg/n:.4f}")
c2 = Counter(runs)
ioc = sum(v * (v - 1) for v in c2.values()) / (n * (n - 1) / 29.0)
print(f"rune-index IoC={ioc:.3f}")
