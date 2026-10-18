# How often do the words DJU and BEI occur, and does BEI follow DJU anywhere else?
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lp

segs = lp.load_segments()
words = []
for i in range(7, 16):
    toks = segs[i]
    runes = lp.runes_of(toks)
    for w, s, e in lp.word_spans(toks, runes):
        words.append((i, w, s, e))

dju = [(i, s) for i, w, s, e in words if w == "DJU"]
bei = [(i, s) for i, w, s, e in words if w == "BEI"]
pairs = [(i, s) for n, (i, w, s, e) in enumerate(words) if w == "DJU" and n + 1 < len(words) and words[n + 1][1] == "BEI"]
print(f"DJU occurrences: {len(dju)} -> {dju}")
print(f"BEI occurrences: {len(bei)} -> {bei}")
print(f"DJU followed by BEI: {len(pairs)} -> {pairs}")
# how many 3-rune words total, and the pair repetition rate for 3-rune words generally
triples = {}
for i, w, s, e in words:
    if len(w) == 3:
        triples.setdefault(w, []).append((i, s))
repeats = {w: v for w, v in triples.items() if len(v) > 1}
print(f"3-rune words: {sum(len(v) for v in triples.values())} types={len(triples)}; repeated 3-rune words: {len(repeats)}")
for w, v in sorted(repeats.items(), key=lambda kv: -len(kv[1]))[:10]:
    print(f"  {w}: {v}")
