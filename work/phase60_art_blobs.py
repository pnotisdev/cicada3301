"""Phase 60: bounding boxes (full-scan pixels, 2400 x 3600) of the large ink blobs on page images, and the cross-vs-glyph
sheet (the Russian cross of images 17-19 rotated 90 degrees next to the black glyph of image 39).

    python work/phase60_art_blobs.py [NN ...]      # blob boxes; default: the art pages in DEFAULT
    python work/phase60_art_blobs.py --cross       # writes work/phase60/cross_vs_glyph.jpg
    python work/phase60_art_blobs.py --sheets      # writes the five 15-page contact sheets work/phase60/sheet_A_B.jpg
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(HERE, "orig")
DEFAULT = [1, 5, 15, 16, 17, 19, 24, 31, 32, 39, 40, 44, 49, 50, 51, 53, 56, 70, 72, 73, 74]


def blobs(n, min_area=1500):
    """ink dilated at 1/4 scale, connected components; returns [(area, 'x.. y..')] largest first (text lines are 584-1812 wide)"""
    a = np.array(Image.open(os.path.join(ORIG, f"{n:02d}.jpg")).convert("L").resize((600, 900))) < 170
    lab, _ = ndi.label(ndi.binary_dilation(a, iterations=4))
    out = []
    for i, s in enumerate(ndi.find_objects(lab)):
        area = int((lab[s] == i + 1).sum())
        if area > min_area:
            out.append((area, f"x{s[1].start * 4}-{s[1].stop * 4} y{s[0].start * 4}-{s[0].stop * 4}"))
    return sorted(out, reverse=True)


def cross_sheet():
    c = Image.open(os.path.join(ORIG, "17.jpg")).convert("L").crop((1820, 600, 2380, 1950)).rotate(90, expand=True)
    g = Image.open(os.path.join(ORIG, "39.jpg")).convert("L").crop((580, 2180, 1800, 2680))
    c.thumbnail((610, 400)); g.thumbnail((610, 400))
    s = Image.new("L", (1230, 260), 255)
    s.paste(c, (0, 0)); s.paste(g, (620, 0))
    p = os.path.join(HERE, "phase60", "cross_vs_glyph.jpg")
    s.save(p, quality=70)
    print("wrote", os.path.relpath(p, os.path.dirname(HERE)))


def sheets(cols=5, tw=300, th=450):
    from PIL import ImageDraw
    for a in range(0, 75, 15):
        nums = list(range(a, a + 15))
        s = Image.new("RGB", (cols * tw, 3 * (th + 18)), "white")
        d = ImageDraw.Draw(s)
        for i, n in enumerate(nums):
            im = Image.open(os.path.join(ORIG, f"{n:02d}.jpg")).convert("RGB")
            im.thumbnail((tw - 4, th - 4))
            x, y = (i % cols) * tw, (i // cols) * (th + 18)
            s.paste(im, (x + 2, y + 18))
            d.text((x + 4, y + 3), f"{n:02d}", fill=(200, 0, 0))
        s.save(os.path.join(HERE, "phase60", f"sheet_{a:02d}_{a + 14:02d}.jpg"), quality=60)


if __name__ == "__main__":
    if "--sheets" in sys.argv:
        sheets()
    elif "--cross" in sys.argv:
        cross_sheet()
    else:
        for n in [int(x) for x in sys.argv[1:]] or DEFAULT:
            print(n, [b[1] for b in blobs(n)[:7]])
