"""Simulators of cipher families: each takes the plaintext P (R, T) of R replicates, the word-start flags `start` (R, T) and returns the cipher text (R, T).

Families (what each stands for):
  random      uniform runes (the null)
  plain       the plaintext itself (control: must be flagged by every plaintext-leaking statistic)
  mono        one random substitution alphabet (control)
  vigenere    additive periodic key of period L
  runkey      additive random running key; with probability q a rune equal to its predecessor is redrawn (avoid-repeat / 'skip on repeat').
              ANY additive keystream without structure (a PRNG, a hash stream, a book code) is statistically this
  ptauto      plaintext autokey c_i = p_i + p_(i-m)
  ctauto      ciphertext autokey c_i = p_i + c_(i-m)
  wordkey     the same key by position in the word, restarted at every word start
  alphawalk   a different random alphabet for each of `period` phases inside a word, fresh alphabets for every word (an evolving alphabet), the phase
              advancing by one when the rune would repeat its predecessor (skip on repeat, probability q per try)
  echo        runkey (q) plus a copy c_i = c_(i-5) with probability eps inside words (a calibration of the lag-5 effect size, not a cipher)
"""
import numpy as np

N = 29


def random_(P, start, rng):
    return rng.integers(0, N, P.shape)


def plain(P, start, rng):
    return P.copy()


def mono(P, start, rng):
    perm = np.argsort(rng.random((len(P), N)), axis=1)
    return np.take_along_axis(perm, P, axis=1)


def vigenere(P, start, rng, L):
    key = rng.integers(0, N, (len(P), L))
    return (P + key[:, np.arange(P.shape[1]) % L]) % N


def _avoid(C, rng, q, start=None):
    """redraw (uniformly among the other 28 values) every rune that equals its predecessor, with probability q"""
    R, T = C.shape
    for i in range(1, T):
        bad = (C[:, i] == C[:, i - 1]) & (rng.random(R) < q)
        if bad.any():
            C[bad, i] = (C[bad, i - 1] + 1 + rng.integers(0, N - 1, int(bad.sum()))) % N
    return C


def runkey(P, start, rng, q):
    return _avoid((P + rng.integers(0, N, P.shape)) % N, rng, q)


def ptauto(P, start, rng, m):
    C = P.copy()
    C[:, m:] = (P[:, m:] + P[:, :-m]) % N
    C[:, :m] = rng.integers(0, N, (len(P), m))
    return C


def ctauto(P, start, rng, m):
    C = rng.integers(0, N, P.shape)
    for i in range(m, P.shape[1]):
        C[:, i] = (P[:, i] + C[:, i - m]) % N
    return C


def _pos(start):
    T = start.shape[1]
    idx = np.where(start, np.arange(T)[None, :], 0)
    return np.arange(T)[None, :] - np.maximum.accumulate(idx, axis=1)


def wordkey(P, start, rng):
    key = rng.integers(0, N, (len(P), 40))
    return (P + np.take_along_axis(key, np.minimum(_pos(start), 39), axis=1)) % N


def alphawalk(P, start, rng, period, q, tries=4):
    R, T = P.shape
    C = np.empty_like(P)
    A = np.zeros((R, period, N), np.int64)
    off = np.zeros(R, np.int64)
    pos = np.zeros(R, np.int64)
    ar = np.arange(R)
    for i in range(T):
        s = start[:, i]
        if s.any():
            k = np.flatnonzero(s)
            A[k] = np.argsort(rng.random((len(k), period, N)), axis=2)
            off[k] = 0; pos[k] = 0
        c = A[ar, (pos + off) % period, P[:, i]]
        if i:
            prev = C[:, i - 1]
            skip = rng.random(R) < q                      # one coin per rune: the rule applies or not (a coin per try would make q depend on R through the early exit)
            for _ in range(tries):
                bad = (c == prev) & skip
                if not bad.any():
                    break
                off[bad] += 1
                c = np.where(bad, A[ar, (pos + off) % period, P[:, i]], c)
        C[:, i] = c
        pos += 1
    return C


def echo(P, start, rng, q, eps, lag=5):
    C = runkey(P, start, rng, q)
    pos = _pos(start)
    for i in range(lag, P.shape[1]):
        e = (pos[:, i] >= lag) & (rng.random(len(P)) < eps)
        C[e, i] = C[e, i - lag]
    return C


# name -> (function, [(label, params)])
FAMILIES = [
    ("random", random_, [("", {})]),
    ("plain", plain, [("", {})]),
    ("mono", mono, [("", {})]),
    ("vigenere", vigenere, [(f"L={L}", {"L": L}) for L in (3, 11, 29, 97)]),
    ("runkey", runkey, [(f"q={q}", {"q": q}) for q in (0.0, 0.5, 0.81, 1.0)]),
    ("ptauto", ptauto, [(f"m={m}", {"m": m}) for m in (1, 5)]),
    ("ctauto", ctauto, [(f"m={m}", {"m": m}) for m in (1, 5)]),
    ("wordkey", wordkey, [("", {})]),
    ("alphawalk", alphawalk, [(f"period={p},q={q}", {"period": p, "q": q}) for p in (4, 5, 6) for q in (0.0, 0.81)]),
    ("echo", echo, [(f"q=0.81,eps={e}", {"q": 0.81, "eps": e}) for e in (0.005, 0.015, 0.03)]),
]
