"""Left-right asymmetries in the border art of the page images.

The margin ornaments (spirals, dot groups) are drawn mirror-symmetric about the page's centre line (x = 1199.5 on the
2400-px originals). A mark with no mirror partner is therefore not part of the decoration and a candidate carrier of
information. For every page image this script
  1. binarises the page and finds the text block (x-range of the rune components),
  2. mirrors the image about the centre line and takes the symmetric difference, after letting each pixel match a
     partner within +-TOL px (so anti-aliasing and 1-px drawing jitter do not count),
  3. lists the connected components of the difference outside the text block (area >= MIN_AREA).

    python work/ornament_dots.py                 # -> results/analysis/ornament_asymmetry.tsv, prints a per-page table
"""
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(HERE, "orig")
THRESH = 140
TOL = 3
MIN_AREA = 12


def text_block(bw):
    """x0, x1, y0, y1 of the rune lines: components of rune size (60-330 px tall), robust percentiles."""
    n, _, st, cen = cv2.connectedComponentsWithStats(bw, connectivity=8)
    st, cen = st[1:], cen[1:]
    rune = (st[:, 3] >= 60) & (st[:, 3] <= 330) & (st[:, 4] <= 20000)
    if rune.sum() < 20:
        return None
    return (np.percentile(cen[rune, 0], 1), np.percentile(cen[rune, 0], 99),
            np.percentile(cen[rune, 1], 1), np.percentile(cen[rune, 1], 99))


def asymmetry(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    _, bw = cv2.threshold(img, THRESH, 255, cv2.THRESH_BINARY_INV)
    h, w = bw.shape
    mirror = bw[:, ::-1]
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (2 * TOL + 1, 2 * TOL + 1))
    a_unmatched = (bw > 0) & (cv2.dilate(mirror, k) == 0)          # ink with no mirror partner within TOL
    tb = text_block(bw)
    keep = np.ones_like(a_unmatched)
    if tb is not None:
        x0, x1, y0, y1 = tb
        keep[int(y0) - 120:int(y1) + 120, int(x0) - 90:int(x1) + 90] = False      # the text block and its rune ends
    resid = (a_unmatched & keep).astype(np.uint8)
    n, _, st, cen = cv2.connectedComponentsWithStats(resid, connectivity=8)
    comps = [(float(cen[i, 0]), float(cen[i, 1]), int(st[i, 4])) for i in range(1, n) if st[i, 4] >= MIN_AREA]
    return tb, comps, int((bw > 0).sum())


def main():
    rows = []
    for i in range(75):
        p = os.path.join(ORIG, f"{i:02d}.jpg")
        if os.path.exists(p):
            tb, comps, ink = asymmetry(p)
            rows.append((i, tb, comps, ink))
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "ornament_asymmetry.tsv"), "w", newline="\n", encoding="utf-8") as f:
        f.write("page\tn_marks\ttotal_area\tmarks (x,y,area)\n")
        for i, tb, comps, ink in rows:
            f.write(f"{i:02d}\t{len(comps)}\t{sum(c[2] for c in comps)}\t"
                    + " ".join(f"({x:.0f},{y:.0f},{a})" for x, y, a in sorted(comps, key=lambda c: (c[1], c[0]))) + "\n")
    print("page  marks  total_area")
    for i, tb, comps, ink in rows:
        print(f"{i:02d}   {len(comps):4d}  {sum(c[2] for c in comps):8d}")


if __name__ == "__main__":
    sys.exit(main())
