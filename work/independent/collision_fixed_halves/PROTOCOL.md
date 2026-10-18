# Fixed-rule halves and blocked section diagnostic — frozen before new execution

Nothing in LP2 is solved. This is a new package; no previous source, tests,
protocol, certificate or artifact is changed. The user asked for fixed T6/I5
halves without selection, and a smaller-block redo of the timed-out section check.
The previous failure log remains evidence; it is not a completed section result.

## Frozen rules and split

- Half A: sections 0.7, 0.9, 0.12, 0.14.
- Half B: sections 0.8, 0.11, 0.13, 0.15.
- Section 0.10 has no lag-6 pair and is omitted from halves, as before.
- Test **raw spend T6**: C[i] repair = 24-2*C[i-6] mod 29, q=.81.
- Test **raw spend I5**: C[i] repair = C[i-5], q=.81.
- No guarded alternatives, mixtures, q estimation for halves, affine search,
  winning-rule selection, preferred half, reverse split, or other tuning.
- The conditional likelihood ratios and masks are the existing fixed scorer
  `../collision_followup/analysis.py:68-91`. No `scan` call is used by these tests.
  A unit test forbids it with a mock that raises if selection is attempted.

Each half uses its own actual section layout and adjacent doublet count per
section, excluding section seams. Null books preserve those counts exactly,
choose repeat positions uniformly and choose each nonrepeat rune uniformly
among 28 alternatives. The first rune per section is uniform. This is the same
conditional Markov null as before, NOT an English or unigram-preserving null
(`../collision_substitution/collision_model.py:262-283`).

Both fixed rules are evaluated on each of 999 null books per half; their scores
are never maximized. Observed p_MC=(1+#null >= observed)/1000. The two rules may
share null books; each marginal test remains calibrated. Raw scores/p-values
for all four tests are returned, without choosing a subset to report.

### Decision rule and multiplicity, fixed before looking

Two co-primary claims: **T6 positive in both halves**, **I5 positive in both halves**.
For a given rule the conjunction p-value is max(p_A,p_B), an intersection-union
test (the null is that at least one half is null). Require both scores >0.
Bonferroni across TWO rule claims: compare each max-p to .025, equivalently
report p_adjusted=min(1,2*max-p) <=.05. This does not require independence across
halves or rules. It is NOT a claim that each of the four individual tests can
be called significant at .05; individual .025 flags are control diagnostics.

This is conditional-model inference for rules now held fixed. **The rules were
previously discovered on all of LP2. Neither these p-values nor freezing now
creates untouched replication or accounts for the historical family discovery.**
Do not multiply section signs or treat their positive excesses as independent
post-selection confirmations.

## Changed-code controls, before LP2 score calculation

Five separate invocations retain the previous forward plant seeds 730001..730004:
0/1 I5 plants, 2/3 T6 plants. Case 4 is the same-layout no-echo conditional null,
seed 980001. Each invocation runs exactly the same four fixed half statistics,
not the old selection pipeline. Null calibration seeds are 5100000+10000*case
for A and +1000 for B, each with rep=0..998. No repeated or alternative seeds.
LP2 calibration uses seed 5300000 for A and 5301000 for B.

For EACH rule separately, report recoveries out of its two matching plants in
each half at p<=.025 and score>0, plus the number of plants positive in both
halves. A deliberately coarse power gate requires >=1/2 recoveries in EACH
half and no fixed-rule null flag in either half. This is a changed-code wiring /
small-sample sensitivity check, NOT a precise population power estimate.

The certificate records pass/fail per rule. The authorized fixed LP2 diagnostic
still returns all four prespecified scores/p-values if this coarse gate fails,
BUT sets inference_eligible=false and withholds controlled_flag for that rule.
A nonflag with a failed power gate is not an LP2 negative. No thresholds, rule
family or seeds will be changed to obtain passing controls. Missing/incomplete
or stale controls prevent even this completed-certificate diagnostic.

All prior local tests run first, plus fixed-rule/multiplicity/block-integrity
identities and a tiny seeded section-bootstrap replay. No skipped tests allowed.
All source, upstream dependencies, protocol and data hashes are checked before
and after each invocation. Certificates and blocks require FINISHED source logs.

## Section diagnostic: same computation, eight small blocks

The old 199-replicate monolithic run timed out at 96.1 s with last progress
81/199 (`results/independent/desktop/20261018T155406Z-collision-followup-sections-1812ed/run.log:39-41`).
The user now authorizes a smaller-block redo; do not silently reuse that run's
incomplete simulation state or treat its last progress as a completed sample.

1. `section-observed`: persist the eight observed section rows and statistics
   before any bootstrap. Reuse the OLD exact raw-T6 moment equations, own-section
   doublet moment fits q_s, real eligible pairs and word layout, and design-q
   sensitivity means; no new fitted parameters or approximations.
2. `section-block --block N`: N=0..7 fixed in advance; replicate IDs
   [0,25), [25,50), [50,75), [75,100), [100,125), [125,150), [150,175), [175,199).
   Use EXACTLY the old seed 3100000+20*rep+section for each simulated section.
   Forward raw-T6 generation at baseline fitted q_s; refit each simulated
   section's q_s and recompute shape and overall-fit statistics. Section 0.10
   is generated at q=.81 but contributes no echo pair, as in the old routine.
   Each block references the same hashed baseline and writes a new artifact.
3. `section-merge`: require all eight FINISHED, hash-matching blocks, exact
   replicate coverage, no duplicate/missing IDs, same baseline. Compute
   p_shape=(1+#shape >= observed)/200 and p_fit=(1+#fit >= observed)/200.
   If any block is incomplete, return that failure and no final p-value.

Unchanged statistics: shape removes the common multiplier sum O/sum E before
summing Pearson-like residuals; overall fit compares O directly with E. The
reference distribution is the **refitted plug-in parametric bootstrap**, not an
independent-pairs chi-square approximation. These are selected-family diagnostics,
not exact conditional p-values or a powered exclusion. Heterogeneity-sized power
remains unknown. A nonflag does not establish model correctness or homogeneity.

## Invocation rules

CPU only, one foreground process/invocation, existing NumPy and standard library.
No installs, network, API, GPU, subprocess, eval, background jobs, builds or
absolute output paths. Fresh folders under results/independent/<runner-alias>/.
95-second cooperative cap per invocation; tiny overshoot at a checkpoint is
possible. Run each case/block once. No increasing caps or automatic reruns.
Units failing stops interpretation. Preserve every failure and original run.log.

From repository root, one at a time with PYTHONIOENCODING=utf-8:

```
python work/independent/collision_fixed_halves/gate.py control --case 0
# separately cases 1, 2, 3, 4 in order
python work/independent/collision_fixed_halves/gate.py certify --inputs <five control.json paths in case order>
python work/independent/collision_fixed_halves/gate.py halves --certificate <certify.json>
python work/independent/collision_fixed_halves/gate.py section-observed
python work/independent/collision_fixed_halves/gate.py section-block --block 0 --baseline <section-observed.json>
# separately blocks 1..7 in order, same baseline
python work/independent/collision_fixed_halves/gate.py section-merge --baseline <section-observed.json> --inputs <eight section-block.json paths in block order>
```

Return the raw scores, controls/certificate, section table, combined diagnostics
and manifest with all FINISHED logs and failures. Do not run a spend/hold
ciphertext discriminator: its previous reference count-test power was only .26065
(`../collision_followup/PROTOCOL.md:267` defines that reference experiment).
