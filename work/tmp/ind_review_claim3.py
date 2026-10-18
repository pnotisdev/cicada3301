"""Independent review, claim 3: reimplementation (from scratch, no import of
work/independent code) of the 'lag-6-value-gated keyless-null decoder' forward
statistic from work/independent/MATH.md section 3 + echo_nulls.py.

Model (as specified there):
  - layout: word starts of LP2 section 0.7, first 300 positions (like their gate)
  - plaintext: Welcome (lp.KNOWN[1][1]) first 300 runes, enciphered with the
    totient (primes-1) library stream, offset 3, mult 1, no atbash, skip q=0.81
  - keyless null at eligible positions (i - word_start >= 6 and
    T(c_{i-6}) != c_{i-1}), T(x) = 24-2x mod 29, probability rho = 0.0272
    (per eligible position), no two consecutive nulls; a null consumes no
    plaintext and no key value
  - statistic S = log P_L(paths) - log P_U(paths), L = Emerson bigram model with
    0.5 pseudocount per cell (reimplemented per manual_common.reference_model),
    U = uniform 1/29; forward states (key pointer, prev plaintext, prev-was-null)
    with exact log-sum-exp over paths; no beam, no free deletions.

Experiment (mirrors their gate's search grid, smaller):
  - variants: offsets 0..7 x mults {1,28} x atbash {F,T} x rho {0, 0.0272} = 64
  - plant A: nulls planted at rho=0.0272 of eligible positions (reseed until >=1)
  - plant B: no nulls (the null control)
  - per plant: S at all 64 settings on the TRUE key; S at all 64 settings on K
    random keys (the matched shuffled-key null, same as their screen)
  - report: true S, margin over wrong settings, random-key best distribution
    (mean/sd/max), z-score, Monte Carlo rank p, and the rho-freedom inflation
    delta (best over full grid - best over rho=0-only grid) for random keys.
  - Viterbi trace at the true setting of plant A: alignment accuracy, planted
    null recall, decoded IoC (their gate's >=98% / all-nulls criteria).
"""
import math
import random
import re
import sys
import time

sys.path.insert(0, "work")
import lp  # trusted project toolkit (work/lp.py), not the reviewed folder

Q = 29
RHO = 0.0272
SKIP_Q = 0.81
LOG_Q = math.log(Q)
MAX_STATES = 100000


# ---------------------------------------------------------------- utilities

def sieve(limit):
    m = bytearray(b"\x01") * (limit + 1)
    m[:2] = b"\x00\x00"
    for p in range(2, math.isqrt(limit) + 1):
        if m[p]:
            m[p * p::p] = b"\x00" * ((limit - p * p) // p + 1)
    return [i for i in range(2, limit + 1) if m[i]]


def totient_key(n):
    """primes-1 stream: (p_i - 1) mod 29 for p_0=2,3,5,... (work/keystreams.py
    'primes-1 (totient)')."""
    limit = 256
    while True:
        ps = sieve(limit)
        if len(ps) >= n:
            break
        limit *= 2
    return [(p - 1) % Q for p in ps[:n]]


def reference_logs():
    text = open("work/ref/emerson_essays1.txt", encoding="utf-8").read()
    marker = text.find("SELF-RELIANCE")
    assert marker >= 0
    text = text[marker:].split("*** END OF")[0]
    words = re.findall(r"[A-Za-z]+", text)
    stream = [r for w in words for r in lp.word_to_key(w.upper().replace("IO", "IA"))]
    assert len(stream) >= 10000
    counts = [[0.5] * Q for _ in range(30)]
    for a, b in zip(stream, stream[1:]):
        counts[a][b] += 1.0
    for b in stream:
        counts[29][b] += 1.0
    return [[math.log(v / sum(row)) for v in row] for row in counts], len(stream)


def layout_starts(section=7, n=300):
    toks = lp.load_segments()[section]
    c = lp.runes_of(toks)
    starts = [-1] * len(c)
    for _, a, b in lp.word_spans(toks, c):
        starts[a:b] = [a] * (b - a)
    assert all(s >= 0 for s in starts)
    return starts[:n]


def ioc(values):
    n = len(values)
    if n < 2:
        return 0.0
    counts = [0] * Q
    for v in values:
        counts[v] += 1
    return sum(x * (x - 1) for x in counts) / (n * (n - 1) / Q)


# ---------------------------------------------------------------- plant

def plant(plain, starts, key, off, mult, atb, rho, seed, q=SKIP_Q):
    rng = random.Random(seed)
    c, aligned, j, at, was_null = [], [], off, 0, False
    for i in range(len(starts)):
        may = i - starts[i] >= 6 and (24 - 2 * c[i - 6]) % Q != c[i - 1]
        if may and not was_null and rng.random() < rho:
            c.append((24 - 2 * c[i - 6]) % Q)
            aligned.append(None)
            was_null = True
            continue
        p = plain[at]
        at += 1
        raw = Q - 1 - p if atb else p
        while True:
            if j >= len(key):
                raise ValueError("plant key too short")
            y = (raw + mult * key[j]) % Q
            j += 1
            if not c or y != c[-1] or rng.random() >= q:
                break
        c.append(y)
        aligned.append(p)
        was_null = False
    return c, aligned


# ---------------------------------------------------------------- forward

def add_log(table, state, value):
    old = table.get(state)
    if old is None:
        table[state] = value
    else:
        hi, lo = max(old, value), min(old, value)
        table[state] = hi + math.log1p(math.exp(lo - hi))


def log_total(values):
    vals = list(values)
    hi = max(vals)
    return hi + math.log(sum(math.exp(v - hi) for v in vals))


def ordinary_arcs(ci, pv, key, j, mult, q):
    accept = math.log1p(-q) if ci == pv else 0.0
    arcs = [(j + 1, (ci - mult * key[j]) % Q, accept)]
    if pv < 0 or q == 0:
        return arcs
    raw = (pv - mult * key[j]) % Q
    prob = math.log(q)
    for t in range(j + 1, len(key)):
        trial = (raw + mult * key[t]) % Q
        if trial == ci:
            arcs.append((t + 1, raw, prob + accept))
        if trial != pv:
            break
        prob += math.log(q)
    return arcs


def forward(c, starts, key, off, mult, atb, rho, logs, q=SKIP_Q, trace=False):
    lang = {(off, Q, False): 0.0}
    uniform = {(off, False): 0.0}
    paths = {(off, Q, False): (0.0, None)} if trace else {}
    peak = 1
    for i, ci in enumerate(c):
        pv = c[i - 1] if i else -1
        can_null = i - starts[i] >= 6 and (24 - 2 * c[i - 6]) % Q != c[i - 1]
        matches = can_null and ci == (24 - 2 * c[i - 6]) % Q
        cache = {}
        nl, nu = {}, {}
        np = {}

        def arcs(j):
            if j not in cache:
                cache[j] = ordinary_arcs(ci, pv, key, j, mult, q)
            return cache[j]

        def take_path(old_state, new_state, weight, emission):
            if not trace:
                return
            value, node = paths[old_state]
            value += weight
            if new_state not in np or value > np[new_state][0]:
                np[new_state] = (value, (node, i, emission))

        for (j, last, was_null), value in lang.items():
            state = (j, last, was_null)
            chance = rho if can_null and not was_null else 0.0
            normal_weight = math.log1p(-chance)
            if chance and matches:
                ns = (j, last, True)
                add_log(nl, ns, value + math.log(chance))
                take_path(state, ns, math.log(chance), None)
            for nj, raw, weight in arcs(j):
                p = Q - 1 - raw if atb else raw
                ns = (nj, p, False)
                weight += normal_weight + logs[last][p]
                add_log(nl, ns, value + weight)
                take_path(state, ns, weight, p)
        for (j, was_null), value in uniform.items():
            chance = rho if can_null and not was_null else 0.0
            normal_weight = math.log1p(-chance)
            if chance and matches:
                add_log(nu, (j, True), value + math.log(chance))
            for nj, _, weight in arcs(j):
                add_log(nu, (nj, False), value + normal_weight + weight - LOG_Q)
        if not nl or not nu:
            raise ValueError("no complete alignment")
        lang, uniform, paths = nl, nu, np
        peak = max(peak, len(lang) + len(uniform))
        if peak > MAX_STATES:
            raise RuntimeError("state budget exceeded")
    ll, lu = log_total(lang.values()), log_total(uniform.values())
    result = {"score_nats": ll - lu, "per_output": (ll - lu) / len(c),
              "peak_states": peak}
    if trace:
        best = max(paths, key=lambda s: paths[s][0])
        node, aligned = paths[best][1], [None] * len(c)
        while node is not None:
            node, pos, emission = node
            aligned[pos] = emission
        plain = [p for p in aligned if p is not None]
        result.update(aligned=aligned, plain=plain,
                      deleted=[i for i, p in enumerate(aligned) if p is None],
                      ioc=ioc(plain))
    return result


# ---------------------------------------------------------------- experiment

VARIANTS = [(off, mult, atb, rho)
            for off in range(8) for mult in (1, 28)
            for atb in (False, True) for rho in (0.0, RHO)]


def search(c, starts, key, logs):
    return [(off, mult, atb, rho,
             forward(c, starts, key, off, mult, atb, rho, logs)["score_nats"])
            for off, mult, atb, rho in VARIANTS]


def main():
    t0 = time.time()
    n = 300
    logs, corpus_n = reference_logs()
    starts = layout_starts(7, n)
    eligible = sum(i - starts[i] >= 6 for i in range(n))
    print(f"corpus runes={corpus_n}; section 0.7 layout n={n}, "
          f"eligible lag-6 positions={eligible}")

    plain = lp.KNOWN[1][1](lp.runes_of(lp.load_segments()[1]))[:n]
    print(f"Welcome plaintext n={len(plain)}, IoC={ioc(plain):.4f}")

    key = totient_key(4 * n + 64)
    assert len(key) == 4 * n + 64
    print(f"totient key: first 8 = {key[:8]} (expect 1,2,4,6,10,12,16,18 = p-1 for p=2..19)")

    # plant A: nulls at rho of eligible positions; reseed until >=1 null
    attempts = 0
    while True:
        attempts += 1
        cA, alignedA = plant(plain, starts, key, 3, 1, False, RHO, 10000 + attempts)
        deletedA = [i for i, p in enumerate(alignedA) if p is None]
        if deletedA:
            break
        assert attempts < 1000
    # plant B: null control (no nulls)
    cB, alignedB = plant(plain, starts, key, 3, 1, False, 0.0, 20000)
    assert all(p is not None for p in alignedB)
    print(f"plant A: {len(deletedA)} nulls planted (rho={RHO} per eligible; "
          f"attempts={attempts}); plant B: 0 nulls")

    # benchmark one forward
    t1 = time.time()
    forward(cA, starts, key, 3, 1, False, RHO, logs)
    dt = time.time() - t1
    print(f"one forward call: {dt * 1000:.0f} ms")

    # true-key searches
    rowsA = search(cA, starts, key, logs)
    rowsB = search(cB, starts, key, logs)

    def true_rows(rows, off=3, mult=1, atb=False):
        return [r for r in rows if r[0] == off and r[1] == mult and r[2] == atb]

    def wrong_rows(rows, off=3, mult=1, atb=False):
        return [r for r in rows if not (r[0] == off and r[1] == mult and r[2] == atb)]

    for name, rows in (("A (nulls planted)", rowsA), ("B (no nulls)", rowsB)):
        tr = true_rows(rows)
        wr = wrong_rows(rows)
        best_true = max(tr, key=lambda r: r[4])
        best_wrong = max(wr, key=lambda r: r[4])
        s0 = [r for r in tr if r[3] == 0.0][0][4]
        sr = [r for r in tr if r[3] == RHO][0][4]
        print(f"plant {name}: true S(rho=0)={s0:+.2f} S(rho=RHO)={sr:+.2f} "
              f"(best true variant {best_true[3]}, S={best_true[4]:+.2f}); "
              f"best wrong setting S={best_wrong[4]:+.2f} at {best_wrong[:4]}; "
              f"margin={best_true[4] - best_wrong[4]:+.2f} nats")

    # Viterbi trace at the true setting of plant A (their gate criteria)
    trA = forward(cA, starts, key, 3, 1, False, RHO, logs, trace=True)
    acc = sum(a == b for a, b in zip(alignedA, trA["aligned"])) / n
    recall = sum(i in trA["deleted"] for i in deletedA)
    print(f"plant A trace: accuracy={acc:.3f} ({sum(a == b for a, b in zip(alignedA, trA['aligned']))}/{n}), "
          f"planted-null recall={recall}/{len(deletedA)}, "
          f"false deleted={len(trA['deleted']) - recall}, IoC={trA['ioc']:.3f}")

    # random-key matched nulls: K keys x the same 64-setting grid, per plant
    K = 16
    nullA, nullB = [], []
    for k in range(K):
        rng = random.Random(770000 + k)
        rkey = [rng.randrange(Q) for _ in range(len(key))]
        rowsRA = search(cA, starts, rkey, logs)
        rowsRB = search(cB, starts, rkey, logs)
        bestA = max(r[4] for r in rowsRA)
        bestB = max(r[4] for r in rowsRB)
        # rho-freedom inflation: best over rho=0-only settings
        rho0A = max(r[4] for r in rowsRA if r[3] == 0.0)
        rho0B = max(r[4] for r in rowsRB if r[3] == 0.0)
        nullA.append((bestA, rho0A))
        nullB.append((bestB, rho0B))
        print(f"random key {k + 1}/{K}: A best={bestA:+.2f} (rho0-only {rho0A:+.2f}), "
              f"B best={bestB:+.2f} (rho0-only {rho0B:+.2f})")

    def stats(xs, s_true):
        bests = [x[0] for x in xs]
        mean = sum(bests) / len(bests)
        var = sum((v - mean) ** 2 for v in bests) / max(1, len(bests) - 1)
        sd = math.sqrt(var)
        z = (s_true - mean) / sd if sd else float("inf")
        rank = (1 + sum(v >= s_true for v in bests)) / (len(bests) + 1)
        infl = [x[0] - x[1] for x in xs]
        return mean, sd, max(bests), z, rank, max(infl), sum(infl) / len(infl)

    sA = max(r[4] for r in true_rows(rowsA))
    sB = max(r[4] for r in true_rows(rowsB))
    mA, sA_sd, maxA, zA, rA, iA_max, iA_mean = stats(nullA, sA)
    mB, sB_sd, maxB, zB, rB, iB_max, iB_mean = stats(nullB, sB)
    print(f"plant A: S_true={sA:+.2f} nats vs random-key null bests "
          f"mean={mA:+.2f} sd={sA_sd:.2f} max={maxA:+.2f}; z={zA:.1f}; "
          f"MonteCarlo rank p={rA:.3f}; rho-freedom inflation on random keys "
          f"mean={iA_mean:+.2f} max={iA_max:+.2f} nats")
    print(f"plant B: S_true={sB:+.2f} nats vs random-key null bests "
          f"mean={mB:+.2f} sd={sB_sd:.2f} max={maxB:+.2f}; z={zB:.1f}; "
          f"rank p={rB:.3f}; rho-freedom inflation mean={iB_mean:+.2f} "
          f"max={iB_max:+.2f} nats")

    # mechanism check: margin(true offset 3 vs best wrong offset 0..7) vs the
    # position of the plant's FIRST hidden redraw, over 6 plant seeds (mult 1,
    # atb F, rho 0).  If margins track the first redraw position, the shallow
    # valley is the skip rule's hidden pointer freedom, not an implementation bug.
    print("margin vs first-redraw-position sweep (rho=0 plants):")
    for seed in range(20000, 20006):
        rng2 = random.Random(seed)
        cc, jj, redraws = [], 3, []
        for i in range(n):
            p = plain[i]
            while True:
                y = (p + key[jj]) % Q
                jj += 1
                if not cc or y != cc[-1] or rng2.random() >= SKIP_Q:
                    break
                redraws.append(i)
            cc.append(y)
        first = redraws[0] if redraws else -1
        scores = {off: forward(cc, starts, key, off, 1, False, 0.0, logs)["score_nats"]
                  for off in range(8)}
        margin = scores[3] - max(v for o, v in scores.items() if o != 3)
        print(f"  seed {seed}: first redraw at pos {first}; S(off3)={scores[3]:+.1f} "
              f"margin over offsets 0..7 = {margin:+.1f} nats")
    print(f"total wall time: {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
