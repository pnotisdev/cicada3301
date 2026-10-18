# Fixed-rule halves and blocked section diagnostic — 2026-10-18

**Nothing in LP2 is solved.** User authorized fixed T6/I5 halves with no selection,
and a smaller-block redo of the timed-out section diagnostic. New protocol:
`work/independent/collision_fixed_halves/PROTOCOL.md`. The source, tests, protocol,
seeds and decision rules were unchanged during all 17 invocations. Every invocation
passed 21 upstream + 6 new tests (27 total, zero skips) and ended FINISHED.
Each ran once, sequentially, with a 95 s cooperative cap. No failures, retries,
background work, GPU, new q fitting for halves or spend/hold discriminator.

These are rules frozen BEFORE THESE RUNS, **not before their historical discovery
on LP2**. They test retrospective fixed-hypothesis consistency under a specified
conditional Markov null; they are NOT independent replication or a correction for
all historical selection. The old selected-rule split's failed controls and
original section timeout remain recorded; neither is overwritten.

## 1. Frozen fixed-rule halves, B=999

A = sections 0.7, 0.9, 0.12, 0.14.
B = sections 0.8, 0.11, 0.13, 0.15.
Raw spend T6 and raw spend I5 only, q=.81, no guard, mixture, search or tuning.
The null conditions on each half's section-specific observed doublet counts and
retains its actual word layout. The two rules share null books but are never
maximized. Code: `work/independent/collision_fixed_halves/gate.py:48-81`.

Source: `results/independent/desktop/20261018T162720Z-collision-fixed-halves-cae869/halves.json`.

| Rule | Half | Eligible targets | Score, nats | Exceedances / 999 | p_MC | Null-score median |
|---|---|---:|---:|---:|---:|---:|
| T6 raw | A | 517 | +3.198569 | 3 | .004 | -4.035425 |
| T6 raw | B | 773 | +8.803375 | 0 | .001 floor | -5.972760 |
| I5 raw | A | 844 | +3.394918 | 2 | .003 | -6.663120 |
| I5 raw | B | 1261 | -.224223 | 15 | .016 | -9.683758 |

Raw scores/p-values are at `halves.json:5-6,1021-1022,2039-2040,3055-3056`.
The sums of half scores reproduce the old whole-book raw scores: T6 +12.001944,
I5 +3.170695. This is a consistency observation, not another test.

### Frozen decision

For each rule, both-half conjunction p=max(p_A,p_B), require BOTH scores >0.
Bonferroni over two rule claims: threshold .025 per conjunction, adjusted
p=min(1,2*max-p). No independence assumption is needed for this construction;
no four independent-discovery claims are made.

- **T6 meets the criterion:** p_both=.004, adjusted p=.008, both scores positive.
- **I5 does not meet the criterion:** p_both=.016, adjusted p=.032, but its B score
  is negative. The adjusted tail p is small; the separate required score sign fails.
  This does NOT mean lag-5 equality has no signal. A negative log LR can still be
  in the upper tail of its conditional-null distribution (here median -9.684).
  The full-strength q=.81 I5 alternative narrowly loses to baseline in B, while
  being less poor than almost all null-generated books. Do not tune q afterward
  and call the retuned result prespecified.

Claims and flags: `halves.json:4072-4085`. Both are eligible for the coarse
changed-code control check below. Meeting T6's fixed criterion is retrospective
consistency, not untouched replication, collision causality or decryption.

## 2. Changed-code controls, no selection

Retained forward plant seeds 730001..730004; matched null control 980001.
Calibration seeds were fixed separately in the new protocol. Each case runs the
same four fixed half statistics; no planted rule is supplied to a selector.

| Case | Matching mechanism | A score | A p_MC | B score | B p_MC | Matching rule positive in both at .025? |
|---|---|---:|---:|---:|---:|---|
| 0 | I5 | +.902362 | .016 | +11.310826 | .001 | yes |
| 1 | I5 | +3.783442 | .003 | +12.150086 | .001 | yes |
| 2 | T6 | +3.791896 | .003 | +11.085951 | .001 | yes |
| 3 | T6 | +.112686 | .063 | +6.367854 | .001 | no |
| 4 | no-echo null, T6 scored | -2.198408 | .237 | -7.011647 | .595 | no |
| 4 | no-echo null, I5 scored | -6.155347 | .464 | -9.598204 | .458 | no |

All cross-mechanism scores also remain in each control artifact; nothing was
suppressed in the raw output. I5: 2/2 recoveries in each half and 2/2 both-half
plants. T6: 1/2 in A, 2/2 in B and 1/2 both-half plants. No null flag.
Both prespecified coarse per-rule gates pass (>=1/2 plants in EACH half and
no null flag). Two plants per rule cannot establish a precise population power.
This criterion was frozen for the NEW fixed-rule method, not retroactively used
to declare the old selection-method controls passing.

Certificate source:
`results/independent/desktop/20261018T162712Z-collision-fixed-certify-754ea4/certify.json:2-20`.

## 3. Own-doublet-rate T6 section predictions

Source: observed artifact below, lines 2-101; same rows retained in the final
merged artifact. Each q_s is a bounded moment fit to its own adjacent doublets,
not its echo hits. The raw model corrects for repairs that emit the previous rune.
Unconditional mean equations and parameters are unchanged from the earlier package;
only execution is blocked. Own-rate means use actual word-prefix counts and
eligible pairs, not just a common repair rate times all-book length.

| Section | Eligible | Adjacent doublets | Fitted raw q_s | T6 expected | Observed | O-E |
|---|---:|---:|---:|---:|---:|---:|
| 0.7 | 79 | 4 | .843776 | 4.944451 | 6 | +1.055549 |
| 0.8 | 106 | 6 | .850581 | 6.658524 | 6 | -.658524 |
| 0.9 | 184 | 9 | .852039 | 11.567294 | 10 | -1.567294 |
| 0.11 | 178 | 10 | .849521 | 11.174891 | 13 | +1.825109 |
| 0.12 | 100 | 11 | .689567 | 5.744783 | 5 | -.744783 |
| 0.13 | 152 | 13 | .755031 | 9.063875 | 11 | +1.936125 |
| 0.14 | 154 | 12 | .783445 | 9.328963 | 9 | -.328963 |
| 0.15 | 337 | 21 | .819123 | 20.815578 | 20 | -.815578 |
| Total | 1290 | 86 | section-specific | **79.298359** | **80** | **+.701641** |

Observed source:
`results/independent/desktop/20261018T162753Z-collision-fixed-section-observed-a7fb33/section-observed.json`.
The caption section 0.10 has no lag-6 pair and no contributing doublet, so it is
omitted from this table. The artifact separately retains common design-q means
(total 79.287272 from the previous rational tables), clipped deficit estimates
and fitted doublet means. The large difference between high- and low-q sections
is preserved, not averaged away.

## 4. Completed blocked bootstrap, 199/199

All eight fixed blocks finished in 20.6-33.6 s each. No partial artifacts from the
old timed-out monolithic run were reused. IDs 0..198 occur exactly once, with
original seeds 3100000+20*rep+section. Each simulated section is forward generated
at baseline q_s and refitted, as originally prescribed. The merge checks all
input hashes, FINISHED logs, same baseline and exact block coverage.

- Shape statistic (common echo multiplier removed): **1.3365592865**.
  197/199 simulated values >= observed: **p_upper=.990**.
- Overall discrepancy statistic: **1.3545935182**.
  198/199 simulated values >= observed: **p_upper=.995**.
- Simulated shape statistic: minimum 1.037695, median 6.252352.
- Simulated overall-fit statistic: minimum 1.342814, median 6.975379.

Source:
`results/independent/desktop/20261018T163227Z-collision-fixed-section-merge-120ada/section-merge.json:100-101,1099-1100`.

**Interpretation:** no large-discrepancy flag under these upper-tail diagnostics.
The observed profile is unusually smooth compared with the forward books; a very
large upper-tail p is NOT affirmative evidence for a true model. No lower-tail
or two-sided claim was prespecified, and none is promoted as a new discovery.
This remains a refitted plug-in parametric bootstrap for a selected family, with
only 199 replicates and unknown heterogeneity-sized power. It does not establish
homogeneity, exclude alternative mechanisms or validate the whole cipher model.
No post-selection sign-test probability is attached to the section excesses.

## 5. Invocation manifest

All folder names below are under `results/independent/desktop/`. Each has the
original `run.log` and the indicated JSON. Every invocation ended FINISHED.

| Mode | Folder | Seconds | Artifact |
|---|---|---:|---|
| control 0 | `20261018T162433Z-collision-fixed-control-08c9a1` | 27.4 | `control.json` |
| control 1 | `20261018T162504Z-collision-fixed-control-4c7b0b` | 29.1 | `control.json` |
| control 2 | `20261018T162537Z-collision-fixed-control-f886b1` | 27.2 | `control.json` |
| control 3 | `20261018T162609Z-collision-fixed-control-40d76f` | 27.3 | `control.json` |
| control 4 | `20261018T162640Z-collision-fixed-control-02ee99` | 26.8 | `control.json` |
| certify | `20261018T162712Z-collision-fixed-certify-754ea4` | 3.0 | `certify.json` |
| halves | `20261018T162720Z-collision-fixed-halves-cae869` | 27.2 | `halves.json` |
| section observed | `20261018T162753Z-collision-fixed-section-observed-a7fb33` | 3.5 | `section-observed.json` |
| block 0, reps 0-24 | `20261018T162809Z-collision-fixed-section-block-fb63ca` | 20.6 | `section-block.json` |
| block 1, reps 25-49 | `20261018T162835Z-collision-fixed-section-block-cc7460` | 33.6 | `section-block.json` |
| block 2, reps 50-74 | `20261018T162914Z-collision-fixed-section-block-421958` | 31.7 | `section-block.json` |
| block 3, reps 75-99 | `20261018T162950Z-collision-fixed-section-block-025430` | 26.5 | `section-block.json` |
| block 4, reps 100-124 | `20261018T163021Z-collision-fixed-section-block-a3d52f` | 28.6 | `section-block.json` |
| block 5, reps 125-149 | `20261018T163054Z-collision-fixed-section-block-d1ccba` | 23.4 | `section-block.json` |
| block 6, reps 150-174 | `20261018T163122Z-collision-fixed-section-block-6836fe` | 21.6 | `section-block.json` |
| block 7, reps 175-198 | `20261018T163147Z-collision-fixed-section-block-9dcb86` | 31.7 | `section-block.json` |
| section merge | `20261018T163227Z-collision-fixed-section-merge-120ada` | 4.6 | `section-merge.json` |

No new engine, key/plaintext recovery, winner's-curse correction to the observed
80, or spend/hold discriminator was run. The earlier full-selection optimism
estimate cannot be subtracted from these counts; fixed-T6 true inflation remains
unknown. No claim about LP2 being solved follows from any of these results.
