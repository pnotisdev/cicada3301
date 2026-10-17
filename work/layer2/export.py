"""Inputs for the two-layer screen (work/layer2).

    python work/layer2/export.py

data/core.ksb      the number-theoretic part of the kscreen library (work/kscreen/data/library.ksb, built by
                   work/kscreen/export.py): integer sequences, constants' digits, Cicada numbers. Hash streams and
                   solved-text keywords are left out (the outer layer of H-LAYER is "a number stream"); the layer2
                   screen runs every offset of each.
data/core20.ksb    20 of them closest to the solved pages' methods and Cicada's numbers (CORE20 below)
data/keywords.txt  keywords for mode=bigram / known: the keys of the solved pages and Cicada words (30)
data/keywords_solved.txt  the three keys of the solved pages (DIVINITY, FIRFUMFERENFE, CIRCUMFERENCE)
data/combined.ksb  variant A1: each CORE20 stream with a solved key folded in (one pointer for both), every phase and sign
data/keyword_none.txt  the trivial keyword "NONE 0": with it mode=bigram is a single-layer screen scored by English bigrams
data/plain.txt     held-out English windows for the controls (a copy of work/phpmt/data/english.txt)
"""
import os
import re
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, WORK)
import lp  # noqa: E402

OUT = os.path.join(HERE, "data")
LIB = os.path.join(WORK, "kscreen", "data", "library.ksb")

# the streams closest to the solved pages' own methods (An End: phi of the primes) and to Cicada's numbers, for the
# screens whose keyword list makes the full core set too slow
CORE20 = ["primes", "primes-1 (totient)", "primes+1", "phi(n)", "sigma(n)", "n", "n^2", "triangular", "fibonacci", "lucas",
          "pi digits (base 10)", "pi digits (base 29)", "e digits (base 10)", "e digits (base 29)", "phi digits (base 29)",
          "sqrt2 digits (base 29)", "primes from 3301", "3301*n", "cumulative prime sum", "gematria primes cycle"]
SOLVED = ["DIVINITY", "FIRFUMFERENFE", "CIRCUMFERENCE"]

KEYWORDS = ["DIVINITY", "FIRFUMFERENFE", "CIRCUMFERENCE", "INSTAR", "EMERGENCE", "PRIMALITY", "TOTIENT", "PILGRIM",
            "CICADA", "LIBERPRIMUS", "INTUS", "PARABLE", "KOAN", "WELCOME", "PRIMES", "SACRED", "WISDOM",
            "INSTRUCTION", "WARNING", "TRUTH", "ENLIGHTENED", "CONSUMPTION", "PRESERVATION", "ADHERENCE",
            "DECEPTION", "CIRCUMFERENCES", "SURFACE", "EMERGE", "THEPRIMESARESACRED", "AWARNING"]


def read_ksb(path):
    with open(path, "rb") as f:
        b = f.read()
    assert b[:4] == b"KSB1", path
    n = struct.unpack_from("<I", b, 4)[0]
    p, out = 8, []
    for _ in range(n):
        ln = struct.unpack_from("<H", b, p)[0]
        p += 2
        name = b[p:p + ln].decode("utf-8")
        p += ln
        L = struct.unpack_from("<I", b, p)[0]
        p += 4
        out.append((name, b[p:p + L]))
        p += L
    return out


def write_ksb(path, items):
    with open(path, "wb") as f:
        f.write(b"KSB1" + struct.pack("<I", len(items)))
        for name, v in items:
            nb = name.encode("utf-8")
            f.write(struct.pack("<H", len(nb)) + nb + struct.pack("<I", len(v)) + bytes(v))


def is_core(name):
    return not (name.startswith("kw:") or name.startswith("sha") or name.startswith("md5")
                or "payload" in name or name.startswith("hash"))


def main():
    if not os.path.exists(LIB):
        sys.exit(f"missing {os.path.relpath(LIB, WORK)}: run python work/kscreen/export.py first")
    os.makedirs(OUT, exist_ok=True)
    core = [(n, v) for n, v in read_ksb(LIB) if is_core(n)]
    write_ksb(os.path.join(OUT, "core.ksb"), core)
    with open(os.path.join(OUT, "core.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(n for n, _ in core) + "\n")
    names = {n: v for n, v in core}
    missing = [n for n in CORE20 if n not in names]
    assert not missing, f"CORE20 streams missing from the library: {missing}"
    write_ksb(os.path.join(OUT, "core20.ksb"), [(n, names[n]) for n in CORE20])
    # variant A1: the keyword folded into the stream with ONE pointer, k_j = S_j + s*K[(j + phase) mod m] (the anti-repeat
    # rule then acts on the combined key); screened as a single layer with the trivial keyword of keyword_none.txt
    comb = []
    for n in CORE20:
        v = names[n]
        for w in SOLVED:
            key = lp.word_to_key(w)
            m = len(key)
            for sgn in (1, 28):
                for ph in range(m):
                    comb.append((f"{n} + {sgn}*{w}@{ph}", bytes((v[j] + sgn * key[(j + ph) % m]) % 29 for j in range(len(v)))))
    write_ksb(os.path.join(OUT, "combined.ksb"), comb)
    with open(os.path.join(OUT, "keyword_none.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write("# the trivial keyword: mode=bigram becomes a single-layer screen scored by English bigrams\nNONE 0\n")
    for fname, words, title in (("keywords.txt", KEYWORDS, "keys of the solved pages and Cicada words"),
                                ("keywords_solved.txt", SOLVED, "the keys of the solved pages")):
        with open(os.path.join(OUT, fname), "w", newline="\n", encoding="utf-8") as f:
            f.write(f"# name rune values (Gematria Primus indices); {title}\n")
            for w in words:
                key = lp.word_to_key(re.sub(r"[^A-Z]", "", w))
                f.write(w + " " + " ".join(map(str, key)) + "\n")
    shutil.copyfile(os.path.join(WORK, "phpmt", "data", "english.txt"), os.path.join(OUT, "plain.txt"))
    print(f"layer2 export: {len(core)} core streams, {len(KEYWORDS)} keywords -> {os.path.relpath(OUT, WORK)}")


if __name__ == "__main__":
    main()
