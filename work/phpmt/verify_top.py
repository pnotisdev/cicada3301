"""Full-segment check of the best PRNG-sweep candidates against random-seed controls.

    python work/phpmt/verify_top.py results/prng/php_07.tsv [more.tsv ...] [--top 20] [--controls 40]

The generator is taken from the file name prefix (php_, glibc_, net_). For each of the top candidates the
engine decodes the WHOLE segment (not just the 60-rune screening window) and reports the share of runes in
dictionary words. The same decode with random seeds (same window and variant) gives the null: random seeds
decode LP2 to about 0.08, while a planted true key decodes its whole text to about 0.8.
"""
import argparse
import os
import random
import statistics
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_NAME = "phpmt.exe" if os.name == "nt" else "phpmt"
EXE = os.environ.get("PHPMT_BIN") or next(
    (p for p in (os.path.join(HERE, d, "release", _NAME) for d in ("target_gen", "target")) if os.path.exists(p)),
    os.path.join(HERE, "target", "release", _NAME))
WINDOWS = os.path.join(HERE, "data", "windows.txt")
DICT = os.path.join(HERE, "data", "dict.txt")


def verify(gen, seed, window, model, mapping, sign, atb, windows=WINDOWS):
    out = subprocess.run([EXE, "verify", gen, windows, DICT, str(seed), window, str(mapping), str(model), str(sign),
                          str(atb)], capture_output=True, text=True, check=True).stdout
    score, _, text = out.strip().split("\t", 2)
    return float(score), text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tsv", nargs="+")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--controls", type=int, default=40)
    ap.add_argument("--windows", default=WINDOWS, help="windows file the TSV was produced from")
    ap.add_argument("--gen", default=None, help="generator (default: from the file name prefix)")
    a = ap.parse_args()
    rng = random.Random(3301)
    for path in a.tsv:
        gen = a.gen or os.path.basename(path).split("_")[0]
        if gen not in ("php", "glibc", "net"):
            gen = "php"
        rows = [line.split("\t") for line in open(path).read().splitlines()[1:]]
        print(f"== {path} ({gen}): {len(rows)} candidates, checking top {a.top}")
        seen = set()
        for r in rows[: a.top]:
            score, seed, window, model, mapping, sign, atb = r[:7]
            key = (seed, window, model, mapping, sign, atb)
            if key in seen:
                continue
            seen.add(key)
            full, text = verify(gen, seed, window, model, mapping, sign, atb, a.windows)
            hi = 2 ** 31 if gen == "net" else 2 ** 32
            null = [verify(gen, rng.randrange(hi), window, model, mapping, sign, atb, a.windows)[0]
                    for _ in range(a.controls)]
            mu, sd = statistics.mean(null), statistics.pstdev(null) or 1e-9
            flag = "  <-- CHECK" if full > mu + 6 * sd else ""
            print(f"  screen {score:>3} seed {seed:>10} {window} model {model} map {mapping} sign {sign:>2} atb {atb}: "
                  f"full {full:.3f} (random seeds {mu:.3f} +- {sd:.3f}, z {(full - mu) / sd:+.1f}){flag}")
            if flag:
                print("    ", text[:200])


if __name__ == "__main__":
    sys.exit(main())
