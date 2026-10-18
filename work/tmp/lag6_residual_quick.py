# Quick independent check: is the within-word lag-6 relation c' = 24 - 2c (mod 29)
# the enciphering equation itself (c_i = p_i + 24 - 2*c_{i-6} within words)?
# If so, r = (c' + 2c - 24) mod 29 IS the plaintext at lag-6-eligible positions.
# Also the lag-5 residual r5 = (c' - c) mod 29 under c_i = p_i + c_{i-5} (+b variants).
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lp

N = 29
segs = lp.load_segments()

def lags_within(seg, d):
    toks = seg
    runes = lp.runes_of(toks)
    spans = lp.word_spans(toks, runes)
    pairs = []
    for _w, s, e in spans:
        for j in range(s, e - d):
            pairs.append((runes[j], runes[j + d]))
    return pairs

def chi2(counts, n):
    e = n / N
    return sum((c - e) ** 2 / e for c in counts)

def counts_of(pairs, fn):
    cs = [0] * N
    for a, b in pairs:
        cs[fn(a, b)] += 1
    return cs

print("== LP2 sections 0.7-0.15 (indexes 7..15) ==")
# sanity: reproduce echo numbers
pairs6 = []
pairs5 = []
for i in range(7, 16):
    pairs6 += lags_within(segs[i], 6)
    pairs5 += lags_within(segs[i], 5)
hits6 = sum(1 for a, b in pairs6 if b == (24 - 2 * a) % N)
hits5 = sum(1 for a, b in pairs5 if b == a)
ss5 = sum(1 for a, b in pairs5 if b == a and a == 15)
print(f"lag6 pairs={len(pairs6)} hits={hits6} expected~{len(pairs6)/N:.1f}")
print(f"lag5 pairs={len(pairs5)} hits={hits5} expected~{len(pairs5)/N:.1f}  S,S={ss5}")

# residual lag6: r = (b + 2a - 24) mod 29  -> candidate plaintext p_i
r6 = counts_of(pairs6, lambda a, b: (b + 2 * a - 24) % N)
n6 = len(pairs6)
print(f"\nlag6 residual r = c' + 2c - 24  (n={n6})  chi2={chi2(r6, n6):.1f}  IoC={lp.ioc([(b + 2*a - 24) % N for a, b in pairs6]):.4f}")
top = sorted(range(N), key=lambda j: -r6[j])[:12]
print("  top:", " ".join(f"{lp.LATIN[j]}:{r6[j]}" for j in top))
print(f"  r==0 (F) count: {r6[0]} vs expected {n6/N:.1f}")

# residual lag5: r = (b - a) mod 29 under c' = p' + c (coincidence <-> p'=0)
r5 = counts_of(pairs5, lambda a, b: (b - a) % N)
n5 = len(pairs5)
print(f"\nlag5 residual r = c' - c  (n={n5})  chi2={chi2(r5, n5):.1f}  IoC={lp.ioc([(b - a) % N for a, b in pairs5]):.4f}")
top5 = sorted(range(N), key=lambda j: -r5[j])[:12]
print("  top:", " ".join(f"{lp.LATIN[j]}:{r5[j]}" for j in top5))

# print residual tails per word as candidate plaintext (longest words first)
print("\n== residual per word (lag6, a=27 b=24) ==")
for i in range(7, 16):
    toks = segs[i]
    runes = lp.runes_of(toks)
    for _w, s, e in lp.word_spans(toks, runes):
        if e - s >= 9:
            tail = "".join(lp.LATIN[(runes[j + 6] + 2 * runes[j] - 24) % N] for j in range(s, e - 6))
            src = "".join(lp.LATIN[x] for x in runes[s:e])
            print(f"  sec {i} len{e-s:2d}  {src}  ->  {tail}")

# null: solved An End ciphertext (seg 6), same stats
print("\n== solved An End (seg 6) as real-data null ==")
p6 = lags_within(segs[6], 6)
h = sum(1 for a, b in p6 if b == (24 - 2 * a) % N)
r = counts_of(p6, lambda a, b: (b + 2 * a - 24) % N)
print(f"  pairs={len(p6)} hits={h} expected~{len(p6)/N:.1f}  chi2={chi2(r, len(p6)):.1f}  IoC={lp.ioc([(b + 2*a - 24) % N for a, b in p6]):.4f}")
