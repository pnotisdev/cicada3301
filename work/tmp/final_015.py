"""Untruncated comparison for seg 0.15 at L=1322: real vs shuffled/random nulls vs synthetic true/wrong."""
import os
import random
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import attack  # noqa: E402
import cribsolve as cs  # noqa: E402
import lp  # noqa: E402
import stats  # noqa: E402

SEG = stats.SEGS[15]


def with_runes(toks, runes):
    it = iter(runes)
    return [next(it) if isinstance(t, int) else t for t in toks]


def job(args):
    kind, L, seed = args
    R = random.Random(seed)
    c = lp.runes_of(SEG)
    if kind == "real":
        toks = SEG
    elif kind == "shuffled":
        c = c[:]
        R.shuffle(c)
        toks = with_runes(SEG, c)
    elif kind == "random":
        toks = with_runes(SEG, [R.randrange(29) for _ in c])
    else:  # synthetic English, periodic key 1322, solved at L (true if L == 1322)
        pt = attack.synthetic_tokens(3316, start=R.randrange(5000, 40000))
        key = [R.randrange(29) for _ in range(1322)]
        toks = cs._encrypt(pt, lambda i: key[i % 1322])
    p = cs.periodic_problem(toks, L)
    r = p.solve_beam(width=100, per_state=20)
    spr, wild, dec = p.quality(r)
    return kind, L, seed, spr, wild, dec, r["seconds"]


if __name__ == "__main__":
    tasks = [("real", 1322, 0), ("real", 1350, 0), ("shuffled", 1322, 1), ("shuffled", 1322, 2),
             ("random", 1322, 1), ("random", 1322, 2), ("synthetic", 1322, 1), ("synthetic", 1084, 1)]
    with Pool(len(tasks)) as pool:
        for kind, L, seed, spr, wild, dec, sec in pool.imap_unordered(job, tasks):
            print(f"{kind:9s} L={L} seed={seed}: {spr:.2f}/rune, unexplained {100 * wild:.0f}%, "
                  f"decided {100 * dec:.0f}% of linked words, {sec:.0f}s", flush=True)
