# Staggered 300-rune windows for the kscreen library screen (audit assumption D test, phase11).
# Writes work/kscreen/data/staggered.txt in the engine's windows-file format
# (W <name> <prev_rune> / R <runes> / L <word lengths>), 12 windows at mid-section offsets.
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lp

segs = lp.load_segments()
N = 29
WIN = 300

windows = []  # (name, prev, runes300, word_lengths)
for i in range(7, 16):
    toks = segs[i]
    runes = lp.runes_of(toks)
    if len(runes) < WIN + 60:
        continue
    spans = lp.word_spans(toks, runes)  # [(word, s, e)]
    offsets = sorted({len(runes) // 3, len(runes) // 2, (2 * len(runes)) // 3, len(runes) - WIN})
    for o in offsets:
        if o <= 0 or o + WIN > len(runes):
            continue
        prev = runes[o - 1] if o > 0 else -1
        seg = runes[o:o + WIN]
        lens = []
        for _w, s, e in spans:
            cs, ce = max(s, o), min(e, o + WIN)
            if ce > cs:
                lens.append(ce - cs)
        windows.append((f"stag0.{i}@{o}", prev, seg, lens))

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kscreen", "data", "staggered.txt")
with open(out, "w", encoding="utf-8", newline="\n") as f:
    for name, prev, seg, lens in windows:
        f.write(f"W {name} {prev}\n")
        f.write("R " + " ".join(map(str, seg)) + "\n")
        f.write("L " + " ".join(map(str, lens)) + "\n")
print(f"wrote {out}: {len(windows)} windows")
for name, prev, seg, lens in windows:
    print(f"  {name:12s} prev={prev} runes={len(seg)} words={len(lens)}")
