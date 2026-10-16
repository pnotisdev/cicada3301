"""Build the PRNG sweep engine's inputs in work/phpmt/data/ from the verified transcription.

    python work/phpmt/export_data.py

windows.txt     all unsolved segments with >= 100 runes (word lengths from lp.word_spans, wraps rejoined)
windows_07.txt  segment 0.7 only (LP2 page 0: the start of a whole-book pad)
dict.txt        rune-word codes "length code" (same dictionary as attack.rune_dictionary)
english.txt     three 400-rune held-out English plaintexts for plant-and-recover tests
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import attack  # noqa: E402
import lp  # noqa: E402
import stats  # noqa: E402

OUT = os.path.join(HERE, "data")


def window(f, name, prev, runes, lens):
    assert sum(lens) == len(runes)
    f.write(f"W {name} {prev}\nR {' '.join(map(str, runes))}\nL {' '.join(map(str, lens))}\n")


def main():
    os.makedirs(OUT, exist_ok=True)
    segs = stats.SEGS
    with open(os.path.join(OUT, "windows.txt"), "w") as f, open(os.path.join(OUT, "windows_07.txt"), "w") as f07:
        for i in stats.UNSOLVED:
            c = lp.runes_of(segs[i])
            if len(c) < 100:
                continue
            prev = lp.runes_of(segs[i - 1])[-1] if i > 7 else -1
            lens = [b - a for _, a, b in lp.word_spans(segs[i], c)]
            window(f, f"seg0.{i}", prev, c, lens)
            if i == 7:
                window(f07, f"seg0.{i}", prev, c, lens)
    rd = attack.rune_dictionary()
    n = 0
    with open(os.path.join(OUT, "dict.txt"), "w") as f:
        for L, (codes, _) in rd.items():
            for c in codes:
                f.write(f"{L} {int(c)}\n")
                n += 1
    with open(os.path.join(OUT, "english.txt"), "w") as f:
        for k, start in enumerate((5000, 20000, 40000)):
            toks = attack.synthetic_tokens(400, start=start)
            c = lp.runes_of(toks)
            lens = [b - a for _, a, b in lp.word_spans(toks, c)]
            window(f, f"eng{k}", -1, c, lens)
    print(f"wrote windows, windows_07, dict ({n} codes), english to {OUT}")


if __name__ == "__main__":
    main()
