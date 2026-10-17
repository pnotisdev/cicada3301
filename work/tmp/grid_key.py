"""Exploration: key = a*w + b*j + c*w*j (mod 29) with w = word index, j = position inside the word, over the whole book.
Score = IoC of the decoded runes; null = shuffled rune order inside the same word layout; control = English plus a planted key."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import attack  # noqa: E402
import lp  # noqa: E402
import stats  # noqa: E402

N = 29


def layout(words):
    W = np.concatenate([np.full(len(w), k) for k, w in enumerate(words)]) % N
    J = np.concatenate([np.arange(len(w)) for w in words]) % N
    return W, J


def best(x, W, J):
    out = (0.0, 0, 0, 0)
    WJ = (W * J) % N
    for a in range(N):
        xa = (x - a * W) % N
        for b in range(N):
            xb = (xa - b * J) % N
            for c in range(N):
                e = (xb - c * WJ) % N
                h = np.bincount(e, minlength=N)
                v = N * (int((h * h).sum()) - len(e)) / (len(e) * (len(e) - 1))
                if v > out[0]:
                    out = (v, a, b, c)
    return out


words = []
for i in stats.UNSOLVED:
    c = lp.runes_of(stats.SEGS[i])
    words += [c[a:b] for _, a, b in lp.word_spans(stats.SEGS[i], c)]
W, J = layout(words)
x = np.array([r for w in words for r in w])
rng = np.random.default_rng(2)
b = best(x, W, J)
nulls = [best(rng.permutation(x), W, J)[0] for _ in range(3)]
print(f"LP2 ({len(x)} runes): best IoC {b[0]:.4f} at a={b[1]} b={b[2]} c={b[3]}; null (3 shuffles) max {max(nulls):.4f}")
toks = attack.synthetic_tokens(16000, start=9000)
ew = [[]]
for t in toks:
    if t == " ":
        ew.append([])
    else:
        ew[-1].append(t)
ew = [w for w in ew if w][:2900]
We, Je = layout(ew)
xe = (np.array([r for w in ew for r in w]) + 4 * We + 7 * Je + 2 * We * Je) % N
b = best(xe, We, Je)
print(f"planted control (English + 4w + 7j + 2wj, {len(xe)} runes): best IoC {b[0]:.3f} at a={b[1]} b={b[2]} c={b[3]}")
