"""One-shot D1 FIRST gate: exact tiny laws, not cryptanalytic power.
Standard library only. No project imports, engines, subprocesses or randomness.
"""
from __future__ import annotations

import time
START = time.monotonic()
from collections import defaultdict
from fractions import Fraction as F
from functools import lru_cache
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RESULT = HERE/"result.json"
Q, REPAIR, RHO = 3, F(81, 100), F(7, 250)
MODES = ("HOLD", "SPEND", "SKIP", "INSERT_UNIFORM", "INSERT_VALUE")
KEYS = {"empty": (), "single": (0,), "constant_short": (0, 0), "ample": (0, 1, 2)*4}
PI = {"biased": (F(1, 2), F(1, 3), F(1, 6)), "uniform": (F(1, 3),)*3}
A = {"biased": ((F(1, 2), F(1, 4), F(1, 4)), (F(1, 5), F(3, 5), F(1, 5)), (F(1, 3), F(1, 6), F(1, 2))),
     "uniform": ((F(1, 3),)*3,)*3}
OUT = {"gate": "D1 FIRST correctness gate only", "status": "RUNNING", "invocations": 1,
       "wall_cap_seconds": 90, "external_cap_seconds": 120, "LP2_read_or_searched": False,
       "random_seeds": [], "later_power_calibration_authorized": False,
       "inputs": {}, "laws": [], "mutation_controls": [], "checks": {}}
NODES = 0


def check_time():
    if time.monotonic()-START >= 90:
        raise TimeoutError("Cooperative 90-second gate deadline; preserve partial output, no retry")


def save():
    OUT["elapsed_seconds"] = round(time.monotonic()-START, 6)
    RESULT.write_text(json.dumps(OUT, indent=2, allow_nan=False)+"\n", encoding="utf-8", newline="\n")


def read(rel):
    b = (ROOT/rel).read_bytes()
    OUT["inputs"][rel] = {"sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}
    return b


# Independent implementation A: explicit causal event tree. It never calls DP.
@lru_cache(None)
def enumerate_forward(mode, key, law, horizon):
    success, failed = defaultdict(F), defaultdict(F)
    def visit(prefix, j, previous_plain, last_null, mass):
        global NODES
        NODES += 1
        if NODES % 128 == 0:
            check_time()
        if len(prefix) == horizon:
            success[prefix] += mass
            return
        i, prev = len(prefix), prefix[-1] if prefix else -1
        null_ok = mode == "INSERT_UNIFORM" and i in (1, 2, 3) and not last_null
        value = None
        if mode == "INSERT_VALUE" and i in (2, 3) and not last_null:
            value = (2*prefix[i-2]+1) % Q
            null_ok = value != prev
        normal_mass = mass*(1-RHO) if null_ok else mass
        if null_ok:
            emissions = range(Q) if mode == "INSERT_UNIFORM" else (value,)
            for c in emissions:
                weight = RHO/Q if mode == "INSERT_UNIFORM" else RHO
                visit(prefix+(c,), j, previous_plain, True, mass*weight)
        prior = PI[law] if previous_plain == -1 else A[law][previous_plain]
        for p, prob in enumerate(prior):
            weight = normal_mass*prob
            if not weight:
                continue
            if j >= len(key):
                failed[prefix] += weight
                continue
            trial = (p+key[j]) % Q
            if mode in ("HOLD", "SPEND"):
                if trial != prev:
                    visit(prefix+(trial,), j+1, p, False, weight)
                else:
                    visit(prefix+(trial,), j+1, p, False, weight*(1-REPAIR))
                    for c in range(Q):
                        if c != prev:
                            end = j if mode == "HOLD" else j+1
                            visit(prefix+(c,), end, p, False, weight*REPAIR/(Q-1))
            else:
                # Retrying a collision consumes keys but NOT another plaintext symbol.
                def attempt(at, attempt_mass):
                    if at == len(key):
                        failed[prefix] += attempt_mass
                        return
                    emitted = (p+key[at]) % Q
                    if emitted != prev:
                        visit(prefix+(emitted,), at+1, p, False, attempt_mass)
                    else:
                        visit(prefix+(emitted,), at+1, p, False, attempt_mass*(1-REPAIR))
                        attempt(at+1, attempt_mass*REPAIR)
                attempt(j, weight)
    visit((), 0, -1, False, F(1))
    return dict(success), dict(failed)


# Independent implementation B: filter observed symbols. No simulator arc helpers.
@lru_cache(None)
def dp_states(output, mode, key, law, mutant=""):
    if not output:
        return {(0, -1, False): F(1)}
    prefix, ci = output[:-1], output[-1]
    previous = dp_states(prefix, mode, key, law, mutant)
    i, prev = len(prefix), prefix[-1] if prefix else -1
    nxt = defaultdict(F)
    for (j, last_p, was_null), mass in previous.items():
        possible = mode == "INSERT_UNIFORM" and 1 <= i <= 3
        target_value = None
        if mode == "INSERT_VALUE" and 2 <= i <= 3:
            target_value = (1+2*prefix[-2]) % Q
            possible = target_value != prev
        allowed = possible and not was_null
        normal = (1-RHO) if allowed else F(1)
        if mutant in ("post_null_penalty", "prototype") and possible:
            normal = 1-RHO
        if allowed:
            emit = F(1, Q) if mode == "INSERT_UNIFORM" else F(int(ci == target_value))
            if mutant in ("missing_null_factor", "prototype") and mode == "INSERT_UNIFORM":
                emit = F(1)
            if mutant == "divide_value_null" and mode == "INSERT_VALUE":
                emit /= Q
            end = j+1 if mutant == "null_spends_key" else j
            nxt[(end, last_p, True)] += mass*RHO*emit
        prior = PI[law] if last_p < 0 else A[law][last_p]
        if j >= len(key):
            continue  # this weight belongs to FAIL, not to successful output strings
        if mode in ("HOLD", "SPEND"):
            if ci != prev:
                p = (ci-key[j]) % Q
                nxt[(j+1, p, False)] += mass*normal*prior[p]
            elif prev >= 0:
                p = (prev-key[j]) % Q
                nxt[(j+1, p, False)] += mass*normal*prior[p]*(1-REPAIR)
            if prev >= 0 and ci != prev:
                p = (prev-key[j]) % Q
                end = j if mode == "HOLD" and mutant != "hold_advances_key" else j+1
                last = last_p if mutant == "hold_loses_plain_history" else p
                nxt[(end, last, False)] += mass*normal*prior[p]*REPAIR/(Q-1)
        else:
            for at in range(j, len(key)):
                p = (ci-key[at]) % Q
                if any((p+key[t]) % Q != prev for t in range(j, at)):
                    continue
                weight = REPAIR**(at-j)
                if ci == prev:
                    weight *= 1-REPAIR
                nxt[(at+1, p, False)] += mass*normal*prior[p]*weight
    return {state: p for state, p in nxt.items() if p}


def dp_probability(c, mode, key, law, mutant=""):
    return sum(dp_states(c, mode, key, law, mutant).values(), F())


def dp_failure_after(prefix, mode, key, law):
    total = F()
    i, prev = len(prefix), prefix[-1] if prefix else -1
    for (j, last_p, was_null), mass in dp_states(prefix, mode, key, law).items():
        eligible = mode == "INSERT_UNIFORM" and i in (1, 2, 3)
        if mode == "INSERT_VALUE":
            eligible = i in (2, 3) and (2*prefix[-2]+1) % Q != prev
        ordinary = 1-RHO if eligible and not was_null else F(1)
        prior = PI[law] if last_p == -1 else A[law][last_p]
        if mode in ("HOLD", "SPEND"):
            if j >= len(key):
                total += mass*ordinary
        else:
            for p, pp in enumerate(prior):
                exhaust = F(1)
                for t in range(j, len(key)):
                    if (p+key[t]) % Q != prev:
                        exhaust = F()
                        break
                    exhaust *= REPAIR
                total += mass*ordinary*pp*exhaust
    return total


def all_outputs(n):
    return itertools.product(range(Q), repeat=n)


def compare_full_grid():
    comparisons = 0
    for mode, (key_name, key), law, n in itertools.product(MODES, KEYS.items(), PI, range(5)):
        check_time()
        oracle, oracle_fail = enumerate_forward(mode, key, law, n)
        mass, max_error = F(), F()
        for c in all_outputs(n):
            probability = dp_probability(c, mode, key, law)
            error = abs(probability-oracle.get(c, F()))
            max_error = max(max_error, error)
            mass += probability
            comparisons += 1
        fail = sum((dp_failure_after(prefix, mode, key, law) for length in range(n) for prefix in all_outputs(length)), F())
        failure_error = abs(fail-sum(oracle_fail.values(), F()))
        row = {"model": mode, "key": key_name, "plaintext_law": law, "horizon": n,
               "output_strings": Q**n, "success_mass": str(mass), "failure_mass": str(fail),
               "complete_mass": str(mass+fail), "max_DP_vs_tree_error": str(max_error),
               "failure_DP_vs_tree_error": str(failure_error)}
        OUT["laws"].append(row)
        save()
        assert max_error == 0 and failure_error == 0 and mass+fail == 1, f"Full-grid correctness failed: {row}"
    OUT["checks"]["full_grid"] = {"laws": len(OUT["laws"]), "output_probabilities_compared": comparisons,
        "all_complete_masses_one": True, "all_exact_DP_vs_tree": True, "all_exact_failure_masses": True}


def mutation_controls():
    tests = (("missing_null_factor", "INSERT_UNIFORM", 2),
             ("post_null_penalty", "INSERT_UNIFORM", 3),
             ("null_spends_key", "INSERT_UNIFORM", 3),
             ("hold_advances_key", "HOLD", 3),
             ("hold_loses_plain_history", "HOLD", 3),
             ("divide_value_null", "INSERT_VALUE", 3))
    for mutant, mode, n in tests:
        reference, _ = enumerate_forward(mode, KEYS["ample"], "biased", n)
        wrong_mass, error = F(), F()
        for c in all_outputs(n):
            p = dp_probability(c, mode, KEYS["ample"], "biased", mutant)
            wrong_mass += p
            error = max(error, abs(p-reference.get(c, F())))
        record = {"mutation": mutant, "model": mode, "horizon": n,
                  "mutant_success_mass": str(wrong_mass), "max_error": str(error), "detected": error > 0}
        OUT["mutation_controls"].append(record)
        save()
        assert error > 0, f"Mutation was not detected: {mutant}"


def latent_fixture():
    hold = dp_states((0, 1), "HOLD", KEYS["ample"], "biased")
    insertion = dp_states((0, 1), "INSERT_UNIFORM", KEYS["ample"], "biased")
    h, z = hold.get((1, 2, False), F()), insertion.get((1, 0, True), F())
    assert h == F(81, 1600) and z == F(7, 1500)
    OUT["checks"]["consumption_fixture"] = {"ciphertext_prefix": [0, 1],
        "HOLD_state_nextkey_previousplain_nullflag": [1, 2, False], "HOLD_path_mass": str(h),
        "INSERT_state_nextkey_previousplain_nullflag": [1, 0, True], "INSERT_path_mass": str(z),
        "distinct_plaintext_consumption_preserved": True}


def offsets():
    prior = (F(1, 2), F(1, 3), F(1, 6))
    keys = tuple(KEYS["ample"][off:] for off in range(3))
    ref = [enumerate_forward("INSERT_UNIFORM", key, "biased", 3)[0] for key in keys]
    rows, total, maximized_total = [], F(), F()
    for c in all_outputs(3):
        cond = [dp_probability(c, "INSERT_UNIFORM", key, "biased") for key in keys]
        mixed = sum((w*p for w, p in zip(prior, cond)), F())
        explicit = sum((prior[i]*ref[i].get(c, F()) for i in range(3)), F())
        assert mixed == explicit
        posterior = [w*p/mixed for w, p in zip(prior, cond)]
        assert sum(posterior, F()) == 1
        rows.append({"output": list(c), "mixture": str(mixed), "posterior": list(map(str, posterior))})
        total += mixed
        maximized_total += max(cond)
    assert total == 1 and maximized_total > 1
    OUT["checks"]["offset_mixture"] = {"prior": list(map(str, prior)), "output_strings": len(rows),
        "mixture_mass": str(total), "sum_of_maximized_conditional_weights": str(maximized_total),
        "maximization_is_not_the_prescribed_mixture": True, "rows": rows}


def normalizer_qualification():
    totals, distributions = {}, {}
    for law in PI:
        dist = {c: dp_probability(c, "INSERT_UNIFORM", KEYS["ample"], law, "prototype") for c in all_outputs(3)}
        totals[law] = sum(dist.values(), F())
        distributions[law] = dist
    expected_Z = (1-RHO)**2 + 2*Q*RHO*(1-RHO)
    assert totals["biased"] == totals["uniform"] == expected_Z
    for c in all_outputs(3):
        a, b = distributions["biased"][c], distributions["uniform"][c]
        assert a/b == (a/totals["biased"])/(b/totals["uniform"])
    finite = {law: sum((dp_probability(c, "INSERT_UNIFORM", KEYS["constant_short"], law, "prototype") for c in all_outputs(3)), F()) for law in PI}
    assert finite["biased"] != finite["uniform"]
    mass29 = F(1)+28*RHO
    assert mass29 == F(223, 125)
    OUT["checks"]["normalizer_qualification"] = {"ample_key_global_Z_by_plaintext_law": {k: str(v) for k, v in totals.items()},
        "hard_core_mask_partition_Z": str(expected_Z), "all_27_ratios_unchanged": True,
        "finite_key_success_only_Z_by_law": {k: str(v) for k, v in finite.items()},
        "finite_key_success_normalizers_differ": True, "fresh_29_rune_weight_sum": str(mass29),
        "fresh_29_rune_weight_sum_decimal": str(float(mass29)),
        "interpretation": "Wrong stated online prior does not by itself invalidate every possible ratio; cancellation has conditions"}


def main():
    for rel in ("work/independent/frontier/gates/d1/PROTOCOL.md", "work/independent/frontier/gates/d1/gate.py",
                "work/independent/frontier/REPORT.md", "work/independent/frontier/LIKELIHOOD_NOTE.md"):
        read(rel)
    assert all(sum(p, F()) == 1 for p in PI.values())
    assert all(sum(row, F()) == 1 for matrix in A.values() for row in matrix)
    save()
    compare_full_grid()
    latent_fixture()
    mutation_controls()
    offsets()
    normalizer_qualification()
    check_time()
    OUT["status"] = "PASS_FIRST_CORRECTNESS_GATE"
    OUT["summary"] = {"exact_laws_passed": len(OUT["laws"]),
        "output_probabilities_compared": OUT["checks"]["full_grid"]["output_probabilities_compared"],
        "broken_DP_mutations_detected": sum(r["detected"] for r in OUT["mutation_controls"]),
        "planted_key_power_tested": False, "LP2_inference_authorized": False}


def report():
    lines = RESULT.read_text(encoding="utf-8").splitlines()
    def loc(needle):
        return next(i for i, s in enumerate(lines, 1) if needle in s)
    out = ["# D1 FIRST correctness-gate result", "", f"**{OUT['status']}** (`result.json:{loc(chr(34)+'status'+chr(34)+':')}`). Nothing in LP2 is solved.", "",
           f"Elapsed seconds: {OUT['elapsed_seconds']} (`result.json:{loc(chr(34)+'elapsed_seconds'+chr(34)+':')}`). One invocation; no retry.", "",
           "## Completed checks", ""]
    if "summary" in OUT:
        s = OUT["summary"]
        out += [f"- {s['exact_laws_passed']} exact output laws; {s['output_probabilities_compared']} DP-versus-event-tree output probabilities.",
                "- Successful output mass plus explicitly retained exhaustion mass is exactly one in each law.",
                f"- {s['broken_DP_mutations_detected']}/6 deliberately broken transitions detected.",
                "- Hold and insertion preserve different latent plaintext-consumption states.",
                "- Frozen offset-prior marginalization agrees exactly with explicit enumeration; maximizing offsets is a different statistic.",
                "- Ample-key prototype language/uniform weights share a global normalizer and preserve their ratios; finite-key success-only normalizers need not.",
                f"- Summary source: `result.json:{loc(chr(34)+'summary'+chr(34)+':')}-{len(lines)}`."]
    else:
        out += [f"- Partial law records retained: {len(OUT['laws'])}."]
    check_start = loc('"checks":')
    check_end = loc('"elapsed_seconds":')-1
    out += [f"- Full exact identities, state fixtures and normalizer values: `result.json:{check_start}-{check_end}`.", "",
            "## Not established", "", "No English/plaintext or key-family recovery power, real-stream offset equivalence, calibrated null tail, LP2 exclusion or decryption.",
            "The later positive/null calibration is unapproved. Passing this first correctness gate is not permission to search LP2.",
            "All failed/incomplete checks remain in the first result; the script refuses a second invocation."]
    if "error" in OUT:
        out += ["", "## Error", "", json.dumps(OUT["error"])]
    (HERE/"REPORT.md").write_text("\n".join(out)+"\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    if RESULT.exists():
        raise SystemExit("Refusing to overwrite/retry the first gate result; seek new approval")
    save()
    try:
        main()
    except Exception as exc:
        OUT["status"] = "INCOMPLETE_TIMEOUT" if isinstance(exc, TimeoutError) else "FAILED_CORRECTNESS"
        tb = exc.__traceback__
        while tb and tb.tb_next:
            tb = tb.tb_next
        OUT["error"] = {"type": type(exc).__name__, "message": str(exc).replace(str(ROOT), "<repo>"), "gate_line": tb.tb_lineno if tb else None}
    finally:
        save()
        report()
    print(json.dumps({"status": OUT["status"], "summary": OUT.get("summary"), "error": OUT.get("error"), "elapsed_seconds": OUT["elapsed_seconds"]}))
    if OUT["status"] != "PASS_FIRST_CORRECTNESS_GATE":
        raise SystemExit(1)
