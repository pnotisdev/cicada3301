"""P-8: label-free audit of the doublet sites (are LP2's missing doublets a transcription artefact?).

Two identical adjacent runes have near-identical glyph bitmaps. For every adjacent glyph pair
on the unsolved pages, compute the bitmap correlation. Calibrate on lines whose image glyph count
equals the transcription's (canon tells which pairs are doublets), then count image doublets
everywhere and compare with canon's 86. A transcriber who merged a doubled rune would leave an
image doublet that canon lacks (and a line where the image has one more glyph than canon).

    python doublet_audit.py
"""
import json
import os
import sys

import numpy as np

import lp
import ocr

HERE = os.path.dirname(os.path.abspath(__file__))


def sim(a, b):
    a = a - a.mean()
    b = b - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d else 0.0


def run(pages=range(15, 71)):
    mp = ocr.master_pages(lp.MASTER)
    matched_d, matched_nd, extra_lines, image_doublets = [], [], [], []
    canon_doublets = 0
    for p in pages:
        ml = mp[p]
        if not ml:
            continue
        canon_doublets += sum(a == b for line in ml for a, b in zip(line, line[1:]))
        dl, H, _ = ocr.segment(ocr.image_of(p))
        for mi, di in ocr.align_lines(ml, dl):
            if mi is None or di is None:
                continue
            glyphs = [g for g in dl[di] if g.kind != "dropcap"]
            feats = [g.feature() for g in glyphs]
            sims = [sim(a, b) for a, b in zip(feats, feats[1:])]
            canon = ml[mi][1:] if any(g.kind == "dropcap" for g in dl[di]) else ml[mi]
            if len(canon) == len(glyphs):
                for k, s in enumerate(sims):
                    (matched_d if canon[k] == canon[k + 1] else matched_nd).append((s, p, mi, k))
            else:
                extra_lines.append((p, mi, len(canon), len(glyphs), max(sims) if sims else 0))
            for k, s in enumerate(sims):
                image_doublets.append((s, p, mi, k, len(canon) == len(glyphs)))
        print(f"page {p}", end="\r", flush=True)
    return canon_doublets, matched_d, matched_nd, extra_lines, image_doublets


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    canon, md, mnd, extra, img = run()
    sd = np.array([s for s, *_ in md])
    snd = np.array([s for s, *_ in mnd])
    print(f"\ncanon doublets on unsolved pages: {canon}")
    print(f"count-matched lines: {len(md)} canon-doublet pairs, {len(snd)} non-doublet pairs")
    print(f"  bitmap similarity, canon doublets:     min {sd.min():.3f}  median {np.median(sd):.3f}")
    print(f"  bitmap similarity, non-doublet pairs:  max {snd.max():.3f}  99.9% {np.percentile(snd, 99.9):.3f}")
    thr = (sd.min() + snd.max()) / 2 if sd.min() > snd.max() else np.percentile(sd, 1)
    print(f"  threshold {thr:.3f} (clean separation: {sd.min() > snd.max()})")
    imgd = [r for r in img if r[0] >= thr]
    print(f"image doublets (similarity >= threshold) on all aligned lines: {len(imgd)}")
    not_canon = [r for r in imgd if not r[4]]
    print(f"  of which on lines whose glyph count differs from canon: {len(not_canon)} {not_canon[:10]}")
    print(f"lines with glyph count != canon: {len(extra)}; with image > canon: "
          f"{sum(1 for e in extra if e[3] > e[2])}")
    with open(os.path.join(HERE, "tmp", "phase4", "doublet_audit.json"), "w") as f:
        json.dump({"canon": canon, "matched_doublet_sims": sd.tolist(), "nondoublet_max": float(snd.max()),
                   "threshold": float(thr), "image_doublets": len(imgd), "extra_lines": extra}, f)
