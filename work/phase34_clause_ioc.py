"""Tiny 1-core check for phase 34: is a per-clause constant shift (clause key = f(the clause's numbers)) visible as excess within-clause IoC?
A key that is constant over a clause of length m leaves c = p + K: the clause IoC equals the plaintext IoC (about 1.7), far above the 1.0 of a running key.
Null: the same clause lengths filled by shuffling all runes of the section (keeps unigram counts). Clauses of >= 25 runes, segments 0.7-0.15."""
import random, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lp, stats

def ioc(r):
    n = len(r); c = [0] * 29
    for x in r: c[x] += 1
    return 29 * sum(v * (v - 1) for v in c) / (n * (n - 1))

rng = random.Random(34)
obs, nul, allr = [], [], []
for seg in range(7, 16):
    toks = stats.SEGS[seg]
    cl, cur = [], []
    for t in toks:
        if isinstance(t, int): cur.append(t)
        elif t == "." and cur: cl.append(cur); cur = []
    if cur: cl.append(cur)
    cl = [c for c in cl if len(c) >= 25]
    if not cl:
        print(f'segment {seg}: no clause of >= 25 runes'); continue
    flat = [x for c in cl for x in c]
    for rep in range(200):
        s = flat[:]; rng.shuffle(s); i = 0; m = []
        for c in cl:
            m.append(ioc(s[i:i + len(c)])); i += len(c)
        nul.append(sum(m) / len(m))
    if cl: obs.append(sum(ioc(c) for c in cl) / len(cl)); allr.append(len(cl))
    print(f"segment {seg}: {len(cl)} clauses >= 25 runes, mean within-clause IoC {obs[-1]:.4f}; shuffle null mean {sum(nul[-200:])/200:.4f} sd {(sum((x-sum(nul[-200:])/200)**2 for x in nul[-200:])/200)**.5:.4f}")
