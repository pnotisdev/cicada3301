"""Phase 64: is LP2's clause structure authored like LP1's? See work/log/phase64_clause_structure.md.

    python work/phase64_clause_structure.py [--perm 5000] [--wins 300]     # -> results/analysis/phase64_clause_structure.txt

Clause = the runes between two of the marks '.' (clause / sentence end) and '&' (paragraph end); '%', '\\n' and numerals are not clause marks (a numeral cuts a word,
a bare line / page break does not). LP1 = segments 0-6 (the solved sections' ciphertext keeps the plaintext's marks), LP2 = segments 7-9 and 11-15 (segment 10, the caption, left out).
Reference prose: the phase 22/25 corpora spelled as `fam_data.english` does (greedy digraphs, IO -> IA), punctuation as clause marks in two schemes:
'sentence' = . ! ?  and  'clause' = . , ; : ! ?  (a paragraph is a blank-line block); windows of LP1's / LP2's rune count.
"""
import argparse
import os
import re
import sys
import time
from math import comb

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "families"))
import fam_data as D  # noqa: E402
import lp  # noqa: E402

LP1, LP2 = [0, 1, 2, 3, 4, 5, 6], [7, 8, 9, 11, 12, 13, 14, 15]
OUT = []
NAMES = ["mean clause runes", "CV clause runes", "mean words / clause", "share 1-word clauses", "clauses / paragraph", "last word - mean word (runes)", "share odd rune count", "median clause runes"]


def say(s=""):
    print(s, flush=True)
    OUT.append(s)


def clauses(toks):
    """-> (list of (runes, [word lengths], marks_at_line_end), list of clause counts per paragraph); toks may be pseudo-tokens from prose"""
    cl, par, words, cur, nclause, n = [], [], [], 0, 0, len(toks)
    for i, t in enumerate(toks):
        if isinstance(t, int):
            cur += 1
            continue
        if t in ("\n", "%"):
            continue
        if cur:
            words.append(cur)
            cur = 0
        if t in (".", "&"):
            if words:
                nxt = toks[i + 1] if i + 1 < n else None
                cl.append((sum(words), words, nxt in ("\n", "%")))
                words = []
                nclause += 1
            if t == "&" and nclause:
                par.append(nclause)
                nclause = 0
    if cur:
        words.append(cur)
    if words:
        cl.append((sum(words), words, False))
        nclause += 1
    if nclause:
        par.append(nclause)
    return cl, par


def summary(cl, par):
    L = np.array([c[0] for c in cl], float)
    W = np.array([len(c[1]) for c in cl], float)
    allw = np.concatenate([c[1] for c in cl]).astype(float)
    last = np.array([c[1][-1] for c in cl], float)
    return np.array([L.mean(), L.std() / L.mean(), W.mean(), (W == 1).mean(), np.mean(par), last.mean() - allw.mean(), (L % 2 == 1).mean(), np.median(L)])


def lp_clauses(segs):
    S = lp.load_segments()
    toks = []
    for i in segs:
        toks += S[i]
        if not toks or toks[-1] != "&":
            toks.append("&")
    return clauses(toks)


def prose_tokens(scheme):
    """per corpus: pseudo-token list with paragraph starts; the marks of `scheme`"""
    marks = set(".!?") if scheme == "sentence" else set(".,;:!?")
    cache, res = {}, []
    for name in D.CORPORA:
        path = os.path.join(D.WORK, "ref", name)
        if not os.path.exists(path):
            continue
        txt = open(path, encoding="utf-8", errors="ignore").read()
        if "SELF-RELIANCE" in txt:
            txt = txt[txt.index("SELF-RELIANCE"):]
        if "*** START OF" in txt:
            txt = txt.split("*** START OF", 1)[1].split("\n", 1)[1]
        txt = txt.split("*** END OF")[0]
        toks, pstart = [], []
        for par in re.split(r"\n\s*\n", txt):
            pstart.append(len(toks))
            n0 = len(toks)
            for w in re.findall(r"[A-Za-z]+|[.,;:!?]", par):
                if w in marks:
                    if toks and len(toks) > n0 and toks[-1] != ".":
                        toks.append(".")
                    continue
                if not w[0].isalpha():
                    continue
                r = cache.get(w.lower())
                if r is None:
                    r = cache[w.lower()] = lp.word_to_key(w.upper().replace("IO", "IA"))
                if not r:
                    continue
                if len(toks) > n0 and isinstance(toks[-1], int):
                    toks.append(" ")
                elif len(toks) > n0 and toks[-1] == ".":
                    toks.append(" ")
                toks += r
            if len(toks) > n0:
                if toks[-1] == ".":
                    toks.pop()
                toks.append("&")
        res.append((toks, [p for p in pstart if p < len(toks)]))
    return res


def windows(corp, nrunes, k, rng):
    out = []
    while len(out) < k:
        toks, ps = corp[int(rng.integers(len(corp)))]
        s = ps[int(rng.integers(len(ps)))]
        cnt, e = 0, s
        while e < len(toks) and cnt < nrunes:
            cnt += isinstance(toks[e], int)
            e += 1
        if cnt >= nrunes:
            out.append(toks[s:e])
    return out


def perm_diff(cl1, par1, cl2, par2, rng, nperm):
    """two-sided permutation P of the LP1 vs LP2 difference for every statistic: clauses pooled and relabelled (paragraph counts: paragraphs pooled)"""
    obs = summary(cl1, par1) - summary(cl2, par2)
    pool, pp, n1, m1 = cl1 + cl2, par1 + par2, len(cl1), len(par1)
    d = np.zeros((nperm, len(obs)))
    for k in range(nperm):
        ip = rng.permutation(len(pool))
        a = [pool[i] for i in ip[:n1]]
        b = [pool[i] for i in ip[n1:]]
        jp = rng.permutation(len(pp))
        d[k] = summary(a, [pp[i] for i in jp[:m1]]) - summary(b, [pp[i] for i in jp[m1:]])
    return obs, (1 + (np.abs(d) >= np.abs(obs)).sum(0)) / (nperm + 1)


def ks(a, b):
    a, b = np.sort(a), np.sort(b)
    g = np.concatenate([a, b])
    return np.abs(np.searchsorted(a, g, "right") / len(a) - np.searchsorted(b, g, "right") / len(b)).max()


def holm(p):
    o = np.argsort(p)
    adj = np.empty(len(p))
    run = 0.0
    for r, i in enumerate(o):
        run = max(run, (len(p) - r) * p[i])
        adj[i] = min(1.0, run)
    return adj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--perm", type=int, default=5000)
    ap.add_argument("--wins", type=int, default=300)
    a = ap.parse_args()
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    t0 = time.process_time()
    rng = np.random.default_rng(64)
    c1, p1 = lp_clauses(LP1)
    c2, p2 = lp_clauses(LP2)
    r1, r2 = sum(c[0] for c in c1), sum(c[0] for c in c2)
    say("# Phase 64: clause structure of LP2 against LP1 and ordinary English (2026-10-23). Nothing in LP2 is solved.")
    say("Clause marks counted: '.' and '&' (paragraph end); '%' and line breaks are not marks; numerals cut words only.")
    say(f"LP1 (segments 0-6): {len(c1)} clauses, {len(p1)} paragraphs, {r1} runes; LP2 (7-9, 11-15): {len(c2)} clauses, {len(p2)} paragraphs, {r2} runes")
    s1, s2 = summary(c1, p1), summary(c2, p2)
    say()
    say("## LP1 vs LP2 (permutation of pooled clauses, two-sided, " + str(a.perm) + " permutations; Holm over the 8 statistics + KS of clause length)")
    obs, p = perm_diff(c1, p1, c2, p2, rng, a.perm)
    kd = ks([c[0] for c in c1], [c[0] for c in c2])
    pk = np.mean([ks(*(lambda s: (s[:len(c1)], s[len(c1):]))(rng.permutation([c[0] for c in c1 + c2]))) >= kd for _ in range(a.perm)])
    pall = np.r_[p, (1 + pk * a.perm) / (a.perm + 1)]
    adj = holm(pall)
    for i, nm in enumerate(NAMES + ["KS clause length"]):
        v1, v2 = (s1[i], s2[i]) if i < 8 else (kd, kd)
        say(f"  {nm:30s} LP1 {v1:8.3f}  LP2 {v2:8.3f}  P {pall[i]:.4f}  Holm {adj[i]:.4f}" if i < 8 else f"  {nm:30s} D {kd:.3f}  P {pall[i]:.4f}  Holm {adj[i]:.4f}")
    le1, le2 = np.mean([c[2] for c in c1]), np.mean([c[2] for c in c2])
    lw1 = sum(1 for t in [x for i in LP1 for x in lp.load_segments()[i]] if t == "\n") / max(1, sum(1 for t in [x for i in LP1 for x in lp.load_segments()[i]] if t == " "))
    say(f"  share of clause marks directly before a line / page break: LP1 {le1:.3f}, LP2 {le2:.3f} (line breaks per word space: LP1 {lw1:.3f})")
    # bootstrap CIs of the clause-level means
    say("  bootstrap 95% intervals (clauses resampled): mean clause runes LP1 [{:.1f}, {:.1f}], LP2 [{:.1f}, {:.1f}]".format(
        *np.percentile([np.mean([c1[i][0] for i in rng.integers(0, len(c1), len(c1))]) for _ in range(2000)], [2.5, 97.5]),
        *np.percentile([np.mean([c2[i][0] for i in rng.integers(0, len(c2), len(c2))]) for _ in range(2000)], [2.5, 97.5])))
    say("  clause lengths (runes) LP1: " + " ".join(str(c[0]) for c in c1))
    say("  clause length histogram LP2 (bins 1-9, 10-19, ..., 100+): " + str(np.histogram([c[0] for c in c2], bins=[1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 10 ** 6])[0].tolist()))
    say("  clause length histogram LP1 (same bins):                " + str(np.histogram([c[0] for c in c1], bins=[1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 10 ** 6])[0].tolist()))
    say()
    say("## Ordinary English prose in runes (phase 22/25 corpora): windows of LP1's and LP2's rune count; z and percentile of LP1 / LP2 among the windows")
    for scheme in ("sentence", "clause"):
        corp = prose_tokens(scheme)
        w1 = windows(corp, r1, a.wins, rng)
        w2 = windows(corp, r2, a.wins, rng)
        m1 = np.array([summary(*clauses(w)) for w in w1])
        m2 = np.array([summary(*clauses(w)) for w in w2])
        say(f"scheme '{scheme}': prose windows {a.wins} x {r1} runes (mean clauses {np.mean([len(clauses(w)[0]) for w in w1[:50]]):.0f}) and {a.wins} x {r2} runes")
        say(f"  {'statistic':30s} {'prose(LP1-size) mean+-sd':>26s} {'LP1 z':>7s} {'pct':>5s} | {'prose(LP2-size) mean+-sd':>26s} {'LP2 z':>7s} {'pct':>5s}")
        for i, nm in enumerate(NAMES):
            z1, z2 = (s1[i] - m1[:, i].mean()) / (m1[:, i].std() + 1e-9), (s2[i] - m2[:, i].mean()) / (m2[:, i].std() + 1e-9)
            say(f"  {nm:30s} {m1[:, i].mean():10.3f} +- {m1[:, i].std():7.3f} {z1:+7.1f} {100 * (m1[:, i] < s1[i]).mean():5.0f} | {m2[:, i].mean():10.3f} +- {m2[:, i].std():7.3f} {z2:+7.1f} {100 * (m2[:, i] < s2[i]).mean():5.0f}")
    say()
    say("## Trace of prime-sum authoring in clause lengths (step 3)")
    S = lp.load_segments()
    pr = lp.PRIME
    odd, tot, isprime = 0, 0, 0

    def isp(n):
        return n > 1 and all(n % d for d in range(2, int(n ** 0.5) + 1))
    for i in LP1:
        pl = lp.KNOWN[i][1](lp.runes_of(S[i]))
        k, cur = 0, []
        for t in S[i] + ["&"]:
            if isinstance(t, int):
                cur.append(pl[k]); k += 1
            elif t in (".", "&") and cur:
                s = sum(pr[x] for x in cur)
                odd += s % 2; tot += 1; isprime += isp(s); cur = []
    say(f"LP1 decrypted: {tot} clauses, prime-value sum odd in {odd} ({odd / tot:.2f}), prime in {isprime} ({isprime / tot:.2f})")
    corp = prose_tokens("sentence")
    rr = np.random.default_rng(5)
    shares = []
    for w in windows(corp, r1, a.wins, rr):
        n_odd = n = 0
        cur = 0
        for t in w + ["&"]:
            if isinstance(t, int):
                cur += pr[t]
            elif t in (".", "&") and cur:
                n_odd += cur % 2; n += 1; cur = 0
        shares.append(n_odd / max(n, 1))
    say(f"prose windows (sentence marks, LP1 size): share of clauses with odd prime-value sum {np.mean(shares):.2f} +- {np.std(shares):.2f}; LP1 {odd / tot:.2f} -> z {(odd / tot - np.mean(shares)) / np.std(shares):+.1f}")
    k2, n2 = round(s2[6] * len(c2)), len(c2)
    pb = min(1.0, 2 * min(sum(comb(n2, x) for x in range(k2 + 1)), sum(comb(n2, x) for x in range(k2, n2 + 1))) / 2 ** n2)
    say(f"clause rune count odd: LP1 {s1[6]:.2f} (n {len(c1)}), LP2 {s2[6]:.2f} (n {n2}); binomial P(LP2 vs 0.5, two-sided) = {pb:.3f}")
    for tag, cl in (("LP1", c1), ("LP2", c2)):
        L = np.array([c[0] for c in cl])
        out = []
        for m in (2, 3, 5):
            h = np.bincount(L % m, minlength=m)
            ex = len(L) / m
            chi = ((h - ex) ** 2 / ex).sum()
            sim = np.array([(((np.bincount(rng.integers(0, m, len(L)), minlength=m) - ex) ** 2) / ex).sum() for _ in range(5000)])
            out.append(f"mod {m}: {h.tolist()} chi2 {chi:.1f} P {(1 + (sim >= chi).sum()) / 5001:.3f}")
        say(f"  {tag} clause length " + "; ".join(out) + "  (3 moduli: Bonferroni x3)")
    say()
    say(f"CPU time {time.process_time() - t0:.0f} s")
    with open(os.path.join(HERE, "..", "results", "analysis", "phase64_clause_structure.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
