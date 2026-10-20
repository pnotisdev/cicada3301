"""Pointer-direction rules for the kscreen engine (pdir=, D lines): 'their numbers are the direction' read as the key pointer walking forward or backward through the key stream for each word, the direction d_w decided by a number of the transcription.

The 61 sign rules of signrules.py (same causal restriction: the current word's length and positions and anything of the PREVIOUS words' ciphertext) are reused as direction rules, +1 = forward, -1 = backward. Unlike signs the two orientations are different rules (negating a direction
rule is a reversed key stream, not the multiplier 28): the engine option dirneg=1 gives the second orientation, 122 vectors in all. Added here, on the Gematria Primus PRIME VALUES of a word (G = sum of the primes of its ciphertext runes, not of the rune indices R):
 G2_prev / G2_cur   G even -> forward   (A_prev_G already is G2_prev: dropped as a duplicate)
 G4_prev / G4_cur   G mod 4 in {0, 1} -> forward
 GP_prev / GP_cur   G prime -> forward
the *_cur variants use the word's OWN ciphertext, which the encryptor cannot know before it enciphers the word (acausal; kept as labelled extras because the quantities are the ones the 2016 message names), the *_prev variants are causal. Duplicates of a kept vector or of its
negation are dropped (the orientation pair covers both).

    python work/kscreen/dirrules.py      # -> data/dirs/<rule>.txt (windows with D lines), dir_rules.txt (kept names, tracked)
"""
import os

import signrules as R

OUT = os.path.join(R.HERE, "data", "dirs")
EXTRA_CAUSAL = ["G4_prev", "GP_prev"]
EXTRA_ACAUSAL = ["G2_cur", "G4_cur", "GP_cur"]


def is_prime(x):
    return x > 1 and all(x % p for p in range(2, int(x ** 0.5) + 1))


def extra_rules():
    def of(src, test):
        return lambda ws, w: (1 if test(src(ws, w)) else -1) if src(ws, w) is not None else 1
    prev = lambda ws, w: ws[w - 1]["G"] if w >= 1 else None
    cur = lambda ws, w: ws[w]["G"]
    return {
        "G4_prev": of(prev, lambda g: g % 4 <= 1),
        "GP_prev": of(prev, is_prime),
        "G2_cur": of(cur, lambda g: g % 2 == 0),
        "G4_cur": of(cur, lambda g: g % 4 <= 1),
        "GP_cur": of(cur, is_prime),
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    tabs = R.section_tables()
    base = R.build_rules()
    kept_names = [l.strip() for l in open(os.path.join(R.HERE, "sign_rules.txt"), encoding="utf-8") if l.strip()]
    rules = {n: base[n] for n in kept_names}
    rules.update(extra_rules())
    vec = lambda fn: tuple(x for (_, runes, _, spans, words) in tabs for x in R.sign_vector(fn, words, spans, len(runes)))
    seen, kept = {}, []
    for name, fn in rules.items():
        v = vec(fn)
        neg = tuple(-x for x in v)
        if len(set(v)) == 1 or v in seen or neg in seen:
            print("dropped", name)
            continue
        seen[v] = name
        kept.append(name)
        with open(os.path.join(OUT, name + ".txt"), "w", newline="\n", encoding="utf-8") as f:
            for head, runes, lens, spans, words in tabs:
                f.write(f"{head}\nR {' '.join(map(str, runes))}\n{lens}\nD {' '.join(map(str, R.sign_vector(fn, words, spans, len(runes))))}\n")
    with open(os.path.join(R.HERE, "dir_rules.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(kept) + "\n")
    print(f"{len(kept)} direction rules kept ({sum(n in base for n in kept)} from the sign campaign, {sum(n not in base for n in kept)} extra), {2 * len(kept)} vectors with both orientations")
    return rules, kept


if __name__ == "__main__":
    main()
