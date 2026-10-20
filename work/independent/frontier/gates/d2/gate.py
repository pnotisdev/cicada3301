"""One-shot D2 synthetic feasibility gate. Standard library; no project imports.
Run once, from repo root, with external timeout 120 seconds and python -B.
"""
from __future__ import annotations

import time
START = time.monotonic()
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import random
import re
import struct
import subprocess
from fractions import Fraction

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RESULT = HERE / "result.json"
Q = 29
KEEP = .19
CAP = 90.0
OUT = {"gate": "D2 first feasibility gate", "status": "RUNNING", "invocations": 1,
       "reviewed_head": "b38bc2e", "wall_cap_seconds": CAP, "external_cap_seconds": 120,
       "LP2_searched": False, "later_calibration_authorized": False,
       "inputs": {}, "checks": {}, "cases": [], "native_commands": []}


def check_time():
    if time.monotonic() - START >= CAP:
        raise TimeoutError("Cooperative 90-second gate deadline reached; no retry")


def scrub(s):
    s = str(s)
    for prefix in (str(ROOT), ROOT.as_posix()):
        s = s.replace(prefix, "<repo>")
    for key in ("USERNAME", "COMPUTERNAME", "USERPROFILE"):
        v = os.environ.get(key, "")
        if len(v) > 3:
            s = s.replace(v, "<private>")
    return s


def save():
    OUT["elapsed_seconds"] = round(time.monotonic() - START, 6)
    RESULT.write_text(json.dumps(OUT, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8", newline="\n")


def read(rel):
    check_time()
    b = (ROOT / rel).read_bytes()
    OUT["inputs"][rel] = {"sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}
    return b


def convolve(a, b):
    n = len(a)
    return [sum(a[(i-j) % n]*b[j] for j in range(n)) for i in range(n)]


def pop_ioc(h):
    return len(h)*sum(x*x for x in h)


def histogram(v, n=Q):
    c = [0]*n
    for x in v:
        c[x] += 1
    return [x/len(v) for x in c]


def sample_ioc(v):
    c = [0]*Q
    for x in v:
        c[x] += 1
    return Q*sum(x*(x-1) for x in c)/(len(v)*(len(v)-1))


def algebra():
    h = [Fraction(1, 2), Fraction(1, 3), Fraction(1, 6)]
    values = []
    for word in itertools.product(range(3), repeat=2):
        w = [Fraction(word.count(i), 2) for i in range(3)]
        values.append(pop_ioc(convolve(h, w)))
    expected = 1+(pop_ioc(h)-1)/2
    checks = {"length2_mean_identity": sum(values)/9 == expected,
              "balanced_keyword_flattens": pop_ioc(convolve(h, [Fraction(1, 3)]*3)) == 1,
              "length1_shift_preserves_ioc": all(pop_ioc(convolve(h, [int(i == s) for i in range(3)])) == pop_ioc(h) for s in range(3))}
    OUT["checks"]["exact_algebra"] = {"tests": checks, "keywords_enumerated": 9,
        "standalone_J": str(pop_ioc(h)), "mean_after_L2": str(sum(values)/9), "formula": str(expected)}
    assert all(checks.values()), "Exact convolution identity/control failed"


def corpus():
    text = read("work/ref/emerson_essays1.txt").decode("utf-8")
    first = text.index("SELF-RELIANCE")
    text = text[text.index("SELF-RELIANCE", first+1):].split("*** END OF")[0]
    latin = "F U TH O R C G W H N I J EO P X S T B E M L ING OE D A AE Y IA EA".split()
    idx = {s: i for i, s in enumerate(latin)}
    pattern = re.compile("|".join(sorted(latin, key=lambda s: -len(s))))
    letters = []
    for word in re.findall("[A-Za-z]+", text):
        w = word.upper().replace("IO", "IA").translate(str.maketrans({"V": "U", "K": "C", "Z": "S", "Q": "C"}))
        pieces = pattern.findall(w)
        assert "".join(pieces) == w, "Unrecognized plaintext spelling"
        letters.extend(idx[p] for p in pieces)
    return letters


def load_stream():
    data = read("work/kscreen/data/library.ksb")
    assert data[:4] == b"KSB1"
    count, = struct.unpack_from("<I", data, 4)
    p, found = 8, None
    for _ in range(count):
        size, = struct.unpack_from("<H", data, p)
        p += 2
        name = data[p:p+size].decode("utf-8")
        p += size
        n, = struct.unpack_from("<I", data, p)
        p += 4
        if name == "primes^2":
            assert found is None
            found = list(data[p:p+n])
        p += n
    assert p == len(data) and found is not None and len(found) == 20000
    sieve = bytearray([1])*300001
    sieve[:2] = bytes(2)
    for k in range(2, math.isqrt(300000)+1):
        if sieve[k]:
            lo = k*k
            sieve[lo::k] = bytes((300000-lo)//k+1)
    primes = [i for i, yes in enumerate(sieve) if yes][:20000]
    assert len(primes) == len(found)
    assert found == [(p*p) % Q for p in primes], "Independent prime-square identity failed"
    rows = read("work/kscreen/data/library.tsv").decode("utf-8").split("\n")
    row = next(s for s in rows if s.startswith("primes^2\t")).split("\t")
    OUT["checks"]["stream_identity"] = {"KSB1_stream_count": count, "compared_values": len(found),
        "all_equal": True, "recorded_prefilter_J": float(row[-2]), "recorded_rejected": int(row[-1]) == 1}
    return found, float(row[-2])


def plant(plain, key, kw, offset, model, clock, seed):
    rng = random.Random(seed)
    j, prev, ciphertext, used = 0, -1, [], []
    for i, p in enumerate(plain):
        if i % 1024 == 0:
            check_time()
        def value(at):
            return (p+key[offset+at]+kw[(at if clock == "attempt" else i) % len(kw)]) % Q
        at = j
        y = value(at)
        j += 1
        if model == 0:
            tries = 0
            while y == prev:
                draw = rng.random()  # source draws even at its five-redraw cap
                if draw < KEEP or tries >= 5:
                    break
                at = j
                y = value(at)
                j += 1
                tries += 1
        elif y == prev:
            j += 1  # coin position is consumed even when the repeat is retained
            if rng.random() >= KEEP:
                at = j
                y = value(at)
                j += 1
        ciphertext.append(y)
        used.append(at)
        prev = y
    return ciphertext, used, j


def viterbi(c, key, kw, off, model, clock, logf):
    # Known keyword, UNKNOWN alignment. Unigram Markov state is just next key index.
    states = {0: (0.0, ())}
    prev = -1
    for i, ci in enumerate(c):
        if i % 16 == 0:
            check_time()
        nxt = {}
        def add(end, p, prob, score, path):
            if prob <= 0:
                return
            value = score + logf[p] + math.log(prob)
            if end not in nxt or value > nxt[end][0]:
                nxt[end] = (value, path+(p,))
        for j, (score, path) in states.items():
            def kval(at):
                return (key[off+at]+kw[(at if clock == "attempt" else i) % len(kw)]) % Q
            if model == 0:
                for r in range(6):
                    at = j+r
                    if off+at >= len(key):
                        break
                    p = (ci-kval(at)) % Q
                    if any((p+kval(t)) % Q != prev for t in range(j, at)):
                        continue
                    prob = (.81**r) * (KEEP if ci == prev and r < 5 else 1.)
                    add(at+1, p, prob, score, path)
            else:
                if off+j >= len(key):
                    continue
                p = (ci-kval(j)) % Q
                add(j+(2 if ci == prev else 1), p, KEEP if ci == prev else 1., score, path)
                if prev >= 0 and off+j+2 < len(key):
                    p = (ci-kval(j+2)) % Q
                    if (p+kval(j)) % Q == prev:
                        add(j+3, p, .81, score, path)
        if not nxt:
            return None
        states, prev = nxt, ci
    score, path = max(states.values(), key=lambda z: z[0])
    return score, list(path)


def native(cmd, stdout_name, stderr_name):
    check_time()
    OUT["native_commands"].append({"argv": cmd, "stdout": stdout_name, "stderr": stderr_name})
    save()
    with (HERE/stdout_name).open("w", encoding="utf-8", newline="\n") as out, (HERE/stderr_name).open("w", encoding="utf-8", newline="\n") as err:
        proc = subprocess.run(cmd, cwd=ROOT, stdout=out, stderr=err,
                              timeout=max(.01, CAP-(time.monotonic()-START)), check=False)
    for name in (stdout_name, stderr_name):
        path = HERE/name
        path.write_text(scrub(path.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
    assert proc.returncode == 0, f"Native command failed ({proc.returncode}); retained logs"
    check_time()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def main():
    read(relative(HERE/"PROTOCOL.md"))
    read(relative(HERE/"gate.py"))
    for rel in ("work/h5rs/target/release/h5rs.exe", "work/h5rs/src/main.rs",
                "work/h5rs/src/logf.rs", "work/h5slice/h5slice.py", "work/keystreams.py", "work/sim.py", "work/lp.py", "work/kscreen/export.py"):
        read(rel)
    save()
    algebra()
    plain_all = corpus()
    freq = histogram(plain_all)
    smoothed = [(x*len(plain_all)+.5)/(len(plain_all)+Q*.5) for x in freq]
    logf = [math.log(x) for x in smoothed]
    key, recorded_J = load_stream()
    h = histogram(key[:4000])
    predicted = [pop_ioc(convolve(freq, histogram([(s*x) % Q for x in key[:4000]]))) for s in (1, -1)]
    assert abs(max(predicted)-recorded_J) < .000051 and max(predicted) > 1.003
    OUT["checks"]["prefilter"] = {"recomputed_J_plus_minus": predicted, "rejected": True,
                                      "corpus_runes": len(plain_all), "cutoff": 1.003}
    rng = random.Random(78300)
    iid = [rng.randrange(Q) for _ in key]
    banks = {"real": key, "iid": iid, "structured": key[7001:]+key[:7001]}
    cells, index, plants = [], {}, []
    for k, (L, model, clock) in enumerate(itertools.product((13, 20), (0, 1), ("attempt", "emission"))):
        check_time()
        kw_rng = random.Random(78101+k)
        kw = [kw_rng.randrange(Q) for _ in range(L)]
        begin = 6500+400*k
        plain = plain_all[begin:begin+12956]
        assert len(plain) == 12956
        c, used, consumed = plant(plain, key, kw, 317, model, clock, 78201+k)
        recovered = [(ci-key[317+at]-kw[(at if clock == "attempt" else i) % L]) % Q for i, (ci, at) in enumerate(zip(c, used))]
        assert recovered == plain, "Oracle-alignment round trip failed"
        known = viterbi(c[:300], key, kw, 317, model, clock, logf)
        accuracy = sum(a == b for a, b in zip(known[1], plain[:300]))/300 if known else 0.
        composite_J = pop_ioc(convolve(freq, histogram([(key[317+j]+kw[j % L]) % Q for j in range(4000)]))) if clock == "attempt" else None
        case_id = f"L{L}_m{model}_{clock}"
        case = {"case_id": case_id, "index": k, "period": L, "model": model, "clock": clock,
                "keyword_seed": 78101+k, "coin_seed": 78201+k, "keyword": kw,
                "corpus_start": begin, "long_n": len(c), "key_values_consumed": consumed,
                "composite_independent_P_prediction_J": composite_J,
                "uniform_keyword_independent_phase_expectation_J": 1+(predicted[0]-1)/L,
                "long_forward_sample_J": sample_ioc(c), "oracle_roundtrip_exact": True,
                "known_keyword_unknown_alignment_accuracy": accuracy,
                "known_keyword_recovery_pass": accuracy >= .95}
        OUT["cases"].append(case)
        plants.append({"case_id": case_id, "plain_prefix300": plain[:300], "ciphertext": c,
                       "used_key_indices": used, "keyword": kw})
        for bank_name, bank in banks.items():
            for off in (316, 317, 318):
                for decode_model in (0, 1):
                    cid = f"c{k}_{bank_name}_{off}_{decode_model}"
                    vals = bank[off:off+407]
                    assert len(vals) == 407
                    cells += [f"cell {cid} {off} {L} {decode_model} 120 0.9 v:"+",".join(map(str, vals)),
                              "R "+" ".join(map(str, c[:300])), "T dec1"]
                    index[cid] = (k, bank_name, off, decode_model)
        save()
    (HERE/"plants.json").write_text(json.dumps(plants, separators=(",", ":"))+"\n", encoding="utf-8", newline="\n")
    (HERE/"cells.txt").write_text("\n".join(cells)+"\n", encoding="utf-8", newline="\n")
    binary = "work/h5rs/target/release/h5rs.exe"
    native([binary, "parity", relative(HERE/"cells.txt"), relative(HERE/"native_cells.txt"), "--engine", "fast"], "native_stdout.txt", "native_stderr.txt")
    actual = {}
    for line_no, line in enumerate((HERE/"native_cells.txt").read_text(encoding="utf-8").splitlines(), 1):
        parts = line.split()
        cid = parts[0]
        assert cid in index and cid not in actual
        rec = {"aborted": parts[2] == "abort", "line": line_no}
        if not rec["aborted"]:
            attrs = dict(p.split("=", 1) for p in parts[3:])
            rec.update(ioc=float(attrs["ioc"]), keyword=list(map(int, attrs["wcol"].split(","))), skips=int(attrs["skips"]))
        actual[cid] = rec
    assert len(actual) == len(index) == 144
    for case, plant_data in zip(OUT["cases"], plants):
        k, model = case["index"], case["model"]
        scores = {}
        for bank in banks:
            values = [r["ioc"] for cid, r in actual.items() if index[cid][:2] == (k, bank) and not r["aborted"]]
            scores[bank] = max(values) if values else None
        truth_id = f"c{k}_real_317_{model}"
        truth = actual[truth_id]
        case["native_true_cell"] = truth
        case["bank_cells_each"] = 6
        case["native_bank_maxima"] = scores
        case["native_true_cell_log"] = f"native_cells.txt:{truth['line']}"
        required_floor = max([1.6]+[scores[b]+.15 for b in ("iid", "structured") if scores[b] is not None])
        case["required_IoC_floor"] = required_floor
        native_accuracy, shift_selected = None, None
        equivalent = False
        if not truth["aborted"]:
            equivalent = len({(a-b) % Q for a, b in zip(truth["keyword"], case["keyword"])}) == 1
            # Select global shift ONLY by model likelihood, never by planted accuracy.
            best = None
            for shift in range(Q):
                fit = viterbi(plant_data["ciphertext"][:300], key, [(v+shift) % Q for v in truth["keyword"]], 317, model, case["clock"], logf)
                if fit and (best is None or fit[0] > best[0]):
                    best = (fit[0], fit[1], shift)
            if best:
                native_accuracy = sum(a == b for a, b in zip(best[1], plant_data["plain_prefix300"]))/300
                shift_selected = best[2]
        case["native_keyword_equivalent_by_constant_shift"] = equivalent
        case["native_keyword_then_independent_alignment_accuracy"] = native_accuracy
        case["global_shift_selected_by_likelihood"] = shift_selected
        case["native_recovery_pass"] = not truth["aborted"] and equivalent and truth["ioc"] >= required_floor and native_accuracy is not None and native_accuracy >= .95
        case["composition_witness"] = case["clock"] == "attempt" and case["composite_independent_P_prediction_J"] <= 1.003 and abs(case["long_forward_sample_J"]-1.) <= .003 and case["known_keyword_recovery_pass"] and case["native_recovery_pass"]
        save()
    regression_rel = "work/h5rs/data/plant_c1500_seg0.14.txt"
    (HERE/"retained_c1500.txt").write_bytes(read(regression_rel))
    native([binary, "decode", relative(HERE/"retained_c1500.txt"), "1500", "8", "0", "--engine", "fast", "--abort", "120", "0.9"], "c1500_stdout.txt", "c1500_stderr.txt")
    regression = (HERE/"c1500_stdout.txt").read_text(encoding="utf-8").strip()
    OUT["retained_regression"] = {"output": regression, "matches_historical_abort": regression == "ABORT",
        "planted_key_recovery_pass": False if regression == "ABORT" else None,
        "note": "ABORT remains a positive-control recovery failure, not a successful recovery control"}
    canonical = [r for r in OUT["cases"] if r["clock"] == "attempt"]
    witnesses = [r["case_id"] for r in canonical if r["composition_witness"]]
    OUT["summary"] = {"new_synthetic_native_cells": 144, "canonical_cases": len(canonical),
        "canonical_native_recovery_passes": sum(r["native_recovery_pass"] for r in canonical),
        "known_keyword_passes_all_clocks": sum(r["known_keyword_recovery_pass"] for r in OUT["cases"]),
        "composition_witnesses": witnesses, "null_banks_per_case": 2,
        "global_error_rate": "unknown; one tiny bank per null type; no p-value claimed"}
    OUT["status"] = "LIMITED_FEASIBILITY_ONLY" if witnesses and all(r["native_recovery_pass"] for r in canonical) and all(r["known_keyword_recovery_pass"] for r in OUT["cases"]) else "FAILED_RECOVERY_GATE"


def report():
    json_lines = RESULT.read_text(encoding="utf-8").splitlines()
    def at(needle):
        return next(i for i, s in enumerate(json_lines, 1) if needle in s)
    starts = {r["case_id"]: at('"case_id": "'+r["case_id"]+'"') for r in OUT["cases"]}
    boundaries = list(starts.values())+[at('"native_commands":')]
    ranges = {r["case_id"]: f"result.json:{boundaries[i]}-{boundaries[i+1]-1}" for i, r in enumerate(OUT["cases"])}
    lines = ["# D2 first-gate result", "", f"**{OUT['status']}**. Nothing in LP2 is solved (`result.json:{at(chr(34)+'status'+chr(34)+':')}`).", "",
             f"Elapsed seconds: {OUT['elapsed_seconds']}. One invocation; no automatic retry (`result.json:{at(chr(34)+'elapsed_seconds'+chr(34)+':')}`).",
             "", "All numbers below are from `result.json`, the retained native rows and the frozen protocol.",
             "This is a synthetic bounded feasibility gate, not a family exclusion or a global power test.", "",
             "| Case | Long forward IoC | Known-keyword accuracy | Native keyword + independent alignment accuracy | Native control pass | Composition witness | Native source |",
             "|---|---:|---:|---:|---|---|---|"]
    for r in OUT["cases"]:
        lines.append(f"| {r['case_id']} | {r['long_forward_sample_J']:.6f} | {r['known_keyword_unknown_alignment_accuracy']:.6f} | {r.get('native_keyword_then_independent_alignment_accuracy')} | {r.get('native_recovery_pass', 'incomplete')} | {r.get('composition_witness', 'incomplete')} | {r.get('native_true_cell_log', 'incomplete')}; {ranges[r['case_id']]} |")
    lines += ["", "## Limits", "", "- Emission-clock cases are unsupported by the native H5 model; retain them as diagnostics.",
              "- The retained c1500 failure is not replaced by a passing offset or counted as recovery.",
              "- Tiny matched null menus do not estimate campaign-wide error or twenty-case power.",
              "- No LP2 look, later calibration, engine patch, build or long run is authorized by this result.",
              "- All inputs/code/protocol hashes, partial results and exceptions: `result.json`.",
              "- Failed or incomplete cases are retained. Do not rerun this gate to improve its outcome."]
    if "error" in OUT:
        lines += ["", "## Invocation error", "", json.dumps(OUT["error"], ensure_ascii=False)]
    (HERE/"REPORT.md").write_text("\n".join(lines)+"\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    if RESULT.exists():
        raise SystemExit("Refusing a second invocation; preserve the first result and seek new approval")
    save()
    try:
        main()
    except Exception as exc:
        OUT["status"] = "INCOMPLETE_TIMEOUT" if isinstance(exc, (TimeoutError, subprocess.TimeoutExpired)) else "FAILED_EXCEPTION"
        tb = exc.__traceback__
        while tb and tb.tb_next:
            tb = tb.tb_next
        OUT["error"] = {"type": type(exc).__name__, "message": scrub(exc), "gate_line": tb.tb_lineno if tb else None}
    finally:
        save()
        report()
    print(json.dumps({"status": OUT["status"], "summary": OUT.get("summary"), "error": OUT.get("error"), "elapsed_seconds": OUT["elapsed_seconds"]}))
    if OUT["status"] not in {"LIMITED_FEASIBILITY_ONLY"}:
        raise SystemExit(1)
