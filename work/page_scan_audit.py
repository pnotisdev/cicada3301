"""Structure audit of the 75 original page scans (work/orig/NN.jpg): containers, appended data, hidden faint marks, stipple.

    python page_scan_audit.py        # writes results/analysis/page_scan_audit.txt

  1. JPEG marker segments, quantisation-table family and bytes after the last EOI of every scan.
  2. The two scans that carry extra data are unpacked: 10.jpg holds pages 10-13 end to end (appended bytes are exact copies of
     11.jpg, 12.jpg, 13.jpg); 05.jpg is [page][360-byte text][the same page byte-reversed], and the text decodes to the 25 cells of
     the page's own magic square (digits written least significant first).
  3. SHA-512 of every scan against the 'An End' hash (no scan is 'the page').
  4. Hidden faint marks: pixels that are not pure white and lie more than 24 px from any ink. Control: a faint (252-254) text and
     rectangle planted in two clean pages and re-encoded as JPEG is found; the clean text pages show none.
  5. The stippled insect of 74.jpg: number and size of the dots and whether they sit on a block lattice.

Scouting; own parser, no third-party code.
"""
import hashlib
import os
import re
import struct
import sys
from collections import Counter

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(HERE, "orig")
OUT = os.path.join(os.path.dirname(HERE), "results", "analysis", "page_scan_audit.txt")
AN_END = ("36367763ab73783c7af284446c59466b4cd653239a311cb7116d4618dee09a8425893dc7500b464fdaf1672d7bef5e891c6e2274568926a49fb4f45132c2a8b4")
MARK = {0xD8: "SOI", 0xD9: "EOI", 0xDB: "DQT", 0xC0: "SOF0", 0xC1: "SOF1", 0xC2: "SOF2", 0xC4: "DHT", 0xDA: "SOS", 0xDD: "DRI",
        0xFE: "COM", 0xE0: "APP0", 0xE1: "APP1", 0xE2: "APP2", 0xEE: "APP14"}


def parse(b):
    """marker segments up to the first EOI; returns (segments, offset after EOI or None)"""
    segs, i = [], 2
    while i < len(b):
        if b[i] != 0xFF:
            return segs, None
        while b[i] == 0xFF:
            i += 1
        m = b[i]
        i += 1
        name = MARK.get(m, "M%02X" % m)
        if m == 0xD9:
            return segs, i
        if 0xD0 <= m <= 0xD7 or m == 0x01:
            continue
        ln = struct.unpack(">H", b[i:i + 2])[0]
        segs.append((name, ln, b[i + 2:i + ln][:64]))
        i += ln
        if m == 0xDA:
            j = i
            while j < len(b) - 1 and not (b[j] == 0xFF and b[j + 1] != 0x00 and not 0xD0 <= b[j + 1] <= 0xD7):
                j += 1
            i = j
    return segs, None


def load(n):
    return open(os.path.join(ORIG, f"{n:02d}.jpg"), "rb").read()


def far_offwhite(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ink = np.maximum((g < 200).astype(np.uint8), (img.min(axis=2) < 200).astype(np.uint8))
    near = cv2.dilate(ink, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (49, 49)))
    return int(((near == 0) & (img.min(axis=2) < 255)).sum())


def decode_cells(text):
    """the 360-byte text of 05.jpg: hex digits that decode to tokens [first digit][digits...][terminator '0' or ':'];
    each number is written least significant digit first"""
    h = text.decode("ascii").strip()[1:]
    s = bytes.fromhex(h[:len(h) // 2 * 2]).decode("latin-1")
    vals = []
    for row in s.split(":"):  # ':' ends a row of the square
        toks = [t for t in re.split(r" {4,}", row) if t.strip(" ")]
        for k, t in enumerate(toks):
            t = t.strip(" ") if t[0] != " " else t.lstrip(" ")
            last = k == len(toks) - 1  # a row's last token has no '0' terminator (':' took its place)
            body = t if last else t[:-1]
            if body[0].isdigit():  # the first digit 0 is written as a space, which the split removed
                digits = [0] + [int(c) for c in body]
            else:
                p = ord(body[0])
                digits = [p if p < 0x20 else p - 0x20] + [int(c) for c in body[1:]]
            vals.append(int("".join(map(str, digits[::-1]))))
    return vals


def main():
    L = ["# Page scan audit (work/page_scan_audit.py), 75 scans in work/orig. Scouting; no claim about LP2's key.", ""]
    rows = []
    for n in range(75):
        b = load(n)
        segs, end = parse(b)
        qt = hashlib.sha1(b"".join(s[2] for s in segs if s[0] == "DQT")).hexdigest()[:8]
        app = sorted({(s[0], s[1]) for s in segs if s[0].startswith("APP")})
        com = sum(1 for s in segs if s[0] == "COM")
        rows.append((n, len(b), qt, app, com, (len(b) - end) if end else None, hashlib.sha512(b).hexdigest()))
    L.append("1. JPEG structure")
    fam = {}
    for r in rows:
        fam.setdefault(r[2], []).append(r[0])
    for q, ns in sorted(fam.items(), key=lambda kv: -len(kv[1])):
        L.append(f"   quantisation family {q}: {len(ns)} scans: {ns}")
    L.append(f"   marker sets: {Counter(tuple(r[3]) for r in rows)}")
    L.append(f"   COM segments: {sum(r[4] for r in rows)}; scans with bytes after the first EOI: {[(r[0], r[5]) for r in rows if r[5]]}")
    L.append("")
    # ---- 2. containers
    L.append("2. The two scans with extra data")
    b10 = load(10)
    k10 = rows[10][5]
    tail = b10[len(b10) - k10:]
    off, parts = 0, []
    for m in (11, 12, 13):
        o = load(m)
        parts.append((m, tail[off:off + len(o)] == o))
        off += len(o)
    L.append(f"   10.jpg: {len(b10)} bytes = page 10 ({len(b10) - k10} bytes) + {k10} appended bytes; appended part equals "
             + ", ".join(f"{m}.jpg: {ok}" for m, ok in parts) + f" (all consumed: {off == k10})")
    b5 = load(5)
    k5 = rows[5][5]
    tail5 = b5[len(b5) - k5:]
    page5 = b5[:len(b5) - k5]
    text, rev = tail5[:360], tail5[360:]
    L.append(f"   05.jpg: {len(b5)} bytes = page ({len(page5)} bytes) + {len(text)}-byte text + {len(rev)} bytes; "
             f"reversed tail equals the page: {rev[::-1] == page5}")
    cells = decode_cells(text)
    grid = [cells[i:i + 5] for i in range(0, 25, 5)]
    L.append(f"   text decodes to {len(cells)} numbers: {cells}")
    L.append(f"   as a 5x5 square: row sums {[sum(r) for r in grid]}, column sums {[sum(c) for c in zip(*grid)]}, "
             f"diagonals {sum(grid[i][i] for i in range(5))}, {sum(grid[i][4 - i] for i in range(5))}; palindromic: {cells == cells[::-1]}")
    L.append("")
    # ---- 3. hash
    L.append("3. SHA-512 of the scans against the An End hash: matches " + str([r[0] for r in rows if r[6] == AN_END]))
    L.append("")
    # ---- 4. hidden faint marks
    L.append("4. Off-white pixels far (> 24 px) from ink, per scan (art with soft shading explains most; text-only pages should be 0)")
    counts = [far_offwhite(cv2.imread(os.path.join(ORIG, f"{n:02d}.jpg"))) for n in range(75)]
    for a in range(0, 75, 15):
        L.append("   " + "  ".join(f"{n:02d}:{counts[n]:>6d}" for n in range(a, a + 15)))
    L.append(f"   scans with 0: {sum(1 for c in counts if c == 0)} of 75")
    for page in (36, 46):
        img = cv2.imread(os.path.join(ORIG, f"{page:02d}.jpg"))
        res = []
        for level in (254, 253, 252):
            for q in (95, 85):
                m = img.copy()
                cv2.putText(m, "HIDDEN 3301", (300, 3350), cv2.FONT_HERSHEY_SIMPLEX, 6, (level, level, level), 14)
                cv2.rectangle(m, (200, 200), (900, 330), (level, level, level), -1)
                ok, buf = cv2.imencode(".jpg", m, [cv2.IMWRITE_JPEG_QUALITY, q])
                res.append(f"level {level} q{q}: {far_offwhite(cv2.imdecode(buf, 1))}")
        L.append(f"   control, page {page} (clean: {counts[page]}): planted faint mark -> " + "; ".join(res))
    L.append("")
    # ---- 5. stipple
    g = cv2.cvtColor(cv2.imread(os.path.join(ORIG, "74.jpg")), cv2.COLOR_BGR2GRAY)
    sub = g[1950:3300, 600:1800]
    mask = (sub < 128).astype(np.uint8)
    n, _, stats, cent = cv2.connectedComponentsWithStats(mask, connectivity=8)
    areas = stats[1:, cv2.CC_STAT_AREA]
    best = []
    for s in (3, 4, 5, 8):
        for py in range(s):
            for px in range(s):
                h = (mask.shape[0] - py) // s * s
                w = (mask.shape[1] - px) // s * s
                fr = mask[py:py + h, px:px + w].reshape(h // s, s, w // s, s).mean(axis=(1, 3))
                best.append((((fr > 0) & (fr < 1)).sum() / max(1, (fr > 0).sum()), s, px, py))
    best.sort()
    L.append("5. Stippled insect on 74.jpg")
    L.append(f"   {n - 1} connected components (largest {areas.max()} px, the body); dot areas: "
             f"{dict(sorted(Counter(int(a) for a in areas if a < 40).items()))}")
    L.append(f"   best block lattice: mixed/non-empty = {best[0][0]:.2f} at scale {best[0][1]} (a clean upscaled bitmap would be near 0): irregular")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    sys.exit(main())
