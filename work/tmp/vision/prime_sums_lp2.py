"""Scouting: are the Gematria sums of LP2's CIPHERTEXT words / clauses / lines / paragraphs / pages prime more often than
chance? Null: same unit lengths filled with a random permutation of the section's own runes (500 shuffles). Own code."""
import os, sys, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..")); sys.path.insert(0, os.path.join(HERE, "..", ".."))
import lp
def sieve(n):
    s = bytearray([1]) * (n + 1); s[0:2] = b"\x00\x00"
    for i in range(2, int(n ** 0.5) + 1):
        if s[i]: s[i * i::i] = bytearray(len(s[i * i::i]))
    return s
IS_P = sieve(300000)
segs = lp.load_segments()
random.seed(2901)
def units(toks, kind):
    out, cur = [], []
    def flush():
        nonlocal cur
        if cur: out.append(cur)
        cur = []
    for t in toks:
        if isinstance(t, int): cur.append(t)
        elif t == " ":
            if kind == "word": flush()
        elif t == ".":
            if kind in ("word", "clause"): flush()
        elif t == "&":
            if kind in ("word", "clause", "para"): flush()
        elif t == "%":
            if kind in ("word", "clause", "para", "page"): flush() if kind != "clause" else None
        elif t == "\n":
            if kind == "line": flush()
    flush()
    return out
tot = {}
print(f"{'sec':5s}{'unit':8s}{'n':>6s}{'prime':>7s}{'obs%':>7s}{'null%':>8s}{'z':>7s}")
for i in range(7, 16):
    if i == 10: continue
    toks = segs[i]; r = lp.runes_of(toks)
    for kind in ("word", "clause", "line", "para", "page"):
        U = units(toks, kind)
        if kind == "word": U = [u for u in U if len(u) >= 2]
        if len(U) < 3: continue
        lens = [len(u) for u in U]
        obs = sum(IS_P[sum(lp.PRIME[j] for j in u)] for u in U)
        pool = list(r); nulls = []
        for _ in range(300):
            random.shuffle(pool); p = 0; k = 0
            for L in lens:
                p += IS_P[sum(lp.PRIME[j] for j in pool[k:k + L])]; k += L
            nulls.append(p)
        mu = sum(nulls) / len(nulls); var = sum((x - mu) ** 2 for x in nulls) / len(nulls)
        z = (obs - mu) / var ** .5 if var else 0
        if kind in ("clause", "para", "page") or abs(z) > 2:
            print(f"0.{i:<3d}{kind:8s}{len(U):6d}{obs:7d}{100*obs/len(U):7.1f}{100*mu/len(U):8.1f}{z:7.2f}")
        t = tot.setdefault(kind, [0, 0, 0.0, 0.0]); t[0] += len(U); t[1] += obs; t[2] += mu; t[3] += var
print("--- pooled over LP2 (ciphertext)")
for kind, (n, o, mu, var) in tot.items():
    print(f"{kind:8s} n={n:5d} prime={o:5d} ({100*o/n:5.1f}%)  null {100*mu/n:5.1f}%  z={(o-mu)/var**.5:6.2f}")
