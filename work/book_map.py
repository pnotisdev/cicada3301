"""Annotated map of the 75 page scans (work/orig/NN.jpg): one thumbnail per image, border colour = status of the text on it.

    python book_map.py        # writes figures/book_map.png

Section -> image mapping follows ocr.image_of (transcription page p is image p + 2, page 0 is image 1; images 0 and 2 are the
title and the chapter title). Flags come from work/log/phase9_art.md and work/log/research_2026-10-17.md (art, dots,
cuneiform numerals, the base-60 payload) and from work/page_scan_audit.py (scans that are containers).
"""
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(HERE, "orig")
OUT = os.path.join(HERE, "figures", "book_map.png")

# image number -> (section label, group)
GROUPS = {"title": (150, 150, 150), "enc": (200, 120, 30), "plain": (60, 160, 60), "lp2": (40, 90, 220), "end": (160, 60, 160)}
SECTIONS = [  # (first image, last image, label, group)
    (0, 0, "title", "title"), (1, 1, "0.0", "enc"), (2, 2, "ch.1", "title"), (3, 4, "0.1", "enc"), (5, 5, "0.2", "plain"),
    (6, 9, "0.3", "enc"), (10, 13, "0.4", "plain"), (14, 15, "0.5", "enc"), (16, 16, "0.6", "plain"),
    (17, 19, "0.7", "lp2"), (20, 24, "0.8", "lp2"), (25, 31, "0.9", "lp2"), (32, 32, "0.10", "lp2"), (33, 39, "0.11", "lp2"),
    (40, 43, "0.12", "lp2"), (44, 50, "0.13", "lp2"), (51, 56, "0.14", "lp2"), (57, 72, "0.15", "lp2"),
    (73, 73, "0.16", "end"), (74, 74, "0.17", "plain"),
]
FLAGS = {  # image -> short tags drawn under the thumbnail
    1: ["Atbash"], 3: ["Vig DIVINITY"], 5: ["grid 1033", "container"], 6: ["Atbash+3"], 10: ["container x4"], 14: ["Vig FIRFUM.."],
    16: ["grid 3301"], 24: ["5 dots"], 31: ["mayfly"], 32: ["4x4 grid", "caption 9"], 39: ["glyph+body"], 40: ["5 dots"],
    50: ["3 dots", "wedges"], 51: ["wedges", "red 1.."], 56: ["3 dots"], 66: ["base-60"], 67: ["base-60"], 68: ["base-60"],
    70: ["cicada"], 72: ["cicada"], 73: ["hash", "5 dots"], 74: ["stipple"],
}
COLS, TW, TH, GAP, LAB = 15, 150, 225, 10, 54


def group_of(n):
    for a, b, lab, g in SECTIONS:
        if a <= n <= b:
            return lab, g
    return "?", "title"


def main():
    rows = (75 + COLS - 1) // COLS
    W = COLS * (TW + GAP) + GAP
    H = 150 + rows * (TH + LAB + GAP) + GAP + 30
    canvas = np.full((H, W, 3), 255, np.uint8)
    cv2.putText(canvas, "Liber Primus: the 75 page scans, by section", (GAP, 46), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (20, 20, 20), 3, cv2.LINE_AA)
    legend = [("solved, encrypted", "enc"), ("solved, plain text", "plain"), ("LP2 (unsolved, 12,956 runes)", "lp2"),
              ("An End", "end"), ("title pages", "title")]
    x = GAP
    for text, g in legend:
        cv2.rectangle(canvas, (x, 70), (x + 30, 100), GROUPS[g], -1)
        cv2.putText(canvas, text, (x + 38, 94), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (30, 30, 30), 2, cv2.LINE_AA)
        x += 38 + 15 * len(text) + 40
    cv2.putText(canvas, "number = file NN.jpg, then section 0.x; tags: art and puzzle furniture (work/log/phase9_art.md); "
                "container = file holds extra data (work/page_scan_audit.py)", (GAP, 126), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (60, 60, 60), 1, cv2.LINE_AA)
    for n in range(75):
        r, c = divmod(n, COLS)
        x0 = GAP + c * (TW + GAP)
        y0 = 150 + GAP + r * (TH + LAB + GAP)
        img = cv2.imread(os.path.join(ORIG, f"{n:02d}.jpg"))
        th = cv2.resize(img, (TW, TH), interpolation=cv2.INTER_AREA)
        canvas[y0:y0 + TH, x0:x0 + TW] = th
        lab, g = group_of(n)
        col = GROUPS[g]
        cv2.rectangle(canvas, (x0 - 3, y0 - 3), (x0 + TW + 2, y0 + TH + 2), col, 5)
        cv2.putText(canvas, f"{n:02d}  {lab}", (x0, y0 + TH + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (20, 20, 20), 2, cv2.LINE_AA)
        for k, tag in enumerate(FLAGS.get(n, [])[:2]):
            cv2.putText(canvas, tag, (x0, y0 + TH + 38 + 15 * k), cv2.FONT_HERSHEY_SIMPLEX, 0.47, (0, 0, 150), 1, cv2.LINE_AA)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cv2.imwrite(OUT, canvas)
    print("wrote", os.path.relpath(OUT, os.path.dirname(HERE)), canvas.shape)


if __name__ == "__main__":
    main()
