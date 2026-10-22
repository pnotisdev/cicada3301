"""Phase 65: prime clause sums as a language-free score. See work/log/phase65_prime_clause_score.md.

    python work/phase65_prime_clause_score.py [--mc 2000]     # -> results/analysis/phase65_prime_clause_score.txt

Unit = the runes between two clause marks ('.' or '&', as phase 64); a unit is 'prime' when the sum of its runes' Gematria prime values (lp.PRIME) is prime.
"""
import argparse
import glob
import os
import re
import sys
import time

import numpy as np
from scipy.stats import binom

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "families"))
import lp  # noqa: E402
import phase64_clause_structure as P64  # noqa: E402

PRIME = np.array(lp.PRIME)
LP1, LP2 = [0, 1, 2, 3, 4, 5, 6], [7, 8, 9, 11, 12, 13, 14, 15]
OUT = []
SIEVE = np.ones(400000, bool)
SIEVE[:2] = False
for _i in range(2, 633):
    if SIEVE[_i]:
        SIEVE[_i * _i::_i] = False


def say(s=""):
    print(s, flush=True)
    OUT.append(s)


def lp1_units():
    """per segment: list of units (rune index lists of the decrypted text), cut at '.' and '&'"""
    S = lp.load_segments()
    segs = []
    for i in LP1:
        pl = lp.KNOWN[i][1](lp.runes_of(S[i]))
        k, cur, units, par = 0, [], [], []
        for t in S[i] + ["&"]:
            if isinstance(t, int):
                cur.append(pl[k]); k += 1
            elif t in (".", "&") and cur:
                units.append(cur); cur = []
                if t == "&":
                    par.append(len(units))
        segs.append((units, par))
    return segs


def merge(units, k=None, minlen=None):
    out, cur, n = [], [], 0
    for u in units:
        cur += u; n += 1
        if (k and n == k) or (minlen and len(cur) >= minlen):
            out.append(cur); cur, n = [], 0
    if cur:
        out.append(cur)
    return out


def share(units):
    s = np.array([PRIME[u].sum() for u in units])
    return SIEVE[s].mean()


def lengths_of(i):
    return [c[0] for c in P64.clauses(lp.load_segments()[i] + ["&"])[0]]


def pb_tail(ps, k):
    """P(Poisson-binomial >= k)"""
    d = np.zeros(len(ps) + 1)
    d[0] = 1.0
    for p in ps:
        d[1:] = d[1:] * (1 - p) + d[:-1] * p
        d[0] *= 1 - p
    return d[k:].sum()


def kcrit(ps, alpha):
    for k in range(len(ps) + 2):
        if pb_tail(ps, k) <= alpha:
            return k
    return len(ps) + 1


def b_of(L, rng, mc):
    """P(prime sum) of L uniform random runes (a wrong key's decode)"""
    return SIEVE[PRIME[rng.integers(0, 29, (mc, L))].sum(1)].mean()


TOKS = sorted(((t, i) for i, t in enumerate(lp.LATIN)), key=lambda x: -len(x[0]))


def parse_prime(latin, bounds):
    """greedy longest-match parse of the Latin spelling into runes (the spelling is ambiguous: EO / E O, OE, AE, IA, EA, TH, ING; an exact parse search costs 3 s per string),
    then the number of prime units among those ending at the cumulative rune counts `bounds`; the null goes through the same spelling and parse"""
    runes, pos = [], 0
    while pos < len(latin):
        for t, ix in TOKS:
            if latin.startswith(t, pos):
                runes.append(ix); pos += len(t); break
    if not bounds or len(runes) < bounds[-1]:
        return None
    sums = np.add.reduceat(PRIME[runes[:bounds[-1]]], [0] + bounds[:-1])
    return int(SIEVE[sums].sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mc", type=int, default=2000)
    a = ap.parse_args()
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    t0 = time.process_time()
    rng = np.random.default_rng(65)
    say("# Phase 65: prime clause sums as a language-free score (2026-10-23). Nothing in LP2 is solved.")
    say("Unit = runes between clause marks '.' / '&'; prime unit = sum of Gematria prime values (F = 2 ... 109) is prime.")
    # ---------------------------------------------------------------- (1) calibration
    segs = lp1_units()
    allu = [u for units, _ in segs for u in units]
    say()
    say("## (1) LP1 (decrypted, segments 0-6): share of prime units, by unit level; baselines at the same unit lengths")
    prose = P64.prose_tokens("sentence")
    pr_runes = [np.array([t for t in toks if isinstance(t, int)]) for toks, _ in prose]
    levels = {"clause ('.', '&')": allu,
              "2 clauses merged": [u for units, _ in segs for u in merge(units, k=2)],
              "3 clauses merged": [u for units, _ in segs for u in merge(units, k=3)],
              "merged to >= 77 runes": [u for units, _ in segs for u in merge(units, minlen=77)],
              "paragraph": [u for units, par in segs for u in merge(units, k=None, minlen=10 ** 9)]}
    # paragraph units: cut at the paragraph ends recorded
    pu = []
    for units, par in segs:
        prev = 0
        for e in par:
            pu.append([r for u in units[prev:e] for r in u]); prev = e
        if prev < len(units):
            pu.append([r for u in units[prev:] for r in u])
    levels["paragraph"] = pu
    say("level | units | mean runes | LP1 share | uniform-random share (sd) | shuffled-LP1 share (sd) / P(>=) | English prose share (sd)")
    flat = np.array([r for u in allu for r in u])
    for name, us in levels.items():
        L = [len(u) for u in us]
        obs = share(us)
        uni = [SIEVE[[PRIME[rng.integers(0, 29, l)].sum() for l in L]].mean() for _ in range(a.mc // 4)]
        sh = []
        for _ in range(a.mc):
            p = rng.permutation(flat)
            i, s = 0, []
            for l in L:
                s.append(PRIME[p[i:i + l]].sum()); i += l
            sh.append(SIEVE[s].mean())
        pe = []
        for _ in range(a.mc // 4):
            s = []
            for l in L:
                r = pr_runes[int(rng.integers(len(pr_runes)))]
                j = int(rng.integers(0, len(r) - l))
                s.append(PRIME[r[j:j + l]].sum())
            pe.append(SIEVE[s].mean())
        say(f"{name:24s} | {len(us):3d} | {np.mean(L):6.1f} | {obs:.3f} | {np.mean(uni):.3f} ({np.std(uni):.3f}) | {np.mean(sh):.3f} ({np.std(sh):.3f}) / {(1 + (np.array(sh) >= obs).sum()) / (len(sh) + 1):.4f} | {np.mean(pe):.3f} ({np.std(pe):.3f})")
    p_auth = share(allu)
    # ---------------------------------------------------------------- (2) power
    say()
    say("## (2) Power at LP2's unit lengths (wrong key = uniform runes; true = each unit prime with probability p; p = LP1's clause rate or weaker)")
    lens = {i: lengths_of(i) for i in LP2}
    allL = sorted(set(l for v in lens.values() for l in v))
    bL = {l: b_of(l, rng, 20000) for l in allL}
    bar = np.mean([bL[l] for v in lens.values() for l in v])
    say(f"LP2: {sum(len(v) for v in lens.values())} units, mean wrong-key prime probability b = {bar:.3f} (uniform runes at LP2's lengths); LP1 authored rate p = {p_auth:.3f}")
    say("section | units | alpha 1e-3 / 1e-6 / 1e-9 critical count | power at p = LP1 rate / 0.30 / 0.20 (alpha 1e-6)")
    for i, v in lens.items():
        ps = [bL[l] for l in v]
        ks = [kcrit(ps, al) for al in (1e-3, 1e-6, 1e-9)]
        pw = [pb_tail([p] * len(v), ks[1]) if ks[1] <= len(v) else 0.0 for p in (p_auth, 0.30, 0.20)]
        say(f"0.{i:<5d} | {len(v):3d} | {ks[0]} / {ks[1]} / {ks[2]} (of {len(v)}) | " + " / ".join(f"{x:.2f}" for x in pw))
    ws = []
    for i, v in lens.items():
        cum = np.cumsum(v)
        n = cum[-1]
        for s in range(0, n - 299, 300):
            idx = [j for j in range(len(v)) if (cum[j] - v[j]) >= s and cum[j] <= s + 300]
            ws.append([bL[v[j]] for j in idx])
    nu = np.array([len(w) for w in ws])
    pw = [np.mean([pb_tail([p] * len(w), kcrit(w, 1e-6)) if kcrit(w, 1e-6) <= len(w) else 0.0 for w in ws]) for p in (p_auth, 0.30)]
    say(f"n300 windows (non-overlapping from each section start, units fully inside): {len(ws)} windows, units per window mean {nu.mean():.1f}, {np.mean(nu == 0):.0%} with none; mean power at alpha 1e-6, p = {p_auth:.2f} / 0.30: {pw[0]:.3f} / {pw[1]:.3f}")
    say("units needed for 80% power (identical units, b = {:.3f}):".format(bar))
    for al in (1e-3, 1e-6, 1e-9):
        row = []
        for p in (p_auth, 0.30, 0.20):
            n = 1
            while True:
                k = int(binom.isf(al, n, bar)) + 1       # smallest k with P(Bin(n, b) >= k) <= alpha
                if k <= n and binom.sf(k - 1, n, p) >= 0.8:
                    break
                n += 1
            row.append(n)
        say(f"  alpha {al:g}: p = {p_auth:.2f} -> {row[0]} units; p = 0.30 -> {row[1]}; p = 0.20 -> {row[2]}  (LP2 has {sum(len(v) for v in lens.values())} units in total, at most {max(len(v) for v in lens.values())} in one section)")
    # IoC for comparison
    wi = []
    for r in pr_runes[:3]:
        for _ in range(300):
            j = int(rng.integers(0, len(r) - 300))
            wi.append(lp.ioc(list(r[j:j + 300])))
    wn = [lp.ioc(list(rng.integers(0, 29, 300))) for _ in range(900)]
    dioc = (np.mean(wi) - np.mean(wn)) / np.std(wn)
    m = nu.mean() if nu.mean() > 0 else 1
    dprime = m * (p_auth - bar) / np.sqrt(m * bar * (1 - bar))
    say(f"IoC at n = 300: English prose windows {np.mean(wi):.2f}, random {np.mean(wn):.2f} (sd {np.std(wn):.3f}): d' = {dioc:.1f}; prime-unit count of an average n300 window ({m:.1f} units, p = {p_auth:.2f}): d' = {dprime:.2f}; combined d' = {np.hypot(dioc, dprime):.1f}")
    say("Reading: where the plaintext is English the IoC (and the bigram score) already separates by d' of tens; the prime score adds a fraction of one sd per window and has no power on single n300 windows (a third of the windows contain no complete unit).")
    # ---------------------------------------------------------------- (3) rescore recorded hits
    say()
    say("## (3) Rescoring of the recorded decodes (`decoded :` lines of results/**/*verify*; first 160 runes of the hit, section start; greedy parse of the ambiguous Latin spelling)")
    recs, skipped = {}, 0
    for f in glob.glob(os.path.join(ROOT, "results", "**", "*verify*"), recursive=True):
        txt = open(f, encoding="utf-8", errors="ignore").read().split("\n")
        for k, line in enumerate(txt):
            m = re.match(r"\s*decoded\s*:\s*([A-Z]+)\s*$", line)
            if not m:
                continue
            hdr = txt[k - 1] if k else ""
            w = re.search(r"(?:window[= ]+(?:seg)?0\.|seg0\.)(\d+)", hdr)
            if not w or int(w.group(1)) not in LP2:
                skipped += 1
                continue
            recs.setdefault((int(w.group(1)), m.group(1)), os.path.relpath(f, ROOT))
    say(f"{len(recs)} distinct (section, decoded string) records ({skipped} lines skipped: no LP2 section window in the header)")
    bounds = {i: [int(x) for x in np.cumsum(lens[i]) if x <= 160] for i in LP2}
    sc, nul, nulfull, nullen = [], [], [], []
    for (sec, latin), fname in recs.items():
        bd = bounds[sec]
        if not bd:
            continue
        mx = parse_prime(latin, bd)
        if mx is None:
            continue
        sc.append((mx, len(bd), sec, fname, latin))
        for _ in range(3):
            lat = "".join(lp.LATIN[x] for x in rng.integers(0, 29, 160))
            nv = parse_prime(lat, bd)
            nul.append(nv / len(bd) if nv is not None else 0.0)
            nulfull.append((nv == len(bd)) if nv is not None else False)
            nullen.append(len(bd))
    frac = np.array([s[0] / s[1] for s in sc])
    say(f"records scored: {len(sc)} (complete units inside 160 runes: 1-{max(s[1] for s in sc)}); prime fraction: records mean {frac.mean():.3f}, matched random decodes (3 per record) {np.mean(nul):.3f}")
    full = [s for s in sc if s[0] == s[1] and s[1] >= 2]
    say(f"records with every complete unit prime and >= 2 units: {len(full)} (matched null in the same stratum: {np.mean([f for f, n in zip(nulfull, nullen) if n >= 2]):.4f} of {sum(1 for n in nullen if n >= 2)} null decodes; records: {len(full) / max(1, sum(1 for x in sc if x[1] >= 2)):.4f} of {sum(1 for x in sc if x[1] >= 2)}); best by (units, share):")
    for s in sorted(sc, key=lambda s: (-(s[0] / s[1]), -s[1]))[:8]:
        say(f"  section 0.{s[2]} {s[0]}/{s[1]} prime units  ({s[3]})")
    say("No record is a candidate by the verify rule (all are noise by IoC); the prime-unit fraction of the recorded decodes is that of random decodes within the spread, as it must be at 1-2 units per record.")
    # ---------------------------------------------------------------- (4) clause-final words
    say()
    say("## (4) Phase 64's clause-final observation: first / last word of a clause minus the mean word (runes), with standard errors")
    S = lp.load_segments()

    def fl(segids):
        f, l, allw = [], [], []
        for i in segids:
            for _, ws, _ in P64.clauses(S[i] + ["&"])[0]:
                f.append(ws[0]); l.append(ws[-1]); allw += ws
        mw, sd = np.mean(allw), np.std(allw)
        return np.mean(f) - mw, np.mean(l) - mw, sd / np.sqrt(len(f)), len(f)
    for tag, ids in (("LP1", LP1), ("LP2", LP2)):
        fw, lw, se, n = fl(ids)
        say(f"{tag}: first word {fw:+.2f}, last word {lw:+.2f} (se {se:.2f}, {n} clauses)")
    say("Explanations the observation allows: (a) the LP2 marks do not stand at plaintext clause ends (placed by layout or an independent rule): both statistics 0; (b) the extra rune of R4 avoids final words (a final word is then shorter by about the extra-rune share, -0.4): last word about -0.4 against an English +1.3 minus 0.4 = +0.9 unless (a) also holds; (c) the word cuts are not plaintext words: both statistics 0;")
    say("(d) LP2 is not English text: both 0 (random runes). LP2's last-word value is -0.25 +- 0.18: consistent with 0 (a, c, d) and with -0.4 (b), not with +1.3; the contrast with prose is the finding, not the sign.")
    say("Cheap keyless check: the word BEFORE '&' (paragraph end) and the word AFTER a mark (clause-initial words are shorter than average in English: function words) in LP1 vs LP2, plus the same statistic for words before random word positions; (b) predicts a final-word deficit at '.' and '&' only, (a), (c), (d) predict 0 for first and last words alike. Done above for first / last at '.'; the '&' split needs more units than the 14 paragraph ends.")
    say()
    say(f"CPU time {time.process_time() - t0:.0f} s")
    with open(os.path.join(HERE, "..", "results", "analysis", "phase65_prime_clause_score.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
