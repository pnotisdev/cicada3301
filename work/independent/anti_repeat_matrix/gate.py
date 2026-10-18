"""HUMAN-RUN ONLY: exhaustive kernel/arc identities, then reference matrix numbers.

No engine launches, builds, seed search, GPU, network or API. Default foreground
budget 110 seconds, never more than 115. Runtime/completion are UNMEASURED until
human-run. A timeout is INCOMPLETE, not an LP2 negative or a power measurement.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import sys

# Imports must not create __pycache__ files in shared helper/kernel folders.
sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from manual_common import execute, lp_module, relative, sha256
import reference as R


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def snapshot():
    paths = [HERE / name for name in ("reference.py", "gate.py", "CATALOGUE.md", "MATRIX.md")]
    paths += [HERE.parent / "manual_common.py", R.PREVIOUS / "collision_model.py",
              HERE.parent.parent / "lp.py", HERE.parent.parent / "ref" / "lp_verified.txt",
              HERE.parent.parent / "kscreen" / "src" / "main.rs",
              HERE.parent.parent / "kscreen" / "export.py"]
    return {relative(path): sha256(path) for path in paths}


def kernel_checks(run):
    checked = 0
    for mid in R.IDS:
        run.check()
        for a in range(R.Q):
            for adv in ((0, 1, 2) if mid in ("M11", "M12") else (0,)):
                kernel = R.joint_kernel(mid, a, adv)
                require(sum(kernel.values()) == 1, f"Normalization {mid}")
                require(all(v >= 0 for v in kernel.values()), f"Negative mass {mid}")
                marginal = R.marginal(kernel)
                expected = (1 - R.QN) / R.Q if mid == "M07" else R.DELTA
                require(marginal[a] == expected, f"Doublet calibration {mid}")
                if mid not in ("M07", "M08"):
                    expected_row = [R.CM.baseline_probability(y, a, R.Q0) for y in range(R.Q)]
                    require(marginal == expected_row, f"K0 identity {mid}")
                checked += 1
            if mid == "M07":
                for b in range(R.Q):
                    if b == a:
                        continue
                    pending = R.joint_kernel(mid, a, pending=b)
                    require(pending == {(b, 1, 1, None): F(1)}, "Pending retry must be exact")
    stationary_normal = R.Q / (R.Q + R.QN)
    require(stationary_normal * (1 - R.QN) / R.Q == R.DELTA, "Null stationary denominator")
    require(R.QN / (R.Q + R.QN) == F(10453, 388410), "Null stationary fraction")
    # Deliberate countercontrol: q0 is NOT the once-redraw calibration.
    wrong_once = (1 - R.Q0) / R.Q + R.Q0 / R.Q ** 2
    require(wrong_once != R.DELTA, "Gate must detect reusing one q for every rule")
    # Retained-key countercontrol: a known next plaintext can give nu(a)=1.
    nu = [F(0)] * R.Q
    nu[0] = F(1)
    retained = R.marginal(R.joint_kernel("M04", 0, nu=nu))[0]
    require(retained == 1 - R.Q0 and retained != R.DELTA, "Hold cannot inherit English uniformity")
    # Native-step and iid-plaintext mask identities, exhaustive finite alphabets.
    for a in range(R.Q):
        for u in range(R.Q - 1):
            hist = Counter((a + 1 + (u + k) % (R.Q - 1)) % R.Q for k in range(R.Q - 1))
            require(hist[a] == 0 and all(hist[y] == 1 for y in range(R.Q) if y != a), "Step class bijection")
        for held_key in range(R.Q):
            require(sum((p + held_key) % R.Q == a for p in range(R.Q)) == 1,
                    "Uniform-new-plaintext mask; not an English assertion")
    for a, p, k in product(range(R.Q), repeat=3):
        feedback = (a + p + k) % R.Q
        require((feedback == a) == ((p + k) % R.Q == 0), "Feedback collision target transform")
        require((feedback - a - k) % R.Q == p, "Feedback positive emission control")
    run.log(f"Kernel identities: {checked} rows; full alphabets, plus stationary-null and retained-key countercontrols.")
    return dict(checked_rows=checked, hold_english_calibration="unknown",
                infinite_retry_tail="summed geometrically, not truncated", passed=True)


def prefix_checks(run):
    """Literal exhaustive 29^3 key prefixes, known plaintext=previous=0.

    Translation of all keys by p-a reduces arbitrary p,a to this canonical case.
    Branch coin probabilities are exact rational weights, not random draws.
    """
    den, repair = R.Q1.denominator, R.Q1.numerator
    total = R.Q ** 3 * den
    mass, avoid, survive, avoid_survive, plaintext = Counter(), Counter(), Counter(), Counter(), Counter()
    models = ("M01", "M03", "M05")
    for k0 in range(R.Q):
        run.check()
        for k1, k2 in product(range(R.Q), repeat=2):
            keys = (k0, k1, k2)
            for mid in models:
                if k0:
                    branches = [(k0, 1, den, False)]
                else:
                    keep_dj = 2 if mid == "M03" else 1
                    used = 1 if mid == "M01" else 2
                    dj = 2 if mid == "M01" else 3
                    branches = [(0, keep_dj, den - repair, False), (keys[used], dj, repair, keys[used] != 0)]
                for y, dj, weight, avoided in branches:
                    mass[mid, y, dj] += weight
                    if avoided:
                        avoid[mid] += weight
                    for mode in ("S", "C"):
                        for d in (0, 1, 2):
                            key = mid, mode, d
                            options = R.decoder_outputs_at_end(y, 0, keys, d, mode, dj)
                            if options:
                                survive[key] += weight
                                if avoided:
                                    avoid_survive[key] += weight
                            if 0 in options:
                                plaintext[key] += weight
    rows = []
    for mid in models:
        expected = R.joint_kernel(mid, 0)
        for (y, dj, dp, latch), probability in expected.items():
            require(F(mass[mid, y, dj], total) == probability, f"Forward enumeration joint kernel {mid}")
        require(F(avoid[mid], total) == R.RHO, f"Net repair hazard {mid}")
        for mode in ("S", "C"):
            for d in (0, 1, 2):
                key = mid, mode, d
                got = F(survive[key], total), F(avoid_survive[key], avoid[mid])
                require(got == R.scalar_fg(mid, mode, decoder_advance=d), f"Phase F/g {key}: {got}")
                require(plaintext[key] <= survive[key], "Symbol support cannot exceed phase support")
                rows.append(dict(model=mid, decoder=mode, preadvance=d, F=str(got[0]), g=str(got[1]),
                                 correct_symbol_and_phase=str(F(plaintext[key], total))))
    require(F(plaintext["M01", "S", 0], total) == 1, "Positive plant: once/S all symbols")
    require(F(plaintext["M03", "C", 0], total) == 1, "Positive plant: coin/C all symbols")
    require(avoid_survive["M01", "C", 0] == 0, "Mismatch sentinel: once/C first avoidance")
    require(plaintext["M03", "S", 1] < survive["M03", "S", 1], "Phase is not plaintext identity")
    run.log(f"Literal forward enumeration: {R.Q ** 3} key prefixes, S/C and all relevant decoder pre-advances.")
    return rows


def compressed_checks(run):
    """Exact sufficient partitions for longer draw prefixes.

    In these canonical phase conditions only whether each attempted key equals
    the colliding value matters. Multiplicity (Q-1)^nonzero sums every raw value.
    The until-loop's unreachable tail beyond the tested reach is an exact category.
    """
    rows = []
    for mid in ("layout-once", "M02"):
        run.check()
        width = 4 if mid == "layout-once" else 7
        q = R.Q1 if mid == "layout-once" else R.Q0
        norm = R.Q ** width * q.denominator
        totals, avoided_surv, all_avoid = Counter(), Counter(), Counter()
        settings = range(-2, 3) if mid == "layout-once" else range(5)
        for bits in product((0, 1), repeat=width):
            multiplicity = (R.Q - 1) ** sum(bits)
            for setting in settings:
                t, d = (max(setting, 0), max(-setting, 0)) if mid == "layout-once" else (0, setting)
                first = bits[t]
                if first:
                    branches = [(first, t + 1, q.denominator, False)]
                else:
                    if mid == "layout-once":
                        y, dj = bits[t + 1], t + 2
                        active = (y, dj, q.numerator, y != 0)
                    else:
                        terminal = next((i for i in range(1, width) if bits[i]), None)
                        # Every completion of the infinite tail eventually differs;
                        # its end is beyond ALL supported decoder reaches here.
                        active = (1, terminal + 1 if terminal is not None else width + 1, q.numerator, True)
                    branches = [(0, t + 1, q.denominator - q.numerator, False), active]
                for y, dj, weight, avoided in branches:
                    weight *= multiplicity
                    if avoided:
                        all_avoid[setting] += weight
                    for mode in ("S", "C"):
                        options = R.decoder_outputs_at_end(y, 0, bits, d, mode, dj)
                        if options:
                            totals[setting, mode] += weight
                            if avoided:
                                avoided_surv[setting, mode] += weight
        for setting in settings:
            for mode in ("S", "C"):
                got = F(totals[setting, mode], norm), F(avoided_surv[setting, mode], all_avoid[setting])
                want = R.once_fg(mode, setting) if mid == "layout-once" else R.scalar_fg("M02", mode, decoder_advance=setting)
                require(got == want, f"Exact compressed partition {mid, setting, mode}: {got} != {want}")
                rows.append(dict(model=mid, offset_or_advance=setting, decoder=mode, F=str(got[0]), g=str(got[1])))
    run.log("Long-prefix checks: exhaustive sufficient equality classes, exact multiplicities and geometric tail.")
    return rows


def stateful_checks(run):
    # Hold: independently enumerate new plaintext and auxiliary off-previous rune.
    q, norm = R.Q0, R.Q * (R.Q - 1) * R.Q0.denominator
    for mode, masked, unequal in product(("S", "C"), (False, True), (False, True)):
        run.check()
        u, counter = int(unequal), Counter()
        for p, r in product(range(R.Q), range(1, R.Q)):
            if p:
                branches = [(p, 1, q.denominator)]
            else:
                branches = [(0, 1, q.denominator - q.numerator), (r, 0, q.numerator)]
            for y, dj, weight in branches:
                if masked:
                    supported = dj == 0
                    next_state = int(y != u)
                else:
                    supported = dj == 1 and (mode == "S" or y != u)
                    next_state = 0
                if supported:
                    counter[next_state] += weight
        matrix, _ = R.transition_and_event("M04", mode, True, masked, 0, 0)
        require(tuple(F(counter[s], norm) for s in (0, 1)) == matrix[int(unequal)], "Hold comparison-state matrix")
    # Null NORMAL row, independently enumerated over candidate/repair outputs.
    q, norm = R.QN, R.Q * (R.Q - 1) * R.QN.denominator
    for mode, masked in product(("S", "C"), (False, True)):
        counter = Counter()
        for candidate, r in product(range(R.Q), range(1, R.Q)):
            branches = ([(candidate, 1, q.denominator)] if candidate else
                        [(0, 1, q.denominator - q.numerator), (r, 0, q.numerator)])
            for y, dj, weight in branches:
                supported = (dj == 0) if masked else bool(R.decoder_outputs_at_end(
                    y, 0, (candidate, 0, 0), 0, mode, dj))
                if supported:
                    counter[int(dj == 0)] += weight
        matrix, _ = R.transition_and_event("M07", mode, True, masked, 0, 0)
        require(tuple(F(counter[s], norm) for s in (0, 1)) == matrix[0], "Null NORMAL matrix")
    # Null: enumerate every off-previous padding symbol and its exact retry.
    for a in range(R.Q):
        for r in range(R.Q):
            if r == a:
                continue
            retry = R.joint_kernel("M07", r, pending=a)
            require(retry == {(a, 1, 1, None): F(1)}, "Every visible null must create a,R,a")
            require(bool(R.decoder_outputs_at_end(a, a, (0, 0, 0), 0, "S", 1)), "N+S must permit retry")
            require(not R.decoder_outputs_at_end(a, a, (0, 0, 0), 0, "C", 1), "N+C incorrectly spends retry coin")
    for mode in ("S", "C"):
        unmasked, event0 = R.transition_and_event("M07", mode, True, False, 0, 0)
        masked, event1 = R.transition_and_event("M07", mode, True, True, 0, 0)
        require(masked == ((F(0), R.RNULL), (F(0), F(0))), "Null masked-state matrix")
        require(unmasked[1] == ((F(1) if mode == "S" else F(0)), F(0)), "Null pending-state matrix")
        require(event0 == (0, 0) and event1 == (0, 1), "Null event initialization")
    run.log("Stateful controls: retained-key comparison states and mandatory visible-null retry verified.")


def signal_controls(run):
    # Known affine key: wrong physical index can retain ALL IoC.
    plain = [0, 0, 0, 1, 1, 2, 3, 5, 8, 13]
    key = [i % R.Q for i in range(len(plain) + 1)]
    cipher = [(p + key[i]) % R.Q for i, p in enumerate(plain)]
    wrong_phase = [(c - key[i + 1]) % R.Q for i, c in enumerate(cipher)]
    require(Counter(wrong_phase).most_common()[0][1] == Counter(plain).most_common()[0][1], "Affine key counterexample")
    require(sorted(Counter(wrong_phase).values()) == sorted(Counter(plain).values()), "IoC relabelling invariance")
    # Unselected independent wrong-key control: decoded residues exactly uniform.
    null = Counter((actual - decoy) % R.Q for actual, decoy in product(range(R.Q), repeat=2))
    require(all(null[y] == R.Q for y in range(R.Q)), "Independent wrong-key null")
    # Exact contrast attenuation of the uniform-off-diagonal error channel.
    pi = [F(i + 1, R.Q * (R.Q + 1) // 2) for i in range(R.Q)]
    observed = [(1 - R.RHO) * p + R.RHO * (1 - p) / (R.Q - 1) for p in pi]
    f = 1 - R.Q * R.RHO / (R.Q - 1)
    require(R.Q * sum(p * p for p in observed) - 1 == f * f * (R.Q * sum(p * p for p in pi) - 1), "Local-noise IoC attenuation")
    shifted = [(1 - R.RHO) * pi[i] + R.RHO * pi[(i - 1) % R.Q] for i in range(R.Q)]
    source_contrast = R.Q * sum(p * p for p in pi) - 1
    shifted_contrast = R.Q * sum(p * p for p in shifted) - 1
    require((1 - 2 * R.RHO) ** 2 * source_contrast <= shifted_contrast <= source_contrast,
            "Plaintext-adjustment IoC bounds")
    run.log("Signal controls: affine-phase counterexample, independent wrong-key null, exact local-noise attenuation/bounds.")


def layouts(run):
    lp, windows = lp_module(), []
    segments = lp.load_segments()
    for section in range(7, 16):
        toks = segments[section]
        runes = lp.runes_of(toks)
        if len(runes) < 300:
            continue
        n = 300  # Declared screen-length design; not a measured runtime.
        word, initial, final = [0] * n, [False] * n, [False] * n
        for _, a, b in lp.word_spans(toks, runes):
            if a < n:
                initial[a] = True
            if 0 < a < n:
                word[a] = 1
            if b - 1 < n:
                final[b - 1] = True
        pos, breaks = 0, Counter()
        for token in toks:
            if isinstance(token, int):
                pos += 1
            elif token in ("\n", "%") and 0 < pos < n:
                breaks[pos] += 1
        # export.py break_positions preserves duplicates: line AND page can both
        # occur at one rune position. Do NOT turn the B line into a set.
        wb = [word[i] + breaks[i] for i in range(n)]
        windows.append(dict(section=section, n=n, word=word, initial=initial, final=final, word_break=wb))
    run.log(f"Read-only fixed layouts: {len(windows)} windows. These are not plaintext word-boundary assumptions.")
    return windows


def theoretical_numbers():
    result = dict(parameters=R.parameters(), units="Native bigram scores are rounded/clipped 10*log-odds, NOT nats",
                  provenance="Derived scenario numbers; not measured power",
                  sources=dict(calibration="results/analysis/cicadanotebook_checks_2026-10-17.txt:9,36",
                               ioc="STATUS.md:19", bigram_scaling="work/phpmt/bg.py:52-64",
                               correct_bigram="results/analysis/true_key_score.txt:1,13"), bare_interior=[])
    for mid in R.IDS:
        if mid == "M10":
            continue
        for mode in ("S", "C"):
            f, g = R.scalar_fg(mid, mode)
            limit = None if f == 1 else str(g * f / (1 - f))
            result["bare_interior"].append(dict(model=mid, decoder=mode, F=str(f), g=str(g),
                                                 unbounded_post_run=limit, remaining_299=float(g * R.g_run(1 - f, 299)),
                                                 note="M11/M12: interior only, real layout changes this" if mid in ("M11", "M12") else None))
    f = 1 - R.Q * R.RHO / (R.Q - 1)
    result["local_noise_ioc_illustration"] = [float(1 + f * f * (i - 1)) for i in (F(8, 5), F(103, 50))]
    result["fixed_adjustment_ioc_lower_bounds"] = [float(1 + (1 - 2 * R.RHO) ** 2 * (i - 1))
                                                    for i in (F(8, 5), F(103, 50))]
    result["wait_to_net_repair"] = str(1 / R.RHO)
    result["checks_300_initial_collisions"] = str(F(300, R.Q))
    result["checks_300_net_repairs"] = str(300 * R.RHO)
    return result


def action(run, args):
    before = snapshot()
    check = kernel_checks(run)
    rows = prefix_checks(run) + compressed_checks(run)
    stateful_checks(run)
    signal_controls(run)
    run.check()
    run.save("kernel_checks.json", dict(**check, coefficient_checks=rows, fingerprint=before,
                                       power="unknown: no English engine/beam/selection test was run"))
    run.save("theoretical_numbers.json", theoretical_numbers())
    summaries = []
    if not args.kernels_only:
        for window in layouts(run):
            run.check()
            matrix = R.window_matrix(window)
            run.save(f"reset_matrix_seg{window['section']}.json", dict(layout=window, matrix=matrix,
                         meaning="Reset-oracle strict phase prefix only; actual beam run and detection power UNKNOWN"))
            for row in matrix:
                summaries.append(dict(section=window["section"], **{k: v for k, v in row.items()
                                      if k != "conditional_lengths_after_positions"}))
            run.log(f"Reference reset matrix written for section 0.{window['section']}; not a beam-power result.")
        run.save("matrix_summary.json", dict(reset_before_event=True, layout_exogenous=True, measured=False, rows=summaries,
                  warning="Averaging resets before every hypothetical first event. Earlier errors, offset gauge, pruning and resynchronization are not modelled."))
    run.check()
    require(snapshot() == before, "Inputs/code changed during gate; incomplete, rerun on a stable snapshot")
    run.save("gate.json", dict(passed=True, fingerprint=before, parameters=R.parameters(),
                              full_layout_matrix=not args.kernels_only, measured_lp2_power=False,
                              scope="Local exhaustive probability/arc identities and analytical reference diagnostics only"))
    run.log("KERNEL IDENTITY GATE PASSED. Actual English crossed power remains UNKNOWN. Nothing in LP2 is solved.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernels-only", action="store_true", help="omit the optional real-layout analytical matrix")
    parser.add_argument("--seconds", type=float, default=110, help="foreground checked budget, must be <=115")
    args = parser.parse_args()
    if not 0 < args.seconds <= 115:
        parser.error("Keep this gate under two minutes: 0 < --seconds <=115; no automatic long rerun")
    raise SystemExit(execute("anti-repeat-matrix", lambda run: action(run, args), args.seconds))
