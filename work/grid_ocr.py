"""Glyph-metric audit of the 256-byte base-60 grid (pages 64-66, images 66-68).

Each token is two characters: a digit 0-4, then one of 0-9 A-Z a-x. The ambiguous pairs in this
Futura-like face are I / l / 1, O / 0 / o, L, W / w, etc. Every character is cropped from the
original image and measured (height relative to the token's leading digit, width ratio, ink
distribution), and the measurement is compared with the transcription's character.

    python grid_ocr.py     # writes tmp/grid_ocr/*.png crops and prints the audit
"""
import os
import sys

import cv2
import numpy as np

import grid60

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tmp", "grid_ocr")
IMAGES = (66, 67, 68)


def components(img_gray, y0, y1):
    mask = (img_gray[y0:y1] < 120).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    comps = [(x, y + y0, w, h, a) for x, y, w, h, a in stats[1:] if a > 30]
    return comps


def grid_rows(gray):
    """Text rows of the Latin grid: horizontal bands whose components are digit-sized."""
    mask = (gray < 120).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    comps = [tuple(s) for s in stats[1:] if s[4] > 30]
    # digits are ~80-110 px tall and narrow; runes are similar height, so use row membership later
    comps.sort(key=lambda s: s[1] + s[3] / 2)
    rows, cur = [], []
    for c in comps:
        cy = c[1] + c[3] / 2
        if cur and abs(cy - np.mean([q[1] + q[3] / 2 for q in cur])) > 50:
            rows.append(cur)
            cur = []
        cur.append(c)
    if cur:
        rows.append(cur)
    return rows


def tokens_in_row(row):
    """Split a row of components into tokens (big horizontal gaps) of characters (component groups)."""
    row = sorted(row, key=lambda c: c[0])
    # merge components that overlap horizontally (e.g. the dot of i/j)
    chars = []
    for c in row:
        if chars and c[0] < chars[-1][0] + chars[-1][2] - 2:
            x0 = min(chars[-1][0], c[0]); y0 = min(chars[-1][1], c[1])
            x1 = max(chars[-1][0] + chars[-1][2], c[0] + c[2]); y1 = max(chars[-1][1] + chars[-1][3], c[1] + c[3])
            chars[-1] = (x0, y0, x1 - x0, y1 - y0, chars[-1][4] + c[4])
        else:
            chars.append(c)
    gaps = [b[0] - (a[0] + a[2]) for a, b in zip(chars, chars[1:])]
    if not gaps:
        return []
    thr = (max(gaps) + np.median(gaps)) / 2
    toks, cur = [], [chars[0]]
    for g, c in zip(gaps, chars[1:]):
        if g > thr:
            toks.append(cur)
            cur = []
        cur.append(c)
    toks.append(cur)
    return toks


def row_chars(row):
    """Characters of a grid row (x-band of the grid only), dots merged into their letter."""
    inner = sorted([c for c in row if 600 < c[0] < 1800], key=lambda c: c[0])
    med_area = np.median([c[4] for c in inner]) if inner else 0
    chars = []
    for c in inner:
        if chars:
            p = chars[-1]
            overlap = min(p[0] + p[2], c[0] + c[2]) - max(p[0], c[0])
            narrow = min(p[2], c[2])
            dot = min(p[4], c[4]) < 0.15 * med_area
        if chars and overlap > 0 and (overlap > 0.5 * narrow or dot):
            x0 = min(chars[-1][0], c[0]); y0 = min(chars[-1][1], c[1])
            x1 = max(chars[-1][0] + chars[-1][2], c[0] + c[2]); y1 = max(chars[-1][1] + chars[-1][3], c[1] + c[3])
            chars[-1] = (x0, y0, x1 - x0, y1 - y0, chars[-1][4] + c[4])
        else:
            chars.append(c)
    # a remaining tiny component (dot not overlapping) joins its nearest neighbour
    while len(chars) > 16:
        k = min(range(len(chars)), key=lambda i: chars[i][4])
        tiny = chars.pop(k)
        j = min(range(len(chars)), key=lambda i: abs(chars[i][0] - tiny[0]))
        a = chars[j]
        x0 = min(a[0], tiny[0]); y0 = min(a[1], tiny[1])
        x1 = max(a[0] + a[2], tiny[0] + tiny[2]); y1 = max(a[1] + a[3], tiny[1] + tiny[3])
        chars[j] = (x0, y0, x1 - x0, y1 - y0, a[4] + tiny[4])
    return chars


def is_grid_row(row):
    return len(row_chars(row)) == 16 and sum(1 for c in row if 600 < c[0] < 1800) <= 18


def grid_tokens_of_row(row):
    ch = row_chars(row)
    return [ch[i:i + 2] for i in range(0, 16, 2)]


def measure(gray, ch, ref):
    x, y, w, h, a = ch
    rx, ry, rw, rh, _ = ref
    crop = gray[y:y + h, x:x + w] < 120
    return {
        "h_rel": h / rh,                       # height relative to the leading digit
        "top_rel": (ry - y) / rh,              # how far it rises above the digit's top
        "bottom_rel": (y + h - (ry + rh)) / rh,  # descends below baseline?
        "w_rel": w / rh,
        "fill": crop.mean(),
        "foot": crop[-max(2, h // 8):, :].mean(),  # ink in the bottom eighth (L has a foot)
        "hole": None,
    }


def audit():
    os.makedirs(OUT, exist_ok=True)
    toks = grid60.grid_tokens()
    found = []
    for n in IMAGES:
        img = cv2.imread(os.path.join(HERE, "orig", f"{n:02d}.jpg"))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        for row in grid_rows(gray):
            if not is_grid_row(row):
                continue
            for tok in grid_tokens_of_row(row):
                found.append((n, gray, tok))
    print(f"located {len(found)} grid tokens on the images (transcription has {len(toks)})")
    rows = []
    for k, ((n, gray, tok), t) in enumerate(zip(found, toks)):
        m = measure(gray, tok[1], tok[0])
        rows.append((k, n, t, m, tok))
    return rows, found


def classify(rows):
    """Group second characters by transcribed symbol and print their metrics, so a mis-
    transcribed glyph stands out against the others of its class."""
    from collections import defaultdict
    by = defaultdict(list)
    for k, n, t, m, tok in rows:
        by[t[1]].append((k, m))
    return by


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    rows, found = audit()
    by = classify(rows)
    print("second-character metrics by transcribed symbol (h_rel: height / digit height; top_rel: rise above digit top)")
    for sym in sorted(by, key=lambda s: grid60.DIGITS.index(s)):
        hs = [m["h_rel"] for _, m in by[sym]]
        tops = [m["top_rel"] for _, m in by[sym]]
        ws = [m["w_rel"] for _, m in by[sym]]
        print(f"  {sym}: n={len(hs):2d} h_rel {min(hs):.2f}-{max(hs):.2f} top {min(tops):+.2f}..{max(tops):+.2f} "
              f"w {min(ws):.2f}-{max(ws):.2f}")
    contested = [25, 175, 182, 199, 215, 237]
    print("\ncontested indices:")
    for k in contested:
        _, n, t, m, tok = rows[k]
        print(f"  index {k}: transcribed {t!r} on image {n}: h_rel {m['h_rel']:.2f} top {m['top_rel']:+.2f} "
              f"w {m['w_rel']:.2f} fill {m['fill']:.2f} foot {m['foot']:.2f}")
        x0 = min(c[0] for c in tok) - 20; y0 = min(c[1] for c in tok) - 20
        x1 = max(c[0] + c[2] for c in tok) + 20; y1 = max(c[1] + c[3] for c in tok) + 20
        cv2.imwrite(os.path.join(OUT, f"idx{k:03d}_{t}.png"), cv2.imread(os.path.join(HERE, "orig", f"{n:02d}.jpg"))[y0:y1, x0:x1])
