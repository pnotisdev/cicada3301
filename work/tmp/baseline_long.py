"""Beam-solver baseline at long periods with few repetitions (matches seg 0.15, 3316 runes)."""
import os
import random
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import attack  # noqa: E402
import cribsolve as cs  # noqa: E402


def job(args):
    L, LL, seed = args
    R = random.Random(seed)
    pt = attack.synthetic_tokens(3316, start=R.randrange(5000, 40000))
    key = [R.randrange(29) for _ in range(L)]
    ct = cs._encrypt(pt, lambda i: key[i % L])
    p = cs.periodic_problem(ct, LL)
    r = p.solve_beam(width=100, per_state=20)
    n = sum(len(p.words[w][1]) for w in p.linked)
    wild = sum(1 for w in p.linked if r["words"].get(w, 0) is None) / len(p.linked)
    acc, _ = cs.accuracy(p, r["assign"], [pt])
    return L, LL, seed, r["score"] / n, wild, acc


if __name__ == "__main__":
    tasks = [(1322, 1322, s) for s in (1, 2)] + [(1322, LL, s) for s in (1, 2) for LL in (1084, 1465)]
    with Pool() as pool:
        for L, LL, seed, spr, wild, acc in pool.imap_unordered(job, tasks):
            print(f"true L={L} solved as L={LL} seed {seed}: {spr:.2f}/rune unexplained {100 * wild:.0f}% "
                  f"accuracy {100 * acc:.0f}%", flush=True)
