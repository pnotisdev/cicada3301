"""Phase 48 step 2: oracle statistic null on LP2's one-rune ciphertext runes."""
import sys, math, random
sys.path.insert(0, "work")
import lp
segs = lp.load_segments()
c = []
for i in range(7, 16):
    r = lp.runes_of(segs[i])
    c += [r[a] for w, a, b in lp.word_spans(segs[i], r) if b - a == 1]
nF = sum(1 for x in c if x == 0); n = len(c); nn = n - nF
print("one-rune words", n, "of which ciphertext F", nF, "ciphertext A", c.count(24), "ciphertext I", c.count(10))
A, I = 24, 10
rng = random.Random(4801)
T = 100000; hist = [0] * (n + 1)
for _ in range(T):
    hit = 0
    for x in c:
        if x == 0: continue          # skip rule: F passes as F, never A/I
        hit += (x - rng.randrange(29)) % 29 in (A, I)
    hist[hit] += 1
mean = sum(k * h for k, h in enumerate(hist)) / T
p = 2 / 29
print("MC mean hits %.3f vs binomial mean %.3f; fraction %.4f" % (mean, nn * p, mean / n))
def bsf(k, m):  # P(X>=k)
    return sum(math.comb(m, j) * p**j * (1-p)**(m-j) for j in range(k, m+1))
for k in (5, 7, 10, 15, 20, 30, 50, 75):
    mc = sum(hist[k:]) / T
    print("P(hits>=%d): MC %.5f binomial %.3e" % (k, mc, bsf(k, nn)))
# minimal count of one-rune words needed for p<1e-4 with O=0.9
for m in range(3, 20):
    k = math.ceil(0.9 * m)
    if bsf(k, m) < 1e-4: print("smallest m with O>=0.9 giving p<1e-4: m=%d k=%d p=%.2e" % (m, k, bsf(k, m))); break
# Opair null: max over v of count in {v, v+14}
def opair(vals):
    from collections import Counter
    cnt = Counter(vals); return max(cnt[v] + cnt[(v + 14) % 29] for v in range(29))
hp = [0] * (n + 1)
for _ in range(20000):
    vals = [(x - rng.randrange(29)) % 29 if x else 0 for x in c]
    hp[opair(vals)] += 1
print("Opair null (count of runes in best {v,v+14}): mean %.2f; " % (sum(k*h for k,h in enumerate(hp))/20000),
      " ".join("P(>=%d)=%.4f" % (k, sum(hp[k:])/20000) for k in (8, 10, 12, 14, 16, 20, 30, 50)))
