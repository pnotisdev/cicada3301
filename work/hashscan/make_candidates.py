"""Candidate lists for hashscan (one candidate per line, UTF-8). Written to work/hashscan/data/ (git-ignored).

    python work/hashscan/make_candidates.py

lore     Cicada strings and numbers, every word and 2-4-word phrase of the solved sections, the keyword list used by
         earlier screens; case variants (as is, lower, upper, no spaces)                        ~ 40k
words    the 20k-word frequency list, lower / UPPER / Capitalized                               ~ 60k
pairs    two of the 1,500 most frequent words, separators "", " ", "_", "-"                     ~ 9M
numbers  0 .. 9,999,999 as decimal strings                                                      10M
dates    YYYYMMDD, YYYY-MM-DD, DD.MM.YYYY and YYYY for 1900-2030                               ~ 0.6M
"""
import itertools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import grid60  # noqa: E402
import lp  # noqa: E402
import prng_screen  # noqa: E402

OUT = os.path.join(HERE, "data")


def write(name, items):
    os.makedirs(OUT, exist_ok=True)
    seen, n = set(), 0
    path = os.path.join(OUT, name + ".txt")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for s in items:
            if s and s not in seen and "\n" not in s:
                seen.add(s)
                f.write(s + "\n")
                n += 1
    print(f"{name}: {n:,} candidates -> {path}")


def variants(s):
    yield s
    yield s.lower()
    yield s.upper()
    yield s.replace(" ", "")
    yield s.lower().replace(" ", "")
    yield s.upper().replace(" ", "")
    yield s.replace(" ", "_")
    yield s.replace(" ", "-")


def lore():
    base = list(prng_screen.seeds()) + list(grid60.passphrases()) + list(lp.KEYWORDS)
    base += ["Liber Primus", "Cicada 3301", "3301", "1033", "an end", "a warning", "welcome", "pilgrim", "instar",
             "emergence", "the primes are sacred", "the circumferences", "divinity", "within", "intus", "deep web",
             "1a2b3c", "Cicada", "cicada", "CICADA", "primus", "liber", "gematria", "gematria primus", "runes"]
    for b in base:
        yield from variants(str(b))


def words():
    ws = sorted(lp.COMMON_N, key=lambda w: -lp.COMMON_N[w])
    for w in ws:
        yield w.lower()
        yield w.upper()
        yield w.capitalize()


def pairs(top=1500):
    ws = [w.lower() for w in sorted(lp.COMMON_N, key=lambda w: -lp.COMMON_N[w])[:top]]
    for a, b in itertools.product(ws, ws):
        for sep in ("", " ", "_", "-"):
            yield a + sep + b


def numbers():
    for i in range(10_000_000):
        yield str(i)


def dates():
    for y in range(1900, 2031):
        yield str(y)
        for m in range(1, 13):
            for d in range(1, 32):
                yield f"{y}{m:02d}{d:02d}"
                yield f"{y}-{m:02d}-{d:02d}"
                yield f"{d:02d}.{m:02d}.{y}"


if __name__ == "__main__":
    for name, gen in (("lore", lore), ("words", words), ("dates", dates), ("pairs", pairs), ("numbers", numbers)):
        write(name, gen())
