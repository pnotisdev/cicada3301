"""Cheap checks of assumptions under many of our negatives (project review, 2026-10-18).

 1. LANGUAGE. The boundary-free seed / OEIS / KDF / hashscan lanes score by an ENGLISH rune-bigram table (bg.py). If LP2's plaintext were not English, how many windows would a true key still pass? Same score as true_key_score.py on Latin, German, French,
    Spanish and Italian (Project Gutenberg texts of work/ref/corpora, letters spelled in runes as for English), for the lane windows (120 runes with the +300 gate and the 40-rune abort at +60; 60 and 48 runes for the OEIS sets).
 2. IoC RULE. kscreen calls a window a hit at IoC >= 1.40 on 300 runes. IoC of the PLAINTEXT of every 300-rune and 100-rune window of the solved Liber Primus sections (a correct key decodes to this) and of the English books.
 3. LITERAL F. In the solved sections plaintext F is written as F. A literal F in LP2 would raise the share of ciphertext F above 1/29: the count of rune 0 in LP2 against its binomial expectation.

    python work/families/assumption_checks.py          # -> results/analysis/assumption_checks.txt
"""
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, WORK)
sys.path.insert(0, os.path.join(WORK, "phpmt"))
import lp  # noqa: E402
import stats  # noqa: E402
import bg  # noqa: E402
import wordlen_languages as wl  # noqa: E402
from true_key_score import window_scores  # noqa: E402

OUT = []


def say(s=""):
    print(s)
    OUT.append(s)


def runes_of_words(words, limit=250_000):
    out = []
    for w in words:
        w = re.sub(r"[^A-Za-z]", "", w).upper().replace("IO", "IA")
        r = lp.word_to_key(w) if w else None
        if r:
            out += r
        if len(out) >= limit:
            break
    return out


def ioc(c):
    n = len(c)
    h = np.bincount(c, minlength=29)
    return float((h * (h - 1)).sum() / (n * (n - 1) / 29))


def window_iocs(stream, L, stride):
    s = np.asarray(stream)
    return np.array([ioc(s[i:i + L]) for i in range(0, len(s) - L + 1, stride)])


def main():
    tbl = bg.load_table()
    say("1. TRUE-KEY SCORE OF THE BOUNDARY-FREE LANES BY PLAINTEXT LANGUAGE (English table; a correct key decodes to the plaintext)")
    say(f"{'text':36s} {'per rune':>9s} {'120 runes >= +300':>18s} {'60 >= +300':>11s} {'48 >= +300':>11s} {'first 40 >= +60':>16s}")
    rows = [("Cicada's solved sections", [r for i in sorted(lp.KNOWN) for r in lp.KNOWN[i][1](lp.runes_of(stats.SEGS[i]))])]
    for name in ("English (Emerson, Essays I)", "English (Thoreau, Walden)", "Latin (Caesar, De bello Gallico)", "Latin (Vergil, Aeneid)", "German (Goethe, Faust I)", "French (Hugo, Les Miserables I)",
                 "Spanish (Cervantes, Don Quijote)", "Italian (Dante, Commedia)"):
        try:
            rows.append((name, runes_of_words(wl.words_of(name))))
        except Exception as e:  # noqa: BLE001
            say(f"{name:36s} not available ({type(e).__name__})")
    for name, st in rows:
        a = {L: window_scores(st, tbl, L) for L in (120, 60, 48, 40)}
        say(f"{name:36s} {a[120].mean() / 120:+9.2f} {100 * (a[120] >= 300).mean():17.1f}% {100 * (a[60] >= 300).mean():10.1f}% {100 * (a[48] >= 300).mean():10.1f}% {100 * (a[40] >= 60).mean():15.1f}%")
    say("")
    say("2. IoC OF THE PLAINTEXT, 300-rune and 100-rune windows (the kscreen rule is IoC >= 1.40; planted keys decode to English at about 1.6-2.06)")
    solved = rows[0][1]
    for name, st in (("Cicada's solved sections (stride 50)", solved), ("English, Emerson", rows[1][1][:60000]), ("Latin, Caesar", None)):
        if st is None:
            continue
        for L in (300, 100):
            v = window_iocs(st, L, 50 if L == 300 else 25)
            say(f"{name:38s} L={L}: windows {len(v):5d}, mean {v.mean():.3f}, min {v.min():.3f}, 5th pct {np.percentile(v, 5):.3f}, share >= 1.40: {100 * (v >= 1.40).mean():5.1f}%")
    say("")
    runes, start, sid = (lambda: __import__("fam_data").lp2())()
    n, f = len(runes), int((runes == 0).sum())
    p = 1 / 29
    z = (f - n * p) / np.sqrt(n * p * (1 - p))
    cnt = np.bincount(runes, minlength=29)
    say(f"3. LITERAL F: LP2 has {f} ciphertext F of {n} runes (expected {n * p:.0f} +- {np.sqrt(n * p * (1 - p)):.0f}, z {z:+.2f}); a literal plaintext F (about 2% of English runes) would add about {0.02 * n:.0f}. Rank of F among the 29 rune counts: {int((cnt > f).sum()) + 1}.")
    dest = os.path.join(HERE, "..", "..", "results", "analysis")
    with open(os.path.join(dest, "assumption_checks.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    main()
