import sys
sys.path.insert(0, ".")
import lp
segs = lp.load_segments()
pages = []
cur = []
for si, toks in enumerate(segs):
    for t in toks:
        if isinstance(t, int):
            cur.append(t)
        elif t == "%":
            pages.append((si, cur)); cur = []
    pages.append((si, cur)); cur = []
idx = {n: i for i, n in enumerate(lp.LATIN)}
def find(seq):
    for k, (si, r) in enumerate(pages):
        for p in range(len(r) - len(seq) + 1):
            if r[p:p+len(seq)] == seq:
                print("piece", k, "seg", si, "at", p, "of", len(r), "ctx", [lp.LATIN[x] for x in r[max(0,p-9):p+len(seq)+16]])
for name, seq in (("DJUBEI", ["D","J","U","B","E","I"]), ("OFLOENG", ["O","F","L","OE","ING"])):
    print(name)
    find([idx[x] for x in seq])
p = pages[60][1]
print(len(p), "piece60 first 11:", [lp.LATIN[x] for x in p[:11]], sum(lp.PRIME[x] for x in p[:11]), "col1", sum(lp.PRIME[p[i]] for i in range(0,121,11)), "total", sum(lp.PRIME[x] for x in p))
p = pages[85][1]
print(len(p), sorted(set(lp.LATIN) - set(lp.LATIN[x] for x in p)), "total", sum(lp.PRIME[x] for x in p))
