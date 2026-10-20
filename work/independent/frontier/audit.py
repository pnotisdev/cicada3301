"""Offline provenance/arithmetic audit, NOT a cryptanalytic search.

Reads repository text as data. Imports no project modules and launches no engines,
subprocesses, threads, network requests, or statistical searches. Writes only here.
Run once from the repository root: python -B work/independent/frontier/audit.py
"""
from __future__ import annotations

import collections
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import struct
import time
import tomllib

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
START = time.monotonic()
INPUTS = {}
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
LATIN = "F U TH O R C G W H N I J EO P X S T B E M L ING OE D A AE Y IA EA".split()
RI = {r: k for k, r in enumerate(RUNES)}


def read(rel):
    if time.monotonic() - START > 90:
        raise RuntimeError("Audit exceeded cooperative 90-second design cap")
    data = (ROOT / rel).read_bytes()
    INPUTS[rel] = hashlib.sha256(data).hexdigest()
    return data.decode("utf-8-sig")


def parse(raw):
    # Independent character scanner: / and % are wraps; other semantic tokens
    # terminate words. ASCII whitespace used to format the transcription is ignored.
    c, words, word, nums = [], [], [], []
    breaks, marks = [], []
    i = 0
    while i < len(raw):
        ch = raw[i]
        if ch in RI:
            word.append(RI[ch])
            c.append(RI[ch])
        elif ch in "/%":
            breaks.append((len(c), ch))
        elif ch in "-.&":
            if word:
                words.append(tuple(word))
                word = []
            marks.append((len(c), ch))
        elif ch.isalnum():
            if word:
                words.append(tuple(word))
                word = []
            j = i + 1
            while j < len(raw) and raw[j].isalnum() and raw[j] not in RI:
                j += 1
            nums.append((len(c), raw[i:j]))
            i = j - 1
        i += 1
    if word:
        words.append(tuple(word))
    assert sum(map(len, words)) == len(c)
    return dict(c=c, words=words, nums=nums, breaks=breaks, marks=marks)


def window_records(rel):
    records = []
    for line in read(rel).splitlines():
        if line.startswith("W "):
            name, prev = line[2:].rsplit(" ", 1)
            records.append(dict(name=name, prev=int(prev), n=0, lens=[]))
        elif line.startswith("R "):
            records[-1]["n"] = len(line[2:].split())
        elif line.startswith("L "):
            records[-1]["lens"] = list(map(int, line[2:].split()))
    for r in records:
        r["length_sum"] = sum(r["lens"])
        r["layout_valid"] = r["n"] == r["length_sum"]
    return records


def frac(f):
    return {"exact": str(f), "decimal": float(f)}


def main():
    read("work/independent/frontier/audit.py")  # fingerprint this inventory implementation too
    read("work/independent/frontier/LIKELIHOOD_NOTE.md")
    body = read("work/ref/lp_verified.txt").split("\n\n", 1)[1].split("§", 1)[0]
    segs = [parse(raw) for raw in body.split("$") if any(r in RI for r in raw)]
    sections = []
    for sid in range(7, 16):
        s = segs[sid]
        c, words = s["c"], s["words"]
        sections.append({
            "section": f"0.{sid}", "runes": len(c), "words": len(words),
            "transitions": len(c)-1,
            "doublets": sum(x == y for x, y in zip(c, c[1:])),
            "lag5_pairs": sum(max(len(w)-5, 0) for w in words),
            "lag5_hits": sum(w[k] == w[k-5] for w in words for k in range(5, len(w))),
            "lag5_S_opportunities": sum(w[k-5] == 15 for w in words for k in range(5, len(w))),
            "lag5_S_hits": sum(w[k] == w[k-5] == 15 for w in words for k in range(5, len(w))),
            "lag6_pairs": sum(max(len(w)-6, 0) for w in words),
            "lag6_T_hits": sum(w[k] == (24-2*w[k-6]) % 29 for w in words for k in range(6, len(w))),
            "nonrune_tokens": s["nums"],
            "line_tokens": sum(t == "/" for _, t in s["breaks"]),
            "page_tokens": sum(t == "%" for _, t in s["breaks"]),
        })
    cols = ("runes", "words", "transitions", "doublets", "lag5_pairs", "lag5_hits", "lag5_S_opportunities", "lag5_S_hits", "lag6_pairs", "lag6_T_hits")
    totals = {k: sum(s[k] for s in sections) for k in cols}
    assert [totals[k] for k in cols] == [12956, 2896, 12947, 86, 2105, 104, 74, 11, 1290, 80]
    pair_counts = collections.Counter((a, b) for s in segs[7:16] for a, b in zip(s["words"], s["words"][1:]))
    repeated = [{"words": ["".join(LATIN[r] for r in w) for w in pair], "count": n} for pair, n in pair_counts.items() if n > 1]
    reg = tomllib.loads(read("docs/registry.toml"))
    statuses = dict(collections.Counter(x["status"] for x in reg["experiment"]))
    windows = {}
    for rel in ("work/kscreen/data/segments.txt", "work/kscreen/data/heads.txt", "work/kscreen/data/pages.txt", "work/kscreen/data/staggered.txt"):
        if (ROOT / rel).exists():
            rows = window_records(rel)
            windows[rel] = {"count": len(rows), "invalid_layout": [r for r in rows if not r["layout_valid"]], "records": rows}
    # Some generated stream names contain control characters; ordinary CSV plus
    # splitlines is not a reliable record parser for this particular TSV export.
    rows = []
    tail_pattern = re.compile(r"^(.*)\t(\d+)\t(\d+)\t([0-9.]+)\t([01])$")
    for line in read("work/kscreen/data/library.tsv").split("\n"):
        m = tail_pattern.fullmatch(line.rstrip("\r"))
        if m:
            rows.append(dict(zip(("name", "length", "period", "predicted_ioc_english", "excluded_by_global_ioc"), m.groups())))
    rel = "work/kscreen/data/library.ksb"
    binary = (ROOT / rel).read_bytes()
    INPUTS[rel] = hashlib.sha256(binary).hexdigest()
    assert binary[:4] == b"KSB1"
    binary_count = struct.unpack_from("<I", binary, 4)[0]
    lib_count = len(rows)
    assert lib_count == binary_count, (lib_count, binary_count)
    lib_flagged = sum(int(r["excluded_by_global_ioc"]) for r in rows)
    # This is an independent-phases marginal calculation, NOT a forward-key plant.
    prime_square = next(r for r in rows if r["name"] == "primes^2")
    J = Fraction(prime_square["predicted_ioc_english"])
    ideal_keyword_L20_ioc = 1 + (J - 1)/20
    gate_source = read("work/tmp/gated_null_gate.py")
    assert "NULL_RATE = 0.42" in gate_source and "Q_NULL = 0.028" in gate_source
    scope_log = read("work/tmp/lag_feedback_scope_extension.txt")
    scope_source = read("work/tmp/lag_sweep_main.py")
    assert "d in {5,6}" in scope_log and "scope sweep" in scope_source
    q = Fraction(81, 100)
    rho = q/29
    real_cells = 581 * 8 * 2000 * 19 * 2
    campaign_null_cells = 8 * 8 * 2000 * 19 * 2
    control_cells = 4 * 8 * 50 * 19 * 2
    looks = {
        "registered_rows": len(reg["experiment"]),
        "registered_nonobserved_rows": sum(x["status"] != "observed" for x in reg["experiment"]),
        "affine_lag_cells": 8*28*29,
        "advertised_full_four_scope_menu_not_verified_as_executed": 4*8*28*29,
        "executed_scope_extension_rows_four_scopes_two_lags": 4*2*28*29,
        "word_all_eight_lags_plus_nonword_two_lags_unique_rows": (8+3*2)*28*29,
        "residual_chi_square_b_shift_classes_upper_bound_on_unique_scores": (8+3*2)*28,
        "later_kernel_cells_including_guards_and_mixtures": 2*8*28*29+3,
        "family_diagnostic_cells": 25*10,
        "lag_by_source_cells_logged": 8*29,
        "repeat_spectrum_lengths": 8,
        "wordlen_parameter_settings": 161*2,
        "corpus_spelling_rows": 17*2,
        "wordlen_two_parameter_grid": 11*81,
        "wordlen_mechanism_grid": 4*91,
        "wordlen_expansions": 7+1,
        "executed_residual_rows_plus_later_kernel_menu_not_independent": (8+3*2)*28*29 + (2*8*28*29+3),
        "effective_independent_looks": "unknown; overlapping cells and adaptive history; do not sum as independent tests",
    }
    arithmetic = {
        "h5_real_cells": real_cells,
        "h5_campaign_null_cells": campaign_null_cells,
        "h5_small_control_cells": control_cells,
        "h5_real_to_campaign_null_ratio": frac(Fraction(real_cells, campaign_null_cells)),
        "h5_real_to_small_control_ratio": frac(Fraction(real_cells, control_cells)),
        "source_S_gross_collision_budget_at_q_081": frac(rho*74),
        "shared_lag5_lag6_excess_rounded_input": "(104-36)-(72.9-27.8)+(80-44.9) = 58.0; expectations are rounded different-null outputs",
        "shared_collision_attempt_mean_at_q_081": frac(rho*1290),
        "global_doublet_fraction": frac(Fraction(86, 12947)),
        "global_doublet_percent": frac(100*Fraction(86, 12947)),
        "ungated_null_one_step_mass_if_null_value_factor_omitted": frac(1 + 28*Fraction(28, 1000)),
        "proper_uniform_null_one_step_mass": frac(Fraction(1)),
        "prime_square_library_marginal_ioc": frac(J),
        "expected_ioc_after_random_keyword_L20_independent_phases": frac(ideal_keyword_L20_ioc),
        "marginal_formula_warning": "No collision rule, finite-stream clock correlations or decoder power calibrated by this calculation.",
        "generic_unigrams_and_bigrams_cannot_be_exactly_iid": "Doublet deficit already rules out exact iid bigrams; flat means no other detected departures, not equality to iid.",
    }
    # Bonferroni sensitivity only. NOT reconstructed historical/global p-values.
    sensitivity = {str(M): {str(p): min(1.0, M*p) for p in (0.001, 0.008, 0.007, 0.016)} for M in (1, 10, 62, 95)}
    audit = dict(kind="read-only inventory and exact arithmetic, not a cryptanalytic search or exclusion", totals=totals,
                 sections=sections, registry_statuses=statuses, adjacent_word_pairs=sum(pair_counts.values()),
                 repeated_adjacent_word_pairs=repeated, windows=windows,
                 local_library=dict(rows=lib_count, flagged_by_plain_additive_marginals=lib_flagged, unflagged=lib_count-lib_flagged),
                 looks=looks, arithmetic=arithmetic, hypothetical_bonferroni_sensitivity=sensitivity,
                 sensitivity_warning="M is hypothetical; p values have different nulls and existing local corrections. Reported MC .001 is a floor, not a known true tail probability.",
                 input_sha256=INPUTS, elapsed_seconds=round(time.monotonic()-START, 4))
    (HERE / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
    lines = ["# Frontier audit: completed offline inventory and algebra", "", "No engines, searches, simulation, new significance tests or exclusions. Input hashes and full records: `audit.json`.", "", "## Independently scanned canonical transcription", "", "| section | runes | words | doublets | lag5 eligible / hits / S hits | lag6 eligible / T hits |", "|---|---:|---:|---:|---|---|"]
    for s in sections:
        lines.append(f"| {s['section']} | {s['runes']} | {s['words']} | {s['doublets']} | {s['lag5_pairs']} / {s['lag5_hits']} / {s['lag5_S_hits']} | {s['lag6_pairs']} / {s['lag6_T_hits']} |")
    lines += ["", "Totals: "+json.dumps(totals), f"Adjacent word pairs: {sum(pair_counts.values())}; repeated types: {repeated}.", "", "## Registry and local exports", "", f"Registry statuses: {statuses}.", f"Local library.tsv: {lib_count} rows; {lib_flagged} plain-additive marginal flags; {lib_count-lib_flagged} unflagged. This is local generated data, not new family coverage."]
    for rel, info in windows.items():
        lines.append(f"- `{rel}`: {info['count']} windows; {len(info['invalid_layout'])} have L sums different from R length.")
        for r in info["invalid_layout"]:
            lines.append(f"  - {r['name']}: R={r['n']}, L sum={r['length_sum']}. Default IoC does not use L; layout-option fallbacks are a separate scope issue.")
    lines += ["", "## Mechanical look menus (not independent trial counts)", ""]
    lines += [f"- {k}: {v}" for k, v in looks.items()]
    lines += ["", "## Exact arithmetic and explicit reference assumptions", ""]
    lines += [f"- {k}: {v}" for k, v in arithmetic.items()]
    lines += ["", "## Hypothetical family-multiplicity sensitivity, NOT global p-values", "", "Columns use the reported .001 MC floor, .008 fixed-halves adjusted p, .007 S-related calibration, .016 word-shuffle p, respectively."]
    lines += [f"- M={M}: {values}" for M, values in sensitivity.items()]
    lines += ["", "Existing local corrections must not be counted twice. Historical effective independent looks and a calibrated global p remain unknown.", "", "The registry's broad four-scope lag-1..8 phrasing is not the recorded executed grid: the non-word scope extension is only lags 5 and 6. All b shifts only relabel residual histograms, leaving chi-square unchanged: 392 b-shift classes are an upper bound on distinct numerical scores, not a measured count of unique values. Do not count the advertised 25,984-cell rectangle as executed independent tests.", "", "## Static-audit caveats", "", "- The un-gated prototype gives each possible null value weight rho, rather than rho/29. Summing its one-output masses yields 1+28*rho, not the stated local Bernoulli kernel. This does NOT alone invalidate the ratio: a different globally conditioned mask prior can have a common language/uniform normalizer (LIKELIHOOD_NOTE.md). The gated deterministic-null original is different and is not refuted by this identity.", "- Prototype NULL_RATE=.42 is per eligible position, while the decoder uses .028; neither is the reported .42 per multi-rune WORD. Its report also retains a wrong-plaintext-window caveat. These are different experiments.", "- The random-key full PLANTS in gated_null_report.md are true-key positives, not wrong-key nulls. Their 5/12 passes are not a false-positive estimate.", "- No exact-offset requirement is assumed equivalent to plaintext/key-family detection. That requires a new calibrated gate, not automatic authorization to screen.", "", f"FINISHED; elapsed seconds: {audit['elapsed_seconds']}. No statistical gate or search was run; invocation history is in RUN_LOG.md."]
    (HERE / "AUDIT.md").write_text("\n".join(lines)+"\n", encoding="utf-8", newline="\n")
    print("FINISHED: work/independent/frontier/AUDIT.md and audit.json")
    print(json.dumps({"totals": totals, "local_library": audit["local_library"], "invalid_layouts": {k: len(v["invalid_layout"]) for k,v in windows.items()}, "elapsed_seconds": audit["elapsed_seconds"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
