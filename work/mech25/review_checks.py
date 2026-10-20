"""Phase 23 review checks (1 core, numba cache redirected so the running queue's cache is untouched).
(a) where the -1e18 sentinel arises; (b) power with LETTER-spelled plaintext (the decoder's model f is digraph Walden); (c) stage-1 hit at misaligned offsets."""
import os, sys
os.environ["NUMBA_CACHE_DIR"] = "E:/tmp/claude/nbcache"
os.environ["NUMBA_NUM_THREADS"] = "1"
import numpy as np
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, W)
import book_key_screen as S
from book_key_decoder import LN_SKIP, beam_decode, encrypt_skip_ptr
from book_key_flatness import dist, flattest_table, to_runes
N = 29

wins = S.lp2_windows()
for spell in ("digraph", "letters"):
    K = S.key_of("liber_al", spell)
    g = S.grid_of(K)
    print(f"(a) {spell}: key {len(K)} runes, grid {len(g)} offsets, last grid offset {g[-1]}, runes left after it {len(K) - g[-1]}")
    MT = S.model()
    bad = []
    for name, c in wins:
        for o in g[-6:]:
            sc = beam_decode(c, K, int(o), MT, 64, LN_SKIP, 8, 8)[0] / len(c)
            if sc < -1:
                bad.append((name, int(o), len(K) - int(o)))
    print("    sentinel (beam died) at (window, offset, key runes left):", bad)

rng = np.random.default_rng(11)
em = open(os.path.join(S.HERE, "ref", "emerson_essays1.txt"), encoding="utf-8", errors="ignore").read()
MT = S.model()
for spell in ("digraph", "letters"):
    K = S.key_of("liber_al", spell)
    for pl in ("digraph", "letters"):
        P = to_runes(em, letters=(pl == "letters"))
        sc = []
        for r in range(12):
            _, pi = flattest_table(dist(P), dist(K), rng, restarts=3)
            table = np.argsort(pi)
            o = int(rng.integers(100, len(K) - 3 * 729))
            po = int(rng.integers(0, len(P) - 729))
            c, _ = encrypt_skip_ptr(P[po:po + 729], table[K[o:o + 3 * 729]], rng)
            gp = o - o % 8
            sc.append(beam_decode(c, K, gp, MT, 64, LN_SKIP, 8, 8)[0] / 729)
        sc = np.array(sc)
        print(f"(b) key {spell}, PLAINTEXT {pl} spelling, 12 plants: scores median {np.median(sc):+.3f} min {sc.min():+.3f} max {sc.max():+.3f}; above threshold {S.THR[spell]}: {(sc > S.THR[spell]).sum()}/12")
# (c) offset sensitivity: score at the true grid point +-8k
K = S.key_of("liber_al", "digraph")
P = to_runes(em)
_, pi = flattest_table(dist(P), dist(K), rng, restarts=3)
table = np.argsort(pi)
o = 8000 + 3
c, _ = encrypt_skip_ptr(P[500:500 + 729], table[K[o:o + 3 * 729]], rng)
print("(c) plant at true offset", o, "(grid point 8000): score per rune at grid offsets:")
for gp in range(7960, 8049, 8):
    print(f"    {gp:6d} {beam_decode(c, K, gp, MT, 64, LN_SKIP, 8, 8)[0] / 729:+.4f}")
print("    odd offsets (single, spread=1) true-aligned vs +-1,+-4:", [(d, round(beam_decode(c, K, o + d, MT, 64, LN_SKIP, 8, 1)[0] / 729, 4)) for d in (-4, -1, 0, 1, 4)])
