"""Count the stipple dots of the dissolving insect on scan 74 and the margin dots elsewhere (scouting). Own code."""
import os
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(HERE, "..", "..", "orig")
img = cv2.imread(os.path.join(ORIG, "74.jpg"))
g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
H, W = g.shape
region = (slice(1950, 3300), slice(600, 1800))  # y, x in original pixels (below the text)
sub = g[region]
for thr in (100, 128, 160, 200):
    mask = (sub < thr).astype(np.uint8)
    n, lab, stats, cent = cv2.connectedComponentsWithStats(mask, connectivity=8)
    areas = stats[1:, cv2.CC_STAT_AREA]
    print(f"thr {thr}: components {n-1}, area min/median/max {areas.min()}/{int(np.median(areas))}/{areas.max()}, "
          f"total ink px {int(mask.sum())}, comps with area>=4: {(areas>=4).sum()}, >=9: {(areas>=9).sum()}")
mask = (sub < 128).astype(np.uint8)
n, lab, stats, cent = cv2.connectedComponentsWithStats(mask, connectivity=8)
areas = stats[1:, cv2.CC_STAT_AREA]
big = areas.max()
print("largest component area", big, "(the body/spine)")
# dot pitch: do centroid coordinates fall on a lattice?
c = cent[1:]
for name, v in (("x", c[:, 0]), ("y", c[:, 1])):
    fr = np.mod(np.round(v).astype(int), 4)
    print(name, "centroid mod 4 histogram:", np.bincount(fr, minlength=4).tolist())
# connected components of 1-px size: typical stipple size in px
sizes = np.bincount(np.minimum(areas, 30))
print("area histogram (1..30):", sizes[1:31].tolist())
