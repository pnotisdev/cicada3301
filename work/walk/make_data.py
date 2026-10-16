"""Data for the word-scoped solver (walk/): English rune trigram LM, LP2 ciphertext, synthetic tests.

Writes walk/data/lm3.bin (30^3 float32 log-probs, index (a*30+b)*30+c, token 29 = word boundary),
walk/data/lp2.txt (all unsolved segments as one text, windows format) and synthetic ciphertexts.
"""
import os
import random
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import lp  # noqa: E402
import stats  # noqa: E402

N = 29
BND = 29
OUT = os.path.join(HERE, "data")


def english_words():
    with open(os.path.join(os.path.dirname(HERE), "ref", "emerson_essays1.txt"), encoding="utf-8") as f:
        txt = f.read()
    txt = txt[txt.index("SELF-RELIANCE"):].split("*** END OF")[0]
    ws = [lp.word_to_key(w.upper().replace("IO", "IA")) for w in re.findall(r"[A-Za-z]+", txt)]
    return [w for w in ws if w]


def solved_words():
    segs = lp.load_segments()
    out = []
    for i, (_, f) in lp.KNOWN.items():
        c = lp.runes_of(segs[i])
        p = f(c)
        out += [p[a:b] for _, a, b in lp.word_spans(segs[i], c)]
    return out


def build_lm(words, held_out=0):
    import numpy as np
    c3 = np.zeros((30, 30, 30))
    for w in words:
        seq = [BND, BND] + list(w) + [BND]
        for a, b, c in zip(seq, seq[1:], seq[2:]):
            c3[a, b, c] += 1
    c2 = c3.sum(axis=0)          # (b, c)
    c1 = c2.sum(axis=0)          # (c)
    p1 = (c1 + 1) / (c1 + 1).sum()
    p2 = (c2 + 0.5 * p1[None, :]) / (c2.sum(axis=1, keepdims=True) + 0.5)
    tot3 = c3.sum(axis=2, keepdims=True)
    p3 = (c3 + 2.0 * p2[None, :, :]) / (tot3 + 2.0)
    lp3 = np.log(p3).astype(np.float32)
    return lp3


def write_windows(path, items):
    with open(path, "w") as f:
        for name, runes, lens in items:
            f.write(f"W {name} -1\nR {' '.join(map(str, runes))}\nL {' '.join(map(str, lens))}\n")


def main():
    os.makedirs(OUT, exist_ok=True)
    eng = english_words()
    sol = solved_words()
    train = eng[: len(eng) - 6000] + sol * 3          # keep the last 6,000 Emerson words for synthetic tests
    test = eng[len(eng) - 6000:]
    lp3 = build_lm(train)
    with open(os.path.join(OUT, "lm3.bin"), "wb") as f:
        f.write(lp3.tobytes())
    # LP2: all unsolved segments as separate windows (the solver treats them as one text)
    segs = stats.SEGS
    items = []
    for i in stats.UNSOLVED:
        c = lp.runes_of(segs[i])
        if len(c) < 100:
            continue
        lens = [b - a for _, a, b in lp.word_spans(segs[i], c)]
        items.append((f"seg0.{i}", c, lens))
    write_windows(os.path.join(OUT, "lp2.txt"), items)
    # held-out English plaintext with LP2's size (for synthetic encryption by the Rust tool)
    runes, lens = [], []
    for w in test:
        if len(runes) + len(w) > 12956:
            break
        runes += w
        lens.append(len(w))
    write_windows(os.path.join(OUT, "english_test.txt"), [("eng_test", runes, lens)])
    print(f"LM trained on {len(train)} words; LP2 windows {len(items)}; test plaintext {len(runes)} runes, {len(lens)} words")


if __name__ == "__main__":
    main()
