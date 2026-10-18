# Section-edge words: do LP2 sections share first/last words? (DJU-BEI is the book's final pair;
# a per-word or per-section key convention might show edge structure.)
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lp

segs = lp.load_segments()
print("first 6 and last 6 words of each LP2 section:")
edges = []
for i in range(7, 16):
    toks = segs[i]
    runes = lp.runes_of(toks)
    ws = [w for w, s, e in lp.word_spans(toks, runes)]
    print(f"  0.{i}: head {' '.join(ws[:6]):30s} | tail {' '.join(ws[-6:]):30s}")
    edges.append((ws[:6], ws[-6:]))
# repeats among section heads / tails
from collections import Counter
heads = Counter(w for h, t in edges for w in h)
tails = Counter(w for h, t in edges for w in t)
print("\nwords appearing in >= 2 section heads:", {w: c for w, c in heads.items() if c >= 2})
print("words appearing in >= 2 section tails:", {w: c for w, c in tails.items() if c >= 2})
# is DJU at the same ordinal position in both sections? (0.13 word 6, 0.15 word 734)
