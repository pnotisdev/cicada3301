"""Full-segment check of the best prngx candidates against random-seed controls (like work/phpmt/verify_top.py).

    python work/prngx/verify.py results/prngx/mt_a_small.tsv --gen mt [--top 20] [--controls 40]

A candidate (seed, variant) is re-decoded over the WHOLE segment and compared with the same decode under random
seeds. Random seeds decode LP2 to about 0.08 (share of runes in dictionary words); a true key to about 0.8.
A hit is flagged only above 0.25 (the best of 4,000 selected candidates reaches ~0.12 by selection alone).
"""
import argparse
import os
import random
import statistics
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EXE = os.environ.get("PRNGX_BIN") or os.path.join(HERE, "target", "release", "prngx" + (".exe" if os.name == "nt" else ""))
DATA = os.path.join(ROOT, "work", "phpmt", "data")
WINDOWS = os.path.join(DATA, "windows_07.txt")
DICT = os.path.join(DATA, "dict.txt")
FLAG = 0.25      # a true key decodes the whole segment to ~0.8; selection noise reaches ~0.12


def verify(gen, seed, window, model, mapping, sign, atb, windows):
    out = subprocess.run([EXE, "verify", gen, windows, DICT, str(seed), window, str(mapping), str(model), str(sign),
                          str(atb)], capture_output=True, text=True, check=True).stdout
    score, _, text = out.strip().split("\t", 2)
    return float(score), text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tsv")
    ap.add_argument("--gen", required=True)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--controls", type=int, default=40)
    ap.add_argument("--windows", default=WINDOWS)
    a = ap.parse_args()
    rng = random.Random(3301)
    with open(a.tsv, encoding="utf-8") as f:
        rows = [line.split("\t") for line in f.read().splitlines()[1:]]
    print(f"== {os.path.relpath(a.tsv, ROOT).replace(os.sep, '/')} ({a.gen}): {len(rows)} candidates, checking top {a.top}")
    seen = set()
    for r in rows[: a.top]:
        score, seed, window, model, mapping, sign, atb = r[:7]
        key = (seed, window, model, mapping, sign, atb)
        if key in seen:
            continue
        seen.add(key)
        full, text = verify(a.gen, seed, window, model, mapping, sign, atb, a.windows)
        null = [verify(a.gen, rng.randrange(2 ** 32), window, model, mapping, sign, atb, a.windows)[0]
                for _ in range(a.controls)]
        mu, sd = statistics.mean(null), statistics.pstdev(null) or 1e-9
        flag = "  <-- CHECK" if full > max(mu + 6 * sd, FLAG) else ""
        print(f"  screen {score:>3} seed {seed:>11} {window} model {model} map {mapping} sign {sign:>2} atb {atb}: "
              f"full {full:.3f} (random seeds {mu:.3f} +- {sd:.3f}, z {(full - mu) / sd:+.1f}){flag}")
        if flag:
            print("    ", text[:200])


if __name__ == "__main__":
    sys.exit(main())
