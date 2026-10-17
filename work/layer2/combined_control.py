"""Positive control for layer2's variant A1 ('combined': a solved key folded into the stream, one pointer, screened with kw=NONE, isigns=1).

selftest.py plants the two-layer cipher with keyword lists; the A1 slice (data/combined.ksb, kw=data/keyword_none.txt) has no plant of its own. Here English windows are enciphered with one
combined stream under the skip / coin rule by the independent planter (plant_ref.py, keyword [0], so the whole key is the stream) and screened with exactly the A1 options; each window's best
must be that item at the true offset (within 2) with at least +2.0 per rune, and the whole-window re-decode at the truth must beat its matched null by 5 (verify.py's rule).

    python work/layer2/combined_control.py [--threads N]      # -> results/layer2/combined_control.txt
"""
import argparse
import os
import re
import sys

import selftest as S
import plant_ref
from export import read_ksb

HERE = S.HERE
ROOT = S.ROOT
PICKS = ((0, 2000, 1, 0), (7, 2000, 28, 1), (13, 2000, 1, 1), (19, 2000, 28, 0))      # (index in combined.ksb, first offset, mult, model)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=os.cpu_count())
    a = ap.parse_args()
    os.makedirs(S.TMP, exist_ok=True)
    ksb = os.path.join(HERE, "data", "combined.ksb")
    names = [n for n, _ in read_ksb(ksb)]
    lines, ok = [], True
    for pi, (idx, off, mult, model) in enumerate(PICKS):
        item = names[idx]
        plant = os.path.join(S.TMP, f"combined_plant{pi}.txt")
        tsv = os.path.join(S.TMP, f"combined_plant{pi}.tsv")
        text = plant_ref.plant(os.path.join(HERE, "data", "plain.txt"), ksb, item, off, mult, model, 0.18, 30 + pi, [0], 0, 1, 0, 0)
        with open(plant, "w", newline="\n", encoding="utf-8") as f:
            f.write(text)
        S.run(["screen", S.rel(plant), "file:data/combined.ksb", S.rel(tsv), "mode=bigram", "kw=data/keyword_none.txt", "litf=0", "isigns=1", f"only={item}", "offs=0:4000",
               f"threads={a.threads}"])
        best = S.window_bests(tsv)
        for win, toff in S.truths(plant).items():
            sc, bitem, boff, inner = best[win]
            good = bitem == item and abs(boff - toff) <= 2 and sc >= S.THRESH
            vout = S.run(["verify", S.rel(plant), "file:data/combined.ksb", item, str(toff), str(mult), str(model), win, "mode=bigram", "kwvals=0", "isign=1", "phase=0", "litf=0", "atb=0",
                          "controls=20"])
            vsc = float(re.search(r"score (-?[\d.]+)", vout).group(1))
            cmax = float(re.search(r"controls \d+ random offsets: mean (-?[\d.]+) max (-?[\d.]+)", vout).group(2))
            good &= vsc >= S.THRESH and vsc >= cmax + 5
            ok &= good
            lines.append(f"{'PASS' if good else 'FAIL'}  A1 plant {item!r} mult={mult} model={model} {win}: best {sc:+.3f} at offset {boff} (truth {toff}); whole window at truth {vsc:+.3f}, matched null max {cmax:+.3f}")
    lines.append("A1 CONTROL PASSED" if ok else "A1 CONTROL FAILED")
    out = os.path.join(ROOT, "results", "layer2", "combined_control.txt")
    with open(out, "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
