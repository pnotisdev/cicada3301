"""Fixed-length windows for the boundary-free lanes of prngx: the first N runes of every window of a windows file (no word ends needed).

    python work/prngx/bg_windows.py <windows.txt> <out.txt> [--runes 36] [--skip-short]

The L line is one word of N runes (the boundary-free decoder ignores it; the file stays loadable by the dictionary decoder).
"""
import argparse
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--runes", type=int, default=36)
    a = ap.parse_args()
    lines = open(a.src, encoding="utf-8").read().splitlines()
    out = []
    for k in range(0, len(lines), 3):
        head, r = lines[k], lines[k + 1]
        runes = r[2:].split()
        if len(runes) < a.runes:
            continue
        out += [head, "R " + " ".join(runes[:a.runes]), f"L {a.runes}"]
    with open(a.dst, "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"{len(out) // 3} windows of {a.runes} runes -> {a.dst}")


if __name__ == "__main__":
    sys.exit(main())
