"""sliding_window gate: a mid-book key alignment is recoverable by a sliding window.

Run: python run.py   (Windows: run.bat)
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import common  # noqa: E402
from common import N, ioc, decode_beam, totient_key, markov, print_verdict


def main():
    print("=" * 72)
    print("sliding_window gate: mid-book key alignment is recoverable")
    print("=" * 72)
    rng = random.Random(20261017)
    base = common.to_runes(common.CORPUS_B)  # real English (IoC ~1.85)
    book = []
    while len(book) < 3200:
        off = rng.randrange(len(base) - 100)
        book.extend(base[off:off + 100])
    book = book[:3200]
    total = len(book)
    key = totient_key(600)

    pos = rng.randrange(0, total - 320)
    off = rng.randrange(0, 200)
    c = book[:]
    prev = -1
    for i in range(total):
        if pos <= i < pos + 300:
            x = (book[i] + key[off + (i - pos)]) % N
            if x == prev and rng.random() < 0.81:  # anti-repeat skip inside the window
                x = (book[i] + key[off + (i - pos) + 1]) % N
            c[i] = x
            prev = x
        else:
            c[i] = (book[i] + rng.randrange(N)) % N
            prev = c[i]
    print("planted window at position %d of %d, key offset %d" % (pos, total, off))

    def score(wpos, woff):
        return ioc(decode_beam(c[wpos:wpos + 300], key[woff:], beam=32))

    true = score(pos, off)
    nulls = []
    for _ in range(120):
        nulls.append(score(rng.randrange(0, total - 300), rng.randrange(0, 250)))
    null_max = max(nulls)
    print("planted (pos, offset):  IoC %.3f" % true)
    print("120 random pairs:       max IoC %.3f" % null_max)

    near = [score(p, off) for p in range(max(0, pos - 5), min(total - 300, pos + 5) + 1)]
    best_near = max(near)
    print("10 neighbouring positions at the true offset: best IoC %.3f (overlapping windows tie)"
          % best_near)

    ok = (true >= 1.5) and (true > null_max + 0.3) and (true >= best_near)
    return print_verdict("sliding_window", ok,
                         "true %.2f / null max %.2f / neighbour best %.2f" %
                         (true, null_max, best_near))


if __name__ == "__main__":
    sys.exit(main())
