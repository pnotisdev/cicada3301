"""Find where the winner's (plain, ptr) stops being a coherent c-k decode."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

Q = 29


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
finals = [f for f in finals if f < n]

r = Rng(301 ^ 0x05EED5EED5EED5EE)
streams = [[r.below(Q) for _ in range(20000)] for _ in range(300)]
k = streams[127]
off = 11746

plain = [int(x) for x in open(os.path.join(HERE, "nulledge_tmp", "winner_plain.txt"), encoding="utf-8").read().split(",")]
ptr = [int(x) for x in open(os.path.join(HERE, "nulledge_tmp", "winner_ptr.txt"), encoding="utf-8").read().split(",")]
print(f"plain {len(plain)} letters, ptr {len(ptr)} entries")

# greedy: letter p occupies the earliest rune r >= current pos with (c[r] - k[ptr[p]]) % Q == plain[p]
pos, scored = 0, []
fails = []
for p, (t, jj) in enumerate(zip(plain, ptr)):
    found = -1
    for rr in range(pos, n):
        if (c[rr] - k[off + jj]) % Q == t:
            found = rr
            break
    if found < 0:
        fails.append((p, t, jj, pos))
        if len(fails) > 5:
            break
        pos += 1          # give up on this letter
        continue
    scored.append((found, p, t, jj))
    pos = found + 1
print("scored runes reconstructed:", len(scored), "of", len(plain))
print("first mismatch letters:", fails[:3])

if fails:
    p0, t0, jj0, pos0 = fails[0]
    print(f"letter {p0} value {t0} ptr {jj0} search from rune {pos0}")
    # show the surrounding context: which runes satisfy (c[r] - k[j]) == t for j = jj0, jj0-1, jj0+1
    for jj in (jj0, jj0 + 1, jj0 - 1, jj0 + 2):
        hits = [rr for rr in range(n) if (c[rr] - k[off + jj]) % Q == t0]
        print(f"  j={jj}: runes {hits[:6]}")
    # what are the neighbouring scored runes
    print("  last 3 scored:", scored[-3:])

# where do the scored runes sit relative to word finals?
sf = set(f for f, p, t, jj in scored)
print(f"scored set size {len(sf)}; non-final scored: {len(sf - set(finals))}; final scored: {len(sf & set(finals))}")
skipped_finals = sorted(set(finals) - sf)
print(f"word finals NOT scored (skipped): {len(skipped_finals)}: {skipped_finals}")
print("total skips = 300 - scored =", 300 - len(scored))

# does ptr[p] advance consistently? ptr[p] should be >= p (key index >= letter index is impossible in forward decode!)
print("ptr[p] < p for p:", [p for p in range(len(ptr)) if ptr[p] < p][:10])
print("ptr non-monotone at:", [p for p in range(1, len(ptr)) if ptr[p] < ptr[p - 1]][:10])
