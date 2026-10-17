"""Exact upper tail of the index of coincidence of n draws from 28 equally likely classes (multinomial), by dynamic programming over
(draws used, sum of squared counts), and the same quantity by Monte Carlo at moderate thresholds; compares with the chi-square
approximation IoC = (chi2_27 + n - 28)/(n - 1) used earlier."""
import sys
import numpy as np
from math import lgamma, log, exp
from scipy.stats import chi2

NC = 28


def exact_tail(n, ioc_thr):
    """P(IoC >= thr): sum of squares s >= s_thr = n + thr*n*(n-1)/NC"""
    s_thr = int(np.ceil(n + ioc_thr * n * (n - 1) / NC - 1e-9))
    cap = s_thr                                    # everything at or above the cap is the tail
    hmax = int(cap ** 0.5) + 1
    # state[m, s] = sum over (h_1..h_k) with sum m and sum of squares s of prod 1/h_i!  (log-scaled by a constant)
    state = np.zeros((n + 1, cap + 1))
    state[0, 0] = 1.0
    tail = np.zeros(n + 1)                         # mass already at or above the cap, by m
    invfact = [exp(-lgamma(h + 1)) for h in range(n + 1)]
    for _ in range(NC):
        new = np.zeros_like(state)
        newtail = tail.copy()                      # h = 0 keeps the tail mass
        for h in range(0, min(n, hmax) + 1):
            w = invfact[h]
            sq = h * h
            if h == 0:
                new += state * w
                continue
            # states (m, s) -> (m + h, s + sq); those with s + sq >= cap go to the tail
            m_ok = n + 1 - h
            keep = cap + 1 - sq
            if keep > 0:
                new[h:h + m_ok, sq:sq + keep] += state[:m_ok, :keep] * w
                if keep < cap + 1:
                    newtail[h:h + m_ok] += state[:m_ok, keep:].sum(axis=1) * w
            else:
                newtail[h:h + m_ok] += state[:m_ok].sum(axis=1) * w
            newtail[h:h + m_ok] += tail[:m_ok] * w
        # h larger than hmax: s + h^2 >= cap for every state: straight to the tail
        for h in range(hmax + 1, n + 1):
            m_ok = n + 1 - h
            if m_ok <= 0:
                break
            w = invfact[h]
            newtail[h:h + m_ok] += (state[:m_ok].sum(axis=1) + tail[:m_ok]) * w
        # states that reached the cap with s exactly == cap are inside `new` at index cap: move them to the tail
        newtail += new[:, cap]
        new[:, cap] = 0
        state, tail = new, newtail
    # (the h = 0 branch for tail states was handled by newtail = tail.copy())
    logfac = lgamma(n + 1) - n * log(NC)
    return tail[n] * exp(logfac)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 240
    rng = np.random.default_rng(0)
    for thr in (1.10, 1.15, 1.20, 1.30, 1.37, 1.40, 1.45):
        ex = exact_tail(n, thr)
        approx = chi2.sf(thr * (n - 1) - (n - 28), 27)
        mc = ""
        if thr <= 1.20:
            h = rng.multinomial(n, [1 / NC] * NC, size=2_000_000)
            ioc = NC * ((h * h).sum(1) - n) / (n * (n - 1))
            mc = f"   Monte Carlo (2e6): {(ioc >= thr - 1e-12).mean():.3e}"
        print(f"n={n} IoC >= {thr:.2f}: exact {ex:.3e}   chi-square approx {approx:.3e}{mc}")
