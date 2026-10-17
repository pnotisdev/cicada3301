"""Short (~36-rune) decoding windows for the integer-sequence lane: most OEIS entries hold only 40-100 terms.

    python work/prngx/short_windows.py <windows.txt> <out.txt> [--runes 36]

Cuts every window of the input at its last word end within --runes runes (the dictionary decoder needs word ends).
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
        head, r, l = lines[k], lines[k + 1], lines[k + 2]
        runes = r[2:].split()
        lens = [int(x) for x in l[2:].split()]
        tot, keep = 0, []
        for L in lens:
            if tot + L > a.runes:
                break
            tot += L
            keep.append(L)
        if not keep:
            continue
        out += [head, "R " + " ".join(runes[:tot]), "L " + " ".join(map(str, keep))]
    with open(a.dst, "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"{len(out) // 3} windows -> {a.dst}")


if __name__ == "__main__":
    sys.exit(main())
