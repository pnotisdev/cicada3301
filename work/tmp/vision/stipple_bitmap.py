"""Recover the low-resolution bitmap behind the stippled insect on scan 74 (scouting). Own code."""
import os
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(HERE, "..", "..", "orig")
g = cv2.cvtColor(cv2.imread(os.path.join(ORIG, "74.jpg")), cv2.COLOR_BGR2GRAY)
y0, y1, x0, x1 = 1950, 3300, 600, 1800
mask = (g[y0:y1, x0:x1] < 128).astype(np.uint8)
res = []
for s in (3, 4, 5, 8):
    for py in range(s):
        for px in range(s):
            h = (mask.shape[0] - py) // s * s
            w = (mask.shape[1] - px) // s * s
            fr = mask[py:py + h, px:px + w].reshape(h // s, s, w // s, s).mean(axis=(1, 3))
            res.append(((fr > 0) & (fr < 1)).sum() / max(1, (fr > 0).sum()) * 1.0)
            res[-1] = (res[-1], s, px, py, int((fr == 1).sum()), int(((fr > 0) & (fr < 1)).sum()))
res.sort()
print("best lattices (mixed/non-empty ratio, scale, phase x, phase y, full blocks, mixed blocks):")
for r in res[:6]:
    print(r)
r, s, px, py, full, mixed = res[0]
h = (mask.shape[0] - py) // s * s
w = (mask.shape[1] - px) // s * s
fr = mask[py:py + h, px:px + w].reshape(h // s, s, w // s, s).mean(axis=(1, 3))
bm = (fr >= 0.5).astype(np.uint8)
print("bitmap shape", bm.shape, "set pixels", int(bm.sum()))
cv2.imwrite(os.path.join(HERE, "stipple74_bitmap.png"), (1 - bm) * 255)
big = cv2.resize((1 - bm) * 255, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)
cv2.imwrite(os.path.join(HERE, "stipple74_bitmap_x3.png"), big)
np.save(os.path.join(HERE, "stipple74_bitmap.npy"), bm)
