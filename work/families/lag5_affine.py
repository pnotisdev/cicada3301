"""Affine relations between runes at a fixed distance inside words: is the within-word lag-5 effect an EQUALITY echo, and is there any other relation c_(i+lag) = a c_i + b (mod 29)?

For every lag 1..8, every (a, b) with a = 1..28, b = 0..28 (812 relations; equality is a = 1, b = 0) the number of within-word pairs (i, i+lag) obeying it is compared with the expectation
from the rune frequencies (z = Poisson-normal). The look-elsewhere is calibrated by the same scan on 1,000 shuffles of LP2's runes inside sections (word structure and frequencies kept):
the best z of each lag, and the best z over all lags. The best relation is then split by section.

    python work/families/lag5_affine.py          # -> results/analysis/lag5_affine.txt
"""
import itertools
import os
import sys

import numpy as np

import fam_data as D

HERE = os.path.dirname(os.path.abspath(__file__))
N = D.N
LAGS = range(1, 9)                    # longer lags have too few within-word pairs (lag 9: 192) for the Poisson-normal z
OUT = []
C_ = np.arange(N)
M = (np.arange(1, N)[:, None, None] * C_[None, None, :] + np.arange(N)[None, :, None]) % N      # M[a-1, b, c] = a c + b mod 29


def say(s=""):
    print(s)
    OUT.append(s)


def table(C, start, sid, lag):
    """29 x 29 counts of (c_i, c_(i+lag)) over within-word pairs"""
    wid = np.cumsum(start)
    v = (wid[lag:] == wid[:-lag]) & (sid[lag:] == sid[:-lag])
    return np.bincount(C[:-lag][v] * N + C[lag:][v], minlength=N * N).reshape(N, N)


def scan(T, f):
    """(z, observed, expected) of every affine relation, arrays (28, 29)"""
    n = T.sum()
    obs = T[C_[None, None, :], M].sum(-1)
    ex = n * (f[C_][None, None, :] * f[M]).sum(-1)
    return np.where(ex >= 5, (obs - ex) / np.sqrt(np.maximum(ex, 1e-9)), -np.inf), obs, ex          # relations expected fewer than 5 times are not scored


def best(C, start, sid):
    f = np.bincount(C, minlength=N) / len(C)
    out = []
    for lag in LAGS:
        z, o, e = scan(table(C, start, sid, lag), f)
        a, b = np.unravel_index(np.argmax(z), z.shape)
        out.append((float(z[a, b]), a + 1, int(b), int(o[a, b]), float(e[a, b])))
    return out


def split_half(C, start, sid):
    """choose the best (lag, relation) in one half of the sections, score it in the other half; mean replication z over all 4 + 4 splits (both directions)
    of the 8 sections with more than 100 runes, and how often the chosen relation is the lag-6 one"""
    secs = [k for k in np.unique(sid) if (sid == k).sum() > 100]
    wid = np.cumsum(start)
    Ts = {k: np.array([table(C[sid == k], start[sid == k], sid[sid == k], lag) for lag in LAGS]) for k in secs}
    cnt = {k: np.bincount(C[sid == k], minlength=N) for k in secs}
    reps, lag6 = [], 0
    for A in itertools.combinations(secs, len(secs) // 2):
        B = [k for k in secs if k not in A]
        for X, Y in ((list(A), B), (B, list(A))):
            def half(ks):
                T = sum(Ts[k] for k in ks)
                f = sum(cnt[k] for k in ks) / sum(cnt[k].sum() for k in ks)
                return [scan(T[i], f)[0] for i in range(len(LAGS))]
            zx, zy = half(X), half(Y)
            i = int(np.argmax([z.max() for z in zx]))
            a_, b_ = np.unravel_index(np.argmax(zx[i]), zx[i].shape)
            v = zy[i][a_, b_]
            reps.append(float(v) if np.isfinite(v) else 0.0)                  # a relation too rare to score in the held-out half counts as no replication
            lag6 += (i == 5 and (a_ + 1, b_) == (27, 24))
    return float(np.mean(reps)), lag6 / len(reps)


def main():
    runes, start, sid = D.lp2()
    rng = np.random.default_rng(9)
    obs = best(runes, start, sid)
    say(f"{len(runes)} runes; for each lag 1..8 the best of 812 affine relations c' = a c + b (mod 29) on within-word pairs; equality is a = 1, b = 0")
    null = []
    for _ in range(1000):
        Cp = runes.copy()
        for k in np.unique(sid):
            m = sid == k
            Cp[m] = rng.permutation(Cp[m])
        null.append([x[0] for x in best(Cp, start, sid)])
    null = np.array(null)
    f = np.bincount(runes, minlength=N) / len(runes)
    say("lag  best relation                  z      observed / expected   equality z   P(best of 812 under shuffles)")
    for i, lag in enumerate(LAGS):
        z, a, b, o, e = obs[i]
        zeq = scan(table(runes, start, sid, lag), f)[0][0, 0]
        say(f"{lag:3d}  c' = {a:2d} c + {b:2d}      {z:+6.2f}   {o:5d} / {e:6.1f}      {zeq:+6.2f}      {(null[:, i] >= z).mean():.3f}")
    gm = null.max(1)
    top = max(obs)
    say(f"best over all 8 lags: z {top[0]:+.2f} (lag {obs.index(top) + 1}); shuffle null of the best over lags and relations: median {np.median(gm):+.2f}, "
        f"95th percentile {np.percentile(gm, 95):+.2f}; P(null best >= observed) = {(gm >= top[0]).mean():.3f}")
    lag = obs.index(top) + 1
    _, a, b, _, _ = top
    say(f"the best relation (lag {lag}, c' = {a} c + {b}) by section:")
    wid = np.cumsum(start)
    for k in np.unique(sid):
        m = sid == k
        T = table(runes[m], start[m], sid[m], lag)
        ff = np.bincount(runes[m], minlength=N) / m.sum()
        n = T.sum()
        o = int(T[C_, (a * C_ + b) % N].sum())
        e = n * float((ff[C_] * ff[(a * C_ + b) % N]).sum())
        say(f"   section 0.{7 + k}: {n} pairs, {o} obey it, {e:.1f} expected ({(o - e) / np.sqrt(e) if e else 0:+.1f})")
    m_obs, share = split_half(runes, start, sid)
    nm = []
    for _ in range(200):
        Cp = runes.copy()
        for k in np.unique(sid):
            m = sid == k
            Cp[m] = rng.permutation(Cp[m])
        nm.append(split_half(Cp, start, sid)[0])
    say(f"split-half replication (best relation of 4 sections scored in the other 4; 70 directed splits): mean z in the held-out half {m_obs:+.2f} against a shuffle null "
        f"{np.mean(nm):+.2f} +- {np.std(nm):.2f} (P(null >= observed) = {(np.array(nm) >= m_obs).mean():.3f}); the half-best relation is the lag-6 one in {100 * share:.0f}% of the splits")
    dest = os.path.join(HERE, "..", "..", "results", "analysis")
    with open(os.path.join(dest, "lag5_affine.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    sys.exit(main())
