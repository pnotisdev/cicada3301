"""Phase 23 diagnostic: path accuracy of the book-key beam vs beam width (where do plants lose the path?)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import book_key_decoder as d
from book_key_flatness import HERE, dist, flattest_table, gutenberg_body, to_runes
rng = np.random.default_rng(7)
em = open(os.path.join(HERE, "ref", "emerson_essays1.txt"), encoding="utf-8", errors="ignore").read()
P = to_runes(em)
MT = d.log_ratio(to_runes(gutenberg_body(os.path.join(HERE, "ref", "corpora", "pg205.txt"))))
Kb = to_runes(gutenberg_body(os.path.join(HERE, "ref", "corpora", "pg26.txt")))
_, pi = flattest_table(dist(P), dist(Kb), rng, restarts=3)
table = np.argsort(pi)
for n in (() if __name__ != "__main__" else (300, 729)):
    for r in range(12):
        c, o, used, _ = d.plant(P, Kb, n, rng, table)
        row = []
        for beam in (24, 96, 384):
            s, path = d.beam_decode(c, Kb, o, MT, beam, d.LN_SKIP)
            ok = path == o + used
            first_bad = int(np.argmin(ok)) if not ok.all() else n
            row.append(f"b{beam}: acc {ok.mean():.2f} first_bad {first_bad:4d} s {s / n:+.3f}")
        print(n, "skips", int(used[-1] - n + 1), " | ".join(row), flush=True)


def path_score(c, key, path, MT):
    G = np.zeros((29, 29))
    for x, j in zip(c, path):
        G[key[j]] += MT[x]
    m = G.max(axis=1)
    lse = m + np.log(np.exp(G - m[:, None]).sum(axis=1)) - np.log(29)
    skips = (np.diff(path) - 1).sum()
    return lse.sum() + skips * d.LN_SKIP


if __name__ == "__main__":
    print("true-path score vs beam score (nats/rune)")
    for r in range(12):
        c, o, used, _ = d.plant(P, Kb, 300, rng, table)
        s, path = d.beam_decode(c, Kb, o, MT, 24, d.LN_SKIP)
        print(f"beam {s / 300:+.3f} (rescored {path_score(c, Kb, path, MT) / 300:+.3f})  truth {path_score(c, Kb, o + used, MT) / 300:+.3f}"
              f"  acc {(path == o + used).mean():.2f}  first skip at {int(np.argmax(np.diff(o + used) > 1))}")
    