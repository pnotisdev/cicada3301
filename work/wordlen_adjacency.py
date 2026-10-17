"""Do LP2's word separators carry linguistic structure? Adjacent word lengths in running English are correlated (a 2-letter function word
is followed by a longer word more often than chance, long words are rarely adjacent...). If the separators of LP2 mark real words of a
language, its word-length sequence should show such serial structure even though the length histogram is off; if the lengths were drawn
independently (random segmentation of a stream with a length distribution) the serial structure is at the shuffled level.

Statistics per sequence set (pairs never cross a section / text boundary): mutual information (bits) between L_i and L_{i+1} with lengths binned
1..8 and 9+, and the Pearson correlation at lags 1-3, each with a z-score against shuffles of the same set (shuffled inside each section).
Controls: the solved sections 0-6, 16, 17 (words placed by the Cicadas), English runs (Emerson; KJV and Walden if fetched) cut to LP2's size.

    python work/wordlen_adjacency.py          # -> results/analysis/wordlen_adjacency.txt
"""
import os
import re
import sys

import numpy as np

import lp
import stats

HERE = os.path.dirname(os.path.abspath(__file__))
NB = 9
SOLVED = [0, 1, 2, 3, 4, 5, 6, 16, 17]
LAGS = (1, 2, 3)


def seqs_of(ids):
    out = []
    for i in ids:
        c = lp.runes_of(stats.SEGS[i])
        out.append([b - a for _, a, b in lp.word_spans(stats.SEGS[i], c)])
    return out


def english_seqs(path, marker, rune_len=True, chunk=150, n_chunks=None, cap=400000):
    with open(path, encoding="utf-8", errors="replace") as f:
        txt = f.read()
    txt = txt.split("*** START OF", 1)[-1].split("*** END OF", 1)[0]
    if marker:
        i = txt.find(marker)
        txt = txt[i if i >= 0 else 0:]
    txt = txt[:cap]
    ws = re.findall(r"[A-Za-z]+", txt)
    lens = [len(lp.word_to_key(w.upper().replace("IO", "IA"))) if rune_len else len(w) for w in ws]
    lens = [x for x in lens if x]
    return [lens[k:k + chunk] for k in range(0, len(lens) - chunk + 1, chunk)][:n_chunks]


def pairs(seqs, lag):
    a = np.concatenate([np.array(s[:-lag]) for s in seqs if len(s) > lag])
    b = np.concatenate([np.array(s[lag:]) for s in seqs if len(s) > lag])
    return a, b


def mi(a, b):
    a, b = np.minimum(a, NB) - 1, np.minimum(b, NB) - 1
    j = np.zeros((NB, NB))
    np.add.at(j, (a, b), 1)
    j /= j.sum()
    pa, pb = j.sum(1, keepdims=True), j.sum(0, keepdims=True)
    m = j > 0
    return float((j[m] * np.log2(j[m] / (pa @ pb)[m])).sum())


def corr(a, b):
    return float(np.corrcoef(a, b)[0, 1])


def evaluate(name, seqs, rng, reps=400):
    n = sum(len(s) for s in seqs)
    obs = {lag: (mi(*pairs(seqs, lag)), corr(*pairs(seqs, lag))) for lag in LAGS}
    null = {lag: ([], []) for lag in LAGS}
    for _ in range(reps):
        sh = [list(rng.permutation(s)) for s in seqs]
        for lag in LAGS:
            m, c = mi(*pairs(sh, lag)), corr(*pairs(sh, lag))
            null[lag][0].append(m)
            null[lag][1].append(c)
    cells = []
    for lag in LAGS:
        m, c = obs[lag]
        zm = (m - np.mean(null[lag][0])) / (np.std(null[lag][0]) or 1)
        zc = (c - np.mean(null[lag][1])) / (np.std(null[lag][1]) or 1)
        cells.append(f"lag{lag}: r {c:+.3f} (z {zc:+5.1f}), MI {m:.4f} (z {zm:+5.1f})")
    return f"{name:34s} n={n:5d}  " + " | ".join(cells)


def pmi_section(path, sets, rng, reps=400):
    """A likelihood-ratio style statistic: the mean pointwise mutual information of adjacent length pairs under an English table trained on the
    first 40,000 Emerson words, evaluated on held-out English, on LP2 and on shuffles of LP2 (English-like serial structure scores ~ the MI of English)."""
    ws = re.findall(r"[A-Za-z]+", open(path, encoding="utf-8").read())
    lens = [len(lp.word_to_key(w.upper().replace("IO", "IA"))) for w in ws]
    lens = np.array([x for x in lens if x])
    train, test = lens[:40000], lens[40000:]
    a, b = np.minimum(train[:-1], NB) - 1, np.minimum(train[1:], NB) - 1
    J = np.full((NB, NB), 0.5)
    np.add.at(J, (a, b), 1)
    J /= J.sum()
    pmi = np.log2(J / (J.sum(1, keepdims=True) @ J.sum(0, keepdims=True)))

    def score(seqs):
        x, y = pairs(seqs, 1)
        return float(pmi[np.minimum(x, NB) - 1, np.minimum(y, NB) - 1].mean())

    out = ["Mean pointwise mutual information of adjacent length pairs under an English table (trained on 40,000 Emerson words; "
           "English-like serial structure scores near the English value, independent lengths near 0):"]
    held = [list(test[k:k + 150]) for k in range(0, min(len(test), 3000) - 150 + 1, 150)]
    out.append(f"  held-out English (Emerson, {sum(len(h) for h in held)} words): {score(held):+.4f}")
    for name, seqs in sets[:2]:
        sc = score(seqs)
        nul = [score([list(rng.permutation(q)) for q in seqs]) for _ in range(reps)]
        out.append(f"  {name:38s}: {sc:+.4f}   shuffled: mean {np.mean(nul):+.4f} sd {np.std(nul):.4f}  z {(sc - np.mean(nul)) / np.std(nul):+.1f}")
    return out


def main():
    rng = np.random.default_rng(3)
    out = ["Serial structure of word lengths: Pearson r and mutual information at lags 1-3, z against shuffles inside each section/chunk "
           "(400 shuffles)", ""]
    sets = [("LP2 unsolved sections 0.7-0.15", seqs_of(stats.UNSOLVED)),
            ("solved sections 0-6, 16, 17 (control)", seqs_of(SOLVED))]
    em = os.path.join(HERE, "ref", "emerson_essays1.txt")
    txt = open(em, encoding="utf-8").read()
    txt = txt[txt.index("SELF-RELIANCE"):].split("*** END OF")[0]
    tmp = os.path.join(HERE, "..", "work", "tmp", "_emerson_body.txt")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt)
    sets.append(("English (Emerson), runes, 20 chunks of 150", english_seqs(tmp, None, True, 150, 20)))
    sets.append(("English (Emerson), letters", english_seqs(tmp, None, False, 150, 20)))
    corp = os.path.join(HERE, "ref", "corpora")
    for name, fn, marker in (("English (KJV)", "pg10.txt", "In the beginning"), ("English (Walden)", "pg205.txt", "Economy"),
                             ("English (Milton)", "pg26.txt", "BOOK I"), ("Latin (Caesar)", "pg218.txt", "GALLIA"),
                             ("German (Faust)", "pg2229.txt", "Faust")):
        p = os.path.join(corp, fn)
        if os.path.exists(p):
            sets.append((name + ", runes, 20 chunks of 150", english_seqs(p, marker, True, 150, 20)))
    for name, seqs in sets:
        out.append(evaluate(name, seqs, rng))
    out.append("")
    out += pmi_section(tmp, sets, rng)
    out.append("")
    out.append("Reading: z is the distance of the observed statistic from its mean over within-section shuffles. Real word sequences "
               "(the solved sections, English, Latin, German) have serial structure at lag 1; a sequence of independently drawn lengths has z around 0.")
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "wordlen_adjacency.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
