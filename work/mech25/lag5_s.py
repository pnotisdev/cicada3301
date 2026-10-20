"""Phase 25 part A: the S carrier of the in-word lag-5 echo.
(1) plaintext side: P(p_i = p_(i-5)) inside a word, overall and with source S, in English before encryption (Emerson, Walden, Origin, Republic), digraph and letter
    spelling, with LP2's word-length weighting (pairs counted per word occurrence);
(2) look-elsewhere: the maximum over the 29 source runes of the in-word lag-5 hit z, LP2 against 1000 shuffles inside sections;
(3) a cipher whose key repeats with period 5 inside a fraction f of words (k_i = k_(i-5)) keeps the plaintext coincidences: c_i = c_(i-5) iff p_i = p_(i-5).
    Its predicted excess = f * (plaintext rate - chance) overall and for source S, simulated on English with LP2's layout; f is fitted to the overall excess
    and the S excess is then predicted.

    python work/mech25/lag5_s.py     # -> results/analysis/lag5_s.txt
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "families"))
import fam_data as D  # noqa: E402
import measure as M  # noqa: E402
import sim25 as S  # noqa: E402
import wordlen25 as B  # noqa: E402
import lp  # noqa: E402

N = 29
SR = 15


def word_runes(w, letters):
    w = w.upper().replace("QU", "CW")
    if letters:
        return [lp.RUNE_IDX_L[x] if x in lp.RUNE_IDX_L else {"V": 1, "K": 5, "Z": 15}.get(x, 0) for x in w]
    return lp.word_to_key(w.replace("IO", "IA"))


def plain_rates(path, letters):
    pairs = eq = ps = es = 0
    cache = {}
    for w in B.words_of(path):
        r = cache.get(w) or cache.setdefault(w, word_runes(w, letters))
        for i in range(5, len(r)):
            pairs += 1; eq += r[i] == r[i - 5]
            if r[i - 5] == SR:
                ps += 1; es += r[i] == SR
    return pairs, eq, ps, es


def main():
    lp.RUNE_IDX_L = {lp.LATIN[i]: i for i in range(N) if len(lp.LATIN[i]) == 1}
    out = []

    def say(x=""):
        print(x, flush=True); out.append(x)

    ref, (c, start, sid) = M.lp2_stats()
    r5 = M.relation(c, start, sid, 5, M.EQ)
    n_s = int((((np.arange(len(c)) >= 5) & (sid == np.roll(sid, 5)) & (np.cumsum(start) == np.roll(np.cumsum(start), 5)))[:] & (np.roll(c, 5) == SR)).sum())
    say(f"LP2 in-word lag 5: {r5['in'][0]} pairs, {r5['in'][1]} equal (rate {r5['in'][1] / r5['in'][0]:.4f}, chance {r5['in'][2] / r5['in'][0]:.4f}); source S: {n_s} pairs, {r5['S']} S,S (rate {r5['S'] / n_s:.3f})")
    say("")
    say("(1) English plaintext before encryption, in-word lag 5 (rate of equal runes; rate of S,S given source S):")
    say("corpus            spelling    pairs   eq rate  | S-source pairs  S,S rate")
    plain = {}
    for name, path in (("Emerson", "emerson_essays1.txt"), ("Walden", "corpora/pg205.txt"), ("Origin", "corpora/pg2009.txt"), ("Republic", "corpora/pg1497.txt")):
        for letters in (False, True):
            p, e, ps, es = plain_rates(path, letters)
            plain[(name, letters)] = (e / p, es / max(ps, 1))
            say(f"{name:16s}  {'letters' if letters else 'digraph':8s} {p:8d}  {e / p:.4f}  | {ps:8d}        {es / max(ps, 1):.4f}")
    # chance rate: sum f^2 of the same text
    say("")
    say("(2) look-elsewhere over the 29 source runes (z = (hits - expected)/sqrt(expected), expected from the section shuffle; LP2 vs 1000 shuffles inside sections)")
    wid, loc = M.wordinfo(start)
    i = np.arange(5, len(c))
    same = (sid[i] == sid[i - 5]) & (wid[i] == wid[i - 5])

    def per_source(cc):
        h = np.bincount(cc[i - 5][same & (cc[i] == cc[i - 5])], minlength=N)
        return h

    rng = np.random.default_rng(2512)
    sh = np.array([per_source(M.np.copy(c) if False else _shuf(c, sid, rng)) for _ in range(1000)])
    e = sh.mean(0); sd = np.sqrt(e + 0.5)
    obs = per_source(c)
    z = (obs - e) / sd
    top = np.argsort(-z)[:3]
    say(f"  LP2 per-source z top 3: " + ", ".join(f"{lp.LATIN[t]} {obs[t]}/{e[t]:.1f} z {z[t]:+.2f}" for t in top))
    zmax_sh = ((sh - e) / sd).max(1)
    say(f"  P(max_z over 29 sources >= LP2's S z {z[SR]:+.2f}) among shuffles = {(zmax_sh >= z[SR]).mean():.3f}  (S is LP2's own max: {top[0] == SR}); shuffle max-z median {np.median(zmax_sh):.2f}, 95th {np.percentile(zmax_sh, 95):.2f}")
    say(f"  tail of the raw S count: P(shuffle S hits >= {obs[SR]}) = {(sh[:, SR] >= obs[SR]).mean():.4f}")
    say("")
    say("(3) period-5 key in a fraction f of words (k_i = k_(i-5) for i at word position >= 5; plaintext coincidences survive), English plaintext, LP2 layout, 60 replicates")
    n = len(c)
    P0, st0 = S.english(False)
    for f in (0.0, 0.1, 0.3, 0.6, 1.0):
        exc, exs, dbl = [], [], []
        for _ in range(60):
            s0 = int(rng.integers(0, len(P0) - n - 5000)); s0 += int(np.flatnonzero(st0[s0:])[0])
            p = P0[s0:s0 + n]; st = st0[s0:s0 + n].copy()
            # impose LP2 section starts, keep natural word boundaries
            first = np.r_[0, np.flatnonzero(np.diff(sid)) + 1]
            st[first] = True
            wid2 = np.cumsum(st)
            use = rng.random(wid2.max() + 2) < f
            k = rng.integers(0, N, n)
            pos = M.wordinfo(st)[1]
            for j in range(n):
                if pos[j] >= 5 and use[wid2[j]]:
                    k[j] = k[j - 5]
            cc = (p + k) % N
            for j in range(1, n):   # skip rule, as M0
                if cc[j] == cc[j - 1] and sid[j] == sid[j - 1] and rng.random() < 0.81:
                    cc[j] = (cc[j - 1] + 1 + rng.integers(0, N - 1)) % N
            r = M.relation(cc, st, sid, 5, M.EQ)
            exc.append((r["in"][1] - r["in"][2]) / r["in"][0]); exs.append(r["S"] - 0)
            dbl.append(M.doublets(cc, st, sid)[0])
        say(f"  f={f:.1f}: lag-5 excess per pair {np.mean(exc):+.4f} +- {np.std(exc):.4f} (LP2 {(r5['in'][1] - r5['in'][2]) / r5['in'][0]:+.4f}); S,S hits {np.mean(exs):.1f} +- {np.std(exs):.1f} (LP2 {r5['S']}); doublets {100 * np.mean(dbl):.2f}%")
    with open(os.path.join(HERE, "..", "..", "results", "analysis", "lag5_s.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")


def _shuf(c, sid, rng):
    c = c.copy()
    for k in np.unique(sid):
        m = sid == k
        c[m] = rng.permutation(c[m])
    return c


if __name__ == "__main__":
    main()
