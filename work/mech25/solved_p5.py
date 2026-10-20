"""Phase 25 part C (sections 9+): (1) in-word lag-5 equality by source rune on the SOLVED pages (ciphertext and decrypted plaintext) against a section shuffle;
(2) the period-5-key prediction at lags 10 and 15 on LP2, with f = 0.6 plants at LP2's layout; (3) the 11 S,S sites against English S____S words.

    python work/mech25/solved_p5.py     # -> results/analysis/solved_p5.txt
"""
import collections
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
import stats  # noqa: E402

N, SR = 29, 15
OUT = []


def say(x=""):
    print(x, flush=True)
    OUT.append(x)


def solved(plain):
    runes, start, sid = [], [], []
    for k, i in enumerate(sorted(lp.KNOWN)):
        toks = stats.SEGS[i]
        c = lp.runes_of(toks)
        p = list(lp.KNOWN[i][1](c))
        r = p if plain else c
        st = np.zeros(len(c), bool)
        for _, a, b in lp.word_spans(toks, c):
            st[a] = True
        runes += list(r)
        start += st.tolist()
        sid += [k] * len(c)
    return np.array(runes), np.array(start), np.array(sid)


def shuf(c, sid, rng):
    c = c.copy()
    for k in np.unique(sid):
        m = sid == k
        c[m] = rng.permutation(c[m])
    return c


def by_source(c, start, sid, L):
    wid, _ = M.wordinfo(start)
    i = np.arange(L, len(c))
    same = (sid[i] == sid[i - L]) & (wid[i] == wid[i - L])
    hit = same & (c[i] == c[i - L])
    return int(same.sum()), np.bincount(c[i - L][hit], minlength=N), np.bincount(c[i - L][same], minlength=N)


def part1(rng):
    say("(1) SOLVED pages (sections 0-6, 16, 17; LP1), in-word lag-5 equality")
    for plain in (False, True):
        c, st, sid = solved(plain)
        n, h, src = by_source(c, st, sid, 5)
        sh = np.array([by_source(shuf(c, sid, rng), st, sid, 5)[1] for _ in range(500)])
        e = sh.mean(0)
        z = (h - e) / np.sqrt(e + 0.5)
        zs = ((sh - e) / np.sqrt(e + 0.5)).max(1)
        top = np.argsort(-z)[:3]
        say(f"  {'plaintext' if plain else 'ciphertext'}: {len(c)} runes, {n} in-word lag-5 pairs, {h.sum()} equal (expected {e.sum():.1f}); S: {h[SR]} hits / {e[SR]:.2f} expected, {src[SR]} S-source pairs; top sources "
            + ", ".join(f"{lp.LATIN[t]} {h[t]}/{e[t]:.1f} z{z[t]:+.1f}" for t in top) + f"; shuffle max-z 95th pct {np.percentile(zs, 95):.2f}")
    say("  per-section layer: " + "; ".join(f"{i}: {lp.KNOWN[i][0]}" for i in sorted(lp.KNOWN)))


def part2(rng):
    c, start, sid = D.lp2()
    n = len(c)
    say("")
    say("(2) period-5 key in a fraction f of words: in-word equality at lags 5, 10, 15. LP2 z (against the section-shuffle expectation) vs plants f=0.6 and f=0 (English, LP2 layout, 100 replicates each)")
    ref = {L: M.relation(c, start, sid, L, M.EQ)["in"] for L in (5, 10, 15)}
    say("  LP2: " + "; ".join(f"lag {L}: {v[1]}/{v[2]:.1f} of {v[0]} pairs, z {v[3]:+.2f}" for L, v in ref.items()))
    P0, st0 = S.english(False)
    first = np.r_[0, np.flatnonzero(np.diff(sid)) + 1]
    for f in (0.0, 0.6):
        zs = {L: [] for L in (5, 10, 15)}
        for _ in range(100):
            s0 = int(rng.integers(0, len(P0) - n - 5000))
            s0 += int(np.flatnonzero(st0[s0:])[0])
            p = P0[s0:s0 + n]
            st = st0[s0:s0 + n].copy()
            st[first] = True
            wid2 = np.cumsum(st)
            pos = M.wordinfo(st)[1]
            use = rng.random(wid2.max() + 2) < f
            k = rng.integers(0, N, n)
            for j in range(5, n):
                if pos[j] >= 5 and use[wid2[j]]:
                    k[j] = k[j - 5]
            cc = (p + k) % N
            for j in range(1, n):
                if cc[j] == cc[j - 1] and sid[j] == sid[j - 1] and rng.random() < 0.81:
                    cc[j] = (cc[j - 1] + 1 + rng.integers(0, N - 1)) % N
            for L in zs:
                zs[L].append(M.relation(cc, st, sid, L, M.EQ)["in"][3])
        say(f"  plants f={f}: " + "; ".join(f"lag {L}: z {np.mean(v):+.2f} +- {np.std(v):.2f}" for L, v in zs.items())
            + "; P(plant z >= LP2 z): " + ", ".join(f"lag {L} {np.mean(np.array(zs[L]) >= ref[L][3]):.2f}" for L in zs)
            + "; P(plant z <= LP2 z) at lag 10: " + f"{np.mean(np.array(zs[10]) <= ref[10][3]):.2f}")


def part3(rng):
    c, start, sid = D.lp2()
    wid, loc = M.wordinfo(start)
    L_of = np.bincount(wid)
    i = np.arange(5, len(c))
    same = (sid[i] == sid[i - 5]) & (wid[i] == wid[i - 5])
    hit = same & (c[i] == c[i - 5])

    def feat(j, ln):
        return (min(int(j), 9), min(int(ln - 1 - j), 5))   # position of the later rune, distance to the word end

    lp_s = [feat(loc[x], L_of[wid[x]]) for x in i[hit & (c[i] == SR)]]
    lp_o = [feat(loc[x], L_of[wid[x]]) for x in i[hit & (c[i] != SR)]]
    eng_s, eng_o = collections.Counter(), collections.Counter()
    for path in ("emerson_essays1.txt", "corpora/pg205.txt", "corpora/pg1497.txt"):
        for w in B.words_of(path):
            r = lp.word_to_key(w.upper().replace("IO", "IA"))
            for j in range(5, len(r)):
                if r[j] == r[j - 5]:
                    (eng_s if r[j] == SR else eng_o)[feat(j, len(r))] += 1
    keys = [(a, b) for a in range(10) for b in range(6)]

    def dist(cn):
        v = np.array([cn[k] + 0.5 for k in keys])
        return dict(zip(keys, v / v.sum()))

    ps, po = dist(eng_s), dist(eng_o)
    ratio = {k: np.log(ps[k] / po[k]) for k in keys}
    obs = sum(ratio[f] for f in lp_s)
    pv = np.array([po[k] for k in keys])
    sv = np.array([ps[k] for k in keys])
    rv = np.array([ratio[k] for k in keys])
    nul_o = rv[rng.choice(len(keys), (20000, 11), p=pv)].sum(1)
    nul_s = rv[rng.choice(len(keys), (20000, 11), p=sv)].sum(1)
    lo = np.array([ratio[f] for f in lp_o])
    nul_lp = lo[rng.integers(0, len(lo), (20000, 11))].sum(1)
    say("")
    say("(3) the 11 S,S sites: features (position of the later S in the word, distance to the word end)")
    say(f"  LP2 S,S sites: later-S positions {sorted(f[0] for f in lp_s)}, distances to end {sorted(f[1] for f in lp_s)}; word-final {sum(f[1] == 0 for f in lp_s)} of 11")
    tot_s = sum(eng_s.values())
    tot_o = sum(eng_o.values())
    say(f"  English (Emerson+Walden+Republic, in-word lag-5 equal pairs): S pairs {tot_s}: word-final {sum(v for k, v in eng_s.items() if k[1] == 0) / tot_s:.2f}, position 5 {sum(v for k, v in eng_s.items() if k[0] == 5) / tot_s:.2f}; other runes {tot_o}: word-final {sum(v for k, v in eng_o.items() if k[1] == 0) / tot_o:.2f}, position 5 {sum(v for k, v in eng_o.items() if k[0] == 5) / tot_o:.2f}")
    say(f"  LP2 other equal lag-5 pairs ({len(lp_o)}): word-final {sum(f[1] == 0 for f in lp_o) / len(lp_o):.2f}, position 5 {sum(f[0] == 5 for f in lp_o) / len(lp_o):.2f}")
    say(f"  log-likelihood ratio (English-S shape vs English-other shape) of the 11 LP2 sites: {obs:+.2f}; draws from the other-rune shape (20,000): mean {nul_o.mean():+.2f}, P(>= obs) = {np.mean(nul_o >= obs):.4f}; draws from the S shape: mean {nul_s.mean():+.2f}, P(<= obs) = {np.mean(nul_s <= obs):.3f}; LP2's own other-rune sites resampled: mean {nul_lp.mean():+.2f}, P(>= obs) = {np.mean(nul_lp >= obs):.4f}")


def main():
    rng = np.random.default_rng(2514)
    part1(rng)
    part2(rng)
    part3(rng)
    with open(os.path.join(HERE, "..", "..", "results", "analysis", "solved_p5.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
