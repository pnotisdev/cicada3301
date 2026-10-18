"""Frozen lower-dispersion test of T6 echo HIT sites, not hidden repair labels."""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import random
import sys
import unittest

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "collision_followup"))
import analysis as P
from manual_common import execute, relative, repo_path, sha256
sys.modules.setdefault("dispersion_gate", sys.modules[__name__])

BASELINE = "results/independent/desktop/20261018T162753Z-collision-fixed-section-observed-a7fb33/section-observed.json"
B, TOTAL = 999, 80
NAMES = ("section", "eligible100", "gaps")
CONFIG = dict(B=B, total_echo_hits=TOTAL, relation="within-word T6 raw, no I5 or other maps",
              scales=list(NAMES), bin_size=100, bin_origin="first eligible pair of each section; include short terminal bin",
              gap="internal inter-hit gaps in eligible-pair order, exposure-adjusted; no cross-section gaps",
              direction="lower tail only", alpha=.05, multiplicity="Bonferroni over exactly 3 scales",
              null="independent inhomogeneous Bernoulli site law, conditioned on exactly 80 hits",
              rates="raw-T6 pair marginal by local word position; prior own-doublet q_s fixed, not refitted to sites",
              controls="4 matched Bernoulli negatives, 4 random-phase systematic evenly-spaced positives",
              caveat="motivated by previous same-data smoothness; not independent replication or a forward-cipher null")


def fingerprint():
    out = P.fingerprint()
    for path in [HERE / x for x in ("gate.py", "test_dispersion.py", "PROTOCOL.md")] + [repo_path(BASELINE)]:
        out[relative(path)] = sha256(path)
    return out


def units(run):
    P.units(run)
    import test_dispersion
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(test_dispersion))
    for line in stream.getvalue().splitlines():
        run.log(line)
    if not result.wasSuccessful() or result.skipped:
        raise RuntimeError("Dispersion unit controls failed; no interpretation")
    run.check()


class ConditionalBernoulli:
    """Exact finite-population conditioning via Poisson-binomial dynamic programming."""
    def __init__(self, probabilities, count):
        self.p = np.asarray(probabilities, dtype=float)
        self.n, self.count = len(self.p), count
        if not 0 < count < self.n or not np.all((self.p > 0) & (self.p < 1)):
            raise ValueError("Require interior probabilities and 0<count<n")
        d = np.zeros((self.n+1, count+1)); d[self.n, 0] = 1.
        for i in range(self.n-1, -1, -1):
            d[i] = (1-self.p[i])*d[i+1]
            d[i, 1:] += self.p[i]*d[i+1, :-1]
        self.suffix = d
        z = d[0, count]
        if not z > 0:
            raise ValueError("Zero/underflow conditioning probability")
        self.total_probability = float(z)
        prefix = np.zeros(count+1); prefix[0] = 1.
        marginal = []
        for i, p in enumerate(self.p):
            marginal.append(p*np.dot(prefix[:count], d[i+1, count-1::-1])/z)
            nxt = (1-p)*prefix
            nxt[1:] += p*prefix[:-1]
            prefix = nxt
        self.marginal = np.asarray(marginal)
        if not np.all((self.marginal > 0) & (self.marginal < 1)) or abs(self.marginal.sum()-count) > 1e-8:
            raise ValueError("Conditional marginal normalization failed")

    def draw(self, seed):
        rng, remaining = random.Random(seed), self.count
        mask = np.zeros(self.n, dtype=bool)
        for i, p in enumerate(self.p):
            if not remaining:
                break
            if remaining == self.n-i:
                mask[i:] = True
                remaining = 0
                break
            chance = p*self.suffix[i+1, remaining-1]/self.suffix[i, remaining]
            if not -1e-12 <= chance <= 1+1e-12:
                raise ValueError("Invalid conditional draw probability")
            if rng.random() < chance:
                mask[i] = True
                remaining -= 1
        if remaining or int(mask.sum()) != self.count:
            raise RuntimeError("Conditional draw did not conserve count")
        return mask

    def evenly_spaced(self, seed):
        # Systematic weighted sampling: fixed-count hit sites, no ciphertext edits.
        phase = random.Random(seed).random()
        cdf = np.cumsum(self.marginal)/self.count
        cdf[-1] = 1.
        idx = np.searchsorted(cdf, (np.arange(self.count)+phase)/self.count, side="right")
        if len(set(map(int, idx))) != self.count:
            raise ValueError("Even grid would duplicate a site")
        mask = np.zeros(self.n, dtype=bool); mask[idx] = True
        return mask


class Dispersion:
    def __init__(self, sampler, section_ids):
        self.sampler = sampler
        self.sections = np.asarray(section_ids, dtype=int)
        if len(self.sections) != sampler.n or np.any(np.diff(self.sections) < 0):
            raise ValueError("Sites must be ordered contiguously by section")
        self.section_values = sorted(set(map(int, self.sections)))
        self.groups = [np.flatnonzero(self.sections == s) for s in self.section_values]
        self.bins = [g[j:j+100] for g in self.groups for j in range(0, len(g), 100)]
        self.section_means = np.asarray([sampler.marginal[g].sum() for g in self.groups])
        self.bin_means = np.asarray([sampler.marginal[g].sum() for g in self.bins])
        self.coordinates = [np.cumsum(sampler.marginal[g])-.5*sampler.marginal[g] for g in self.groups]

    def statistics(self, mask):
        mask = np.asarray(mask, dtype=bool)
        if len(mask) != self.sampler.n or int(mask.sum()) != self.sampler.count:
            raise ValueError("Wrong site-mask length or hit count")
        sect = np.asarray([mask[g].sum() for g in self.groups])
        bins = np.asarray([mask[g].sum() for g in self.bins])
        section = float(np.sum((sect-self.section_means)**2/self.section_means))
        hundred = float(np.sum((bins-self.bin_means)**2/self.bin_means))
        square, intervals = 0., 0
        for g, coordinates in zip(self.groups, self.coordinates):
            at = np.flatnonzero(mask[g])
            if len(at) >= 3:
                gaps = np.diff(coordinates[at])
                square += float(np.sum((gaps/gaps.mean()-1)**2))
                intervals += len(gaps)
        gap_score = square/intervals if intervals else 0.
        return [section, hundred, gap_score]

    def profile(self, mask):
        sections = [dict(section=s, eligible=len(g), observed=int(mask[g].sum()), expected=float(mu))
                    for s, g, mu in zip(self.section_values, self.groups, self.section_means)]
        bins = []
        k = 0
        for section, group in zip(self.section_values, self.groups):
            for start in range(0, len(group), 100):
                g = self.bins[k]
                bins.append(dict(section=section, eligible_start_zero_based=start, eligible=len(g),
                                 observed=int(mask[g].sum()), expected=float(self.bin_means[k])))
                k += 1
        return dict(sections=sections, bins=bins)


def layout(d):
    baseline = json.loads(repo_path(BASELINE).read_text(encoding="utf-8"))
    if not (repo_path(BASELINE).parent / "run.log").read_text(encoding="utf-8").rstrip().endswith("FINISHED"):
        raise ValueError("Prior rate baseline not FINISHED")
    probabilities, ids, site_info = [], [], []
    for s in d["sections"]:
        sid = s["section"]
        rate = next((r for r in baseline["rows"] if r["section"] == sid), None)
        if rate is None:
            if any(n > 6 for n in s["word_lengths"]):
                raise ValueError("Missing eligible-section q")
            continue
        q = rate["q_raw_moment"]
        moments = P.float_moments(max(s["word_lengths"]), q)
        start, rank = 0, 0
        for length in s["word_lengths"]:
            for pos in range(6, length):
                probabilities.append((1+28*moments[pos-6, pos][1])/29)
                ids.append(sid)
                site_info.append(dict(section=sid, target_index=start+pos, eligible_rank=rank))
                rank += 1
            start += length
    if len(probabilities) != 1290:
        raise ValueError("Changed eligible layout")
    sampler = ConditionalBernoulli(probabilities, TOTAL)
    return Dispersion(sampler, ids), site_info


def calibration(model, seed, run):
    rows = []
    for rep in range(B):
        run.check()
        rows.append(model.statistics(model.sampler.draw(seed+rep)))
    return np.asarray(rows)


def assess(statistics, reference):
    reference = np.asarray(reference)
    k = (reference <= np.asarray(statistics)).sum(axis=0)
    p = (1+k)/(len(reference)+1)
    adjusted = np.minimum(1., 3*p)
    return dict(statistics=dict(zip(NAMES, map(float, statistics))),
                lower_exceedances=dict(zip(NAMES, map(int, k))),
                p_lower=dict(zip(NAMES, map(float, p))),
                p_bonferroni=dict(zip(NAMES, map(float, adjusted))),
                p_omnibus=float(min(1., 3*min(p))), flag=bool(min(adjusted) <= .05))


def controls(model, run):
    ref = calibration(model, 8000000, run)
    records = []
    for kind, seedbase in (("Bernoulli", 8100000), ("evenly_spaced", 8200000)):
        for case in range(4):
            mask = model.sampler.draw(seedbase+case) if kind == "Bernoulli" else model.sampler.evenly_spaced(seedbase+case)
            answer = assess(model.statistics(mask), ref)
            records.append(dict(kind=kind, case=case, seed=seedbase+case,
                                selected_indices=np.flatnonzero(mask).tolist(), **answer))
            run.log(f"{kind} {case}: {answer}")
    neg = sum(r["flag"] for r in records if r["kind"] == "Bernoulli")
    pos = sum(r["flag"] for r in records if r["kind"] == "evenly_spaced")
    return dict(passed=neg == 0 and pos >= 3, negatives_flagged=neg, positives_flagged=pos,
                records=records, null_statistics=ref.tolist(), calibration_seed=8000000,
                power="strong fully regular 80-hit plants only; partial-regularity and forward-cipher power unknown")


def action(run, args):
    before = fingerprint()
    units(run)
    run.log(CONFIG)
    d = P.G.data()
    model, site_info = layout(d)
    if args.mode == "controls":
        result = controls(model, run)
        run.log(f"Controls passed={result['passed']}")
    else:
        path = repo_path(args.controls)
        cert = json.loads(path.read_text(encoding="utf-8"))
        if not cert.get("passed") or cert.get("fingerprint") != before or cert.get("config") != json.loads(json.dumps(CONFIG)):
            raise ValueError("Missing, failed or stale dispersion controls")
        if not (path.parent / "run.log").read_text(encoding="utf-8").rstrip().endswith("FINISHED"):
            raise ValueError("Controls not FINISHED")
        sections = {s["section"]: s["runes"] for s in d["sections"]}
        mask = np.asarray([sections[r["section"]][r["target_index"]] ==
                           P.M.transform(sections[r["section"]][r["target_index"]-6], 1) for r in site_info])
        if int(mask.sum()) != TOTAL:
            raise ValueError("Observed total differs from frozen 80; do not silently recondition")
        ref = calibration(model, 8400000, run)
        result = assess(model.statistics(mask), ref)
        result.update(null_statistics=ref.tolist(), calibration_seed=8400000,
                      controls=dict(path=relative(path), sha256=sha256(path)),
                      observed_sites=[r for r, hit in zip(site_info, mask) if hit],
                      profile=model.profile(mask),
                      interpretation="conditional Bernoulli site-process dispersion only; historically selected hypothesis, not replication or rejection of a forward cipher")
        run.log({k: v for k, v in result.items() if k in ("statistics", "p_lower", "p_bonferroni", "p_omnibus", "flag")})
    run.check()
    if fingerprint() != before:
        raise RuntimeError("Inputs/code/protocol changed during invocation")
    result.update(fingerprint=before, config=CONFIG, kind=args.mode, eligible=model.sampler.n,
                  conditioned_hits=TOTAL, conditional_total_probability=model.sampler.total_probability,
                  conditional_marginal_sum=float(model.sampler.marginal.sum()), lp2_solved=False)
    run.save(args.mode+".json", result)
    run.log(f"Saved {args.mode}.json; nothing in LP2 solved")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("controls", "test"))
    ap.add_argument("--controls")
    ap.add_argument("--seconds", type=float, default=95)
    args = ap.parse_args()
    if not 0 < args.seconds <= 95:
        ap.error("Cooperative foreground cap must be <=95 seconds")
    raise SystemExit(execute("echo-dispersion-"+args.mode, lambda run: action(run, args), args.seconds))
