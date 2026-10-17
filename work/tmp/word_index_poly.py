"""Exploration: is the key a low-degree polynomial in the WORD index? For each position j inside the words, take the stream of
the j-th rune of every word (words in book order), subtract a1*w + a2*w^2 (mod 29) and score the index of coincidence.
Null: the same words in random order. 841 (a1, a2) per position; a constant offset does not change the IoC."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lp  # noqa: E402
import stats  # noqa: E402

N = 29
words = []
for i in stats.UNSOLVED:
    c = lp.runes_of(stats.SEGS[i])
    words += [c[a:b] for _, a, b in lp.word_spans(stats.SEGS[i], c)]
print(len(words), "words")


def ioc(x):
    h = np.bincount(x, minlength=N)
    n = len(x)
    return N * (int((h * h).sum()) - n) / (n * (n - 1))


def best(stream_w, stream_x):
    w = stream_w % N
    out = (0, 0, 0)
    for a1 in range(N):
        for a2 in range(N):
            x = (stream_x - a1 * w - a2 * w * w) % N
            v = ioc(x)
            if v > out[0]:
                out = (v, a1, a2)
    return out


rng = np.random.default_rng(1)
for j in range(6):
    idx = np.array([w for w, wd in enumerate(words) if len(wd) > j])
    x = np.array([words[w][j] for w in idx])
    b = best(idx, x)
    nulls = [best(idx, rng.permutation(x))[0] for _ in range(6)]
    print(f"position {j}: n={len(x):5d}  best IoC {b[0]:.4f} (a1={b[1]}, a2={b[2]})  null (6 shuffles) max {max(nulls):.4f}")

# positive control: the first runes of English words (Emerson) plus 3*w + 5*w^2
import attack  # noqa: E402

toks = attack.synthetic_tokens(14000, start=9000)
ew = [[]]
for t in toks:
    if t == " ":
        ew.append([])
    else:
        ew[-1].append(t)
ew = [w for w in ew if w][:2900]
idx = np.arange(len(ew))
x = (np.array([w[0] for w in ew]) + 3 * idx + 5 * idx * idx) % N
b = best(idx, x)
print(f"planted control (English first runes + 3w + 5w^2, n={len(x)}): best IoC {b[0]:.3f} at a1={b[1]}, a2={b[2]}")
