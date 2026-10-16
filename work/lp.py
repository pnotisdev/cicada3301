"""Liber Primus toolkit: Gematria Primus, transcription parsing, ciphers, scoring.

Usage:
    python lp.py segments              # list segments with rune counts and IoC
    python lp.py solve <seg>           # try every known Cicada method on one segment
    python lp.py show <seg> <method>   # print full decryption with one method
    python lp.py known                 # print every solved section with its exact rule
"""
import math
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

# Gematria Primus: (rune, latin, prime). Index in this list is the rune's value 0..28.
GP = [
    ("ᚠ", "F", 2), ("ᚢ", "U", 3), ("ᚦ", "TH", 5), ("ᚩ", "O", 7), ("ᚱ", "R", 11),
    ("ᚳ", "C", 13), ("ᚷ", "G", 17), ("ᚹ", "W", 19), ("ᚻ", "H", 23), ("ᚾ", "N", 29),
    ("ᛁ", "I", 31), ("ᛄ", "J", 37), ("ᛇ", "EO", 41), ("ᛈ", "P", 43), ("ᛉ", "X", 47),
    ("ᛋ", "S", 53), ("ᛏ", "T", 59), ("ᛒ", "B", 61), ("ᛖ", "E", 67), ("ᛗ", "M", 71),
    ("ᛚ", "L", 73), ("ᛝ", "ING", 79), ("ᛟ", "OE", 83), ("ᛞ", "D", 89), ("ᚪ", "A", 97),
    ("ᚫ", "AE", 101), ("ᚣ", "Y", 103), ("ᛡ", "IA", 107), ("ᛠ", "EA", 109),
]
N = len(GP)
RUNE_IDX = {r: i for i, (r, _, _) in enumerate(GP)}
LATIN = [l for _, l, _ in GP]
PRIME = [p for _, _, p in GP]

HERE = os.path.dirname(os.path.abspath(__file__))
MASTER_ORIGINAL = os.path.join(HERE, "ref", "lp_master.txt")   # community (rtkd/iddqd)
MASTER = os.path.join(HERE, "ref", "lp_verified.txt")         # + Phase 2 errata (ref/errata.tsv)


# ---------------------------------------------------------------- parsing

def load_segments(path=MASTER):
    """Return list of segments; each segment is a list of tokens.

    A token is either an int (rune index) or a separator string:
    ' ' word, '.' clause, '\\n' line, '&' paragraph, '%' page.
    """
    with open(path, encoding="utf-8") as f:
        text = f.read()
    body = text.split("\n\n", 1)[1]           # drop the delimiter legend
    body = body.split("§")[0]                 # chapter 0 only (chapter 1 is empty)
    segs = []
    for raw in body.split("$"):
        toks = []
        for ch in raw:
            if ch in RUNE_IDX:
                toks.append(RUNE_IDX[ch])
            elif ch == "-":
                toks.append(" ")
            elif ch == ".":
                toks.append(".")
            elif ch == "/":
                toks.append("\n")
            elif ch in "&%":
                toks.append(ch)
            elif ch.isalnum():
                if toks and isinstance(toks[-1], str) and toks[-1].startswith("#"):
                    toks[-1] += ch
                else:
                    toks.append("#" + ch)
        if any(isinstance(t, int) for t in toks):
            segs.append(toks)
    return segs


def runes_of(toks):
    return [t for t in toks if isinstance(t, int)]


def numeral_positions(toks):
    """[(rune_index_before_which_it_appears, '#token')] for every non-rune token."""
    out, k = [], 0
    for t in toks:
        if isinstance(t, int):
            k += 1
        elif t.startswith("#"):
            out.append((k, t))
    return out


def render(toks, plain):
    """Rebuild text from tokens, substituting decrypted indices in order."""
    out, it = [], iter(plain)
    for t in toks:
        if isinstance(t, int):
            out.append(LATIN[next(it)])
        elif t == " ":
            out.append(" ")
        elif t == ".":
            out.append(". ")
        elif t == "%":
            out.append("\n[page]\n")
        elif t == "&":
            out.append("\n")
        elif t.startswith("#"):
            out.append(f" {t[1:]} ")
    return re.sub(r" +", " ", "".join(out)).strip()


# ---------------------------------------------------------------- statistics

def ioc(idx):
    """Normalised index of coincidence (random = 1.0, English runes ~ 1.7-1.9)."""
    n = len(idx)
    if n < 2:
        return 0.0
    counts = [0] * N
    for i in idx:
        counts[i] += 1
    return sum(c * (c - 1) for c in counts) / (n * (n - 1) / N)


COMMON = set("""
A AN THE OF TO AND IN IS IT YOU THAT HE WAS FOR ON ARE AS WITH HIS THEY I AT BE THIS
HAVE FROM OR ONE HAD BY WORD BUT NOT WHAT ALL WERE WE WHEN YOUR CAN SAID THERE USE
EACH WHICH SHE DO HOW THEIR IF WILL UP OTHER ABOUT OUT MANY THEN THEM THESE SO SOME
HER WOULD MAKE LIKE HIM INTO TIME HAS LOOK TWO MORE WRITE GO SEE NUMBER NO WAY COULD
PEOPLE MY THAN FIRST WATER BEEN CALL WHO OIL ITS NOW FIND DOWN DAY DID GET COME MADE
MAY PART OWN WITHIN TRUTH TRUE KNOW BOOK BELIEVE NOTHING EXCEPT DEATH SACRED SELF
DIVINITY PRIMES WISDOM INSTRUCTION WARNING WELCOME KOAN END PARABLE LIKE INSTAR
EMERGE SURFACE CIRCUMFERENCE SHED OUR MUST BECOME CONSUMPTION TEST KNOWLEDGE EXPERIENCE
""".split())


def normalize(word):
    """Collapse spellings the rune alphabet cannot distinguish (V/U, K/C, IO/IA, NG/ING...)."""
    w = word.upper().replace("QU", "CW")
    for a, b in (("V", "U"), ("K", "C"), ("Q", "C"), ("Z", "S"), ("IA", "IO"),
                 ("IING", "NG"), ("ING", "NG")):
        w = w.replace(a, b)
    return w


def _load_dictionary(path=os.path.join(HERE, "ref", "english_20k.txt"), top=10000):
    """normalised word -> weight in (0.5, 1]; frequent words weigh more so that
    ambiguous readings (e.g. OF vs FO) resolve toward the common word."""
    weights = {normalize(w): 1.0 for w in COMMON}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            vocab = f.read().split()[:top]
        for rank, w in enumerate(vocab):
            if len(w) > 1 or w in ("a", "i"):
                n = normalize(w)
                weights[n] = max(weights.get(n, 0.0), 1.0 - 0.5 * rank / top)
    return weights


COMMON_N = _load_dictionary()


def word_spans(toks, plain):
    """[(latin_word, first_rune_pos, last_rune_pos+1)] in reading order.
    A bare line break ('\\n' between two runes) is a typographic wrap inside a word, not a word
    boundary: in the transcription a real boundary at a line end is always written '-' or '.'."""
    spans, cur, start, pos = [], [], 0, 0
    for t in toks + [" "]:
        if isinstance(t, int):
            if not cur:
                start = pos
            cur.append(LATIN[plain[pos]])
            pos += 1
        elif t == "\n":
            continue
        elif cur:
            spans.append(("".join(cur), start, pos))
            cur = []
    return spans


def latin_words(toks, plain):
    return [w for w, _, _ in word_spans(toks, plain)]


def word_score(toks, plain, lo=0, hi=None):
    """Fraction of runes (optionally only in words overlapping runes lo..hi) that sit in
    dictionary words."""
    spans = [(w, b - a) for w, a, b in word_spans(toks, plain) if b > lo and (hi is None or a < hi)]
    total = sum(n for _, n in spans)
    if not total:
        return 0.0
    return sum(n * COMMON_N.get(normalize(w), 0.0) for w, n in spans) / total


# ---------------------------------------------------------------- ciphers
# All return list of plaintext indices. "skip_f": a ciphertext ᚠ is passed
# through unencrypted and does not consume a key position (Cicada's rule
# "clear text F is not encrypted").

def shift(c, k):
    return [(x - k) % N for x in c]


def atbash(c, k=0):
    return [(N - 1 - x + k) % N for x in c]


def atbash_rev(c, k=0):
    return [(N - 1 - ((x - k) % N)) % N for x in c]


def keystream_decrypt(c, keyfn, skip_f=True, atb=False):
    out, j = [], 0
    for x in c:
        if skip_f and x == 0:
            out.append(0)
            continue
        p = (x - keyfn(j)) % N
        out.append(N - 1 - p if atb else p)
        j += 1
    return out


def keyed(c, keyfn, literal=(), atb=False):
    """Keystream decrypt where runes at positions in `literal` pass through unencrypted
    and do not consume a key position."""
    out, j = [], 0
    for i, x in enumerate(c):
        if i in literal:
            out.append(x)
            continue
        p = (x - keyfn(j)) % N
        out.append(N - 1 - p if atb else p)
        j += 1
    return out


def find_literal_f(toks, keyfn, atb=False, window=40, beam=16):
    """Decide which ciphertext ᚠ are literal F's. Beam search over the ᚠ positions in
    reading order, scoring each branch on the runes decided so far plus `window` runes of
    lookahead (where all later ᚠ are assumed encrypted)."""
    c = runes_of(toks)
    fpos = [k for k, x in enumerate(c) if x == 0]
    states = [frozenset()]
    for i in fpos:
        cand = {s | extra for s in states for extra in (frozenset(), frozenset([i]))}
        scored = sorted(cand, key=lambda s: (word_score(toks, keyed(c, keyfn, s, atb), 0, i + window),
                                             -len(s)), reverse=True)
        states = scored[:beam]
    best = max(states, key=lambda s: (word_score(toks, keyed(c, keyfn, s, atb)), -len(s)))
    return sorted(best)


def vigenere(c, key, skip_f=True, atb=False):
    return keystream_decrypt(c, lambda j: key[j % len(key)], skip_f, atb)


def primes(n):
    ps, k = [], 2
    while len(ps) < n:
        if all(k % p for p in ps if p * p <= k):
            ps.append(k)
        k += 1
    return ps


def totient_primes(c, skip_f=True, plus=False):
    # phi(p) = p - 1 for prime p
    ps = primes(len(c) + 10)
    sign = -1 if plus else 1
    return keystream_decrypt(c, lambda j: sign * (ps[j] - 1), skip_f)


def word_to_key(word):
    """Latin key word -> rune indices (greedy on digraphs)."""
    order = sorted(range(N), key=lambda i: -len(LATIN[i]))
    w, out = word.upper(), []
    while w:
        for i in order:
            if w.startswith(LATIN[i]):
                out.append(i)
                w = w[len(LATIN[i]):]
                break
        else:
            alias = {"V": 1, "K": 5, "Z": 15, "Q": 5}
            out.append(alias[w[0]])
            w = w[1:]
    return out


KEYWORDS = ["DIVINITY", "FIRFUMFERENFE", "CIRCUMFERENCE", "INSTAR", "PRIMES",
            "CICADA", "LIBERPRIMUS", "WELCOME", "KOAN", "INTUS", "PILGRIM",
            "WISDOM", "TRUTH", "SACRED", "DIVINE", "EMERGE", "SELF"]


def candidate_methods():
    yield "plain", lambda c: c
    for k in range(1, N):
        yield f"shift{k}", lambda c, k=k: shift(c, k)
    for k in range(N):
        yield f"atbash+{k}", lambda c, k=k: atbash(c, k)
    for kw in KEYWORDS:
        key = word_to_key(kw)
        for skip in (True, False):
            for atb in (False, True):
                tag = f"vig:{kw}{':skipF' if skip else ''}{':atbash' if atb else ''}"
                yield tag, lambda c, key=key, s=skip, a=atb: vigenere(c, key, s, a)
    for skip in (True, False):
        for plus in (False, True):
            tag = f"totient{'+' if plus else '-'}{':skipF' if skip else ''}"
            yield tag, lambda c, s=skip, p=plus: totient_primes(c, s, p)


METHODS = dict(candidate_methods())


# ---------------------------------------------------------------- solved sections
# Exact rules for every solved segment. Rule shared by all keystream sections
# (verified in Phase 1): plaintext F is never encrypted and does not consume a key
# position. Ciphertext alone cannot always tell a literal ᚠ from an encrypted one
# (e.g. "OF" -> ᚠᚠ in Welcome), so the literal positions are listed explicitly.
# They were found with find_literal_f() and equal the plaintext-F positions.

_DIVINITY = word_to_key("DIVINITY")
_FIRFUM = word_to_key("FIRFUMFERENFE")
_PRIMES = primes(2000)

KNOWN = {
    0: ("A Warning", lambda c: atbash(c)),
    1: ("Welcome", lambda c: keyed(c, lambda j: _DIVINITY[j % len(_DIVINITY)],
                                   {48, 74, 84, 132, 159, 160, 250, 421, 443, 465, 514})),
    2: ("Some Wisdom", lambda c: c),
    3: ("A Koan", lambda c: atbash(c, 3)),
    4: ("The Loss of Divinity", lambda c: c),
    5: ("A Koan", lambda c: keyed(c, lambda j: _FIRFUM[j % len(_FIRFUM)], {49, 58})),
    6: ("An Instruction", lambda c: c),
    16: ("An End", lambda c: keyed(c, lambda j: _PRIMES[j] - 1, {56})),
    17: ("Parable", lambda c: c),
}


def decrypt_known(segs, i):
    return render(segs[i], KNOWN[i][1](runes_of(segs[i])))


# ---------------------------------------------------------------- CLI

def main(argv):
    segs = load_segments()
    cmd = argv[1] if len(argv) > 1 else "segments"
    if cmd == "segments":
        for i, s in enumerate(segs):
            r = runes_of(s)
            print(f"0.{i:<3} runes={len(r):5d} pages={s.count('%')+1:3d} ioc={ioc(r):.3f}")
    elif cmd == "solve":
        s = segs[int(argv[2])]
        c = runes_of(s)
        res = sorted(((word_score(s, f(c)), ioc(f(c)), m) for m, f in METHODS.items()),
                     reverse=True)
        for sc, ic, m in res[:int(argv[3]) if len(argv) > 3 else 8]:
            print(f"{sc:.2f}  {m:28s} {render(s, METHODS[m](c))[:110]}")
    elif cmd == "show":
        s = segs[int(argv[2])]
        print(render(s, METHODS[argv[3]](runes_of(s))))
    elif cmd == "known":
        for i, (title, _) in KNOWN.items():
            print(f"===== 0.{i} {title}\n{decrypt_known(segs, i)}\n")
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
