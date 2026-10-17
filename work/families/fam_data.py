"""Data for the family simulations: the real LP2 (sections 0.7-0.15, the project's word segmentation) and English plaintext in runes.

Segmentation arrays are (T,) for the real text and (R, T) for R simulated replicates: `start` flags the first rune of a word, `sid` the section.
"""
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, WORK)
import lp  # noqa: E402
import stats  # noqa: E402

N = lp.N
CORPORA = ["emerson_essays1.txt", os.path.join("corpora", "pg205.txt"), os.path.join("corpora", "pg2680.txt"), os.path.join("corpora", "pg1497.txt"),
           os.path.join("corpora", "pg1998.txt"), os.path.join("corpora", "pg2009.txt")]


def lp2():
    """the real LP2 as (runes (T,), start (T,) bool, sid (T,)): sections 0.7-0.15, words as lp.word_spans cuts them"""
    runes, start, sid = [], [], []
    for k, i in enumerate(stats.UNSOLVED):
        toks = stats.SEGS[i]
        r = lp.runes_of(toks)
        st = np.zeros(len(r), bool)
        for _, a, b in lp.word_spans(toks, r):
            st[a] = True
        runes += r; start += st.tolist(); sid += [k] * len(r)
    return np.array(runes), np.array(start), np.array(sid)


def english(max_words=400_000):
    """English as rune words from the Gutenberg texts in work/ref (git-ignored corpora): (runes (M,), start (M,) bool).
    Words are spelled like the project's other models (greedy digraphs, IO -> IA)."""
    cache, runes, start = {}, [], []
    n = 0
    for name in CORPORA:
        path = os.path.join(WORK, "ref", name)
        if not os.path.exists(path):
            continue
        txt = open(path, encoding="utf-8", errors="ignore").read()
        if "SELF-RELIANCE" in txt:
            txt = txt[txt.index("SELF-RELIANCE"):]
        txt = txt.split("*** END OF")[0]
        for w in re.findall(r"[A-Za-z]+", txt):
            r = cache.get(w.lower())
            if r is None:
                r = cache[w.lower()] = lp.word_to_key(w.upper().replace("IO", "IA"))
            if not r:
                continue
            runes += r; start += [True] + [False] * (len(r) - 1)
            n += 1
            if n >= max_words:
                break
    return np.array(runes), np.array(start)


def windows(eng, T, R, rng, natural, lp2_start, sec_start):
    """R plaintext windows of T runes: (P (R,T), start (R,T)). natural=True keeps English word boundaries, else the LP2 word cuts are imposed on the
    English rune stream (the 'separators are not the plaintext words' reading). Section starts are always word starts."""
    runes, start = eng
    starts = np.flatnonzero(start)
    starts = starts[starts < len(runes) - T]
    a = rng.choice(starts, R)
    P = np.stack([runes[x:x + T] for x in a])
    st = np.stack([start[x:x + T] for x in a]) if natural else np.broadcast_to(lp2_start, (R, T)).copy()
    st[:, 0] = True
    st |= sec_start[None, :]
    return P, st
