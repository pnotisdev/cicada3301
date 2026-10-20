"""Positive control for the hidden-contrast scan: plant a faint (value 252-254) pattern in a clean text page, re-encode
as JPEG at several qualities, and count the off-white pixels far from ink with the same detector. Own code."""
import os
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(HERE, "..", "..", "orig")
def detect(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ink = np.maximum((g < 200).astype(np.uint8), (img.min(axis=2) < 200).astype(np.uint8))
    near = cv2.dilate(ink, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (49, 49)))
    return int(((near == 0) & (img.min(axis=2) < 255)).sum())
for page in (36, 46):
    img = cv2.imread(os.path.join(ORIG, f"{page:02d}.jpg"))
    base = detect(img)
    for level in (254, 253, 252):
        for q in (95, 85):
            m = img.copy()
            # a faint 'message': text and a rectangle in the bottom margin, outside the text block
            cv2.putText(m, "HIDDEN 3301", (300, 3350), cv2.FONT_HERSHEY_SIMPLEX, 6, (level, level, level), 14)
            cv2.rectangle(m, (200, 200), (900, 330), (level, level, level), -1)
            ok, buf = cv2.imencode(".jpg", m, [cv2.IMWRITE_JPEG_QUALITY, q])
            re = cv2.imdecode(buf, 1)
            print(f"page {page}: base off-white far-from-ink px {base:5d} | planted level {level} q{q}: {detect(re):8d}")
