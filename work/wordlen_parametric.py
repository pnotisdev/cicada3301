"""Do LP2's word lengths look like independent draws from a simple parametric distribution?  (They show no serial structure at all, see
wordlen_adjacency.py, which English and the solved sections do show.) Fits 1-3 parameter families to the histogram (bins 1..11, 12+) by minimum G
and reports G, degrees of freedom and p; also the best English-based mechanism of wordlen_languages.py for comparison.

    python work/wordlen_parametric.py          # -> results/analysis/wordlen_parametric.txt
"""
import os
import sys

import numpy as np
from scipy import stats as st
from scipy.optimize import minimize

import lp
import stats

HERE = os.path.dirname(os.path.abspath(__file__))
BINS = 12


def hist_of(lens):
    h = np.zeros(BINS)
    for L in lens:
        h[min(L, BINS) - 1] += 1
    return h


def binned(pmf_fn):
    """pmf over 1..11 and the tail mass for 12+ from a function pmf(k) on k >= 1"""
    p = np.array([pmf_fn(k) for k in range(1, BINS)], dtype=float)
    return np.concatenate([p, [max(1e-12, 1 - p.sum())]])


def g_stat(obs, p):
    p = np.clip(p, 1e-12, None)
    p = p / p.sum()
    e = obs.sum() * p
    m = obs > 0
    return 2 * float((obs[m] * np.log(obs[m] / e[m])).sum())


FAMILIES = {
    "shifted Poisson (L-1 ~ Poisson(lam))": (1, lambda t: binned(lambda k: st.poisson.pmf(k - 1, np.exp(t[0]))), [np.log(3.4)]),
    "shifted negative binomial (L-1 ~ NB(r, p))": (2, lambda t: binned(lambda k: st.nbinom.pmf(k - 1, np.exp(t[0]), 1 / (1 + np.exp(-t[1])))), [np.log(4), 0.0]),
    "shifted geometric mixture, 2 components": (3, lambda t: binned(lambda k: (1 / (1 + np.exp(-t[2]))) * st.geom.pmf(k, 1 / (1 + np.exp(-t[0]))) +
                                                                     (1 - 1 / (1 + np.exp(-t[2]))) * st.geom.pmf(k, 1 / (1 + np.exp(-t[1])))), [0.5, -1.5, 0.0]),
    "discretised log-normal (mu, sigma)": (2, lambda t: binned(lambda k: st.lognorm.cdf(k + 0.5, np.exp(t[1]), scale=np.exp(t[0])) -
                                                               st.lognorm.cdf(k - 0.5, np.exp(t[1]), scale=np.exp(t[0]))), [1.3, np.log(0.5)]),
    "discretised gamma (shape, scale)": (2, lambda t: binned(lambda k: st.gamma.cdf(k + 0.5, np.exp(t[0]), scale=np.exp(t[1])) -
                                                             st.gamma.cdf(k - 0.5, np.exp(t[0]), scale=np.exp(t[1]))), [np.log(4), np.log(1)]),
    "discretised Weibull (shape, scale)": (2, lambda t: binned(lambda k: st.weibull_min.cdf(k + 0.5, np.exp(t[0]), scale=np.exp(t[1])) -
                                                               st.weibull_min.cdf(k - 0.5, np.exp(t[0]), scale=np.exp(t[1]))), [np.log(2), np.log(5)]),
}


def main():
    lens = []
    for i in stats.UNSOLVED:
        c = lp.runes_of(stats.SEGS[i])
        lens += [b - a for _, a, b in lp.word_spans(stats.SEGS[i], c)]
    obs = hist_of(lens)
    out = [f"LP2: {len(lens)} words, mean {np.mean(lens):.2f}, share by length 1..11,12+ (%): " + " ".join(f"{x:.1f}" for x in 100 * obs / obs.sum()), ""]
    out.append("independent draws from a parametric family, fitted by minimum G (df = 11 - parameters):")
    for name, (k, fn, t0) in FAMILIES.items():
        best = None
        for start in (t0, [x + 0.3 for x in t0], [x - 0.3 for x in t0]):
            r = minimize(lambda t: g_stat(obs, fn(t)), start, method="Nelder-Mead", options={"xatol": 1e-6, "fatol": 1e-8, "maxiter": 4000})
            if best is None or r.fun < best.fun:
                best = r
        df = BINS - 1 - k
        out.append(f"  {name:48s} G = {best.fun:7.1f}  df = {df}  p = {st.chi2.sf(best.fun, df):.2e}   shares " +
                   " ".join(f"{x:.1f}" for x in 100 * fn(best.x)))
    out.append("")
    out.append("for comparison, the best English-based fits (wordlen_languages.py): +1 rune in 40% of multi-rune words G = 20.4 (df 10, p = 0.026); "
               "2-rune words missing G = 17.1 (df 10, p = 0.07).")
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "wordlen_parametric.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
