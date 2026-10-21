"""Phase 48 step 1b: one-rune count under three word-cut rules (page-safe = repo rule; line break = boundary; line+page = boundary)."""
import sys, collections
sys.path.insert(0, "work")
import lp
segs = lp.load_segments()
def spans(toks, WB):
    out, cur, pos, start = [], 0, 0, 0
    for t in toks + [" "]:
        if isinstance(t, int):
            if not cur: start = pos
            cur += 1; pos += 1
        elif t in ("\n", "%") and t not in WB:
            continue
        elif cur:
            out.append((start, pos)); cur = 0
    return out
for name, WB in (("page-safe", set()), ("line=boundary", {"\n"}), ("line+page=boundary", {"\n", "%"})):
    n2 = 0; solved = collections.Counter()
    for i in range(7, 16):
        n2 += sum(1 for a, b in spans(segs[i], WB) if b - a == 1)
    sn = sa = 0
    for i, (_, f) in lp.KNOWN.items():
        p = f(lp.runes_of(segs[i]))
        for a, b in spans(segs[i], WB):
            if b - a == 1:
                sn += 1; sa += lp.LATIN[p[a]] in ("A", "I")
    print(name, "LP2 one-rune words", n2, "| solved", f"{sa}/{sn}")
