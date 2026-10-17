"""The community crib for the start of LP2 (section 0.7), from two PDFs and a repo that propose a plaintext for the first 13 + 141 runes:

    heading (13 runes): DIVINITY WITHIN
    body (141 runes):   FIND YOU ARE NECESSARILY ALONE WHEN YOU ARE BORN AND CANNOT COMMUNICATE IT IN ANY WAY FOREVER AFTER REMEMBER TO THINK OF ALL YOU VALUE IN ONE
                        WORD JUST RECITE YOUR ANSWER NOW

Their evidence is arithmetic on the running key K = C - P (mod 29): Fibonacci residues, 4 x 4 "matrices" of 16 consecutive keys, repeated totals, 434 / 491 checkpoints.
This script (1) reproduces their numbers from the master transcription, (2) counts how many other English words would have fitted each Fibonacci claim, and
(3) gives the nulls: the same statistics for random dictionary words of the same rune lengths on the same ciphertext.

    python work/crib_matrix_check.py          # -> results/analysis/crib_matrix_check.txt
"""
import os
import sys

import numpy as np

import attack
import lp
import stats

HERE = os.path.dirname(os.path.abspath(__file__))
N = lp.N
rng = np.random.default_rng(int(os.environ.get("SEED", 3)))
OUT = []

PHRASE = ("FIND YOU ARE NECESSARILY ALONE WHEN YOU ARE BORN AND CANNOT COMMUNICATE IT IN ANY WAY FOREVER AFTER REMEMBER TO THINK OF ALL YOU VALUE IN ONE WORD "
          "JUST RECITE YOUR ANSWER NOW").split()
LENS = [4, 3, 3, 11, 5, 4, 3, 3, 4, 3, 6, 11, 2, 2, 3, 3, 7, 5, 8, 2, 4, 2, 3, 3, 5, 2, 3, 4, 4, 6, 4, 6, 3]
SPANS = {"S0": (3, 5), "S1": (7, 11), "S2": (18, 22), "S3": (22, 27), "S4": (29, 32)}   # word ranges of the five 16-rune matrices
FIB = sorted({x % 29 for x in (0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233)})


def say(s=""):
    print(s)
    OUT.append(s)


def spell(word, n):
    return next(s for s in attack.rune_spellings(word) if len(s) == n)


def regions(k):
    m = np.array(k).reshape(4, 4)
    t = int(m.sum()); i = int(m[1:3, 1:3].sum())
    return {"T": t, "D": int(np.trace(m)), "A": int(np.trace(m[::-1])), "C": int(m[0, 0] + m[0, 3] + m[3, 0] + m[3, 3]), "I": i, "B": t - i}


def repeated(mats):
    """values that occur in two different matrices (distinct values)"""
    seen = {}
    for name, r in mats.items():
        for v in r.values():
            seen.setdefault(v, set()).add(name)
    return sorted(v for v, s in seen.items() if len(s) > 1)


def pieces(keys):
    """the five matrices' region values from a key vector of 141 values (body runes 0..140)"""
    off = np.concatenate([[0], np.cumsum(LENS)])
    return {n: regions(keys[off[a]:off[b]]) for n, (a, b) in SPANS.items()}


def main():
    toks = stats.SEGS[7]
    c = np.array(lp.runes_of(toks))
    # cipher words as lp.word_spans cuts them: bare line and page breaks are wraps inside a word (until 2026-10-17 this
    # script cut at every line break, which split FOREVER, THINK, WORD and ANSWER)
    cw = [list(c[a:b]) for _, a, b in lp.word_spans(toks, lp.runes_of(toks))]
    heading = c[:13]
    body = c[13:13 + 141]
    say(f"section 0.7: {len(cw)} cipher words; first words of {[len(w) for w in cw[:2]]} runes = the 13-rune heading, then {[len(w) for w in cw[2:40]]}")
    assert [len(w) for w in cw[:2]] == [8, 5]
    off = np.concatenate([[0], np.cumsum(LENS)])
    cipher_cuts = set(np.cumsum([len(w) for w in cw[2:]]).tolist())
    inside = [(PHRASE[j], int(off[j + 1] - off[j])) for j in range(33) for cut in [None]
              if any(off[j] < x < off[j + 1] for x in cipher_cuts)]
    say(f"the 33 crib words cover {int(off[-1])} runes; cipher word separators that fall INSIDE a crib word: {len(inside)} ({inside}); "
        f"crib word boundaries that are cipher separators: {sum(int(x) in cipher_cuts for x in off[1:-1])} of 32")
    # --- reproduction of the quoted numbers
    P = np.array([x for w, n in zip(PHRASE, LENS) for x in spell(w, n)])
    K = (body - P) % N
    say(f"key of FIND = {K[:4].tolist()} (quoted 2 1 26 2); YOU {K[4:7].tolist()} (3 8 21); ARE {K[7:10].tolist()} (8 5 13)")
    assert K[:10].tolist() == [2, 1, 26, 2, 3, 8, 21, 8, 5, 13]
    kk = [int(K[off[a]:off[b]].sum()) for a, b in [(0, 3), (3, 5), (5, 10)]]
    say(f"key sums of the first three blocks {kk} (quoted 89, 115, 230), total {sum(kk)} (quoted 434); plus CANNOT = {int(K[off[10]:off[11]].sum())} -> "
        f"{sum(kk) + int(K[off[10]:off[11]].sum())} (quoted 491)")
    mats = pieces(K)
    say("matrix regions T/D/A/C/I/B: " + "; ".join(f"{n} " + "/".join(str(v) for v in r.values()) for n, r in mats.items()))
    say(f"values repeated across different matrices: {repeated(mats)} (quoted 32, 201, 51, 54, 41)")
    spans16 = [(a, b) for a in range(33) for b in range(a + 1, 34) if off[b] - off[a] == 16]
    say(f"word-aligned 16-rune spans in the crib: {len(spans16)} (quoted: exactly five)")
    # --- Fibonacci claim
    inset = np.isin(K, FIB)
    say("")
    say(f"Fibonacci residues mod 29: {FIB} ({len(FIB)} of 29 values, chance {len(FIB) / 29:.3f} per rune)")
    say(f"key values in that set: first 14 body runes {int(inset[:14].sum())} of 14 (all 14 by chance: {(len(FIB) / 29) ** 14:.1e}); "
        f"remaining 127 body runes {int(inset[14:].sum())} (chance expectation {127 * len(FIB) / 29:.0f})")
    words = {}
    for w in lp.COMMON_N:
        for s in attack.rune_spellings(w):
            words.setdefault(len(s), set()).add((w, s))
    for name, a, b, rl in (("FIND", 0, 4, 4), ("YOU", 4, 7, 3), ("ARE", 7, 10, 3), ("NECESSARILY (8 of 11 in the set)", 10, 21, 11)):
        cs = body[a:b] if rl < 11 else body[10:21]
        fit = [w for w, s in words[rl] if (np.isin((cs - np.array(s)) % N, FIB).all() if rl < 11 else np.isin((cs - np.array(s)) % N, FIB).sum() >= 8)]
        say(f"   slot {name}: {len(words[rl])} dictionary spellings of {rl} runes, {len(fit)} give a key entirely inside the set"
            f"{'' if rl < 11 else ' (>= 8 of 11)'}: {sorted(set(fit))[:14]}")
    # --- nulls: random dictionary words of the same lengths on the same ciphertext
    T = 20000
    bylen = {n: [s for _, s in sorted(v)] for n, v in words.items()}
    reps, hit491, hit491_any, nrep_obs = [], 0, 0, len(repeated(mats))
    first14, zeros = [], []
    for _ in range(T):
        Pn = np.array([x for n in LENS for x in bylen[n][rng.integers(len(bylen[n]))]])
        Kn = (body - Pn) % N
        reps.append(len(repeated(pieces(Kn))))
        pre = np.cumsum([int(Kn[off[j]:off[j + 1]].sum()) for j in range(33)])
        hit491 += int(pre[10] == 491)
        hit491_any += int((pre == 491).any())
        first14.append(int(np.isin(Kn[:14], FIB).sum()))
        zeros.append(int((Kn == 0).sum()))
    reps = np.array(reps)
    say("")
    say(f"nulls ({T} draws of random dictionary words with the crib's rune lengths on the same ciphertext):")
    say(f"   values repeated across the five matrices: mean {reps.mean():.1f}, P(>= {nrep_obs}) = {(reps >= nrep_obs).mean():.2f} (observed {nrep_obs})")
    say(f"   key running total equal to 491 after CANNOT: {hit491 / T:.4f}; at any of the 33 word ends: {hit491_any / T:.4f}")
    say(f"   key values equal to 0 (plaintext rune = cipher rune): observed {int((K == 0).sum())} of 141 (expected {141 / 29:.1f}); null mean {np.mean(zeros):.1f}")
    say(f"   Fibonacci-set keys among the first 14 runes for a random word choice: mean {np.mean(first14):.1f} of 14 (14 of 14 in {(np.array(first14) == 14).sum()} draws)")
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "crib_matrix_check.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    sys.exit(main())
