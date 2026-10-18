# Prespecified T6 echo-hit dispersion test — freeze before new statistics

**Nothing in LP2 is solved.** The user requested a dispersion test with scales
fixed first: per section, per 100 eligible pairs, gaps between sites; Bernoulli
plants against evenly spaced plants. This protocol is hashed before any new
observed dispersion statistic is calculated. No prior package is changed.

The question was motivated by already observed section smoothness. This is
**prespecified for these new runs, not untouched replication or a correction for
historical hypothesis selection**. No new significance claim erases that caveat.

## Scope and null: echo HITS, not latent repairs

Only within-word lag-6 T hits, C[i]=24-2*C[i-6] mod 29. No I5, other affine maps,
other lags, word scopes, orientations, adjustable rates or chosen bin offsets.
The known total is 80 among 1290 eligible pairs across eight contributing sections.
0.10 has none. Eligible pairs are ordered by target rune within a section, joining
wrapped words with the repository's already verified parser.

A site-process null must be distinguished from a cipher null:

- Assign each eligible pair the **raw-T6 unconditional one-pair probability** at
  its local word position, computed using the existing two-point recurrence and
  the section's previously fitted own-doublet q_s. The prior persisted baseline is
  `results/independent/desktop/20261018T162753Z-collision-fixed-section-observed-a7fb33/section-observed.json`.
  Use q_s ONLY; do not fit to section echo counts. Pin that artifact and upstream
  code/data hashes. These rates are frozen nuisance estimates, not known English
  probabilities or hidden repair probabilities.
- Model eligible-site indicators as **independent inhomogeneous Bernoulli draws**,
  then condition on EXACTLY 80 total hits, not on eight section counts. This removes
  amplitude as a confounder while preserving a section-count dispersion test.
- Sample this finite conditional distribution using a Poisson-binomial dynamic
  program, not iid shuffling, sampling with replacement, approximate weighted
  sampling or a Gaussian count approximation. Compute exact conditional one-site
  inclusion probabilities pi_i from prefix/suffix convolutions. Their sum is 80.
  Floating-point evaluation is checked against independent exact small enumerations.

**Independence of hit indicators is an assumption.** Actual T6 relations share
ciphertext positions, and raw collision generators can induce dependencies.
Taking their exact one-pair probabilities does NOT make Bernoulli placement an
exact forward-cipher null. This test can flag that SPECIFIED SITE PROCESS only.
It cannot by itself exclude raw-T6 encryption, structured keys, collision repair,
or demonstrate a deterministic schedule. Prior q_s uncertainty is not propagated.
A later forward-cipher dispersion calibration would require a separate protocol.

## Three scales, all lower-tail and fixed in advance

Let a simulated or observed 1290-bit mask contain exactly 80 hits. Use expected
conditional inclusion probabilities pi_i, not the unconditional means, throughout.

1. **Per section**: E_s=sum pi_i over eligible pairs in section s. Statistic
   D_section=sum_s (O_s-E_s)^2/E_s. Eight sections, no reordering or selected subset.
2. **Per 100 eligible pairs**: within EACH section partition eligible ranks
   [0,100), [100,200), etc., starting at its first eligible target. Include the
   final partial bin, weighted by its own E_b=sum pi_i; never discard it or pool
   it with another section. D_100=sum_b (O_b-E_b)^2/E_b. No alternative offset,
   window size, overlapping/sliding window or rune-distance bin scan.
3. **Gaps between sites**: within each section, assign eligible pair i the
   coordinate z_i=sum_{j<=i} pi_j - pi_i/2. For sections with >=3 hits, take
   INTERNAL consecutive hit gaps g=diff(z at hit indices), divide by their own
   section's mean gap, and pool sum (g/mean(g)-1)^2 divided by the total number of
   included gaps. No cross-section or boundary gaps. Sections with <3 hits supply
   no gap degrees of freedom. A small value means similar internal gaps in
   exposure-adjusted eligible-pair order, not necessarily periodicity in rune
   distance. Compact regularly spaced clusters can also have small gap CV; the
   count scales supply complementary information, not guaranteed detection of all
   departures. No gap threshold, chosen lag or period scan.

Lower values at each scale mean less dispersion. Keep all three statistics and
p-values even if some do not flag. For each, p_lower=(1+#null statistic <= observed)
/1000 with inclusive ties. Family control: p_Bonf=min(1,3*p_lower) for each scale,
p_omnibus=min(1,3*min(p_lower)), flag iff p_omnibus<=.05. This pays for three fixed
scales without assuming their independence. Raw p grid .001; adjusted minimum
.003, not p=0. No upper-tail or two-sided result will replace this frozen decision.
No post hoc subdivisions or extra scales will be promoted as prespecified tests.

## Matched controls: random versus regular, same total and one-point marginals

Before examining the actual site dispersion, run one control invocation with an
independent 999-book conditional-Bernoulli reference, seeds 8000000+b, b=0..998.
Assess eight generated site masks with exactly the same three statistics and
multiplicity penalty:

- Four negative **Bernoulli plants**, conditional on 80 hits, seeds 8100000..8100003.
  They are drawn from the exact stated null, not random keys or ciphertext plants.
- Four positive **evenly spaced plants**, seeds 8200000..8200003. A single uniform
  random phase U defines grid positions (j+U)/80, j=0..79, in the global cumulative
  CONDITIONAL expected-exposure measure sum(pi_i)/80. Map each grid point to its
  containing eligible site. Every pi_i<1, so sites are distinct. Random-phase
  systematic sampling has the SAME inclusion marginals pi_i and total 80 as the
  null; only the joint spacing/count dependence changes. These are evenly spaced
  in expected eligible exposure, not guaranteed equal raw rune distances.

Frozen control gate: **0/4 Bernoulli flags and >=3/4 evenly spaced flags** using
p_omnibus<=.05. Preserve all per-scale outcomes and selected indices. Four samples
per class are a coarse method/wiring check, not a precise false-positive or power
estimate. Fully regular 80-HIT plants are deliberately strong: they do NOT measure
power for ~35 regular hidden repairs mixed with natural hits. That power is unknown.
If the gate fails, stop before the LP2 test. Do not change seeds, thresholds,
regularity strength or the null until a pass appears.

The LP2 invocation requires current FINISHED controls with matching fingerprint
and config. It uses a separate reference bank, seeds 8400000+b. It verifies that
the actual total is still the frozen 80; a mismatch stops rather than silently
changing the conditioning target. No controls or earlier null samples are counted
as extra LP2 replicates. Report actual site locations using section-relative rune
indices and eligible-pair ranks; no absolute machine paths.

## Gates, outputs and human limits

Run old identities plus the new conditional-sampling, marginal-matching, bin,
gap and tail-direction controls first. A skip or failure stops interpretation.
Every invocation is foreground CPU-only, cap 95 s cooperatively (not a preemptive
kill); no network, API, eval, subprocess, GPU, install or background job. Each
invocation gets a fresh results/independent/<runner-alias>/ folder. No retries or
longer caps after a failure. Original logs, including failures, must be retained.
Source, test, protocol and upstream input hashes are compared before/after.

From repository root, one invocation at a time, PYTHONIOENCODING=utf-8:

```
python work/independent/echo_dispersion/gate.py controls
# ONLY if controls passed and log ended FINISHED:
python work/independent/echo_dispersion/gate.py test --controls <repository-relative controls.json>
```

Return run.log, controls.json/test.json, all per-scale scores and adjusted p-values,
per-section and fixed-bin counts/means, and the exact model limitations. An
incomplete gate is not an LP2 negative; a large p does not prove a model true.
No spend/hold discriminator, key search, decryption or original cipher-model
exclusion is authorized by this experiment.
