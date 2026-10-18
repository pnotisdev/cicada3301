# Word structure around the two DJU-BEI occurrences (which span word seams).
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lp

segs = lp.load_segments()
for i, pos in ((13, 28), (15, 3310)):
    toks = segs[i]
    runes = lp.runes_of(toks)
    spans = lp.word_spans(toks, runes)
    print(f"section 0.{i}, DJU-BEI at rune pos {pos}; last 6 words:")
    for w, s, e in spans[-6:]:
        print(f"  [{s}:{e}] {w}")
    print("  words overlapping the 6-gram:")
    for w, s, e in spans:
        if s <= pos + 6 and pos < e:
            print(f"  [{s}:{e}] {w}  (6-gram inside: {w[pos-s:pos+6-s]})")
