"""Periodic keys in the step domain (relative-rank chain cipher, research note C1): coincidences of the step classes at lag P.

If the key of the cipher D_i = 1 + (q_i + K_j) mod 28 (variant A) or D_i = 2^(q_i + L_j) mod 29 (variant B) has period P,
the step classes satisfy J_i - J_{i+P} = q_i - q_{i+P}, so J_i == J_{i+P} about 6.5% of the time (English) instead of 1/28.
Zero steps (doublets, the "ditto" of the model) either consume a key value (mode keep: the lag is in text positions) or
not (mode drop: the zero steps are removed first, the lag is in non-zero steps). Both are scanned, for variant A (J = D-1)
and B (J = log2 D), inside every section and over the sections concatenated in book order.

    python work/step_periodicity.py          # -> results/analysis/step_periodicity.txt
"""
import os
import sys

import numpy as np

import lp
import stats

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "kscreen"))
import step28  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
Q = 29
NC = 28
LOG2 = np.zeros(Q, np.int64)
for _e in range(NC):
    LOG2[pow(2, _e, Q)] = _e
MAXLAG = 3000


def classes(c, prev, variant, mode):
    """step classes of the ciphertext c (previous rune `prev`), -1 for a zero step; mode drop removes the zero steps"""
    J = step28.step_classes(c, prev, variant).astype(np.int64)
    J[J == 255] = -1
    return J[J >= 0] if mode == "drop" else J


def lag_stats(J, max_lag):
    """(pairs, equal pairs) at lags 0..max_lag, counting only pairs where both entries are usable, via FFT"""
    n = len(J)
    max_lag = min(max_lag, n - 1)
    size = 1 << (2 * n - 1).bit_length()
    valid = (J >= 0).astype(float)
    fv = np.fft.rfft(valid, size)
    pairs = np.fft.irfft(fv * np.conj(fv), size)[:max_lag + 1]
    eq = np.zeros(size)
    for x in range(NC):
        f = np.fft.rfft((J == x).astype(float), size)
        eq += np.fft.irfft(f * np.conj(f), size)
    return np.rint(pairs).astype(np.int64), np.rint(eq[:max_lag + 1]).astype(np.int64)


def scan(J, max_lag=MAXLAG, min_pairs=300):
    """z of the equal-pair count at every lag >= 2 with enough pairs: (lags, z)"""
    pairs, eq = lag_stats(J, max_lag)
    f = np.bincount(J[J >= 0], minlength=NC) / max(1, (J >= 0).sum())
    S = float((f ** 2).sum())
    lags = np.arange(len(pairs))
    ok = (lags >= 2) & (pairs >= min_pairs)
    z = (eq - pairs * S) / np.sqrt(np.maximum(pairs * S * (1 - S), 1e-9))
    return lags[ok], z[ok]


def sections():
    out = []
    for i in stats.UNSOLVED:
        c = np.array(lp.runes_of(stats.SEGS[i]))
        prev = int(lp.runes_of(stats.SEGS[i - 1])[-1]) if i > 7 else -1
        out.append((i, c, prev))
    return out


def planted(rng, variant, mode, period, n=3000):
    """English classes under a key of the given period: the step stream the scan must find"""
    import attack
    toks = attack.synthetic_tokens(n + 200, start=int(rng.integers(5000, 40000)))
    p = np.array(lp.runes_of(toks))[:n]
    p = np.where(p == 14, 6, p)
    q = np.where(p > 14, p - 1, p)
    key = np.resize(rng.integers(0, NC, period), len(q) + 10)           # the periodic key, in the class domain
    ditto = rng.random(len(q)) < 0.0066
    return step28.encrypt(q, key, variant, mode, 1, 0, ditto, prev=3)


def main():
    rng = np.random.default_rng(1)
    out = []
    P = out.append
    P(f"Step-domain periodic-key scan, lags 2..{MAXLAG}: z = (equal pairs - pairs*S)/sd, S = sum f^2 of the step classes")
    P("")
    P("Controls (English classes, key of the given period, one 3000-step section; the scan must put the planted lag first):")
    ctl_ok = True
    for variant in ("A", "B", "C"):
        for mode in ("drop", "keep"):
            for period in (97, 400, 1200):
                c, prev = planted(rng, variant, mode, period)
                lags, z = scan(classes(c, prev, variant, mode))
                k = int(np.argmax(z))
                hit = int(lags[k]) % period == 0
                found = hit and z[k] > 5.5
                ctl_ok &= found or period > 800        # a period of 1200 has only 1800 pairs in 3000 steps: power, not a gate
                P(f"  planted {variant}/{mode:4s} period {period:5d}: best lag {int(lags[k]):5d}  z = {z[k]:+6.2f}  "
                  f"{'found' if found else 'below 5.5 (low power at this period)' if period > 800 else 'MISSED'}")
    nulls = []
    for _ in range(20):
        c = rng.integers(0, Q, 3000)
        nulls.append(max(scan(classes(c, 3, v, m))[1].max() for v in ("A", "B", "C") for m in ("drop", "keep")))
    P(f"  null (20 random sections, max over the 4 settings): max z {max(nulls):.2f}, median {np.median(nulls):.2f}")
    P("")
    P("LP2 (max z over lags; the largest of ~3,000 lags x settings is about 4 by chance):")
    secs = sections()
    allz = []
    for variant in ("A", "B", "C"):
        for mode in ("drop", "keep"):
            rows = []
            for i, c, prev in secs:
                lags, z = scan(classes(c, prev, variant, mode))
                if len(z):
                    k = int(np.argmax(z))
                    rows.append((z[k], int(lags[k]), f"0.{i}"))
            Jcat = np.concatenate([classes(c, prev, variant, "keep") for _, c, prev in secs])
            if mode == "drop":
                Jcat = Jcat[Jcat >= 0]
            lags, z = scan(Jcat, max_lag=MAXLAG)
            k = int(np.argmax(z))
            rows.sort(reverse=True)
            top = ", ".join(f"{s} z={zz:+.2f}@{l}" for zz, l, s in rows[:3])
            P(f"  {variant}/{mode:4s}: concatenated sections: max z {z[k]:+.2f} at lag {int(lags[k])}; per section, top 3: {top}")
            allz += [rows[0][0], z[k]]
    obs = max(allz)
    reps = 40
    nullmax = []
    for _ in range(reps):                      # the same statistic on random sections of LP2's lengths (anti-repeat rule included)
        fake = []
        for i, c, prev in secs:
            r, last = [], 3
            for _ in range(len(c)):
                x = int(rng.integers(0, Q))
                while x == last and rng.random() < 0.82:
                    x = int(rng.integers(0, Q))
                r.append(x)
                last = x
            fake.append((i, np.array(r), prev))
        m = 0.0
        for variant in ("A", "B", "C"):
            for mode in ("drop", "keep"):
                for i, c, prev in fake:
                    z = scan(classes(c, prev, variant, mode))[1]
                    m = max(m, z.max() if len(z) else 0)
                Jcat = np.concatenate([classes(c, prev, variant, "keep") for _, c, prev in fake])
                Jcat = Jcat[Jcat >= 0] if mode == "drop" else Jcat
                m = max(m, scan(Jcat, max_lag=MAXLAG)[1].max())
        nullmax.append(m)
    P(f"  largest z of all scopes and settings: LP2 {obs:.2f}; {reps} random replicates of the same statistic: "
      f"median {np.median(nullmax):.2f}, max {max(nullmax):.2f}, replicates >= LP2: {sum(x >= obs for x in nullmax)}")
    P("")
    P("controls " + ("passed" if ctl_ok else "FAILED"))
    text = "\n".join(out)
    print(text)
    dest = os.path.join(HERE, "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "step_periodicity.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write(text + "\n")
    return 0 if ctl_ok else 1


if __name__ == "__main__":
    sys.exit(main())
