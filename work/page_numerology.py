"""Page-numerology claims from the community, each reproduced from the master transcription and then given a null.

A. Page of 121 runes (11 x 11): first row sums to 563 and first column to 569 (the 2016 hint image is said to be 563 x 569 px); a 5 x 5 subgrid has a
   circumference sum 1136 (the OutGuess payload is 1,136 bytes); pi(1136) = 189 = GP(LAW).
   Null: shuffle the page's own runes (same multiset), 1e6 shuffles; report the chance of the claimed hit for the first row/column only and for ANY row/column,
   ANY k x k subgrid (k = 3..11).
B. Page-count arithmetic of the two tree pages (121 and 76 runes): 121 + 76 = 197 prime, 197 is the 45th prime, 121 - 76 = 45, 11 + 11 + 4 + 19 = 45; the
   4 x 19 grid's last column sums to 198 = GP of the four runes (O N T Y) the 76-rune page does not use.
   Null: how many of ALL page pairs satisfy the same relations; shuffle null for the last-column claim.
C. "Subtract two pages where a run repeats and a word appears" (DJUBEI -> TRUTH, OFLOENG -> EARTH): every maximal repeat of >= 5 runes in the whole text, the
   difference of the two pages (later - earlier, and the reverse) 16 runes either side of the run, dictionary words of >= 4 runes inside the difference, against
   random pairs of windows of the same shape (the word rate of a random difference).

    python work/page_numerology.py          # -> results/analysis/page_numerology.txt
"""
import os
import sys

import numpy as np

import attack
import lp

HERE = os.path.dirname(os.path.abspath(__file__))
N = lp.N
P = np.array(lp.PRIME)
rng = np.random.default_rng(int(os.environ.get("SEED", 11)))
LAT = lp.LATIN
OUT = []


def say(s=""):
    print(s)
    OUT.append(s)


def pages():
    """non-empty page pieces of the master transcription ('%' ends a page, '$' ends a section): [(section index, runes)]"""
    out, cur = [], []
    for si, toks in enumerate(lp.load_segments()):
        for t in toks:
            if isinstance(t, int):
                cur.append(t)
            elif t == "%":
                out.append((si, cur)); cur = []
        out.append((si, cur)); cur = []
    return [(si, p) for si, p in out if p]


def prime_count(n):
    s = np.ones(n + 1, bool); s[:2] = False
    for i in range(2, int(n ** 0.5) + 1):
        if s[i]:
            s[i * i::i] = False
    return int(s.sum()), s


def block(S, r, c, k):
    return S[:, r + k, c + k] - S[:, r, c + k] - S[:, r + k, c] + S[:, r, c]


def ring(S, r, c, k):
    return block(S, r, c, k) - (block(S, r + 1, c + 1, k - 2) if k > 2 else 0)


def table(v):
    """summed-area tables of (M, h, w) value grids"""
    M, h, w = v.shape
    S = np.zeros((M, h + 1, w + 1), np.int64)
    S[:, 1:, 1:] = v.cumsum(1).cumsum(2)
    return S


def part_a(pg):
    side = 11
    assert len(pg) == 121
    v = P[pg].reshape(1, side, side)
    S = table(v)
    row1, col1 = int(v[0, 0].sum()), int(v[0, :, 0].sum())
    say(f"A. the 121-rune page: first row {row1}, first column {col1}, whole page {int(v.sum())}")
    assert (row1, col1) == (563, 569)
    obs = {k: [(r, c) for r in range(side - k + 1) for c in range(side - k + 1) if int(ring(S, r, c, k)[0]) == 1136] for k in range(3, side + 1)}
    say("   subgrids with circumference 1136, by size k: " + ", ".join(f"{k}x{k}: {len(x)}" for k, x in obs.items() if x))
    say(f"   the 5 x 5 subgrid(s) at (row, col) = {obs[5]}")
    sh, tot = 0, {"first": 0, "any_rc": 0, "any_rc_swap": 0, "k5": 0, "any_k": 0, "all_three": 0}
    M = 100_000
    for _ in range(10):
        g = P[pg][rng.random((M, 121)).argsort(1)].reshape(M, side, side)
        rows, cols = g.sum(2), g.sum(1)
        tot["first"] += int(((rows[:, 0] == 563) & (cols[:, 0] == 569)).sum())
        a, b = (rows == 563).any(1), (cols == 569).any(1)
        tot["any_rc"] += int((a & b).sum())
        tot["any_rc_swap"] += int(((a & b) | ((rows == 569).any(1) & (cols == 563).any(1))).sum())
        S = table(g)
        k5 = np.zeros(M, bool); anyk = np.zeros(M, bool)
        for k in range(3, side + 1):
            for r in range(side - k + 1):
                for c in range(side - k + 1):
                    h = ring(S, r, c, k) == 1136
                    anyk |= h
                    if k == 5:
                        k5 |= h
        tot["k5"] += int(k5.sum()); tot["any_k"] += int(anyk.sum())
        tot["all_three"] += int(((a & b) & k5).sum())
        sh += M
    say(f"   shuffle null ({sh} shuffles of the same 121 runes): P(first row = 563 and first column = 569) = {tot['first'] / sh:.2e}"
        f" ({tot['first']} hits);  P(ANY row = 563 and ANY column = 569) = {tot['any_rc'] / sh:.2e};  either order = {tot['any_rc_swap'] / sh:.2e}")
    say(f"   P(some 5 x 5 circumference = 1136) = {tot['k5'] / sh:.3f};  P(some k x k circumference, k = 3..11, = 1136) = {tot['any_k'] / sh:.3f};"
        f"  P(any row/column pair AND a 5 x 5 ring) = {tot['all_three'] / sh:.2e}")
    pi_, _ = prime_count(1136)
    law = sum(lp.PRIME[x] for x in lp.word_to_key("LAW"))
    sums = [sum(lp.PRIME[x] for x in lp.word_to_key(w)) for w in lp.COMMON_N]
    say(f"   pi(1136) = {pi_}, GP(LAW) = {law}; dictionary words with GP sum 189: {sum(s == 189 for s in sums)} of {len(sums)}"
        f" (a three-letter word is one of {sum(s == 189 for s in sums)} that fit)")


def part_b(pgs):
    c = [len(p) for p in pgs]
    pg121, pg76 = next(p for p in pgs if len(p) == 121), next(p for p in pgs if len(p) == 76)
    cnt = lambda n: prime_count(n)[0]
    a, b = 121, 76
    say("")
    say(f"B. page counts {a} and {b}: sum {a + b} (prime: {prime_count(a + b)[1][a + b]}), pi({a + b}) = {cnt(a + b)}, difference {a - b}")

    def dims(n):                                   # most square factorization
        r = max(d for d in range(1, int(n ** 0.5) + 1) if n % d == 0)
        return r, n // r
    assert dims(121) == (11, 11) and dims(76) == (4, 19)
    say(f"   grid sides {dims(a)} and {dims(b)}: sum of the four sides = {sum(dims(a)) + sum(dims(b))}")
    pairs = [(x, y) for i, x in enumerate(c) for y in c[i + 1:]]
    rel1 = lambda x, y: cnt(x + y) == abs(x - y)
    rel2 = lambda x, y: sum(dims(x)) + sum(dims(y)) == abs(x - y)
    n1, n2, n12 = sum(rel1(*p) for p in pairs), sum(rel2(*p) for p in pairs), sum(rel1(*p) and rel2(*p) for p in pairs)
    say(f"   among all {len(pairs)} pairs of the {len(c)} non-empty pages: pi(sum) = difference: {n1} pairs; side-sum = difference: {n2}; both: {n12}")
    miss = sorted(set(range(N)) - set(pg76))
    say(f"   the 76-rune page lacks {[LAT[x] for x in miss]} with GP sum {int(P[miss].sum())}; last column of the 4 x 19 grid (runes 19, 38, 57, 76) sums to "
        f"{int(P[[pg76[i] for i in (18, 37, 56, 75)]].sum())}")
    tgt = int(P[miss].sum())
    M, hit_last, hit_any = 200_000, 0, 0
    for _ in range(5):
        g = P[pg76][rng.random((M, 76)).argsort(1)].reshape(M, 4, 19)
        hit_last += int((g[:, :, -1].sum(1) == tgt).sum())
        hit_any += int(((g.sum(1) == tgt).any(1) | (g.sum(2) == tgt).any(1)).sum())
    say(f"   shuffle null of the 76 runes: P(last column = {tgt}) = {hit_last / (5 * M):.4f}; P(some row or column = {tgt}) = {hit_any / (5 * M):.3f}")
    # the same statement for every page with exactly four unused runes
    rows = []
    for p in pgs:
        m = sorted(set(range(N)) - set(p))
        r, cc = dims(len(p))
        if len(m) == 4 and r > 1:
            g = P[p].reshape(r, cc)
            rows.append((len(p), int(P[m].sum()), int(g[:, -1].sum()) if g.shape[0] == 4 else None, int(P[m].sum()) in set(g.sum(0)) | set(g.sum(1))))
    say(f"   pages with exactly four unused runes and a non-trivial grid: {len(rows)}; those whose missing-rune sum equals some row or column sum: "
        f"{sum(x[3] for x in rows)}  (the claim is one of these)")


def words_in(seq, tbl):
    n, hits = len(seq), set()
    for L, codes in tbl.items():
        for s in range(n - L + 1):
            k = 0
            for x in seq[s:s + L]:
                k = k * N + int(x)
            if k in codes:
                hits.add((s, L))
    return hits


def part_c(pgs):
    tbl = {}
    for w in lp.COMMON_N:
        for k in attack.rune_spellings(w):                 # every spelling: E-A-R-TH as well as EA-R-TH
            if 4 <= len(k) <= 9:
                tbl.setdefault(len(k), set()).add(sum(x * N ** (len(k) - 1 - i) for i, x in enumerate(k)))
    say("")
    say(f"C. repeated runs of >= 5 runes inside LP2 (sections 0.7-0.15) and the page difference (dictionary: {sum(len(v) for v in tbl.values())} spelled words of 4-9 runes)")
    # ---- control: the scanner finds a planted word in a difference of two random strings
    tru = [x for x in lp.word_to_key("TRUTH")]
    base = rng.integers(0, N, 30)
    other = base.copy(); other[10:10 + len(tru)] = (base[10:10 + len(tru)] - np.array(tru)) % N
    assert any(L == len(tru) for _, L in words_in((base - other) % N, tbl)), "control failed"
    key = {}
    pgs = [p for s, p in pgs if 7 <= s <= 15]
    say(f"   {len(pgs)} page pieces, {sum(map(len, pgs))} runes")
    for k, p in enumerate(pgs):
        for i in range(len(p) - 4):
            key.setdefault(tuple(p[i:i + 5]), []).append((k, i))
    al = []
    for t, locs in key.items():
        for a in range(len(locs)):
            for b in range(a + 1, len(locs)):
                (ka, ia), (kb, ib) = locs[a], locs[b]
                if ia > 0 and ib > 0 and pgs[ka][ia - 1] == pgs[kb][ib - 1]:
                    continue                                    # not maximal on the left
                L = 5
                while ia + L < len(pgs[ka]) and ib + L < len(pgs[kb]) and pgs[ka][ia + L] == pgs[kb][ib + L]:
                    L += 1
                al.append((ka, ia, kb, ib, L))
    say(f"   {len(al)} maximal repeats of >= 5 runes (any two places of the text)")
    W = 16
    big = [np.array(p) for p in pgs]
    cache = {}

    def null_rate(nb, na, T=2000):
        """chance that two random windows of these lengths show a word in the difference (either direction), same rule as the observed windows"""
        if (nb, na) not in cache:
            hits = 0
            for _ in range(T):
                ok = False
                for ln in (nb, na):
                    if ln < 4:
                        continue
                    cand = [q for q in big if len(q) >= ln]
                    px, py = cand[rng.integers(len(cand))], cand[rng.integers(len(cand))]
                    s1, s2 = rng.integers(0, len(px) - ln + 1), rng.integers(0, len(py) - ln + 1)
                    d = (px[s1:s1 + ln] - py[s2:s2 + ln]) % N
                    ok |= bool(words_in(d, tbl) or words_in((-d) % N, tbl))
                hits += ok
            cache[(nb, na)] = hits / T
        return cache[(nb, na)]

    obs, rates, lens = [], [], {}
    for ka, ia, kb, ib, L in al:
        A, B = big[ka], big[kb]
        lens[L] = lens.get(L, 0) + 1
        nb, na = min(W, ia, ib), min(W, len(A) - ia - L, len(B) - ib - L)
        pre, post = (A[ia - nb:ia] - B[ib - nb:ib]) % N, (A[ia + L:ia + L + na] - B[ib + L:ib + L + na]) % N
        found = []
        for sgn, name in ((1, "earlier-later"), (-1, "later-earlier")):
            for part, seq in (("before", (sgn * pre) % N), ("after", (sgn * post) % N)):
                for s, l in sorted(words_in(seq, tbl)):
                    found.append((name, part, "".join(LAT[x] for x in seq[s:s + l])))
        rates.append(null_rate(nb, na))
        obs.append(bool(found))
        if len(al) <= 20 or L >= 6 or found:
            say(f"   run {' '.join(LAT[x] for x in A[ia:ia + L])} (length {L}) at pages {ka}/{kb}, windows {nb} before / {na} after: "
                f"words in the difference: {found if found else 'none'}; random-window hit rate {null_rate(nb, na):.2f}")
    say(f"   run lengths of the {len(al)} repeats: " + ", ".join(f"{k}: {v}" for k, v in sorted(lens.items())))
    p = np.array(rates)
    dist = np.array([1.0])                              # Poisson-binomial tail of the number of alignments that show a word
    for q in p:
        dist = np.convolve(dist, [1 - q, q])
    H = int(sum(obs))
    say(f"   alignments with a >= 4-rune dictionary word in the difference: {H} of {len(al)}; expected by chance {p.sum():.1f}; P(>= {H}) = {dist[H:].sum():.3f}")
    say(f"   random-window hit rate per alignment: mean {p.mean():.2f} (min {p.min():.2f}, max {p.max():.2f})")


def main():
    allp = pages()
    say(f"{len(allp)} non-empty page pieces, {sum(len(p) for _, p in allp)} runes (random seed {os.environ.get(chr(83) + 'EED', 11)})")
    pgs = [p for _, p in allp]
    part_a(next(p for p in pgs if len(p) == 121))
    part_b(pgs)
    part_c(allp)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "page_numerology.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    sys.exit(main())
