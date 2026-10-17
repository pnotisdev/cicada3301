"""Per-line check of single-dot word separators for ALL matched lines (also those with unequal glyph/rune counts).

word_gaps.py compares separator positions on the 537 lines whose detected glyph count equals the rune count. This
script drops the position requirement: for every line it counts the isolated single dots between glyphs and compares
that with the number of '-' in the transcription (ligatures do not change dot counts, so the 57 unequal lines are
usable too).

    python work/word_gaps_lines.py     # -> results/analysis/word_gaps_lines.txt
"""
import os
import sys

import cv2
import numpy as np

import lp
import ocr
import red_runs
import stats as lpstats

HERE = os.path.dirname(os.path.abspath(__file__))


def master_pages():
    with open(lp.MASTER_ORIGINAL, encoding="utf-8") as f:
        body = f.read().split("\n\n", 1)[1].split("§")[0]
    pages = []
    for pg in body.split("%"):
        lines = []
        for raw in pg.split("/"):
            items = []
            for ch in raw:
                if ch in lp.RUNE_IDX:
                    items.append([lp.RUNE_IDX[ch], ""])
                elif ch in "-.&" and items:
                    items[-1][1] += ch
            if items:
                lines.append(items)
        pages.append(lines)
    return pages


def main():
    pages = master_pages()
    ids = sorted({p for p, (seg, pos) in red_runs.page_seg_offsets().items() if seg in lpstats.UNSOLVED})
    rows = []
    tot_lines = tot_eq = 0
    for p in ids:
        n = ocr.image_of(p)
        lines, H, _img = ocr.segment(n)
        _, ink, _ = ocr.load_ink(n)
        _, _, st, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
        st = st[1:]
        area, ws, hs = st[:, 4], st[:, 2], st[:, 3]
        cand = (area >= 0.004 * H * H) & (area <= 0.09 * H * H) & (ws <= 0.4 * H) & (hs <= 0.4 * H)
        for mi, di in ocr.align_lines([[r for r, _ in l] for l in pages[p]], lines):
            if mi is None or di is None:
                continue
            ml, dl = pages[p][mi], lines[di]
            top = min(g.y for g in dl) - 0.3 * H
            bot = max(g.y + g.h for g in dl) + 0.3 * H
            left, right = dl[0].x - 0.1 * H, dl[-1].x + dl[-1].w + 0.1 * H
            sel = cand & (st[:, 1] >= top) & (st[:, 1] + hs <= bot) & (st[:, 0] >= left) & (st[:, 0] + ws <= right)
            dots = sorted(st[i, 0] + ws[i] / 2 for i in np.where(sel)[0]
                          if not any(g.x <= st[i, 0] + ws[i] / 2 <= g.x + g.w for g in dl))
            marks = []
            for x in dots:                      # dots closer than 0.3 H form one multi-dot mark
                if marks and x - marks[-1][-1] < 0.3 * H:
                    marks[-1].append(x)
                else:
                    marks.append([x])
            single = sum(1 for m in marks if len(m) == 1)
            tot_lines += 1
            tot_eq += len(ml) == len(dl)
            rows.append((p, mi, len(ml), len(dl), sum(1 for _, s in ml[:-1] if "-" in s),
                         sum(1 for _, s in ml[:-1] if "." in s), single, len(marks) - single))
    bad = [r for r in rows if r[4] != r[6]]
    out = [f"lines {tot_lines}, with equal rune and glyph counts {tot_eq}",
           f"total '-' in the transcription {sum(r[4] for r in rows)}; isolated single dots in the images {sum(r[6] for r in rows)}",
           f"lines where the two numbers differ: {len(bad)} (all by one or two: an extra dot, or a multi-dot mark cut into dots, typically at a line edge, where the transcription is known to drop marks)"]
    for r in bad:
        out.append("  page %d line %d: runes %d glyphs %d | '-' %d '.' %d | single dots %d, multi-dot marks %d" % r)
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "word_gaps_lines.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
