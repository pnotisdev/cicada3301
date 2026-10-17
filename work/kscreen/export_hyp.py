"""Keystreams for the untested hypotheses H3-H6 of docs/HYPOTHESES.md (campaign kscreen-hyp).

    python work/kscreen/export_hyp.py          # about 10 minutes: the deep constant digits dominate

data/library_hyp.ksb   H3 every main-library stream decimated by d = 2..29 (key pointer stepping d terms);
                       H4 the numbers of a known text: prefix sums of rune indices and of prime values, per-word Gematria
                       sums (prime values and indices) mod 29, for the solved LP plaintext and for Self-Reliance, forwards
                       and reversed; H6 pi, e, phi, sqrt2 digits (bases 10 and 29) from positions 10^6 and 3301*1033
                       (positions 1033 and 3301 are inside the main library's streams already).
data/library_h5.ksb    H5 ciphertext as key: the keyed solved sections (0.1, and 0.1+0.5+0.16) and LP2's ciphertext read
                       backwards, forwards and reversed. Screened with all 28 multipliers.
data/library_self.ksb  H5 LP2's ciphertext (sections 0.7-0.15 in book order) as a forward key: long-lag ciphertext autokey
                       and keys taken from another section. Screened with all 28 multipliers on
data/segments_self.txt the section windows with a G line (the window's index in that stream): the engine then never
                       deciphers a rune with itself (c_i - c_i = 0 would score a huge IoC).
Every stream must pass constraint 1 of docs/HYPOTHESES.md: its predicted ciphertext IoC under English plaintext may
exceed 1 only by what its finite histogram allows (LP2 has 0.9999 +- 0.0006). Each .ksb gets a .tsv like library.tsv.
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
import stats  # noqa: E402

N = lp.N
OUT = export.OUT
MINLEN = 400                       # a 300-rune screen window needs 383 key values
DEEP = (10 ** 6, 3301 * 1033)
BLOCK = keystreams.LEN


def admissible(v, P):
    """constraint 1; an i.i.d. uniform key of length n shows an excess of about 0.8/n from its histogram alone"""
    n = min(4000, len(v))
    pi = max(keystreams.predicted_ioc(v, P, 1, n=n), keystreams.predicted_ioc(v, P, -1, n=n))
    return pi <= 1.002 + 1.6 / n


def decimated(base):
    out = {}
    for name, v in base.items():
        v = np.asarray(v, dtype=np.int64) % N
        for d in range(2, N + 1):
            w = v[::d]
            if len(w) >= MINLEN:
                out[f"dec{d}:{name}"] = w
    return out


def solved_words():
    """the solved plaintext (sections 0.0-0.6, 0.16, 0.17 in book order) as a list of words of rune indices"""
    segs = stats.SEGS
    words = []
    for i, (_, f) in sorted(lp.KNOWN.items()):
        plain = f(lp.runes_of(segs[i]))
        words += [list(plain[a:b]) for _, a, b in lp.word_spans(segs[i], plain)]
    return words


def self_reliance_words():
    """the essay body: from its title above the first paragraph to the next essay (III. COMPENSATION)"""
    text = open(os.path.join(WORK, "ref", "emerson_essays1.txt"), encoding="utf-8").read()
    s = text.index("SELF-RELIANCE")
    for _ in range(2):                                  # contents, title page with epigraphs, title of the body
        s = text.index("SELF-RELIANCE", s + 1)
    body = text[s:text.index("COMPENSATION", s)]
    body = body[:body.rfind("III.")]
    words = [lp.word_to_key(w.upper().replace("IO", "IA")) for w in re.findall(r"[A-Za-z]+", body)]
    return [w for w in words if w]


def text_numbers(label, words):
    out = {}
    for rev in (False, True):
        ws = [w[::-1] for w in words[::-1]] if rev else words
        runes = np.array([r for w in ws for r in w], dtype=np.int64)
        primes = np.array([lp.PRIME[r] for r in runes], dtype=np.int64)
        tag = " (reversed)" if rev else ""
        out[f"{label} prefix sum of rune indices{tag}"] = np.cumsum(runes) % N
        out[f"{label} prefix sum of prime values{tag}"] = np.cumsum(primes) % N
        out[f"{label} word sums of prime values{tag}"] = np.array([sum(lp.PRIME[r] for r in w) for w in ws]) % N
        out[f"{label} word sums of rune indices{tag}"] = np.array([sum(w) for w in ws]) % N
    return out


def deep_digits():
    import mpmath
    mpmath.mp.prec = int((max(DEEP) + BLOCK) * np.log2(N)) + 256   # base 29 needs the most bits
    consts = {"pi": lambda: +mpmath.pi, "e": lambda: +mpmath.e, "phi": lambda: (1 + mpmath.sqrt(5)) / 2,
              "sqrt2": lambda: mpmath.sqrt(2)}
    out = {}
    for name, f in consts.items():
        v = f()
        frac = v - mpmath.floor(v)
        for base in (10, N):
            for pos in DEEP:
                # fractional digits pos+1 .. pos+BLOCK: floor(frac * base^(pos+BLOCK)) mod base^BLOCK
                x = int(mpmath.floor(frac * mpmath.mpf(base) ** (pos + BLOCK))) % base ** BLOCK
                dig = []
                for _ in range(BLOCK):
                    x, r = divmod(x, base)
                    dig.append(r)
                out[f"{name} digits (base {base}) from position {pos}"] = np.array(dig[::-1], dtype=np.int64) % N
        print(f"  deep digits of {name} done", flush=True)
    return out


def lp2_ciphertext():
    """LP2's runes in book order and each section's index in that stream"""
    starts, c = {}, []
    for i in stats.UNSOLVED:
        starts[i] = len(c)
        c += lp.runes_of(stats.SEGS[i])
    return np.array(c, dtype=np.int64), starts


def write_self_windows(path, starts):
    with open(path, "w", newline="\n") as f:
        for name, prev, runes, lens in export.segment_windows():
            g = starts[int(name.split(".")[1])]
            f.write(f"W {name} {prev}\nR {' '.join(map(str, runes))}\nL {' '.join(map(str, lens))}\nG {g}\n")


def keep(ks, P, label):
    out = {k: v for k, v in ks.items() if len(v) >= MINLEN and admissible(np.asarray(v) % N, P)}
    print(f"{label}: {len(out)} of {len(ks)} streams pass constraint 1 and the length cut")
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    P = keystreams.english_distribution()
    hyp = keep(decimated(export.library()), P, "H3 decimations")
    hyp.update(keep({**text_numbers("solved LP", solved_words()), **text_numbers("Self-Reliance", self_reliance_words())}, P,
                    "H4 text numbers"))
    hyp.update(keep(deep_digits(), P, "H6 deep constants"))
    export.write_ksb(os.path.join(OUT, "library_hyp.ksb"), hyp, os.path.join(OUT, "library_hyp.tsv"))

    c, starts = lp2_ciphertext()
    segs = stats.SEGS
    solved = {"ciphertext 0.1": lp.runes_of(segs[1]),
              "ciphertext 0.1+0.5+0.16": lp.runes_of(segs[1]) + lp.runes_of(segs[5]) + lp.runes_of(segs[16])}
    h5 = {}
    for name, v in solved.items():
        h5[name] = np.array(v, dtype=np.int64)
        h5[name + " (reversed)"] = np.array(v[::-1], dtype=np.int64)
    h5["LP2 ciphertext (reversed)"] = c[::-1].copy()
    h5 = keep(h5, P, "H5 ciphertext keys")
    export.write_ksb(os.path.join(OUT, "library_h5.ksb"), h5, os.path.join(OUT, "library_h5.tsv"))

    assert keep({"x": c}, P, "H5 LP2 ciphertext forward"), "LP2's own ciphertext must pass constraint 1"
    export.write_ksb(os.path.join(OUT, "library_self.ksb"), {"LP2 ciphertext (forward)": c},
                     os.path.join(OUT, "library_self.tsv"))
    write_self_windows(os.path.join(OUT, "segments_self.txt"), starts)
    print(f"wrote library_hyp.ksb ({len(hyp)} streams), library_h5.ksb ({len(h5)}), library_self.ksb (1), segments_self.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
