"""How special is it that an English phrase fits a given word-length pattern? For the 33-word crib pattern of the community's 'FIND YOU ARE NECESSARILY ALONE ...' and for
null patterns, the MOST FLUENT word sequence (word-bigram language model from the Gutenberg texts in ref/corpora, 20k-word vocabulary) whose word i has the pattern's rune
length is found by Viterbi. If the optimum for random patterns is as fluent as for the real one, a fluent fit says nothing about the pattern.

Null patterns: (a) random permutations of the crib's 33 lengths, (b) 33 consecutive cipher words from random places of LP2 (sections 0.7-0.15).

    python work/crib_fluency_null.py          # -> results/analysis/crib_fluency_null.txt
"""
import glob
import os
import re
import sys

import numpy as np

import attack
import lp
import stats

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "ref")
rng = np.random.default_rng(int(os.environ.get("SEED", 5)))
OUT = []
LAMBDA = 0.7
CRIB = ("find you are necessarily alone when you are born and cannot communicate it in any way forever after remember to think of all you value in one word "
        "just recite your answer now").split()
CRIB_LENS = [4, 3, 3, 11, 5, 4, 3, 3, 4, 3, 6, 11, 2, 2, 3, 3, 7, 5, 8, 2, 4, 2, 3, 3, 5, 2, 3, 4, 4, 6, 4, 6, 3]


def say(s=""):
    print(s)
    OUT.append(s)


def build():
    vocab = [w.strip() for w in open(os.path.join(REF, "english_20k.txt"), encoding="utf-8")]
    vocab = [w for w in vocab if w.isalpha()]
    for w in CRIB:
        if w not in vocab:
            vocab.append(w)
    ix = {w: i for i, w in enumerate(vocab)}
    pairs, uni = [], np.zeros(len(vocab))
    for f in sorted(glob.glob(os.path.join(REF, "corpora", "pg*.txt"))):
        txt = open(f, encoding="utf-8", errors="ignore").read().lower()
        ids = np.array([ix.get(w, -1) for w in re.findall(r"[a-z]+", txt)])
        ok = ids >= 0
        uni += np.bincount(ids[ok], minlength=len(vocab))
        m = ok[:-1] & ok[1:]
        pairs.append(ids[:-1][m] * len(vocab) + ids[1:][m])
    key, cnt = np.unique(np.concatenate(pairs), return_counts=True)
    ia, ib = key // len(vocab), key % len(vocab)
    lens = [sorted({len(s) for s in attack.rune_spellings(w.upper())}) for w in vocab]
    return vocab, ix, uni, ia, ib, cnt, lens


def viterbi(pattern, V, uni, ia, ib, cnt, mem, want_path=False):
    n = len(uni)
    p1 = (uni + 1) / (uni + 1).sum()
    pa = uni[ia]
    tail = np.log(LAMBDA * cnt / pa)
    score = np.where(mem[pattern[0]], np.log(p1), -np.inf)
    back = []
    for L, Lp in zip(pattern[1:], pattern):
        obs = mem[Lp][ia] & mem[L][ib]
        val = score[ia[obs]] + np.log(LAMBDA * cnt[obs] / pa[obs] + (1 - LAMBDA) * p1[ib[obs]])
        best = np.full(n, -np.inf); arg = np.full(n, -1)
        order = np.argsort(val)                              # last write wins = largest value
        best[ib[obs][order]] = val[order]; arg[ib[obs][order]] = ia[obs][order]
        top = int(np.argmax(score)); fall = score[top] + np.log((1 - LAMBDA) * p1)
        use = (fall > best) & mem[L]
        best[use] = fall[use]; arg[use] = top
        best[~mem[L]] = -np.inf
        score = best
        back.append(arg.copy())
    end = int(np.argmax(score))
    if not want_path:
        return float(score[end]) / len(pattern), None
    path = [end]
    for arg in reversed(back):
        path.append(int(arg[path[-1]]))
    return float(score[end]) / len(pattern), [V[i] for i in reversed(path)]


def phrase_score(words, ix, uni, ia, ib, cnt):
    n = len(uni)
    p1 = (uni + 1) / (uni + 1).sum()
    key = ia * n + ib
    srt = np.argsort(key)
    s = np.log(p1[ix[words[0]]])
    for a, b in zip(words, words[1:]):
        k = ix[a] * n + ix[b]
        j = np.searchsorted(key[srt], k)
        c = cnt[srt[j]] if j < len(key) and key[srt[j]] == k else 0
        s += np.log(LAMBDA * c / max(uni[ix[a]], 1) + (1 - LAMBDA) * p1[ix[b]])
    return s / len(words)


def main():
    V, ix, uni, ia, ib, cnt, lens = build()
    mem = {L: np.array([L in l for l in lens]) for L in range(1, 20)}
    say(f"bigram model: vocabulary {len(V)}, {len(ia)} distinct bigrams, {int(uni.sum())} word tokens from ref/corpora; interpolation lambda {LAMBDA}")
    ps = phrase_score(CRIB, ix, uni, ia, ib, cnt)
    sc, path = viterbi(CRIB_LENS, V, uni, ia, ib, cnt, mem, True)
    say(f"the community crib's own mean log-probability per word under this model: {ps:.2f}")
    say(f"most fluent sentence with the same 33 rune lengths: {sc:.2f} per word:  {' '.join(path).upper()}")
    perm = [viterbi(list(rng.permutation(CRIB_LENS)), V, uni, ia, ib, cnt, mem)[0] for _ in range(60)]
    say(f"   (a) 60 random permutations of the crib's 33 lengths: best-sentence score mean {np.mean(perm):.2f}, sd {np.std(perm):.2f}, min {np.min(perm):.2f}, max {np.max(perm):.2f}")
    cw = []
    for si in range(7, 16):                       # cipher word lengths as lp.word_spans cuts them (line and page wraps rejoined)
        c = lp.runes_of(stats.SEGS[si])
        cw.append([b - a for _, a, b in lp.word_spans(stats.SEGS[si], c)])
    flat = [(si, j) for si, ws in enumerate(cw) for j in range(len(ws) - 33)]
    pick = [flat[i] for i in rng.choice(len(flat), 60, replace=False)]
    win = [viterbi(cw[si][j:j + 33], V, uni, ia, ib, cnt, mem)[0] for si, j in pick]
    real = viterbi(cw[0][2:35], V, uni, ia, ib, cnt, mem)[0]
    fin = np.array([w for w in win if np.isfinite(w)])          # a window with a word length no vocabulary word has (e.g. 13+ runes) has no fit at all
    say(f"   (b) 60 windows of 33 consecutive LP2 cipher words at random places (no merges): {len(fin)} have a fit, mean {fin.mean():.2f}, sd {fin.std():.2f}, "
        f"min {fin.min():.2f}, max {fin.max():.2f}; the real location (words 3-35 of 0.7, no merges): {real:.2f}")
    say(f"   the crib's best fit ({sc:.2f}) lies {(sc - np.mean(perm)) / np.std(perm):+.1f} sd from the permutation null and "
        f"{(sc - fin.mean()) / fin.std():+.1f} sd from the LP2-window null; the real location ({real:.2f}) lies {(real - fin.mean()) / fin.std():+.1f} sd from it; "
        f"the crib phrase itself ({ps:.2f}) is below the optimum by {sc - ps:.2f} per word")
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "crib_fluency_null.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    sys.exit(main())
