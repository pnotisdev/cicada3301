"""Scratch check (not committed): does the h2_coincidence statistic survive the anti-repeat rule?
The gate plants with no skips; LP2 has the rule (81% enforcement). Same statistic, same corpus, same nulls."""
import os
import random
import sys

sys.path.insert(0, "work/proposals")
sys.path.insert(0, "work/proposals/h2_coincidence")
import common  # noqa: E402
from common import N, to_runes, totient_key  # noqa: E402
from run import coincidence, z_of  # noqa: E402

rng = random.Random(7)
plain = to_runes(common.CORPUS_A + " " + common.CORPUS_B)[:1600]
n = len(plain)
key = totient_key(n * 2)
T = [list(range(N)) for _ in range(N)]
for row in T:
    rng.shuffle(row)


def enc(skip):
    """tableau cipher T[key][plain]; with skip, a doublet in the ciphertext is redrawn with the next key value (81%)"""
    c, j, prev = [], 0, -1
    for p in plain:
        x = T[key[j]][p]
        j += 1
        if skip and x == prev and rng.random() < 0.81:
            x = T[key[j]][p]
            j += 1
        c.append(x)
        prev = x
    return c, j


for skip in (False, True):
    c, used = enc(skip)
    # the screen knows the key stream and offset 0 only (skip drift unmodelled), as the gate does
    true = coincidence(c, key[:n])
    offs = [coincidence(c, key[d:d + n]) for d in (rng.randrange(1, n) for _ in range(12))]
    print("skip=%s: key values used %d for %d runes; coincidence %d vs null mean %.1f -> z %.1f"
          % (skip, used, n, true, sum(offs) / len(offs), z_of(true, offs)))
