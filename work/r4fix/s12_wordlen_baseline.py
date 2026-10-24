"""s12: how strong is LP2's word-length anomaly against honest baselines, and what extra-rune share q does each imply?

Nothing in LP2 is solved.  Keyless: only LP2's 2,896 word LENGTHS are used (no ciphertext runes are scored).

    python -B work/r4fix/s12_wordlen_baseline.py [--quick]

Output: results/r4fix/s12_wordlen_baseline/summary.txt (+ results.json).  One process, numpy only.

Definitions
- Histogram bins: word length 1..11 and 12+ (12 bins), as work/wordlen.py.
- Baselines: Cicada's solved text (lp.KNOWN, 739 words) and English corpora (Emerson, Walden, Origin of Species, KJV, The
  Republic, Meditations, Paradise Lost, Ethics), each in two spellings:
    runes   = Gematria Primus runes, digraphs one rune (TH NG EA OE AE EO IA), IO -> IA (fam_data.english / wordlen.py);
    letters = Latin letters, one rune per letter (the "no digraph runes" reading).
- Two-sample test: G (and Pearson chi2) of the 2 x 12 table LP2 vs baseline, df 11; p by Monte Carlo from the pooled
  histogram (both samples redrawn), so the baseline's own sampling noise counts.
- Fit: "+1 rune in a share q of words": expected baseline counts B(q) = shift of the baseline histogram; G(q) = two-sample G
  between LP2's histogram and B(q) (the baseline sample size N2 enters, so a small baseline is noisy); q = argmin over a
  0.005 grid.  `multi` convention: only words of >= 2 runes may get the extra rune; `all`: every word.
  CI: nonparametric bootstrap (LP2 and baseline both resampled from their empirical histograms).  Fit p: parametric
  bootstrap at the fitted q (LP2* ~ Mult(n1, B(q)/N2), baseline* ~ Mult(N2, baseline), refit q, compare min G).
"""
import json
import os
import re
import sys
import time

import numpy as np
from scipy.special import xlogy
from scipy.stats import chi2 as chi2dist, kstest

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
REPO = os.path.normpath(os.path.join(WORK, ".."))
sys.path.insert(0, WORK)
import lp      # noqa: E402
import stats   # noqa: E402

QUICK = "--quick" in sys.argv
BINS = 12
Q = np.round(np.arange(0.0, 1.0001, 0.005), 3)
OUT = os.path.join(REPO, "results", "r4fix", "s12_wordlen_baseline")
LINES = []


def say(s=""):
    print(s, flush=True)
    LINES.append(s)


# ------------------------------------------------------------------ data
def hist(lengths):
    h = np.zeros(BINS)
    for L in lengths:
        h[min(int(L), BINS) - 1] += 1
    return h


def lp2_lengths():
    segs = lp.load_segments()
    out = []
    for i in stats.UNSOLVED:
        c = lp.runes_of(segs[i])
        out += [b - a for _, a, b in lp.word_spans(segs[i], c)]
    return np.array(out)


def solved_words():
    """[(latin spelling, rune count)] of lp.KNOWN, reading order (739 words, 2,977 runes)."""
    segs = lp.load_segments()
    out = []
    for i, (_, f) in lp.KNOWN.items():
        c = lp.runes_of(segs[i])
        p = f(c)
        for w, a, b in lp.word_spans(segs[i], p):
            out.append((w, b - a))
    return out


CORPORA = {
    "Emerson": "ref/emerson_essays1.txt",
    "Walden": "ref/corpora/pg205.txt",
    "Origin of Species": "ref/corpora/pg2009.txt",
    "KJV Bible": "ref/corpora/pg10.txt",
    "Republic (Jowett)": "ref/corpora/pg1497.txt",
    "Meditations": "ref/corpora/pg2680.txt",
    "Paradise Lost": "ref/corpora/pg26.txt",
    "Ethics (Elwes)": "ref/corpora/pg3800.txt",
}


def corpus_words(path):
    txt = open(os.path.join(WORK, path), encoding="utf-8", errors="ignore").read()
    if "SELF-RELIANCE" in txt:
        txt = txt[txt.index("SELF-RELIANCE"):]
    elif "*** START OF" in txt:
        txt = txt[txt.index("*** START OF"):]
        txt = txt[txt.index("\n") + 1:]
    txt = txt.split("*** END OF")[0]
    return [w.upper() for w in re.findall(r"[A-Za-z]+", txt)]


_cache = {}


def rune_len(w):
    r = _cache.get(w)
    if r is None:
        r = _cache[w] = len(lp.word_to_key(w.replace("IO", "IA")))
    return r


class Corpus:
    def __init__(self, name, words=None, lens_runes=None, lens_letters=None):
        self.name = name
        if words is not None:
            lens_runes = np.array([rune_len(w) for w in words])
            lens_letters = np.array([len(w) for w in words])
            self.words = words
        self.lens = {"runes": lens_runes, "letters": lens_letters}
        self.hist = {s: hist(v) for s, v in self.lens.items()}
        self.cum = {}
        for s, v in self.lens.items():
            c = np.zeros((len(v) + 1, BINS), np.int32)
            b = np.minimum(v, BINS) - 1
            for k in range(BINS):
                c[1:, k] = np.cumsum(b == k)
            self.cum[s] = c

    def block_hists(self, s, size, K, rng):
        c = self.cum[s]
        n = len(self.lens[s])
        st = rng.integers(0, n - size + 1, K)
        return (c[st + size] - c[st]).astype(float)


# ------------------------------------------------------------------ statistics
def g2(o1, o2):
    """Two-sample G on (..., BINS) arrays (counts may be fractional in o2)."""
    n1 = o1.sum(-1, keepdims=True)
    n2 = o2.sum(-1, keepdims=True)
    pool = (o1 + o2) / (n1 + n2)
    e1 = n1 * pool + 1e-300
    e2 = n2 * pool + 1e-300
    return 2 * (xlogy(o1, o1 / e1).sum(-1) + xlogy(o2, o2 / e2).sum(-1))


def pearson2(o1, o2):
    n1, n2 = o1.sum(), o2.sum()
    pool = (o1 + o2) / (n1 + n2)
    m = pool > 0
    e1, e2 = n1 * pool[m], n2 * pool[m]
    return float((((o1[m] - e1) ** 2) / e1).sum() + (((o2[m] - e2) ** 2) / e2).sum())


def two_sample(o1, o2, R, rng):
    """G, chi2, df, p_MC (pooled-null Monte Carlo), p_asym (chi2 on G, df 11)."""
    g = float(g2(o1, o2))
    n1, n2 = int(o1.sum()), int(o2.sum())
    pool = (o1 + o2) / (n1 + n2)
    a = rng.multinomial(n1, pool, size=R).astype(float)
    b = rng.multinomial(n2, pool, size=R).astype(float)
    gs = g2(a, b)
    return dict(G=g, chi2=pearson2(o1, o2), df=BINS - 1, p_mc=float((1 + (gs >= g - 1e-9).sum()) / (R + 1)),
                p_asym=float(chi2dist.sf(g, BINS - 1)),
                s1=float(o1[1] / n1), s2=float(o2[1] / n2),
                z2=float((o1[1] / n1 - o2[1] / n2) / np.sqrt(pool[1] * (1 - pool[1]) * (1 / n1 + 1 / n2))))


def shift(b, Qv, multi=True):
    """b (..., BINS) counts or probabilities -> (..., len(Qv), BINS): a share q of eligible words gets +1 rune."""
    ins = b.copy()
    if multi:
        ins[..., 0] = 0
    ins = ins[..., None, :] * Qv[:, None]
    m = b[..., None, :] - ins
    m[..., 1:] += ins[..., :-1]
    m[..., -1] += ins[..., -1]
    return m


def fit_batch(o1, o2, multi=True):
    """o1, o2 (R, BINS) -> (qhat (R,), Gmin (R,)).  chunks keep memory small."""
    qs, gm = [], []
    for i in range(0, len(o1), 250):
        a, b = o1[i:i + 250], o2[i:i + 250]
        B = shift(b, Q, multi)
        G = g2(a[:, None, :], B)
        k = G.argmin(1)
        qs.append(Q[k])
        gm.append(G[np.arange(len(k)), k])
    return np.concatenate(qs), np.concatenate(gm)


def fit(o1, o2, R_ci, R_p, rng, multi=True):
    q, gm = fit_batch(o1[None], o2[None], multi)
    q, gm = float(q[0]), float(gm[0])
    n1, n2 = int(o1.sum()), int(o2.sum())
    # nonparametric bootstrap CI: both samples resampled
    a = rng.multinomial(n1, o1 / n1, size=R_ci).astype(float)
    b = rng.multinomial(n2, o2 / n2, size=R_ci).astype(float)
    qb, _ = fit_batch(a, b, multi)
    lo, hi = np.percentile(qb, [2.5, 97.5])
    # parametric bootstrap p of the fitted model
    pi1 = shift(o2 / n2, np.array([q]), multi)[0]
    a = rng.multinomial(n1, pi1 / pi1.sum(), size=R_p).astype(float)
    b = rng.multinomial(n2, o2 / n2, size=R_p).astype(float)
    _, gms = fit_batch(a, b, multi)
    p = float((1 + (gms >= gm - 1e-9).sum()) / (R_p + 1))
    return dict(q=q, Gmin=gm, lo=float(lo), hi=float(hi), p=p, qb_sd=float(qb.std()),
                at_zero=float((qb == 0).mean()), at_one=float((qb == 1).mean()))


def exp_one_rune(o1, o2, q, multi):
    """expected number of 1-rune words in a sample of size n1 under the fitted shift model."""
    n1 = o1.sum()
    m = shift(o2 / o2.sum(), np.array([q]), multi)[0]
    return float(n1 * m[0])


def pseudo_insert(h, n, q, rng):
    """n words with lengths drawn from the histogram h, +1 rune in a share q of multi-rune words."""
    c = rng.multinomial(n, h / h.sum())
    out = c.astype(float)
    for k in range(1, BINS - 1):
        ins = rng.binomial(c[k], q)
        out[k] -= ins
        out[k + 1] += ins
    return out


# ------------------------------------------------------------------ main
def main():
    t0 = time.time()
    cpu0 = time.process_time()
    rng = np.random.default_rng(20261024)
    RB = 2000 if not QUICK else 300
    RMC = 20000 if not QUICK else 2000
    NCTL = 200 if not QUICK else 30
    RC = 600 if not QUICK else 100

    L2 = lp2_lengths()
    O1 = hist(L2)
    n1 = int(O1.sum())
    say("# s12: LP2 word-length anomaly against honest baselines (2026-10-24)")
    say("Nothing in LP2 is solved.  Keyless: LP2's 2,896 word lengths only.  Seed 20261024, single process, numpy.")
    say(f"LP2: {n1} words, 1-rune {int(O1[0])}, 2-rune {int(O1[1])} ({100 * O1[1] / n1:.2f}%), bins 1..11,12+:")
    say("  " + " ".join(f"{x:5.1f}" for x in 100 * O1 / n1))

    sw = solved_words()
    solved = Corpus("Solved text", lens_runes=np.array([r for _, r in sw]),
                    lens_letters=np.array([len(w) for w, _ in sw]))
    say(f"Solved text (lp.KNOWN keys {sorted(lp.KNOWN)}): {len(sw)} words, {sum(r for _, r in sw)} runes")
    cors = {}
    for name, path in CORPORA.items():
        c = Corpus(name, words=corpus_words(path))
        cors[name] = c
        say(f"  {name}: {len(c.lens['runes'])} words")
    allc = dict(cors)
    base = {"Solved text": solved}
    base.update(cors)

    # ---------------- reproduce loose-ends numbers
    say("\n## 0. Reproduction of the loose-ends audit and of results/analysis/wordlen.txt")
    for s in ("runes", "letters"):
        r = two_sample(O1, solved.hist[s], RMC, rng)
        say(f"  LP2 vs solved text ({s}): chi2 {r['chi2']:.1f}, G {r['G']:.1f}, df 11, asymptotic p {r['p_asym']:.2e} "
            f"(Pearson-chi2 p {chi2dist.sf(r['chi2'], 11):.2e}), MC p {r['p_mc']:.4f}; "
            f"2-rune share {100 * r['s2']:.1f}% vs LP2 {100 * r['s1']:.1f}%, z {r['z2']:+.1f}")
        # the old one-sample G against a fixed histogram
        pm = solved.hist[s] / solved.hist[s].sum()
        g1 = 2 * float(xlogy(O1, O1 / (n1 * pm)).sum())
        say(f"    old one-sample G against the fixed solved histogram ({s}): {g1:.1f}, p {chi2dist.sf(g1, 11):.2e}")
    for s in ("runes", "letters"):
        pm = cors["Emerson"].hist[s] / cors["Emerson"].hist[s].sum()
        g1 = 2 * float(xlogy(O1, O1 / (n1 * pm)).sum())
        say(f"    old one-sample G against Emerson ({s}): {g1:.1f}, p {chi2dist.sf(g1, 11):.2e} "
            f"(wordlen.txt: runes 242.4, letters 60.4)")

    # ---------------- main table
    say("\n## 1. Baseline x spelling: two-sample test and fitted q  (multi = +1 only in words of >= 2 runes)")
    hdr = ("baseline / spelling | words | 2-rune % | chi2 (df 11) | G | p two-sample MC | q multi [95% CI] | min G, p fit "
           "| q all [CI] | 1-rune exp (multi) vs 83")
    say(hdr)
    rows = {}
    for name, c in base.items():
        for s in ("runes", "letters"):
            o2 = c.hist[s]
            ts = two_sample(O1, o2, RMC, rng)
            fm = fit(O1, o2, RB, RB, rng, True)
            fa = fit(O1, o2, RB, RB, rng, False)
            e1 = exp_one_rune(O1, o2, fm["q"], True)
            rows[f"{name}|{s}"] = dict(ts=ts, fit_multi=fm, fit_all=fa, e1=e1, n2=int(o2.sum()))
            say(f"{name} / {s} | {int(o2.sum())} | {100 * ts['s2']:.1f} | {ts['chi2']:.1f} | {ts['G']:.1f} | "
                f"{ts['p_mc']:.4f} (asym {ts['p_asym']:.1e}) | {fm['q']:.3f} [{fm['lo']:.3f}, {fm['hi']:.3f}] | "
                f"{fm['Gmin']:.1f}, p {fm['p']:.3f} | {fa['q']:.3f} [{fa['lo']:.3f}, {fa['hi']:.3f}] (G {fa['Gmin']:.1f}, "
                f"p {fa['p']:.3f}) | {e1:.1f}")
    say("(chi2 / G / p are for the UNFITTED model 'LP2 has the baseline's distribution'; the fit columns are the +1 model.)")

    # ---------------- one-rune accounting
    say("\n## 2. One-rune accounting (LP2 has 83 one-rune words)")
    for key in ("Solved text|runes", "Solved text|letters", "Emerson|runes", "Emerson|letters"):
        r = rows[key]
        name, s = key.split("|")
        b1 = base[name].hist[s][0] / base[name].hist[s].sum()
        q = r["fit_multi"]["q"]
        qa = r["fit_all"]["q"]
        say(f"  {key}: baseline 1-rune share {100 * b1:.2f}% -> {n1 * b1:.1f} words expected without insertion; "
            f"multi convention (q {q:.3f}) expects {r['e1']:.1f} (observed 83, z {(83 - r['e1']) / np.sqrt(r['e1']):+.2f}); "
            f"all-words convention (q {qa:.3f}) expects {n1 * b1 * (1 - qa):.1f} "
            f"(z {(83 - n1 * b1 * (1 - qa)) / np.sqrt(n1 * b1 * (1 - qa)):+.2f}); "
            f"z for the multi convention with the baseline's own noise (variance x (1 + n1/N2), N2 = "
            f"{int(base[name].hist[s].sum())}): {(83 - r['e1']) / np.sqrt(r['e1'] * (1 + n1 / base[name].hist[s].sum())):+.2f}")

    # ---------------- genre noise: how far apart are English blocks
    say("\n## 3. Genre noise: English blocks against the solved text, and LP2 among them")
    say("Blocks of 2,896 contiguous words (1,000 per corpus) from each corpus: their G against the solved text's histogram, "
        "next to LP2's own two-sample G against it; percentile = share of blocks with G >= LP2's.")
    blk = {}
    for s in ("runes", "letters"):
        gl = two_sample(O1, solved.hist[s], 10, rng)["G"]
        allG, allS = [], []
        say(f"  spelling {s}: LP2 G {gl:.1f}, LP2 2-rune share {100 * O1[1] / n1:.2f}%")
        for name, c in cors.items():
            h = c.block_hists(s, n1, 1000, rng)
            G = g2(h, np.broadcast_to(solved.hist[s], h.shape))
            sh = h[:, 1] / n1
            allG.append(G)
            allS.append(sh)
            say(f"    {name:20s} block 2-rune share {100 * sh.mean():5.2f}% (2.5-97.5: {100 * np.percentile(sh, 2.5):.2f}-"
                f"{100 * np.percentile(sh, 97.5):.2f}); block G vs solved median {np.median(G):6.1f} "
                f"[2.5-97.5: {np.percentile(G, 2.5):.1f}-{np.percentile(G, 97.5):.1f}]; share of blocks with G >= LP2 "
                f"{(G >= gl).mean():.3f}; share with 2-rune <= LP2 {(sh <= O1[1] / n1).mean():.3f}")
        allG = np.concatenate(allG)
        allS = np.concatenate(allS)
        say(f"    ALL 8 corpora pooled: share of blocks with G >= LP2's {(allG >= gl).mean():.3f}; share with 2-rune share "
            f"<= LP2's 15.47%: {(allS <= O1[1] / n1).mean():.4f}")
        blk[s] = dict(G_lp2=gl, frac_G=float((allG >= gl).mean()), frac_s=float((allS <= O1[1] / n1).mean()))
    # LP2 as one more 2,896-word block against the average English histogram (equal weight per corpus)
    for s in ("runes", "letters"):
        ref = np.mean([c.hist[s] / c.hist[s].sum() for c in cors.values()], axis=0)
        refc = ref * 1e6
        gl = float(g2(O1, refc))
        allG = []
        for name, c in cors.items():
            h = c.block_hists(s, n1, 1000, rng)
            allG.append(g2(h, np.broadcast_to(refc, h.shape)))
        allG = np.concatenate(allG)
        say(f"  LP2 against the equal-weight average of the 8 English histograms [{s}] (2-rune {100 * ref[1]:.1f}%): "
            f"G {gl:.1f}; 8,000 English 2,896-word blocks: median {np.median(allG):.1f}, 95th pct {np.percentile(allG, 95):.1f}, "
            f"99th {np.percentile(allG, 99):.1f}; share of blocks with G >= LP2's {(allG >= gl).mean():.4f}")
        blk[s + "_avg"] = dict(G=gl, frac=float((allG >= gl).mean()))
    say("Blocks of 739 words (the size of the solved text), 1,000 per corpus: two-sample G of LP2 against each block, "
        "and the fitted q with that block as the baseline; the solved text's own value for comparison.")
    for s in ("runes", "letters"):
        gsol = two_sample(O1, solved.hist[s], 10, rng)["G"]
        qsol = fit_batch(O1[None], solved.hist[s][None])[0][0]
        Gs, qs, sh = [], [], []
        for name, c in cors.items():
            h = c.block_hists(s, 739, 1000, rng)
            Gs.append(g2(np.broadcast_to(O1, h.shape), h))
            qs.append(fit_batch(np.broadcast_to(O1, h.shape).copy(), h)[0])
            sh.append(h[:, 1] / 739)
        Gs = np.concatenate(Gs)
        qs = np.concatenate(qs)
        sh = np.concatenate(sh)
        say(f"  {s}: solved text G {gsol:.1f}, q {qsol:.3f}.  739-word English blocks (8000): G median {np.median(Gs):.1f} "
            f"[2.5-97.5: {np.percentile(Gs, 2.5):.1f}-{np.percentile(Gs, 97.5):.1f}], share with G <= solved's "
            f"{(Gs <= gsol).mean():.3f}; q median {np.median(qs):.3f} [{np.percentile(qs, 2.5):.3f}-{np.percentile(qs, 97.5):.3f}]; "
            f"2-rune share median {100 * np.median(sh):.1f}% [{100 * np.percentile(sh, 2.5):.1f}-{100 * np.percentile(sh, 97.5):.1f}]")
        blk[s + "739"] = dict(G_solved=float(gsol), q_solved=float(qsol), q_med=float(np.median(qs)),
                              q_lo=float(np.percentile(qs, 2.5)), q_hi=float(np.percentile(qs, 97.5)),
                              frac_G_le=float((Gs <= gsol).mean()))

    # ---------------- function words
    say("\n## 4. Where the 2-rune deficit sits: word identity in the solved text and in Emerson")
    import collections
    FW = ["OF", "TO", "IN", "IS", "IT", "BE", "AN"]
    cnt_r = collections.Counter(w for w, r in sw if r == 2)
    cnt_l = collections.Counter(w for w, r in sw if len(w) == 2)
    scale = n1 / len(sw)
    for lab, cnt in (("runes (digraphs one rune)", cnt_r), ("letters", cnt_l)):
        tot = sum(cnt.values())
        say(f"  Solved text, 2-{'rune' if lab.startswith('r') else 'letter'} words: {tot} of {len(sw)} "
            f"({100 * tot / len(sw):.1f}%) = {tot * scale:.0f} per 2,896 words; LP2 has 448.")
        cum = 0
        top = cnt.most_common(12)
        say("    type: n (share of the 2-unit bin; expected count at 2,896 words): "
            + "; ".join(f"{w} {c} ({100 * c / tot:.0f}%; {c * scale:.0f})" for w, c in top))
        fwn = sum(cnt.get(w, 0) for w in FW)
        say(f"    the seven named function words OF TO IN IS IT BE AN: {fwn} = {100 * fwn / tot:.1f}% of the bin, "
            f"{100 * fwn / len(sw):.1f}% of all words ({fwn * scale:.0f} per 2,896)")
    # same in Emerson (letters/runes)
    em = cors["Emerson"].words
    ne = len(em)
    cr = collections.Counter(w for w in em if rune_len(w) == 2)
    cl = collections.Counter(w for w in em if len(w) == 2)
    for lab, cnt in (("runes", cr), ("letters", cl)):
        tot = sum(cnt.values())
        fwn = sum(cnt.get(w, 0) for w in FW)
        say(f"  Emerson, 2-unit words ({lab}): {tot} of {ne} ({100 * tot / ne:.1f}%); top: "
            + "; ".join(f"{w} {100 * c / tot:.0f}%" for w, c in cnt.most_common(8))
            + f"; seven function words {100 * fwn / tot:.1f}% of the bin, {100 * fwn / ne:.1f}% of all words")
    # THE spelled as 2 runes
    sthe = sum(1 for w, r in sw if w == "THE")
    say(f"  'THE' is {sthe} of {len(sw)} solved words ({100 * sthe / len(sw):.1f}%), 2 runes but 3 letters: "
        f"in the rune spelling it alone gives {sthe * scale:.0f} of the 2-rune words per 2,896.")
    # deficit under hypotheses: remove classes of 2-unit words from the baseline, refit the unfitted two-sample G
    say("  Deficit hypotheses against the solved-text baseline (what the 2-unit bin would have to lose; two-sample G "
        "to LP2, df 11, MC p; share of 2-unit tokens removed):")
    for lab, s, cnt in (("runes", "runes", cnt_r), ("letters", "letters", cnt_l)):
        h = solved.hist[s].copy()
        tot = sum(cnt.values())
        variants = {"full baseline": 0,
                    "without THE (runes only)": cnt.get("THE", 0) if s == "runes" else 0,
                    "without the seven function words": sum(cnt.get(w, 0) for w in FW),
                    "without the 12 commonest 2-unit types": sum(c for _, c in cnt.most_common(12))}
        for vn, rm in variants.items():
            hh = h.copy()
            hh[1] -= rm
            ts = two_sample(O1, hh, RMC, rng)
            say(f"    {lab:7s} {vn:38s}: 2-unit share {100 * hh[1] / hh.sum():5.1f}%, G {ts['G']:6.1f}, p {ts['p_mc']:.4f}")
    say("  Deficit decomposition (letters, solved-text baseline): LP2 2-letter-equivalent count 448 vs "
        f"{cnt_l and sum(cnt_l.values()) * scale:.0f} expected; the shortfall of "
        f"{sum(cnt_l.values()) * scale - 448:.0f} words equals {100 * (sum(cnt_l.values()) * scale - 448) / (sum(cnt_l.values()) * scale):.0f}% "
        "of the bin, i.e. it could be removed from the seven function words alone "
        f"({sum(cnt_l.get(w, 0) for w in FW) * scale:.0f} per 2,896), but LP2 gives no word identities, so which words "
        "are missing is not observable.")

    # ---------------- controls
    say("\n## 5. Controls")
    ctl = {}

    def run_control(label, make, multi=True, Rci=RC, Rp=RC):
        qs, cov, acc = [], 0, 0
        ps = []
        for _ in range(NCTL):
            o1, o2 = make()
            f = fit(o1, o2, Rci, Rp, rng, multi)
            qs.append(f["q"])
            cov += (f["lo"] <= 0.45 <= f["hi"])
            acc += f["p"] > 0.05
            ps.append(f["p"])
        qs = np.array(qs)
        res = dict(mean_q=float(qs.mean()), sd_q=float(qs.std()), coverage=cov / NCTL, accept=acc / NCTL,
                   p_median=float(np.median(ps)))
        ctl[label] = res
        say(f"  {label}: q-hat mean {qs.mean():.3f} sd {qs.std():.3f} (true 0.45); CI covers 0.45 in {cov}/{NCTL}; "
            f"model accepted (p > 0.05) in {acc}/{NCTL}; median fit p {np.median(ps):.3f}")

    say("Positive controls (pseudo-LP2 of 2,896 words, +1 rune at q 0.45 in multi-rune words; fit CI and p use "
        f"{RC} bootstrap draws each; {NCTL} pseudo texts):")
    for s in ("runes", "letters"):
        run_control(f"P1 solved text -> solved text baseline [{s}] (brief's design; baseline sample shared with the source)",
                    lambda s=s: (pseudo_insert(solved.hist[s], n1, 0.45, rng), solved.hist[s]))
    for s in ("runes", "letters"):
        run_control(f"P2 Walden + q 0.45 -> Emerson baseline [{s}] (independent texts)",
                    lambda s=s: (pseudo_insert(cors["Walden"].hist[s], n1, 0.45, rng), cors["Emerson"].hist[s]))
    wl = {s: solved.lens[s] for s in ("runes", "letters")}

    def p3(s):
        idx = rng.permutation(len(sw))
        a, b = idx[:len(sw) // 2], idx[len(sw) // 2:]
        return pseudo_insert(hist(wl[s][a]), n1, 0.45, rng), hist(wl[s][b])
    for s in ("runes", "letters"):
        run_control(f"P3 half of solved text + q 0.45 -> other half as baseline [{s}] (independent, 369/370 words)",
                    lambda s=s: p3(s))

    say(f"Null controls ({NCTL} draws unless stated; two-sample MC p with {RMC // 10} draws each):")
    NR = RMC // 10
    for s in ("runes", "letters"):
        # N1: Emerson pseudo-LP2, no insertion, vs solved text (the brief's null)
        ps, qh = [], []
        for _ in range(NCTL):
            o = rng.multinomial(n1, cors["Emerson"].hist[s] / cors["Emerson"].hist[s].sum()).astype(float)
            ps.append(two_sample(o, solved.hist[s], NR, rng)["p_mc"])
            qh.append(fit_batch(o[None], solved.hist[s][None])[0][0])
        ps = np.array(ps)
        say(f"  N1 Emerson pseudo-LP2 (no insertion) vs solved text [{s}]: rejects at 0.05 in {int((ps < 0.05).sum())}/{NCTL} "
            f"(nominal 5%); median p {np.median(ps):.4f}; fitted q on the same: mean {np.mean(qh):.3f}")
        ctl[f"N1_{s}"] = dict(reject=float((ps < 0.05).mean()), p_median=float(np.median(ps)), q_mean=float(np.mean(qh)))
        # N2a: Emerson both independent
        ps = []
        for _ in range(NCTL * 2):
            pe = cors["Emerson"].hist[s] / cors["Emerson"].hist[s].sum()
            a = rng.multinomial(n1, pe).astype(float)
            b = rng.multinomial(739, pe).astype(float)
            ps.append(two_sample(a, b, NR, rng)["p_mc"])
        ps = np.array(ps)
        ks = kstest(ps, "uniform").pvalue
        say(f"  N2a Emerson 2,896 vs independent Emerson 739 [{s}] ({NCTL * 2} draws): rejects at 0.05 in "
            f"{(ps < 0.05).mean():.3f}; KS p of uniformity {ks:.2f}")
        ctl[f"N2a_{s}"] = dict(reject=float((ps < 0.05).mean()), ks=float(ks))
        # N2b: the literal solved text against itself (pseudo from the baseline histogram, baseline shared)
        ps = []
        ps_c = []
        for _ in range(NCTL * 2):
            ps_ = solved.hist[s] / solved.hist[s].sum()
            a = rng.multinomial(n1, ps_).astype(float)
            ps.append(two_sample(a, solved.hist[s], NR, rng)["p_mc"])
            b = rng.multinomial(len(sw), ps_).astype(float)
            ps_c.append(two_sample(a, b, NR, rng)["p_mc"])
        ps, ps_c = np.array(ps), np.array(ps_c)
        say(f"  N2b solved text against itself [{s}] ({NCTL * 2} draws): (i) pseudo from the solved histogram vs the SAME "
            f"739-word baseline: rejects at 0.05 in {(ps < 0.05).mean():.3f}, KS p {kstest(ps, 'uniform').pvalue:.2g} "
            f"(shared sample: conservative by design); (ii) pseudo vs a fresh 739-word resample: rejects "
            f"{(ps_c < 0.05).mean():.3f}, KS p {kstest(ps_c, 'uniform').pvalue:.2f}")
        ctl[f"N2b_{s}"] = dict(reject_shared=float((ps < 0.05).mean()), reject_fresh=float((ps_c < 0.05).mean()),
                               ks_fresh=float(kstest(ps_c, 'uniform').pvalue))
    # N3: fit null: pseudo from the baseline with q = 0 should fit q near 0
    say("  N3 (fit under q = 0): pseudo-LP2 from the solved text without insertion, solved text baseline, "
        "q-hat should sit near 0:")
    for s in ("runes", "letters"):
        qs = []
        for _ in range(NCTL):
            o1_ = pseudo_insert(solved.hist[s], n1, 0.0, rng)
            qs.append(fit_batch(o1_[None], solved.hist[s][None])[0][0])
        say(f"    [{s}] q-hat mean {np.mean(qs):.3f}, share exactly 0: {np.mean(np.array(qs) == 0):.2f} "
            f"(boundary bias: the fit cannot go below 0)")

    # ---------------- summary
    say("\n## 6. Reading")
    r_sl = rows["Solved text|letters"]
    r_sr = rows["Solved text|runes"]
    say(f"  Against Cicada's own text in letters: G {r_sl['ts']['G']:.1f} (df 11), MC p {r_sl['ts']['p_mc']:.4f} (asymptotic "
        f"{r_sl['ts']['p_asym']:.1e}); in runes G {r_sr['ts']['G']:.1f}, MC p {r_sr['ts']['p_mc']:.1e}.")
    say(f"  Fitted q: solved/letters {r_sl['fit_multi']['q']:.3f} [{r_sl['fit_multi']['lo']:.3f}, {r_sl['fit_multi']['hi']:.3f}], "
        f"solved/runes {r_sr['fit_multi']['q']:.3f} [{r_sr['fit_multi']['lo']:.3f}, {r_sr['fit_multi']['hi']:.3f}], "
        f"Emerson/runes {rows['Emerson|runes']['fit_multi']['q']:.3f} [{rows['Emerson|runes']['fit_multi']['lo']:.3f}, "
        f"{rows['Emerson|runes']['fit_multi']['hi']:.3f}].")
    say(f"\nWall {time.time() - t0:.0f} s, process CPU {time.process_time() - cpu0:.0f} s.")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "summary.txt" if not QUICK else "summary_quick.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(LINES) + "\n")
    with open(os.path.join(OUT, "results.json" if not QUICK else "results_quick.json"), "w", newline="\n") as f:
        json.dump(dict(rows=rows, controls=ctl, blocks=blk), f, indent=1, default=float)


if __name__ == "__main__":
    main()
