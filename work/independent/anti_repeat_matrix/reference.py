"""Declared reference channels; no engine, experiment, or search runs on import.

CATALOGUE.md defines the physical mechanisms. MATRIX.md defines the reset-oracle
metric. This is NOT a faithful finite-beam power emulator. In particular hold
numbers assume iid uniform plaintext, not English.
"""
from __future__ import annotations

from fractions import Fraction as F
from functools import lru_cache
from pathlib import Path
import sys

PREVIOUS = Path(__file__).resolve().parent.parent / "collision_substitution"
sys.path.insert(0, str(PREVIOUS))
import collision_model as CM

Q = CM.Q
DELTA = F(86, 12947)
Q0 = 1 - Q * DELTA
Q1 = Q * Q0 / (Q - 1)
QN = Q0 / (1 + DELTA)
RHO = Q0 / Q
ALPHA = Q1 / Q
KAPPA = (1 - Q1) / Q
RNULL = QN / Q
IDS = tuple(f"M{i:02}" for i in range(1, 13))
DECODERS = (("S", "S", 0, 0), ("C", "C", 0, 0),
            ("N1S", "S", 1, 0), ("N1C", "C", 1, 0),
            ("N2S", "S", 2, 0), ("N2C", "C", 2, 0),
            ("A1S", "S", 0, 1), ("A1C", "C", 0, 1),
            ("A2S", "S", 0, 2), ("A2C", "C", 0, 2))
ZERO = F(0)
ONE = F(1)


def parameters():
    return {"Q": Q, "delta": str(DELTA), "q0": str(Q0), "q1": str(Q1),
            "qN": str(QN), "rho": str(RHO), "alpha": str(ALPHA),
            "kappa": str(KAPPA), "null_stationary_fraction": str(QN / (Q + QN))}


def joint_kernel(mid, a, advance=0, nu=None, pending=None):
    """(output, key increment, plaintext increment, new pending latch) -> mass.

    M02's infinite tail is collected as key increment '>=4', with EXACT geometric
    mass. It is not truncated or redirected into an accepted finite step.
    M04 uses the explicit nu, or the declared uniform-plaintext reference.
    """
    out = {}

    def put(y, dj, dp, probability, latch=None):
        if probability:
            key = (y, dj, dp, latch)
            out[key] = out.get(key, ZERO) + probability

    def ordinary(q, extra=0):
        for y in range(Q):
            put(y, extra + 1, 1, F(1, Q) if y != a else (1 - q) / Q)

    if pending is not None:
        if mid != "M07" or pending == a:
            raise ValueError("Invalid pending-null state")
        put(pending, 1, 1, ONE)
        return out
    if mid in ("M01", "M05", "M09", "M11", "M12"):
        extra = advance if mid in ("M11", "M12") else 0
        ordinary(Q1, extra)
        for y in range(Q):
            put(y, extra + (3 if mid == "M05" else 2), 1, Q1 / (Q * Q))
    elif mid == "M02":
        ordinary(Q0)
        for y in range(Q):
            if y != a:
                put(y, 2, 1, Q0 / Q ** 2)
                put(y, 3, 1, Q0 / Q ** 3)
                put(y, ">=4", 1, Q0 / (Q ** 3 * (Q - 1)))
    elif mid == "M03":
        for y in range(Q):
            if y != a:
                put(y, 1, 1, F(1, Q))
            put(y, 3, 1, Q1 / (Q * Q))
        put(a, 2, 1, (1 - Q1) / Q)
    elif mid == "M04":
        nu = list(nu) if nu is not None else [F(1, Q)] * Q
        if sum(nu) != 1 or any(p < 0 for p in nu):
            raise ValueError("nu must be a probability distribution")
        for y in range(Q):
            put(y, 1, 1, nu[y] * (1 - (Q0 if y == a else 0)))
            if y != a:
                put(y, 0, 1, Q0 * nu[a] / (Q - 1))
    elif mid == "M06":
        # Guarded I_1 always selects the old output, hence uses U_off_previous.
        probabilities = CM.kernel([a], ((1, 0, ONE),), Q0, guarded=True)
        for y, probability in enumerate(probabilities):
            put(y, 1, 1, probability)
    elif mid == "M07":
        ordinary(QN)
        for y in range(Q):
            if y != a:
                put(y, 0, 0, QN / (Q * (Q - 1)), a)
    elif mid == "M08":
        ordinary(Q0)
        put((a + 1) % Q, 1, 1, Q0 / Q)
    elif mid == "M10":
        put(a, 0, 0, DELTA)
        for y in range(Q):
            if y != a:
                put(y, 1, 1, (1 - DELTA) / (Q - 1))
    else:
        raise ValueError(mid)
    return out


def marginal(kernel):
    out = [ZERO] * Q
    for (y, _, _, _), probability in kernel.items():
        out[y] += probability
    return out


def decoder_outputs_at_end(y, a, keys, start, mode, end):
    """Unpruned forward arc proxy, filtered by end BEFORE accessing key values.

    Matches the cited default S/C branches. Does not import/call the Rust/GPU
    engines, merge scores, simulate their beam, or handle flags implicitly.
    """
    out = []
    if mode == "S":
        for skip in range(3):
            if start + skip + 1 != end:
                continue
            p = (y - keys[start + skip]) % Q
            if all((p + keys[start + k]) % Q == a for k in range(skip)):
                out.append(p)
    elif mode == "C":
        if start + 1 + (y == a) == end:
            out.append((y - keys[start]) % Q)
        if start + 3 == end:
            p = (y - keys[start + 2]) % Q
            if (p + keys[start]) % Q == a:
                out.append(p)
    else:
        raise ValueError(mode)
    return out


@lru_cache(maxsize=None)
def once_fg(mode, h):
    # PHASE, not a promise that the current decoded plaintext is correct.
    fs = {-2: ZERO, -1: ALPHA, 0: ONE, 1: F(1, Q), 2: (1 - ALPHA) / Q ** 2}
    fc = {-2: ZERO, -1: RHO, 0: F(Q - 1, Q) + ALPHA / Q,
          1: KAPPA + ALPHA / Q, 2: (1 - ALPHA) / Q}
    gs = {-2: ZERO, -1: ONE, 0: ONE, 1: F(1, Q), 2: ZERO}
    gc = {-2: ZERO, -1: ONE, 0: ZERO, 1: F(1, Q), 2: ZERO}
    return (fs if mode == "S" else fc).get(h, ZERO), (gs if mode == "S" else gc).get(h, ZERO)


@lru_cache(maxsize=None)
def scalar_fg(mid, mode, true_advance=0, decoder_advance=0):
    d = decoder_advance
    if mid in ("M01", "M09", "M11", "M12"):
        return once_fg(mode, true_advance - d)
    if mid == "M02":
        pm = lambda m: Q0 * (Q - 1) / Q ** m
        if d < 0:
            raise ValueError("Decoder pre-advance cannot be negative")
        if d == 0:
            return ((1 - RHO / Q ** 2, 1 - F(1, Q ** 2)) if mode == "S" else
                    (F(Q - 1, Q) + pm(3), F(Q - 1, Q ** 2)))
        allowed = range(d + 1, d + 4) if mode == "S" else (d + 1, d + 3)
        return (sum((pm(m) for m in allowed), ZERO),
                sum((F(Q - 1, Q ** (m - 1)) for m in allowed), ZERO))
    if mid in ("M03", "M05"):
        if mode == "S":
            f0 = 1 - F(Q - 1, Q ** 2) if mid == "M03" else 1 - RHO
            f1 = KAPPA + ALPHA / Q if mid == "M03" else ALPHA / Q
            f, g = (f0, f1, ALPHA), (F(1, Q), F(1, Q), ONE)
        else:
            f0 = ONE if mid == "M03" else 1 - KAPPA
            f, g = (f0, ALPHA / Q, RHO), (ONE, ZERO, ONE)
        return (f[d], g[d]) if d in (0, 1, 2) else (ZERO, ZERO)
    if mid in ("M06", "M08"):
        return ((ONE if mode == "S" else 1 - DELTA), ONE) if d == 0 else (ZERO, ZERO)
    if mid == "M04":
        return ((1 - RHO if mode == "S" else F(Q - 1, Q)), ZERO) if d == 0 else (ZERO, ZERO)
    if mid == "M07":
        return ((1 - RNULL if mode == "S" else F(Q - 1, Q)), ZERO) if d == 0 else (ZERO, ZERO)
    if mid == "M10":
        raise ValueError("No would-be mod-29 collision exists in M10")
    raise ValueError(mid)


@lru_cache(maxsize=None)
def transition_and_event(mid, mode, has_null_mask, null_here, true_advance, decoder_advance):
    """2x2 substochastic PHASE matrix and post-first-avoid state vector.

    The event vector is conditional on a true avoided collision at this site.
    The reset oracle has the correct comparison value immediately before it.
    """
    if mid == "M04" and has_null_mask:
        if null_here:
            matrix = ((ZERO, RHO), (RHO / (Q - 1), RHO * (Q - 2) / (Q - 1)))
        else:
            f0 = 1 - RHO if mode == "S" else F(Q - 1, Q)
            f1 = 1 - RHO if mode == "S" else 1 - RHO - F(1, Q)
            matrix = ((f0, ZERO), (f1, ZERO))
        return matrix, ((ZERO, ONE) if null_here else (ZERO, ZERO))
    if mid == "M07" and has_null_mask:
        if null_here:
            matrix = ((ZERO, RNULL), (ZERO, ZERO))
        else:
            f = 1 - RNULL if mode == "S" else F(Q - 1, Q)
            matrix = ((f, ZERO), ((ONE if mode == "S" else ZERO), ZERO))
        return matrix, ((ZERO, ONE) if null_here else (ZERO, ZERO))
    f, g = scalar_fg(mid, mode, true_advance, decoder_advance)
    if null_here:
        f = g = ZERO
    return ((f, ZERO), (ZERO, ZERO)), (g, ZERO)


def g_run(h, remaining):
    if h == 0:
        return F(remaining)
    s = 1 - h
    return s * (1 - s ** remaining) / h


def window_matrix(window):
    """Compact reset-oracle diagnostics on real fixed masks, not actual beam power.

    First output is safe; first-event time is geometric over subsequent positions.
    Earlier decoder errors are deliberately RESET before that event, not ignored
    accidentally. M10 is N/A. Float recurrence values are labelled as rounded.
    """
    n = window["n"]
    out = []
    for mid in IDS:
        for name, mode, null_kind, adv_kind in DECODERS:
            if mid == "M10":
                out.append(dict(model=mid, decoder=name, reset_oracle_mean=None,
                                actual_beam_power="unknown", reason="no mod-29 collision event"))
                continue
            mask = window["final"] if null_kind == 1 else window["initial"] if null_kind == 2 else [False] * n
            actual_adv = window["word"] if mid == "M11" else window["word_break"] if mid == "M12" else [0] * n
            dec_adv = window["word"] if adv_kind == 1 else window["word_break"] if adv_kind == 2 else [0] * n
            future = [(0.0, 0.0)] * (n + 1)
            events = []
            for i in range(n - 1, -1, -1):
                matrix, event = transition_and_event(mid, mode, bool(null_kind), mask[i], actual_adv[i], dec_adv[i])
                nxt = future[i + 1]
                future[i] = tuple(sum(float(matrix[x][y]) * (1 + nxt[y]) for y in (0, 1)) for x in (0, 1))
                events.append((i, event))
            event_map = dict(events)
            rate = float(RNULL if mid == "M07" else RHO)
            z = 1 - (1 - rate) ** (n - 1)
            mean = immediate = 0.0
            by_position = []
            for i in range(1, n):
                event = event_map[i]
                length = sum(float(event[y]) * future[i + 1][y] for y in (0, 1))
                w = rate * (1 - rate) ** (i - 1) / z
                mean += w * length
                immediate += w * sum(float(p) for p in event)
                by_position.append(length)
            out.append(dict(model=mid, decoder=name, reset_oracle_mean=mean,
                            reset_oracle_immediate_phase_support=immediate,
                            conditional_lengths_after_positions=by_position,
                            actual_beam_run_length="unknown", actual_beam_power="unknown",
                            plaintext_warning=("uniform-plaintext hold reference" if mid == "M04" else
                                               "wrong native emission/domain" if mid == "M09" else
                                               "local symbol corruption" if mid in ("M06", "M08") else None)))
    return out
