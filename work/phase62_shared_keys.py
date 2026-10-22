"""Phase 62: do LP2 sections share keys? See work/log/phase62_shared_keys.md.

    python work/phase62_shared_keys.py [--null 300] [--plants 30]     # -> results/analysis/phase62_shared_keys.txt

Two sections A, B with c = p + k (mod 29) and the same key stream at relative offset d: c_A[i] - c_B[i+d] = p_A - p_B ('diff'); with the key sign-flipped
c_A[i] + c_B[i+d] = p_A + p_B ('sum'); with the key reversed the same on B read backwards ('diff-rev', 'sum-rev'). Statistic: z = (chi2 - 28) / sqrt(56) of the 29-bin
histogram of the combination over the overlap (>= MINOV runes), maximum over offsets and the four relations ('full'); 'win' cuts the shorter section into blocks of WIN runes
(all matched against the whole other section; a block that stays aligned for WIN runes is enough: the drift-tolerant variant). All offsets at once by a 2-D FFT cross-correlation
(residue axis x position axis). Null: every section shuffled within its words, same pairs and offsets, so the maximum over pairs, relations and offsets is in the null.
Plants: English rune words under one random key, models plain / R4-E / R4-P (see the log), the same test as for LP2.
"""
import argparse
import ctypes
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "families"))
import fam_data as D  # noqa: E402
import lp  # noqa: E402
import stats  # noqa: E402

M, MINOV, WIN = 29, 100, 300
REL = ["diff", "sum", "diff-rev", "sum-rev"]
SECS = [7, 8, 9, 11, 12, 13, 14, 15]
NAME = {i: f"0.{i}" for i in SECS}
OUT = []


def say(s=""):
    print(s, flush=True)
    OUT.append(s)


def spec(x, L):
    oh = np.zeros((M, L))
    oh[np.asarray(x, int), np.arange(len(x))] = 1
    return np.fft.fft(np.fft.rfft(oh, axis=1), axis=0)


def corr_z(FA, nA, FB, nB, L, minov, shift=0):
    """z of the histogram of A[i] -/+ B[i+d] over every offset d with overlap >= minov: (zmax, d, m) for diff and sum; FA/FB spectra of (A, B)."""
    d = np.arange(-(nA - 1), nB)
    m = np.minimum(nA, nB - d) - np.maximum(0, -d)
    ok = m >= minov
    res = []
    for F in (FA, FA[(-np.arange(M)) % M]):                  # diff: correlation; sum: residue axis of A flipped
        G = np.fft.irfft(np.fft.ifft(np.conj(F) * FB, axis=0), n=L, axis=1)
        N2 = np.rint(G[:, d % L]) ** 2
        z = ((M / m) * N2.sum(0) - m - (M - 1)) / np.sqrt(2 * (M - 1))
        z = np.where(ok, z, -np.inf)
        k = int(np.argmax(z))
        res.append((float(z[k]), int(d[k]) + shift, int(m[k])))
    return res


def pair_stats(a, b, full=True, win=True):
    """{(stat, relation): (z, d, m)} for the pair; the window blocks are cut from the shorter section"""
    out = {}
    s, t = (a, b) if len(a) <= len(b) else (b, a)
    L = 1 << int(np.ceil(np.log2(len(a) + len(b) + 1)))
    FS, FT, FTr = spec(s, L), spec(t, L), spec(t[::-1], L)
    if full:
        for tag, FB in (("", FT), ("-rev", FTr)):
            for name, r in zip(("diff", "sum"), corr_z(FS, len(s), FB, len(t), L, MINOV)):
                out[("full", name + tag)] = r
    if win:
        for k in range(len(s) // WIN):
            blk = s[k * WIN:(k + 1) * WIN]
            FW = spec(blk, L)
            for tag, FB in (("", FT), ("-rev", FTr)):
                for name, r in zip(("diff", "sum"), corr_z(FW, WIN, FB, len(t), L, WIN, shift=k * WIN)):
                    key = ("win", name + tag)
                    if key not in out or r[0] > out[key][0]:
                        out[key] = r
    return out


def shuffle_words(c, spans, rng):
    c = np.array(c)
    for a, b in spans:
        c[a:b] = rng.permutation(c[a:b])
    return c


def load():
    secs, spans = {}, {}
    for i in SECS:
        toks = stats.SEGS[i]
        r = lp.runes_of(toks)
        secs[i] = np.array(r)
        spans[i] = [(a, b) for _, a, b in lp.word_spans(toks, r)]
    return secs, spans


def all_pairs(secs, full=True, win=True, order=None):
    pr = order or [(a, b) for k, a in enumerate(SECS) for b in SECS[k + 1:]]
    return {p: pair_stats(secs[p[0]], secs[p[1]], full, win) for p in pr}


def gmax(res, stat):
    return max(v[0] for st in res.values() for k, v in st.items() if k[0] == stat)


# ---------------------------------------------------------------- plants

def T(x):
    return (24 - 2 * x) % M


def encrypt(P, ST, p0, n, key, ko, sign, r4, emit, rng):
    """English words from P[p0:] under key[ko:] (key advances with every emitted rune if emit, else with plaintext runes only); r4: phase 57's R4 (45% of words
    get a null at a uniform slot; a would-be doublet is repaired with prob 0.81 by 24 - 2c(-6) when the rune 6 back is in the word, else a uniform other rune)"""
    out, ki, pi = [], ko, p0
    while len(out) < n:
        j = pi + 1
        while not ST[j]:
            j += 1
        w = P[pi:j]
        pi = j
        L, ws = len(w), len(out)
        slot = int(rng.integers(0, L + 1)) if r4 and L >= 2 and rng.random() < 0.45 else -1
        for t in range(L + 1):
            if t == slot:
                v = int(rng.integers(0, M))
                if out and v == out[-1]:
                    v = (v + 1 + int(rng.integers(0, M - 1))) % M
                out.append(v)
                ki += emit
            if t < L:
                x = (int(w[t]) + sign * int(key[ki])) % M
                ki += 1
                if r4 and out and x == out[-1] and rng.random() < 0.81:
                    tb = T(out[-6]) if len(out) - ws >= 6 else -1
                    x = tb if tb >= 0 and tb != out[-1] else (out[-1] + 1 + int(rng.integers(0, M - 1))) % M
                out.append(x)
    return np.array(out[:n])


def plant(eng, na, nb, rel, model, rng):
    P, ST = eng
    starts = np.flatnonzero(ST)
    starts = starts[starts < len(P) - 20000]
    key = rng.integers(0, M, 3 * (na + nb) + 4000)
    r4, emit = model != "plain", model != "R4-P"
    ka, kb = 1500, 1500 + int(rng.integers(-600, 600))
    sign = -1 if rel.startswith("sum") else 1
    kB = key[::-1] if rel.endswith("rev") else key
    if model == "indep":
        kB = rng.integers(0, M, len(key))
    a = encrypt(P, ST, int(rng.choice(starts)), na, key, ka, 1, r4, emit, rng)
    b = encrypt(P, ST, int(rng.choice(starts)), nb, kB, kb, sign, r4, emit, rng)
    return a, b


def power(eng, thr, pairs, secs, plants, seed):
    rng = np.random.default_rng(seed)
    say(f"{'pair (lengths)':22s} {'model':6s} {'planted relation':9s} | detected full / win (thresholds {thr['full']:.1f} / {thr['win']:.1f}) | median z full / win | right relation")
    rows = []
    for (a, b) in pairs:
        na, nb = len(secs[a]), len(secs[b])
        for model in ("plain", "R4-E", "R4-P", "indep"):
            for rel in (REL if model != "indep" else ["diff"]):
                zs = []
                for _ in range(plants):
                    ca, cb = plant(eng, na, nb, rel, model, rng)
                    st = pair_stats(ca, cb)
                    zf = max(v[0] for k, v in st.items() if k[0] == "full")
                    zw = max(v[0] for k, v in st.items() if k[0] == "win")
                    top = max((v[0], k[1]) for k, v in st.items() if k[0] == "full")[1]
                    zs.append((zf, zw, top == rel))
                zs = np.array(zs, float)
                df, dw = (zs[:, 0] > thr["full"]).mean(), (zs[:, 1] > thr["win"]).mean()
                say(f"{NAME[a]}-{NAME[b]} ({na},{nb})".ljust(22) + f" {model:6s} {rel:9s} | {df:5.2f} / {dw:5.2f} | {np.median(zs[:, 0]):7.1f} / {np.median(zs[:, 1]):6.1f} | {zs[:, 2].mean():.2f}")
                rows.append((a, b, model, rel, df, dw))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--null", type=int, default=300)
    ap.add_argument("--plants", type=int, default=16)
    ap.add_argument("--null_win", type=int, default=100)
    ap.add_argument("--len_plants", type=int, default=40)
    a = ap.parse_args()
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)   # below normal
    t0 = time.process_time()
    secs, spans = load()
    say("# Phase 62: shared keys between LP2 sections (2026-10-23). Nothing in LP2 is solved.")
    say("sections: " + ", ".join(f"{NAME[i]} n={len(secs[i])}" for i in SECS))
    # selftest: a noiseless planted shared key must give a huge z, and an unrelated pair must not
    rng = np.random.default_rng(1)
    flat = rng.integers(0, M, 600)
    r = pair_stats(flat, (flat + 7) % M, win=False)                                       # identical texts shifted by 7: diff histogram has one bin
    assert r[("full", "diff")][0] > 50 and r[("full", "diff")][1] == 0
    r = pair_stats(flat, (-flat) % M, win=False)
    assert r[("full", "sum")][0] > 50
    r = pair_stats(flat, flat[::-1], win=False)
    assert r[("full", "diff-rev")][0] > 50
    say("selftest ok (identical / negated / reversed copies are found at the right relation and offset)")
    say()
    # real data
    say("## LP2")
    real = {}
    first = [(7, 11)] + [(x, y) for i, x in enumerate(SECS) for y in SECS[i + 1:] if (x, y) != (7, 11)]
    real = all_pairs(secs, order=first)
    g = {s: gmax(real, s) for s in ("full", "win")}
    # null: whole LP2 shuffled within words
    nulls = {"full": [], "win": []}
    rng = np.random.default_rng(62)
    for rep in range(a.null):
        sh = {i: shuffle_words(secs[i], spans[i], rng) for i in SECS}
        r = all_pairs(sh, win=rep < a.null_win)
        nulls["full"].append(gmax(r, "full"))
        if rep < a.null_win:
            nulls["win"].append(gmax(r, "win"))
    thr = {s: float(np.percentile(nulls[s], 95)) for s in nulls}
    say(f"null: {a.null} replicates (window statistic: first {a.null_win}) of LP2 shuffled within words; maximum over 28 pairs x 4 relations x offsets: " + "; ".join(
        f"{s} mean {np.mean(nulls[s]):.2f} sd {np.std(nulls[s]):.2f} 95th pct {thr[s]:.2f} 99th {np.percentile(nulls[s], 99):.2f}" for s in nulls))
    say()
    say("0.7 vs 0.11 first (the art link): " + "; ".join(f"{k[0]} {k[1]} z {v[0]:.2f} (d {v[1]}, overlap {v[2]})" for k, v in sorted(real[(7, 11)].items())))
    say()
    say("Per pair: best z over offsets for each relation (full | win); P = share of null replicates whose GLOBAL maximum is at least this pair's value")
    for s in ("full", "win"):
        say(f"-- {s}")
        for p, st in real.items():
            best = max((v, k[1]) for k, v in st.items() if k[0] == s)
            row = " ".join(f"{k[1]}={v[0]:5.2f}" for k, v in sorted(st.items()) if k[0] == s)
            P = (1 + np.sum(np.array(nulls[s]) >= best[0][0])) / (len(nulls[s]) + 1)
            say(f"{NAME[p[0]]}-{NAME[p[1]]}: {row} | best {best[1]} d {best[0][1]} m {best[0][2]} | P(global) {P:.3f}")
    say()
    say(f"GLOBAL: full max z {g['full']:.2f} (P {(1 + np.sum(np.array(nulls['full']) >= g['full'])) / (len(nulls['full']) + 1):.3f}), "
        f"win max z {g['win']:.2f} (P {(1 + np.sum(np.array(nulls['win']) >= g['win'])) / (len(nulls['win']) + 1):.3f})")
    say()
    say("## Power (positive control): English rune texts under one random key, same test, thresholds = null 95th percentile of the global maximum")
    eng = D.english(150_000)
    power(eng, thr, [(7, 11), (8, 12), (14, 15)], secs, a.plants, 5)
    say()
    say("Plain model, planted diff / sum relation, equal lengths n (full statistic only): detection against the null 95th percentile of the global maximum")
    rng = np.random.default_rng(9)
    for n in (500, 1000, 1500, 2000, 3000):
        hit = []
        for rel in ("diff", "sum"):
            zs = [max(v[0] for v in pair_stats(*plant(eng, n, n, rel, "plain", rng), win=False).values()) for _ in range(a.len_plants)]
            hit.append(f"{rel} {np.mean(np.array(zs) > thr['full']):.2f} (median z {np.median(zs):.1f})")
        say(f"n = {n}: " + "; ".join(hit))
    say()
    say(f"CPU time {time.process_time() - t0:.0f} s")
    outp = os.path.join(HERE, "..", "results", "analysis", "phase62_shared_keys.txt")
    open(outp, "w", encoding="utf-8").write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
