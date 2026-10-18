"""HUMAN STARTS THIS. No experiments run on import.

Modes: tables (unit identities + exact raw-spend means), controls (short power
calibration), test (requires current passing controls; conditional Markov-null test).
No engine, GPU, API, network, background job or shared-document writes.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction as F
import io
import json
import math
from pathlib import Path
import random
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from manual_common import execute, lp_module, relative, repo_path, sha256
import collision_model as M


CONFIG = dict(q=str(M.DESIGN_Q), null_replicates=99, alpha=0.05,
              scan="812 affine maps x 8 lags x raw/guarded + 3 fixed mixtures",
              key_mode="spend only; hold needs plaintext law")


def snapshot():
    paths = [HERE / name for name in ("gate.py", "collision_model.py", "test_collision_model.py")]
    paths += [HERE.parent / "manual_common.py", HERE.parent.parent / "lp.py",
              HERE.parent.parent / "ref" / "lp_verified.txt"]
    return {relative(path): sha256(path) for path in paths}


def units(run):
    import test_collision_model
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromModule(test_collision_model)
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    for line in stream.getvalue().splitlines():
        run.log(line)
    run.check()
    if not result.wasSuccessful() or result.skipped:
        raise RuntimeError("Unit gate failed; a skip also counts as failure")
    return result.testsRun


def data():
    lp = lp_module()
    segments = lp.load_segments()
    c, local, lengths, words, by_position, section_records = [], [], [], [], Counter(), []
    for section in range(7, 16):
        runes = lp.runes_of(segments[section])
        spans = lp.word_spans(segments[section], runes)
        loc = [-1] * len(runes)
        section_lengths = []
        for _, a, b in spans:
            words.append((len(c) + a, len(c) + b))
            section_lengths.append(b - a)
            for i in range(a, b):
                loc[i] = i - a
                by_position[i - a] += 1
        if any(p < 0 for p in loc):
            raise ValueError("The word layout does not cover all runes")
        ds = sum(a == b for a, b in zip(runes, runes[1:]))
        section_records.append(dict(section=section, runes=runes, word_lengths=section_lengths,
                                    doublets=ds, length=len(runes)))
        c.extend(runes)
        local.extend(loc)
        lengths.append(len(runes))
    pair_counts = {lag: sum(max(b - a - lag, 0) for a, b in words)
                   for lag in range(1, max(by_position) + 1)}
    cited = [10060, 7247, 4882, 3237, 2105, 1290, 731, 388, 201, 92, 35, 10]
    if len(c) != 12956 or any(pair_counts.get(lag) != expected for lag, expected in enumerate(cited, 1)):
        raise ValueError("Current input/layout differs from the cited LP2 counts; inspect before continuing")
    n_by_pos = [by_position[p] for p in range(max(by_position) + 1)]
    return dict(c=c, local=local, lengths=lengths, words=words, n_by_pos=n_by_pos,
                pair_counts=pair_counts, sections=section_records)


def observed_profiles(d):
    """Exact permutation expectations: no Monte Carlo shuffles or invented means."""
    rows = {}
    offset = 0
    for section in d["sections"]:
        c, sizes, n = section["runes"], section["word_lengths"], section["length"]
        counts = Counter(c)
        pos_count = Counter(p for length in sizes for p in range(length))
        for e in (0, 1):
            permutation = [F(counts[x] * (counts[M.transform(x, e)] - (M.transform(x, e) == x)), n * (n - 1))
                           for x in range(29)]
            for lag in range(1, len(d["n_by_pos"])):
                for j in range(len(d["n_by_pos"]) - lag):
                    pairs = pos_count[j + lag]
                    if not pairs:
                        continue
                    key = (lag, e, j)
                    row = rows.setdefault(key, dict(lag=lag, relation="I" if e == 0 else "T",
                                                     earlier_position=j, pairs=0,
                                                     observed_by_source=[0] * 29,
                                                     exact_shuffle_by_source=[F(0)] * 29))
                    row["pairs"] += pairs
                    for x in range(29):
                        row["exact_shuffle_by_source"][x] += pairs * permutation[x]
        start = 0
        for length in sizes:
            for j in range(length):
                x = c[start + j]
                for lag in range(1, length - j):
                    y = c[start + j + lag]
                    for e in (0, 1):
                        if y == M.transform(x, e):
                            rows[lag, e, j]["observed_by_source"][x] += 1
            start += length
        offset += n
    out = []
    for key, row in sorted(rows.items()):
        row["observed_total"] = sum(row["observed_by_source"])
        row["exact_shuffle_total"] = str(sum(row["exact_shuffle_by_source"], F(0)))
        row["exact_shuffle_by_source"] = [str(v) for v in row["exact_shuffle_by_source"]]
        out.append(row)
    return out


def correlation_audit(d):
    rows = []
    q = M.DESIGN_Q
    for section in d["sections"]:
        c = section["runes"]
        pairs = hits = 0
        start = 0
        for length in section["word_lengths"]:
            for i in range(start + 6, start + length):
                pairs += 1
                hits += c[i] == M.transform(c[i - 6], 1)
            start += length
        if not pairs:
            continue
        doublet_rate = F(section["doublets"], section["length"] - 1)
        rows.append(dict(section=section["section"], pairs=pairs, hits=int(hits),
                         transitions=section["length"] - 1, doublets=section["doublets"],
                         echo_excess_iid=float(F(int(hits), pairs) - F(1, 29)),
                         avoided_deficit=float(F(1, 29) - doublet_rate),
                         avoided_fixed_q=float(doublet_rate * q / (1 - q))))

    def corr(name):
        x = [r["echo_excess_iid"] for r in rows]
        y = [r[name] for r in rows]
        mx, my = sum(x) / len(x), sum(y) / len(y)
        numerator = sum((a - mx) * (b - my) for a, b in zip(x, y))
        den = math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))
        return numerator / den if den else None
    return dict(rows=rows, contributing_sections=len(rows),
                pearson_deficit=corr("avoided_deficit"), pearson_fixed_q=corr("avoided_fixed_q"),
                uncertainty="unknown; small heterogeneous section counts; no significance claim")


def budget_controls(run, d):
    # A same-layout legal collision plant must not flag. A deliberately strong
    # independent overlay must flag. This tests wiring, not LP2-sized power.
    null, _ = M.collision_plant(d["local"], d["lengths"], 6, 1, 749001)
    null_result = M.budget_evalue(null, d["local"])
    rng, plant, starts, at = random.Random(749002), [], set(), 0
    for n in d["lengths"]:
        starts.add(at)
        at += n
    for i, p in enumerate(d["local"]):
        value = rng.randrange(29)
        if i not in starts and value == plant[-1] and rng.random() < float(M.DESIGN_Q):
            v = rng.randrange(28)
            value = v + (v >= plant[-1])
        if p >= 6 and rng.random() < 0.5:
            value = plant[i - 5] if rng.randrange(2) == 0 else M.transform(plant[i - 6], 1)
        plant.append(value)
    positive = M.budget_evalue(plant, d["local"])
    passed = not null_result["reject_budget"] and positive["reject_budget"]
    record = dict(passed=passed, legal_collision_null=null_result, strong_overlay_positive=positive,
                  seeds=[749001, 749002], overlay_probability=0.5,
                  power="strong out-of-family wiring control only; LP2-sized power UNKNOWN")
    run.save("budget_controls.json", record)
    run.log(f"Budget controls: legal-null flag={null_result['reject_budget']}; strong-positive flag={positive['reject_budget']}")
    if not passed:
        raise RuntimeError("Budget controls failed; do not interpret an LP2 budget statistic")
    run.check()


def tables(run, args, before, d, unit_count):
    run.log("Exact rational means: raw spend-key rules only; hold-key numerical means UNKNOWN.")
    position, aggregate = M.exact_tables(d["n_by_pos"], check=run.check)
    profiles = observed_profiles(d)
    budget_controls(run, d)
    budget = M.budget_evalue(d["c"], d["local"], q_max=1.0)
    audit = correlation_audit(d)
    c, local = d["c"], d["local"]
    intersections = dict(eligible_lag6=sum(p >= 6 for p in local),
                         lag6_hits=sum(c[i] == M.transform(c[i - 6], 1) for i, p in enumerate(local) if p >= 6),
                         W3_direct_causal_upper=sum(c[i] == M.transform(c[i - 6], 1) and c[i - 1] == c[i - 6]
                                                   for i, p in enumerate(local) if p >= 6))
    if snapshot() != before:
        raise RuntimeError("Inputs or code changed during the calculation; rerun on a stable snapshot")
    header = dict(fingerprint=before, config=CONFIG, units=unit_count,
                  n_by_target_position=d["n_by_pos"], pair_counts=d["pair_counts"],
                  source_classes={"source_8": [8], "each_source_other_than_8": [x for x in range(29) if x != 8]},
                  note="Each non-8 source has the listed mean separately, not the sum for all 28.",
                  unknown=["hold-key unconditional counts", "guarded unconditional counts",
                           "joint goodness-of-fit and its power", "which rules survive a joint check",
                           "cross-word unconditional numeric means"], lp2_decryption=False)
    run.save("table_manifest.json", header)
    run.save("exact_position_means.json", position)
    run.save("exact_aggregate_means.json", aggregate)
    run.save("observed_profiles.json", profiles)
    run.save("budget_evalue.json", budget)
    run.save("correlation_audit.json", audit)
    run.save("intersections.json", intersections)
    for row in aggregate:
        if row["rule"] in ("I_5", "T_6", "mix_I5_T6_w=1/2") and row["lag"] in (3, 4, 5, 6, 7, 8):
            run.log(f"{row['rule']} lag={row['lag']} rel={row['relation']}: expected={float(F(row['expected_any_source'])):.6f}; "
                    f"excess-vs-Markov={float(F(row['excess_vs_markov_any_source'])):+.6f}")
    run.log(f"Budget diagnostic: {budget}")
    run.log(f"Recomputed correlation (definition matters): deficit={audit['pearson_deficit']}, "
            f"fixed-q={audit['pearson_fixed_q']}, contributing sections={audit['contributing_sections']}; uncertainty UNKNOWN")
    run.log("Exact means are NOT confidence intervals. No rule has been declared to fit both echoes.")


def controls(run, args, before, d, unit_count):
    records = []
    for rep, (lag, exponent) in enumerate(((5, 0), (5, 0), (6, 1), (6, 1))):
        c, repairs = M.collision_plant(d["local"], d["lengths"], lag, exponent, 730001 + rep)
        answer = M.randomization_test(c, d["local"], d["lengths"], 800000 + rep * 1000, check=run.check)
        record = dict(kind="plant", rule=f"{'I' if exponent == 0 else 'T'}_{lag}",
                      repair_attempts=len(repairs), **answer)
        records.append(record)
        run.save(f"plant_{rep}.json", record)
        run.log(f"Plant {rep + 1}/4 {record['rule']}: p={answer['p_mc']:.4f}, flag={answer['flag']}")
    ds = M.section_doublets(d["c"], d["lengths"])
    null = M.conditional_null(d["lengths"], ds, 980001)
    null_result = M.randomization_test(null, d["local"], d["lengths"], 990001, check=run.check)
    run.save("null_control.json", null_result)
    successes = sum(r["flag"] for r in records)
    passed = successes >= 3 and not null_result["flag"]
    if snapshot() != before:
        raise RuntimeError("Inputs or code changed during controls; no passing record")
    run.save("controls.json", dict(passed=passed, fingerprint=before, config=CONFIG, units=unit_count,
                                   plant_flags=successes, plants=records, null_control=null_result,
                                   power="small-sample gate only; precision UNKNOWN"))
    run.log(f"Plants flagged: {successes}/4; null falsely flagged: {null_result['flag']}")
    run.log("CONTROLS PASSED" if passed else "CONTROLS FAILED: do not test LP2 with this calibration")
    if not passed:
        raise RuntimeError("Recovery/null gate failed; not an LP2 negative")


def test(run, args, before, d, unit_count):
    if not args.controls:
        raise ValueError("test requires --controls <repository-relative controls.json>")
    path = repo_path(args.controls)
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("passed") is not True or record.get("fingerprint") != before or record.get("config") != CONFIG:
        raise ValueError("Controls missing, failed, or stale: rerun controls")
    answer = M.randomization_test(d["c"], d["local"], d["lengths"], 1033001, check=run.check)
    if snapshot() != before:
        raise RuntimeError("Inputs or code changed during test; incomplete")
    run.save("test.json", dict(fingerprint=before, config=CONFIG, units=unit_count,
                               controls_path=relative(path), controls_sha256=sha256(path), **answer,
                               interpretation="Deviation from conditional Markov null only; joint fit UNKNOWN; collision causality not identifiable; nothing solved"))
    run.log(f"Full-search maximum: {answer['observed']['maximum']:.6f}; p_MC={answer['p_mc']:.4f}")
    run.log(f"Winning kernel setting (NOT plaintext): {answer['observed']['best']}")
    run.log("KERNEL DEVIATION FLAG" if answer["flag"] else "No kernel flag against this stated null")
    run.log("This does NOT establish both-echo fit, key consumption, collision causality, or decryption.")


def action(run, args):
    before = snapshot()
    unit_count = units(run)
    d = data()
    run.log(f"Read-only layout: {len(d['c'])} runes, {len(d['words'])} words; longest word {len(d['n_by_pos'])}")
    run.log(CONFIG)
    {"tables": tables, "controls": controls, "test": test}[args.mode](run, args, before, d, unit_count)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("tables", "controls", "test"))
    ap.add_argument("--controls", help="passing controls.json, needed only for test")
    ap.add_argument("--seconds", type=float, default=120, help="foreground wall budget; no silent continuation")
    args = ap.parse_args()
    raise SystemExit(execute(f"collision-{args.mode}", lambda run: action(run, args), args.seconds))
