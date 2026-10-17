"""Checks of cicadanotebook.com claims on our own data (work/log/research_cicadanotebook_2026-10-17.md, section 5).
The site's numbers are data; every number printed here is computed from our transcription (lp.MASTER) and corpora.

1. Word statistics with the page seams joined (a page break without '-' or '.' is a wrap, like a line break; image check in
   page_seam_dots.py): words, one-rune words, within-word lag-5, under both conventions.
2. Doublets per section against sum n(n-1)/N, the exact expectation for a random reordering (their Session 29).
3. The doublet floor for additive keys that ignore the text (their Sessions 75-77). With c = p + k (or k - p) and key
   increments independent of plaintext increments, P(doublet) = sum_j q(j) p(-j) >= min_d p(d), whatever the key's
   distribution or structure (periodic, running key, PRNG, hash). Floor = transitions * min_d p(d), on English converted to
   runes. Positive control: the constant-step key that attains the floor, on English windows of LP2's length. Null: a
   uniform key.
4. The ciphertext-feedback frequency barrier (their Session 33): p_i = pi(c_i) - pi(c_{i-1}) + r for any rune permutation pi;
   relaxed to one bijection per previous rune. No plaintext rune can then exceed max(diagonal total, sum over rows of the
   largest off-diagonal count); the entropy floor is that of the sorted, aligned histogram. Positive control: English
   through the cipher with a random pi (the bound must admit its true peak). Null: random text with LP2's doublet rate.
5. Whole-word repetition by length (their Session 41) and the chance of a repeated two-word phrase of 6 runes.

    python work/tmp/hyp/notebook_checks.py   -> results/analysis/cicadanotebook_checks_2026-10-17.txt
"""
import glob
import math
import os
import re
import sys
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.path.join(HERE, "..", ".."))
REPO = os.path.dirname(WORK)
sys.path.insert(0, WORK)
import lp  # noqa: E402
import stats as lpstats  # noqa: E402

N = lp.N
SEGS = lpstats.SEGS
LP2 = lpstats.UNSOLVED
LP1 = list(range(0, 7))
OUT = os.path.join(REPO, "results", "analysis", "cicadanotebook_checks_2026-10-17.txt")
RNG = np.random.default_rng(3301)

out = []


def say(s=""):
    print(s)
    out.append(s)


# ------------------------------------------------------------------ data

def section(i):
    return np.array(lp.runes_of(SEGS[i]), dtype=np.int64)


def plain_section(i):
    return np.array(lp.KNOWN[i][1](lp.runes_of(SEGS[i])), dtype=np.int64)


def words(seg_ids, page_is_wrap, plain=False):
    """[(segment, [runes])]; '\\n' is always a wrap, '%' too when page_is_wrap; every other separator token ends a word"""
    res = []
    for i in seg_ids:
        vals = plain_section(i) if plain else section(i)
        cur, pos = [], 0
        for t in SEGS[i] + [" "]:
            if isinstance(t, int):
                cur.append(int(vals[pos]))
                pos += 1
            elif t == "\n" or (t == "%" and page_is_wrap):
                continue
            elif cur:
                res.append((i, cur))
                cur = []
    return res


def corpus(path):
    """(language, rune array) of a Project Gutenberg text, converted like work/sim.py (IO -> IA, greedy digraphs)"""
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    m = re.search(r"^Language:\s*(\w+)", text, re.M)
    lang = m.group(1) if m else "?"
    if "*** START OF" in text:
        text = text.split("*** START OF", 1)[1].split("\n", 1)[1]
    text = text.split("*** END OF")[0]
    runes = []
    for w in re.findall(r"[A-Za-z]+", text):
        runes += lp.word_to_key(w.upper().replace("IO", "IA"))
    return lang, np.array(runes, dtype=np.int64)


def incr_dist(p):
    return np.bincount((p[1:] - p[:-1]) % N, minlength=N) / (len(p) - 1)


# ------------------------------------------------------------------ 1. words

def word_stats():
    say("== 1. Words in LP2 (0.7-0.15): page break as boundary (old) vs as a wrap when unmarked (corrected)")
    for wrap in (False, True):
        ws = words(LP2, wrap)
        lens = np.array([len(w) for _, w in ws])
        ones = Counter(s for s, w in ws if len(w) == 1)
        pairs = coinc = 0
        for _, w in ws:
            for a in range(len(w) - 5):
                pairs += 1
                coinc += w[a] == w[a + 5]
        z = (coinc - pairs / N) / math.sqrt(pairs * (1 / N) * (1 - 1 / N))
        say(f"   {'corrected' if wrap else 'old      '}: {len(ws)} words, {int((lens == 1).sum())} one-rune "
            f"(by section {[ones.get(s, 0) for s in LP2]}), 2-rune share {100 * (lens == 2).mean():.1f}%, "
            f"mean length {lens.mean():.3f}, within-word lag-5 {coinc} of {pairs} (z {z:+.2f})")
    ones_types = Counter(w[0] for _, w in words(LP2, True) if len(w) == 1)
    missing = [lp.LATIN[r] for r in range(N) if r not in ones_types]
    say(f"   corrected one-rune words cover {len(ones_types)} of 29 runes; never alone: {missing}")
    say()


# ------------------------------------------------------------------ 2. doublets per section

def doublet_table():
    say("== 2. Doublets per section: observed against sum n(n-1)/N (random reordering of the section)")
    to = te = 0
    row = []
    for i in LP2:
        c = section(i)
        o = int((c[1:] == c[:-1]).sum())
        n = np.bincount(c, minlength=N)
        e = float((n * (n - 1)).sum() / len(c))
        to += o
        te += e
        row.append(f"0.{i} {o}/{e:.2f}")
    say("   " + ", ".join(row))
    say(f"   total {to} / {te:.2f} ({100 * to / te:.1f}% of expectation); transitions {sum(len(section(i)) - 1 for i in LP2)}")
    say()
    return to


# ------------------------------------------------------------------ 3. doublet floor

def doublet_floor(observed):
    say("== 3. Doublet floor for additive keys independent of the text: transitions x min_d p(d)")
    T = sum(len(section(i)) - 1 for i in LP2)
    refs = [("LP1 plaintext, segments 0.0-0.6", np.concatenate([plain_section(i) for i in LP1]))]
    english, other = [], []
    for path in sorted(glob.glob(os.path.join(WORK, "ref", "corpora", "pg*.txt"))) + [os.path.join(WORK, "ref", "emerson_essays1.txt")]:
        lang, r = corpus(path)
        if os.path.basename(path).startswith("emerson"):
            lang = "English"
        (english if lang == "English" else other).append((os.path.basename(path), lang, r))
    pooled = np.concatenate([r for _, _, r in english])
    refs.append((f"English pooled ({len(english)} texts)", pooled))
    say(f"   {'reference':40s} {'runes':>9s} {'p(0)':>7s} {'min p(d)':>9s} {'at d':>5s} {'floor':>7s}")
    for name, p in refs + [(f"   {n}", r) for n, _, r in english]:
        d = incr_dist(p)
        say(f"   {name:40s} {len(p):9d} {100 * d[0]:6.2f}% {100 * d.min():8.3f}% {int(d.argmin()):5d} {T * d.min():7.1f}")
    for n, lang, r in other:
        d = incr_dist(r)
        say(f"   (other language) {n} {lang:8s} {len(r):9d} runes: min p(d) {100 * d.min():.3f}% -> floor {T * d.min():.1f}")
    # positive control: the constant step that attains the floor, on English windows of LP2's length (pooled english)
    dp = incr_dist(pooled)
    dstar = int(dp.argmin())
    L = sum(len(section(i)) for i in LP2)
    starts = range(0, len(pooled) - L, L)
    fixed, best, unif = [], [], []
    for s0 in starts:
        w = pooled[s0:s0 + L]
        dw = (w[1:] - w[:-1]) % N
        cnt = np.bincount(dw, minlength=N)
        fixed.append(int(cnt[dstar]))                  # key step -d*: a doublet exactly when the plaintext step is d*
        best.append(int(cnt.min()))                    # the best constant step for this very window (chosen knowing it)
    for s0 in list(starts)[:200]:
        w = pooled[s0:s0 + L]
        c = (w + RNG.integers(0, N, L)) % N
        unif.append(int((c[1:] == c[:-1]).sum()))
    fixed, best = np.array(fixed), np.array(best)
    say(f"   positive control: {len(fixed)} English windows of {L} runes, constant key step {(-dstar) % N} (attains the floor):")
    say(f"      doublets mean {fixed.mean():.1f}, min {fixed.min()}, 1st percentile {np.percentile(fixed, 1):.0f}; "
        f"best step chosen per window: mean {best.mean():.1f}, min {best.min()}")
    say(f"   null control: uniform random key on {len(unif)} windows: doublets mean {np.mean(unif):.1f} (min {min(unif)})")
    say(f"   LP2: {observed} doublets in {T} transitions")
    say()


# ------------------------------------------------------------------ 4. feedback barrier

def barrier(streams):
    """(top bin bound, entropy floor in bits, transitions) for p_i = sigma_{c_{i-1}}(c_i) with sigma_x(x) = r for every x"""
    Tm = np.zeros((N, N), dtype=np.int64)
    for c in streams:
        np.add.at(Tm, (c[:-1], c[1:]), 1)
    tot = int(Tm.sum())
    off = Tm.copy()
    np.fill_diagonal(off, -1)
    srt = -np.sort(-off, axis=1)[:, :N - 1]            # 28 off-diagonal counts per row, largest first
    h = np.concatenate([[np.trace(Tm)], srt.sum(axis=0)]).astype(float)
    q = h[h > 0] / tot
    return h.max(), float(-(q * np.log2(q)).sum()), tot


def peak_entropy(streams):
    v = np.concatenate([s[1:] for s in streams])        # the first rune of a section has no predecessor
    f = np.bincount(v, minlength=N) / len(v)
    q = f[f > 0]
    return f.max(), float(-(q * np.log2(q)).sum())


def feedback_barrier():
    say("== 4. Ciphertext-feedback barrier: p_i = pi(c_i) - pi(c_{i-1}) + r, relaxed to one bijection per previous rune")
    real = [section(i) for i in LP2]
    top, H, tot = barrier(real)
    say(f"   LP2: no plaintext rune above {top:.0f} / {tot} = {100 * top / tot:.2f}%; entropy at least {H:.4f} bits")
    lp1 = [plain_section(i) for i in LP1]
    pk, he = peak_entropy(lp1)
    say(f"   LP1 plaintext: peak rune {100 * pk:.2f}%, entropy {he:.4f} bits")
    # positive control: English cut into LP2's section lengths, encrypted with a random pi and r
    _, eng = corpus(os.path.join(WORK, "ref", "corpora", "pg2009.txt"))
    lens = [len(s) for s in real]
    for trial in range(3):
        pi = RNG.permutation(N)
        inv = np.argsort(pi)
        r = int(RNG.integers(N))
        off = int(RNG.integers(0, len(eng) - sum(lens)))
        plains, ciphers = [], []
        for L in lens:
            p = eng[off:off + L]
            off += L
            c = np.empty(L, dtype=np.int64)
            c[0] = RNG.integers(N)
            for k in range(1, L):
                c[k] = inv[(p[k] - r + pi[c[k - 1]]) % N]
            plains.append(p)
            ciphers.append(c)
        ctop, cH, ctot = barrier(ciphers)
        pk, pe = peak_entropy(plains)
        say(f"   positive control {trial + 1} (English, random pi, r={r}): bound {100 * ctop / ctot:.2f}% >= true peak "
            f"{100 * pk:.2f}%; entropy floor {cH:.4f} <= true {pe:.4f}")
    # null: random text with LP2's doublet rate (a repeat is re-drawn 81% of the time)
    tops = []
    for trial in range(20):
        streams = []
        for L in lens:
            c = np.empty(L, dtype=np.int64)
            c[0] = RNG.integers(N)
            for k in range(1, L):
                x = RNG.integers(N)
                while x == c[k - 1] and RNG.random() < 0.81:
                    x = RNG.integers(N)
                c[k] = x
            streams.append(c)
        t, _, tt = barrier(streams)
        tops.append(100 * t / tt)
    say(f"   null (random text, 81% repeat re-draw, 20 runs): bound {np.mean(tops):.2f}% "
        f"(range {min(tops):.2f}-{max(tops):.2f})")
    say()


# ------------------------------------------------------------------ 5. word repetition and the phrase

def word_repetition():
    say("== 5. Whole-word repetition by length (corrected words) and the repeated two-word phrase")
    for name, ws in (("LP2 ciphertext", words(LP2, True)), ("LP1 plaintext", words(LP1, True, plain=True))):
        by = {}
        for _, w in ws:
            L = min(len(w), 4)
            by.setdefault(L, Counter())[tuple(w)] += 1
        parts = []
        for L in (1, 2, 3, 4):
            c = by.get(L, Counter())
            n = sum(c.values())
            pairs = sum(k * (k - 1) // 2 for k in c.values())
            if L < 4:
                exp = n * (n - 1) / 2 / (N * (N - 1) ** (L - 1))
                parts.append(f"len {L}: {n} words, {len(c)} distinct, {pairs} pairs (uniform without doublets {exp:.1f})")
            else:
                parts.append(f"len 4+: {n} words, {len(c)} distinct, {pairs} pairs")
        say(f"   {name}: " + "; ".join(parts))
    # adjacent word pairs inside a section with 6 runes in all; the phrase is one identical pair of shape (3, 3)
    ws = words(LP2, True)
    shapes = Counter()
    seen = Counter()
    for (s1, a), (s2, b) in zip(ws, ws[1:]):
        if s1 == s2 and len(a) + len(b) == 6:
            shapes[(len(a), len(b))] += 1
            seen[(tuple(a), tuple(b))] += 1
    rep = [(k, v) for k, v in seen.items() if v > 1]
    exp = sum(n * (n - 1) / 2 for n in shapes.values()) / (N * (N - 1) ** 5)
    say(f"   two-word spans of 6 runes: {sum(shapes.values())} ({dict(sorted(shapes.items()))}); repeated: "
        f"{[(' '.join(lp.LATIN[x] for x in a) + ' | ' + ' '.join(lp.LATIN[x] for x in b), v) for (a, b), v in rep]}")
    say(f"   expected identical pairs if the ciphertext were uniform without doublets: {exp:.2e} (chosen after the phrase was seen)")
    say()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    word_stats()
    obs = doublet_table()
    doublet_floor(obs)
    feedback_barrier()
    word_repetition()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("# work/tmp/hyp/notebook_checks.py: cicadanotebook.com claims recomputed on our data (seed 3301)\n")
        f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
