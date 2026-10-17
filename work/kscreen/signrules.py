"""Word-level key-sign rules for the kscreen engine: 'their numbers are the direction' (2016) read as c_i = p_i + s_w * k_j, the sign s_w of the key for every rune of word w decided by a number of the transcription.

An outside LLM enumerated 112 rules over ten word quantities (docs/prs, work/log/phase10_signrules.md). Two changes here, both argued in the log:
 * the two 'orientations' of a rule are one rule: a global sign flip is the multiplier 28 that every screen already tries (mults=1,28);
 * a rule must be computable by the ENCRYPTOR before it enciphers the word, so it may use the current word's length and positions (n, w index in the section, wp index in the page, ws index in the clause) and ANY quantity of the
   PREVIOUS words' ciphertext, but not the current word's own ciphertext numbers (G, R, first / last rune), which would depend on the sign being chosen. (The plaintext word's numbers are not computable by a solver.)
Quantities of a word: n length, G Gematria Primus prime sum of its ciphertext runes, R sum of their rune indices, f / l index of the first / last rune, pf / pl their GP primes (tags kept distinct: file names are case-insensitive).
Templates: A parity; B half split of q mod p (p = 3, 5, 7; 29 for G and R of the previous word); C q_w > q_(w-1) (strict); D last > first (index f, l) or last prime > first prime of the previous word; E length threshold n >= t (3, 4, 5).
The first word(s) without the needed predecessor get +1. Rules whose sign vector is constant or equals another rule's (or its negation) on all eight section windows are dropped.

    python work/kscreen/signrules.py          # -> data/signs/<rule>.txt (windows with S lines) and data/signs/rules.tsv
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, WORK)
import lp  # noqa: E402
import keystreams  # noqa: E402
import stats  # noqa: E402

OUT = os.path.join(HERE, "data", "signs")
N = 29


def numbers(r):
    """the ciphertext numbers of a word given its runes"""
    return dict(G=sum(lp.PRIME[x] for x in r), R=sum(r), f=r[0], l=r[-1], pf=lp.PRIME[r[0]], pl=lp.PRIME[r[-1]])


def word_table(runes, spans, page_of=None, clause_of=None):
    """words of a window as dicts: n, w (1-based index in the window's section), wp, ws and the ciphertext numbers G R f l F L"""
    words, pg, cl, wp, ws = [], None, None, 0, 0
    for k, (a, b) in enumerate(spans):
        r = runes[a:b]
        p = page_of[a] if page_of else 0
        c = clause_of[a] if clause_of else 0
        wp = wp + 1 if p == pg else 1
        ws = ws + 1 if c == cl else 1
        pg, cl = p, c
        words.append(dict(n=len(r), w=k + 1, wp=wp, ws=ws, **numbers(r)))
    return words


def build_rules():
    """name -> fn(words, w) -> +1 / -1, using words[w]['n', 'w', 'wp', 'ws'] and the ciphertext numbers of words[w-1], words[w-2] only"""
    rules = {}
    cur = ("n", "w", "wp", "ws")
    prev = ("n", "G", "R", "f", "l", "pf", "pl")

    def q_cur(q):
        return lambda ws, w: ws[w][q]

    def q_prev(q, back=1):
        return lambda ws, w: ws[w - back][q] if w - back >= 0 else None

    sources = {f"cur_{q}": q_cur(q) for q in cur}
    sources.update({f"prev_{q}": q_prev(q) for q in prev})
    for name, src in sources.items():
        rules[f"A_{name}"] = (lambda src: lambda ws, w: (1 if src(ws, w) % 2 == 0 else -1) if src(ws, w) is not None else 1)(src)
        for p in (3, 5, 7):
            rules[f"B{p}_{name}"] = (lambda src, p: lambda ws, w: (1 if src(ws, w) % p <= (p - 1) // 2 else -1) if src(ws, w) is not None else 1)(src, p)
    for q in ("G", "R"):
        rules[f"B29_prev_{q}"] = (lambda q: lambda ws, w: (1 if ws[w - 1][q] % 29 <= 14 else -1) if w >= 1 else 1)(q)
    for q in ("n", "wp", "ws"):
        rules[f"C_cur_{q}"] = (lambda q: lambda ws, w: (1 if ws[w][q] > ws[w - 1][q] else -1) if w >= 1 else 1)(q)
    for q in prev:
        rules[f"C_prev_{q}"] = (lambda q: lambda ws, w: (1 if ws[w - 1][q] > ws[w - 2][q] else -1) if w >= 2 else 1)(q)
    rules["D_prev_fl"] = lambda ws, w: (1 if ws[w - 1]["l"] > ws[w - 1]["f"] else -1) if w >= 1 else 1
    rules["D_prev_pfpl"] = lambda ws, w: (1 if ws[w - 1]["pl"] > ws[w - 1]["pf"] else -1) if w >= 1 else 1
    for t in (3, 4, 5):
        rules[f"E_cur_n{t}"] = (lambda t: lambda ws, w: 1 if ws[w]["n"] >= t else -1)(t)
        rules[f"E_prev_n{t}"] = (lambda t: lambda ws, w: (1 if ws[w - 1]["n"] >= t else -1) if w >= 1 else 1)(t)
    return rules


def section_tables():
    """(name, runes, spans, words) for the 8 windows of data/segments.txt; page and clause indices from the transcription tokens"""
    lines = open(os.path.join(HERE, "data", "segments.txt"), encoding="utf-8").read().splitlines()
    wins = []
    for k in range(0, len(lines), 3):
        wins.append((lines[k], [int(x) for x in lines[k + 1][2:].split()], lines[k + 2]))
    out = []
    for head, runes, lens in wins:
        seg = int(head.split()[1].split(".")[1])
        toks = stats.SEGS[seg]
        r = lp.runes_of(toks)
        assert r == runes, f"{head}: window runes differ from the transcription"
        spans = [(a, b) for _, a, b in lp.word_spans(toks, r)]
        page_of, clause_of, pg, cl, i = [], [], 0, 0, 0
        for t in toks:
            if isinstance(t, int):
                page_of.append(pg)
                clause_of.append(cl)
            elif t == "%":
                pg += 1
            elif t == ".":
                cl += 1
        out.append((head, runes, lens, spans, word_table(runes, spans, page_of, clause_of)))
    return out


def sign_vector(rule, words, spans, n):
    s = []
    for w, (a, b) in enumerate(spans):
        s += [rule(words, w)] * (b - a)
    return s[:n] + [1] * max(0, n - len(s))


def flat_library():
    """data/library_flat.ksb: the library streams that LP2's flat IoC does not already exclude as keys (predicted IoC under English <= 1.003). With signs the effective key is s * k, which stays non-flat
    unless k is symmetric and the signs are random-like, so the exclusion is kept for the sign screens (the others are about 60% of the cost)."""
    sys.path.insert(0, os.path.join(WORK, "layer2"))
    from export import read_ksb
    import struct
    import numpy as np
    flat = set()
    with open(os.path.join(HERE, "data", "library.tsv"), encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if p[4] == "0":
                flat.add(p[0])
    ks = {name: np.frombuffer(bytes(v), dtype=np.uint8).astype(np.int64) for name, v in read_ksb(os.path.join(HERE, "data", "library.ksb")) if name in flat}
    with open(os.path.join(HERE, "data", "library_flat.ksb"), "wb") as f:                      # the KSB1 format of kscreen/export.py::write_ksb (streams already truncated there)
        f.write(b"KSB1" + struct.pack("<I", len(ks)))
        for name, v in ks.items():
            nb = name.encode("utf-8")[:300]
            f.write(struct.pack("<H", len(nb)) + nb + struct.pack("<I", len(v)) + bytes(v.astype(np.uint8)))
    print(f"library_flat.ksb: {len(ks)} streams")
    # the excluded streams that WOULD be flat under a sign mask flipping a share f of the runes independent of the key (marginal (1 - f) h(v) + f h(-v), f = 0.25, 0.5, 0.75; audit of 2026-10-18): screened separately
    P = keystreams.english_distribution()
    extra = {}
    for name, v in read_ksb(os.path.join(HERE, "data", "library.ksb")):
        if name in flat:
            continue
        v = np.frombuffer(bytes(v), dtype=np.uint8).astype(np.int64)
        h = np.bincount(v[:4000] % N, minlength=N) / min(4000, len(v))
        for fr in (0.25, 0.5, 0.75):
            hm = (1 - fr) * h + fr * h[(-np.arange(N)) % N]
            q = sum(hm[k] * np.roll(P, k) for k in range(N))
            if N * (q ** 2).sum() <= 1.003:
                extra[name] = v
    with open(os.path.join(HERE, "data", "library_signed_extra.ksb"), "wb") as f:
        f.write(b"KSB1" + struct.pack("<I", len(extra)))
        for name, v in extra.items():
            nb = name.encode("utf-8")[:300]
            f.write(struct.pack("<H", len(nb)) + nb + struct.pack("<I", len(v)) + bytes(v.astype(np.uint8)))
    print(f"library_signed_extra.ksb: {len(extra)} streams")


def main():
    os.makedirs(OUT, exist_ok=True)
    tabs = section_tables()
    rules = build_rules()
    kept, seen, rows = {}, {}, []
    for name, fn in rules.items():
        vec = tuple(x for (_, runes, _, spans, words) in tabs for x in sign_vector(fn, words, spans, len(runes)))
        neg = tuple(-x for x in vec)
        if len(set(vec)) == 1:
            rows.append((name, "dropped: constant", 0))
            continue
        if vec in seen or neg in seen:
            rows.append((name, f"dropped: same as {seen.get(vec) or seen.get(neg)}", 0))
            continue
        seen[vec] = name
        kept[name] = fn
        rows.append((name, "kept", sum(1 for x in vec if x < 0)))
    for name, fn in kept.items():
        with open(os.path.join(OUT, name + ".txt"), "w", newline="\n", encoding="utf-8") as f:
            for head, runes, lens, spans, words in tabs:
                f.write(f"{head}\nR {' '.join(map(str, runes))}\n{lens}\nS {' '.join(map(str, sign_vector(fn, words, spans, len(runes))))}\n")
    with open(os.path.join(OUT, "rules.tsv"), "w", newline="\n", encoding="utf-8") as f:
        f.write("rule\tstatus\tnegative_runes\n" + "\n".join(f"{n}\t{s}\t{k}" for n, s, k in rows) + "\n")
    with open(os.path.join(HERE, "sign_rules.txt"), "w", newline="\n", encoding="utf-8") as f:       # tracked: the runner reads the rule names at import time
        f.write("\n".join(kept) + "\n")
    flat_library()
    print(f"{len(rules)} rules built, {len(kept)} kept ({len(rules) - len(kept)} dropped as constant or duplicate)")
    for n, s, k in rows:
        if s != "kept":
            print("   ", n, s)
    return kept


if __name__ == "__main__":
    main()
