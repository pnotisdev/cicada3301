"""Phase 25 section 10: Old English (Beowulf, Harrison & Sharp 1893, PG 9700) and Middle English (Chaucer, Canterbury Tales, Skeat, PG 22120) as plaintext models of LP2's word lengths.
Texts are DATA in work/ref/oldenglish/ (git-ignored); nothing from them is executed.

Mapping rules to Gematria Primus runes (written down before looking at G):
  thorn, eth        -> TH (one rune U+16A6) in the 'digraph' and 'source' variants; T + H in the 'letters' variant
  ash (ae)          -> AE (one rune) in 'digraph' and 'source'; A + E in 'letters'
  wynn / w          -> W;  yogh -> G;  oe ligature -> OE (one rune) / O + E;  c k q -> C (k, q aliases as lp.word_to_key), v -> U, z -> S, j -> J
  accents (macron, acute, circumflex, umlaut) are stripped; case ignored
  variants:  digraph = lp.word_to_key greedy (TH EO ING OE AE IA EA are single runes; IO -> IA, as the repo's English models);
             source  = only the OE letters thorn, eth, ash are single runes, everything else letter by letter (the orthography as written, no digraph runes);
             letters = every GP digraph spelled out
  hyphenated compounds: kept as one word ('joined') or split ('split')
Beowulf = the Old English verse lines only (text between 'BEOWULF.' and 'NOTES.'; caesura gaps joined, line numbers removed). Chaucer = the Canterbury Tales verse and prose lines from the General Prologue on
(lines indented two spaces).

    python work/mech25/oldenglish.py    # -> results/analysis/oldenglish.txt
"""
import os
import re
import sys
import unicodedata

import numpy as np
from scipy.stats import chi2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import lp  # noqa: E402
import stats  # noqa: E402
import wordlen as W  # noqa: E402
import wordlen25 as B  # noqa: E402

REF = os.path.join(HERE, "..", "ref", "oldenglish")
N = 29
LET = {lp.LATIN[i]: i for i in range(N) if len(lp.LATIN[i]) == 1}
ALIAS = {"V": 1, "K": 5, "Z": 15, "Q": 5}


def beowulf_lines():
    t = open(os.path.join(REF, "pg9700.txt"), encoding="utf-8").read().split("\n")
    a = next(i for i, l in enumerate(t) if l.strip() == "BEÓWULF." and i > 100)
    b = next(i for i, l in enumerate(t) if i > a and l.strip() == "NOTES.")
    out = []
    for l in t[a:b]:
        if re.match(r"^(\d+\s{2,}|\s{5})\S", l):
            out.append(re.sub(r"^\d+", "", l).strip())
    return out


def chaucer_lines():
    t = open(os.path.join(REF, "pg22120.txt"), encoding="utf-8").read().split("\n")
    a = next(i for i, l in enumerate(t) if "Whan that Aprille" in l)
    b = next((i for i, l in enumerate(t) if i > a and l.startswith("*** END")), len(t))
    out = []
    for l in t[a:b]:
        if re.match(r"^  \S", l):
            out.append(re.sub(r"\s+\d+\s*$", "", l).strip())
    return out


def tokens(lines, split):
    txt = " ".join(lines)
    txt = txt.replace("þ", "\x01").replace("Þ", "\x01").replace("ð", "\x01").replace("Ð", "\x01").replace("æ", "\x02").replace("Æ", "\x02").replace("ƿ", "w").replace("ȝ", "g")
    txt = unicodedata.normalize("NFKD", txt)
    txt = "".join(ch for ch in txt if not unicodedata.combining(ch))
    pat = r"[A-Za-z\x01\x02]+(?:-[A-Za-z\x01\x02]+)*"
    ws = re.findall(pat, txt)
    out = []
    for w in ws:
        out += w.split("-") if split else [w.replace("-", "")]
    return [w for w in out if w]


def runes(word, variant):
    w = word.upper()
    if variant == "digraph":
        return lp.word_to_key(w.replace("\x01", "TH").replace("\x02", "AE").replace("IO", "IA"))
    r = []
    i = 0
    for ch in w:
        if ch == "\x01":
            r += [lp.LATIN.index("TH")] if variant == "source" else [LET["T"], LET["H"]]
        elif ch == "\x02":
            r += [lp.LATIN.index("AE")] if variant == "source" else [LET["A"], LET["E"]]
        else:
            r.append(LET[ch] if ch in LET else ALIAS.get(ch, 0))
    return r


def main():
    segs = lp.load_segments()
    lp2 = []
    for i in stats.UNSOLVED:
        c = lp.runes_of(segs[i])
        lp2 += [b - a for _, a, b in lp.word_spans(segs[i], c)]
    obs = W.hist(lp2)
    out = []

    def say(x=""):
        print(x, flush=True)
        out.append(x)

    say("LP2 histogram (%): " + " ".join(f"{x:.1f}" for x in 100 * obs / obs.sum()) + f"   ({len(lp2)} words; half-sample noise floor of G: mean 11.3, 95th pct 33.5)")
    say("")
    say("text / variant / hyphens           words  G (df 11)  p        1-rune 2-rune % | unigram IoC x29 | digraph runes TH EO ING OE AE IA EA (% of runes)")
    texts = {"Beowulf (OE)": beowulf_lines(), "Chaucer (ME)": chaucer_lines()}
    for name, lines in texts.items():
        say(f"-- {name}: {len(lines)} lines used")
    dig = [lp.LATIN.index(d) for d in ("TH", "EO", "ING", "OE", "AE", "IA", "EA")]
    for name, lines in texts.items():
        for split in (False, True):
            ws = tokens(lines, split)
            for variant in ("digraph", "source", "letters"):
                rs = [runes(w, variant) for w in ws]
                L = np.array([len(r) for r in rs])
                h = W.hist(L)
                g = W.g_test(obs, h)[0]
                allr = np.concatenate([np.array(r) for r in rs])
                f = np.bincount(allr, minlength=N) / len(allr)
                ioc = N * float((f * f).sum())
                say(f"{name:13s} {variant:8s} {'split ' if split else 'joined'}  {len(ws):7d}  {g:8.1f}  {chi2.sf(g, 11):.1e}  {100 * h[0] / h.sum():4.1f} {100 * h[1] / h.sum():5.1f}  |  {ioc:.3f}  |  " + " ".join(f"{100 * f[d]:.2f}" for d in dig))
    # reference: Emerson, same code path
    ws = B.words_of("emerson_essays1.txt")
    for variant in ("digraph", "letters"):
        rs = [lp.word_to_key(w.upper().replace("IO", "IA")) if variant == "digraph" else [LET[ch] if ch in LET else ALIAS.get(ch, 0) for ch in w.upper()] for w in ws]
        h = W.hist(np.array([len(r) for r in rs]))
        allr = np.concatenate([np.array(r) for r in rs])
        f = np.bincount(allr, minlength=N) / len(allr)
        say(f"Emerson (en)  {variant:8s}          {len(ws):7d}  {W.g_test(obs, h)[0]:8.1f}  {chi2.sf(W.g_test(obs, h)[0], 11):.1e}  {100 * h[0] / h.sum():4.1f} {100 * h[1] / h.sum():5.1f}  |  {N * float((f * f).sum()):.3f}  |  " + " ".join(f"{100 * f[d]:.2f}" for d in dig))
    flp = np.bincount(np.concatenate([np.array(lp.runes_of(segs[i])) for i in stats.UNSOLVED]), minlength=N)
    flp = flp / flp.sum()
    say(f"LP2 (cipher)                                                                 |  {N * float((flp * flp).sum()):.3f}  |  " + " ".join(f"{100 * flp[d]:.2f}" for d in dig))
    with open(os.path.join(HERE, "..", "..", "results", "analysis", "oldenglish.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
