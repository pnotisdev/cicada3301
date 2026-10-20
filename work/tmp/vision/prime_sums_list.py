"""List the Gematria sum of every clause of the solved plaintext (scouting). Own code."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(HERE, ".."))
import lp
def isp(n):
    if n < 2: return False
    i = 2
    while i * i <= n:
        if n % i == 0: return False
        i += 1
    return True
segs = lp.load_segments()
for i, (title, fn) in lp.KNOWN.items():
    toks = segs[i]; plain = fn(lp.runes_of(toks)); it = iter(plain)
    cur, words, out = [], [], []
    def flush():
        global cur
        if cur:
            out.append(cur)
        cur = []
    for t in toks:
        if isinstance(t, int):
            cur.append(next(it))
        elif t in (".", "&", "%"):
            flush()
    flush()
    print(f"=== 0.{i} {title}")
    for u in out:
        s = sum(lp.PRIME[j] for j in u)
        print(f"  {s:6d} {'PRIME' if isp(s) else '     '}  n={len(u):3d}  {''.join(lp.LATIN[j] for j in u)[:70]}")
