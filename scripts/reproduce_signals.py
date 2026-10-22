"""Recompute the numbers in docs/FINDINGS.md section 1 and print each next to the claimed value (PASS / FAIL).

    python scripts/fetch_data.py                 # once
    python scripts/reproduce_signals.py          # 1-4 minutes of CPU, below-normal priority
    python scripts/reproduce_signals.py --fast   # skips the mechanism simulation, fewer null draws (about 30 s)

Exit status 1 if any check FAILs. Reuses the phase code (stats, phase54_lag6_dissect, phase57_mechanism,
discord_cumulative_check, prime_sums, wordlen, families/fam_data, mech25/measure); only the glue is new.
Null draws are fewer than in the phases (stated per line); tolerances are wide enough for that, not wider.
Not recomputed: the P 0.005-0.013 over the whole relation search (only the 812 affine lag-6 forms are searched here),
"uniform over runes" for doublets, the ID3 product 1259 x 1031 x 1229 (a file fact), and the solved-page control behind
the prime clause sums beyond the shuffle null.
"""
import argparse
import contextlib
import io
import math
import os
import re
import sys
import types

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "work")
for p in (WORK, os.path.join(WORK, "families"), os.path.join(WORK, "mech25")):
    sys.path.insert(0, p)
import discord_cumulative_check as dcc  # noqa: E402
import fam_data as D  # noqa: E402
import lp  # noqa: E402
import measure as M  # noqa: E402
import phase54_lag6_dissect as p54  # noqa: E402
import phase57_mechanism as p57  # noqa: E402
import prime_sums as ps  # noqa: E402
import stats  # noqa: E402
import wordlen  # noqa: E402

ROWS = []


def check(name, claimed, got, tol, fmt="{:.2f}", note=""):
    """PASS if |got - claimed| <= tol"""
    ok = abs(got - claimed) <= tol
    ROWS.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name:58s} claimed {fmt.format(claimed):>9s}  got {fmt.format(got):>9s}  (tol {tol:g}){'  ' + note if note else ''}", flush=True)


def check_min(name, bound, got, note=""):
    ok = got >= bound
    ROWS.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name:58s} claimed >= {bound:g}  got {got:.3g}{'  ' + note if note else ''}", flush=True)


def lag6_pairs(c, start, sid):
    i = np.arange(len(c) - 6)
    wid = np.cumsum(start) - 1
    return i, sid[i] == sid[i + 6], wid[i] == wid[i + 6]


def section_doublets(c, start, sid, rng, draws):
    n = len(c)
    j = np.arange(1, n)
    same = sid[j] == sid[j - 1]
    d = (c[j] == c[j - 1]) & same
    f = np.bincount(c, minlength=29) / n
    ind, gap = int((d & ~start[j]).sum()), int((d & start[j]).sum())
    print("-- doublets (adjacent equal runes, same section, words as lp.word_spans cuts them)")
    check("doublets, total", 86, ind + gap, 0, "{:.0f}")
    check("doublet rate, % of adjacent pairs", 0.66, 100 * (ind + gap) / same.sum(), 0.02)
    check("random-text doublet rate, % (sum of squared frequencies)", 3.45, 100 * float((f * f).sum()), 0.05)
    check("share of would-be repeats prevented, %", 81, 100 * (1 - (ind + gap) / same.sum() / float((f * f).sum())), 1)
    # 2026-10-22: the discord check now merges bare line / page wraps like lp.word_spans (it used to count them as gaps: 26, 25.5%)
    segs = lp.load_segments()
    tot_gap = sum(dcc.doublets(segs[i])[1] for i in dcc.LP2)
    tot_in = sum(dcc.doublets(segs[i])[0] for i in dcc.LP2)
    pairs = sum(len(dcc.words(segs[i])) - 1 for i in dcc.LP2)
    allp = sum(len(lp.runes_of(segs[i])) - 1 for i in dcc.LP2)
    check("doublets across word gaps (discord_cumulative_check), of 86", 23, tot_gap, 0, "{:.0f}", f"in-word {tot_in}")
    check("gap share of adjacent pairs, % (same word definition)", 22.3, 100 * pairs / allp, 0.5)
    check("doublets across word gaps (lp.word_spans), of 86", 23, gap, 0, "{:.0f}", f"in-word {ind}")


def flat(c, start, sid, rng, draws):
    print(f"-- flatness: unigram / bigram chi2 and max lag-2..12 |z| against {draws} within-section rune shuffles")
    real = p57.measure(c.astype(np.int16), start, sid)
    nulls = []
    for _ in range(draws):
        x = c.copy()
        for s in np.unique(sid):
            m = np.flatnonzero(sid == s)
            x[m] = rng.permutation(x[m])
        nulls.append(p57.measure(x.astype(np.int16), start, sid))
    bi = np.array([r["bi"] for r in nulls])
    check("bigram chi2 (doublets excluded), LP2", 786, real["bi"], 40, "{:.0f}")
    check("bigram chi2, null mean (claimed 760 +- 45)", 760, bi.mean(), 20, "{:.0f}", f"null sd {bi.std():.0f}")
    check("bigram chi2 sd under the null", 45, bi.std(), 20, "{:.0f}")
    for k, lab in (("uni", "unigram chi2"), ("bi", "bigram chi2"), ("lagz", "max |z| over lags 2-12")):
        v = np.array([r[k] for r in nulls])
        pv = (1 + (v >= real[k]).sum()) / (draws + 1)
        ROWS.append(pv > 0.01)
        print(f"{'PASS' if pv > 0.01 else 'FAIL'}  flat: {lab:50s} LP2 {real[k]:8.2f}  null {v.mean():8.2f}  one-sided P {pv:.3f} (> 0.01 required)", flush=True)


def lag6(draws):
    print(f"-- lag-6 relation c' = 24 - 2c (mod 29), within words, {draws} within-word shuffles (phase 54 used 10,000)")
    rng = np.random.default_rng(54)
    C, W, P, L, SEC, PG = p54.load(stats.UNSOLVED)
    i = p54.sites(C, W)
    h = int(p54.hits(C, i).sum())
    check("within-word lag-6 pairs", 1290, len(i), 0, "{:.0f}")
    check("hits", 80, h, 0, "{:.0f}")
    check("expected under independence", 44.5, p54.expected_indep(C, i), 0.1, "{:.1f}")
    tot = []
    for _ in range(draws // 250):
        X = p54.shuffle_batch(C, W, 250, rng)
        tot.append((X[:, i + 6] == (24 - 2 * X[:, i]) % 29).sum(1))
    tot = np.concatenate(tot)
    z = (h - tot.mean()) / tot.std()
    check("shuffle-null mean", 45.7, tot.mean(), 1.5, "{:.1f}")
    check("z against the shuffle null", 5.3, z, 0.8, "{:+.2f}", f"null sd {tot.std():.2f}")
    check("excess per within-word pair", 0.027, (h - tot.mean()) / len(i), 0.004, "{:.4f}")
    # across gaps (same section, different word): no excess
    c, st, sid = D.lp2()
    ii, s6, inw = lag6_pairs(c, st, sid)
    x = s6 & ~inw
    a, b = c[ii][x], c[ii + 6][x]
    f = np.bincount(c, minlength=29) / len(c)
    exp = x.sum() * float(sum(f[k] * f[(24 - 2 * k) % 29] for k in range(29)))
    got = int((b == (24 - 2 * a) % 29).sum())
    zx = (got - exp) / math.sqrt(exp)
    ROWS.append(abs(zx) < 2)
    print(f"{'PASS' if abs(zx) < 2 else 'FAIL'}  across word gaps: hits {got} of {x.sum()} pairs, independence {exp:.1f}, z {zx:+.2f} (claimed: zero excess, |z| < 2 required)", flush=True)
    # best of all 812 affine forms at lag 6, within words, against the same shuffle null (the 'corrected for relations searched' part, one lag only)
    def best(Cm):
        a_, b_ = Cm[i], Cm[i + 6]
        return max(int(np.bincount((b_ - m * a_) % 29, minlength=29).max()) for m in range(1, 29))
    real_best = best(C)
    nb = np.array([best(p54.shuffle_batch(C, W, 1, rng)[0]) for _ in range(draws // 2)])
    pv = (1 + (nb >= real_best).sum()) / (len(nb) + 1)
    ROWS.append(pv <= 0.013)
    print(f"{'PASS' if pv <= 0.013 else 'FAIL'}  max over 812 affine forms at lag 6: LP2 {real_best}, null mean {nb.mean():.1f}, P {pv:.4f} (claimed P 0.005-0.013 over a wider search; <= 0.013 required)", flush=True)
    # excess = prevented-doublet rate
    f2 = float((f * f).sum())
    n = len(c) - 1
    print(f"      prevented-doublet rate {(f2 - 86 / n):.4f} per pair, lag-6 excess rate {(h - tot.mean()) / len(i):.4f} per pair (claimed equal)")
    return C, W, P, L, SEC, i


def sections(C, SEC, i, W):
    """phase 54 vs phase 57 per-section lag-6 counts, both statistics"""
    h = p54.hits(C, i)
    n = np.bincount(SEC[i], minlength=9)
    k = np.bincount(SEC[i][h], minlength=9)
    ex = n * h.sum() / n.sum()
    m = n > 0
    chi57 = float(((k - ex)[m] ** 2 / ex[m]).sum())
    print("-- per-section lag-6 (phase 54 vs phase 57 statistic)")
    print("      hits/sites per section 0.7..0.15: " + ", ".join(f"{a}/{b}" for a, b in zip(k, n)))
    check("phase 57 statistic (chi2 vs equal rate per site)", 1.4, chi57, 0.2, "{:.2f}")
    # phase 54: expectation = per-section mean of the within-word shuffle null (composition aware)
    rng = np.random.default_rng(54)
    X = p54.shuffle_batch(C, W, 400, rng)
    H = X[:, i + 6] == (24 - 2 * X[:, i]) % 29
    mu = np.array([H[:, SEC[i] == s].sum(1).mean() for s in range(9)])
    chi54 = float(((k - mu)[m] ** 2 / mu[m]).sum())
    chi54null = np.array([float((((np.array([H[b, SEC[i] == s].sum() for s in range(9)]) - mu)[m]) ** 2 / mu[m]).sum()) for b in range(400)])
    check("phase 54 statistic (chi2 vs section-composition expectation)", 28.75, chi54, 4, "{:.1f}", f"null mean {chi54null.mean():.1f}")
    print("      per-section expected hits: equal-rate " + ", ".join(f"{x:.1f}" for x in ex) + " | composition-aware " + ", ".join(f"{x:.1f}" for x in mu))


def wordlen_checks():
    print("-- word lengths")
    c, st, sid = D.lp2()
    obs = M.hist(st)
    lens = np.diff(np.append(np.flatnonzero(st), len(st)))
    check("2-rune words, % of LP2's words", 15.5, 100 * (lens == 2).mean(), 0.05)
    check("one-rune words in LP2", 83, int((lens == 1).sum()), 1, "{:.0f}", "registry ai-oracle says 83; seploss table 2.9% = 84")
    words = wordlen.emerson_words()
    em = [x for x in (len(lp.word_to_key(w.replace("IO", "IA"))) for w in words) if x]
    check("2-rune words, English (Emerson) in runes, %", 27.0, 100 * np.mean(np.array(em) == 2), 1)
    check("2-rune words, English in letters, %", 20.0, 100 * np.mean(np.array([len(w) for w in words]) == 2), 1)
    o = wordlen.hist(lens)
    g, df, pv = wordlen.g_test(o, wordlen.hist(em))
    check("log10 p of LP2 lengths against English runes (about 1e-45)", -45, math.log10(pv), 3, "{:.1f}")
    base = wordlen.hist(em) / wordlen.hist(em).sum()
    best = None
    for r in np.linspace(0, 0.8, 161):
        ins = base.copy(); ins[0] = 0
        q = base - r * ins
        q[1:] += r * ins[:-1]; q[-1] += r * ins[-1]
        gg = wordlen.g_test(o, q, fitted=1)[0]
        if best is None or gg < best[1]:
            best = (r, gg)
    check("best fit: extra rune in x% of multi-rune words", 42, 100 * best[0], 3, "{:.0f}", f"G {best[1]:.1f}")


def mechanism(reps):
    print(f"-- R4 mechanism fit (phase 57 code, rule R4 only, {reps} replicates instead of 500)")
    buf = io.StringIO()
    old = sys.argv
    sys.argv = ["phase57", "--reps", str(reps), "--only", "R4"]
    try:
        with contextlib.redirect_stdout(buf):
            p57.main()
    finally:
        sys.argv = old
    m = re.search(r"R4 [^\n]*chi2\s+([\d.]+)\s+P\s+([\d.]+)", buf.getvalue())
    P = float(m.group(2))
    check("combined-chi2 P of R4", 0.64, P, 0.2, "{:.2f}", f"SE about {math.sqrt(0.64 * 0.36 / reps):.2f}; fewer corpora than the phase if work/ref/corpora is missing")


def verifiers(shuffles, tol):
    print(f"-- verifiers on the solved pages")
    segs = lp.load_segments()
    import random
    rng = random.Random(1033)
    rows, mp, vp = [], 0.0, 0.0
    for i, (title, fn) in lp.KNOWN.items():
        plain = fn(lp.runes_of(segs[i]))
        rows += [(i, len(u), ps.gsum(u), "".join(lp.LATIN[j] for j in u)) for u in ps.units(segs[i], plain, "clause")]
    body = [r for r in rows if not (r[3] in ps.LABELS or r[1] < 6 or r[3].startswith("SHADOWS"))]
    for i in sorted({r[0] for r in body}):
        plain = lp.KNOWN[i][1](lp.runes_of(segs[i]))
        a, b, _, _ = ps.shuffle_null([r[1] for r in body if r[0] == i], plain, rng, shuffles)
        mp += a; vp += b
    obs = sum(ps.IS_P[r[2]] for r in body)
    check("body clauses", 76, len(body), 0, "{:.0f}")
    check("clauses with a prime Gematria sum", 36, obs, 0, "{:.0f}")
    check("z against the shuffle null", 7.9, (obs - mp) / vp ** .5, tol, "{:+.1f}", f"{shuffles} shuffles per section (prime_sums used 500)")
    one = []
    for i, (title, fn) in lp.KNOWN.items():
        plain = fn(lp.runes_of(segs[i]))
        one += [lp.LATIN[plain[a]] for _, a, b in lp.word_spans(segs[i], plain) if b - a == 1]
    check("one-rune words of the solved pages", 27, len(one), 0, "{:.0f}")
    check("... that are A or I", 27, sum(x in ("A", "I") for x in one), 0, "{:.0f}")


def main(fast=False):
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    elif hasattr(os, "nice"):
        os.nice(10)
    ROWS.clear()
    c, st, sid = D.lp2()
    assert len(c) == 12956
    rng = np.random.default_rng(3301)
    section_doublets(c, st, sid, rng, 0)
    flat(c, st, sid, rng, 60 if fast else 200)
    C, W, P, L, SEC, i = lag6(1000 if fast else 3000)
    sections(C, SEC, i, W)
    wordlen_checks()
    if not fast:
        mechanism(100)
    else:
        print("-- R4 mechanism fit: skipped (--fast)")
    verifiers(40 if fast else 500, 1.2 if fast else 0.6)
    bad = ROWS.count(False)
    print(f"\n{len(ROWS) - bad} PASS, {bad} FAIL" + ("  (--fast: mechanism skipped, fewer draws)" if fast else ""))
    return bad


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true")
    sys.exit(1 if main(ap.parse_args().fast) else 0)
