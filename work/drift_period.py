"""Periodic keys under the anti-repeat skip rule: a drift-aware period scan with power curves.

The old lag scans (crib.lag_scan) look for extra ciphertext coincidences at lag P. Under the skip rule
the key pointer runs ahead of the rune index by one at every skip, so two runes that used the same key
element are P - Δd apart, where Δd is the number of skips between them (≈ Poisson(r·P), r ≈ 0.028 per
rune for LP2's measured doublet deficit). The excess is smeared over a band of lags just below P and the
plain lag scan loses it for P beyond ~60. This scan applies a matched filter over that band (and the
bands below 2P, 3P, ...), calibrates the noise on LP2 itself, and measures its power on Emerson text
enciphered with random periodic keys under the same rule.

    python drift_period.py              # power curve, then the LP2 scan
    python drift_period.py --quick      # fewer control trials
"""
import argparse
import os
import random
import sys

import numpy as np

import lp
import sim
import stats

N = lp.N
HERE = os.path.dirname(os.path.abspath(__file__))


def lag_coincidences(c, max_lag):
    """A[L] = #{i : c[i] == c[i+L]} for L = 0..max_lag, via FFT per symbol."""
    c = np.asarray(c)
    n = len(c)
    size = 1 << (2 * n - 1).bit_length()
    A = np.zeros(size)
    for x in range(N):
        f = np.fft.rfft((c == x).astype(float), size)
        A += np.fft.irfft(f * np.conj(f), size)
    return np.rint(A[:max_lag + 1]).astype(np.int64)


def poisson_pmf(mu, kmax):
    k = np.arange(kmax + 1)
    from scipy.special import gammaln
    return np.exp(k * np.log(max(mu, 1e-12)) - mu - gammaln(k + 1))


def matched_scan(c, periods, rate, harmonics=4):
    """Z(P) for each P: weighted excess of coincidences in the drift bands below k*P, k = 1..harmonics."""
    n = len(c)
    max_lag = n - 1
    A = lag_coincidences(c, max_lag).astype(float)
    f = np.bincount(c, minlength=N) / n
    s2 = float((f ** 2).sum())
    L = np.arange(max_lag + 1)
    E = (n - L) * s2
    excess = A - E
    Z = np.zeros(len(periods))
    for pi, P in enumerate(periods):
        num = var = 0.0
        for k in range(1, harmonics + 1):
            span = k * P
            if span >= n - 50:
                break
            mu = rate * span
            kmax = int(mu + 6 * np.sqrt(mu + 1) + 3)
            w = poisson_pmf(mu, kmax)                       # w[d] = P(Δd = d)
            lags = span - np.arange(kmax + 1)
            ok = (lags >= 2) & (lags <= max_lag)
            if not ok.any():
                continue
            lw = lags[ok]
            # expected excess per lag ∝ pairs * w; matched-filter weight = that expectation
            wt = (n - lw) * w[ok]
            num += float((wt * excess[lw]).sum())
            var += float((wt ** 2 * E[lw]).sum())
        Z[pi] = num / np.sqrt(var) if var > 0 else 0.0
    return Z


def encrypt_periodic(plain, P, q=0.82, seed=0):
    """Random period-P key, collision-skip rule with skip probability q (sim.make_skip_key semantics)."""
    R = random.Random(seed)
    key = [R.randrange(N) for _ in range(P)]
    out, j = [], 0
    for t in plain:
        y = (t + key[j % P]) % N
        j += 1
        while out and y == out[-1] and R.random() < q:
            y = (t + key[j % P]) % N
            j += 1
        out.append(y)
    return out


def lp2_stream():
    segs = stats.SEGS
    return [x for i in stats.UNSOLVED for x in lp.runes_of(segs[i])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--rate", type=float, default=None, help="skips per rune (default: from LP2's doublet deficit)")
    ap.add_argument("--max-period", type=int, default=6400)
    args = ap.parse_args()
    c = np.array(lp2_stream())
    n = len(c)
    d_obs = int((c[1:] == c[:-1]).sum())
    d_exp = (n - 1) / N
    rate = args.rate if args.rate is not None else (d_exp - d_obs) / n
    print(f"LP2 stream: {n} runes, doublets {d_obs} vs {d_exp:.0f} expected -> skip rate r = {rate:.4f} per rune")
    periods = np.arange(2, args.max_period + 1)

    # ---- null first: random runes under LP2's anti-repeat rule, scanned exactly like LP2
    trials = 3 if args.quick else 8
    R = random.Random(7)
    null_max = []
    for t in range(trials):
        x = []
        for _ in range(n):
            y = R.randrange(N)
            while x and y == x[-1] and R.random() < 0.82:
                y = R.randrange(N)
            x.append(y)
        null_max.append(float(matched_scan(np.array(x), periods, rate).max()))
    thr = max(null_max)
    print(f"null (random runes, same rule): max Z over P=2..{args.max_period}: "
          f"{' '.join(f'{z:.2f}' for z in null_max)}  -> detection threshold {thr:.2f}")

    # ---- power curve on synthetic English (Emerson) with random periodic keys under the skip rule
    eng = sim.english_runes()
    print("\npower (Emerson, LP2 length, random periodic key, skip rule q=0.82):")
    print("    P   Z(true P) mean/min   detected (Z(true P) above the null maximum)")
    for P in (30, 60, 100, 200, 400, 800, 1600, 3200):
        zs = []
        for t in range(trials):
            start = 1000 + 17000 * t
            plain = eng[start:start + n]
            ct = np.array(encrypt_periodic(plain, P, seed=1000 * P + t))
            zs.append(matched_scan(ct, periods, rate)[P - 2])
        print(f"  {P:5d}  {np.mean(zs):6.1f} / {min(zs):6.1f}     {sum(z > thr for z in zs)}/{trials}", flush=True)

    # ---- LP2
    Z = matched_scan(c, periods, rate)
    order = np.argsort(Z)[::-1]
    print(f"\nLP2: max Z {Z.max():.2f} at P={periods[order[0]]}; top 12:")
    for k in order[:12]:
        print(f"  P={periods[k]:5d}  Z={Z[k]:.2f}")
    print(f"LP2 Z at r=0 (the old plain lag scan), top 3: "
          + ", ".join(f"P={periods[k]} Z={z:.2f}" for k, z in
                      sorted(enumerate(matched_scan(c, periods, 0.0, harmonics=1)), key=lambda t: -t[1])[:3]))
    verdict = "CANDIDATE" if Z.max() > thr + 1.0 else "NULL"
    print(f"\nverdict: {verdict} (LP2 max {Z.max():.2f} vs null max {thr:.2f})")
    out = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "drift_period.tsv"), "w", newline="\n") as f:
        f.write("period\tZ\n")
        for p, z in zip(periods, Z):
            f.write(f"{p}\t{z:.3f}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
