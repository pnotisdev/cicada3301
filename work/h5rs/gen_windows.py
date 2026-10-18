"""Build the h5rs sweep windows file: the 8 LP2 section windows (first 300 runes each of
work/kscreen/data/segments.txt, prev rune from the W line) in the kscreen/h5rs window format
(W name prev / R runes). L/B lines are not needed by the H5 decode (word-agnostic).

Run from anywhere; writes work/h5rs/data/lp2_windows.txt next to this script.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SEGMENTS = os.path.join(HERE, "..", "kscreen", "data", "segments.txt")
OUT = os.path.join(HERE, "data", "lp2_windows.txt")
N_WIN = 8
N_RUNES = 300

windows = []  # (name, prev, [runes])
cur = None
with open(SEGMENTS, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "W":
            name = parts[1]
            prev = int(parts[2]) if len(parts) > 2 else -1
            cur = [name, prev, []]
            windows.append(cur)
        elif parts[0] == "R" and cur is not None:
            cur[2].extend(int(x) for x in parts[1:])

assert len(windows) == N_WIN, f"expected {N_WIN} windows, got {len(windows)}"
for name, prev, runes in windows:
    assert len(runes) >= N_RUNES, f"{name}: only {len(runes)} runes"
    assert all(0 <= r < 29 for r in runes), f"{name}: rune out of range"

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    for name, prev, runes in windows:
        f.write(f"W {name} {prev}\n")
        f.write("R " + " ".join(str(r) for r in runes[:N_RUNES]) + "\n")

print(f"wrote {OUT}: {len(windows)} windows x {N_RUNES} runes")
for name, prev, runes in windows:
    print(f"  {name} prev={prev} first3={runes[:3]} last3={runes[-3:]}")
