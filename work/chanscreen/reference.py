"""Full-state channel forward reference. No beam, band, or iid-key tail shortcut."""
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
import json
import math
import numpy as np

CHANNELS = json.loads(Path(__file__).with_name('channels.json').read_text())


def arcs(key, j, p, a, sign, q, Q, channel):
    """Yield (output or None=FAILURE, next pointer, mass). Exact if q is Fraction."""
    spec = CHANNELS[channel]
    kind = spec['kernel']
    if kind == 'unimplemented':
        raise ValueError('extension kernel not implemented')
    if j >= len(key):
        yield None, j, 1
        return
    x = (p + sign * key[j]) % Q
    if a is None or x != a:
        yield x, j + 1, 1
    elif kind == 'substitute':
        yield x, j + 1, 1 - q
        for y in range(Q):
            if y != a:
                yield y, j + spec['repair_advance'], q / (Q - 1)
    elif kind == 'coin':
        if j + 1 >= len(key):
            yield None, len(key), 1
        else:
            yield x, j + 2, 1 - q
            if j + 2 >= len(key):
                yield None, len(key), q
            else:
                yield (p + sign * key[j + 2]) % Q, j + 3, q
    elif kind == 'retry':
        weight, t = 1, 0
        while True:
            h = j + t
            if h >= len(key):
                yield None, len(key), weight
                break
            y = (p + sign * key[h]) % Q
            cap = spec['max_redraws']
            if y != a or (cap is not None and t == cap):
                yield y, h + 1, weight
                break
            yield y, h + 1, weight * (1 - q)
            weight *= q
            t += 1
    else:
        raise ValueError('unknown kernel')


def rational_forward(cipher, key, off, sign, q, channel, pi, L):
    Q = len(pi)
    states = {(off, -1): F(1)}
    for i, y in enumerate(cipher):
        nxt = defaultdict(F)
        for (j, r), mass in states.items():
            for p, lp in enumerate(pi if r == -1 else L[r]):
                if not mass * lp:
                    continue
                for emitted, h, w in arcs(key, j, p, cipher[i-1] if i else None, sign, q, Q, channel):
                    if emitted == y and w:
                        nxt[h, p] += mass * lp * w
        states = nxt
    return sum(states.values(), F(0))


def event_tree(key, off, sign, q, channel, pi, L, n, mutant=None):
    """Independent generative enumeration, deliberately NOT using arcs/DP.

    Return distribution over complete outputs and failed prefixes; no merging
    until leaves. Suitable only for tiny cases. Mutation hooks exercise witnesses.
    """
    Q = len(pi)
    outputs, failed = defaultdict(F), defaultdict(F)

    def emit(prefix, j, p, w, y):
        walk(prefix + (y,), j, p, w)

    def attempt(prefix, j, p, w, tries=0):
        if j >= len(key):
            failed[prefix] += w
            return
        x = (p + sign * key[j]) % Q
        a = prefix[-1] if prefix else None
        if x != a:
            emit(prefix, j + 1, p, w, x)
        elif channel in ('hold', 'spend'):
            emit(prefix, j + 1, p, w * (1-q), x)
            step = int(channel == 'spend' or mutant == 'hold_spends')
            den = Q if mutant == 'replacement_denominator' else Q-1
            for y in range(Q):
                if y != a:
                    emit(prefix, j + step, p, w*q/den, y)
        elif channel == 'coin':
            coin = 0 if mutant == 'coin_missing_slot' else 1
            if j + coin >= len(key):
                failed[prefix] += w
            else:
                emit(prefix, j + 1 + coin, p, w*(1-q), x)
                if j + 1 + coin >= len(key):
                    failed[prefix] += w*q
                else:
                    y = (p + sign * key[j+1+coin]) % Q
                    emit(prefix, j+2+coin, p, w*q, y)
        elif channel in ('skip', 'skip5'):
            if channel == 'skip5' and tries == 5:
                emit(prefix, j+1, p, w, x)
            else:
                emit(prefix, j+1, p, w*(1-q), x)
                if not (mutant == 'skip_drops_tail' and tries == 1):
                    attempt(prefix, j+1, p, w*q, tries+1)
        else:
            raise ValueError(channel)

    def walk(prefix, j, prev, w):
        if not w:
            return
        if len(prefix) == n:
            outputs[prefix] += w
            return
        for p, lp in enumerate(pi if prev is None else L[prev]):
            attempt(prefix, j, p, w*lp)

    walk((), off, None, F(1))
    return {k:v for k,v in outputs.items() if v}, {k:v for k,v in failed.items() if v}


def validate(cipher, key, off, sign, q, channel, pi, L):
    Q = len(pi)
    if Q < 2 or np.shape(L) != (Q, Q) or sign not in (-1, 1):
        raise ValueError('invalid model')
    if not 0 <= off <= len(key) or not 0 <= q <= 1:
        raise ValueError('offset or q')
    if any(not 0 <= x < Q for x in (*cipher, *key)):
        raise ValueError('symbol out of range')
    if np.any(np.asarray(pi) < 0) or np.any(np.asarray(L) < 0):
        raise ValueError('negative probability')
    if not np.isclose(sum(pi), 1, atol=1e-14, rtol=0) or not np.allclose(np.sum(L, axis=1), 1, atol=1e-14, rtol=0):
        raise ValueError('unnormalized model')
    if channel not in CHANNELS or CHANNELS[channel]['kernel'] == 'unimplemented':
        raise ValueError('unsupported channel')


def forward(cipher, key, off, sign, q, channel, pi, L):
    """NumPy float64 full forward; log joint probability of observed output.

    General transition implementation favors auditability over speed. Each row
    is an absolute pointer (including exhausted m); columns are last plaintext.
    """
    pi, L = np.asarray(pi, dtype=np.float64), np.asarray(L, dtype=np.float64)
    validate(cipher, key, off, sign, q, channel, pi, L)
    Q, m = len(pi), len(key)
    states = np.zeros((m+1, Q), dtype=np.float64)
    total = 0.0
    for i, y in enumerate(cipher):
        predictive = states @ L if i else np.zeros_like(states)
        if not i:
            predictive[off] = pi
        nxt = np.zeros_like(states)
        for j in np.flatnonzero(predictive.sum(axis=1)):
            for p in range(Q):
                v = predictive[j, p]
                if not v:
                    continue
                for emitted, h, w in arcs(key, int(j), p, cipher[i-1] if i else None, sign, q, Q, channel):
                    if emitted == y:
                        nxt[h, p] += v*w
        z = float(nxt.sum())
        if not z:
            return -math.inf
        total += math.log(z)
        states = nxt/z
    return total


def score(cipher, key, off, sign, q, channel, pi, L, engine=forward):
    Q = len(pi)
    lu = engine(cipher, key, off, sign, q, channel, np.full(Q, 1/Q), np.full((Q,Q), 1/Q))
    ll = engine(cipher, key, off, sign, q, channel, pi, L)
    return dict(log_L=ll, log_U=lu, score=ll-lu if math.isfinite(lu) else None,
                discarded_tail_mass=0.0)
