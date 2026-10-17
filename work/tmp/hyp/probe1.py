"""Probe 1 (2026-10-17, laptop): a fresh look at LP2 fingerprints, looking for hypotheses not yet tested.

1. within-word coincidences c[j] == c[j+d] by lag d and word length L (LP2 against uniform and against English
   plaintext in GP runes, Emerson);
2. statistics of rune F (index 0), which a multiplicative cipher c = p*k (mod 29) or a literal-F rule leaves fixed;
3. chi-square of the lag-d difference stream (c[i+d] - c[i]) mod 29 for d = 1..400 (ciphertext autokey at lag d
   would leave the plaintext's letter distribution in it).
Run from anywhere: python work/tmp/hyp/probe1.py
"""
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, WORK)
import lp  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
N = lp.N
LP2 = list(range(7, 16))


def words_of(toks):
    """Rune-index lists per word, reading order; a bare line or page break is a wrap, not a boundary (lp.word_spans)."""
    out, cur = [], []
    for t in toks + [" "]:
        if isinstance(t, int):
            cur.append(t)
        elif t in ("\n", "%"):
            continue
        elif cur:
            out.append(cur)
            cur = []
    return out


def english_words(path=os.path.join(WORK, "ref", "emerson_essays1.txt"), start_marker="SELF-RELIANCE"):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    text = text[text.index(start_marker, text.index(start_marker) + 1):]
    text = text.split("*** END OF")[0]
    out = []
    for w in re.findall(r"[A-Za-z]+", text):
        w = w.upper().replace("IO", "IA")
        out.append(lp.word_to_key(w))
    return out


def within_word_table(words, lags=range(1, 11), lengths=range(2, 15)):
    """{(d, L): (pairs, coincidences)} and {d: (pairs, coincidences)} pooled over lengths."""
    tab, pooled = {}, {}
    for d in lags:
        P = C = 0
        for L in lengths:
            p = c = 0
            for w in words:
                if len(w) != L or L <= d:
                    continue
                for j in range(L - d):
                    p += 1
                    c += w[j] == w[j + d]
            tab[(d, L)] = (p, c)
            P += p
            C += c
        pooled[d] = (P, C)
    return tab, pooled


def main():
    segs = lp.load_segments()
    lp2_words = [w for i in LP2 for w in words_of(segs[i])]
    eng_words = english_words()
    print(f"LP2 words {len(lp2_words)}, runes {sum(map(len, lp2_words))}; English words {len(eng_words)}")

    # ---- 1. within-word coincidences
    tab, pooled = within_word_table(lp2_words)
    etab, epooled = within_word_table(eng_words)
    print("\n1. within-word coincidence rate by lag (percent); uniform 3.45")
    print("  d   LP2 pairs  LP2 coinc  LP2 %   z(unif)   English %")
    for d in pooled:
        P, C = pooled[d]
        eP, eC = epooled[d]
        e = P / N
        z = (C - e) / (e * (1 - 1 / N)) ** 0.5 if e else 0
        print(f" {d:2d}  {P:8d}  {C:8d}  {100 * C / max(P, 1):6.2f}  {z:+7.2f}   {100 * eC / max(eP, 1):6.2f}")

    print("\n   LP2 z-score (vs uniform) by lag d (rows) and word length L (columns)")
    Ls = list(range(2, 15))
    print("  d " + "".join(f"{L:>7d}" for L in Ls))
    for d in range(1, 11):
        row = []
        for L in Ls:
            p, c = tab[(d, L)]
            if p < 10:
                row.append("      .")
                continue
            e = p / N
            row.append(f"{(c - e) / (e * (1 - 1 / N)) ** 0.5:+7.1f}")
        print(f" {d:2d} " + "".join(row))
    print("   half-word lag (d = L/2) for even L:")
    for L in range(4, 15, 2):
        p, c = tab[(L // 2, L)]
        e = p / N
        print(f"   L={L:2d} d={L // 2}: pairs {p:5d} coinc {c:4d} expected {e:6.1f} z {(c - e) / (e * (1 - 1 / N)) ** 0.5:+5.2f}")

    # ---- 2. rune F (index 0)
    allr = [x for w in lp2_words for x in w]
    print("\n2. rune F (index 0)")
    print(f"   share of all runes: {100 * allr.count(0) / len(allr):.2f}% (uniform 3.45)")
    eng = [x for w in eng_words for x in w]
    print(f"   English plaintext F share (Emerson in GP runes): {100 * eng.count(0) / len(eng):.2f}%")
    two = [w for w in lp2_words if len(w) == 2]
    print(f"   2-rune words: {len(two)}; F last {sum(w[1] == 0 for w in two)}, F first {sum(w[0] == 0 for w in two)}"
          f" (uniform {len(two) / N:.1f} each)")
    etwo = [w for w in eng_words if len(w) == 2]
    print(f"   English 2-rune words: F last {100 * sum(w[1] == 0 for w in etwo) / len(etwo):.1f}%, "
          f"F first {100 * sum(w[0] == 0 for w in etwo) / len(etwo):.1f}%")
    init = Counter(w[0] for w in lp2_words)
    fin = Counter(w[-1] for w in lp2_words if len(w) > 1)
    print(f"   word-initial F {init[0]} of {len(lp2_words)} ({100 * init[0] / len(lp2_words):.2f}%), "
          f"word-final F {fin[0]} of {sum(fin.values())} ({100 * fin[0] / sum(fin.values()):.2f}%)")

    # ---- 3. lag-d difference stream
    print("\n3. chi-square (28 df: mean 28, sd 7.5) of (c[i+d]-c[i]) mod 29 within sections")
    streams = [lp.runes_of(segs[i]) for i in LP2]
    res = []
    for d in range(1, 401):
        cnt = Counter()
        for s in streams:
            for i in range(len(s) - d):
                cnt[(s[i + d] - s[i]) % N] += 1
        n = sum(cnt.values())
        e = n / N
        chi = sum((cnt[k] - e) ** 2 / e for k in range(N))
        chi_wo0 = sum((cnt[k] - e) ** 2 / e for k in range(1, N))
        res.append((d, chi, chi_wo0, cnt[0], e))
    for d, chi, chi0, z0, e in res[:12]:
        print(f"   d={d:3d} chi {chi:7.1f}  chi without bin 0 {chi0:6.1f}  bin0 {z0} (exp {e:.0f})")
    top = sorted(res, key=lambda r: -r[1])[:10]
    print("   largest chi over d = 1..400:", ", ".join(f"d={d}:{chi:.0f}" for d, chi, _, _, _ in top))
    top0 = sorted(res[1:], key=lambda r: -r[2])[:10]
    print("   largest chi without bin 0 over d = 2..400:", ", ".join(f"d={d}:{c0:.0f}" for d, _, c0, _, _ in top0))


if __name__ == "__main__":
    main()
