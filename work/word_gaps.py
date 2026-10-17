"""Are LP2's word boundaries in the transcription the ones printed on the pages?

The book separates words with a small mid-height dot (and clauses with a different mark). Phase 2 verified every rune
against the page images, but the word separators of the community transcription ('-' in lp_master.txt) were not
checked, and every word-length statistic (2,928 words, the missing 2-rune words) depends on them. This script finds the
separator dots in the images (small connected components between consecutive rune glyphs) and compares them with the
transcription, line by line, for every line whose detected glyph count equals its rune count.

    python work/word_gaps.py        # -> results/analysis/word_gaps.txt, work/tmp/word_gaps/ (mismatch crops)
"""
import os
import sys
from collections import Counter

import cv2
import numpy as np

import lp
import ocr
import red_runs
import stats as lpstats

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, "tmp", "word_gaps")


def master_lines():
    """page -> list of lines; each line is a list of (rune, separator_after) where separator is '' | '-' | '.' | other"""
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


def dots_between(glyphs, stats_cc, H):
    """number of separator-sized components between each pair of consecutive glyphs"""
    out = []
    xs = stats_cc[:, 0]
    ws = stats_cc[:, 2]
    hs = stats_cc[:, 3]
    area = stats_cc[:, 4]
    ys = stats_cc[:, 1]
    cand = (area >= 0.004 * H * H) & (area <= 0.09 * H * H) & (ws <= 0.4 * H) & (hs <= 0.4 * H)
    top = min(g.y for g in glyphs) - 0.3 * H
    bot = max(g.y + g.h for g in glyphs) + 0.3 * H
    cand &= (ys >= top) & (ys + hs <= bot)
    ci = np.where(cand)[0]
    cx = xs[ci] + ws[ci] / 2
    for a, b in zip(glyphs, glyphs[1:]):
        lo, hi = a.x + a.w, b.x
        out.append(int(((cx > lo - 0.05 * H) & (cx < hi + 0.05 * H)).sum()))
    return out


def main():
    os.makedirs(TMP, exist_ok=True)
    pages = master_lines()
    page_ids = sorted({p for p, (seg, pos) in red_runs.page_seg_offsets().items() if seg in lpstats.UNSOLVED})
    conf = Counter()
    gap_sizes = {"-": [], "": [], ".": []}
    mism = []
    n_lines = n_used = 0
    for p in page_ids:
        n = ocr.image_of(p)
        lines, H, img = ocr.segment(n)
        _, ink, _ = ocr.load_ink(n)
        _, _, st, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
        st = st[1:]
        mlines = pages[p]
        pairs = ocr.align_lines([[r for r, _ in l] for l in mlines], lines)
        for mi, di in pairs:
            if mi is None or di is None:
                continue
            n_lines += 1
            ml, dl = mlines[mi], lines[di]
            if len(ml) != len(dl):
                continue
            n_used += 1
            dots = dots_between(dl, st, H)
            for k, d in enumerate(dots):
                sep = ml[k][1]
                kind = "-" if "-" in sep else ("." if "." in sep else "")
                gap = (dl[k + 1].x - (dl[k].x + dl[k].w)) / H
                gap_sizes[kind].append(gap)
                conf[(kind, min(d, 2))] += 1
                if (kind == "" and d >= 1) or (kind != "" and d == 0):
                    mism.append((p, mi, k, kind, d, round(gap, 2)))
    out = []
    P = out.append
    P(f"{len(page_ids)} pages, {n_lines} matched lines, {n_used} with equal rune and glyph counts.")
    P("transcription separator vs dots found between the two glyphs (rows: transcription; columns: 0, 1, 2+ dots):")
    for kind, name in (("", "no separator"), ("-", "word '-'"), (".", "clause '.'")):
        row = [conf[(kind, d)] for d in (0, 1, 2)]
        tot = sum(row)
        P(f"   {name:14s} {row[0]:6d} {row[1]:6d} {row[2]:6d}   ({tot} gaps)")
    for kind in ("", "-", "."):
        g = np.array(gap_sizes[kind])
        if len(g):
            P(f"   gap width / rune height, {('none' if kind == '' else kind):>4s}: mean {g.mean():.2f}, p5 {np.percentile(g, 5):.2f}, "
              f"p95 {np.percentile(g, 95):.2f}")
    bad_missing = [m for m in mism if m[3] != "" and m[4] == 0]
    bad_extra = [m for m in mism if m[3] == "" and m[4] >= 1]
    P("")
    P(f"transcribed boundary without a dot: {len(bad_missing)}; dot where the transcription has none: {len(bad_extra)}")
    for m in (bad_extra + bad_missing)[:40]:
        P(f"   page {m[0]} line {m[1]} after rune {m[2]}: transcription {m[3] or 'none'!r}, dots {m[4]}, gap {m[5]}")
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "word_gaps.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
