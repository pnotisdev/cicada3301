"""Phase 53: do LP2 marks work as paired open/close brackets? Feasibility only (see work/log/phase53_nested_marks.md)."""
import os, random, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lp import MASTER, RUNE_IDX
sys.stdout.reconfigure(encoding="utf-8")

text = open(MASTER, encoding="utf-8").read().split("\n\n", 1)[1].split("§")[0]
raw = [c for c in text.split("$") if any(ch in RUNE_IDX for ch in c)]
raw = raw[:16]   # chunks 16-17 are not sections; chunks 7-15 sum to 12,956 runes
def marks(c): return [ch for ch in c if ch not in RUNE_IDX and ch != "\n"]

def stats(m, a, b):
    """open=a, close=b: equal counts, never-close-before-open, strict alternation, max depth."""
    d = mn = mx = 0; alt = True; last = None
    for x in m:
        if x == a: d += 1
        elif x == b: d -= 1
        else: continue
        mn, mx = min(mn, d), max(mx, d)
        if x == last: alt = False
        last = x
    return d == 0, mn >= 0, alt, mx

print("section runes " + "word clause line para page  other")
for i, c in enumerate(raw):
    cn = Counter(marks(c)); r = sum(ch in RUNE_IDX for ch in c)
    other = {k: v for k, v in cn.items() if k not in "-./&%"}
    print(f"0.{i:<2} {r:6d} " + " ".join(f"{cn[k]:5d}" for k in "-./&%") + f"  {other or ''}")
print("LP2 only (0.7-0.15) positions of rare marks (rune index in section):")
for i in range(7, 16):
    ri = 0
    for ch in raw[i]:
        if ch in RUNE_IDX: ri += 1
        elif ch in "&%" or (ch not in "-./\n"): print(f"  0.{i} {ch!r}@{ri}", end="")
    print()

random.seed(53)
pairs = [("&", "%"), ("%", "&"), ("&", "&"), (".", "&")]
print("\npair stats per section: equal / nested / alternating / maxdepth  (real vs null P of >= as good, 1000 shuffles)")
for a, b in [("&", "%"), ("%", "&")]:
    for lo, hi, name in [(0, 7, "solved 0.0-0.6"), (7, 16, "LP2 0.7-0.15")]:
        eq = ne = al = 0; tot = 0
        pe = pn = pa = 0
        for i in range(lo, hi):
            m = marks(raw[i])
            if a not in m or b not in m: continue
            tot += 1; e, n, l, _ = stats(m, a, b); eq += e; ne += n; al += l
            sub = [x for x in m if x in (a, b)]
            for _ in range(1000):
                random.shuffle(sub); e2, n2, l2, _ = stats(sub, a, b)
                pe += e2 >= e; pn += n2 >= n; pa += l2 >= l
        print(f"open {a!r} close {b!r} {name}: sections with both {tot}, equal {eq}, nested {ne}, alternating {al}; "
              f"null mean frac equal {pe/1000/max(tot,1):.2f}, nested {pn/1000/max(tot,1):.2f}, alt {pa/1000/max(tot,1):.2f}")
