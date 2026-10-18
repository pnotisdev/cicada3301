"""Debug: can any word-final skip trajectory make the null-control winner's letters non-uniform?

The winner: RANDOM 127 (rand:300:301), offset 11746, model 0, nulledge=1, 261 letters, IoC 1.7547, s = 4106.
For ANY monotone trajectory (skip a subset of the 45 word-final positions), the letters t_i = c_i - k[off + i - s_i]
use distinct i.i.d. uniform key values, so they must be i.i.d. uniform (IoC ~= 1.0). If no trajectory reproduces
the concentration, the engine's result is impossible and the decoder has a bug.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import lp  # noqa: E402

Q = 29


class Rng:
    def __init__(self, seed):
        self.s = seed & 0xFFFFFFFFFFFFFFFF

    def next(self):
        self.s = (self.s + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = self.s
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        return (z ^ (z >> 31)) & 0xFFFFFFFFFFFFFFFF

    def below(self, n):
        return ((self.next() >> 32) * n) >> 32


def main():
    win = os.path.join(HERE, "nulledge_window_v1.txt")
    lines = open(win, encoding="utf-8").read().splitlines()
    runes = [int(x) for x in lines[[i for i, l in enumerate(lines) if l.startswith("R ")][0]].split()[1:]]
    lens = [int(x) for x in lines[[i for i, l in enumerate(lines) if l.startswith("L ")][0]].split()[1:]]
    n = 300
    c = runes[:n]
    # word-final positions among the first 300 runes
    finals, b = [], 0
    for l in lens:
        b += l
        finals.append(b - 1)
    finals = [f for f in finals if f < n]
    print(f"window: {n} runes, {len(finals)} word-final positions, L sums to {sum(lens)}")

    r = Rng(301 ^ 0x05EED5EED5EED5EE)
    streams = [[r.below(Q) for _ in range(20000)] for _ in range(300)]
    k = streams[127]
    off = 11746

    # fixed trajectory: skip the first s word-finals
    import random
    rnd = random.Random(0)

    def letters(skips):
        """skip set -> decoded letters (no anti-repeat advances, i.e. the winner's ~3 extra advances ignored)"""
        out = []
        j = off
        for i in range(n):
            if i in skips:
                continue
            out.append((c[i] - k[j]) % Q)
            j += 1
        return out

    # all-skip / no-skip / random trajectories: all must be uniform
    allskip = set(finals)
    for tag, skips in (("none", set()), ("all", allskip)):
        t = letters(skips)
        print(f"{tag} skip: {len(t)} letters, IoC {lp.ioc(t):.4f}")

    best = 0.0
    for rep in range(5000):
        skips = set(f for f in finals if rnd.random() < 0.42)
        t = letters(skips)
        v = lp.ioc(t)
        if v > best:
            best = v
    print(f"5000 random trajectories: best IoC {best:.4f} (expect ~1.0-1.1)")

    # exact DP over the word finals: maximize the pair sum of the remaining letters
    # (a Viterbi over skip/score choices; this is the beam's exact objective)
    import itertools

    def viterbi():
        # states: (j, cnt-tuple) too big; instead enumerate via DP over letters counts is infeasible.
        pass

    # brute force for the first 24 finals (2^24 too big); instead verify the winner's OWN letters directly:
    # for each position, the letter the winner printed must equal c[i] - k[j_i]; reconstruct which positions were
    # skipped from the winner's plain/ptr (printed by mode verify) and check consistency.
    plain = [int(x) for x in open(os.path.join(HERE, "nulledge_tmp", "winner_plain.txt"), encoding="utf-8").read().split(",")]
    ptr = [int(x) for x in open(os.path.join(HERE, "nulledge_tmp", "winner_ptr.txt"), encoding="utf-8").read().split(",")]
    print(f"winner: {len(plain)} letters, last ptr {ptr[-1]}")
    # reconstruct scored positions: ptr[p] = key index used for letter p; between letters j advances >= 1;
    # each advance > 1 is a model-0 skip event. The rune position of letter p: walk forwards, a null skip
    # does not change j, so the rune position cannot be recovered from ptr alone. Instead check the
    # NECESSARY condition per letter: plain[p] == c[r] - k[ptr[p]] for SOME rune r in a consistent order.
    ok = 0
    for p in range(len(plain)):
        # find rune positions r consistent: plain[p] == (c[r] - k[ptr[p]]) % Q
        hits = [i for i in range(n) if (c[i] - k[ptr[p]]) % Q == plain[p]]
        if hits:
            ok += 1
    print(f"letters consistent with SOME rune: {ok}/{len(plain)}")

    # stronger: rune of letter p must be ~= p + (skips so far); skips so far = ptr[p] - p - extra_advances.
    # With the winner's ptr: ptr[p]-p jumps tell the extra advances; the skipped runes are the word finals.
    # enumerate the winner's skip set: rune r is skipped iff r is a word final and never used; try to find
    # an assignment where rune(letter p) is increasing. Greedy:
    def reconstruct(plain, ptr):
        pos = 0          # current rune
        out_letters = []
        skips = []
        for p, (t, jj) in enumerate(zip(plain, ptr)):
            while pos < n and (c[pos] - k[jj]) % Q != t:
                pos += 1
            if pos >= n:
                return None
            skips.append(pos)
            pos += 1
        return skips

    sks = reconstruct(plain, ptr)
    print("greedy reconstruction:", None if sks is None else f"{len(sks)} runes used, skipped positions set matches finals: {set(sks) == set(finals) if len(sks) == len(plain) else 'n/a'}")
    # verify each used rune is a non-skip position and the key index matches
    bad = 0
    for p, (t, jj) in enumerate(zip(plain, ptr)):
        if (c[sks[p]] - k[jj]) % Q != t:
            bad += 1
    print(f"reconstruction mismatches: {bad}")
    if bad == 0:
        print("winner decode IS consistent with c - k on distinct key indices -> letters i.i.d. uniform ->")
        print("the winner's 21-concentration must come from beam SELECTION over trajectories.")
        # estimate how many trajectories the beam could have searched and the max IoC over them
        import statistics
        iocs = [lp.ioc(letters(set(f for f in finals if rnd.random() < 0.5))) for _ in range(3000)]
        print(f"max over 3000 more trajectories: {max(iocs):.4f}")


if __name__ == "__main__":
    main()
