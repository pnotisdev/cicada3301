"""Human-run only. No import-time experiments; no discriminator implemented."""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction as F
import importlib.util
import io
import json
import math
from pathlib import Path
import random
import re
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from manual_common import execute, relative, repo_path, sha256, lp_module
OLD = HERE.parent / "collision_substitution"
sys.path.insert(0, str(OLD))
import collision_model as M
spec = importlib.util.spec_from_file_location("previous_collision_gate", OLD / "gate.py")
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)

B = 999
TRAIN = (7, 9, 12, 14)
VALIDATE = (8, 11, 13, 15)
CONFIG = dict(B=B, alpha=0.05, q="81/100", train=TRAIN, validate=VALIDATE,
              selection="unchanged full affine/lag/raw/guarded scan and 3 mixtures",
              tie="existing scan order, first maximum", seeds="fixed in source",
              caveat="retrospective split stability, not untouched replication")


def fingerprint():
    out = G.snapshot()
    for path in (HERE / "analysis.py", HERE / "test_followup.py", HERE / "PROTOCOL.md",
                 HERE.parent.parent / "ref" / "emerson_essays1.txt"):
        out[relative(path)] = sha256(path)
    return out


def units(run):
    import test_collision_model
    import test_followup
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m)
                               for m in (test_collision_model, test_followup))
    stream = io.StringIO()
    answer = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    for line in stream.getvalue().splitlines():
        run.log(line)
    if not answer.wasSuccessful() or answer.skipped:
        raise RuntimeError("Unit gate failed (skips forbidden)")
    run.check()


def subset(d, ids):
    c, local, lengths = [], [], []
    for s in d["sections"]:
        if s["section"] in ids:
            c.extend(s["runes"])
            local.extend(p for n in s["word_lengths"] for p in range(n))
            lengths.append(s["length"])
    return dict(c=c, local=local, lengths=lengths)


def score(c, local, rule):
    """Single frozen rule, never reselect on the validation half."""
    import numpy as np
    c, local = np.asarray(c), np.asarray(local)
    q = float(M.DESIGN_Q)
    if "lag" in rule:
        idx = np.flatnonzero(local >= rule["lag"])
        x, a, y = c[idx-rule["lag"]], c[idx-1], c[idx]
        r = (rule["a"] * x + rule["b"]) % 29
        base = np.where(y == a, (1-q)/29, (1+q/28)/29)
        prob = (1-q*(y == a)+q*(y == r))/29
        if rule["guarded"]:
            prob = np.where(r == a, base, prob)
    else:
        w = float(F(rule["rule"].split("=")[1]))
        idx = np.flatnonzero(local >= 1)
        a, y = c[idx-1], c[idx]
        base = np.where(y == a, (1-q)/29, (1+q/28)/29)
        prob = base.copy()
        for lag, weight, aa, bb in ((5, w, 1, 0), (6, 1-w, 27, 24)):
            active = local[idx] >= lag
            r = (aa*c[np.maximum(idx-lag, 0)]+bb) % 29
            prob += q/29 * weight * active * ((y == r).astype(float)-(y != a)/28)
    return float(np.log(prob/base).sum())


def mc(c, local, lengths, seed, check, frozen=None):
    ds = M.section_doublets(c, lengths)
    obs = M.scan(c, local, check) if frozen is None else score(c, local, frozen)
    target = obs["maximum"] if frozen is None else obs
    nulls = []
    for b in range(B):
        check()
        cc = M.conditional_null(lengths, ds, seed+b)
        nulls.append(M.scan(cc, local, check)["maximum"] if frozen is None else score(cc, local, frozen))
    k = sum(x >= target for x in nulls)
    return dict(observed=obs, null_scores=nulls, exceedances=k, p_mc=(1+k)/(B+1),
                flag=(1+k)/(B+1) <= .05, B=B, seed=seed, doublets=ds)


def split(c, local, lengths, d, run, seed):
    # Select once on TRAIN, including all maps and guarded choices.
    training = subset(d, TRAIN)
    validation = subset(d, VALIDATE)
    rule = M.scan(training["c"], training["local"], run.check)["best"]
    answer = mc(**validation, seed=seed, check=run.check, frozen=rule)
    return dict(training_rule=rule, train_sections=TRAIN, validation_sections=VALIDATE,
                heldout=answer, stability_flag=answer["flag"] and answer["observed"] > 0,
                untouched_replication=False)


def replace_book(d, c):
    out, start = [], 0
    for s in d["sections"]:
        n = s["length"]
        out.append(dict(s, runes=c[start:start+n]))
        start += n
    return dict(d, c=c, sections=out)


def control_case(run, args, d):
    case = args.case
    if case < 4:
        lag, e = ((5, 0), (5, 0), (6, 1), (6, 1))[case]
        c, repairs = M.collision_plant(d["local"], d["lengths"], lag, e, 730001+case)
        seed = 800000+case*1000
    else:
        c = M.conditional_null(d["lengths"], M.section_doublets(d["c"], d["lengths"]), 980001)
        repairs, seed = [], 990001
    full = mc(c, d["local"], d["lengths"], seed, run.check)
    sd = replace_book(d, c)
    half = split(c, d["local"], d["lengths"], sd, run, 2100000+case*2000)
    return dict(case=case, full=full, split=half, repairs=len(repairs))


def load_certificate(paths, before):
    if len(paths) != 1:
        raise ValueError("Requires one current certificate.json")
    path = repo_path(paths[0])
    rec = json.loads(path.read_text(encoding="utf-8"))
    if not (path.parent / "run.log").read_text(encoding="utf-8").rstrip().endswith("FINISHED"):
        raise ValueError("Certificate not FINISHED")
    if not rec.get("passed") or rec.get("fingerprint") != before or rec.get("config") != json.loads(json.dumps(CONFIG)):
        raise ValueError("Failed/stale certificate; rerun changed-code controls")
    return dict(path=relative(path), sha256=sha256(path))


def certify(paths, before):
    if len(paths) != 5:
        raise ValueError("Supply all five completed case.json paths in order 0..4")
    cases, provenance = [], []
    for i, name in enumerate(paths):
        path = repo_path(name)
        rec = json.loads(path.read_text(encoding="utf-8"))
        if rec["fingerprint"] != before or rec["config"] != json.loads(json.dumps(CONFIG)) or rec["case"] != i:
            raise ValueError("Stale/misordered control case")
        log = (path.parent / "run.log").read_text(encoding="utf-8")
        if not log.rstrip().endswith("FINISHED"):
            raise ValueError("Control not FINISHED")
        cases.append(rec)
        provenance.append(dict(path=relative(path), sha256=sha256(path)))
    full_flags = sum(r["full"]["flag"] for r in cases[:4])
    half_flags = sum(r["split"]["stability_flag"] for r in cases[:4])
    passed = full_flags >= 3 and not cases[4]["full"]["flag"]
    split_passed = half_flags >= 2 and not cases[4]["split"]["stability_flag"]
    # Separate coarse half-power gate: do not let a full-book pass certify it.
    return dict(passed=passed, split_passed=split_passed, plant_full_flags=full_flags,
                plant_split_flags=half_flags, case_paths=provenance,
                power_precision="unknown; four plants do not estimate population power accurately")


def float_moments(length, q):
    """Same exact algebra as raw T6 recurrence; floating evaluation only."""
    import numpy as np
    zero = np.zeros(28); zero[0] = 1
    pairs = {}
    for i in range(1, length):
        for j in range(i):
            prev = zero if j == i-1 else pairs[j, i-1]
            row = (-q/28 if i < 6 else -q/29)*prev
            if i >= 6:
                k = i-6
                src = zero if j == k else pairs[j, k] if j < k else pairs[k, j][(-np.arange(28)) % 28]
                row = row+q/29*np.roll(src, 1)
            pairs[j, i] = row
    return pairs


def section_mean(s, q):
    ns = Counter(p for n in s["word_lengths"] for p in range(n))
    weights = float_moments(max(ns)+1, q)
    echo = sum(ns[i]*(1+28*weights[i-6, i][1])/29 for i in ns if i >= 6)
    # All transitions use fallback except local >=6. Raw repairs may fail.
    doublets = (s["length"]-1)*(1-q)/29
    doublets += sum(ns[i]*q/29*(1+28*weights[i-6, i-1][1])/29 for i in ns if i >= 6)
    return echo, doublets


def fit_section(s, doublets):
    # Bounded method of moments, not an MLE. Refit identically in bootstrap.
    lo, hi = 0., 1.
    for _ in range(24):
        q = (lo+hi)/2
        if section_mean(s, q)[1] > doublets:
            lo = q
        else:
            hi = q
    q = (lo+hi)/2
    mean, fitted_d = section_mean(s, q)
    return q, mean, fitted_d


def hits(c, local, lag=6, a=27, b=24):
    return sum(y == (a*c[i-lag]+b) % 29 for i, y in enumerate(c) if local[i] >= lag)


def section_rows(d):
    rows = []
    for s in d["sections"]:
        loc = [p for n in s["word_lengths"] for p in range(n)]
        n = sum(p >= 6 for p in loc)
        if not n:
            continue
        ds = M.section_doublets(s["runes"], [s["length"]])[0]
        q, mu, fitted = fit_section(s, ds)
        h = hits(s["runes"], loc)
        rows.append(dict(section=s["section"], eligible=n, observed=h, doublets=ds,
                         q_raw_moment=q, expected=mu, residual=h-mu,
                         expected_design_q=section_mean(s, .81)[0], fitted_doublets=fitted,
                         q_deficit_clipped=max(0., min(1., 1-29*ds/(s["length"]-1)))))
    return rows


def heterogeneity(rows):
    # Remove fitted common echo multiplier: shape/heterogeneity rather than amplitude.
    scale = sum(r["observed"] for r in rows)/sum(r["expected"] for r in rows)
    stat = sum((r["observed"]-scale*r["expected"])**2/max(scale*r["expected"], 1e-12) for r in rows)
    amplitude = sum((r["observed"]-r["expected"])**2/max(r["expected"], 1e-12) for r in rows)
    return stat, amplitude


def sections(run, d):
    rows = section_rows(d)
    stat, amplitude = heterogeneity(rows)
    null_shape, null_fit = [], []
    for rep in range(199):
        run.check()
        book = []
        for s in d["sections"]:
            r = next((r for r in rows if r["section"] == s["section"]), None)
            q = r["q_raw_moment"] if r else .81
            loc = [p for n in s["word_lengths"] for p in range(n)]
            c, _ = M.collision_plant(loc, [s["length"]], 6, 1,
                                     3100000+rep*20+s["section"], q)
            book.extend(c)
        rr = section_rows(replace_book(d, book))
        a, b = heterogeneity(rr)
        null_shape.append(a); null_fit.append(b)
        if rep % 10 == 0:
            run.log(f"Section bootstrap {rep+1}/199")
    return dict(rows=rows, shape_statistic=stat, amplitude_statistic=amplitude,
                p_shape=(1+sum(x >= stat for x in null_shape))/200,
                p_fit=(1+sum(x >= amplitude for x in null_fit))/200,
                bootstrap_shape=null_shape, bootstrap_fit=null_fit,
                caveat="plug-in parametric bootstrap, refitted q; not exact conditional p; selected T6 family")


def optimism(run, d):
    ds = M.section_doublets(d["c"], d["lengths"])
    rows = []
    for rep in range(B):
        run.check()
        a = M.conditional_null(d["lengths"], ds, 4100000+rep)
        b = M.conditional_null(d["lengths"], ds, 4200000+rep)
        best = M.scan(a, d["local"], run.check)["best"]
        selected_t6 = (best.get("lag") == 6 and best.get("a") == 27 and best.get("b") == 24) or "mix_" in best.get("rule", "")
        if "lag" in best:
            lag, aa, bb = best["lag"], best["a"], best["b"]
        else:
            lag, aa, bb = 6, 27, 24  # T6 component of mixture, NOT total mixture count.
        rows.append(dict(winner=best, lag=lag,
                         selected_count=hits(a, d["local"], lag, aa, bb),
                         independent_count=hits(b, d["local"], lag, aa, bb),
                         T6_selected=selected_t6,
                         fixed_T6_count=hits(a, d["local"]), fixed_T6_independent=hits(b, d["local"])))
    group = [r for r in rows if r["T6_selected"]]
    lag6 = [r for r in rows if r["lag"] == 6]
    def summary(rr, first, second):
        if len(rr) < 20:
            return dict(n=len(rr), optimism="unknown; fewer than 20 matching selections")
        diffs = [r[first]-r[second] for r in rr]
        mean = sum(diffs)/len(diffs)
        se = math.sqrt(sum((x-mean)**2 for x in diffs)/(len(diffs)-1)/len(diffs))
        return dict(n=len(rr), mean_count_optimism=mean, mc_se=se)
    return dict(rows=rows, selected_lag6_map=summary(lag6, "selected_count", "independent_count"),
                selected_fixed_T6=summary(group, "fixed_T6_count", "fixed_T6_independent"),
                observed_count_bias="unknown; pure-null optimism is not an identifiable correction to 80",
                selection_tail_matches=sum(r["winner"]["score"] >= 15.8952686734721 for r in rows))


def mechanisms(d):
    """Predictable opportunity budgets, not fitted mechanism claims."""
    c, local = d["c"], d["local"]
    groups = {}
    for label, mask in (("first_eligible", lambda p: p == 5),
                        ("shared", lambda p: p >= 6),
                        ("all_lag5", lambda p: p >= 5)):
        idx = [i for i, p in enumerate(local) if mask(p)]
        source_s = [i for i in idx if c[i-5] == 15]
        groups[label] = dict(eligible=len(idx), hits=sum(c[i] == c[i-5] for i in idx),
                             S_opportunities=len(source_s), S_hits=sum(c[i] == 15 for i in source_s),
                             max_S_copy_repair_contribution=str(M.DESIGN_Q*len(source_s)/29),
                             note="Gross predictable forced-hit budget; excludes lost natural hits and is not an unconditional fitted mean")
    # One extra branch only: at a repair use I5 when source=S, otherwise T6.
    # This is deliberately NOT fitted or run as an LP2 likelihood test.
    return dict(groups=groups, shared_budget=M.budget_evalue(c, local),
                one_branch_rule="If local>=5 and C[i-5]=S copy S; else use raw T6 or its specified unavailable-tap fallback",
                satisfies_all_counts="unknown; no joint fit or flat-lag control run",
                limitation="S gate steals shared T6 repairs; cannot create an independent budget")


def english_difference_law():
    path = HERE.parent.parent / "ref" / "emerson_essays1.txt"
    text = path.read_text(encoding="utf-8")
    start = text.find("SELF-RELIANCE")
    if start < 0:
        raise ValueError("Missing corpus marker")
    lp = lp_module()
    stream = [r for w in re.findall(r"[A-Za-z]+", text[start:].split("*** END OF")[0])
              for r in lp.word_to_key(w.upper().replace("IO", "IA"))]
    if len(stream) < 10000:
        raise ValueError("Unexpected corpus size")
    counts = Counter((b-a) % 29 for a, b in zip(stream, stream[1:]))
    # Joint bigram add-half smoothing: 29 cells contribute to EACH difference.
    denom = 2*(len(stream)-1)+841
    return [F(2*counts[d]+29, denom) for d in range(29)]


def binomial(n, p):
    return [F(math.comb(n, k))*p**k*(1-p)**(n-k) for k in range(n+1)]


def convolve(a, b):
    out = [F(0)]*(len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i+j] += x*y
    return out


def exact_power(n, m, p0, p1, alpha=F(1, 20)):
    null = binomial(n, p0)
    alt = convolve(binomial(n-m, p0), binomial(m, p1))
    # Randomized boundary is prespecified; also report conservative nonrandom power.
    above = F(0)
    for k in range(n, -1, -1):
        if above+null[k] > alpha:
            gamma = (alpha-above)/null[k]
            conservative = sum(alt[k+1:], F(0))
            return dict(threshold=k, randomization=gamma, size=above+gamma*null[k],
                        nonrandom_size=above,
                        power=conservative+gamma*alt[k], nonrandom_power=conservative)
        above += null[k]
    raise ValueError("Invalid alpha")


def power(run):
    law = english_difference_law()
    order = sorted(range(29), key=lambda d: (-law[d], d))
    results = []
    for k in range(1, 29):
        run.check()
        p0, f = F(k, 29), sum((law[d] for d in order[:k]), F(0))
        # Uniform independent repair geometry reference, NOT exact real-site geometry.
        p1 = (1-M.DESIGN_Q/29)*f + M.DESIGN_Q/29*p0
        ans = exact_power(80, 35, p0, p1)
        results.append(dict(differences=order[:k], p0=p0, p1=p1, **ans))
    best = max(results, key=lambda r: r["power"])
    sensitivity = {str(m): exact_power(80, m, best["p0"], best["p1"]) for m in (20, 25, 30, 35, 40)}
    def encode(x):
        if isinstance(x, F):
            return dict(rational=str(x), decimal=float(x))
        if isinstance(x, dict):
            return {k: encode(v) for k, v in x.items()}
        if isinstance(x, list):
            return [encode(v) for v in x]
        return x
    return encode(dict(law=law, best=best, sensitivity=sensitivity, candidates=results,
                       n=80, true_repairs=35, actual_usable_sites="unknown",
                       real_site_exact_power="unknown; English law at selected repairs, geometry and dependence unspecified",
                       reference="independent sites; exactly 35 uniformly hidden repair labels; uniform geometry; English joint-bigram difference marginal",
                       discriminator_authorized=False))


def action(run, args):
    before = fingerprint()
    units(run)
    run.log(CONFIG)
    if args.mode == "power":
        result, filename = power(run), "power.json"
    elif args.mode == "certify":
        result, filename = certify(args.controls, before), "certificate.json"
    else:
        d = G.data()
        if args.mode == "control":
            result, filename = control_case(run, args, d), "case.json"
        elif args.mode in ("test", "split"):
            provenance = load_certificate(args.controls, before)
            if args.mode == "split":
                cert = json.loads(repo_path(args.controls[0]).read_text(encoding="utf-8"))
                if not cert["split_passed"]:
                    raise ValueError("Half-power gate failed; no heldout negative justified")
                result = split(d["c"], d["local"], d["lengths"], d, run, 2300000)
            else:
                result = mc(d["c"], d["local"], d["lengths"], 1033001, run.check)
            result["controls"] = provenance
            filename = args.mode+".json"
        elif args.mode == "sections":
            result, filename = sections(run, d), "sections.json"
        elif args.mode == "mechanisms":
            result, filename = mechanisms(d), "mechanisms.json"
        else:
            result, filename = optimism(run, d), "optimism.json"
    run.check()
    if fingerprint() != before:
        raise RuntimeError("Inputs/code changed; result invalid")
    result.update(fingerprint=before, config=CONFIG, status="completed", lp2_solved=False)
    run.save(filename, result)
    run.log(f"Saved {filename}; nothing in LP2 is solved.")
    if args.mode == "certify":
        run.log(f"Full controls passed={result['passed']}; half controls passed={result['split_passed']}")
    if args.mode == "power":
        run.log(f"Reference exact power={result['best']['power']}; actual-site power unknown; no discriminator run proposed")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("control", "certify", "test", "split", "sections", "optimism", "mechanisms", "power"))
    ap.add_argument("--case", type=int, choices=range(5), default=0)
    ap.add_argument("--controls", nargs="*", default=[])
    ap.add_argument("--seconds", type=float, default=95)
    args = ap.parse_args()
    if not 0 < args.seconds <= 95:
        ap.error("Budget must be in (0,95]; never extend an incomplete gate")
    raise SystemExit(execute("collision-followup-"+args.mode, lambda run: action(run, args), args.seconds))
