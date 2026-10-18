"""Debug 3: instrumented plant pointers vs decoder Viterbi pointers at offsets
3 and 4, position by position."""
import sys
sys.path.insert(0, "work/tmp")
from ind_review_claim3 import Q, layout_starts, reference_logs, totient_key, ordinary_arcs

sys.path.insert(0, "work")
import lp
import random
import math

logs, _ = reference_logs()
n = 300
starts = layout_starts(7, n)
plain = lp.KNOWN[1][1](lp.runes_of(lp.load_segments()[1]))[:n]
key = totient_key(4 * n + 64)

# instrumented plant
rng = random.Random(20000)
c, j, ptrs, redraws = [], 3, [], []
for i in range(n):
    p = plain[i]
    while True:
        y = (p + key[j]) % Q
        j += 1
        if not c or y != c[-1] or rng.random() >= 0.81:
            break
        redraws.append(i)
    c.append(y)
    ptrs.append(j)
print(f"redraws at positions: {redraws}")
print(f"plant pointer-after, first 14: {ptrs[:14]}")

# own Viterbi with per-position (ptr, plaintext) recording
def viterbi(c, off):
    # state -> (value, node); node = (parent_node, ptr_after, plaintext)
    states = {off: (0.0, None)}
    for i, ci in enumerate(c):
        pv = c[i - 1] if i else -1
        nxt = {}
        for j0, (v, node) in states.items():
            last = Q if node is None else node[2]
            for nj, p, w in ordinary_arcs(ci, pv, key, j0, 1, 0.81):
                v2 = v + w + logs[last][p]
                cand = (v2, (node, nj, p))
                if nj not in nxt or v2 > nxt[nj][0]:
                    nxt[nj] = cand
        states = nxt
    best_j = max(states, key=lambda s: states[s][0])
    chain, node = [], states[best_j][1]
    while node is not None:
        parent, nj, p = node
        chain.append((nj, p))
        node = parent
    chain.reverse()
    return states[best_j][0], [(nj, p) for nj, p in chain]

for off in (3, 4, 5):
    val, path = viterbi(c, off)
    dptr = [(i, ptrs[i], path[i][0]) for i in range(n) if ptrs[i] != path[i][0]]
    dmatch = [(i, plain[i], path[i][1]) for i in range(n) if plain[i] != path[i][1]]
    print(f"\noffset {off}: Viterbi value={val:+.2f}, pointer diffs vs plant: {dptr[:12]}")
    print(f"  plaintext diffs: {dmatch[:12]} (total {len(dmatch)})")
