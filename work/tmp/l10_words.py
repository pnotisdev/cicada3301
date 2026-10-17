import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lp, stats
rows = []
for i in stats.UNSOLVED:
    c = lp.runes_of(stats.SEGS[i])
    for _, a, b in lp.word_spans(stats.SEGS[i], c):
        w = c[a:b]
        if len(w) == 10:
            co = [j for j in range(5) if w[j] == w[j + 5]]
            rows.append((i, a, w, co))
print(len(rows), "words of 10 runes;", sum(1 for r in rows if r[3]), "with a lag-5 coincidence")
for i, a, w, co in rows:
    if co:
        print(f"seg {i:2d} pos {a:5d}", " ".join(f"{x:2d}" for x in w), "  ", "".join(lp.LATIN[x] + "." for x in w), " coincide at j =", co)
