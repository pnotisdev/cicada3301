"""Task B: render the two hypotheses into the source patch, JPEG-compress with the real file's tables, correlate with the real
difference patch; null = the same optimisation at other positions (same JPEG phase). See work/log/phase49_p13_1033.md."""
import io, sys, json, itertools, numpy as np
from PIL import Image, ImageDraw, ImageFont
R = 'work/ref/blake_1033/'; A = json.load(open('work/blake1033/align.json'))
PX0, PY0, PW, PH = 296, 0, 736, 1012                   # panel in 1033.jpg coordinates
W = np.asarray(Image.open(R + 'Newton-WilliamBlake_wikimedia.jpg').convert('RGB'))[:, ::-1]
Iim = Image.open(R + '1033.jpg'); I = np.asarray(Iim.convert('RGB')).astype(np.float32)
S = W[A['oy']:A['oy'] + 1427, A['ox']:A['ox'] + 1327].astype(np.float32)[PY0:PY0 + PH, PX0:PX0 + PW]   # source panel
Ip = I[PY0:PY0 + PH, PX0:PX0 + PW]
QT = [list(v) for v in Iim.quantization.values()]
QUAL = int(sys.argv[2]) if len(sys.argv) > 2 else None
Y = lambda a: a @ np.array([.299, .587, .114], np.float32)
# window: 96 x 48, origin multiple of 16 in panel coordinates, containing the mark (panel x 448..494, y 950..968)
WX, WY, WW, WH = 416, 928, 96, 48
# line geometry in window coordinates (from the real difference image, threshold 12): top line x 744-789, y 950-955; bottom x 752-781, y 963-967
TOP = (744 - PX0 - WX, 950 - WY, 46, 6); BOT = (752 - PX0 - WX, 963 - WY, 30, 5)
_l = np.asarray(Image.open(R + 'Outt.png').convert('LA').split()[0]).astype(np.float32)
LOGO = Image.fromarray((_l / _l.max() * 255).astype(np.uint8))            # logo = grey values 0..7 (the alpha channel is opaque)

def encode(a):
    im = Image.fromarray(np.clip(np.rint(a), 0, 255).astype(np.uint8)); b = io.BytesIO()
    if QUAL: im.save(b, 'JPEG', quality=QUAL, subsampling=2)
    else: im.save(b, 'JPEG', qtables=QT, subsampling=2)
    return np.asarray(Image.open(io.BytesIO(b.getvalue())).convert('RGB')).astype(np.float32)

def to_mask(img, box, ss=8):
    """img: PIL 'L' shape (white = ink); resample to box (x,y,w,h) on a WH x WW canvas, area-averaged."""
    x, y, w, h = box; c = Image.new('L', (WW * 1, WH * 1), 0)
    r = img.resize((max(w, 1), max(h, 1)), Image.BOX); c.paste(r, (x, y)); return np.asarray(c).astype(np.float32) / 255

def logo_masks():
    out = {}; bb = (TOP[0], TOP[1], 46, BOT[1] + BOT[3] - TOP[1])      # bounding box of the mark: 46 x 18
    for o, (mir, rot) in enumerate(((0, 0), (1, 0), (0, 1), (1, 1))):
        g = LOGO
        if mir: g = g.transpose(Image.FLIP_LEFT_RIGHT)
        if rot: g = g.transpose(Image.ROTATE_180)
        g = g.crop(g.getbbox())
        ar = g.width / g.height
        for fit in ('stretch', 'height', 'width'):
            if fit == 'stretch': w, h = bb[2], bb[3]
            elif fit == 'height': h = bb[3]; w = max(1, round(h * ar))
            else: w = bb[2]; h = max(1, round(w / ar))
            x = bb[0] + (bb[2] - w) // 2; y = bb[1] + (bb[3] - h) // 2
            out[('logo', o, fit)] = to_mask(g, (x, y, w, h))
    return out

def text_masks():
    out = {}
    for fname in ('arial.ttf', 'times.ttf', 'ARIALN.TTF'):
        for sc in (0.9, 1.0, 1.1):
            S8 = 8; c = Image.new('L', (WW * S8, WH * S8), 0); d = ImageDraw.Draw(c)
            # size: top line MMMCCCI width = 46 px at scale 1
            fs = 1
            for s in range(4, 400):
                f = ImageFont.truetype('C:/Windows/Fonts/' + fname, s)
                if f.getlength('MMMCCCI') >= 46 * S8 * sc: fs = s; break
            f = ImageFont.truetype('C:/Windows/Fonts/' + fname, fs)
            capH = f.getbbox('M')[3] - f.getbbox('M')[1]
            # top line upright, centred on the top-line box; bottom line rotated 180 about its own centre, centred on the bottom-line box
            def line(txt, box, rot):
                t = Image.new('L', (int(f.getlength(txt)) + 4, capH + 8), 0); ImageDraw.Draw(t).text((2, 2 - f.getbbox('M')[1] + 2), txt, fill=255, font=f)
                t = t.crop(t.getbbox())
                if rot: t = t.transpose(Image.ROTATE_180)
                cx = (box[0] + box[2] / 2) * S8; cy = (box[1] + box[3] / 2) * S8
                c.paste(t, (int(cx - t.width / 2), int(cy - t.height / 2)), t)
            line('MMMCCCI', TOP, False); line('MXXXIII', BOT, True)
            m = np.asarray(c.resize((WW, WH), Image.BOX)).astype(np.float32) / 255
            out[('text', fname, sc)] = m
    return out

def ncc(a, b):
    a = a - a.mean(); b = b - b.mean(); d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > 0 else 0.0

BASESUB = len(sys.argv) > 3 and sys.argv[3] == 'sub'   # post hoc: subtract the recompressed unedited source J(S) from both sides

def best_score(masks, wx, wy, tgt=None, detail=False):
    """max over variants/colour/alpha/shift of NCC((J(S+overlay) - S), (I - S)) in the window at panel position (wx, wy)."""
    s = S[wy:wy + WH, wx:wx + WW]; ref = Y(encode(s)) if BASESUB else Y(s); real = Y(Ip[wy:wy + WH, wx:wx + WW]) - ref
    best = (-2, None)
    for key, m in masks.items():
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                ms = np.roll(np.roll(m, dy, 0), dx, 1)
                for col in (255.0, 0.0):
                    for al in (0.4, 0.8):
                        a = (al * ms)[..., None]; comp = s * (1 - a) + col * a
                        sc = ncc(Y(encode(comp)) - ref, real)
                        if sc > best[0]: best = (sc, (key, dx, dy, col, al))
    return best

if __name__ == '__main__':
    K = int(sys.argv[1]); rng = np.random.default_rng(49)
    L = logo_masks(); T = text_masks()
    real = {'logo': best_score(L, WX, WY), 'text': best_score(T, WX, WY)}
    print('REAL', real, flush=True)
    # baseline: no overlay, same compression
    s = S[WY:WY + WH, WX:WX + WW]; print('baseline J(S)-S vs real:', ncc(Y(encode(s)) - Y(s), Y(Ip[WY:WY + WH, WX:WX + WW]) - Y(s)))
    cand = [(WX + 16 * a, WY + 16 * b) for a in range(-26, 14) for b in range(-58, 2)
            if 0 <= WX + 16 * a <= PW - WW and 0 <= WY + 16 * b <= PH - WH and (abs(16 * a) >= 96 or abs(16 * b) >= 64)]
    pick = rng.choice(len(cand), min(K, len(cand)), replace=False); nulls = []
    for n, i in enumerate(pick):
        wx, wy = cand[i]; nulls.append((wx, wy, best_score(L, wx, wy)[0], best_score(T, wx, wy)[0]))
        if n % 20 == 0: print(n, nulls[-1], flush=True)
    json.dump(dict(real={k: [v[0], str(v[1])] for k, v in real.items()}, null=nulls), open('work/blake1033/result%s%s.json' % (('_q%d' % QUAL) if QUAL else '', '_sub' if BASESUB else ''), 'w'))
