"""Do the DISPLAYED (cipher) sentence sums of the solved pages carry the prime property too? (scouting) Own code."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..")); sys.path.insert(0, os.path.join(HERE, "..", ".."))
import lp
def isp(n):
    if n < 2: return False
    i = 2
    while i * i <= n:
        if n % i == 0: return False
        i += 1
    return True
segs = lp.load_segments()
tot = [0, 0]
for i, (title, fn) in lp.KNOWN.items():
    toks = segs[i]; cur, units = [], []
    for t in toks:
        if isinstance(t, int): cur.append(t)
        elif t in (".", "&"):
            if cur: units.append(cur); cur = []
    if cur: units.append(cur)
    units = [u for u in units if len(u) >= 6]
    pr = sum(isp(sum(lp.PRIME[j] for j in u)) for u in units)
    tot[0] += pr; tot[1] += len(units)
    print(f"0.{i:<3d}{title:24s} displayed-cipher clause sums prime: {pr}/{len(units)}")
print("pooled", tot, f"{100*tot[0]/tot[1]:.1f}%  (null about 13-15%)")
