"""Full-segment check of the best hashscan candidates against random-candidate controls.

    python work/hashscan/verify.py results/hashscan/lore.tsv [--top 20] [--controls 40]

A candidate (string, algo, conv, map, model, sign, atb) is decoded over the WHOLE segment and compared with random
candidate strings under the same variant. Random candidates decode LP2 to about 0.08 (share of runes in dictionary
words); a true key to about 0.8. A hit is flagged only above 0.25.
"""
import argparse
import os
import random
import statistics
import string
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EXE = os.environ.get("HASHSCAN_BIN") or os.path.join(HERE, "target", "release", "hashscan" + (".exe" if os.name == "nt" else ""))
DATA = os.path.join(ROOT, "work", "phpmt", "data")
WINDOWS = os.path.join(DATA, "windows_07.txt")
DICT = os.path.join(DATA, "dict.txt")
FLAG = 0.25


def verify(cand, algo, conv, mp, model, sign, atb, windows, window):
    out = subprocess.run([EXE, "verify", algo, conv, mp, model, sign, atb, cand, windows, DICT, window],
                         capture_output=True, text=True, check=True, encoding="utf-8").stdout
    score, _, text = out.rstrip("\n").split("\t", 2)
    return float(score), text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tsv")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--controls", type=int, default=40)
    ap.add_argument("--windows", default=WINDOWS)
    a = ap.parse_args()
    rng = random.Random(3301)
    with open(a.tsv, encoding="utf-8") as f:
        rows = [line.rstrip("\n").split("\t") for line in f.read().splitlines()[1:]]
    print(f"== {os.path.relpath(a.tsv, ROOT).replace(os.sep, '/')}: {len(rows)} candidates, checking top {a.top}")
    seen = set()
    for r in rows[: a.top]:
        score, cand, window, algo, conv, mp, model, sign, atb = r[:9]
        key = tuple(r[1:])
        if key in seen:
            continue
        seen.add(key)
        full, text = verify(cand, algo, conv, mp, model, sign, atb, a.windows, window)
        null = [verify("".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randrange(5, 12))), algo, conv, mp, model,
                       sign, atb, a.windows, window)[0] for _ in range(a.controls)]
        mu, sd = statistics.mean(null), statistics.pstdev(null) or 1e-9
        flag = "  <-- CHECK" if full > max(mu + 6 * sd, FLAG) else ""
        print(f"  screen {score:>3} {cand[:28]!r:30s} a{algo} c{conv} m{mp} model {model} sign {sign:>2} atb {atb}: full {full:.3f} "
              f"(random strings {mu:.3f} +- {sd:.3f}, z {(full - mu) / sd:+.1f}){flag}")
        if flag:
            print("    ", text[:200])


if __name__ == "__main__":
    sys.exit(main())
