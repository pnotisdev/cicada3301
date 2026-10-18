#!/usr/bin/env python
"""Corrected gate for the lag-6 keyless-null statistic (work/tmp/gated_null_gate.py).

Full reimplementation from scratch.  work/independent/* was read as data only and is
never imported or executed here.  Everything below is my own derivation.

Model (per task):
  * keystream k: totient stream, k_i = (p_i - 1) mod 29 over the primes 2,3,5,...
    (identical to the library stream "primes-1 (totient)", work/keystreams.py:44);
    cross-checked here against lp.primes (sieve vs trial division).
  * skip rule (kscreen model 0): plaintext letter p at key pointer j encrypts to
    y = (p + k[j]) mod 29.  If y equals the previous CIPHERTEXT rune, the draw is
    rejected with probability q = 0.81 (a hidden redraw: the pointer has already
    advanced and the same p is redrawn at j+1), accepted otherwise.  One ciphertext
    rune therefore consumes 1 + (#rejections) key values.
  * keyless null: at word-interior lag-6-eligible positions only (j - word_start >= 6
    in the ciphertext coordinate system), with FIXED prior q_null = 0.028, the rune
    consumes NO key value, has no letter likelihood (scored at the prior), and two
    nulls are never adjacent (a null flag in the DP state).
  * word layout: nulledge L-line convention -- the L line is the CIPHERTEXT word
    lengths including nulls ("a null adds a rune to its word").  Here the L line is
    derived from lp.word_spans on the plant window (Welcome plaintext words, first n
    runes; padded with the next solved sections for n > 515), inflated by the planted
    nulls.  Plant and decoder share the layout, exactly as the nulledge engine reads
    the window's L line from segments.txt.
  * letter model: English RUNE unigram over the committed Emerson corpus
    (work/sim.py:23-32 construction, reimplemented here: words -> runes via
    lp.word_to_key, add-one smoothing over the 29 runes).  Uniform model = 1/29.

Statistic (summed-path evidence ratio, no maximizing / no beam -- the anti-overfit
design carried over from the review): with state (j, f), j = key pointer,
f = previous-output-was-null (0/1),

  S(o) = ln Z_eng(o) - ln Z_unif(o)

where Z_model(o) = sum over all null/letter paths of
  prod_pos [ null:      q_null                              (eligible & f=0)
             letter:    (1 - q_null_if_eligible) * P_arc * P_model(letter) ] ,
  P_arc = direct-read arc probability (1, or 1-q on a doublet) or the rejection-chain
  arc probability (q per rejection), P_eng = unigram, P_unif = 1/29.
The null prior is FIXED at q_null = 0.028 (never fitted), so random keys cannot
inflate it; the letter probability is summed (not maxed) over paths.

DP: exact forward (log-sum-exp) over (pointer, null-flag) per position; a Viterbi
variant (max + backpointers) reports the best alignment / null flags.  The null
branch is ungated (fires at every eligible position; the ciphertext value of the
null is not modelled) unless `gated` is set, which reproduces the value-gated
variant (null branch only when c_i == 24 - 2*c_{i-6} mod 29) for the null-side grid.

Gate (the CORRECTED gate): the statistic at the TRUE offset must exceed the statistic
at ALL neighbor offsets +/-1..3 AND every matched-null decode (12 uniform random keys
x the same offsets on the plant's ciphertext -- the "12 random-key plants, uniform
keys, same settings" null side; a full random-key plant cannot be a null because its
own true offset legitimately aligns English) by at least 10 nats.
"""
from __future__ import annotations

import json
import math
import random
import re
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent          # work/tmp
REPO = HERE.parent.parent                       # repo root
sys.path.insert(0, str(REPO / "work"))

import lp  # data module only: GP, load_segments, KNOWN, word_spans, ioc, word_to_key

Q = 29
LOG_Q = math.log(Q)
NEG = float("-inf")

SKIP_Q = 0.81        # accept probability; hidden redraws happen with 1-q per collision
Q_NULL = 0.028       # FIXED null prior per eligible word-interior position
NULL_RATE = 0.42     # plant: null at ~42% of eligible positions (the word-length model)
TRUE_OFFSET = 3      # plant's key start offset (as in the reviewed setup)
SEED_PLANT = 12345   # plant coins (same seed as the nulledge control plant)
KEY_LEN = 2048

# ------------------------------------------------------------------ streams

def _primes_upto(limit):
    s = bytearray(b"\x01") * (limit + 1)
    s[:2] = b"\x00\x00"
    for p in range(2, math.isqrt(limit) + 1):
        if s[p]:
            s[p * p:limit + 1:p] = b"\x00" * (((limit - p * p) // p) + 1)
    return [i for i in range(2, limit + 1) if s[i]]


def totient_key(n):
    bound = int(n * (math.log(n) + math.log(math.log(max(n, 3)))) + 64)
    ps = _primes_upto(bound)
    assert len(ps) >= n, "sieve bound too small"
    return [(p - 1) % Q for p in ps[:n]]


def uniform_key(n, seed):
    rng = random.Random(seed)
    return [rng.randrange(Q) for _ in range(n)]


# ------------------------------------------------------------------ layout

def window_spans(n):
    """(plaintext, spans) for the first n solved runes; spans = [(a, b)] in rune
    coordinates.  The window starts at the Welcome plaintext (section 0.1, the
    task's plant window) and pads with the NEXT solved sections in book order
    (0.2..0.6, An End, Parable); section 0.0 precedes Welcome and is only used as a
    last-resort fallback if the padding runs short."""
    segs = lp.load_segments()
    order = [1, 2, 3, 4, 5, 6, 16, 17, 0]
    plain, spans, pos = [], [], 0
    for s in order:
        toks = segs[s]
        p = lp.KNOWN[s][1](lp.runes_of(toks))
        need = n - len(plain)
        if need <= 0:
            break
        take = min(need, len(p))
        sub, k = [], 0
        for t in toks:
            if isinstance(t, int):
                if k >= take:
                    break
                k += 1
            sub.append(t)
        sub.append(" ")
        for _w, a, b in lp.word_spans(sub, p[:take]):
            spans.append((a + pos, b + pos))
        plain.extend(p[:take])
        pos += take
    if len(plain) < n:
        raise ValueError(f"only {len(plain)} solved runes available, need {n}")
    return plain, spans


# ------------------------------------------------------------------ language model

def emerson_unigram_logs():
    """log P(rune) under the English rune unigram: Emerson essays converted to runes
    via lp.word_to_key (same construction as work/sim.py:23-32), add-one smoothing."""
    with open(REPO / "work" / "ref" / "emerson_essays1.txt", encoding="utf-8") as f:
        text = f.read()
    text = text[text.index("SELF-RELIANCE", text.index("SELF-RELIANCE") + 1):]
    text = text.split("*** END OF")[0]
    counts = [0] * Q
    total = 0
    for w in re.findall(r"[A-Za-z]+", text):
        w = w.upper().replace("IO", "IA")
        for r in lp.word_to_key(w):
            counts[r] += 1
            total += 1
    return [math.log((counts[r] + 1.0) / (total + Q)) for r in range(Q)]


# ------------------------------------------------------------------ plant

def plant(plain, spans, key, offset, null_rate, null_kind, seed, q=SKIP_Q):
    """Forward encryptor: draws coins, never inverse-decoder arcs.

    null_kind: 'echo'   -> null value = (24 - 2*c[j-6]) mod 29 (the lag-6 echo form)
               'uniform'-> null value = uniform 0..28
    A value coin is drawn in BOTH cases so the coin streams (hence the redraw sites)
    are identical across null kinds; 'echo' simply overrides the drawn value.
    Returns dict(c, starts, aligned, nulls, redraws, first_redraw, key_consumed)."""
    rng = random.Random(seed)
    c, starts, aligned = [], [], []
    nulls, redraws = [], []
    j, at, was_null = offset, 0, False
    for _a, b in spans:
        word_start = len(c)
        t = _a
        while t < b:
            if len(c) - word_start >= 6 and not was_null:
                # one value coin always (keeps streams aligned across null kinds)
                val = rng.randrange(Q)
                if rng.random() < null_rate:
                    if null_kind == "echo":
                        val = (24 - 2 * c[len(c) - 6]) % Q
                    c.append(val)
                    starts.append(word_start)
                    aligned.append(None)
                    nulls.append(len(c) - 1)
                    was_null = True
                    continue                # null consumed no plaintext: same letter again
            p = plain[at]
            at += 1
            while True:
                y = (p + key[j]) % Q
                j += 1
                if not c or y != c[-1] or rng.random() >= q:
                    break
                redraws.append(len(c))          # hidden redraw at this position
            c.append(y)
            starts.append(word_start)
            aligned.append(p)
            was_null = False
            t += 1
    return dict(c=c, starts=starts, aligned=aligned, nulls=nulls, redraws=redraws,
                first_redraw=(min(redraws) if redraws else None), key_consumed=j - offset)


# ------------------------------------------------------------------ decoder arcs

def letter_arcs(c, prev, key, j, mult, q):
    """All (next pointer, plaintext raw, log arc probability) readings of ciphertext c
    from pointer j under the skip rule.

    Direct read at j: p = c - mult*k[j], pointer j+1, prob 1 (or 1-q if c == prev).
    Rejected-read chain: the draw at j equals prev (prob q) so p = prev - mult*k[j];
    subsequent draws of the same p are rejected while they equal prev (prob q each)
    and the chain ends where the draw equals c (prob 1, or 1-q when c == prev)."""
    if j >= len(key):
        return []
    accept = math.log1p(-q) if c == prev else 0.0
    arcs = [(j + 1, (c - mult * key[j]) % Q, accept)]
    if prev < 0 or q == 0:
        return arcs
    raw = (prev - mult * key[j]) % Q
    prob = math.log(q)
    for used in range(j + 1, len(key)):
        trial = (raw + mult * key[used]) % Q
        if trial == c:
            arcs.append((used + 1, raw, prob + accept))
        if trial != prev:
            break
        prob += math.log(q)
    return arcs


def _add(table, key, value):
    old = table.get(key)
    if old is None:
        table[key] = value
    else:
        hi, lo = max(old, value), min(old, value)
        table[key] = hi + math.log1p(math.exp(lo - hi))


def _total(vals):
    vals = list(vals)
    if not vals:
        return NEG
    hi = max(vals)
    return hi + math.log(sum(math.exp(v - hi) for v in vals))


def forward(c, starts, key, offset, mult, atb, q_null, gated, q=SKIP_Q, logs=None):
    """Summed-path evidence ratio S = ln Z_eng - ln Z_unif over the DP states
    (pointer, null-flag).  Exact forward pass (log-sum-exp), no maximizing.
    A separate viterbi() runs the max variant for alignment reporting."""
    if logs is None:
        logs = UNI_LOGS
    if not c or len(c) != len(starts):
        raise ValueError("bad window")
    lang = {(offset, 0): 0.0}
    unif = {(offset, 0): 0.0}
    peak = 1
    for i, ci in enumerate(c):
        prev = c[i - 1] if i else -1
        elig = i - starts[i] >= 6
        echo = (24 - 2 * c[i - 6]) % Q if elig else -1
        chance = q_null if elig else 0.0
        nw = math.log1p(-chance)
        null_ok = elig and (not gated or ci == echo)
        cache = {}

        def arcs(j):
            if j not in cache:
                cache[j] = letter_arcs(ci, prev, key, j, mult, q)
            return cache[j]

        nl, nu = {}, {}
        for (j, flag), val in lang.items():
            if flag == 0 and null_ok and chance > 0:
                _add(nl, (j, 1), val + math.log(chance))
            for nj, raw, w in arcs(j):
                p = Q - 1 - raw if atb else raw
                _add(nl, (nj, 0), val + nw + w + logs[p])
        for (j, flag), val in unif.items():
            if flag == 0 and null_ok and chance > 0:
                _add(nu, (j, 1), val + math.log(chance))
            for nj, _raw, w in arcs(j):
                _add(nu, (nj, 0), val + nw + w - LOG_Q)
        if not nl or not nu:
            raise ValueError("no complete alignment: key exhausted")
        lang, unif = nl, nu
        peak = max(peak, len(lang) + len(unif))
    ll, lu = _total(lang.values()), _total(unif.values())
    return dict(score_nats=ll - lu, per_output=(ll - lu) / len(c),
                lang_log_mass=ll, unif_log_mass=lu, peak_states=peak)


def viterbi(c, starts, key, offset, mult, atb, q_null, gated, q=SKIP_Q, logs=None):
    if logs is None:
        logs = UNI_LOGS
    vit = {(offset, 0): (0.0, None)}          # state -> (score, backptr)
    for i, ci in enumerate(c):
        prev = c[i - 1] if i else -1
        elig = i - starts[i] >= 6
        echo = (24 - 2 * c[i - 6]) % Q if elig else -1
        chance = q_null if elig else 0.0
        nw = math.log1p(-chance)
        null_ok = elig and (not gated or ci == echo)
        cache = {}

        def arcs(j):
            if j not in cache:
                cache[j] = letter_arcs(ci, prev, key, j, mult, q)
            return cache[j]

        nv = {}
        for (j, flag), (val, bp) in vit.items():
            if flag == 0 and null_ok and chance > 0:
                s = (j, 1)
                w = val + math.log(chance)
                if s not in nv or w > nv[s][0]:
                    nv[s] = (w, (bp, i, None))
            for nj, raw, w in arcs(j):
                p = Q - 1 - raw if atb else raw
                s = (nj, 0)
                w = val + nw + w + logs[p]
                if s not in nv or w > nv[s][0]:
                    nv[s] = (w, (bp, i, p))
        if not nv:
            raise ValueError("no complete alignment: key exhausted")
        vit = nv
    best = max(vit, key=lambda s: vit[s][0])
    node, aligned = vit[best][1], [None] * len(c)
    while node is not None:
        node, pos, em = node
        aligned[pos] = em
    plain = [p for p in aligned if p is not None]
    return dict(aligned=aligned, plain=plain, pointer_end=best[0],
                ioc=lp.ioc(plain) if plain else 0.0, score_nats=vit[best][0])


def score_at(c, starts, key, offsets, mult=1, atb=False, q_null=Q_NULL, gated=False,
             q=SKIP_Q, logs=None):
    return {o: forward(c, starts, key, o, mult, atb, q_null, gated, q, logs=logs)
            ["score_nats"] for o in offsets}


def gate_row(name, kind, sc, offs, t, null_side_max):
    nbr_max = max(v for o, v in sc.items() if o != t)
    nbr_margin = sc[t] - nbr_max
    gate_margin = min(nbr_margin, sc[t] - null_side_max)
    return dict(name=name, kind=kind, S_true=sc[t], nbr_max=nbr_max,
                nbr_margin=nbr_margin, null_side_max=null_side_max,
                gate_margin=gate_margin, passed=gate_margin >= 10)


# ------------------------------------------------------------------ main

def main():
    t0 = time.monotonic()
    print("=" * 78)
    print("CORRECTED GATED-NULL GATE  (q=%.2f, q_null=%.3f, true offset=%d)"
          % (SKIP_Q, Q_NULL, TRUE_OFFSET))
    print("=" * 78)
    global UNI_LOGS
    UNI_LOGS = emerson_unigram_logs()

    # stream cross-check: my sieve vs lp.primes (trial division)
    k = totient_key(KEY_LEN)
    lp_primes = lp.primes(KEY_LEN)
    assert [((p - 1) % Q) for p in lp_primes] == k, "totient stream mismatch"
    print("totient key: length %d, first 12: %s  (sieve == lp.primes, "
          "== library 'primes-1 (totient)' by construction)" % (len(k), k[:12]))

    # ---------------- self-check: q=0, no nulls -> closed-form score
    plain300, spans300 = window_spans(300)
    ck = dict(c=[(p + k[TRUE_OFFSET + i]) % Q for i, p in enumerate(plain300)],
              starts=[0] * 300)
    direct = sum(UNI_LOGS[p] + LOG_Q for p in plain300)   # sum log(29 P(p))
    s_ck = forward(ck["c"], ck["starts"], k, TRUE_OFFSET, 1, False, 0.0, False,
                   q=0.0)["score_nats"]
    print("oracle check (q=0, q_null=0): S(true)=%.6f vs closed form %.6f  %s"
          % (s_ck, direct, "OK" if abs(s_ck - direct) < 1e-6 else "FAIL"))
    results = {"oracle_check": dict(s_dp=s_ck, closed=direct)}
    print("window n=300: plaintext IoC %.4f" % lp.ioc(plain300))

    # ---------------- Part 1: plant + DP recovery
    plantA = plant(plain300, spans300, k, TRUE_OFFSET, NULL_RATE, "echo", SEED_PLANT)
    n_elig = sum(1 for i, s in enumerate(plantA["starts"]) if i - s >= 6)
    print("\nplant A (totient, echo nulls): ciphertext %d runes, %d nulls planted, "
          "%d redraws, first redraw at pos %s, key consumed %d, eligible positions %d"
          % (len(plantA["c"]), len(plantA["nulls"]), len(plantA["redraws"]),
             plantA["first_redraw"], plantA["key_consumed"], n_elig))
    fA = forward(plantA["c"], plantA["starts"], k, TRUE_OFFSET, 1, False, Q_NULL, False)
    vA = viterbi(plantA["c"], plantA["starts"], k, TRUE_OFFSET, 1, False, Q_NULL, False)
    planted_nulls = set(plantA["nulls"])
    flagged = {i for i, em in enumerate(vA["aligned"]) if em is None}
    letter_ok = sum(a == b for a, b in zip(vA["aligned"], plantA["aligned"])
                    if b is not None)
    n_letters = sum(1 for b in plantA["aligned"] if b is not None)
    recall = len(planted_nulls & flagged) / len(planted_nulls) if planted_nulls else 1.0
    prec = len(planted_nulls & flagged) / len(flagged) if flagged else 1.0
    print("Part 1 DP recovery at true offset: S=%.3f nats; letter accuracy %d/%d = %.1f%%;"
          % (fA["score_nats"], letter_ok, n_letters, 100.0 * letter_ok / n_letters))
    print("    null recall %d/%d = %.1f%%; null precision %d/%d = %.1f%%; recovered IoC %.4f"
          % (len(planted_nulls & flagged), len(planted_nulls), 100 * recall,
             len(planted_nulls & flagged), len(flagged), 100 * prec, vA["ioc"]))
    print("    recovered text head: %s"
          % "".join(lp.LATIN[p] if p is not None else "·" for p in vA["aligned"][:70]))
    results["part1"] = dict(S_true=fA["score_nats"], letter_accuracy=letter_ok / n_letters,
                            null_recall=recall, null_precision=prec, ioc=vA["ioc"],
                            planted_nulls=len(planted_nulls), flagged=len(flagged),
                            eligible_positions=n_elig)

    # ---------------- Part 2: plants + corrected gate
    print("\n" + "-" * 78)
    print("PART 2: plant controls under the corrected gate (neighbors +/-1..3 AND "
          "the null side, >= 10 nats)")
    print("-" * 78)
    offs = [TRUE_OFFSET + d for d in range(-3, 4)]       # 0..6
    plantA2 = plant(plain300, spans300, k, TRUE_OFFSET, NULL_RATE, "uniform", SEED_PLANT)
    plantB = plant(plain300, spans300, k, TRUE_OFFSET, 0.0, "echo", SEED_PLANT)
    print("plant A2 (uniform-null values): %d nulls at the same positions; plant B "
          "(no nulls): %d redraws, first redraw pos %s"
          % (len(plantA2["nulls"]), len(plantB["redraws"]), plantB["first_redraw"]))

    # null side: matched nulls = 12 uniform random keys x the same 7 offsets on the
    # plant's own ciphertext (a full random-key plant is NOT a null: its true offset
    # legitimately aligns English).  Computed per plant so every plant gets its own.
    null_keys = [uniform_key(KEY_LEN, 5000 + r) for r in range(12)]
    plants = [("A echo", plantA, k), ("A2 uniform-null", plantA2, k),
              ("B no-null", plantB, k)]
    gate_rows = []
    for name, pl, key in plants:
        sc = score_at(pl["c"], pl["starts"], key, offs)
        null_side_max = max(forward(pl["c"], pl["starts"], nk, o, 1, False, Q_NULL,
                                    False)["score_nats"]
                            for nk in null_keys for o in offs)
        row = gate_row(name, "totient", sc, offs, TRUE_OFFSET, null_side_max)
        row.update(first_redraw=pl["first_redraw"], scores=sc)
        gate_rows.append(row)
        print("  %-14s S(true)=%9.3f  max neighbor=%9.3f  nbr margin=%8.2f  "
              "null-side max=%9.3f  gate margin=%8.2f  %s"
              % (name, sc[TRUE_OFFSET], row["nbr_max"], row["nbr_margin"],
                 null_side_max, row["gate_margin"],
                 "PASS" if row["passed"] else "FAIL"))
        print("      per offset: " + "  ".join("o%d=%8.2f" % (o, v)
                                               for o, v in sorted(sc.items())))

    # the 12 random-key plants (full plants) as a separate false-positive probe:
    # their own true offsets align English, so this probes the NEIGHBOR criterion only
    rand_rows = []
    for r in range(12):
        rk = uniform_key(KEY_LEN, 2000 + r)
        rp = plant(plain300, spans300, rk, TRUE_OFFSET, NULL_RATE, "echo", SEED_PLANT)
        sc = score_at(rp["c"], rp["starts"], rk, offs)
        null_side_max = max(forward(rp["c"], rp["starts"], nk, o, 1, False, Q_NULL,
                                    False)["score_nats"]
                            for nk in null_keys for o in offs)
        row = gate_row("rand-%02d" % r, "random", sc, offs, TRUE_OFFSET, null_side_max)
        row.update(first_redraw=rp["first_redraw"])
        rand_rows.append(row)
        print("  rand-%02d      S(true)=%9.3f  max neighbor=%9.3f  nbr margin=%8.2f"
              "  first redraw pos %s"
              % (r, row["S_true"], row["nbr_max"], row["nbr_margin"],
                 rp["first_redraw"]))
    n_pass_random = sum(1 for r in rand_rows if r["passed"])
    n_pass_c1_random = sum(1 for r in rand_rows if r["nbr_margin"] >= 10)
    print("random-key plants: %d/12 pass the full gate; %d/12 pass the "
          "neighbor-only (>=10) criterion" % (n_pass_random, n_pass_c1_random))
    results["part2"] = dict(
        offsets=offs,
        totient=[{kk: vv for kk, vv in r.items() if kk != "scores"} for r in gate_rows],
        random=[r for r in rand_rows],
        n_pass_random=n_pass_random, n_pass_c1_random=n_pass_c1_random)

    # ---------------- Part 3: n-sweep + seed sweep on the totient plant
    print("\n" + "-" * 78)
    print("PART 3: neighbor separation vs n and vs first-redraw position "
          "(totient plant, echo nulls)")
    print("-" * 78)
    sweep = []
    for n in (300, 600, 900):
        plain_n, spans_n = window_spans(n)
        pl = plant(plain_n, spans_n, k, TRUE_OFFSET, NULL_RATE, "echo", SEED_PLANT)
        sc = score_at(pl["c"], pl["starts"], k, offs)
        nbr_arg = max((o for o in offs if o != TRUE_OFFSET), key=lambda o: sc[o])
        sweep.append(dict(n=n, first_redraw=pl["first_redraw"],
                          n_null=len(pl["nulls"]), n_redraw=len(pl["redraws"]),
                          S_true=sc[TRUE_OFFSET], nbr_argmax=nbr_arg,
                          nbr_margin=sc[TRUE_OFFSET] - sc[nbr_arg], scores=sc))
        r = sweep[-1]
        print("  n=%d: first redraw pos %s, nulls=%d, redraws=%d; S(true)=%.2f, "
              "best neighbor o=%d, margin=%8.2f nats"
              % (n, r["first_redraw"], r["n_null"], r["n_redraw"], r["S_true"],
                 r["nbr_argmax"], r["nbr_margin"]))
        print("      per offset: " + "  ".join("o%d=%8.2f" % (o, v)
                                               for o, v in sorted(sc.items())))
    results["part3_nsweep"] = [{kk: vv for kk, vv in r.items() if kk != "scores"}
                               for r in sweep]
    # seed sweep: does the margin track the first-redraw position on the totient key?
    seed_rows = []
    for seed in (12345, 20004, 771, 31337, 424242):
        pl = plant(plain300, spans300, k, TRUE_OFFSET, NULL_RATE, "echo", seed)
        sc = score_at(pl["c"], pl["starts"], k, offs)
        nbr_arg = max((o for o in offs if o != TRUE_OFFSET), key=lambda o: sc[o])
        seed_rows.append(dict(seed=seed, first_redraw=pl["first_redraw"],
                              nbr_argmax=nbr_arg,
                              nbr_margin=sc[TRUE_OFFSET] - sc[nbr_arg]))
        r = seed_rows[-1]
        print("  seed %-7d first redraw pos %4s  neighbor margin %9.2f nats (best "
              "neighbor o%d)" % (seed, r["first_redraw"], r["nbr_margin"],
                                 r["nbr_argmax"]))
    results["part3_seeds"] = seed_rows

    # ---------------- Part 4: null-side strength
    print("\n" + "-" * 78)
    print("PART 4: null-side strength (16 uniform random keys on the n=300 echo "
          "ciphertext)")
    print("-" * 78)
    cA, stA = plantA["c"], plantA["starts"]
    gridA = [(o, m, a, r) for o in range(8) for m in (1, 28)
             for a in (False, True) for r in (0.0, Q_NULL)]
    gridB = [(o, r, g) for o in (3, 4, 5, 6) for r in (0.0, Q_NULL)
             for g in (False, True)]
    maxA, maxB = [], []
    for r in range(16):
        rk = uniform_key(KEY_LEN, 5000 + r)
        bestA = bestB = NEG
        for o, m, a, rho in gridA:
            s = forward(cA, stA, rk, o, m, a, rho, False)["score_nats"]
            bestA = max(bestA, s)
        for o, rho, g in gridB:
            s = forward(cA, stA, rk, o, 1, False, rho, g)["score_nats"]
            bestB = max(bestB, s)
        maxA.append(bestA)
        maxB.append(bestB)
    s_true = gate_rows[0]["S_true"]
    for label, vals in (("gridA 64 settings (8 off x mult x atb x rho, ungated)", maxA),
                        ("gridB 16 settings (4 off x 2 rho x 2 value-gate)", maxB)):
        mean = sum(vals) / len(vals)
        sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / (len(vals) - 1))
        z = (s_true - mean) / sd
        print("  %-52s max: mean=%9.2f sd=%7.2f min=%9.2f max=%9.2f  z(S_true)=%6.2f"
              % (label, mean, sd, min(vals), max(vals), z))
        results.setdefault("part4", {})[label] = dict(mean=mean, sd=sd, min=min(vals),
                                                      max=max(vals), z=z, values=vals)
    results["part4"]["S_true_reference"] = s_true

    # ---------------- dump
    out_path = HERE / "gated_null_results.json"
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(results, f, indent=1)
    print("\nresults -> %s" % out_path.relative_to(REPO))
    print("wall time %.1f s" % (time.monotonic() - t0))


UNI_LOGS = None

if __name__ == "__main__":
    main()
