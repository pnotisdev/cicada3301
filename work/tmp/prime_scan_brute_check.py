"""Brute-force cross-check of the sweep winners (direct per-pair histograms)."""
import sys, os, random, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import lp

N = 29
P29 = [p % N for p in lp.PRIME]
segs = lp.load_segments()

def dataset(idx):
    runs, spans = [], []
    off = 0
    for i in idx:
        toks = segs[i]
        rs = lp.runes_of(toks)
        for w, s, e in lp.word_spans(toks, rs):
            spans.append((off + s, off + e))
        runs += rs
        off += len(rs)
    return runs, spans

def chi2_brute(runs, spans, d, domain, a):
    h = [0] * N
    for s, e in spans:
        for k in range(e - s - d):
            i, j = s + k, s + k + d
            if domain == "PP":
                x, y = P29[runs[i]], P29[runs[j]]
                r = (y - a * x) % N
            elif domain == "IP":
                r = (P29[runs[j]] - a * runs[i]) % N
            else:
                r = (runs[j] - a * P29[runs[i]]) % N
            h[r] += 1
    n = sum(h)
    e = n / N
    return sum((c - e) ** 2 for c in h) / e

runs, spans = dataset(range(7, 16))
for domain, d in (("PP", 1), ("IP", 5), ("PI", 5), ("PP", 6), ("IP", 6)):
    vals = [(chi2_brute(runs, spans, d, domain, a), a) for a in range(N)]
    vals.sort(reverse=True)
    print(f"{domain} d={d}: top3 a,chi2 = {[(a, round(c,1)) for c, a in vals[:3]]}  a=0 -> {vals[-1][0] if vals[-1][1]==0 else '?'}")

# a=0 reference
print("a=0 PP d=1:", round(chi2_brute(runs, spans, 1, "PP", 0), 1))
print("a=0 IP d=5:", round(chi2_brute(runs, spans, 5, "IP", 0), 1))
print("a=0 PP d=6:", round(chi2_brute(runs, spans, 6, "PP", 0), 1))
