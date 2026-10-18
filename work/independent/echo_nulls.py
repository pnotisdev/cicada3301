"""Human-run, isolated likelihood test for value-gated, keyless lag-6 nulls.

No experiments run on import. See README.md and MATH.md before using this.
This is NOT the existing IoC beam: it sums alignment probabilities, with no beam.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import random
import struct
import unittest
from pathlib import Path

from manual_common import (HERE, Run, execute, fingerprint, lp_module, reference_model,
                           relative, repo_path, scrub, sha256)

Q = 29
SKIP_Q = 0.81
RHO = 0.0272                       # per ELIGIBLE in-word position, NOT per output rune
MAX_STATES = 20000                 # exceeding this aborts; states are never silently pruned
LOG_Q = math.log(Q)
NEG = float("-inf")
VARIANTS = [(m, atb, rho) for m in (1, 28) for atb in (False, True) for rho in (0.0, RHO)]


def add_log(table, state, value):
    old = table.get(state, NEG)
    if old == NEG:
        table[state] = value
    else:
        hi, lo = max(old, value), min(old, value)
        table[state] = hi + math.log1p(math.exp(lo - hi))


def log_total(values):
    values = list(values)
    if not values:
        return NEG
    hi = max(values)
    return hi + math.log(sum(math.exp(v - hi) for v in values))


def layout(section):
    lp = lp_module()
    toks = lp.load_segments()[section]
    c = lp.runes_of(toks)
    starts = [-1] * len(c)
    for _, a, b in lp.word_spans(toks, c):
        starts[a:b] = [a] * (b - a)
    if any(a < 0 for a in starts):
        raise ValueError("Word spans do not cover every rune")
    return c, starts


def eligible(c, starts, i):
    # A deterministic echo null itself may not make a doublet. It remains visible
    # to the NEXT rune's collision check (unlike kscreen's word-edge-null option).
    return i - starts[i] >= 6 and (24 - 2 * c[i - 6]) % Q != c[i - 1]


def ordinary_arcs(c, prev, key, j, mult, q):
    """All (next pointer, pre-Atbash plaintext, log probability) for skip encryption.

    The first rejected draw uniquely fixes the plaintext. Subsequent rejected
    draws must encrypt that SAME plaintext to prev. No arbitrary skip limit.
    """
    if j >= len(key):
        return []
    accept = math.log1p(-q) if c == prev else 0.0
    arcs = [(j + 1, (c - mult * key[j]) % Q, accept)]
    if prev < 0 or q == 0:
        return arcs
    raw = (prev - mult * key[j]) % Q
    probability = math.log(q)
    for used in range(j + 1, len(key)):
        trial = (raw + mult * key[used]) % Q
        if trial == c:
            arcs.append((used + 1, raw, probability + accept))
        if trial != prev:
            break
        probability += math.log(q)
    return arcs


def forward(c, starts, key, offset, mult, atb, rho, logs, *, q=SKIP_Q, trace=False, run=None):
    """Joint-prefix likelihood ratio: English bigrams vs uniform plaintext.

    Both hypotheses use the SAME cipher, null prior, layout and key. State is
    (key pointer, previous plaintext, previous output was a null). Uniform-model
    states can omit previous plaintext. No maximizing/pruning in likelihoods.
    trace=True additionally computes a Viterbi path; it does NOT change the score.
    """
    if not c or len(c) != len(starts) or not 0 <= offset < len(key):
        raise ValueError("Invalid window or offset")
    if not 0 <= rho < 1 or not 0 <= q < 1:
        raise ValueError("Probabilities must lie in [0,1)")
    lang = {(offset, Q, False): 0.0}
    uniform = {(offset, False): 0.0}
    paths = {(offset, Q, False): (0.0, None)} if trace else {}
    peak = 1
    for i, ci in enumerate(c):
        if run is not None and i % 20 == 0:
            run.check()
        pv = c[i - 1] if i else -1       # section start: intentionally unknown
        can_null = eligible(c, starts, i)
        matches = can_null and ci == (24 - 2 * c[i - 6]) % Q
        cache = {}
        nl, nu, np = {}, {}, {}

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
                weight = math.log(chance)
                add_log(nl, ns, value + weight)
                take_path(state, ns, weight, None)
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
            raise ValueError("No complete alignment: key buffer exhausted or model impossible")
        lang, uniform, paths = nl, nu, np
        peak = max(peak, len(lang) + len(uniform))
        if peak > MAX_STATES:
            raise RuntimeError("State budget exceeded; exact calculation stopped, no negative")
    ll, lu = log_total(lang.values()), log_total(uniform.values())
    result = {"score_nats": ll - lu, "per_output": (ll - lu) / len(c),
              "language_log_mass": ll, "uniform_log_mass": lu, "peak_states": peak}
    if trace:
        best = max(paths, key=lambda s: paths[s][0])
        node, aligned = paths[best][1], [None] * len(c)
        while node is not None:
            node, pos, emission = node
            aligned[pos] = emission
        plain = [p for p in aligned if p is not None]
        result.update(aligned=aligned, plain=plain,
                      deleted=[i for i, p in enumerate(aligned) if p is None],
                      pointer_end=best[0], ioc=lp_module().ioc(plain))
    return result


def plant(plain, starts, key, offset, mult, atb, rho, seed, *, q=SKIP_Q):
    """Independent FORWARD encryptor: draws coins, not inverse decoder arcs."""
    rng = random.Random(seed)
    c, aligned, j, at, was_null = [], [], offset, 0, False
    for i in range(len(starts)):
        # Eligibility uses only ALREADY emitted ciphertext, not future/plaintext.
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
                raise ValueError("Plant key too short")
            y = (raw + mult * key[j]) % Q
            j += 1
            if not c or y != c[-1] or rng.random() >= q:
                break
        c.append(y)
        aligned.append(p)
        was_null = False
    return c, aligned


def evaluate(c, starts, keys, offsets, logs, run, *, progress=False):
    rows, done = [], 0
    total = len(keys) * len(offsets) * len(VARIANTS)
    for item, (name, key) in enumerate(keys):
        for off in offsets:
            for mult, atb, rho in VARIANTS:
                answer = forward(c, starts, key, off, mult, atb, rho, logs, run=run)
                rows.append(dict(item=item, name=name, offset=off, mult=mult, atbash=atb, rho=rho, **answer))
                done += 1
                if progress and (done % 16 == 0 or done == total):
                    run.log(f"{done}/{total} hypotheses; current maximum {max(r['score_nats'] for r in rows):.3f} nats")
    return sorted(rows, key=lambda r: r["score_nats"], reverse=True)


def gate(run, args):
    initial_fingerprint = fingerprint()
    import test_core
    output = io.StringIO()
    tests = unittest.defaultTestLoader.loadTestsFromModule(test_core)
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(tests)
    for line in output.getvalue().splitlines():
        run.log(line)
    if not result.wasSuccessful() or result.skipped:
        raise RuntimeError("Unit gate failed (a skipped test also fails)")
    logs, corpus = reference_model()
    lp = lp_module()
    segs = lp.load_segments()
    solved = [p for s in sorted(lp.KNOWN) for p in lp.KNOWN[s][1](lp.runes_of(segs[s]))]
    sections = [s for s in range(7, 16) if len(layout(s)[0]) >= args.n]
    if not sections:
        raise ValueError("No layout is long enough for the requested gate")
    records = []
    # Six ordinary, unconditioned plants measure small-sample power at LP2 layouts.
    # Two conditioned plants ensure that the NEW null branch actually gets tested.
    # Two uniform-plaintext plants are ciphertext-side null controls, same search.
    for rep in range(10):
        run.check()
        _, starts = layout(sections[rep % len(sections)])
        starts = starts[:args.n]
        rng = random.Random(330100 + rep)
        keys = [(f"plant-key-{k}", [rng.randrange(Q) for _ in range(args.n * 4 + 64)]) for k in range(2)]
        mult, atb = (1 if rep % 2 == 0 else 28), bool((rep // 2) % 2)
        plain = ([solved[(rep * 53 + i) % len(solved)] for i in range(args.n)] if rep < 8
                 else [rng.randrange(Q) for _ in range(args.n)])
        attempts = 0
        while True:
            c, planted = plant(plain, starts, keys[0][1], 3, mult, atb, RHO, rep * 10000 + attempts)
            deleted = [i for i, p in enumerate(planted) if p is None]
            attempts += 1
            if rep not in (6, 7) or deleted:
                break
            if attempts >= 1000:
                raise RuntimeError("Could not create the diagnostic null-bearing plant")
        rows = evaluate(c, starts, keys, list(range(8)), logs, run)
        true = [r for r in rows if r["item"] == 0 and r["offset"] == 3
                and r["mult"] == mult and r["atbash"] == atb]
        wrong = [r for r in rows if r not in true]
        margin = max(r["score_nats"] for r in true) - max(r["score_nats"] for r in wrong)
        decoded = forward(c, starts, keys[0][1], 3, mult, atb, RHO, logs, trace=True, run=run)
        accuracy = sum(a == b for a, b in zip(planted, decoded["aligned"])) / args.n
        null_recall = all(i in decoded["deleted"] for i in deleted)
        good = (margin >= 10 and accuracy >= 0.98 and null_recall) if rep < 8 else rows[0]["per_output"] < 0.20
        record = dict(rep=rep, kind=("unconditioned" if rep < 6 else "conditioned-null" if rep < 8 else "uniform-null"),
                      section_layout=sections[rep % len(sections)], resampling_attempts=attempts,
                      planted_nulls=len(deleted), recovered_planted_nulls=sum(i in decoded["deleted"] for i in deleted),
                      accuracy=accuracy, true_minus_wrong_nats=margin,
                      search_max_nats=rows[0]["score_nats"], passed=good)
        records.append(record)
        run.log(record)
        # Persist partial controls too if a later test hits its time budget.
        run.save(f"plant_{rep:02d}.json", record)
    if fingerprint() != initial_fingerprint:
        raise RuntimeError("Code or inputs changed during the gate; rerun on a stable snapshot")
    passed = all(r["passed"] for r in records)
    payload = dict(passed=passed, fingerprint=initial_fingerprint, n=args.n, q=SKIP_Q, rho=RHO,
                   units=result.testsRun, skipped=len(result.skipped), corpus=corpus, controls=records,
                   caveat="Six unconditioned plants are not a precise power estimate; two diagnostic plants were conditioned on a null.")
    run.save("gate.json", payload)
    run.log("GATE PASSED" if passed else "GATE FAILED: no LP2 search authorized by this gate")
    if not passed:
        raise RuntimeError("Planted recovery or null separation failed")


def parse_offsets(value):
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError("Offsets use START:STOP, stop exclusive")
    a, b = map(int, parts)
    if a < 0 or not a < b or b - a > 64:
        raise ValueError("Use 1..64 nonnegative offsets")
    return list(range(a, b))


def prime_streams(names, length):
    limit = max(64, int(length * (math.log(max(3, length)) + math.log(math.log(max(3, length)))) + 128))
    while True:
        sieve = bytearray(b"\x01") * (limit + 1)
        sieve[:2] = b"\x00\x00"
        for p in range(2, math.isqrt(limit) + 1):
            if sieve[p]:
                sieve[p * p:limit + 1:p] = b"\x00" * ((limit - p * p) // p + 1)
        ps = [i for i in range(2, limit + 1) if sieve[i]]
        if len(ps) >= length:
            break
        limit *= 2
    out = []
    for name in names:
        if name not in ("primes", "totient"):
            raise ValueError("Built-in streams: primes,totient only")
        out.append((name, [(p - (name == "totient")) % Q for p in ps[:length]]))
    return out


def load_keys(spec, length):
    if spec["kind"] == "builtin":
        return prime_streams(spec["names"], length)
    path = repo_path(spec["path"])
    if sha256(path) != spec["sha256"]:
        raise ValueError("Library changed since the screen definition")
    wanted = set(spec["items"])
    out = []
    with path.open("rb") as f:
        if f.read(4) != b"KSB1":
            raise ValueError("Not a KSB1 library")
        count, = struct.unpack("<I", f.read(4))
        if count > 100000:
            raise ValueError("Unreasonable library item count")
        for item in range(count):
            size, = struct.unpack("<H", f.read(2))
            name = f.read(size).decode("utf-8")
            size, = struct.unpack("<I", f.read(4))
            if item in wanted:
                values = f.read(size)
                if len(values) != size or any(v >= Q for v in values):
                    raise ValueError("Invalid library values")
                label = scrub("".join(ch if 32 <= ord(ch) < 127 else "?" for ch in name))[:160]
                out.append((f"ksb#{item}:{label}", list(values)))
            else:
                f.seek(size, 1)
    if len(out) != len(wanted):
        raise ValueError("Requested library item is missing")
    return out


def check_gate(path, n):
    record = json.loads(repo_path(path).read_text(encoding="utf-8"))
    if record.get("passed") is not True or record.get("fingerprint") != fingerprint():
        raise ValueError("Gate failed, missing, or stale: rerun gate after code/input changes")
    if record.get("n") != n or record.get("q") != SKIP_Q or record.get("rho") != RHO:
        raise ValueError("Gate settings do not match the screen")


def key_hashes(keys):
    return [{"name": name, "length": len(key), "sha256": hashlib.sha256(bytes(key)).hexdigest()}
            for name, key in keys]


def screen(run, args):
    check_gate(args.gate, args.n)
    initial_fingerprint = fingerprint()
    c, starts = layout(args.section)
    if len(c) < args.n + 120:
        raise ValueError("Need at least 120 unsearched runes beyond the screen")
    offsets = parse_offsets(args.offsets)
    if args.library:
        items = sorted(set(map(int, args.items.split(","))))
        if not items or min(items) < 0 or len(items) > 4:
            raise ValueError("Select 1..4 explicit nonnegative library item indices")
        spec = dict(kind="ksb", path=relative(args.library), sha256=sha256(args.library), items=items)
    else:
        names = list(dict.fromkeys(args.streams.split(",")))
        spec = dict(kind="builtin", names=names)
    length = max(offsets) + 4 * len(c) + 64
    keys = load_keys(spec, length)
    if any(len(k) < length for _, k in keys):
        raise ValueError("Selected key needs a longer prefix for whole-section verification")
    jobs = len(keys) * len(offsets) * len(VARIANTS)
    if jobs > args.max_hypotheses:
        raise ValueError(f"Budget would be {jobs} hypotheses; reduce streams/offsets")
    if not 19 <= args.nulls <= 199:
        raise ValueError("Use 19..199 matched search-null replicates")
    run.log(f"Section 0.{args.section}, first {args.n}/{len(c)} runes; {jobs} settings per search")
    run.log(f"Including nulls: {jobs * (args.nulls + 1)} exact likelihood decodes; unbenchmarked")
    run.log("Null keys are independently shuffled copies: same lengths/marginals, not temporal structure.")
    logs, corpus = reference_model()
    rows = evaluate(c[:args.n], starts[:args.n], keys, offsets, logs, run, progress=True)
    definition = dict(fingerprint=initial_fingerprint, gate=relative(args.gate), gate_sha256=sha256(args.gate),
                      section=args.section, n=args.n, offsets=offsets, key_spec=spec,
                      key_length=length, keys=key_hashes(keys), corpus=corpus, settings=jobs,
                      null_replicates=args.nulls, null_seed=args.seed)
    run.save("scores.json", rows)
    # Written before controls in case the human interrupts; only screen.json below is complete.
    run.save("definition.json", definition)
    maxima = []
    for rep in range(args.nulls):
        rng = random.Random(args.seed + rep)
        null_keys = []
        for name, key in keys:
            values = key.copy()
            rng.shuffle(values)
            null_keys.append((name, values))
        best = evaluate(c[:args.n], starts[:args.n], null_keys, offsets, logs, run)[0]
        maxima.append(best["score_nats"])
        run.log(f"Null search {rep + 1}/{args.nulls}: maximum {maxima[-1]:.3f} nats")
        run.save(f"null_{rep:03d}.json", best)
    if fingerprint() != initial_fingerprint:
        raise RuntimeError("Code or inputs changed during the search; no completed result")
    best = rows[0]
    rank_p = (1 + sum(v >= best["score_nats"] for v in maxima)) / (len(maxima) + 1)
    flagged = best["per_output"] >= 0.20 and best["score_nats"] >= max(maxima) + 20
    run.save("screen.json", dict(complete=True, definition=definition, rows=rows,
                                 null_maxima_nats=maxima, descriptive_rank_p=rank_p, flagged=flagged))
    run.log(f"Best: {best}; null max={max(maxima):.3f}; descriptive rank p={rank_p:.4f}")
    run.log("FLAG FOR MANUAL WHOLE-SECTION VERIFICATION" if flagged else "No flag in this bounded search; no broader exclusion follows.")
    run.log("Rank p is NOT a discovery probability: the model/rate were suggested by LP2 itself.")
    run.log("Use the separate verify command if you want a full-section check. No plaintext claimed.")


def verify(run, args):
    path = repo_path(args.screen)
    record = json.loads(path.read_text(encoding="utf-8"))
    definition = record["definition"]
    if record.get("complete") is not True or definition["fingerprint"] != fingerprint():
        raise ValueError("Screen is incomplete or stale")
    check_gate(definition["gate"], definition["n"])
    if sha256(definition["gate"]) != definition["gate_sha256"]:
        raise ValueError("Screen's gate was replaced")
    if not 1 <= args.rank <= len(record["rows"]):
        raise ValueError("Rank is out of range")
    row = record["rows"][args.rank - 1]
    keys = load_keys(definition["key_spec"], definition["key_length"])
    if key_hashes(keys) != definition["keys"]:
        raise ValueError("Keys no longer reproduce the screen")
    c, starts = layout(definition["section"])
    logs, _ = reference_model()
    _, key = keys[row["item"]]

    def decode(off):
        return forward(c, starts, key, off, row["mult"], row["atbash"], row["rho"], logs, trace=True, run=run)

    answer = decode(row["offset"])
    # Random, unsearched offsets of the SAME structured stream. No short-key cycling.
    hi = len(key) - 4 * len(c)
    possible = [i for i in range(max(0, hi)) if i not in definition["offsets"]]
    if len(possible) < 20:
        raise ValueError("Not enough unsearched offsets for the 20 matched controls")
    offsets = random.Random(args.seed).sample(possible, 20)
    controls = []
    for i, off in enumerate(offsets):
        null = decode(off)
        controls.append(dict(offset=off, score_nats=null["score_nats"], ioc=null["ioc"]))
        run.log(f"Full-section control {i + 1}/20: {null['score_nats']:.3f} nats; IoC {null['ioc']:.4f}")
        run.save(f"verify_null_{i:02d}.json", controls[-1])
    if fingerprint() != definition["fingerprint"]:
        raise RuntimeError("Code or inputs changed during verification; no completed result")
    holdout = (answer["score_nats"] - row["score_nats"]) / (len(c) - definition["n"])
    passed = (answer["per_output"] >= 0.20 and holdout >= 0.20
              and answer["score_nats"] >= max(r["score_nats"] for r in controls) + 20
              and answer["ioc"] >= 1.40 and answer["ioc"] >= max(r["ioc"] for r in controls) + 0.15)
    run.save("verify.json", dict(screen=relative(path), screen_sha256=sha256(path), row=row,
                                 answer=answer, controls=controls, holdout_nats_per_output=holdout,
                                 passed_numerical_checks=passed,
                                 verdict="Candidate for independent reproduction, NOT a solve" if passed else "Fails whole-section numerical verification"))
    lp = lp_module()
    text = "".join("[NULL]" if p is None else lp.LATIN[p] for p in answer["aligned"])
    with (run.directory / "decoded.txt").open("x", encoding="utf-8", newline="\n") as f:
        f.write("Unverified Viterbi output; [NULL] marks a proposed keyless rune. No frequency relabelling.\n")
        f.write(text + "\n")
    run.log(f"Full section: {answer['score_nats']:.3f} nats; IoC {answer['ioc']:.4f}; holdout {holdout:.4f} nats/output")
    run.log("NUMERICAL CANDIDATE: reproduce independently and test a second section; NOT SOLVED" if passed
            else "Whole-section checks FAIL; not a decryption")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    gate_ap = sub.add_parser("gate", help="unit, plant, wrong-key and uniform-plaintext controls ONLY")
    gate_ap.add_argument("--n", type=int, default=300)
    gate_ap.add_argument("--seconds", type=float, default=900)
    scan = sub.add_parser("screen", help="bounded LP2 search; requires a passing, current gate")
    scan.add_argument("--gate", required=True, help="repository-relative gate.json")
    scan.add_argument("--section", type=int, choices=range(7, 16), default=7)
    scan.add_argument("--n", type=int, default=300)
    scan.add_argument("--streams", default="totient", help="primes,totient (ignored with --library)")
    scan.add_argument("--library", help="existing KSB1 file; read only, never exported/rebuilt")
    scan.add_argument("--items", default="0", help="1..4 explicit library indices")
    scan.add_argument("--offsets", default="0:16")
    scan.add_argument("--nulls", type=int, default=19)
    scan.add_argument("--seed", type=int, default=771033)
    scan.add_argument("--max-hypotheses", type=int, default=256)
    scan.add_argument("--seconds", type=float, default=1800)
    ver = sub.add_parser("verify", help="whole-section and 20 unsearched-offset controls; human starts this separately")
    ver.add_argument("--screen", required=True, help="completed screen.json")
    ver.add_argument("--rank", type=int, default=1)
    ver.add_argument("--seed", type=int, default=991033)
    ver.add_argument("--seconds", type=float, default=1800)
    args = ap.parse_args()
    if args.command in ("gate", "screen") and not 120 <= args.n <= 600:
        ap.error("n must be between 120 and 600, with an identically configured gate")
    return execute(f"echo-{args.command}", lambda run: {"gate": gate, "screen": screen, "verify": verify}[args.command](run, args), args.seconds)


if __name__ == "__main__":
    raise SystemExit(main())
