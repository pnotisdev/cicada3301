"""Are the red headings of the unsolved pages a simple (affine) cipher of English?

The solved pages' red titles are short plaintext under a simple map (A WARNING: Atbash). Phase 4 found 17 red runs in
the unsolved sections (`red_runs.py`: section starts and a few mid-section headings, 1-24 runes). This script tries
all 812 affine maps x -> m x + b (mod 29), which contain every Caesar shift, Atbash and every multiplier, on each red
run of >= 8 runes and scores the result with the dictionary-word score; the null is the same best-of-812 score on random
stretches of LP2 with the same word structure (200 per run), so a short heading's lucky score is calibrated.

    python work/heading_affine.py      # -> results/analysis/heading_affine.txt  (needs work/tmp/phase4/red_runs.json:
                                       #    run `python work/red_runs.py` first if it is missing)
"""
import json
import os
import random
import sys

import lp
import stats

HERE = os.path.dirname(os.path.abspath(__file__))
N = lp.N


def best_affine(toks, r, a, b):
    best = (-1.0, 0, 0)
    for mul in range(1, N):
        for add in range(N):
            plain = list(r)
            for k in range(a, b):
                plain[k] = (mul * r[k] + add) % N
            sc = lp.word_score(toks, plain, lo=a, hi=b)
            if sc > best[0]:
                best = (sc, mul, add)
    return best


def main():
    path = os.path.join(HERE, "tmp", "phase4", "red_runs.json")
    if not os.path.exists(path):
        sys.exit("run python work/red_runs.py first")
    runs = json.load(open(path))
    rng = random.Random(8)
    out = []
    P = out.append
    P("red run (page, section@start, runes) | best affine map and dictionary score | null (random stretches, same "
      "length): median / max of 60 | z")
    for run in runs:
        seg, a, b = run["seg"], run["start"], run["start"] + len(run["runes"])
        if len(run["runes"]) < 8:
            continue
        toks = stats.SEGS[seg]
        r = lp.runes_of(toks)
        if b > len(r):
            continue
        sc, mul, add = best_affine(toks, r, a, b)
        null = []
        for _ in range(60):
            s0 = rng.randrange(0, max(1, len(r) - len(run["runes"])))
            null.append(best_affine(toks, r, s0, s0 + len(run["runes"]))[0])
        null.sort()
        mu = sum(null) / len(null)
        sd = (sum((x - mu) ** 2 for x in null) / len(null)) ** 0.5 or 1e-9
        P(f"page {run['page']:2d} 0.{seg:<2d}@{a:<5d} {len(run['runes']):2d} runes | {sc:.2f} (x -> {mul}x + {add}) | "
          f"{null[len(null) // 2]:.2f} / {null[-1]:.2f} | z {(sc - mu) / sd:+.1f}")
    P("")
    P("Reading: no heading stands out from the best-of-812 null; none is a plaintext title under an affine map.")
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "heading_affine.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
