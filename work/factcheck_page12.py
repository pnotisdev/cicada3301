#!/usr/bin/env python3
"""Fact check of a Reddit claim: 'Liber Primus page 12 is officially 100% solved' (r/Cipher, October 2026).

The claim, as the user pasted it on 2026-10-18 (Reddit was not reachable from this machine, so no comments were read): page 12
decrypts to
    TWENTY FOUR PAGES WERE WRITTEN FOR YOU TO FIND THE SECRET PATH TO THE END
by 'layering the standard Dynamic Multiplier 7 Mod-29 framework, injecting a post-multiplier SUMUS key subtractor array, and
pushing the coordinates through the 5x6 Vowel-First Polybius fractionation square (Bifid Style)', with 'zero leftover character
drift'. The post publishes no code, no square, no key values and no intermediate numbers, so every concrete reading below is
ours; the grid in section D covers every reading we could define. The claim is data: nothing of the author's was run.

    python work/factcheck_page12.py [--null 200] [--plants 24] [--page-null 20] [--jobs 14]
        -> results/analysis/factcheck_page12_2026-10-18.txt

A  which page 'page 12' is under the four numbering conventions, and the post's two other 'blueprints' (pages 56 and 28)
B  length and word pattern of the claimed sentence against the page
C  the 5x6 Bifid as a map: not a bijection; where the claimed sentence could come out of it at all
D  the claimed pipeline in every reading on page 12 and on every unsolved page, with planted and null controls
E  the fingerprint the pipeline would leave on a ciphertext (doublets, IoC) against page 12 and LP2
Write-up: work/log/factcheck_page12_2026-10-18.md.
"""
import argparse
import ipaddress
import os
import re
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import lp  # noqa: E402

OUT = os.path.join(REPO, "results", "analysis", "factcheck_page12_2026-10-18.txt")
N = lp.N
INV = N                         # rune outputs: an invalid coordinate or an empty cell
ABC = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LINV = 26                       # letter outputs: the same
CLAIM = "TWENTY FOUR PAGES WERE WRITTEN FOR YOU TO FIND THE SECRET PATH TO THE END"
CLAIM_WORDS = CLAIM.split()
CLAIM_RUNES = np.array([r for w in CLAIM_WORDS for r in lp.word_to_key(w)])
CLAIM_LETTERS = np.array([ABC.index(ch) for ch in CLAIM.replace(" ", "")])
SEGS = lp.load_segments()
UNSOLVED = range(7, 16)
LINES = []


def say(s=""):
    print(s, flush=True)
    LINES.append(s)


# ------------------------------------------------------------------ pages and numbering

def image_of(tp):
    """transcription page -> original image number (as work/ocr.py image_of; kept here so the script needs no OpenCV)"""
    return 1 if tp == 0 else tp + 2


def tp_of_image(img):
    return {1: 0}.get(img, img - 2 if img >= 3 else None)


def pdf_page(img):
    """LiberPrimus.pdf order: 00 title, 02 'Intus', 01 A Warning, then 03.. (PLAN.md, header)"""
    return {0: 1, 2: 2, 1: 3}.get(img, img + 1)


def image_of_pdf(pdf):
    return {1: 0, 2: 2, 3: 1}.get(pdf, pdf - 1)


def page_runes():
    """transcription page -> [(segment, rune position in the segment)] for each of its runes"""
    body = open(lp.MASTER, encoding="utf-8").read().split("\n\n", 1)[1].split("§")[0]
    out, cur, seg, pos = [], [], 0, 0
    for ch in body:
        if ch == "%":
            out.append(cur)
            cur = []
        elif ch == "$":
            seg, pos = seg + 1, 0
        elif ch in lp.RUNE_IDX:
            cur.append((seg, pos))
            assert lp.runes_of(SEGS[seg])[pos] == lp.RUNE_IDX[ch]
            pos += 1
    out.append(cur)
    return out


PAGES = page_runes()


def page_span(tp):
    """(segment, first rune, end) of a page that lies in one segment"""
    segs = {s for s, _ in PAGES[tp]}
    assert len(segs) == 1, (tp, segs)
    s = segs.pop()
    return s, PAGES[tp][0][1], PAGES[tp][-1][1] + 1


def words_in(seg, lo, hi, plain):
    """Latin words of segment seg whose runes overlap [lo, hi) (lp.word_spans: a bare line or page break is a wrap)"""
    return [w for w, a, b in lp.word_spans(SEGS[seg], plain) if b > lo and a < hi]


def letters(runes):
    return "".join(lp.LATIN[r] for r in runes)


# ------------------------------------------------------------------ squares, Bifid, the two key stages

RUNE_VOW6 = [24, 18, 10, 3, 1, 26]          # A E I O U Y
RUNE_VOWDI = [25, 28, 12, 27, 22]           # AE EA EO IA OE
RUNE_VOW_GP = sorted(RUNE_VOW6 + RUNE_VOWDI)


def complete(first, size):
    return list(first) + [s for s in range(size) if s not in first]


class Square:
    """R x C Polybius square; cells past the alphabet are empty (value = alphabet size)."""

    def __init__(self, name, order, size, R, C, bycol=False):
        self.name, self.R, self.C, self.size = name, R, C, size
        self.cell = np.full((R, C), size, np.int64)
        self.rr = np.full(size, -1, np.int64)
        self.cc = np.full(size, -1, np.int64)
        for k, s in enumerate(order):
            r, c = (k % R, k // R) if bycol else (k // C, k % C)
            self.cell[r, c], self.rr[s], self.cc[s] = s, r, c
        assert (self.rr >= 0).all()


def make_squares():
    rune = [("R1 AEIOUY + AE EA EO IA OE + consonants (GP order)", complete(RUNE_VOW6 + RUNE_VOWDI, N), False),
            ("R2 the 11 vowel runes in GP order + consonants", complete(RUNE_VOW_GP, N), False),
            ("R3 AEIOU + the rest in GP order", complete(RUNE_VOW6[:5], N), False),
            ("R1 filled by columns", complete(RUNE_VOW6 + RUNE_VOWDI, N), True)]
    lat = [("L1 AEIOUY + consonants", "AEIOUY" + "BCDFGHJKLMNPQRSTVWXZ", False),
           ("L2 AEIOU + the rest", "AEIOU" + "BCDFGHJKLMNPQRSTVWXYZ", False),
           ("L1 filled by columns", "AEIOUY" + "BCDFGHJKLMNPQRSTVWXZ", True),
           ("L2 filled by columns", "AEIOU" + "BCDFGHJKLMNPQRSTVWXYZ", True)]
    rs, ls = [], []
    for R, C in ((5, 6), (6, 5)):
        rs += [Square(f"{nm}, {R}x{C}", o, N, R, C, bc) for nm, o, bc in rune]
        ls += [Square(f"{nm}, {R}x{C}", [ABC.index(ch) for ch in o], 26, R, C, bc) for nm, o, bc in lat]
    return rs, ls


RSQ, LSQ = make_squares()
PERIODS = [0] + list(range(2, 13))           # 0 = the whole text is one block (classic Bifid without a period)
_IDX = {}


def bifid_index(n, p):
    """Bifid decryption reads the interleaved coordinate stream S = r0 c0 r1 c1 ...; block [s, s+b) takes its plaintext rows
    from S[2s : 2s+b] and its columns from S[2s+b : 2s+2b]. Returns those source indices (IR, IC)."""
    if (n, p) not in _IDX:
        IR, IC = np.empty(n, np.int64), np.empty(n, np.int64)
        L = n if p == 0 else p
        for s in range(0, n, L):
            b = min(L, n - s)
            t = np.arange(b)
            IR[s:s + b], IC[s:s + b] = 2 * s + t, 2 * s + b + t
        _IDX[(n, p)] = (IR, IC)
    return _IDX[(n, p)]


def bifid_decrypt(X, sq, p, wrap):
    """X (B, n) symbols -> (B, n) plaintext; strict: a row index >= R, a column index >= C or an empty cell gives sq.size;
    wrap: indices are reduced mod R / mod C (an empty cell still gives sq.size)"""
    B, n = X.shape
    IR, IC = bifid_index(n, p)
    S = np.empty((B, 2 * n), np.int64)
    S[:, 0::2], S[:, 1::2] = sq.rr[X], sq.cc[X]
    pr, pc = S[:, IR], S[:, IC]
    if wrap:
        return sq.cell[pr % sq.R, pc % sq.C]
    ok = (pr < sq.R) & (pc < sq.C)
    return np.where(ok, sq.cell[np.minimum(pr, sq.R - 1), np.minimum(pc, sq.C - 1)], sq.size)


def bifid_encrypt(P, sq, p):
    """inverse of bifid_decrypt: P (n,) -> (cipher (n,) with sq.size where a pair is not a cell, S, source map)"""
    n = len(P)
    IR, IC = bifid_index(n, p)
    S = np.empty(2 * n, np.int64)
    S[IR], S[IC] = sq.rr[P], sq.cc[P]
    a, b = S[0::2], S[1::2]
    ok = (a < sq.R) & (b < sq.C)
    return np.where(ok, sq.cell[np.minimum(a, sq.R - 1), np.minimum(b, sq.C - 1)], sq.size), S


def make_reachable(P, sq, p, rng, protect=()):
    """Change plaintext symbols until the 5x6 Bifid can encrypt the text (every cipher pair a filled cell). Returns the new
    plaintext and the changed positions. Positions in `protect` are changed only when nothing else can be."""
    P = P.copy()
    n = len(P)
    IR, IC = bifid_index(n, p)
    src = np.empty(2 * n, np.int64)
    src[IR], src[IC] = np.arange(n), np.arange(n)
    protect, changed = set(protect), set()
    for _ in range(100 * n):
        cip, S = bifid_encrypt(P, sq, p)
        bad = np.flatnonzero(cip == sq.size)
        if not len(bad):
            return P, changed
        j = int(bad[0])
        ent = [e for e in (2 * j, 2 * j + 1) if S[e] >= (sq.R if e % 2 == 0 else sq.C)] or [2 * j, 2 * j + 1]
        free = [e for e in ent if int(src[e]) not in protect] or ent
        q = int(src[free[rng.integers(len(free))]])
        P[q] = rng.integers(sq.size)
        changed.add(q)
    raise RuntimeError("no reachable plaintext")


MULTS = ["none", "*7", "*25 (= /7)", "*7^(i+1)", "*25^(i+1)", "*7(i+1)", "*(7+i)", "-7i", "+7i"]
INVERTIBLE_MULTS = ["none", "*7", "*25 (= /7)", "*7^(i+1)", "*25^(i+1)", "-7i", "+7i"]
KEYS = [("no key", None, None),
        ("SUMUS runes, subtract", [15, 1, 19, 1, 15], "sub"), ("SUMUS runes, add", [15, 1, 19, 1, 15], "add"),
        ("SUMUS runes, Beaufort", [15, 1, 19, 1, 15], "beau"),
        ("SUMUS primes mod 29, subtract", [24, 3, 13, 3, 24], "sub"), ("SUMUS primes mod 29, add", [24, 3, 13, 3, 24], "add"),
        ("SUMUS A=0, subtract", [18, 20, 12, 20, 18], "sub"), ("SUMUS A=0, add", [18, 20, 12, 20, 18], "add")]
POW7 = np.array([pow(7, k, N) for k in range(1, 5000)])
POW25 = np.array([pow(25, k, N) for k in range(1, 5000)])


def mult_vec(mode, i):
    return {"*7": np.full(len(i), 7), "*25 (= /7)": np.full(len(i), 25), "*7^(i+1)": POW7[i], "*25^(i+1)": POW25[i],
            "*7(i+1)": 7 * (i + 1) % N, "*(7+i)": (7 + i) % N}[mode]


def apply_mult(mode, X, i):
    if mode == "none":
        return X
    if mode == "-7i":
        Y = (X - 7 * i) % N
    elif mode == "+7i":
        Y = (X + 7 * i) % N
    else:
        Y = X * mult_vec(mode, i) % N
    return np.where(X == INV, INV, Y)


def apply_key(spec, X, i):
    _, key, op = spec
    if key is None:
        return X
    k = np.array(key)[i % 5]
    Y = (X - k) % N if op == "sub" else (X + k) % N if op == "add" else (k - X) % N
    return np.where(X == INV, INV, Y)


def invert_mult(mode, Y, i):
    if mode == "none":
        return Y
    if mode == "-7i":
        return (Y + 7 * i) % N
    if mode == "+7i":
        return (Y - 7 * i) % N
    m = mult_vec(mode, i)
    assert (m % N).all()
    return Y * np.array([pow(int(x), -1, N) for x in m]) % N


def invert_key(spec, Y, i):
    _, key, op = spec
    if key is None:
        return Y
    k = np.array(key)[i % 5]
    return (Y + k) % N if op == "sub" else (Y - k) % N if op == "add" else (k - Y) % N


# ------------------------------------------------------------------ scoring

def rune_table():
    """the project's English rune-bigram table (work/phpmt/data/bigram.txt: round(10 ln(29 P(b|a))), Emerson's Self-Reliance)"""
    t = np.loadtxt(os.path.join(HERE, "phpmt", "data", "bigram.txt"), dtype=np.int64)[:N]
    T = np.full((N + 1, N + 1), -40, np.int64)
    T[:N, :N] = t
    return T


def letter_table():
    """the same construction on letters (A-Z, word boundaries ignored, same Emerson slice as work/phpmt/bg.py make_table)"""
    txt = open(os.path.join(HERE, "ref", "emerson_essays1.txt"), encoding="utf-8").read()
    txt = txt[txt.index("SELF-RELIANCE"):].split("*** END OF")[0]
    s = np.array([ABC.index(ch) for ch in re.sub("[^A-Z]", "", txt.upper())])
    c = np.full((26, 26), 0.5)
    np.add.at(c, (s[:-1], s[1:]), 1)
    t = np.clip(np.round(10 * np.log(26 * c / c.sum(1, keepdims=True))), -40, 40).astype(np.int64)
    T = np.full((27, 27), -40, np.int64)
    T[:26, :26] = t
    return T


TR, TL = rune_table(), letter_table()
LAT_IDX = [np.array([ABC.index(ch) for ch in lp.LATIN[r]], np.int64) for r in range(N)]


def score(O, T):
    """mean bigram score per adjacent pair (10 x ln-odds against uniform; English about +7, random about -10)"""
    return T[O[:, :-1], O[:, 1:]].mean(1)


def align(O, tgt):
    """the most positions any placement of tgt shares with each row of O"""
    B, n = O.shape
    W = n - len(tgt) + 1
    if W < 1:
        return np.zeros(B, np.int64)
    acc = np.zeros((B, W), np.int64)
    for u, t in enumerate(tgt):
        acc += O[:, u:u + W] == t
    return acc.max(1)


def translit(row):
    return np.concatenate([LAT_IDX[r] for r in row])


# ------------------------------------------------------------------ the grid of readings

def combos(offsets):
    return [(o, m, k) for o in offsets for m in MULTS for k in KEYS]


def run_grid(c, offsets):
    """Every reading of the claimed pipeline on one text c (rune indices). Paths:
         rune  MKB  runes: multiplier, then the SUMUS stage, then a rune 5x6 Bifid (the order the post gives)
         rune  BMK  runes: the Bifid first, then the multiplier and the SUMUS stage
         latin MKB  multiplier and SUMUS stage on runes (mod 29), runes written as letters, then a letter 5x6 Bifid
       Returns per path the best scores and alignments with their readings and outputs."""
    c = np.asarray(c, np.int64)
    n = len(c)
    cb = combos(offsets)
    ar = np.arange(n)
    Y = np.stack([apply_key(k, apply_mult(m, c, o + ar), o + ar) for o, m, k in cb])
    res = {"rune": [], "latin": []}
    stats = {"rune": [-1e9, None, None, -1, None, None], "latin": [-1e9, None, None, -1, None, None], "count": 0}

    def note(path, O, sc, al, label):
        st = stats[path]
        b = int(np.argmax(sc))
        if sc[b] > st[0]:
            st[0], st[1], st[2] = float(sc[b]), label(b), O[b].copy()
        a = int(np.argmax(al))
        if al[a] > st[3]:
            st[3], st[4], st[5] = int(al[a]), label(a), O[a].copy()
        stats["count"] += len(sc)
        res[path].append(sc)

    for sq in RSQ:
        for p in PERIODS:
            for wrap in (False, True):
                hand = "wrap" if wrap else "strict"
                O = bifid_decrypt(Y, sq, p, wrap)
                note("rune", O, score(O, TR), align(O, CLAIM_RUNES),
                     lambda b, sq=sq, p=p, hand=hand: ("rune MKB",) + cb[b][:2] + (cb[b][2][0], sq.name, p, hand))
                Bc = bifid_decrypt(c[None, :], sq, p, wrap)[0]
                O = np.stack([apply_key(k, apply_mult(m, Bc, o + ar), o + ar) for o, m, k in cb])
                note("rune", O, score(O, TR), align(O, CLAIM_RUNES),
                     lambda b, sq=sq, p=p, hand=hand: ("rune BMK",) + cb[b][:2] + (cb[b][2][0], sq.name, p, hand))
    lat = [translit(row) for row in Y]
    groups = {}
    for b, row in enumerate(lat):
        groups.setdefault(len(row), []).append(b)
    for sq in LSQ:
        for p in PERIODS:
            for wrap in (False, True):
                hand = "wrap" if wrap else "strict"
                for L, members in groups.items():
                    X = np.stack([lat[b] for b in members])
                    O = bifid_decrypt(X, sq, p, wrap)
                    note("latin", O, score(O, TL), align(O, CLAIM_LETTERS),
                         lambda j, members=members, sq=sq, p=p, hand=hand:
                         ("latin MKB",) + cb[members[j]][:2] + (cb[members[j]][2][0], sq.name, p, hand))
    return {"rune": stats["rune"], "latin": stats["latin"], "count": stats["count"],
            "rune_all": np.concatenate(res["rune"]), "latin_all": np.concatenate(res["latin"])}


def summary(r):
    """the numbers a null or a page contributes (no outputs)"""
    return (r["rune"][0], r["rune"][3], r["latin"][0], r["latin"][3], r["count"])


# ------------------------------------------------------------------ plaintext for the controls (Cicada's own solved text)

def cicada_plain():
    out = []
    for s in sorted(lp.KNOWN):
        out += lp.KNOWN[s][1](lp.runes_of(SEGS[s]))
    return np.array(out, np.int64)


PLAIN = cicada_plain()
PLAIN_LETTERS = translit(PLAIN)


def plant(seed, n, offsets, splice=True):
    """One planted page: a window of Cicada's solved text (with the claimed sentence spliced in at a random place unless
    splice=False), made reachable for a random reading (strict 5x6 Bifid, invertible multiplier), then encrypted by the
    inverse of that reading."""
    rng = np.random.default_rng(seed)
    order = ["MKB", "BMK"][rng.integers(2)]
    o = offsets[rng.integers(len(offsets))]
    m = INVERTIBLE_MULTS[rng.integers(len(INVERTIBLE_MULTS))]
    k = KEYS[rng.integers(len(KEYS))]
    sq = RSQ[rng.integers(len(RSQ))]
    p = PERIODS[rng.integers(len(PERIODS))]
    i = o + np.arange(n)
    s0 = rng.integers(len(PLAIN) - n)
    P = PLAIN[s0:s0 + n].copy()
    at = int(rng.integers(n - len(CLAIM_RUNES)))
    if splice:
        P[at:at + len(CLAIM_RUNES)] = CLAIM_RUNES
    protect = range(at, at + len(CLAIM_RUNES)) if splice else ()
    if order == "MKB":                       # plain = Bifid(K(M(c)))
        P, changed = make_reachable(P, sq, p, rng, protect)
        y2, _ = bifid_encrypt(P, sq, p)
        c = invert_mult(m, invert_key(k, y2, i), i)
    else:                                    # plain = K(M(Bifid(c)))
        b = invert_mult(m, invert_key(k, P, i), i)
        b2, changed = make_reachable(b, sq, p, rng, [q for q in protect])
        P = apply_key(k, apply_mult(m, b2, i), i)
        c, _ = bifid_encrypt(b2, sq, p)
    assert (c < N).all()
    label = (f"rune {order}", o, m, k[0], sq.name, p, "strict")
    return c, P, label, sorted(changed), at


def plant_latin(seed, n):
    """Letter-path control: a window of Cicada's solved text in letters, a random letter square and period. The rune -> letter
    step has no inverse (no rune is written K, Q, V or Z), so this plant tests the letter Bifid and the letter score only."""
    rng = np.random.default_rng(seed)
    sq = LSQ[rng.integers(len(LSQ))]
    p = PERIODS[rng.integers(len(PERIODS))]
    s0 = rng.integers(len(PLAIN_LETTERS) - n)
    P, changed = make_reachable(PLAIN_LETTERS[s0:s0 + n], sq, p, rng)
    c, _ = bifid_encrypt(P, sq, p)
    return c, P, (sq.name, p), changed


def latin_only_grid(c):
    best = (-1e9, None, None)
    for sq in LSQ:
        for p in PERIODS:
            for wrap in (False, True):
                O = bifid_decrypt(c[None, :], sq, p, wrap)
                s = float(score(O, TL)[0])
                if s > best[0]:
                    best = (s, (sq.name, p, "wrap" if wrap else "strict"), O[0])
    return best


# ------------------------------------------------------------------ workers (module level for multiprocessing on Windows)

def w_grid(args):
    c, offsets = args
    return summary(run_grid(c, offsets))


def w_page(args):
    """one unsolved page and its own length-matched null texts"""
    tp, c, offsets, nnull, seed = args
    r = run_grid(c, offsets)
    nulls = [summary(run_grid(t, offsets)) for t in null_texts(nnull, c, seed)]
    return tp, summary(r), r["rune"][1], letters_out(r["rune"][2]), r["latin"][1], latin_out(r["latin"][2]), nulls


def w_plant(args):
    seed, n, offsets = args
    c, P, label, changed, at = plant(seed, n, offsets)
    r = run_grid(c, offsets)
    top = r["rune"][2]
    planted_score = float(score(P[None, :], TR)[0])
    return dict(seed=seed, label=label, changed=len(changed), top_label=r["rune"][1], top_score=r["rune"][0],
                planted_score=planted_score, recovered=float((top == P).mean()),
                claim_align=int(align(top[None, :], CLAIM_RUNES)[0]), claim_changed=sum(at <= q < at + 56 for q in changed),
                rank=int((r["rune_all"] > planted_score + 1e-9).sum()), decodes=r["count"])


def letters_out(O):
    return "".join("?" if x == INV else lp.LATIN[x] for x in O)


def latin_out(O):
    return "".join("?" if x == LINV else ABC[x] for x in O)


def null_texts(count, c, seed):
    rng = np.random.default_rng(seed)
    out = []
    for j in range(count):
        out.append(rng.integers(N, size=len(c)) if j % 2 == 0 else rng.permutation(c))
    return out


# ------------------------------------------------------------------ sections

def section_a():
    say("A. WHICH PAGE IS 'PAGE 12'?")
    say("   Transcription pages tp map to the original images as image = tp + 2 (tp 0 = image 01, A Warning); the 2014 LP2 release")
    say("   numbers its 58 files 0.jpg-57.jpg = images 17-74; LiberPrimus.pdf puts 'Intus' (image 02) before A Warning (image 01).")
    conv = [("LP2 file number (0.jpg-57.jpg)", lambda k: k + 17), ("whole-book image number (00-74)", lambda k: k),
            ("LiberPrimus.pdf page", image_of_pdf), ("this project's transcription page index", image_of)]
    for num in (12, 28, 56):
        say(f"   page {num}:")
        for name, f in conv:
            img = f(num)
            tp = tp_of_image(img)
            if tp is None:
                say(f"     {name:42s} image {img:02d}: a title page, no runes")
                continue
            seg, lo, hi = page_span(tp)
            c = lp.runes_of(SEGS[seg])
            if seg in lp.KNOWN:
                plain = lp.KNOWN[seg][1](c)
                w = words_in(seg, lo, hi, plain)
                state = f"SOLVED section 0.{seg} ({lp.KNOWN[seg][0]})"
            else:
                w = words_in(seg, lo, hi, c)
                state = f"unsolved section 0.{seg}"
            say(f"     {name:42s} image {img:02d} = tp {tp}: {state}, runes {lo}-{hi - 1} ({hi - lo} runes); "
                f"first words{' (ciphertext)' if seg not in lp.KNOWN else ''}: {' '.join(w[:12])}")
    say()
    say("   An End (LP2 56.jpg, image 73) with the project's exact rule (key phi(p_n) = p_n - 1, one literal F; tests/expected_solved.txt):")
    say("     " + " ".join(lp.decrypt_known(SEGS, 16).replace("[page]", "").split())[:250])
    say(f"   The post's page-56 text begins 'TWENTY FOUR MONTHS WAS HERE'. LP2 56.jpg is this solved page; image 56 (book numbering)")
    say("   is unsolved, but then the post's page 12 is image 12, a page of The Loss of Divinity, which is written in plain runes.")
    say()
    s13, lo28, hi28 = page_span(tp_of_image(28 + 17))
    nums = [(k, t) for k, t in lp.numeral_positions(SEGS[s13]) if lo28 <= k < hi28]
    ip = ipaddress.ip_address("108.192.168.50")
    say(f"   Page 28 '108.192.168.50 GATEWAY': LP2 28.jpg (image 45, tp 43, section 0.{s13} runes {lo28}-{hi28 - 1}) has "
        f"{len(nums)} numerals among its runes; the Gematria Primus has no digits.")
    say(f"     108.192.168.50 is_private={ip.is_private} is_global={ip.is_global}; in 192.168.0.0/16: "
        f"{ip in ipaddress.ip_network('192.168.0.0/16')} (RFC 1918 needs 192.168 as the first two octets, so this is no LAN address).")
    say()


def section_b(page_tp):
    say("B. LENGTH AND WORD PATTERN")
    seg, lo, hi = page_span(page_tp)
    c = np.array(lp.runes_of(SEGS[seg])[lo:hi])
    rl = [len(lp.word_to_key(w)) for w in CLAIM_WORDS]
    ll = [len(w) for w in CLAIM_WORDS]
    say(f"   Claimed sentence: {len(CLAIM_WORDS)} words, {len(CLAIM_RUNES)} runes in the Gematria Primus spelling "
        f"({len(CLAIM_LETTERS)} letters). Rune word lengths {rl}; letter word lengths {ll}.")
    pw = [b - a for _, a, b in lp.word_spans(SEGS[seg], lp.runes_of(SEGS[seg])) if b > lo and a < hi]
    say(f"   LP2 12.jpg: {hi - lo} runes, {len(pw)} words (the first and last may continue on the next / previous page);"
        f" first word lengths {pw[:15]}.")
    say(f"   Every stage named in the post maps one symbol to one symbol (a multiplier mod 29, a periodic subtraction, a Bifid square),")
    say(f"   so a whole-page decryption has {hi - lo} symbols: the 56-rune sentence would leave {hi - lo - len(CLAIM_RUNES)} runes"
        f" ({100 * (hi - lo - len(CLAIM_RUNES)) / (hi - lo):.0f}% of the page) unexplained.")
    allw = []
    hits = {"runes": [], "letters": []}
    windows = 0
    for s in UNSOLVED:
        w = [b - a for _, a, b in lp.word_spans(SEGS[s], lp.runes_of(SEGS[s]))]
        allw += w
        for j in range(len(w) - 14):
            windows += 1
            if w[j:j + 15] == rl:
                hits["runes"].append((s, j))
            if w[j:j + 15] == ll:
                hits["letters"].append((s, j))
    f = np.bincount(allw, minlength=30) / len(allw)
    exp_r = windows * np.prod([f[x] for x in rl])
    exp_l = windows * np.prod([f[x] for x in ll])
    best = 0
    for s in UNSOLVED:
        w = [b - a for _, a, b in lp.word_spans(SEGS[s], lp.runes_of(SEGS[s]))]
        for j in range(len(w) - 14):
            best = max(best, sum(x == y for x, y in zip(w[j:j + 15], rl)))
    say(f"   In all of LP2 ({len(allw)} words, {windows} runs of 15 consecutive words) the claimed rune word lengths occur "
        f"{len(hits['runes'])} times (chance {exp_r:.1e}); the letter lengths {len(hits['letters'])} times (chance {exp_l:.1e}).")
    say(f"   Best partial fit anywhere: {best} of 15 word lengths. In every solved section the separators are the plaintext's word")
    say("   boundaries, so a correct plaintext of a page must have the page's word lengths (unless the separators were redrawn).")
    say()
    return c, lo


def section_c(c):
    say("C. THE 5x6 BIFID AS A MAP")
    rng = np.random.default_rng(3)
    n = len(c)
    say("   A Bifid needs every re-paired coordinate to be a cell. In a 5 x 6 square a column index 6 can land where a row is read")
    say("   (or a row index 6 where a column is read in 6 x 5), and the 30th cell is empty: the map is not a bijection.")
    for sqs, plain, tag in ((RSQ, PLAIN, "rune"), (LSQ, PLAIN_LETTERS, "letter")):
        fails, tot = 0, 0
        for sq in sqs:
            for p in PERIODS:
                for _ in range(10):
                    s0 = rng.integers(len(plain) - n)
                    cip, _ = bifid_encrypt(plain[s0:s0 + n], sq, p)
                    fails += (cip == sq.size).any()
                    tot += 1
        say(f"   {tag} squares: {fails} of {tot} English windows of {n} symbols cannot be encrypted at all (8 squares x 12 periods x 10)")
    inv = []
    for sq in RSQ:
        for p in PERIODS:
            inv.append(float((bifid_decrypt(c[None, :], sq, p, False)[0] == INV).mean()))
    say(f"   Decrypting page 12 itself with the rune squares (strict) leaves {100 * min(inv):.1f}-{100 * max(inv):.1f}% of its "
        f"positions without a plaintext symbol (mean {100 * np.mean(inv):.1f}%).")
    # where could the sentence come out of a 5x6 Bifid decryption at all?
    for sqs, tgt, L, tag in ((RSQ, CLAIM_RUNES, n, "runes"), (LSQ, CLAIM_LETTERS, len(translit(c)), "letters")):
        ok = tot = 0
        okp = set()
        for sq in sqs:
            for p in [0] + list(range(2, 61)):
                IR, IC = bifid_index(L, p)
                for a in range(L - len(tgt) + 1):
                    S = np.full(2 * L, -1, np.int64)
                    pos = np.arange(a, a + len(tgt))
                    S[IR[pos]], S[IC[pos]] = sq.rr[tgt], sq.cc[tgt]
                    A, B = S[0::2], S[1::2]
                    bad = ((A >= sq.R) | (B >= sq.C)).any()
                    both = (A >= 0) & (B >= 0) & (A < sq.R) & (B < sq.C)
                    bad = bad or (sq.cell[A[both], B[both]] == sq.size).any()
                    tot += 1
                    if not bad:
                        ok += 1
                        okp.add((sq.name, p))
        say(f"   Claimed sentence in {tag}: a 5x6 Bifid decryption can output it in {ok} of {tot} placements (8 squares x periods"
            f" 0, 2-60 x every offset in a {L}-symbol page; {len(okp)} square/period pairs). The other placements need a pair"
            f" that is not a cell.")
    say()


def section_d(page_tp, c, lo, args):
    say("D. THE CLAIMED PIPELINE IN EVERY READING WE COULD DEFINE")
    offsets = [0, lo]
    t0 = time.time()
    r = run_grid(c, offsets)
    say(f"   Readings per text: {r['count']:,} decodes = multiplier {len(MULTS)} ({', '.join(MULTS)}) x SUMUS stage {len(KEYS)}"
        f" x position origin 2 (page start, section start {lo})")
    say(f"   x [rune path: 2 orders x {len(RSQ)} rune squares | letter path: {len(LSQ)} letter squares] x {len(PERIODS)} periods"
        f" (whole text, 2-12) x 2 overflow rules (strict, wrap). {time.time() - t0:.1f} s.")
    say("   Scores: mean English bigram score per adjacent pair (10 ln-odds; Cicada's solved text +7.3 per rune, random about -10);")
    say("   'claim' = the most positions any placement of the claimed sentence shares with the output (56 runes / 59 letters).")
    ref_r = float(score(PLAIN[None, :], TR)[0])
    ref_l = float(score(PLAIN_LETTERS[None, :], TL)[0])
    say(f"   Calibration: Cicada's solved text scores {ref_r:+.2f} (runes) and {ref_l:+.2f} (letters); the claimed sentence "
        f"{float(score(CLAIM_RUNES[None, :], TR)[0]):+.2f} / {float(score(CLAIM_LETTERS[None, :], TL)[0]):+.2f}.")
    say()
    say(f"   PAGE 12 (LP2 12.jpg, {len(c)} runes):")
    for path, f in (("rune", letters_out), ("latin", latin_out)):
        st = r[path]
        say(f"     {path:5s} best score {st[0]:+.2f}  {st[1]}")
        say(f"           output: {f(st[2])[:150]}")
        say(f"     {path:5s} best claim match {st[3]} of {len(CLAIM_RUNES) if path == 'rune' else len(CLAIM_LETTERS)}  {st[4]}")
    pool = Pool(args.jobs)
    # positive controls
    say()
    say(f"   POSITIVE CONTROL: {args.plants} planted pages ({len(c)} runes of Cicada's solved text, the claimed sentence spliced in at a")
    say("   random place, a random reading with an invertible multiplier and a strict square; plaintext symbols that no 5x6 Bifid can")
    say("   produce are replaced first), each run through the same grid.")
    pr = pool.map(w_plant, [(1000 + j, len(c), offsets) for j in range(args.plants)])
    for d in pr:
        say(f"     seed {d['seed']}: top {d['top_score']:+.2f} (planted text {d['planted_score']:+.2f}, {d['rank']} decodes above it)"
            f" recovered {100 * d['recovered']:.0f}%, claim match {d['claim_align']} of 56 ({d['claim_changed']} sentence runes"
            f" replaced), {d['changed']} replaced in all; planted {d['label'][0]} {d['label'][2]} / {d['label'][3]} / p {d['label'][5]}")
    rec = sum(d["recovered"] >= 0.95 for d in pr)
    say(f"     recovered (top decode = the planted text at >= 95% of positions): {rec} of {len(pr)}; top scores "
        f"{min(d['top_score'] for d in pr):+.2f} .. {max(d['top_score'] for d in pr):+.2f}; claim match "
        f"{min(d['claim_align'] for d in pr)} .. {max(d['claim_align'] for d in pr)}")
    lpl = []
    for j in range(args.plants):
        cl, P, lab, ch = plant_latin(2000 + j, len(translit(c)))
        s, lb, O = latin_only_grid(cl)
        lpl.append((float((O == P).mean()), s, lab, lb))
    say(f"     letter Bifid alone ({args.plants} plants, letter squares x periods x overflow rules): recovered "
        f"{sum(x[0] >= 0.95 for x in lpl)} of {len(lpl)}, top scores {min(x[1] for x in lpl):+.2f} .. {max(x[1] for x in lpl):+.2f}")
    # null controls
    say()
    say(f"   NULL CONTROL: the same grid on {args.null} texts of {len(c)} runes (half uniform random, half shuffles of page 12).")
    nulls = pool.map(w_grid, [(t, offsets) for t in null_texts(args.null, c, 7)])
    nr = np.array([x[0] for x in nulls])
    nra = np.array([x[1] for x in nulls])
    nl = np.array([x[2] for x in nulls])
    nla = np.array([x[3] for x in nulls])
    pg = summary(r)
    for name, v, real in (("rune best score", nr, pg[0]), ("rune claim match", nra, pg[1]),
                          ("letter best score", nl, pg[2]), ("letter claim match", nla, pg[3])):
        say(f"     {name:19s} null median {np.median(v):+.2f}, 95% {np.quantile(v, 0.95):+.2f}, max {v.max():+.2f};"
            f" page 12 {real:+.2f}: {int((v >= real).sum())} of {len(v)} nulls reach it")
    # every unsolved page
    say()
    say("   EVERY UNSOLVED PAGE (LP2 0.jpg-55.jpg; the post: 'the mathematical master key is holding up flawlessly'):")
    jobs, skipped = [], []
    for tp in range(15, 71):
        try:
            seg, a, b = page_span(tp)
        except AssertionError:
            skipped.append(tp)
            continue
        jobs.append((tp, np.array(lp.runes_of(SEGS[seg])[a:b]), [0, a], args.page_null, 9000 + tp))
    pages = pool.map(w_page, jobs)
    pool.close()
    say(f"     {len(pages)} pages ({len(skipped)} skipped because they straddle two sections: tp {skipped}), each against "
        f"{args.page_null} null texts of its own length (half uniform random, half shuffles of the page);"
        f" {sum(x[1][4] * (1 + args.page_null) for x in pages):,} decodes.")
    say(f"     rune best score per page {min(x[1][0] for x in pages):+.2f} .. {max(x[1][0] for x in pages):+.2f}; letter "
        f"{min(x[1][2] for x in pages):+.2f} .. {max(x[1][2] for x in pages):+.2f}; claim match runes "
        f"{min(x[1][1] for x in pages)} .. {max(x[1][1] for x in pages)} of 56, letters {min(x[1][3] for x in pages)} .. "
        f"{max(x[1][3] for x in pages)} of 59")
    for k, name in enumerate(("rune best score", "rune claim match", "letter best score", "letter claim match")):
        reach = [sum(nl[k] >= x[1][k] for nl in x[6]) for x in pages]
        above = sum(r_ == 0 for r_ in reach)
        say(f"     {name:19s}: pages above all {args.page_null} of their nulls {above} of {len(pages)} (no signal: about "
            f"{len(pages) / (args.page_null + 1):.1f}, fewer with ties); median nulls reaching the page {np.median(reach):.0f}")
    for path, k, f in (("rune", 0, 3), ("latin", 2, 5)):
        x = max(pages, key=lambda x: x[1][k] - np.median([nl[k] for nl in x[6]]))
        nk = [nl[k] for nl in x[6]]
        say(f"     largest {path} excess over its own null median: LP2 {image_of(x[0]) - 17}.jpg (tp {x[0]}, "
            f"{len(PAGES[x[0]])} runes) {x[1][k]:+.2f} against null median {np.median(nk):+.2f}, max "
            f"{max(nk):+.2f}; {x[2 if path == 'rune' else 4]}")
        say(f"       output: {x[f][:150]}")
    say()
    return r, pr


def section_e(c):
    say("E. THE FINGERPRINT THE PIPELINE WOULD LEAVE")
    rng = np.random.default_rng(5)
    n = len(c)
    d_obs = int((c[1:] == c[:-1]).sum())
    sims, iocs, iocs_const = [], [], []
    for j in range(1000):
        cc, P, lab, _, _ = plant(50000 + j, n, [0, 1059], splice=False)
        sims.append(int((cc[1:] == cc[:-1]).sum()))
        v = lp.ioc(list(cc))
        iocs.append(v)
        if lab[2] in ("none", "*7", "*25 (= /7)"):
            iocs_const.append(v)
    sims = np.array(sims)
    say(f"   Doublets (the same rune twice in a row): page 12 has {d_obs} in {n - 1} adjacent pairs. Ciphertexts made by the claimed")
    say(f"   pipeline from Cicada's text (1,000 random readings): mean {sims.mean():.2f} per page (sd {sims.std():.2f}),"
        f" {int((sims <= d_obs).sum())} of 1,000 at or below {d_obs}.")
    rate = sims.mean() / (n - 1)
    from math import exp, lgamma, log
    lam = rate * 12947
    tail = sum(exp(k * log(lam) - lam - lgamma(k + 1)) for k in range(87))
    say(f"   All of LP2: 86 doublets in 12,947 pairs; the pipeline's rate {100 * rate:.2f}% predicts {lam:.0f}; P(<= 86) = {tail:.1e}."
        " The pipeline has no anti-repeat step, and every LP2 page shows the deficit.")
    say(f"   IoC (x29): page 12 {lp.ioc(list(c)):.3f}; pipeline ciphertexts {np.mean(iocs):.3f} +- {np.std(iocs):.3f} "
        f"(constant multiplier only {np.mean(iocs_const):.3f} +- {np.std(iocs_const):.3f}): not decisive at {n} runes.")
    say()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--null", type=int, default=200)
    ap.add_argument("--plants", type=int, default=24)
    ap.add_argument("--page-null", type=int, default=20)
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    args = ap.parse_args()
    t0 = time.time()
    say("Fact check: 'Liber Primus page 12 is officially 100% solved' (r/Cipher post, October 2026)")
    say(f"Claimed plaintext: {CLAIM}")
    say("Method as stated: 'Dynamic Multiplier 7 Mod-29 framework' + 'post-multiplier SUMUS key subtractor array' + '5x6 Vowel-First")
    say("Polybius fractionation square (Bifid Style)'; no code, square, key values or intermediate numbers were published.")
    say("Transcription: work/ref/lp_verified.txt. Script: work/factcheck_page12.py. Write-up: work/log/factcheck_page12_2026-10-18.md.")
    say()
    section_a()
    page_tp = tp_of_image(12 + 17)
    c, lo = section_b(page_tp)
    section_c(c)
    section_d(page_tp, c, lo, args)
    section_e(c)
    say(f"Done in {time.time() - t0:.0f} s.")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(LINES) + "\n")
    print("wrote", os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
