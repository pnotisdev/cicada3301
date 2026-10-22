"""Phase 60, item 4: is the 'extra rune' of LP2's words a simple function of the other runes, the previous word, the
word's index or its length?

For every word of >= 3 runes and every position j, a test asks "rune j == (target + b) mod 29" for 15 targets x 3 offsets
b in {-1, 0, +1} (45 tests, rune INDEX 0..28 and the Gematria prime VALUE as the two sum domains). A word is a hit if any
position satisfies it. The statistic is the number of hit words; the null shuffles the runes over all positions (word
lengths, boundaries and rune frequencies kept) and also supplies the multiplicity correction (P of the maximum z over the
45 tests). Controls: (a) planted relation in a shuffled text (45% / 15% of words get one position overwritten with the
function value), (b) the ciphertext of the four solved ENCRYPTED sections (0, 1, 3, 5), which have no extra rune.
Second part: do LP2's word lengths prefer prime lengths beyond what 'one extra rune in q of the words' predicts?

    python work/clue_extra_rune.py [--reps 1000]     # -> results/analysis/phase60_extra_rune.txt, 1 core, a minute or two
"""
import argparse
import os
import re
import sys
from math import sqrt

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lp  # noqa: E402
import stats  # noqa: E402

N = lp.N
PR = np.array(lp.PRIME)
TARGETS = ["sum of other runes (index)", "-(sum of other runes) (index)", "sum of other runes (prime value)",
           "-(sum of other runes) (prime value)", "previous word: index sum", "previous word: prime sum",
           "previous word: length", "previous word: last rune", "previous word: first rune", "word index (all LP2)",
           "word length", "position in word", "length - position", "word index within section",
           "previous word: index sum + this word's length"]
OFFS = (-1, 0, 1)


def words_of_segments(seg_ids):
    """list of rune-index arrays (words), and a section id per word"""
    ws, sec = [], []
    for i in seg_ids:
        c = lp.runes_of(stats.SEGS[i])
        for _, a, b in lp.word_spans(stats.SEGS[i], c):
            ws.append(c[a:b])
            sec.append(i)
    return ws, np.array(sec)


class Layout:
    """flattened word structure; all arrays aligned with the flat rune array"""

    def __init__(self, words, sec):
        self.L = np.array([len(w) for w in words])
        self.start = np.concatenate([[0], np.cumsum(self.L)[:-1]])
        self.n = int(self.L.sum())
        self.wid = np.repeat(np.arange(len(words)), self.L)
        self.pos = np.arange(self.n) - self.start[self.wid]
        self.flat = np.array([x for w in words for x in w])
        self.sec = sec
        first_of_sec = np.array([0] + [i for i in range(1, len(words)) if sec[i] != sec[i - 1]])
        self.wsec_idx = np.arange(len(words)) - np.repeat(first_of_sec, np.diff(np.append(first_of_sec, len(words))))
        self.ok = (self.L[self.wid] >= 3)
        self.hasprev = (self.wid > 0)
        self.nw = len(words)

    def targets(self, r):
        """(len(TARGETS), n) target residues for the rune array r"""
        S = np.add.reduceat(r, self.start)
        SP = np.add.reduceat(PR[r], self.start)
        So = S[self.wid] - r
        Sp = SP[self.wid] - PR[r]
        pw = np.maximum(self.wid - 1, 0)
        last = r[self.start + self.L - 1]
        first = r[self.start]
        Lw = self.L[self.wid]
        t = np.stack([So, -So, Sp, -Sp, S[pw], SP[pw], self.L[pw], last[pw], first[pw], self.wid, Lw, self.pos,
                      Lw - self.pos, self.wsec_idx[self.wid], S[pw] + Lw])
        return t % N

    def stat(self, r):
        """(45,) number of hit words per test"""
        T = self.targets(r)
        out = np.zeros(len(TARGETS) * len(OFFS))
        k = 0
        for ti in range(len(TARGETS)):
            for b in OFFS:
                hit = (r == (T[ti] + b) % N) & self.ok
                if TARGETS[ti].startswith("previous"):
                    hit &= self.hasprev
                out[k] = np.add.reduceat(hit.astype(np.int64), self.start).astype(bool).sum()
                k += 1
        return out


def name(k):
    return f"{TARGETS[k // len(OFFS)]}, b={OFFS[k % len(OFFS)]:+d}"


def null_stats(lay, reps, rng, base=None):
    r0 = lay.flat if base is None else base
    M = np.empty((reps, len(TARGETS) * len(OFFS)))
    for i in range(reps):
        M[i] = lay.stat(rng.permutation(r0))
    return M


def evaluate(lay, r, M):
    mu, sd = M.mean(0), M.std(0) + 1e-9
    z = (lay.stat(r) - mu) / sd
    zn = (M - mu) / sd
    pmax = ((zn.max(1) >= z.max()).sum() + 1) / (len(M) + 1)
    return z, pmax


def plant(lay, base, which, rate, rng):
    """overwrite one random position of `rate` of the words (>=3 runes) with the function value, left to right"""
    r = base.copy()
    ti = TARGETS.index(which)
    for w in range(lay.nw):
        if lay.L[w] < 3 or rng.random() > rate:
            continue
        j = int(rng.integers(lay.L[w]))
        T = lay.targets(r)[ti]            # recomputed so that previous-word targets see earlier plants
        r[lay.start[w] + j] = T[lay.start[w] + j]
    return r


def length_part(out):
    """prime-length preference of LP2's word lengths against the one-extra-rune fit"""
    ws, _ = words_of_segments(stats.UNSOLVED)
    L = np.array([len(w) for w in ws])
    bins = 16
    obs = np.array([(np.minimum(L, bins) == k).sum() for k in range(1, bins + 1)], float)
    path = os.path.join(HERE, "ref", "emerson_essays1.txt")
    txt = open(path, encoding="utf-8").read()
    txt = txt[txt.index("SELF-RELIANCE"):].split("*** END OF")[0]
    el = np.array([len(lp.word_to_key(w.upper().replace("IO", "IA")) or []) for w in re.findall(r"[A-Za-z]+", txt)])
    el = el[el > 0]
    p0 = np.array([(np.minimum(el, bins) == k).sum() for k in range(1, bins + 1)], float)
    p0 /= p0.sum()
    best = None
    for q in np.linspace(0, 0.8, 161):
        p = (1 - q) * p0
        p[1:] += q * p0[:-1]
        p[-1] += q * p0[-1]
        ll = float((obs * np.log(np.clip(p, 1e-12, None))).sum())
        if best is None or ll > best[0]:
            best = (ll, q, p.copy())
    _, q, p = best
    e = obs.sum() * p
    primes = [2, 3, 5, 7, 11, 13]
    out.append(f"\nWord lengths: LP2 {int(obs.sum())} words; Emerson (runes, IO->IA) as the length source; best one-extra-rune q = {q:.3f}")
    out.append("len  LP2   fit   (obs-fit)/sqrt(fit)   prime?")
    for k in range(bins):
        out.append(f"{k + 1:3d} {int(obs[k]):5d} {e[k]:7.1f} {(obs[k] - e[k]) / sqrt(max(e[k], 1)):8.2f}   {'P' if k + 1 in primes else ''}")
    pm = np.array([k + 1 in primes for k in range(bins)])
    z = (obs[pm].sum() - e[pm].sum()) / sqrt(e[pm].sum() * (1 - e[pm].sum() / obs.sum()))
    out.append(f"prime-length words: {int(obs[pm].sum())} observed against {e[pm].sum():.1f} fitted, z {z:+.2f}; "
               f"share LP2 {obs[pm].sum() / obs.sum():.3f}, Emerson {p0[pm].sum():.3f}, fit {p[pm].sum():.3f}")
    # a purely prime-padded model would put the mass of lengths 4, 6, 8, 9, 10 on the next prime: check the shift
    out.append(f"even lengths 4,6,8: LP2 {int(obs[[3, 5, 7]].sum())} fitted {e[[3, 5, 7]].sum():.1f}; "
               f"lengths 5,7,11: LP2 {int(obs[[4, 6, 10]].sum())} fitted {e[[4, 6, 10]].sum():.1f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=1000)
    a = ap.parse_args()
    rng = np.random.default_rng(60)
    out = ["Phase 60 item 4: is the extra rune a simple function of the others? (work/clue_extra_rune.py)"]
    ws, sec = words_of_segments(stats.UNSOLVED)
    lay = Layout(ws, sec)
    out.append(f"LP2: {lay.nw} words, {lay.n} runes, {int((lay.L >= 3).sum())} words of >= 3 runes; {len(TARGETS) * len(OFFS)} tests; {a.reps} shuffles")
    M = null_stats(lay, a.reps, rng)
    z, pmax = evaluate(lay, lay.flat, M)
    order = np.argsort(-z)[:8]
    out.append(f"\nLP2 REAL: max z {z.max():+.2f} ({name(int(z.argmax()))}), P(max over tests) = {pmax:.3f}; min z {z.min():+.2f}")
    for k in order:
        out.append(f"   z {z[k]:+.2f}  {name(int(k))}")
    # positive controls
    out.append("\nPositive controls (plant into a shuffled LP2, then run the same 45 tests against fresh shuffles):")
    for which, rate in (("sum of other runes (index)", 0.45), ("sum of other runes (index)", 0.15),
                        ("previous word: index sum", 0.45), ("word length", 0.15), ("word index (all LP2)", 0.15)):
        base = rng.permutation(lay.flat)
        zr, pm = evaluate(lay, plant(lay, base, which, rate, rng), M)
        ti = TARGETS.index(which) * 3 + 1
        out.append(f"   plant '{which}' in {int(rate * 100)}% of words: z at the planted test {zr[ti]:+.1f}, "
                   f"max z {zr.max():+.1f} ({'planted' if int(zr.argmax()) == ti else name(int(zr.argmax()))}), P(max) {pm:.3f}")
    # negative controls: ciphertext of the solved encrypted sections. Sections 1 and 5 are Vigenere (a repeated word
    # gets different ciphertext); sections 0 and 3 are Atbash, a monoalphabetic cipher, where every copy of THE, OF, ...
    # repeats the same hit or miss, so the word-independent shuffle null is too narrow there (shown for the record).
    for ids, tag in (([1, 5], "Vigenere sections 1, 5"), ([0, 3], "Atbash sections 0, 3 (repeated words clump)")):
        wsc, secc = words_of_segments(ids)
        layc = Layout(wsc, secc)
        Mc = null_stats(layc, a.reps, rng)
        zc, pc = evaluate(layc, layc.flat, Mc)
        out.append(f"\nNegative control, ciphertext of {tag} ({layc.nw} words, {layc.n} runes): "
                   f"max z {zc.max():+.2f} ({name(int(zc.argmax()))}), P(max) {pc:.3f}")
    # null of the null: how often does a SHUFFLED LP2 give P(max) < 0.05?
    ps = []
    for i in range(100):
        zi, pi = evaluate(lay, rng.permutation(lay.flat), M)
        ps.append(pi)
    out.append(f"Null control: 100 fresh shuffles of LP2 judged against the same null: P(max) < 0.05 in {sum(p < 0.05 for p in ps)} of 100 (expected 5)")
    length_part(out)
    txt = "\n".join(out)
    print(txt)
    p = os.path.join(os.path.dirname(HERE), "results", "analysis", "phase60_extra_rune.txt")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt + "\n")


if __name__ == "__main__":
    main()
