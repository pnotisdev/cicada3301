"""Exact raw-spend moments and matched-search statistics. Nothing runs on import.

See DERIVATION.md. Hold-key numerical predictions are intentionally not supplied:
a reused colliding key needs a plaintext law. The guarded kernel is included in
conditional likelihoods, not falsely put through the raw two-point recurrence.
"""
from __future__ import annotations

from fractions import Fraction as F
import math
import random

Q, ORDER, FIXED = 29, 28, 8
DESIGN_Q = F(81, 100)


def transform(x, exponent):
    return (FIXED + pow(-2, exponent % ORDER, Q) * (x - FIXED)) % Q


def templates():
    out = []
    for exponent, label in ((0, "I"), (1, "T")):
        for lag in range(1, 9):
            out.append((f"{label}_{lag}", ((lag, exponent, F(1)),)))
    for w in (F(1, 4), F(1, 2), F(3, 4)):
        out.append((f"mix_I5_T6_w={w}", ((5, 0, w), (6, 1, 1 - w))))
    return out


def baseline_probability(y, previous, q=DESIGN_Q):
    delta = (1 - q) / Q
    return delta if y == previous else (1 - delta) / (Q - 1)


def repair_distribution(history, taps, *, guarded=False):
    """Exact repair-emission distribution, including unavailable-tap fallback."""
    if not history or sum(w for _, _, w in taps) != 1:
        raise ValueError("Need a previous output and normalized tap weights")
    a = history[-1]
    out = [F(0)] * Q
    for d, e, w in taps:
        r = transform(history[-d], e) if len(history) >= d else None
        if r is None or (guarded and r == a):
            for y in range(Q):
                if y != a:
                    out[y] += w / (Q - 1)
        else:
            out[r] += w
    return out


def kernel(history, taps, q=DESIGN_Q, *, guarded=False):
    if not history:
        return [F(1, Q)] * Q
    a, rho = history[-1], q / Q
    repair = repair_distribution(history, taps, guarded=guarded)
    return [F(1, Q) - (rho if y == a else 0) + rho * repair[y] for y in range(Q)]


def independent_overlay_kernel(history, taps, q=DESIGN_Q, *, guarded=False):
    if not history:
        return [F(1, Q)] * Q
    rho, a = q / Q, history[-1]
    b = [(1 - (q if y == a else 0)) / (Q - q) for y in range(Q)]
    repair = repair_distribution(history, taps, guarded=guarded)
    return [(1 - rho) * b[y] + rho * repair[y] for y in range(Q)]


def moments(length, taps, q=DESIGN_Q, check=None):
    """W[j,i,h], exact fractions; one longest word prefix suffices for all means."""
    if not 1 <= length <= 64 or sum(w for _, _, w in taps) != 1:
        raise ValueError("Local prefix outside budget or invalid weights")
    lam, rho = -q / (Q - 1), q / Q
    zero = (F(1),) + (F(0),) * (ORDER - 1)
    pairs = {}

    def get(j, parent):
        if j == parent:
            return zero
        if j < parent:
            return pairs[j, parent]
        reverse = pairs[parent, j]
        return tuple(reverse[(-h) % ORDER] for h in range(ORDER))

    for i in range(1, length):
        if check:
            check()
        active = [(d, e, w) for d, e, w in taps if d <= i]
        s = sum((w for _, _, w in active), F(0))
        beta = lam + rho * s / (Q - 1)
        for j in range(i):
            prev = get(j, i - 1)
            row = [beta * v for v in prev]
            for d, e, w in active:
                source = get(j, i - d)
                for h, v in enumerate(source):
                    row[(h + e) % ORDER] += rho * w * v
            pairs[j, i] = tuple(row)
    return pairs


def pair_probability(weights, x, y):
    return F(1, Q * Q) + sum(
        (v * ((1 if y == transform(x, h) else 0) - F(1, Q)) / Q
         for h, v in enumerate(weights)), F(0))


def relation_probabilities(weights, exponent):
    z = sum(weights, F(0))
    return {
        "any_source": F(1, Q) + F(Q - 1, Q) * weights[exponent],
        "source_8": (1 + (Q - 1) * z) / (Q * Q),
        "each_source_other_than_8": (1 + Q * weights[exponent] - z) / (Q * Q),
    }


def exact_tables(n_by_position, q=DESIGN_Q, check=None):
    """Compressed per-rune classes are exact, not a fit: all non-8 labels share a mean."""
    position_rows, aggregate_rows = [], []
    length = len(n_by_position)
    lam = -q / (Q - 1)
    for name, taps in templates():
        weights = moments(length, taps, q, check)
        totals = {}
        for (j, i), vector in sorted(weights.items()):
            lag, n = i - j, n_by_position[i]
            base = (lam ** lag,) + (F(0),) * (ORDER - 1)
            for e, relation in ((0, "I"), (1, "T")):
                prob = relation_probabilities(vector, e)
                baseline = relation_probabilities(base, e)
                row = dict(rule=name, relation=relation, lag=lag, earlier_position=j,
                           target_position=i, pairs=n)
                for key, value in prob.items():
                    row[f"expected_{key}"] = str(n * value)
                    row[f"excess_vs_markov_{key}"] = str(n * (value - baseline[key]))
                    iid = F(1, Q) if key == "any_source" else F(1, Q * Q)
                    row[f"excess_vs_iid_{key}"] = str(n * (value - iid))
                position_rows.append(row)
                total = totals.setdefault((lag, relation), {"pairs": 0, "expect": {}, "markov": {}})
                total["pairs"] += n
                for key in prob:
                    total["expect"][key] = total["expect"].get(key, F(0)) + n * prob[key]
                    total["markov"][key] = total["markov"].get(key, F(0)) + n * baseline[key]
        for (lag, relation), total in sorted(totals.items()):
            row = dict(rule=name, relation=relation, lag=lag, pairs=total["pairs"])
            for key, value in total["expect"].items():
                row[f"expected_{key}"] = str(value)
                row[f"excess_vs_markov_{key}"] = str(value - total["markov"][key])
                iid = F(1, Q) if key == "any_source" else F(1, Q * Q)
                row[f"excess_vs_iid_{key}"] = str(value - total["pairs"] * iid)
            aggregate_rows.append(row)
    return position_rows, aggregate_rows


def scan(c, local, check=None, q=float(DESIGN_Q)):
    """Whole selection: 812 maps x 8 lags x raw/guarded, plus three fixed mixtures.

    Three small histograms per lag make this fast enough for a bounded human gate.
    The returned scores are conditional-history log likelihoods, not decryption.
    """
    import numpy as np
    c, local = np.asarray(c, dtype=np.int64), np.asarray(local, dtype=np.int64)
    aa = np.repeat(np.arange(1, Q), Q)
    bb = np.tile(np.arange(Q), Q - 1)
    maps = (aa[:, None] * np.arange(Q)[None, :] + bb[:, None]) % Q
    src_rows = np.arange(Q)[None, :]
    log_b = -math.log1p(q / (Q - 1))
    log_hit, log_keep = math.log1p(q), math.log1p(-q)
    candidates, primary = [], []
    for lag in range(1, 9):
        if check:
            check()
        idx = np.flatnonzero(local >= lag)
        if not len(idx):
            continue
        x, a, y = c[idx - lag], c[idx - 1], c[idx]
        dbl = y == a

        def hist(v, mask=None):
            values = x * Q + v
            if mask is not None:
                values = values[mask]
            return np.bincount(values, minlength=Q * Q).reshape(Q, Q)

        # h: tap hits not at doublets; z: replacement=a; t: replacement=a=y.
        h, z, t = hist(y, ~dbl), hist(a), hist(y, dbl)
        hits = h[src_rows, maps].sum(axis=1)
        repeat_source = z[src_rows, maps].sum(axis=1)
        repeat_hit = t[src_rows, maps].sum(axis=1)
        n_non = int((~dbl).sum())
        raw = n_non * log_b + hits * log_hit - repeat_hit * log_keep
        guard = (n_non - repeat_source + repeat_hit) * log_b + hits * log_hit
        for guarded, scores in ((False, raw), (True, guard)):
            index = int(scores.argmax())
            candidates.append(dict(lag=lag, a=int(aa[index]), b=int(bb[index]), guarded=guarded,
                                   score=float(scores[index])))
            for name, ma, mb in (("I", 1, 0), ("T", Q - 2, 24)):
                p = (ma - 1) * Q + mb
                primary.append(dict(rule=f"{name}_{lag}", guarded=guarded, score=float(scores[p])))
    idx = np.flatnonzero(local >= 1)
    if len(idx):
        y, a = c[idx], c[idx - 1]
        off = (y != a).astype(float)
        delta = (1 - q) / Q
        base = np.where(y == a, delta, (1 - delta) / (Q - 1))
        five = (local[idx] >= 5) * (y == np.roll(c, 5)[idx]) - (local[idx] >= 5) * off / (Q - 1)
        six = (local[idx] >= 6) * (y == (24 - 2 * np.roll(c, 6)[idx]) % Q) - (local[idx] >= 6) * off / (Q - 1)
        # Wrapped values occur only in inactive masks; they carry exactly zero weight.
        for weight in (F(1, 4), F(1, 2), F(3, 4)):
            w = float(weight)
            probability = base + (q / Q) * (w * five + (1 - w) * six)
            score = float(np.log(probability / base).sum())
            item = dict(rule=f"mix_I5_T6_w={weight}", score=score)
            candidates.append(item)
            primary.append(item)
    best = max(candidates, key=lambda r: r["score"])
    return dict(maximum=best["score"], best=best,
                best_primary=max(primary, key=lambda r: r["score"]), primary=primary)


def budget_evalue(c, local, q_max=1.0):
    """Universal one-output, fresh-uniform collision-budget falsifier; Eq. (17).

    Log-domain arithmetic; arbitrary repair outputs already maximized out.
    The explicit affine/lag selection penalty is conservative, not optional.
    """
    if not 0 <= q_max <= 1:
        raise ValueError("Invalid repair-probability bound")
    idx = [i for i, p in enumerate(local) if p >= 6]
    stats, overlap, both, total = [], 0, 0, 0
    for i in idx:
        a, b, d = c[i - 1], c[i - 5], transform(c[i - 6], 1)
        same = b == d
        h_old = int(a == b) + int(a == d)
        h = int(c[i] == b) + int(c[i] == d)
        overlap += int(same)
        both += int(h == 2)
        total += h
        stats.append((same, h_old))
    logs = []
    for lam in (1 / 16, 1 / 8, 1 / 4, 1 / 2, 1):
        denominator = 0.0
        for same, h_old in stats:
            base = ((28 + math.exp(2 * lam)) if same else (27 + 2 * math.exp(lam))) / Q
            bound = base + (q_max / Q) * (math.exp(lam * (1 + same)) - math.exp(lam * h_old))
            denominator += math.log(bound)
        logs.append(lam * total - denominator)
    hi = max(logs)
    mixture = hi + math.log(sum(math.exp(v - hi) for v in logs)) - math.log(len(logs))
    choices = (8 * 28 * 29) ** 2
    adjusted = mixture - math.log(choices)
    n = len(idx)
    return dict(eligible=n, observed_source_overlap=overlap, observed_double_hits=both,
                observed_sum_of_hits=total, q_max=q_max, per_lambda_log_e=logs,
                raw_mixture_log_e=mixture, selection_choices=choices,
                selection_adjusted_log_e=adjusted, reject_budget=adjusted >= math.log(20),
                design_q_predictable_upper_count=str(F(2 * n, Q) + DESIGN_Q / Q * (n + overlap)),
                meaning="One-output collision budget only; not collision causality or a decryption")


def conditional_null(lengths, doublets, seed):
    """Exact H0 conditional on each section's doublet count (not rune shuffling)."""
    rng, out = random.Random(seed), []
    for n, d in zip(lengths, doublets):
        repeat = set(rng.sample(range(1, n), d))
        section = [rng.randrange(Q)]
        for i in range(1, n):
            if i in repeat:
                section.append(section[-1])
            else:
                v = rng.randrange(Q - 1)
                section.append(v + (v >= section[-1]))
        out.extend(section)
    return out


def section_doublets(c, lengths):
    out, start = [], 0
    for n in lengths:
        out.append(sum(c[i] == c[i - 1] for i in range(start + 1, start + n)))
        start += n
    return out


def randomization_test(c, local, lengths, seed, replicates=99, check=None):
    observed = scan(c, local, check)
    ds = section_doublets(c, lengths)
    maxima = []
    for rep in range(replicates):
        if check:
            check()
        null = conditional_null(lengths, ds, seed + rep)
        maxima.append(scan(null, local, check)["maximum"])
    p = (1 + sum(t >= observed["maximum"] for t in maxima)) / (replicates + 1)
    return dict(observed=observed, null_maxima=maxima, p_mc=p, flag=p <= 0.05,
                replicates=replicates, conditioned_doublets=ds, seed=seed)


def collision_plant(local, lengths, lag, exponent, seed, q=float(DESIGN_Q)):
    """Forward coins and candidate draws, independent of the likelihood formula.

    Spend-key case: uniform fresh candidates suffice for any fixed plaintext.
    True repair events are returned solely to audit controls, not used by scan().
    """
    rng, c, events = random.Random(seed), [], []
    starts, at = set(), 0
    for n in lengths:
        starts.add(at)
        at += n
    for i, p in enumerate(local):
        candidate = rng.randrange(Q)
        if i not in starts and candidate == c[-1] and rng.random() < q:
            if p >= lag:
                value = transform(c[i - lag], exponent)
            else:
                v = rng.randrange(Q - 1)
                value = v + (v >= c[-1])
            events.append(i)
            candidate = value
        c.append(candidate)
    return c, events
