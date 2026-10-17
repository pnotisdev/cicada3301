import sys
sys.path.insert(0, "..")
sys.path.insert(0, ".")
import lp
segs = lp.load_segments()
pages = []   # (seg index, page-in-seg, runes)
cur = []
for si, toks in enumerate(segs):
    for t in toks:
        if isinstance(t, int):
            cur.append(t)
        elif t == "%":
            pages.append((si, cur)); cur = []
    pages.append((si, cur)); cur = []
print(len(segs), "segments;", len(pages), "page pieces")
for k, (si, r) in enumerate(pages):
    print(k, "seg", si, len(r), "".join(lp.LATIN[x] + " " for x in r[:6]))
