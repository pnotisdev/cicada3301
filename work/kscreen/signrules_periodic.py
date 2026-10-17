"""Per-rune PERIODIC key-sign templates for the kscreen engine (S lines): c_i = p_i + s_i * k_j with s_i = pattern[i mod L], L = 2..5 (the Beaufort / Vigenere alternation read as a sign pattern; proposed by an outside LLM's audit, 2026-10-18).

One representative per complement class (pattern[0] = +1; the complement is the multiplier 28 every screen tries); every phase of a cycle is covered because the rotations of a pattern are among the patterns. Constant patterns and patterns equal to a shorter one (+-+- is +-) are dropped: 1 + 3 + 6 + 15 = 25 templates.
The pattern is anchored at the first rune of each window.

    python work/kscreen/signrules_periodic.py          # -> data/signs_periodic/<name>.txt and sign_periodic_rules.txt (tracked)
"""
import itertools
import os

import signrules as R

OUT = os.path.join(R.HERE, "data", "signs_periodic")


def name_of(pat):
    return f"P{len(pat)}_" + "".join("p" if x > 0 else "m" for x in pat)


def vector(pat, n):
    return [pat[i % len(pat)] for i in range(n)]


def build():
    os.makedirs(OUT, exist_ok=True)
    wins = [(head, runes, lens) for head, runes, lens, _, _ in R.section_tables()]
    kept, seen = {}, set()
    for L in (2, 3, 4, 5):
        for tail in itertools.product((1, -1), repeat=L - 1):
            pat = (1,) + tail
            vec = tuple(x for _, runes, _ in wins for x in vector(pat, len(runes)))
            if len(set(vec)) == 1 or vec in seen:
                continue
            seen.add(vec)
            kept[name_of(pat)] = pat
    for name, pat in kept.items():
        with open(os.path.join(OUT, name + ".txt"), "w", newline="\n", encoding="utf-8") as f:
            for head, runes, lens in wins:
                f.write(f"{head}\nR {' '.join(map(str, runes))}\n{lens}\nS {' '.join(map(str, vector(pat, len(runes))))}\n")
    with open(os.path.join(R.HERE, "sign_periodic_rules.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(kept) + "\n")
    print(f"{len(kept)} periodic sign templates")
    return kept


if __name__ == "__main__":
    build()
