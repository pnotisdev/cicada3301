"""Phase 33: cited books as NUMBER streams for the library-wide kscreen screen (data/booknum.ksb + data/booknum.tsv). Phase 22 covered book LETTERS (a letter -> rune table); this
covers numbers computed from the text, a gap named in work/log/phase22_book_keys.md.

Books (data only, local copies): Liber AL (work/ref/corpora/cited/liber_al_oto.txt), Blake MHH and Songs (pg45315, pg1934), Emerson's Self-Reliance (work/ref/emerson_essays1.txt,
SELF-RELIANCE .. COMPENSATION), the Mabinogion (pg5160), Agrippa 1651 (OCR). Spellings: dg = digraph runes (TH EO ING OE AE IA EA as one rune, IO -> IA), lt = letter by letter.
Streams (all mod 29), tag = family:
  Widx   per-word sum of the GP rune indices            Wpri   per-word sum of the GP prime values
  Lpri   per-rune prime value (2, 3, 5, ... 109)        Plpri  prefix sums of Lpri          Plidx  prefix sums of the rune indices
  Pwidx  prefix sums of Widx                            Pwpri  prefix sums of Wpri
  Sidx   per-sentence sum of indices                    Spri   per-sentence sum of primes (sentence = text up to . ! ? ; :)
  Wlen   word lengths in runes                          Plen   prefix sums of the word lengths
A stream is dropped when shorter than 400 values or when LP2's flat IoC excludes it as a key (predicted IoC under English plaintext above max(1.003, 1.002 + 1.6 / n),
the rule of work/kscreen/signed.py / export_hyp.py). Streams longer than MAXLEN are cut at MAXLEN (cost); the cut is logged.

    python work/kscreen/booknum.py        # -> work/kscreen/data/booknum.ksb, booknum.tsv; prints built / kept per family
"""
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, WORK)
sys.path.insert(0, HERE)
import export  # noqa: E402
import keystreams  # noqa: E402
import lp  # noqa: E402
from book_key_flatness import gutenberg_body  # noqa: E402
import unicodedata  # noqa: E402

N = 29
OUT = os.path.join(HERE, "data")
C = os.path.join(WORK, "ref", "corpora", "cited")
MINLEN = 400
MAXLEN = 400_000
PRIME = np.array(lp.PRIME, dtype=np.int64)
LET = {lp.LATIN[i]: i for i in range(N) if len(lp.LATIN[i]) == 1}
ALIAS = {"V": 1, "K": 5, "Z": 15, "Q": 5}


def book_text(name):
    if name == "liber_al":
        return open(os.path.join(C, "liber_al_oto.txt"), encoding="utf-8", errors="ignore").read()
    if name == "emerson_selfrel":
        t = open(os.path.join(WORK, "ref", "emerson_essays1.txt"), encoding="utf-8", errors="ignore").read().split("\n")
        a = [i for i, l in enumerate(t) if l.strip() == "SELF-RELIANCE"][0]
        b = [i for i, l in enumerate(t) if l.strip() == "COMPENSATION"][0]
        return "\n".join(t[a:b])
    f = {"blake_mhh": "pg45315.txt", "blake_songs": "pg1934.txt", "mabinogion": "pg5160.txt", "agrippa": "agrippa_1651_archive_djvu.txt"}[name]
    p = os.path.join(C, f)
    return gutenberg_body(p) if f.startswith("pg") else open(p, encoding="utf-8", errors="ignore").read()


def rune_word(w, spelling):
    w = w.upper().replace("QU", "CW")
    if spelling == "dg":
        return lp.word_to_key(w.replace("IO", "IA"))
    return [LET[ch] if ch in LET else ALIAS.get(ch, 0) for ch in w]


def parse(text, spelling):
    """(list of words as rune lists, sentence id per word)"""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    words, sent, s = [], [], 0
    for tok in re.findall(r"[A-Za-z]+|[.!?;:]", text):
        if tok in ".!?;:":
            s += 1
            continue
        r = rune_word(tok, spelling)
        if r:
            words.append(r)
            sent.append(s)
    return words, np.array(sent)


def streams_of(text, spelling):
    words, sent = parse(text, spelling)
    allr = np.array([x for w in words for x in w], dtype=np.int64)
    widx = np.array([sum(w) for w in words], dtype=np.int64)
    wpri = np.array([int(PRIME[w].sum()) for w in words], dtype=np.int64)
    wlen = np.array([len(w) for w in words], dtype=np.int64)
    lpri = PRIME[allr]
    out = {"Widx": widx, "Wpri": wpri, "Lpri": lpri, "Plpri": np.cumsum(lpri), "Plidx": np.cumsum(allr),
           "Pwidx": np.cumsum(widx), "Pwpri": np.cumsum(wpri), "Wlen": wlen, "Plen": np.cumsum(wlen)}
    ids = np.unique(sent)
    for tag, v in (("Sidx", widx), ("Spri", wpri)):
        out[tag] = np.array([v[sent == s].sum() for s in ids], dtype=np.int64)
    return {k: v % N for k, v in out.items()}


def main():
    os.makedirs(OUT, exist_ok=True)
    P = keystreams.english_distribution()
    kept, stats, cut = {}, {}, []
    for book in ("liber_al", "blake_mhh", "blake_songs", "emerson_selfrel", "mabinogion", "agrippa"):
        text = book_text(book)
        for spelling in ("dg", "lt"):
            for fam, v in streams_of(text, spelling).items():
                s = stats.setdefault(fam, {"built": 0, "too short": 0, "flat-IoC excluded": 0, "kept": 0})
                s["built"] += 1
                if len(v) < MINLEN:
                    s["too short"] += 1
                    continue
                n = min(4000, len(v))
                pi = max(keystreams.predicted_ioc(v, P, 1, n=n), keystreams.predicted_ioc(v, P, -1, n=n))
                if pi > max(1.003, 1.002 + 1.6 / n):
                    s["flat-IoC excluded"] += 1
                    continue
                if len(v) > MAXLEN:
                    cut.append(f"{fam} {book} {spelling}: {len(v)} -> {MAXLEN}")
                    v = v[:MAXLEN]
                kept[f"{fam} {book} {spelling}"] = v
                s["kept"] += 1
    rows = export.write_ksb(os.path.join(OUT, "booknum.ksb"), kept, os.path.join(OUT, "booknum.tsv"))
    for fam, s in sorted(stats.items()):
        print(fam, s)
    print("cut:", "; ".join(cut) if cut else "none")
    pairs = sum(max(0, n - 382) for _, n, _, _ in rows)
    print(f"booknum.ksb: {len(rows)} streams, {pairs} (stream, offset) pairs for a 300-rune window")
    print("\n".join(f"{n}\t{ln}\tperiod {p}\tpred {pi:.4f}" for n, ln, p, pi in rows))


if __name__ == "__main__":
    main()
