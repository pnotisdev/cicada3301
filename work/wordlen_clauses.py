"""Do LP2's clause marks ('.') sit where sentence ends do? Word-length statistics at clause boundaries: in English the first word of a sentence is short
more often than average (THE, IT, WE, A, IN ...) and the last word is longer; the number of words per clause has an English spread. Compared with the
solved sections (the Cicadas' own clause marks), English prose (Emerson: sentences split at . ! ? ; : ) and LP2's own words in shuffled order.

    python work/wordlen_clauses.py          # -> results/analysis/wordlen_clauses.txt
"""
import os
import re
import sys

import numpy as np

import lp
import stats

HERE = os.path.dirname(os.path.abspath(__file__))
SOLVED = [0, 1, 2, 3, 4, 5, 6, 16, 17]


def clauses_of(ids):
    """[[word lengths of one clause]] per clause-mark-delimited unit (a clause mark is the token '.')"""
    out = []
    for i in ids:
        toks = stats.SEGS[i]
        cur, w = [], 0
        for t in toks:
            if isinstance(t, int):
                w += 1
            else:
                if w:
                    cur.append(w)
                    w = 0
                if t == "." and cur:
                    out.append(cur)
                    cur = []
        if w:
            cur.append(w)
        if cur:
            out.append(cur)
    return out


def english_clauses(path):
    txt = open(path, encoding="utf-8").read()
    txt = txt[txt.index("SELF-RELIANCE"):].split("*** END OF")[0]
    out = []
    for sent in re.split(r"[.!?;:]+", txt):
        ws = re.findall(r"[A-Za-z]+", sent)
        if len(ws) >= 1:
            out.append([len(lp.word_to_key(w.upper().replace("IO", "IA"))) for w in ws])
    return out


def summarize(name, cl, rng, reps=2000):
    allw = np.array([x for c in cl for x in c])
    first = np.array([c[0] for c in cl])
    last = np.array([c[-1] for c in cl if len(c) > 1])
    n = np.array([len(c) for c in cl])
    zf = (first.mean() - allw.mean()) / (allw.std() / np.sqrt(len(first)))
    zl = (last.mean() - allw.mean()) / (allw.std() / np.sqrt(len(last)))
    # shuffled null: same clause sizes, words permuted
    nulls = []
    for _ in range(reps):
        p = rng.permutation(allw)
        k, idx = [], 0
        for s in n:
            k.append(p[idx])
            idx += s
        nulls.append(np.mean(k))
    zs = (first.mean() - np.mean(nulls)) / np.std(nulls)
    return (f"{name:34s} clauses {len(cl):5d}  words/clause mean {n.mean():5.1f} sd {n.std():5.1f} (CV {n.std() / n.mean():.2f})  "
            f"first word {first.mean():.2f} (z vs shuffle {zs:+.1f})  last word {last.mean():.2f}  all {allw.mean():.2f}  "
            f"2-rune share of first words {100 * np.mean(first == 2):.1f}% (all {100 * np.mean(allw == 2):.1f}%)")


def main():
    rng = np.random.default_rng(5)
    out = ["Clause-boundary statistics of word lengths", ""]
    out.append(summarize("LP2 unsolved 0.7-0.15", clauses_of(stats.UNSOLVED), rng))
    out.append(summarize("solved sections (Cicadas' marks)", clauses_of(SOLVED), rng))
    out.append(summarize("English prose (Emerson), sentences", english_clauses(os.path.join(HERE, "ref", "emerson_essays1.txt"))[:3000], rng))
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "wordlen_clauses.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
