"""H9 of docs/HYPOTHESES.md: can a two-time pad between LP2 sections be detected under the skip rule at all?

    python work/pad_reuse_power.py           # writes results/analysis/pad_reuse_power.txt

Open lead 3 of docs/SESSION_LOG.md asked for a drift-aware key-reuse test. Before running one on LP2, measure its power.
Two English sections of n runes are enciphered with the SAME random pad from the same start, each with its own anti-repeat
skips (collision avoided w.p. 0.82), so their relative alignment drifts as the difference of the two skip counts.
Statistics (computed for the true pair and for a pair whose second section used an independent pad):
  band: coincidences c_a[i] == c_b[i + delta] summed over |delta| <= w around the start alignment (the matched filter
        of drift_period.py, here for one reuse), as a z-score against the band's own expectation;
  dp:   best monotone path over delta (Viterbi), match +ln(kappa_E / kappa_R), mismatch ln((1 - kappa_E) / (1 - kappa_R)),
        a change of delta by one costs ln(1 / 0.028) (the skip rate).
Power = the fraction of true pairs scoring above the 95th percentile of the independent-pad pairs.
"""
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sim  # noqa: E402

N = 29
KE, KR = 0.0617, 1 / 29            # English rune coincidence rate (IoC ~1.79) and random
W = 25


def encipher(p, pad, rng, keep=0.18):
    out, j, prev = [], 0, -1
    for x in p:
        y = (x + pad[j]) % N
        j += 1
        while y == prev and rng.random() >= keep:
            y = (x + pad[j]) % N
            j += 1
        out.append(y)
        prev = y
    return np.array(out)


def band_z(a, b, w):
    n = min(len(a), len(b)) - w
    hits = sum(int((a[w:n] == b[w + d:n + d]).sum()) for d in range(-w, w + 1))
    trials = (2 * w + 1) * (n - w)
    return (hits - trials * KR) / np.sqrt(trials * KR * (1 - KR))


def dp_score(a, b, w):
    m, mm, jump = np.log(KE / KR), np.log((1 - KE) / (1 - KR)), np.log(0.028)
    n = min(len(a), len(b)) - w
    deltas = np.arange(-w, w + 1)
    v = np.zeros(len(deltas))
    for i in range(w, n):
        e = np.where(a[i] == b[i + deltas], m, mm)
        best_nb = np.maximum(np.r_[-np.inf, v[:-1]], np.r_[v[1:], -np.inf]) + jump
        v = np.maximum(v, best_nb) + e
        v = np.maximum(v, 0.0)                       # local alignment: a reuse may cover part of the section
    return float(v.max())


def main():
    eng = np.array(sim.english_runes())
    rng = random.Random(3301)
    out = ["H9 power of a drift-aware two-time-pad test between two sections (skip rule, keep 0.18)", ""]
    for n in (400, 1500, 3000):
        res = {"band": ([], []), "dp": ([], [])}
        for rep in range(40):
            s = rng.randrange(len(eng) - 2 * n - 10)
            pa, pb = eng[s:s + n], eng[s + n + 5:s + 2 * n + 5]
            pad = [rng.randrange(N) for _ in range(3 * n)]
            other = [rng.randrange(N) for _ in range(3 * n)]
            a, b, b0 = encipher(pa, pad, rng), encipher(pb, pad, rng), encipher(pb, other, rng)
            for name, f in (("band", band_z), ("dp", dp_score)):
                res[name][0].append(f(a, b, W))
                res[name][1].append(f(a, b0, W))
        for name, (t, z) in res.items():
            thr = np.percentile(z, 95)
            power = np.mean(np.array(t) > thr)
            out.append(f"  n = {n:4d} runes  {name:4s}: true {np.mean(t):7.2f} +- {np.std(t):5.2f}, independent pad "
                       f"{np.mean(z):7.2f} +- {np.std(z):5.2f}; power at the 5% level {power:.2f}")
    out += ["", "Reading: a usable test needs power near 1 at LP2's section sizes (400-3,000 runes) before its negative means "
                "anything; below that, pad reuse between sections cannot be decided from the ciphertext alone."]
    text = "\n".join(out) + "\n"
    print(text)
    with open(os.path.join(os.path.dirname(HERE), "results", "analysis", "pad_reuse_power.txt"), "w", newline="\n",
              encoding="utf-8") as fh:
        fh.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
