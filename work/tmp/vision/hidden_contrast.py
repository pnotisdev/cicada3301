"""Hidden low-contrast marks in the page backgrounds (scouting, 2026-10-19). Own code, read-only on work/orig.
For each scan: pixels that are not pure white but lie > 24 px away from any ink (gray < 200). Anything that is not
JPEG ringing should be rare; clusters of such pixels would be a faint watermark / hidden drawing."""
import os, sys
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(HERE, "..", "..", "orig")
OUT = HERE
rows = []
for n in range(75):
    img = cv2.imread(os.path.join(ORIG, f"{n:02d}.jpg"))
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ink = (g < 200).astype(np.uint8)
    # also colour ink (red etc.): any channel far from white
    col = (img.min(axis=2) < 200).astype(np.uint8)
    ink = np.maximum(ink, col)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (49, 49))
    near = cv2.dilate(ink, k)
    far = near == 0
    nonwhite = img.min(axis=2) < 255
    anomal = far & nonwhite
    cnt = int(anomal.sum())
    total_far = int(far.sum())
    levels = np.bincount(img.min(axis=2)[far].ravel(), minlength=256)
    low = [(v, int(levels[v])) for v in range(200, 255) if levels[v] > 0][-4:]
    rows.append((n, total_far, cnt, low))
    if cnt > 50:
        ys, xs = np.nonzero(anomal)
        print(f"{n:02d}: far-from-ink px {total_far:9d}  non-white {cnt:7d}  y {ys.min()}-{ys.max()} x {xs.min()}-{xs.max()}  levels(last4) {low}")
        # amplified view: stretch 235..255 -> 0..255 on the far region
        amp = np.clip((img.min(axis=2).astype(np.float32) - 235) * (255 / 20), 0, 255).astype(np.uint8)
        amp[~far] = 255
        cv2.imwrite(os.path.join(OUT, f"amp_{n:02d}.png"), cv2.resize(amp, (600, 900), interpolation=cv2.INTER_AREA))
print("scans with 0 anomalous background pixels:", [r[0] for r in rows if r[2] == 0].__len__(), "of 75")
print("scans with > 50:", [(r[0], r[2]) for r in rows if r[2] > 50])
