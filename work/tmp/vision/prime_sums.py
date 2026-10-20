"""Scouting: are the Gematria sums of words / clauses / paragraphs / pages of the SOLVED plaintext prime more often
than chance? (Cicada builds its squares from word sums, so a sum constraint on plaintext units would be a design trait.)
Own code; null = same unit lengths filled by a random permutation of the section's own runes (1000 shuffles)."""
import os, sys, random, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import lp

def sieve(n):
    s = bytearray([1]) * (n + 1); s[0:2] = b"\x00\x00"
    for i in range(2, int(n ** 0.5) + 1):
        if s[i]:
            s[i * i::i] = bytearray(len(s[i * i::i]))
    return s
IS_P = sieve(200000)

segs = lp.load_segments()
random.seed(3301)

def units(toks, plain, kind):
    """list of lists of plain rune indices for each unit of the given kind"""
    it = iter(plain)
    out, cur = [], []
    def flush():
        nonlocal cur
        if cur:
            out.append(cur)
        cur = []
    for t in toks:
        if isinstance(t, int):
            cur.append(next(it))
        elif t == " ":
            if kind == "word":
                flush()
        elif t == ".":
            if kind in ("word", "clause"):
                flush()
        elif t in ("&", "%"):
            if kind in ("word", "clause", "para"):
                flush()
            if kind == "page" and t == "%":
                flush()
        elif t == "\n":
            if kind == "line":
                flush()
    flush()
    return out

def psum(u):
    return sum(lp.PRIME[i] for i in u)

print(f"{'sec':5s}{'unit':7s}{'n':>5s}{'prime':>7s}{'obs%':>7s}{'null%':>8s}{'z':>7s}")
tot = {}
for i, (title, fn) in lp.KNOWN.items():
    r = lp.runes_of(segs[i])
    plain = fn(r)
    for kind in ("word", "clause", "para", "line"):
        U = units(segs[i], plain, kind)
        # for words ignore 1-rune words (a single rune is prime by definition)
        if kind == "word":
            U = [u for u in U if len(u) >= 2]
        if len(U) < 3:
            continue
        obs = sum(IS_P[psum(u)] for u in U)
        lens = [len(u) for u in U]
        pool = list(plain)
        nulls = []
        for _ in range(400):
            random.shuffle(pool)
            p = 0; k = 0
            for L in lens:
                p += IS_P[sum(lp.PRIME[j] for j in pool[k:k + L])]; k += L
            nulls.append(p)
        mu = sum(nulls) / len(nulls); sd = (sum((x - mu) ** 2 for x in nulls) / len(nulls)) ** .5
        z = (obs - mu) / sd if sd else 0
        print(f"0.{i:<3d}{kind:7s}{len(U):5d}{obs:7d}{100*obs/len(U):7.1f}{100*mu/len(U):8.1f}{z:7.2f}")
        t = tot.setdefault(kind, [0, 0, 0.0, 0.0]); t[0] += len(U); t[1] += obs; t[2] += mu; t[3] += sd ** 2
print("--- pooled over all solved sections")
for kind, (n, o, mu, var) in tot.items():
    print(f"{kind:7s} n={n:5d} prime={o:5d} ({100*o/n:5.1f}%)  null {100*mu/n:5.1f}%  z={(o-mu)/var**.5:6.2f}")
