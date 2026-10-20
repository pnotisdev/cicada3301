"""Phase 31: preregistered book-code screen. Pointer sets taken from the book's numbers / LP2 numerals, resolved in the
formats Cicada used (2012-2014), scored with a letter-trigram model against random pointers of the same ranges.

Candidates are counted in advance: pointer set x format x book x ordering. Null: the whole screen repeated with random
pointers (same count, same per-coordinate ranges). Positive control: a plaintext planted with random valid pointers.
Usage: python work/phase31_book_codes.py [out.txt]      (1 core, a few minutes)
"""
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lp  # noqa: E402

OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


CITED = os.path.join(HERE, "ref", "corpora", "cited")
REF = os.path.join(HERE, "ref")
rng = np.random.default_rng(31)


# ------------------------------------------------------------------ books
class Book:
    """letters: uint8 A-Z array of all letters; hierarchical unit tables for words, lines, paragraphs, sentences."""

    def __init__(self, name, paragraphs, lines_by_par=None):
        self.name = name
        self.pars = paragraphs                       # list of paragraph strings
        letters, wfirst, wlast, wl0, wlen = [], [], [], [], []
        par_words, sent_words, sent_par = [], [], []
        pw0, pwn = [], []
        sw0, swn = [], []
        ps0, psn = [], []                            # sentences inside paragraph
        widx = 0
        for p in paragraphs:
            pw0.append(widx)
            ps0.append(len(sw0))
            nsent = 0
            for s in re.split(r"(?<=[.!?;])\s+", p):
                ws = re.findall(r"[A-Za-z]+", s)
                if not ws:
                    continue
                sw0.append(widx)
                swn.append(len(ws))
                nsent += 1
                for w in ws:
                    wl0.append(len(letters))
                    wlen.append(len(w))
                    letters.extend(ord(c) - 65 for c in w.upper())
                    widx += 1
            psn.append(nsent)
            pwn.append(widx - pw0[-1])
        self.L = np.array(letters, np.int16)
        self.wl0, self.wlen = np.array(wl0), np.array(wlen)
        self.pw0, self.pwn = np.array(pw0), np.array(pwn)
        self.sw0, self.swn = np.array(sw0), np.array(swn)
        self.ps0, self.psn = np.array(ps0), np.array(psn)
        # letter-level start of paragraph / sentence
        self.pl0 = self.wl0[np.minimum(self.pw0, len(self.wl0) - 1)]
        pend = np.append(self.pw0[1:], len(self.wl0))
        self.pln = np.array([self.wl0[e - 1] + self.wlen[e - 1] if e > s else 0 for s, e in zip(self.pw0, pend)]) - self.pl0
        self.sl0 = self.wl0[self.sw0]
        send_w = self.sw0 + self.swn
        self.sln = self.wl0[send_w - 1] + self.wlen[send_w - 1] - self.sl0


def par_split(text):
    pars = re.split(r"\n\s*\n", text)
    return [" ".join(p.split()) for p in pars if re.search(r"[A-Za-z]{3}", p)]


def gutenberg(path):
    t = open(path, encoding="utf-8", errors="ignore").read()
    a, b = t.find("*** START"), t.find("*** END")
    return t[t.find("\n", a) + 1:b] if a >= 0 and b > a else t


def load_books():
    books = {}
    t = gutenberg(os.path.join(CITED, "pg5160.txt"))
    t = t[t.find("King Arthur was at Caerlleon"):]
    books["mabinogion"] = Book("mabinogion", par_split(t[:400000]))
    t = gutenberg(os.path.join(CITED, "pg45315.txt"))
    books["blake_mhh"] = Book("blake_mhh", par_split(t))
    em = open(os.path.join(REF, "emerson_essays1.txt"), encoding="utf-8", errors="ignore").read().split("\n")
    books["selfreliance"] = Book("selfreliance", par_split("\n".join(em[847:1727])))
    lines = [l.strip() for l in open(os.path.join(CITED, "liber_al_oto.txt"), encoding="utf-8").read().split("\n") if l.strip()]
    verses, buf = [], []
    for l in lines:
        if re.fullmatch(r"\d+", l):
            continue
        if re.fullmatch(r"\d+\.", l):
            if buf:
                verses.append(" ".join(buf))
            buf = []
            continue
        buf.append(l)
    if buf:
        verses.append(" ".join(buf))
    books["liber_al"] = Book("liber_al", verses)
    return books


# ------------------------------------------------------------------ formats: coordinates -> letter (or -1)
def inb(a, n):
    return (a >= 1) & (a <= n)


def f_letter(B, v):                       # k-th letter of the whole text
    (k,) = v
    ok = inb(k, len(B.L))
    return np.where(ok, B.L[np.clip(k - 1, 0, len(B.L) - 1)], -1)


def f_wfirst(B, v):
    (k,) = v
    ok = inb(k, len(B.wl0))
    return np.where(ok, B.L[B.wl0[np.clip(k - 1, 0, len(B.wl0) - 1)]], -1)


def f_wlast(B, v):
    (k,) = v
    ok = inb(k, len(B.wl0))
    i = np.clip(k - 1, 0, len(B.wl0) - 1)
    return np.where(ok, B.L[B.wl0[i] + B.wlen[i] - 1], -1)


def mk_pair(u_l0, u_ln, u_w0, u_wn, kind):
    def f(B, v):
        a, b = v
        n = len(getattr(B, u_l0))
        ok = inb(a, n)
        i = np.clip(a - 1, 0, n - 1)
        if kind == "letter":
            ok &= inb(b, getattr(B, u_ln)[i])
            return np.where(ok, B.L[np.clip(getattr(B, u_l0)[i] + b - 1, 0, len(B.L) - 1)], -1)
        ok &= inb(b, getattr(B, u_wn)[i])
        w = np.clip(getattr(B, u_w0)[i] + b - 1, 0, len(B.wl0) - 1)
        return np.where(ok, B.L[B.wl0[w]], -1)
    return f


def f_par_sent_word(B, v):                # paragraph a, sentence b, word c (first letter)
    a, b, c = v
    ok = inb(a, len(B.ps0))
    i = np.clip(a - 1, 0, len(B.ps0) - 1)
    ok &= inb(b, B.psn[i])
    s = np.clip(B.ps0[i] + b - 1, 0, len(B.sw0) - 1)
    ok &= inb(c, B.swn[s])
    w = np.clip(B.sw0[s] + c - 1, 0, len(B.wl0) - 1)
    return np.where(ok, B.L[B.wl0[w]], -1)


def f_par_sent_word_letter(B, v):         # 2014 Emerson format: paragraph:sentence:word:letter
    a, b, c, d = v
    ok = inb(a, len(B.ps0))
    i = np.clip(a - 1, 0, len(B.ps0) - 1)
    ok &= inb(b, B.psn[i])
    s = np.clip(B.ps0[i] + b - 1, 0, len(B.sw0) - 1)
    ok &= inb(c, B.swn[s])
    w = np.clip(B.sw0[s] + c - 1, 0, len(B.wl0) - 1)
    ok &= inb(d, B.wlen[w])
    return np.where(ok, B.L[np.clip(B.wl0[w] + d - 1, 0, len(B.L) - 1)], -1)


def f_unit_letter3(B, v):                 # Liber AL style with paragraph = verse: (a = chapter ignored) verse b, letter c
    a, b, c = v
    return mk_pair("pl0", "pln", "pw0", "pwn", "letter")(B, (b, c))


FORMATS = {
    "letter k": (1, f_letter),
    "word k first": (1, f_wfirst),
    "word k last": (1, f_wlast),
    "par a, letter b": (2, mk_pair("pl0", "pln", "pw0", "pwn", "letter")),
    "par a, word b": (2, mk_pair("pl0", "pln", "pw0", "pwn", "word")),
    "sent a, letter b": (2, mk_pair("sl0", "sln", "sw0", "swn", "letter")),
    "sent a, word b": (2, mk_pair("sl0", "sln", "sw0", "swn", "word")),
    "par a, sent b, word c": (3, f_par_sent_word),
    "ch a, verse b, letter c": (3, f_unit_letter3),
    "par:sent:word:letter": (4, f_par_sent_word_letter),
}
ORDERS = ("printed", "reversed", "colmajor", "distinct")


def reorder(vals, how, shape=None):
    v = np.array(vals)
    if how == "printed":
        return v
    if how == "reversed":
        return v[::-1]
    if how == "colmajor" and shape:
        return v.reshape(shape).T.reshape(-1)
    if how == "colmajor":
        return v
    if how == "distinct":
        _, i = np.unique(v, return_index=True)
        return v[np.sort(i)]
    raise ValueError(how)


def tuples(v, k):
    n = len(v) // k
    return [np.array(v[: n * k]).reshape(n, k)[:, j] for j in range(k)]


# ------------------------------------------------------------------ language model
def trigram():
    txt = ""
    for f in ("pg1497.txt", "pg2009.txt", "pg205.txt", "pg3800.txt"):
        txt += gutenberg(os.path.join(REF, "corpora", f))
    L = np.array([ord(c) - 65 for c in re.sub(r"[^A-Z]", "", txt.upper())], np.int16)
    C = np.full((26, 26, 26), 0.5)
    np.add.at(C, (L[:-2], L[1:-1], L[2:]), 1)
    return np.log(C / C.sum(2, keepdims=True))


T3 = trigram()


def ll(s):
    """total log-likelihood of letter arrays s (valid entries only), -1 breaks the context; returns (ll, n_valid)."""
    s = np.asarray(s)
    ok = s >= 0
    if ok.sum() < 6:
        return 0.0, int(ok.sum())
    a, b, c = s[:-2], s[1:-1], s[2:]
    m = (a >= 0) & (b >= 0) & (c >= 0)
    return float(T3[a[m], b[m], c[m]].sum()), int(m.sum())


def score(B, fmt, vals, how, shape, nboot=150, ranges=None):
    k, f = FORMATS[fmt]
    v = reorder(vals, how, shape)
    cols = tuples(v, k)
    res = f(B, tuple(cols))
    n = len(res)
    if n < 6 or (res >= 0).mean() < 0.9:
        return None
    obs, m = ll(res)
    nul = np.empty(nboot)
    for t in range(nboot):
        rc = tuple(rng.integers(lo, hi + 1, n) for lo, hi in ranges_for(cols, ranges))
        r = f(B, rc)
        nul[t] = ll(r)[0] if (r >= 0).mean() >= 0.9 else np.nan
    nul = nul[~np.isnan(nul)]
    if len(nul) < 30:
        return None
    return (obs - nul.mean()) / (nul.std() + 1e-9), m


def ranges_for(cols, ranges):
    return [(int(c.min()), int(c.max())) for c in cols]


def screen(books, sets, nboot=150, only=None):
    """sets: name -> (values, shape). returns list of (z, name, fmt, book, order, n)."""
    out = []
    for sname, (vals, shape) in sets.items():
        for bname, B in books.items():
            for fmt in FORMATS:
                for how in ORDERS:
                    if how == "colmajor" and not shape:
                        continue
                    r = score(B, fmt, vals, how, shape, nboot)
                    if r:
                        out.append((r[0], sname, fmt, bname, how, r[1]))
    return out


def count_candidates(books, sets):
    n = 0
    for sname, (vals, shape) in sets.items():
        for how in ORDERS:
            if how == "colmajor" and not shape:
                continue
            n += len(FORMATS) * len(books)
    return n


# ------------------------------------------------------------------ pointer sets from the book
segs = lp.load_segments()


def nums(i):
    return [int(t[1:]) for t in segs[i] if isinstance(t, str) and t.startswith("#") and t[1:].isdigit()]


def payload():
    alpha = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"[:60]
    toks = [t[1:] for t in segs[15] if isinstance(t, str) and t.startswith("#")]
    out = []
    for t in toks:
        if len(t) == 2 and t[0] in alpha and t[1] in alpha:
            out.append(alpha.index(t[0]) * 60 + alpha.index(t[1]))
    return out


SETS = {
    "0.2 grid (12 printed numbers)": (nums(2), None),
    "0.6 square (25)": (nums(6), (5, 5)),
    "page-30 grid (16)": (nums(10), (4, 4)),
    "256-byte payload (as 0..255)": ([v for v in payload() if v > 0][:256], None),
}
# LP2 word-level pointer sets: Gematria sum of each word and word length per section 0.7 .. 0.15
for i in range(7, 16):
    ws = []
    cur = 0
    ln = 0
    for t in segs[i]:
        if isinstance(t, int):
            cur += lp.PRIME[t]
            ln += 1
        elif t in (" ", ".", "&") or t.startswith("#"):
            if ln:
                ws.append((cur, ln))
                cur = ln = 0
    if ln:
        ws.append((cur, ln))
    if len(ws) >= 100:
        SETS[f"seg0.{i} word Gematria sums"] = ([w[0] for w in ws][:300], None)

if __name__ == "__main__":
    books = load_books()
    say("== books (local) ==")
    for n, B in books.items():
        say(f"  {n}: {len(B.L)} letters, {len(B.wl0)} words, {len(B.ps0)} paragraphs, {int(B.psn.sum())} sentences")
    say(f"== pointer sets: " + "; ".join(f"{k} ({len(v[0])})" for k, v in SETS.items()))
    N = count_candidates(books, SETS)
    say(f"== candidates counted in advance: {N} (sets x orders x formats x books; ordering 'colmajor' only for the 2D grids) ==")
    real = screen(books, SETS, nboot=100)
    real.sort(reverse=True)
    say(f"  scored candidates: {len(real)} of {N} (others had < 90% valid pointers)")
    for r in real[:8]:
        say(f"    z {r[0]:+.2f}: {r[1]} | {r[2]} | {r[3]} | {r[4]} | n={r[5]}")
    # null screens: the same sets with random values of the same ranges and lengths
    say("\n== null screens: random pointer sets, same lengths and ranges ==")
    maxz = []
    for rep in range(12):
        nsets = {}
        for k, (v, sh) in SETS.items():
            v = np.array(v)
            nsets[k] = (list(rng.integers(v.min(), v.max() + 1, len(v))), sh)
        z = screen(books, nsets, nboot=100)
        maxz.append(max(r[0] for r in z))
    maxz = np.array(maxz)
    say(f"  max z over the whole screen, 12 null screens: mean {maxz.mean():.2f}, sd {maxz.std():.2f}, max {maxz.max():.2f}")
    # positive control: planted message
    say("\n== positive control: planted plaintext, random valid pointers ==")
    msg_src = "THEPRIMESARESACREDALLTHINGSSHOULDBEENCRYPTEDFINDYOURTRUTHEXPERIENCEYOURDEATH"
    thr = np.quantile(maxz, 0.95) if len(maxz) else 4
    for n in (12, 25, 64):
        hit = tot = 0
        for rep in range(8):
            bn = ["mabinogion", "blake_mhh", "liber_al", "selfreliance"][rep % 4]
            fmt = ["letter k", "word k first", "par a, letter b", "par a, sent b, word c"][rep // 2 % 4]
            B = books[bn]
            k, f = FORMATS[fmt]
            msg = [ord(c) - 65 for c in msg_src[:n * 1]]
            # n target letters, each needs a tuple of k pointers resolving to it; range like the 0.6 square
            hi = 1311
            tup = []
            for ch in msg:
                for _ in range(20000):
                    c = tuple(rng.integers(1, hi + 1, 1) if j == 0 or k == 1 else rng.integers(1, 40, 1) for j in range(k))
                    if f(B, c)[0] == ch:
                        tup.append(np.array([x[0] for x in c]))
                        break
                else:
                    tup = None
                    break
            if tup is None:
                continue
            vals = list(np.array(tup).reshape(-1))
            tot += 1
            z = score(B, fmt, vals, "printed", None, 100)
            if z is not None and z[0] > max(thr, 4.0):
                hit += 1
        say(f"  planted {n} letters: detected (z > null 95% max {thr:.1f}) {hit}/{tot}")
    if len(sys.argv) > 1:
        open(sys.argv[1], "w", encoding="utf-8").write("\n".join(OUT) + "\n")
