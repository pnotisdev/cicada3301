"""Windows for the ciphertext-feedback hypothesis  c_i = a*c_{i-1} + p_i + k_i  (mod 29), with the anti-repeat rule on c.

Every earlier kscreen run assumed c = p + k. If instead each rune is also shifted by a multiple a of the previous
ciphertext rune, the key sits in c'_i = c_i - a*c_{i-1}, and the encryptor's collision check "c_i == c_{i-1}" reads, in
terms of the candidate plaintext+key sum s = p_i + k_j:  s == (1 - a) * c_{i-1}.  So a window of c' values with a `P`
line holding (1 - a) * c_{i-1} is screened by the unchanged engine. a = 0 is the ordinary model; a = 1 is the
difference sequence c_i - c_{i-1} with the check "s == 0" (a cipher that never shifts by zero).

    python work/kscreen/chain_windows.py [a ...]         # default: a = 1..28 for segments, heads, pages
    -> data/chain/<segments|heads|pages>_a<a>.txt
    python work/kscreen/chain_windows.py --reverse [a ...]   # default: a = 0..28 for segments
    -> data/chain/segments_a<a>_rev.txt

Reversed windows are for a key that runs BACKWARD through the text (read from the end; the encryptor still works front to
back, so each rune's anti-repeat check refers to the rune before it in the text). Reversing both arrays of a window does
exactly that: the engine moves a forward key pointer along the reversed text, and the reference of each position is still
the text-preceding rune, which is the next element of the reversed array. a = 0 is the ordinary model, reversed.

The first rune of a window is dropped when the rune before it is unknown (the start of segment 0.7).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
Q = 29


def read_windows(path):
    wins = []
    with open(path, encoding="utf-8") as f:
        for line in f.read().splitlines():
            if line.startswith("W "):
                p = line[2:].split()
                wins.append({"name": p[0], "prev": int(p[1]) if len(p) > 1 else -1, "R": [], "P": None})
            elif line.startswith("R "):
                wins[-1]["R"] = [int(x) for x in line[2:].split()]
            elif line.startswith("P "):
                wins[-1]["P"] = [int(x) for x in line[2:].split()]
    return wins


def chain_window(w, a):
    c = w["R"]
    before = [w["prev"] if i == 0 else c[i - 1] for i in range(len(c))]
    keep = [i for i in range(len(c)) if before[i] >= 0]
    new_c = [(c[i] - a * before[i]) % Q for i in keep]
    new_p = [((1 - a) * before[i]) % Q for i in keep]
    return {"name": w["name"], "prev": -1, "R": new_c, "P": new_p}


def write_windows(wins, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        for w in wins:
            f.write(f"W {w['name']} {w['prev']}\nR {' '.join(map(str, w['R']))}\nP {' '.join(map(str, w['P']))}\n")


def reverse_window(w):
    return {"name": w["name"], "prev": -1, "R": w["R"][::-1], "P": w["P"][::-1]}


def make(a, kind, data=os.path.join(HERE, "data"), reverse=False):
    src = read_windows(os.path.join(data, f"{kind}.txt"))
    dst = os.path.join(data, "chain", f"{kind}_a{a}{'_rev' if reverse else ''}.txt")
    wins = [chain_window(w, a) for w in src]
    write_windows([reverse_window(w) for w in wins] if reverse else wins, dst)
    return dst


def main():
    args = sys.argv[1:]
    reverse = "--reverse" in args
    vals = [int(x) for x in args if x != "--reverse"] or list(range(0 if reverse else 1, Q))
    for kind in (("segments",) if reverse else ("segments", "heads", "pages")):
        for a in vals:
            make(a, kind, reverse=reverse)
    print(f"wrote {'reversed ' if reverse else ''}chain windows for a = {vals[0]}..{vals[-1]} ({len(vals)} values) "
          f"x {'segments' if reverse else 'segments, heads, pages'} in data/chain/")


if __name__ == "__main__":
    main()
