"""Rune OCR for the original Liber Primus page images (work/orig/NN.jpg).

Segments each page into lines and rune glyphs, trains a glyph classifier from the
community transcription itself (cross-validated by page parity), then aligns every
image line against the transcription line and reports where they disagree.

    python ocr.py seg NN        # segment one image, write tmp/segNN.png overlay
    python ocr.py verify        # full run: writes tmp/phase2/report.tsv + review sheets
"""
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lp  # noqa: E402

ORIG = os.path.join(HERE, "orig")
TMP = os.path.join(HERE, "tmp")
OUT = os.path.join(TMP, "phase2")
S = 32  # normalised glyph size


def image_of(page):
    """Transcription page index -> original image number (00.jpg title, 02.jpg chapter title)."""
    return 1 if page == 0 else page + 2


# ---------------------------------------------------------------- segmentation

def load_ink(n):
    """Binary ink mask (black or red ink = 1) and red mask for image n."""
    img = cv2.imread(os.path.join(ORIG, f"{n:02d}.jpg"))
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    dark = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) < 110
    red = (((hsv[..., 0] < 12) | (hsv[..., 0] > 165)) & (hsv[..., 1] > 90) & (hsv[..., 2] > 60))
    return img, (dark | red).astype(np.uint8), red.astype(np.uint8)


def rune_heights(stats, min_count=15):
    """Rune cap heights on the page: peaks in the height histogram of tall, narrow
    components (most pages have one size; a few mix body text with smaller runes)."""
    hs = [h for x, y, w, h, a in stats if 25 < h < 300 and w < h and a > 40]
    k = np.convolve(np.bincount(hs, minlength=310), np.ones(7), mode="same")
    peaks = []
    for h in np.argsort(-k):
        if k[h] < min_count:
            break
        if all(abs(h - p) > 0.45 * p for p in peaks):
            peaks.append(int(h))
    return peaks or [int(np.argmax(k))]


class Glyph:
    __slots__ = ("x", "y", "w", "h", "red", "mask", "kind")

    def __init__(self, x, y, w, h, red, mask, kind="rune"):
        self.x, self.y, self.w, self.h, self.red, self.mask, self.kind = x, y, w, h, red, mask, kind

    def feature(self):
        """S x S image: glyph scaled by its own height, centred horizontally."""
        scale = S / self.h
        nw = max(1, min(S, int(round(self.w * scale))))
        small = cv2.resize(self.mask.astype(np.float32), (nw, S), interpolation=cv2.INTER_AREA)
        canvas = np.zeros((S, S), np.float32)
        off = (S - nw) // 2
        canvas[:, off:off + nw] = small
        return canvas


def split_wide(x, y, w, h, m, H):
    """Split a component that is too wide for one rune at the lowest-ink columns."""
    k = int(np.clip(round(w / (0.55 * H)), 2, 4))
    proj = m.sum(axis=0)
    cuts, win = [0], int(0.15 * H)
    for i in range(1, k):
        c = int(w * i / k)
        lo, hi = max(cuts[-1] + 1, c - win), min(w - 1, c + win)
        cuts.append(lo + int(np.argmin(proj[lo:hi + 1])) if hi > lo else c)
    cuts.append(w)
    out = []
    for a, b in zip(cuts, cuts[1:]):
        sub = m[:, a:b]
        rows = np.where(sub.any(axis=1))[0]
        if b - a < 2 or not len(rows):
            continue
        out.append((x + a, y + rows[0], b - a, rows[-1] - rows[0] + 1, sub[rows[0]:rows[-1] + 1]))
    return out


def segment(n):
    """Return (lines, H, img): lines top-to-bottom, each a left-to-right list of Glyphs."""
    img, ink, red = load_ink(n)
    _, lab, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    stats = stats[1:]
    heights = rune_heights(stats)
    lines = []
    for H in heights:
        lines += _segment_at(H, lab, stats, red)
    lines.sort(key=lambda l: np.median([g.y for g in l]))
    return lines, heights[0], img


def _segment_at(H, lab, stats, red):
    glyphs, caps = [], []
    # rune-sized components; a glyph's mask is all ink in its box except other runes, so
    # detached strokes (e.g. the inner bar of ᚣ) stay with their rune
    big = np.zeros(len(stats) + 1, bool)
    big[1:] = (stats[:, 3] >= 0.8 * H) & (stats[:, 4] >= 0.05 * H * H)
    for cid, (x, y, w, h, a) in enumerate(stats, start=1):
        if a < 0.05 * H * H:
            continue
        region = lab[y:y + h, x:x + w]
        m = (region == cid) | ((region > 0) & ~big[region])
        is_red = red[y:y + h, x:x + w][region == cid].mean() > 0.5
        if 0.8 * H <= h <= 1.25 * H and w <= 0.9 * H:
            glyphs.append(Glyph(x, y, w, h, is_red, m))
        elif 0.8 * H <= h <= 1.25 * H and w <= 3 * H:
            for gx, gy, gw, gh, gm in split_wide(x, y, w, h, m, H):
                glyphs.append(Glyph(gx, gy, gw, gh, is_red, gm, "split"))
        elif is_red and 2 * H <= h <= 5 * H and w <= 2.5 * H:
            caps.append(Glyph(x, y, w, h, True, m, "dropcap"))

    glyphs.sort(key=lambda g: g.y + g.h / 2)
    lines, cur, cy = [], [], None
    for g in glyphs:
        c = g.y + g.h / 2
        if cy is not None and abs(c - cy) >= 0.5 * H:
            lines.append(cur)
            cur = []
        cur.append(g)
        cy = np.mean([q.y + q.h / 2 for q in cur])
    if cur:
        lines.append(cur)
    lines = [sorted(l, key=lambda g: g.x) for l in lines]

    # text is one horizontal run; split each line at big gaps and keep the largest run,
    # which drops decoration fragments picked up beside the text block
    kept = []
    for l in lines:
        runs, cur = [], [l[0]]
        for a, b in zip(l, l[1:]):
            if b.x - (a.x + a.w) > 2.2 * H:
                runs.append(cur)
                cur = []
            cur.append(b)
        runs.append(cur)
        kept.append(max(runs, key=len))
    lines = [l for l in kept if len(l) >= 3]

    # a drop cap is the first rune of the line level with its top
    for cap in caps:
        if lines:
            best = min(lines, key=lambda l: abs(l[0].y - cap.y))
            if abs(best[0].y - cap.y) < 1.0 * H and cap.x < best[0].x:
                best.insert(0, cap)
    return lines


def overlay(n, lines, img, path=None):
    out = img.copy()
    colours = {"rune": (0, 160, 0), "split": (0, 140, 255), "dropcap": (255, 0, 0)}
    for li, line in enumerate(lines):
        for g in line:
            cv2.rectangle(out, (g.x, g.y), (g.x + g.w, g.y + g.h), colours[g.kind], 3)
        cv2.putText(out, f"{li}:{len(line)}", (max(0, line[0].x - 260), line[0].y + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 0, 255), 3)
    os.makedirs(TMP, exist_ok=True)
    path = path or os.path.join(TMP, f"seg{n:02d}.png")
    cv2.imwrite(path, cv2.resize(out, None, fx=0.4, fy=0.4))
    return path


# ---------------------------------------------------------------- transcription side

def master_pages(path=lp.MASTER_ORIGINAL):
    """List of pages; each page is a list of lines; each line a list of rune indices.
    Defaults to the unmodified community transcription, which is what Phase 2 checks."""
    with open(path, encoding="utf-8") as f:
        body = f.read().split("\n\n", 1)[1].split("§")[0]
    pages = []
    for p in body.split("%"):
        lines = []
        for l in p.split("/"):
            r = [lp.RUNE_IDX[c] for c in l if c in lp.RUNE_IDX]
            if r:
                lines.append(r)
        pages.append(lines)
    return pages


def align_lines(mlines, dlines):
    """Pair transcription lines with detected lines by glyph count (DP; extra detected lines
    are decoration). Returns list of (mi, di) with None for unpaired."""
    n, m = len(mlines), len(dlines)
    D = np.full((n + 1, m + 1), np.inf)
    B = np.zeros((n + 1, m + 1), int)
    D[n, m] = 0
    for i in range(n, -1, -1):
        for j in range(m, -1, -1):
            if i == n and j == m:
                continue
            opts = []
            if i < n and j < m:
                opts.append((D[i + 1, j + 1] + abs(len(mlines[i]) - len(dlines[j])), 0))
            if i < n:
                opts.append((D[i + 1, j] + len(mlines[i]), 1))
            if j < m:
                opts.append((D[i, j + 1] + len(dlines[j]) * 0.5, 2))
            D[i, j], B[i, j] = min(opts)
    i = j = 0
    pairs = []
    while i < n or j < m:
        b = B[i, j]
        if b == 0:
            pairs.append((i, j)); i += 1; j += 1
        elif b == 1:
            pairs.append((i, None)); i += 1
        else:
            pairs.append((None, j)); j += 1
    return pairs


def align_glyphs(runes, logp, wide=None, gap_glyph=5.0, gap_rune=7.0, join_cost=3.5):
    """Needleman-Wunsch: transcription runes vs detected glyphs (logp: glyph x 29 log-probs).
    Returns ops: ('m', ri, gi) match/substitute, ('x', None, gi) extra glyph,
    ('-', ri, None) missing glyph, ('j', ri, gi) runes ri and ri+1 drawn as one touching glyph
    (only allowed where wide[gi] is true)."""
    n, m = len(runes), len(logp)
    wide = wide if wide is not None else [False] * m
    D = np.full((n + 1, m + 1), np.inf)
    B = np.zeros((n + 1, m + 1), int)
    D[0, 0] = 0
    for i in range(n + 1):
        for j in range(m + 1):
            if i and j and D[i - 1, j - 1] - logp[j - 1][runes[i - 1]] < D[i, j]:
                D[i, j], B[i, j] = D[i - 1, j - 1] - logp[j - 1][runes[i - 1]], 0
            if j and D[i, j - 1] + gap_glyph < D[i, j]:
                D[i, j], B[i, j] = D[i, j - 1] + gap_glyph, 2
            if i and D[i - 1, j] + gap_rune < D[i, j]:
                D[i, j], B[i, j] = D[i - 1, j] + gap_rune, 1
            if i >= 2 and j and wide[j - 1] and D[i - 2, j - 1] + join_cost < D[i, j]:
                D[i, j], B[i, j] = D[i - 2, j - 1] + join_cost, 3
    ops, i, j = [], n, m
    while i or j:
        b = B[i, j]
        if b == 0:
            ops.append(("m", i - 1, j - 1)); i -= 1; j -= 1
        elif b == 2:
            ops.append(("x", None, j - 1)); j -= 1
        elif b == 3:
            ops.append(("j", i - 2, j - 1)); i -= 2; j -= 1
        else:
            ops.append(("-", i - 1, None)); i -= 1
    return ops[::-1]


# ---------------------------------------------------------------- classifier

def make_classifier():
    from sklearn.decomposition import PCA
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.pipeline import make_pipeline
    return make_pipeline(PCA(60, random_state=0), KNeighborsClassifier(7, weights="distance"))


def log_proba(clf, X):
    P = np.full((len(X), lp.N), 1e-3)
    P[:, clf.classes_] += clf.predict_proba(X)
    P /= P.sum(axis=1, keepdims=True)
    return np.log(P)


def verify():
    os.makedirs(OUT, exist_ok=True)
    mp = master_pages()
    pages = {}
    for p, mlines in enumerate(mp):
        if not mlines:
            continue
        n = image_of(p)
        dlines, H, _ = segment(n)
        pairs = align_lines(mlines, dlines)
        feats = [[g.feature().ravel() for g in l] for l in dlines]
        pages[p] = (n, mlines, dlines, pairs, feats)
        print(f"segmented page {p:2d} (img {n:02d})", end="\r")

    # bootstrap training set: lines whose glyph count equals the transcription's
    def training(parity):
        X, y = [], []
        for p, (n, ml, dl, pairs, feats) in pages.items():
            if p % 2 != parity:
                continue
            for mi, di in pairs:
                if mi is not None and di is not None and len(ml[mi]) == len(dl[di]):
                    X += feats[di]
                    y += ml[mi]
        return np.array(X), np.array(y)

    clfs = {}
    for parity in (0, 1):
        X, y = training(parity)
        clfs[parity] = make_classifier().fit(X, y)
        print(f"\ntrained on parity {parity}: {len(y)} glyphs")

    rows, agree, total, joins = [], 0, 0, []
    coverage = {}  # page -> [runes in transcription, glyphs agreeing, runes in ᚳ joins]
    for p, (n, ml, dl, pairs, feats) in pages.items():
        clf = clfs[1 - p % 2]  # never predict a page with a model trained on it
        cov = coverage.setdefault(p, [sum(map(len, ml)), 0, 0])
        for mi, di in pairs:
            if mi is None:  # detected line with no transcription line: decoration
                continue
            if di is None:
                rows.append(dict(page=p, img=n, line=mi, pos=None, op="missing-line",
                                 trans=None, pred=None, conf=None, box=None))
                continue
            logp = log_proba(clf, np.array(feats[di]))
            Hl = np.median([g.h for g in dl[di]])
            wide = [g.w > 0.5 * Hl and g.kind != "dropcap" for g in dl[di]]
            ops = align_glyphs(ml[mi], logp, wide)
            matched = [k for k, o in enumerate(ops) if o[0] in "mj"]
            last = 0
            for k, (op, ri, gi) in enumerate(ops):
                if op == "j":
                    joins.append((p, mi, ri, ml[mi][ri], ml[mi][ri + 1]))
                    cov[2] += 2 if ml[mi][ri] == 5 else 0
                    last = gi + 1
                    if ml[mi][ri] != 5:  # only ᚳ is known to touch its neighbour; review the rest
                        g = dl[di][gi]
                        rows.append(dict(page=p, img=n, line=mi, pos=ri, op="join",
                                         trans=ml[mi][ri], pred=ml[mi][ri + 1], conf=None,
                                         box=[int(v) for v in (g.x, g.y, g.w, g.h)],
                                         near=[int(v) for v in (g.x, g.y, g.w, g.h)], kind=g.kind))
                    continue
                if op == "x" and matched and (k < matched[0] or k > matched[-1]):
                    last = gi + 1  # extra glyph outside the text run: decoration
                    continue
                g = dl[di][gi] if gi is not None else None
                near = dl[di][gi if gi is not None else min(last, len(dl[di]) - 1)]
                last = gi + 1 if gi is not None else last
                pred = int(np.argmax(logp[gi])) if gi is not None else None
                conf = float(np.exp(logp[gi][pred])) if gi is not None else None
                if op == "m":
                    total += 1
                    if pred == ml[mi][ri]:
                        agree += 1
                        cov[1] += 1
                        continue
                rows.append(dict(page=p, img=n, line=mi, pos=ri, op=op,
                                 trans=ml[mi][ri] if ri is not None else None, pred=pred,
                                 conf=round(conf, 3) if conf is not None else None,
                                 box=[int(v) for v in (g.x, g.y, g.w, g.h)] if g else None,
                                 near=[int(v) for v in (near.x, near.y, near.w, near.h)],
                                 kind=g.kind if g else None))
    print(f"matched glyphs {total}, classifier agrees with transcription on {agree} "
          f"({100 * agree / total:.2f}%)")
    from collections import Counter
    print(f"{len(joins)} touching rune pairs (one glyph, two runes); first rune:",
          Counter(lp.LATIN[j[3]] for j in joins).most_common(8))
    with open(os.path.join(OUT, "coverage.json"), "w", encoding="utf-8") as f:
        json.dump(coverage, f)
    with open(os.path.join(OUT, "joins.json"), "w", encoding="utf-8") as f:
        json.dump([[int(v) for v in j] for j in joins], f)
    with open(os.path.join(OUT, "disagreements.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=0)
    return rows


def review_sheets(rows, per_sheet=10):
    """Context crops for each disagreement: tmp/phase2/review_NN.png (+ index in review.txt)."""
    tiles, lines = [], []
    cache = {}
    for k, r in enumerate(rows):
        if r["op"] == "missing-line":
            continue
        if r["img"] not in cache:
            cache = {r["img"]: cv2.imread(os.path.join(ORIG, f"{r['img']:02d}.jpg"))}
        img = cache[r["img"]]
        x, y, w, h = r["box"] or r["near"]
        x0, x1 = max(0, x - 5 * h), min(img.shape[1], x + w + 5 * h)
        y0, y1 = max(0, y - h // 3), min(img.shape[0], y + h + h // 3)
        crop = img[y0:y1, x0:x1].copy()
        if r["box"]:
            cv2.rectangle(crop, (x - x0, y - y0), (x - x0 + w, y - y0 + h), (0, 0, 255), 4)
        else:  # missing rune: mark the gap after the nearest glyph
            cv2.line(crop, (x - x0 + w + 4, 0), (x - x0 + w + 4, crop.shape[0]), (255, 0, 255), 4)
        crop = cv2.resize(crop, (900, int(crop.shape[0] * 900 / crop.shape[1])))
        t = lp.LATIN[r["trans"]] if r["trans"] is not None else "-"
        pr = lp.LATIN[r["pred"]] if r["pred"] is not None else "-"
        label = f"#{k} p{r['page']} L{r['line']} i{r['pos']} {r['op']} T={t} P={pr} c={r['conf']}"
        bar = np.full((40, 900, 3), 255, np.uint8)
        cv2.putText(bar, label, (5, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
        tiles.append(np.vstack([bar, crop[:220]]))
        lines.append(label)
    paths = []
    for s_ in range(0, len(tiles), per_sheet):
        group = tiles[s_:s_ + per_sheet]
        hmax = max(t.shape[0] for t in group)
        group = [np.pad(t, ((0, hmax - t.shape[0]), (0, 0), (0, 0)), constant_values=255) for t in group]
        sheet = np.vstack([np.vstack([t, np.full((8, 900, 3), 120, np.uint8)]) for t in group])
        path = os.path.join(OUT, f"review_{s_ // per_sheet:02d}.png")
        cv2.imwrite(path, sheet)
        paths.append(path)
    with open(os.path.join(OUT, "review.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return paths


def main(argv):
    if argv[1] == "seg":
        n = int(argv[2])
        lines, H, img = segment(n)
        print(f"image {n:02d}: rune height {H}px, {len(lines)} lines, glyphs per line {[len(l) for l in lines]}")
        print(overlay(n, lines, img))
    elif argv[1] == "verify":
        rows = verify()
        from collections import Counter
        print(Counter(r["op"] for r in rows))
        print(len(review_sheets(rows)), "review sheets in", OUT)


if __name__ == "__main__":
    main(sys.argv)
