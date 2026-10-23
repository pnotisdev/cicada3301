"""Dense brute-force EXACT reference for the union null arc (R4 repair s08): Fractions, no DP, no class sets, null positions enumerated explicitly.

P(c | offset o) = sum over every per-word placement of the (at most one) keyless null of  prod_words weight(word, placement) * P(c | explicit null positions),
with the slot set S(Lc) of a word of cipher length Lc (words from the word-start flags; position 0 starts a word):
    place 'any'      S = {0..Lc-1}   (Lc >= 2)   weight nu/Lc each, 1-nu for no null     (the union arc: R4 as fitted)
    place 'interior' S = {1..Lc-2}   (Lc >= 3)   weight nu/(Lc-2)                       (the mid arc, kind 3)
    place 'edge'     S = {0, Lc-1}   (Lc >= 2)   weight nu/2
    words with an empty S: weight 1 (no null).
P(c | null positions) is the exact event tree of the encryptors, taken unchanged from work/chanscreen/v2/reference_mid.py (`prob_nulls`: plaintext symbol x channel randomness,
nulls emitted 1/Q, no key, invisible to the anti-repeat rule and the LM; first rune with no previous real rune compares with nothing).  Only the placement enumeration is new here.
Mutants of `prob_nulls` (null_visible, null_keyed) pass through; placement mutants are 'mid_weights' (interior slots with the mid arc's weights used where 'any' is meant) and
'unnormalised' (weight nu per slot, no division by |S|).
"""
import sys
from fractions import Fraction as F
from itertools import product
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'chanscreen' / 'v2'))
from reference_mid import prob_nulls, words_of  # noqa: E402  (read-only reuse)


def slots_of(a, b, place):
    lc = b - a
    if place == 'any':
        return list(range(a, b)) if lc >= 2 else []
    if place == 'interior':
        return list(range(a + 1, b - 1)) if lc >= 3 else []
    if place == 'edge':
        return [a, b - 1] if lc >= 2 else []
    raise ValueError(place)


def prob(c, key, o, s, q, ch, pi, L, wstart, nu, place='any', uniform=False, mutant=None):
    n = len(c)
    nu = F(nu)
    if n == 0:
        return F(1)
    pl = 'interior' if mutant == 'mid_weights' else place
    opts = []
    for a, b in words_of(n, wstart):
        sl = slots_of(a, b, pl)
        if not sl:
            opts.append([(F(1), ())])
        else:
            wt = nu if mutant == 'unnormalised' else nu / len(sl)
            opts.append([(1 - nu, ())] + [(wt, (t,)) for t in sl])
    tot = F(0)
    for combo in product(*opts):
        w = F(1)
        ns = set()
        for wt, t in combo:
            w *= wt
            ns.update(t)
        if w == 0:
            continue
        pm = mutant if mutant in ('null_visible', 'null_keyed') else None
        tot += w * prob_nulls(c, key, o, s, q, ch, pi, L, ns, uniform, pm)
    return tot


def all_offsets_ref(c, key, s, q, ch, pi, L, wstart, nu, place='any', mutant=None):
    m = len(key)
    n = len(c)
    out = []
    for o in range(m + 1):
        if n >= 1 and o >= m:
            out.append((F(0), F(0)))
            continue
        out.append((prob(c, key, o, s, q, ch, pi, L, wstart, nu, place, False, mutant),
                    prob(c, key, o, s, q, ch, pi, L, wstart, nu, place, True, mutant)))
    return out
