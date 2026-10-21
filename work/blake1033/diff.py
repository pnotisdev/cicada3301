import numpy as np, json
from PIL import Image
R = 'work/ref/blake_1033/'; A = json.load(open('work/blake1033/align.json'))
W = np.asarray(Image.open(R + 'Newton-WilliamBlake_wikimedia.jpg').convert('RGB'))[:, ::-1].astype(np.float32)
I = np.asarray(Image.open(R + '1033.jpg').convert('RGB')).astype(np.float32)
ox, oy = A['ox'], A['oy']
# panel extent in 1033 (x from 296, y 0..~1010): find by where the mean abs difference to the aligned crop is small
H, Wd = I.shape[:2]
ys, xs = np.mgrid[0:H, 0:Wd]
cx, cy = xs + ox, ys + oy
ok = (cx >= 0) & (cx < W.shape[1]) & (cy >= 0) & (cy < W.shape[0])
S = np.zeros_like(I); S[ok] = W[cy[ok], cx[ok]]
D = np.abs(I - S).mean(2); D[~ok] = 255
np.save('work/blake1033/D.npy', D)
col = np.median(D, 0); row = np.median(D[:, 320:1000], 1)
print('columns with median diff<12:', np.nonzero(col < 12)[0][[0, -1]])
print('rows with median diff<12:', np.nonzero(row < 12)[0][[0, -1]])
Image.fromarray(np.clip(D * 8, 0, 255).astype(np.uint8)).save('work/blake1033/diff_x8.png')
