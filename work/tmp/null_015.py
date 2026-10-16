"""Null control for the L=1322 / 1465 / 1084 hits on segment 0.15: same word structure, runes
shuffled or replaced by uniform random runes, solved with the same beam settings."""
import os
import random
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cribsolve as cs  # noqa: E402
import lp  # noqa: E402
import stats  # noqa: E402

SEG = stats.SEGS[15]


def with_runes(toks, runes):
    it = iter(runes)
    return [next(it) if isinstance(t, int) else t for t in toks]


def job(args):
    kind, L, seed, atb = args
    R = random.Random(seed)
    c = lp.runes_of(SEG)
    if kind == "real":
        toks = SEG
    elif kind == "shuffled":
        c = c[:]
        R.shuffle(c)
        toks = with_runes(SEG, c)
    else:
        toks = with_runes(SEG, [R.randrange(29) for _ in c])
    p = cs.periodic_problem(toks, L, atbash=atb)
    r = p.solve_beam(width=100, per_state=20)
    n = sum(len(p.words[w][1]) for w in p.linked)
    wild = sum(1 for w in p.linked if r["words"].get(w, 0) is None) / len(p.linked)
    return kind, L, seed, atb, r["score"] / n, wild


if __name__ == "__main__":
    tasks = [("real", 1322, 0, False)]
    tasks += [(k, L, s, False) for k in ("shuffled", "random") for L in (1322, 1465) for s in (1, 2, 3)]
    tasks += [("real", L, 0, False) for L in (1300, 1350, 1400)]  # neighbouring, unflagged periods
    with Pool() as pool:
        for kind, L, seed, atb, spr, wild in pool.imap_unordered(job, tasks):
            print(f"{kind:8s} L={L} seed={seed}: {spr:.2f}/rune unexplained {100 * wild:.0f}%", flush=True)
