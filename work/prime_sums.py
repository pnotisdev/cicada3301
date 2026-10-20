"""Sentence sums of the solved pages are prime far more often than chance (and LP2's ciphertext units are not).

    python prime_sums.py        # writes results/analysis/prime_sums.txt

Gematria sum of a unit = the sum of the Gematria Primus primes of its runes (F = 2 ... EA = 109). Units are the clauses
of the transcription: text between '.' marks, paragraph breaks '&' also end a unit, page breaks do not. Three checks:

  1. SOLVED PLAINTEXT (sections 0.0-0.6, 0.16, 0.17, decrypted with the exact rules of lp.KNOWN): how often is a unit's sum
     prime / odd, against (a) a shuffle null (same unit lengths, runes of the same section in random order) and (b) ordinary
     English (Emerson, Essays I) in GP runes by sentence length.
  2. LP2 CIPHERTEXT (sections 0.7-0.15 except the 9-rune caption): the same counts for words, clauses, lines, paragraphs,
     pages, against the same kind of shuffle null. A decryption that keeps the property would be a language-independent test.
  3. Clause lengths of LP1 and LP2 (how many LP2 clauses are as short as the solved aphorisms).

Exploratory (the unit definition is the transcription's, but the short/long split was made after looking); the pooled clause
effect does not depend on it. Says nothing about LP2's key until a decryption exists.
"""
import os
import random
import re
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lp  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "results", "analysis", "prime_sums.txt")
SHUFFLES = 500
LABELS = {"AWARNING", "WELCOME", "WIDSOM", "SOMEWISDOM", "ACOAN", "ANINSTRUCTIAN", "THELOSSOFDIUINITY", "ANEND", "PARABLE",
          "CONSUMPTIAN", "PRESERUATIAN", "ADHERENCE", "CNOWTHIS", "DAGAIN", "WH"}


def sieve(n):
    s = bytearray([1]) * (n + 1)
    s[0:2] = b"\x00\x00"
    for i in range(2, int(n ** 0.5) + 1):
        if s[i]:
            s[i * i::i] = bytearray(len(s[i * i::i]))
    return s


IS_P = sieve(400000)


def gsum(u):
    return sum(lp.PRIME[j] for j in u)


def units(toks, plain, kind):
    """lists of rune indices (plain = the rune values to use, in reading order)."""
    it = iter(plain)
    out, cur = [], []

    def flush():
        nonlocal cur
        if cur:
            out.append(cur)
        cur = []
    ends = {"word": (" ", ".", "&"), "clause": (".", "&"), "para": ("&",), "page": ("%",), "line": ("\n",)}[kind]
    for t in toks:
        if isinstance(t, int):
            cur.append(next(it))
        elif t in ends:
            flush()
    flush()
    return out


def shuffle_null(lens, pool, rng, reps):
    pool = list(pool)
    P, O = [], []
    for _ in range(reps):
        rng.shuffle(pool)
        p = o = k = 0
        for L in lens:
            s = gsum(pool[k:k + L])
            k += L
            p += IS_P[s]
            o += s % 2
        P.append(p)
        O.append(o)
    mp, mo = st.mean(P), st.mean(O)
    vp = sum((x - mp) ** 2 for x in P) / len(P)
    vo = sum((x - mo) ** 2 for x in O) / len(O)
    return mp, vp, mo, vo


def emerson_rates():
    path = os.path.join(HERE, "ref", "emerson_essays1.txt")
    txt = re.sub(r"\s+", " ", open(path, encoding="utf-8", errors="ignore").read())
    order = sorted(range(lp.N), key=lambda i: -len(lp.LATIN[i]))
    alias = {"V": 1, "K": 5, "Z": 15, "Q": 5}

    def to_runes(s):
        w = re.sub(r"[^A-Za-z ]", "", s).upper().replace("QU", "CW")
        out = []
        for word in w.split():
            while word:
                for i in order:
                    if word.startswith(lp.LATIN[i]) and lp.LATIN[i] not in ("EO", "OE", "AE", "IA", "EA", "ING"):
                        out.append(i)
                        word = word[len(lp.LATIN[i]):]
                        break
                else:
                    out.append(alias.get(word[0], 0))
                    word = word[1:]
        return out
    bins = {}
    for s in re.split(r"(?<=[.!?])\s+", txt):
        r = to_runes(s)
        n = len(r)
        if n < 6 or n > 400:
            continue
        S = gsum(r)
        b = "<=25" if n <= 25 else "26-40" if n <= 40 else "41-80" if n <= 80 else ">80"
        t = bins.setdefault(b, [0, 0, 0])
        t[0] += 1
        t[1] += IS_P[S]
        t[2] += S % 2
    return bins


def main():
    rng = random.Random(1033)
    segs = lp.load_segments()
    lines = ["# Gematria sums of sentences: solved plaintext vs chance (work/prime_sums.py; exploratory, no claim about LP2's key)",
             f"# shuffle null: {SHUFFLES} shuffles per section, same unit lengths, runes of the same section; seed 1033", ""]
    # ---- 1. solved plaintext
    rows = []
    for i, (title, fn) in lp.KNOWN.items():
        plain = fn(lp.runes_of(segs[i]))
        for u in units(segs[i], plain, "clause"):
            lab = "".join(lp.LATIN[j] for j in u)
            rows.append((i, len(u), gsum(u), lab in LABELS or len(u) < 6 or lab.startswith("SHADOWS"), lab))
    body = [r for r in rows if not r[3]]
    lines.append("1. SOLVED PLAINTEXT: clause sums (labels / headings and the 76-rune word square left out)")
    lines.append(f"   units {len(rows)}, body clauses {len(body)}, labels {sum(1 for r in rows if r[3])}")

    def row(sel, name):
        n = len(sel)
        if not n:
            return
        odd = sum(r[2] % 2 for r in sel)
        pr = sum(IS_P[r[2]] for r in sel)
        lines.append(f"   {name:24s} n={n:3d}  odd {odd:3d} ({100*odd/n:5.1f}%)  prime {pr:3d} ({100*pr/n:5.1f}%)")
    row(body, "all body clauses")
    row([r for r in body if r[1] <= 40], "short (<= 40 runes)")
    row([r for r in body if r[1] > 40], "long (> 40 runes)")
    for i in sorted({r[0] for r in body}):
        row([r for r in body if r[0] == i], f"  section 0.{i}")
    mp = vp = mo = vo = 0.0
    for i in sorted({r[0] for r in body}):
        plain = lp.KNOWN[i][1](lp.runes_of(segs[i]))
        a, b, c, d = shuffle_null([r[1] for r in body if r[0] == i], plain, rng, SHUFFLES)
        mp += a
        vp += b
        mo += c
        vo += d
    n = len(body)
    obs_p = sum(IS_P[r[2]] for r in body)
    obs_o = sum(r[2] % 2 for r in body)
    lines.append(f"   prime: observed {obs_p}/{n}, shuffle null {mp:.1f} +- {vp**.5:.1f} ({100*mp/n:.1f}%), z = {(obs_p-mp)/vp**.5:.1f}")
    lines.append(f"   odd:   observed {obs_o}/{n}, shuffle null {mo:.1f} +- {vo**.5:.1f} ({100*mo/n:.1f}%), z = {(obs_o-mo)/vo**.5:.1f}")
    lines.append(f"   label units prime: {sum(IS_P[r[2]] for r in rows if r[3] and r[1] >= 2)} of {sum(1 for r in rows if r[3] and r[1] >= 2)}")
    enc = [u for i in (0, 1, 3, 5, 16) for u in units(segs[i], lp.runes_of(segs[i]), "clause") if len(u) >= 6]
    lines.append(f"   displayed CIPHERTEXT of the encrypted pages (0.0, 0.1, 0.3, 0.5, 0.16): {sum(IS_P[gsum(u)] for u in enc)} of {len(enc)} "
                 f"clauses prime ({100*sum(IS_P[gsum(u)] for u in enc)/len(enc):.1f}%): the property is in the plaintext")
    lines.append("   control, ordinary English (Emerson, Essays I) in GP runes (digraph runes other than TH spelled as letters), "
                 "prime share of sentence sums by length:")
    em = emerson_rates()
    for b in ("<=25", "26-40", "41-80", ">80"):
        n_, p_, o_ = em[b]
        lines.append(f"     length {b:6s} n={n_:5d}  prime {100*p_/n_:5.1f}%  odd {100*o_/n_:5.1f}%")
    lines.append("")
    # ---- 2. LP2 ciphertext
    lines.append("2. LP2 CIPHERTEXT (0.7-0.15 without the 9-rune caption): prime share of unit sums against the shuffle null")
    tot = {}
    for i in range(7, 16):
        if i == 10:
            continue
        r = lp.runes_of(segs[i])
        for kind in ("word", "clause", "line", "para", "page"):
            U = units(segs[i], r, kind)
            if kind == "word":
                U = [u for u in U if len(u) >= 2]
            if len(U) < 3:
                continue
            a, b, _, _ = shuffle_null([len(u) for u in U], r, rng, 300)
            t = tot.setdefault(kind, [0, 0, 0.0, 0.0])
            t[0] += len(U)
            t[1] += sum(IS_P[gsum(u)] for u in U)
            t[2] += a
            t[3] += b
    for kind, (n, o, mu, var) in tot.items():
        lines.append(f"   {kind:6s} n={n:5d}  prime {o:4d} ({100*o/n:5.1f}%)  null {100*mu/n:5.1f}%  z = {(o-mu)/var**.5:5.2f}")
    lines.append("")
    # ---- 3. clause lengths and doublet rate
    lines.append("3. LP1 vs LP2: doublet rate of adjacent runes per section, and CLAUSE LENGTHS (runes); "
                 "LP1 = sections 0.0-0.6, 0.16, 0.17; LP2 = 0.7-0.15")
    for name, sel in (("LP1", [i for i in range(len(segs)) if i < 7 or i >= 16]), ("LP2", [i for i in range(7, 16) if i != 10])):
        rates = []
        for i in sel:
            r = lp.runes_of(segs[i])
            rates.append(100 * sum(1 for a, b in zip(r, r[1:]) if a == b) / (len(r) - 1))
        lines.append(f"   {name}: doublet rate per section {min(rates):.2f}-{max(rates):.2f}% (random: 3.45%)")
    for name, sel in (("LP1", [i for i in range(len(segs)) if i < 7 or i >= 16]), ("LP2", list(range(7, 16)))):
        L = []
        for i in sel:
            L += [len(u) for u in units(segs[i], lp.runes_of(segs[i]), "clause")]
        b = lambda lo, hi: sum(1 for x in L if lo <= x <= hi)  # noqa: E731
        lines.append(f"   {name}: clauses {len(L)}, mean {st.mean(L):.1f}, median {st.median(L)}; <=12: {b(0, 12)}, 13-25: {b(13, 25)}, "
                     f"26-40: {b(26, 40)}, 41-80: {b(41, 80)}, 81-150: {b(81, 150)}, >150: {b(151, 9999)}")
    lines.append("")
    lines.append("4. THE SOLVED CLAUSES: section, runes, Gematria sum, prime?, text (L = label / heading / word square, left out of the counts)")
    for i, n_, s_, is_label, lab in rows:
        lines.append(f"   0.{i:<3d} {n_:3d} {s_:6d} {'PRIME' if IS_P[s_] else '     '} {'L' if is_label else ' '} {lab[:64]}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
