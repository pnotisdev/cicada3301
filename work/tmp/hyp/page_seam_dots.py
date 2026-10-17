"""Image check of the LP2 page seams (work/log/research_cicadanotebook_2026-10-17.md, section 4.1).

The transcription writes a word boundary at a line or page end as '-' or '.', either after the last rune of the line or before the
first rune of the next one; a bare break is a wrap inside a word. 32 of the 56 page breaks in LP2 carry no mark, and our word
splitter (lp.word_spans) treated them as boundaries. Question: do the page images show a separator dot at those 32 seams?

Detector: separator-sized ink components (the size rule of work/word_gaps.py) within 1.2 rune heights after the last glyph of a
line, or before the first glyph of the next line. Calibration on the same geometry: every line end inside the LP2 pages, marked
(a dot must be found on the marked side) and unmarked (no dot expected).

    python work/tmp/hyp/page_seam_dots.py   -> results/analysis/page_seams_2026-10-17.txt
"""
import os
import sys

import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.path.join(HERE, "..", ".."))
REPO = os.path.dirname(WORK)
sys.path.insert(0, WORK)
import lp  # noqa: E402
import ocr  # noqa: E402
import red_runs  # noqa: E402
import stats as lpstats  # noqa: E402
from word_gaps import master_lines  # noqa: E402

OUT = os.path.join(REPO, "results", "analysis", "page_seams_2026-10-17.txt")


def marked_lines():
    """page -> [(rune count, marks before the first rune, marks after the last rune)] per line, from lp.MASTER"""
    with open(lp.MASTER, encoding="utf-8") as f:
        body = f.read().split("\n\n", 1)[1].split("§")[0]
    out = []
    for pg in body.split("%"):
        lines = []
        for raw in pg.split("/"):
            idx = [k for k, c in enumerate(raw) if c in lp.RUNE_IDX]
            if idx:
                lines.append((len(idx), raw[:idx[0]], raw[idx[-1] + 1:]))
            elif lines:                           # a rune-less chunk (paragraph / segment marks) belongs to the line before
                n, lead, trail = lines[-1]
                lines[-1] = (n, lead, trail + "/" + raw)
        out.append(lines)
    return out


def boundary(marks):
    return "-" in marks or "." in marks


def seps_near(glyph_line, st, H, x_lo, x_hi):
    """separator-sized components centred in (x_lo, x_hi) inside the line's vertical band (size rule of word_gaps.dots_between)"""
    xs, ys, ws, hs, area = st[:, 0], st[:, 1], st[:, 2], st[:, 3], st[:, 4]
    cand = (area >= 0.004 * H * H) & (area <= 0.09 * H * H) & (ws <= 0.4 * H) & (hs <= 0.4 * H)
    top = min(g.y for g in glyph_line) - 0.3 * H
    bot = max(g.y + g.h for g in glyph_line) + 0.3 * H
    cand &= (ys >= top) & (ys + hs <= bot)
    cx = xs + ws / 2
    return int((cand & (cx > x_lo) & (cx < x_hi)).sum())


def page_lines(p, mlines):
    """detected glyph lines of transcription page p, aligned to its transcription lines: [glyphs sorted by x or None]"""
    n = ocr.image_of(p)
    lines, H, _ = ocr.segment(n)
    _, ink, _ = ocr.load_ink(n)
    _, _, st, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    st = st[1:]
    al = [None] * len(mlines)
    for m, d in ocr.align_lines([[r for r, _ in l] for l in mlines], lines):
        if m is not None and d is not None:
            al[m] = sorted(lines[d], key=lambda g: g.x)
    return al, st, H


def dot_after(gl, st, H):
    last = gl[-1]
    return seps_near(gl, st, H, last.x + last.w - 0.05 * H, last.x + last.w + 1.2 * H)


def dot_before(gl, st, H):
    first = gl[0]
    return seps_near(gl, st, H, first.x - 1.2 * H, first.x + 0.05 * H)


def main():
    out = []

    def say(s=""):
        print(s)
        out.append(s)

    glyph_pages = master_lines()
    marks = marked_lines()
    offs = red_runs.page_seg_offsets()
    lp2 = [p for p in range(len(marks)) if offs[p][0] in lpstats.UNSOLVED]
    cache = {p: page_lines(p, glyph_pages[p]) for p in lp2 if glyph_pages[p]}

    # calibration: line ends inside a page; side = where the transcription puts the mark
    cal = {"trail": [0, 0], "lead": [0, 0], "none": [0, 0]}   # [seams measured, seams with a dot on the expected side / any side]
    for p, (al, st, H) in cache.items():
        ml = marks[p]
        if len(ml) != len(al):
            continue
        for m in range(len(ml) - 1):
            a, b = al[m], al[m + 1]
            if a is None or b is None:
                continue
            da, db = dot_after(a, st, H), dot_before(b, st, H)
            if boundary(ml[m][2]):
                cal["trail"][0] += 1
                cal["trail"][1] += da >= 1
            elif boundary(ml[m + 1][1]):
                cal["lead"][0] += 1
                cal["lead"][1] += db >= 1
            else:
                cal["none"][0] += 1
                cal["none"][1] += (da + db) >= 1
    say("Calibration on line ends inside the LP2 pages (same detector, same geometry):")
    say(f"   mark after the last rune      {cal['trail'][0]:4d} line ends, dot found after the last glyph at {cal['trail'][1]}")
    say(f"   mark before the next line     {cal['lead'][0]:4d} line ends, dot found before the next first glyph at {cal['lead'][1]}")
    say(f"   no mark (wrap inside a word)  {cal['none'][0]:4d} line ends, dot found on either side at {cal['none'][1]}")
    say()

    rows = []
    for p in lp2:
        q = p + 1
        if p not in cache or q not in cache:
            rows.append((p, "not measured (no runes on one side or end of LP2)", None, None))
            continue
        trail, lead = marks[p][-1][2], marks[q][0][1]
        kind = "trail" if boundary(trail) else ("lead" if boundary(lead) else "none")
        a, b = cache[p][0][-1], cache[q][0][0]
        da = dot_after(a, *cache[p][1:]) if a is not None else None
        db = dot_before(b, *cache[q][1:]) if b is not None else None
        rows.append((p, kind, da, db))
    say("LP2 page breaks (transcription page p -> p+1; image = p + 2):")
    for kind, name in (("trail", "mark after the last rune of the page"), ("lead", "mark before the first rune of the next page"),
                       ("none", "no mark (the 32 seams in question)")):
        sel = [r for r in rows if r[1] == kind]
        da = sum(1 for r in sel if r[2] is not None and r[2] >= 1)
        db = sum(1 for r in sel if r[3] is not None and r[3] >= 1)
        say(f"   {name:45s} {len(sel):3d}: dot after the last glyph at {da}, dot before the next page's first glyph at {db}")
    skipped = [r[0] for r in rows if r[2] is None and r[3] is None]
    say(f"   not measured: pages {skipped} (64 -> 65 and 65 -> 66 border the rune-less number-square page; 70 is the end of LP2)")
    seams = [r for r in rows if r[1] == "none"]
    say(f"   the unmarked seams: transcription pages {[r[0] for r in seams]}")
    odd = [r for r in rows if (r[1] == "none" and ((r[2] or 0) + (r[3] or 0)) >= 1)
           or (r[1] == "trail" and not r[2]) or (r[1] == "lead" and not r[3])]
    say(f"   disagreements with the transcription: {odd if odd else 'none'}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("# work/tmp/hyp/page_seam_dots.py: separator dots at LP2 line and page ends (page images vs transcription)\n")
        f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
