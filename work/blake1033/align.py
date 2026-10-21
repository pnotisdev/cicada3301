"""Locate the 1033.jpg centre panel inside the mirrored Wikimedia original (no resize, crop only, per the community notes)."""
import numpy as np, json
from PIL import Image
from scipy.signal import fftconvolve
R = 'work/ref/blake_1033/'
W = np.asarray(Image.open(R + 'Newton-WilliamBlake_wikimedia.jpg').convert('RGB'))[:, ::-1].astype(np.float32)   # mirrored
I = np.asarray(Image.open(R + '1033.jpg').convert('RGB')).astype(np.float32)
g = lambda a: a.mean(2)
Wg = g(W)
x0, y0, x1, y1 = 420, 560, 900, 980; T = g(I[y0:y1, x0:x1])         # template inside the centre panel
def ncc(Wg, T):
    n = T.size; Tz = T - T.mean(); ts = np.sqrt((Tz ** 2).sum())
    num = fftconvolve(Wg, Tz[::-1, ::-1], mode='valid')
    s1 = fftconvolve(Wg, np.ones_like(T), mode='valid'); s2 = fftconvolve(Wg ** 2, np.ones_like(T), mode='valid')
    den = np.sqrt(np.maximum(s2 - s1 ** 2 / n, 1e-9)) * ts
    return num / den
c = ncc(Wg, T); iy, ix = np.unravel_index(np.argmax(c), c.shape)
print('best NCC', c[iy, ix], 'at W(mirrored) offset', ix, iy, '-> panel origin in W:', ix - x0, iy - y0)
json.dump(dict(ncc=float(c[iy, ix]), ox=int(ix - x0), oy=int(iy - y0)), open('work/blake1033/align.json', 'w'))
