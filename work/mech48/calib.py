"""Phase 48 step 1: one-rune words in solved plaintext and in LP2 ciphertext (independent of lp_verify.py)."""
import sys, math, collections
sys.path.insert(0, "work")
import lp
segs = lp.load_segments()
def one_rune(toks, plain):
    return [(a, lp.LATIN[plain[a]]) for w, a, b in lp.word_spans(toks, plain) if b - a == 1]
det, vig = [0, 2, 3, 4, 6, 17, 16 if False else 0], None
rows = []
for i, (title, f) in lp.KNOWN.items():
    c = lp.runes_of(segs[i]); p = f(c)
    kind = "vigenere" if i in (1, 5, 16) else "deterministic"
    ow = one_rune(segs[i], p)
    cnt = collections.Counter(v for _, v in ow)
    rows.append((i, title, kind, len(c), len(ow), cnt))
    print(i, title, kind, len(c), "one-rune words", len(ow), dict(cnt))
def wilson(k, n, z=1.96):
    if n == 0: return (0, 0)
    ph = k / n; d = 1 + z * z / n
    m = (ph + z * z / (2 * n)) / d; h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return m - h, m + h
for kind in ("deterministic", "vigenere", None):
    sel = [r for r in rows if kind is None or r[2] == kind]
    n = sum(r[4] for r in sel); k = sum(r[5]["A"] + r[5]["I"] for r in sel)
    print(kind or "all", f"{k}/{n}", f"{k/n:.3f}" if n else "", "Wilson95 %.3f-%.3f" % wilson(k, n))
# LP2
print("LP2 one-rune words (ciphertext rune, global rune index, segment, index in segment, page-safe cut):")
tot = 0; ct = collections.Counter(); lst = []
for i in range(7, 16):
    c = lp.runes_of(segs[i])
    for w, a, b in lp.word_spans(segs[i], c):
        if b - a == 1:
            tot += 1; ct[lp.LATIN[c[a]]] += 1; lst.append((i, a, lp.LATIN[c[a]]))
print("total", tot, dict(ct))
per = collections.Counter(s for s, _, _ in lst); print("per segment", dict(per))
print("list", " ".join(f"{s}:{a}:{r}" for s, a, r in lst))
