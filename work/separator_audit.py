"""Audit of the transcription's separator layer against the page images.

Phase 2 verified the runes. The separators ('-' word dot, '.' clause mark) were never checked, yet every word-scoped
statistic (word lengths, the dictionary screens, the seed sweeps' scoring, dsearch) rests on them. aldegonde reports
separators visible in the images but missing from the transcription.

For every unsolved image, lines are segmented with ocr.segment(); a transcription line is paired with a detected line
when their glyph counts are equal (otherwise the line is skipped, as in the rune audit); for each gap between
consecutive runes the ink between the two glyph boxes (at the height of the glyph centre band) is measured:
  none          -> no separator
  one small blob -> word dot
  several blobs / a larger mark -> clause mark
and compared with the transcription's separator after that rune.

    python work/separator_audit.py [image ...]       # default: images 15..70
"""
import os
import sys
from collections import Counter

import cv2
import numpy as np

import lp
import ocr
import red_runs

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_DOT = 40
TICK = (355, 370)          # the tick glyph is a pixel-identical stamp of ~362 px (contraction ticks / quote marks)


def transcription_lines(page):
    """List of lines; each a list of (rune, sep) where sep is '' (none), '-' (word) or '.' (clause) after the rune."""
    body = open(lp.MASTER_ORIGINAL, encoding="utf-8").read().split("\n\n", 1)[1].split("§")[0]
    p = body.split("%")[page]
    out = []
    for line in p.split("/"):
        items = []
        for ch in line:
            if ch in lp.RUNE_IDX:
                items.append([lp.RUNE_IDX[ch], ""])
            elif ch in "-." and items and not items[-1][1]:
                items[-1][1] = ch
        if items:
            out.append([(r, s) for r, s in items])
    return out


def gap_marks(ink, a, b, H):
    """Blob areas between glyph a (left) and glyph b (right) in the centre band of the line."""
    x0, x1 = a.x + a.w, b.x
    if x1 - x0 < 3:
        return None                                   # boxes touch or overlap: cannot tell
    yc = (a.y + a.h / 2 + b.y + b.h / 2) / 2
    y0, y1 = int(yc - 0.55 * H), int(yc + 0.55 * H)
    roi = ink[max(y0, 0):y1, x0:x1]
    n, _, st, _ = cv2.connectedComponentsWithStats(roi, connectivity=8)
    return sorted(int(s[4]) for s in st[1:])


def audit(images):
    """-> (tally, disagreements, ticks) for the given image numbers (writes nothing)."""
    tally = Counter()
    rows, ticks = [], []
    pages = ocr.master_pages(lp.MASTER_ORIGINAL)
    offsets = red_runs.page_seg_offsets()
    for page_idx in range(len(pages)):
        n = ocr.image_of(page_idx)
        if n not in images:
            continue
        lines, H, img = ocr.segment(n)
        _, ink, _ = ocr.load_ink(n)
        tl = transcription_lines(page_idx)
        pairs = ocr.align_lines([[r for r, _ in l] for l in tl], lines)
        for mi, di in pairs:
            if mi is None or di is None or len(tl[mi]) != len(lines[di]):
                continue
            seps = [s for _, s in tl[mi]]
            glyphs = lines[di]
            for k in range(len(glyphs) - 1):
                marks = gap_marks(ink, glyphs[k], glyphs[k + 1], H)
                if marks is None:
                    tally["unmeasurable"] += 1
                    continue
                big = [a for a in marks if a >= MIN_DOT]            # the printed dot is ~80-100 px; JPEG noise is a few px
                seen = "none" if not big else ("word" if len(big) == 1 else "clause")
                tr = {"": "none", "-": "word", ".": "clause"}[seps[k]]
                tally[(tr, seen)] += 1
                if tr != seen:
                    rows.append((n, mi, k, tr, seen, marks))
                nt = sum(TICK[0] <= a <= TICK[1] for a in marks)
                if nt:
                    seg, base = offsets[page_idx]
                    ticks.append((n, mi, k, seg, base + sum(len(l) for l in tl[:mi]) + k + 1, nt, tr))
    return tally, rows, ticks


def main():
    full = not sys.argv[1:]
    images = [int(x) for x in sys.argv[1:]] or list(range(15, 71))
    tally, rows, ticks = audit(images)
    out = []
    P = out.append
    P(f"images {images[0]}..{images[-1]}; {sum(v for k, v in tally.items() if k != 'unmeasurable')} measured gaps, "
      f"{tally['unmeasurable']} unmeasurable")
    P("transcription (rows) against image (columns):     none     word   clause")
    for tr in ("none", "word", "clause"):
        P(f"  {tr:8s}            " + " ".join(f"{tally[(tr, s)]:8d}" for s in ("none", "word", "clause")))
    P("")
    P("disagreements: image, line, gap, transcription, image, blob areas (a ~362 px blob is the tick glyph)")
    for r in rows:
        P("  " + " ".join(map(str, r)))
    text = "\n".join(out)
    print(text)
    if not full:
        return
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "separator_audit.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write(text + "\n")
    with open(os.path.join(HERE, "ref", "tick_marks.tsv"), "w", newline="\n", encoding="utf-8") as f:
        f.write("# raised tick glyphs in the page images that the transcription lacks (separator_audit.py)\n"
                "# a lone tick inside a word = apostrophe; two ticks next to a separator = quotation marks\n"
                "image\tline\tgap_after_rune_k\tsegment\tindex_in_segment\tticks\ttranscription_separator\n")
        for t in ticks:
            f.write("\t".join(map(str, t)) + "\n")
    print(f"{len(ticks)} tick-bearing gaps written to work/ref/tick_marks.tsv")


if __name__ == "__main__":
    sys.exit(main())
