"""Phase 4 item 3: crib-driven analysis and constraint solving.

Cribs come from the preserved word structure: one-rune words must be ᚪ (A) or ᛁ (I), and every
cipher word must decrypt to a dictionary word of the same rune length.

    python crib.py deduce     # family-agnostic deductions from cribs and word patterns
    python crib.py scan       # periodic-key and key-reuse (depth) scans using the A/I cribs
    python crib.py validate   # solver on synthetic periodic / depth ciphertexts
"""
import math
import os
import re
import sys
from collections import Counter, defaultdict

import numpy as np

import lp
import stats

N = lp.N
HERE = os.path.dirname(os.path.abspath(__file__))
A_, I_ = 24, 10  # rune indices of ᚪ and ᛁ
SEGS = stats.SEGS


# ---------------------------------------------------------------- rune word dictionary

def _english_words():
    path = os.path.join(HERE, "ref", "emerson_essays1.txt")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    return [w.upper() for w in re.findall(r"[A-Za-z]+", text)]


_DICT = None


def rune_words(max_len=12):
    """{length: {rune tuple: log-probability}} from Emerson word frequencies plus the solved
    LP text, smoothed with the 10k frequency list."""
    global _DICT
    if _DICT is not None:
        return _DICT
    cnt = Counter()
    for w in _english_words():
        cnt[tuple(lp.word_to_key(w.replace("IO", "IA")))] += 1
    for i, (_, f) in lp.KNOWN.items():
        plain = f(lp.runes_of(SEGS[i]))
        for _, a, b in lp.word_spans(SEGS[i], plain):
            cnt[tuple(plain[a:b])] += 3
    with open(os.path.join(HERE, "ref", "english_20k.txt"), encoding="utf-8") as f:
        for w in f.read().split()[:10000]:
            if len(w) > 1 or w in ("a", "i"):
                cnt[tuple(lp.word_to_key(w.upper().replace("IO", "IA")))] += 1
    total = sum(cnt.values())
    _DICT = defaultdict(dict)
    for t, c in cnt.items():
        if 0 < len(t) <= max_len:
            _DICT[len(t)][t] = math.log(c / total)
    return _DICT


def plain_runes_english():
    out = []
    for w in _english_words():
        out.append(lp.word_to_key(w.replace("IO", "IA")))
    return out


# ---------------------------------------------------------------- word structure of the ciphertext

def cipher_words(seg_ids=stats.UNSOLVED):
    """[(segment, start rune index within segment, rune tuple)] for every unsolved word."""
    out = []
    for i in seg_ids:
        c = lp.runes_of(SEGS[i])
        for _, a, b in lp.word_spans(SEGS[i], c):
            out.append((i, a, tuple(c[a:b])))
    return out


def one_rune_only_ai():
    d = rune_words()
    d[1] = {k: v for k, v in d[1].items() if k in ((A_,), (I_,))}
    return d


# ---------------------------------------------------------------- deductions

def deduce():
    cw = cipher_words()
    eng = [w for w in plain_runes_english() if w]
    print("== D1: is each plaintext word encrypted the same way wherever it occurs?")
    for L in (1, 2, 3):
        cws = [w for _, _, w in cw if len(w) == L]
        n = len(cws)
        sample = [tuple(w) for w in eng if len(w) == L][:50 * n]
        # English: distinct words among n draws (average over chunks)
        chunks = [sample[k:k + n] for k in range(0, len(sample) - n, n)][:40]
        eng_distinct = np.mean([len(set(ch)) for ch in chunks])
        rand_distinct = N ** L * (1 - math.exp(-n / N ** L))
        print(f"  {L}-rune words: n={n}, distinct cipher words={len(set(cws))}; English plaintext would give "
              f"~{eng_distinct:.0f}, a fresh random key per rune ~{rand_distinct:.0f}")
    print("  -> deterministic word-level encryption (same word -> same cipher word) is ruled out.")

    print("\n== D2: one key value per word (word-level shift)?")
    inword = sum(a == b for w in eng for a, b in zip(w, w[1:]))
    inpairs = sum(len(w) - 1 for w in eng)
    obs = obs_pairs = 0
    for _, _, w in cw:
        obs += sum(a == b for a, b in zip(w, w[1:]))
        obs_pairs += len(w) - 1
    print(f"  in-word doublets: English plaintext {100 * inword / inpairs:.2f}% (kept by any word-level shift); "
          f"unsolved ciphertext {100 * obs / obs_pairs:.2f}% ({obs}/{obs_pairs})")
    print("  -> a constant key per word is ruled out (it would preserve plaintext doublets).")

    print("\n== D3: key determined by position inside the word (and/or word length)?")
    ones = Counter(w[0] for _, _, w in cw if len(w) == 1)
    print(f"  {sum(ones.values())} one-rune words use {len(ones)} distinct cipher runes "
          f"(the model allows only 2: A+k and I+k)")
    print("  -> ruled out.")

    print("\n== D4: key restarting at each line / page / segment (same key for same relative position)?")
    for unit in ("\n", "%"):
        groups = defaultdict(list)
        for i in stats.UNSOLVED:
            pos = 0
            for t in SEGS[i]:
                if isinstance(t, int):
                    groups[pos].append(t)
                    pos += 1
                elif t == unit or (unit == "\n" and t in ("%", "&")) or (unit == "%" and t == "&" and False):
                    pos = 0
        hit = tot = 0
        for pos, vals in groups.items():
            cnt = Counter(vals)
            hit += sum(v * (v - 1) for v in cnt.values())
            tot += len(vals) * (len(vals) - 1)
        rate = hit / tot
        sd = math.sqrt((1 / N) * (1 - 1 / N) / (tot / 2))
        name = "line" if unit == "\n" else "page"
        print(f"  same position within {name}: coincidence {100 * rate:.2f}% (random 3.45%, depth would give ~6%; "
              f"z = {(rate - 1 / N) / sd:+.1f})")
    print("  segment restarts are covered by the depth scan (offset 0).")


# ---------------------------------------------------------------- key-reuse scans

ENGLISH_COINC = None


def english_coincidence():
    """P(two independent English runes are equal) = depth coincidence rate."""
    global ENGLISH_COINC
    if ENGLISH_COINC is None:
        p = [x for w in plain_runes_english() for x in w]
        f = np.bincount(p, minlength=N) / len(p)
        ENGLISH_COINC = float((f ** 2).sum())
    return ENGLISH_COINC


def lag_scan(streams, max_lag=6000, band=1):
    """Coincidence count/total at each lag (pooled over segments, within segment).
    With band > 1, lags L..L+band-1 are pooled (tolerates key drift from skips)."""
    hits = np.zeros(max_lag + band + 1)
    tots = np.zeros(max_lag + band + 1)
    for c in streams:
        c = np.asarray(c)
        n = len(c)
        onehot = np.zeros((N, 2 * n))
        onehot[c, np.arange(n)] = 1
        F = np.fft.rfft(onehot, axis=1)
        ac = np.fft.irfft((F * np.conj(F)).sum(axis=0), 2 * n)[:n]      # ac[L] = #{i: c_i == c_{i+L}}
        L = np.arange(n)
        m = min(n, max_lag + band + 1)
        hits[:m] += np.round(ac[:m])
        tots[:m] += (n - L)[:m]
    if band > 1:
        kern = np.ones(band)
        hits = np.convolve(hits, kern)[band - 1:band - 1 + max_lag + 1]
        tots = np.convolve(tots, kern)[band - 1:band - 1 + max_lag + 1]
    else:
        hits, tots = hits[:max_lag + 1], tots[:max_lag + 1]
    return hits, tots


def cross_scan(a, b):
    """For every offset d (b shifted by d against a): coincidences and overlap length."""
    a, b = np.asarray(a), np.asarray(b)
    n, m = len(a), len(b)
    size = n + m
    A = np.zeros((N, size)); A[a, np.arange(n)] = 1
    B = np.zeros((N, size)); B[b, np.arange(m)] = 1
    cc = np.fft.irfft((np.fft.rfft(A, axis=1) * np.conj(np.fft.rfft(B, axis=1))).sum(axis=0), size)
    # cc[d] for d >= 0: sum_i a[i+d]==b[i]; negative d wrap to the end
    offs = np.concatenate([np.arange(0, n), np.arange(-(m - 1), 0)])
    vals = np.concatenate([cc[:n], cc[size - (m - 1):]])
    overlap = np.array([min(n - d, m) if d >= 0 else min(n, m + d) for d in offs])
    return offs, np.round(vals), overlap


def zscores(hits, tots, p0=1 / N):
    with np.errstate(divide="ignore", invalid="ignore"):
        return (hits - p0 * tots) / np.sqrt(p0 * (1 - p0) * tots)


def scan(min_overlap=150, seed=0):
    streams = [lp.runes_of(SEGS[i]) for i in stats.UNSOLVED if len(lp.runes_of(SEGS[i])) > 100]
    pe = english_coincidence()
    print(f"depth (reused key) coincidence rate for English: {100 * pe:.2f}%  vs random {100 / N:.2f}%")
    R = np.random.default_rng(seed)
    shuffled = [R.permutation(c) for c in streams]
    print("\n== S1: periodic key / key reused within a segment (all lags 2..6000)")
    for band in (1, 16):
        res = {}
        for name, st in (("unsolved", streams), ("shuffled control", shuffled)):
            h, t = lag_scan(st, 6000, band)
            z = zscores(h, t)
            ok = t >= min_overlap * band
            ok[:2] = False
            k = int(np.nanargmax(np.where(ok, z, -np.inf)))
            res[name] = (k, z[k], h[k] / t[k], t[k])
        u, cS = res["unsolved"], res["shuffled control"]
        print(f"  band {band:2d}: best lag {u[0]} z={u[1]:+.1f} rate {100 * u[2]:.2f}% (pairs {u[3]:.0f}) | "
              f"shuffled control best z={cS[1]:+.1f}")
    print("\n== S2: same key reused between two segments (every offset, every pair)")
    best = []
    ctrl = []
    for x in range(len(streams)):
        for y in range(len(streams)):
            if x == y:
                continue
            for name, sa, sb, sink in (("u", streams[x], streams[y], best), ("c", shuffled[x], shuffled[y], ctrl)):
                offs, v, ov = cross_scan(sa, sb)
                ok = ov >= min_overlap
                z = zscores(v, ov)
                k = int(np.argmax(np.where(ok, z, -np.inf)))
                sink.append((float(z[k]), x, y, int(offs[k]), float(v[k] / ov[k]), int(ov[k])))
    best.sort(reverse=True)
    ctrl.sort(reverse=True)
    names = [i for i in stats.UNSOLVED if len(lp.runes_of(SEGS[i])) > 100]
    for zz, x, y, d, r, ov in best[:5]:
        print(f"  0.{names[x]} vs 0.{names[y]} offset {d:+5d}: z={zz:+.1f} rate {100 * r:.2f}% over {ov} runes")
    print(f"  shuffled control best z={ctrl[0][0]:+.1f}")
    return best, ctrl
