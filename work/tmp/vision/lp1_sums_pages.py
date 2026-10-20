"""Gematria sums of whole pages / sections of the solved plaintext, with factorisations (scouting). Own code."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..")); sys.path.insert(0, os.path.join(HERE, "..", ".."))
import lp
def fac(n):
    f, d = [], 2
    while d * d <= n:
        while n % d == 0: f.append(d); n //= d
        d += 1
    if n > 1: f.append(n)
    return "*".join(map(str, f))
segs = lp.load_segments()
for i, (title, fn) in lp.KNOWN.items():
    toks = segs[i]; plain = fn(lp.runes_of(toks)); it = iter(plain)
    pages, cur = [], 0
    for t in toks:
        if isinstance(t, int): cur += lp.PRIME[next(it)]
        elif t == "%":
            pages.append(cur); cur = 0
    pages.append(cur)
    tot = sum(lp.PRIME[j] for j in plain)
    print(f"0.{i:<3d}{title:24s} section sum {tot:6d} = {fac(tot):22s} pages: " + ", ".join(f"{p}={fac(p)}" for p in pages))
