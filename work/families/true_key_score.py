"""Power audit of the boundary-free sweeps and the OEIS lane: what does a TRUE key score on Cicada's own plaintext?

The boundary-free statistic (work/phpmt/bg.py) scores a decoded window by sum 10 ln(29 P(b|a)) under an English rune-bigram table trained on Emerson's Self-Reliance onward; the ledger says 'a true key scores about +10 per rune'. That figure
is an in-sample Emerson number. The sweeps gate at +300 (120-rune windows, abort after 40 runes below +60) and the OEIS lane at +300 on 36-rune windows. Here the same score is computed on (a) the plaintext of the solved Liber Primus sections (Cicada's
real text), (b) Emerson itself (in-sample), (c) other English books (held out), and the fraction of windows that would pass each gate. A true key decodes to the plaintext, so this is the score a correct key would get (the beam can only do better).

    python work/families/true_key_score.py          # -> results/analysis/true_key_score.txt
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, WORK)
sys.path.insert(0, os.path.join(WORK, "phpmt"))
import lp  # noqa: E402
import stats  # noqa: E402
import bg  # noqa: E402
import fam_data as D  # noqa: E402

OUT = []


def say(s=""):
    print(s)
    OUT.append(s)


def window_scores(stream, tbl, L):
    """score of every window of L runes: tbl[29][p0] + sum tbl[p_(k-1)][p_k]"""
    s = np.asarray(stream)
    pair = tbl[s[:-1], s[1:]].astype(np.int64)
    first = tbl[29][s].astype(np.int64)
    cs = np.concatenate([[0], np.cumsum(pair)])
    n = len(s) - L + 1
    idx = np.arange(n)
    return first[idx] + (cs[idx + L - 1] - cs[idx])


def report(name, stream, tbl):
    parts = [f"{name:34s} {len(stream):7d} runes"]
    for L, gate in ((36, 300), (120, 300)):
        if len(stream) < L:
            parts.append(f"L={L}: section shorter than the window")
            continue
        sc = window_scores(stream, tbl, L)
        parts.append(f"L={L}: mean {sc.mean() / L:+.2f}/rune, 5th pct {np.percentile(sc, 5):+.0f}, windows >= {gate}: {100 * (sc >= gate).mean():5.1f}%")
    if len(stream) >= 40:
        pre = window_scores(stream, tbl, 40)
        parts.append(f"first 40 runes >= +60 (abort rule): {100 * (pre >= 60).mean():5.1f}%")
    say("   ".join(parts))


def main():
    tbl = bg.load_table()
    say("boundary-free bigram score, sum of 10 ln(29 P(b|a)) per rune; a true key decodes to the plaintext, so these are the scores a correct key gets")
    say("")
    solved = []
    for i in sorted(lp.KNOWN):
        runes = lp.KNOWN[i][1](lp.runes_of(stats.SEGS[i]))
        solved.append(runes)
        report(f"solved section 0.{i}", runes, tbl)
    allsolved = [r for s in solved for r in s]
    say("")
    report("all solved sections joined", allsolved, tbl)
    say("")
    eng, _ = D.english(400_000)
    # Emerson is the first corpus in fam_data.CORPORA; the other books are held out of the table
    names = ["emerson_essays1.txt", "pg205 (Walden)", "pg2680", "pg1497", "pg1998", "pg2009"]
    per = []
    for fn in D.CORPORA:
        path = os.path.join(WORK, "ref", fn)
        if os.path.exists(path):
            per.append(fn)
    import re
    for fn in per:
        txt = open(os.path.join(WORK, "ref", fn), encoding="utf-8", errors="ignore").read()
        if "SELF-RELIANCE" in txt:
            txt = txt[txt.index("SELF-RELIANCE"):]
        txt = txt.split("*** END OF")[0]
        stream = [r for w in re.findall(r"[A-Za-z]+", txt)[:60000] for r in lp.word_to_key(w.upper().replace("IO", "IA"))]
        report(f"{fn} ({'in-sample' if fn.startswith('emerson') else 'held out'})", stream, tbl)
    dest = os.path.join(HERE, "..", "..", "results", "analysis")
    with open(os.path.join(dest, "true_key_score.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    sys.exit(main())
