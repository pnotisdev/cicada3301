# Plain-text window (300 runes of the solved Welcome plaintext) for the staggered-screen plant control.
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lp

segs = lp.load_segments()
full_plain = lp.KNOWN[1][1](lp.runes_of(segs[1]))
plain = full_plain[:300]
# truncate the token stream to the first 300 runes
toks = []
k = 0
for t in segs[1]:
    if isinstance(t, int):
        if k >= 300:
            break
        toks.append(t)
        k += 1
    else:
        toks.append(t)
spans = lp.word_spans(toks, plain)
lens = []
for _w, s, e in spans:
    cs, ce = max(s, 0), min(e, 300)
    if ce > cs:
        lens.append(ce - cs)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stag_plain.txt")
with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write("W welcome300 -1\n")
    f.write("R " + " ".join(map(str, plain)) + "\n")
    f.write("L " + " ".join(map(str, lens)) + "\n")
print(f"wrote {out}: {len(plain)} runes, {len(lens)} words, plaintext IoC {lp.ioc(plain):.3f}")
