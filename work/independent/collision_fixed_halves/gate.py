"""Fixed rules only; human-authorized foreground steps, no selection or subprocesses."""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "collision_followup"))
import analysis as P
from manual_common import execute, relative, repo_path, sha256
M = P.M
sys.modules.setdefault("fixed_gate", sys.modules[__name__])

B = 999
HALVES = {"A": (7, 9, 12, 14), "B": (8, 11, 13, 15)}
RULES = {"T6_raw": dict(lag=6, a=27, b=24, guarded=False),
         "I5_raw": dict(lag=5, a=1, b=0, guarded=False)}
CONFIG = dict(B=B, halves=HALVES, rules=RULES, q="81/100", selection="none",
              claims="two co-primary both-halves claims; p_both=max(p_A,p_B); Bonferroni across two rules",
              alpha_each_rule=.025, bootstrap_replicates=199, block_size=25,
              caveat="fixed now, selected from previously examined LP2; not untouched replication")


def fingerprint():
    out = P.fingerprint()
    for name in ("gate.py", "test_fixed.py", "PROTOCOL.md"):
        out[relative(HERE / name)] = sha256(HERE / name)
    return out


def units(run):
    P.units(run)
    import test_fixed
    stream = io.StringIO()
    answer = unittest.TextTestRunner(stream=stream, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(test_fixed))
    for line in stream.getvalue().splitlines():
        run.log(line)
    if not answer.wasSuccessful() or answer.skipped:
        raise RuntimeError("New fixed-rule/block identities failed")
    run.check()


def both_claim(half_results):
    out = {}
    for name in RULES:
        a, b = (half_results[h][name] for h in HALVES)
        p = max(a["p_mc"], b["p_mc"])
        out[name] = dict(p_both=p, p_adjusted=min(1., 2*p),
                         both_halves_flag=p <= .025 and a["score"] > 0 and b["score"] > 0)
    return out


def fixed_halves(d, run, seed, replicates=B):
    results = {}
    for hindex, (half, ids) in enumerate(HALVES.items()):
        dd = P.subset(d, ids)
        ds = M.section_doublets(dd["c"], dd["lengths"])
        observed = {name: P.score(dd["c"], dd["local"], rule) for name, rule in RULES.items()}
        nulls = {name: [] for name in RULES}
        # Both fixed rules share the matched null books, not a maximum statistic.
        for rep in range(replicates):
            run.check()
            c = M.conditional_null(dd["lengths"], ds, seed+hindex*1000+rep)
            for name, rule in RULES.items():
                nulls[name].append(P.score(c, dd["local"], rule))
        results[half] = {}
        for name, rule in RULES.items():
            k = sum(x >= observed[name] for x in nulls[name])
            p = (1+k)/(1+replicates)
            results[half][name] = dict(score=observed[name], p_mc=p, exceedances=k,
                                      null_scores=nulls[name], B=replicates,
                                      seed=seed+hindex*1000, doublets=ds,
                                      eligible=sum(x >= rule["lag"] for x in dd["local"]),
                                      flag_at_point025=p <= .025 and observed[name] > 0)
        run.log(f"Half {half}: "+str({k: (v['score'], v['p_mc']) for k, v in results[half].items()}))
    return dict(halves=results, claims=both_claim(results))


def load_finished(name, before, kind):
    path = repo_path(name)
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("fingerprint") != before or value.get("config") != json.loads(json.dumps(CONFIG)) or value.get("kind") != kind:
        raise ValueError("Stale/wrong artifact")
    if not (path.parent / "run.log").read_text(encoding="utf-8").rstrip().endswith("FINISHED"):
        raise ValueError("Artifact has no FINISHED log")
    return value, dict(path=relative(path), sha256=sha256(path))


def control(run, d, case):
    if case < 4:
        lag, e = ((5, 0), (5, 0), (6, 1), (6, 1))[case]
        c, _ = M.collision_plant(d["local"], d["lengths"], lag, e, 730001+case)
    else:
        ds = M.section_doublets(d["c"], d["lengths"])
        c = M.conditional_null(d["lengths"], ds, 980001)
    return dict(case=case, **fixed_halves(P.replace_book(d, c), run, 5100000+case*10000))


def certify(paths, before):
    if len(paths) != 5:
        raise ValueError("Need five controls, ordered case 0..4")
    controls, inputs = [], []
    for i, path in enumerate(paths):
        rec, source = load_finished(path, before, "control")
        if rec["case"] != i:
            raise ValueError("Controls misordered")
        controls.append(rec); inputs.append(source)
    power = {}
    for name, cases in (("T6_raw", (2, 3)), ("I5_raw", (0, 1))):
        recovered = {h: sum(controls[c]["halves"][h][name]["flag_at_point025"] for c in cases) for h in HALVES}
        null_clear = not any(controls[4]["halves"][h][name]["flag_at_point025"] for h in HALVES)
        power[name] = dict(half_recoveries_out_of_two=recovered, null_clear=null_clear,
                           coarse_gate_passed=all(n >= 1 for n in recovered.values()) and null_clear,
                           both_halves_recoveries=sum(controls[c]["claims"][name]["both_halves_flag"] for c in cases))
    return dict(rule_controls=power, inputs=inputs,
                precision="two plants per rule; population power unknown; failures must not become LP2 exclusions")


def block_range(block):
    if block not in range(8):
        raise ValueError("Block must be 0..7")
    return range(block*25, min((block+1)*25, 199))


def section_observed(d):
    rows = P.section_rows(d)
    shape, fit = P.heterogeneity(rows)
    return dict(rows=rows, shape_statistic=shape, fit_statistic=fit)


def section_block(d, baseline, block, run):
    result = []
    for rep in block_range(block):
        run.check()
        book = []
        for s in d["sections"]:
            r = next((r for r in baseline["rows"] if r["section"] == s["section"]), None)
            q = r["q_raw_moment"] if r else .81
            loc = [p for n in s["word_lengths"] for p in range(n)]
            c, _ = M.collision_plant(loc, [s["length"]], 6, 1,
                                     3100000+rep*20+s["section"], q)
            book.extend(c)
        rows = P.section_rows(P.replace_book(d, book))
        shape, fit = P.heterogeneity(rows)
        result.append(dict(rep=rep, shape=shape, fit=fit))
        run.log(f"Block {block}, replicate {rep}: complete")
    return dict(block=block, samples=result)


def merge_samples(blocks):
    if len(blocks) != 8 or [r["block"] for r in blocks] != list(range(8)):
        raise ValueError("Need exactly blocks 0..7 in order")
    samples = []
    for block in blocks:
        if [r["rep"] for r in block["samples"]] != list(block_range(block["block"])):
            raise ValueError("Missing, duplicated or altered replicate range")
        samples.extend(block["samples"])
    return samples


def action(run, args):
    before = fingerprint()
    units(run)
    run.log(CONFIG)
    if args.mode == "certify":
        result = certify(args.inputs, before)
    else:
        d = P.G.data()
        if args.mode == "control":
            result = control(run, d, args.case)
        elif args.mode == "halves":
            cert, source = load_finished(args.certificate, before, "certify")
            result = fixed_halves(d, run, 5300000)
            result.update(certificate=source, rule_controls=cert["rule_controls"])
            # Always return the fixed diagnostic; any failed gate withholds inference.
            for name, claim in result["claims"].items():
                claim["inference_eligible"] = cert["rule_controls"][name]["coarse_gate_passed"]
                claim["controlled_flag"] = claim["both_halves_flag"] and claim["inference_eligible"]
        elif args.mode == "section-observed":
            result = section_observed(d)
        else:
            baseline, source = load_finished(args.baseline, before, "section-observed")
            if args.mode == "section-block":
                result = section_block(d, baseline, args.block, run)
            else:
                blocks, sources = [], []
                for name in args.inputs:
                    rec, src = load_finished(name, before, "section-block")
                    if rec["baseline"] != source:
                        raise ValueError("Bootstrap blocks have different baseline")
                    blocks.append(rec); sources.append(src)
                samples = merge_samples(blocks)
                result = dict(rows=baseline["rows"], shape_statistic=baseline["shape_statistic"],
                              fit_statistic=baseline["fit_statistic"], samples=samples,
                              p_shape=(1+sum(r["shape"] >= baseline["shape_statistic"] for r in samples))/200,
                              p_fit=(1+sum(r["fit"] >= baseline["fit_statistic"] for r in samples))/200,
                              inputs=sources,
                              caveat="refitted plug-in parametric bootstrap, selected T6 family; heterogeneity-sized power unknown; not an exclusion")
            result["baseline"] = source
    run.check()
    if fingerprint() != before:
        raise RuntimeError("Code/input/protocol changed during invocation")
    result.update(fingerprint=before, config=CONFIG, kind=args.mode, lp2_solved=False)
    run.save(args.mode+".json", result)
    run.log(f"Saved {args.mode}.json; no selection, nothing in LP2 solved")
    if args.mode == "certify":
        run.log(result["rule_controls"])
    if args.mode == "halves":
        run.log(result["claims"])
    if args.mode == "section-merge":
        run.log(f"p_shape={result['p_shape']}; p_fit={result['p_fit']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("control", "certify", "halves", "section-observed", "section-block", "section-merge"))
    ap.add_argument("--case", type=int, choices=range(5), default=0)
    ap.add_argument("--block", type=int, choices=range(8), default=0)
    ap.add_argument("--certificate")
    ap.add_argument("--baseline")
    ap.add_argument("--inputs", nargs="*", default=[])
    ap.add_argument("--seconds", type=float, default=95)
    args = ap.parse_args()
    if not 0 < args.seconds <= 95:
        ap.error("Foreground cooperative cap must be <=95 seconds")
    raise SystemExit(execute("collision-fixed-"+args.mode, lambda run: action(run, args), args.seconds))
