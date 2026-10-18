"""Exact Python simulation of the nulledge ioc_beam for one decode, to compare with the engine's winner.

Winner under test: RANDOM 127 (rand:300:301), offset 11746, model 0, nulledge=1, engine says s=4106, n=261.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

Q = 29
BEAM = 16


class Rng:
    def __init__(self, seed):
        self.s = seed & 0xFFFFFFFFFFFFFFFF

    def next(self):
        self.s = (self.s + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = self.s
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        return (z ^ (z >> 31)) & 0xFFFFFFFFFFFFFFFF

    def below(self, n):
        return ((self.next() >> 32) * n) >> 32


win = os.path.join(HERE, "nulledge_window_v1.txt")
lines = open(win, encoding="utf-8").read().splitlines()
runes = [int(x) for x in lines[[i for i, l in enumerate(lines) if l.startswith("R ")][0]].split()[1:]]
lens = [int(x) for x in lines[[i for i, l in enumerate(lines) if l.startswith("L ")][0]].split()[1:]]
n = 300
c = runes[:n]
finals, b = [], 0
for l in lens:
    b += l
    finals.append(b - 1)
flags = [False] * n
for f in finals:
    if f < n:
        flags[f] = True

r = Rng(301 ^ 0x05EED5EED5EED5EE)
streams = [[r.below(Q) for _ in range(20000)] for _ in range(300)]
mk = streams[127]
off = 11746
key = mk[off:off + 383]

# model 0, forward, no guard, no signs; states (j, s, cnt tuple, n, pv, hist)
pv0 = -1
cur = [(0, 0, (0,) * Q, 0, pv0, [])]
for i in range(n):
    ci = c[i]
    npv = runes[i + 1] if i + 1 < len(runes) else ci
    extra = []
    if flags[i]:
        extra.extend(cur)
    newcur = []
    idx = 0
    # copy cur to a list we mutate like swap_remove
    work = list(cur)
    while idx < len(work):
        j, s, cnt, nn, pv, hist = work[idx]
        if j + 3 > len(key):
            idx += 1
            continue
        k0 = key[j]
        t0 = (ci - k0) % Q
        if pv >= 0:
            pvv = pv
            k1 = key[j + 1]
            t1 = (ci - k1) % Q
            if (t1 + k0) % Q == pvv:
                cnt2 = list(cnt)
                cnt2[t1] += 1
                extra.append((j + 2, s + 2 * cnt[t1], tuple(cnt2), nn + 1, npv, hist + [(i, j + 1, t1)]))
            k2 = key[j + 2]
            t2 = (ci - k2) % Q
            if (t2 + k0) % Q == pvv and (t2 + k1) % Q == pvv:
                cnt3 = list(cnt)
                cnt3[t2] += 1
                extra.append((j + 3, s + 2 * cnt[t2], tuple(cnt3), nn + 1, npv, hist + [(i, j + 2, t2)]))
        cnt1 = list(cnt)
        cnt1[t0] += 1
        work[idx] = (j + 1, s + 2 * cnt[t0], tuple(cnt1), nn + 1, npv, hist + [(i, j, t0)])
        idx += 1
    cur = work + extra
    if not cur:
        break
    # merge on j keeping max s
    if len(cur) > 1:
        merged = {}
        for st in cur:
            j = st[0]
            if j not in merged or st[1] > merged[j][1]:
                merged[j] = st
        cur = list(merged.values())
        if len(cur) > BEAM:
            cur.sort(key=lambda st: -st[1])
            cur = cur[:BEAM]
    if i + 1 == 150:
        best = max(st[1] for st in cur)
        if best < 925:
            print(f"aborted at 150 (best {best})")
            sys.exit(0)

best = max(cur, key=lambda st: st[1])
s, nn = best[1], best[3]
ioc = Q * s / (nn * (nn - 1))
print(f"sim: s={s} n={nn} ioc={ioc:.4f} (engine: s=4106 n=261 ioc=1.7547)")
cnt = list(best[2])
print("top counts:", sorted(((v, i) for i, v in enumerate(cnt)), reverse=True)[:8])
hist = best[5]
bad = 0
for (r, j, t) in hist:
    if (c[r] - key[j]) % Q != t:
        bad += 1
print(f"history entries: {len(hist)}; letter != c-k violations: {bad}")
js = [j for r, j, t in hist]
print("distinct j:", len(set(js)), "monotone:", all(js[p] < js[p + 1] for p in range(len(js) - 1)))
# scored runes: gaps between runes
rs = [r for r, j, t in hist]
gaps = [rs[p + 1] - rs[p] for p in range(len(rs) - 1)]
print("rune gaps max:", max(gaps) if gaps else 0, "gaps>1:", sum(1 for g in gaps if g > 1))
