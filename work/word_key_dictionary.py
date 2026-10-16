"""Dictionary-consistency test for per-word keys with algebraic structure.

If every word is enciphered c_j = p_j + k_j with a key that has structure *inside the word*, the key cancels in a
suitable difference operator, and the ciphertext word is consistent with an English plaintext word p exactly when
    Delta(c) == Delta(p)          (mod 29)
for that operator. Key families and operators:
  * polynomial of degree d in the position j (any coefficients, new ones for every word): Delta = (d+1)-th finite
    difference. d = 0 is a Caesar shift per word, d = 1 an arithmetic progression, d = 2 a quadratic.
  * a per-word key vector of period P (new vector for every word, restarted at the word start): Delta = lag-P
    difference c[j+P] - c[j].
For a ciphertext word of length L there are L - (d+1) (or L - P) independent constraints, so a random word has
about N_L * 29^-(constraints) consistent dictionary words (N_L = dictionary words of length L), i.e. almost never,
while a word that really follows the model has its plaintext among the consistent words. No dictionary lookup is
needed beyond one vectorised comparison per word.

Controls in the same run: random-rune surrogates with LP2's word lengths and anti-repeat rule (null) and dictionary
words enciphered under each model (with and without extra key-pointer jumps, which an anti-repeat rule causes).
The dictionary covers only part of English (the 20k-word list), so the planted hit rate is shown next to the share
of English word tokens in the dictionary.

    python work/word_key_dictionary.py        # -> results/analysis/word_key_dictionary.txt
"""
import os
import random
import re
import sys

import numpy as np

import attack
import lp
import stats

N = lp.N
HERE = os.path.dirname(os.path.abspath(__file__))

_DIG = {}


def digits():
    """rune digits (n, L) of every dictionary word, per length L"""
    if not _DIG:
        for L, (codes, _w) in attack.rune_dictionary().items():
            if len(codes) == 0:
                continue
            x = codes.copy()
            cols = []
            for _ in range(L):
                cols.append(x % N)
                x //= N
            _DIG[L] = np.stack(cols[::-1], axis=1)
    return _DIG


def fdiff(a, k):
    a = np.asarray(a)
    for _ in range(k):
        a = (a[..., 1:] - a[..., :-1]) % N
    return a


def lagdiff(a, p):
    a = np.asarray(a)
    return (a[..., p:] - a[..., :-p]) % N


def family_op(kind, par):
    """returns (operator, number of constraints for length L)"""
    if kind == "poly":
        return (lambda a: fdiff(a, par + 1)), (lambda L: L - (par + 1))
    return (lambda a: lagdiff(a, par)), (lambda L: L - par)


def consistent(word, op):
    D = digits().get(len(word))
    if D is None:
        return None
    return int((op(D) == op(word)[None, :]).all(axis=1).sum())


def table(words, kind, par, min_constraints=3):
    op, ncons = family_op(kind, par)
    out = {}
    for L in range(2, 13):
        if L not in digits() or ncons(L) < min_constraints:
            continue
        ws = [w for w in words if len(w) == L]
        if not ws:
            continue
        m = [consistent(w, op) for w in ws]
        out[L] = (len(ws), sum(1 for x in m if x > 0), len(digits()[L]) * float(N) ** -ncons(L))
    return out


def lp2_words():
    out = []
    for i in stats.UNSOLVED:
        c = lp.runes_of(stats.SEGS[i])
        out += [c[a:b] for _, a, b in lp.word_spans(stats.SEGS[i], c)]
    return out


def surrogate(lens, rng, q=0.82):
    out, prev = [], -1
    for L in lens:
        w = []
        for _ in range(L):
            x = rng.randrange(N)
            while x == prev and rng.random() < q:
                x = rng.randrange(N)
            w.append(x)
            prev = x
        out.append(w)
    return out


def encipher(seqs, kind, par, rng, jump=0.0, q=0.82):
    """dictionary words enciphered under the skip rule with a fresh per-word key of the given family"""
    out, prev = [], -1
    for s in seqs:
        if kind == "poly":
            co = [rng.randrange(N) for _ in range(par + 1)]
            key = lambda ptr, co=co: sum(co[i] * pow(ptr, i, N) for i in range(len(co))) % N
        else:
            vec = [rng.randrange(N) for _ in range(par)]
            key = lambda ptr, vec=vec: vec[ptr % len(vec)]
        c, ptr = [], 0
        for t in s:
            if rng.random() < jump:
                ptr += 1
            y = (t + key(ptr)) % N
            ptr += 1
            while y == prev and rng.random() < q:
                y = (t + key(ptr)) % N
                ptr += 1
            c.append(y)
            prev = y
        out.append(c)
    return out


def sample_dictionary(rng, per_len=250, lo=4, hi=12):
    seqs = []
    for L, D in digits().items():
        if lo <= L <= hi:
            for k in rng.sample(range(len(D)), min(per_len, len(D))):
                seqs.append([int(x) for x in D[k]])
    return seqs


def coverage():
    """share of English word tokens (Emerson, spelled in runes) that are in the dictionary, by rune length"""
    path = os.path.join(HERE, "ref", "emerson_essays1.txt")
    with open(path, encoding="utf-8") as f:
        txt = f.read()
    txt = txt[txt.index("SELF-RELIANCE"):].split("*** END OF")[0]
    D = {L: set(int(sum(int(x) * N ** (L - 1 - i) for i, x in enumerate(row))) for row in rows)
         for L, rows in digits().items()}
    tot, hit = {}, {}
    for w in re.findall(r"[A-Za-z]+", txt)[:40000]:
        s = lp.word_to_key(w.upper().replace("IO", "IA"))
        L = len(s)
        code = sum(x * N ** (L - 1 - i) for i, x in enumerate(s))
        tot[L] = tot.get(L, 0) + 1
        hit[L] = hit.get(L, 0) + (code in D.get(L, ()))
    return {L: hit[L] / tot[L] for L in sorted(tot) if tot[L] >= 50}


def main():
    rng = random.Random(3)
    real = lp2_words()
    lens = [len(w) for w in real]
    sur = surrogate(lens, rng)
    seqs = sample_dictionary(rng)
    cov = coverage()
    out = []
    P = out.append
    P("Dictionary: " + ", ".join(f"L{L}: {len(v)}" for L, v in sorted(digits().items())) + " words")
    P("Share of English word tokens (Emerson) found in the dictionary: " + ", ".join(f"L{L} {100 * c:.0f}%" for L, c in cov.items() if L >= 5))
    P("")
    P("Each cell: ciphertext words of that length with >= 1 consistent dictionary word / words of that length; "
      "[null expectation of consistent words per word].")
    P("LP2 | surrogate = random runes with LP2's word lengths | planted = dictionary words enciphered under the model "
      "(no jumps / extra pointer jump 0.05 per rune).")
    for kind, par, label in (("poly", 0, "key = constant per word (Caesar shift per word)"),
                             ("poly", 1, "key = arithmetic progression in the position (any start, any step)"),
                             ("poly", 2, "key = quadratic in the position (any coefficients)"),
                             ("per", 2, "per-word key vector of period 2"), ("per", 3, "per-word key vector of period 3"),
                             ("per", 4, "per-word key vector of period 4"), ("per", 5, "per-word key vector of period 5"),
                             ("per", 6, "per-word key vector of period 6"), ("per", 7, "per-word key vector of period 7")):
        tr, ts = table(real, kind, par), table(sur, kind, par)
        tp0 = table(encipher(seqs, kind, par, rng, 0.0), kind, par)
        tp1 = table(encipher(seqs, kind, par, rng, 0.05), kind, par)
        P("")
        P(f"== {label}")
        for name, t in (("LP2", tr), ("surrogate", ts), ("planted", tp0), ("planted, jumps", tp1)):
            P(f"   {name:15s}" + "  ".join(f"L{L}: {a}/{n}" for L, (n, a, e) in t.items()))
        P("   null expectation / word  " + "  ".join(f"L{L}: {e:.3f}" for L, (n, a, e) in tr.items()))
    P("")
    P("Reading: LP2 behaves like the random surrogate for every family (no word of length >= 6 is consistent beyond "
      "chance), while planted keys are recovered for 50-100% of the dictionary words (less with jumps). The "
      "dictionary covers part of English, so the expected LP2 hit rate under a model is the planted rate times the "
      "coverage above: far more than the zero observed. Per-word keys that are constant, linear, quadratic or periodic "
      "with period <= 7 (fresh for every word, English plaintext) are excluded. Words of 4-5 runes have too few "
      "constraints to be informative.")
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "word_key_dictionary.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
