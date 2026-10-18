# T6 echo-hit dispersion: frozen three-scale site-process test

**Nothing in LP2 is solved.** The user requested fixed scales (per section, per
100 eligible pairs, gaps) and Bernoulli versus evenly spaced controls. New frozen
protocol: `work/independent/echo_dispersion/PROTOCOL.md`. The test was motivated by
previous same-data smoothness, so it is not untouched replication or an adjustment
for historical selection. No new scale, tail, offset, rule or rate was tried after
seeing these results.

## Execution and artifacts

Two invocations, each run once, sequentially, unchanged 95 s cooperative cap:

1. Controls: **11.6 s, FINISHED**. 28/28 unit tests, zero skips.
   `results/independent/desktop/20261018T164533Z-echo-dispersion-controls-4db2d5/run.log`
   and `controls.json`.
2. Permitted LP2 test: **7.2 s, FINISHED**. 28/28 unit tests, zero skips.
   `results/independent/desktop/20261018T164550Z-echo-dispersion-test-3cc8e1/run.log`
   and `test.json`.

No code, seed, protocol or input changed during either invocation. No failures,
retries, background work, network, GPU, builds, decryption or spend/hold test.
Hashes bind source, tests, frozen protocol, upstream data/code and the existing
section-rate baseline. Old failures and timeouts are not altered.

## What was tested

Only **80 within-word T6 HIT sites among 1290 eligible pairs**, not 80 known
repairs. Raw-T6 one-pair marginals use each section's own previously fitted
doublet-based q_s and actual local word positions. No fitting to echo-site counts.
The null assumes independent inhomogeneous Bernoulli indicators BEFORE conditioning
on exactly 80 total hits. Conditional draws and inclusion probabilities pi_i are
computed by a Poisson-binomial dynamic program, independently checked on small
exact enumerations; sum pi_i=79.99999999999997.

**This is a conditional Bernoulli SITE PROCESS, not an exact forward-cipher null.**
Conditioning induces the correct fixed-total dependence, but does not add the
extra dependence caused by shared ciphertext positions or a collision generator.
The prior q_s estimates are held fixed; their uncertainty is not propagated.
A result cannot reject raw-T6 encryption or prove deterministic repair scheduling.

Three lower-tail statistics were frozen before actual site statistics:

- Section Pearson-like count dispersion about E_s=sum pi_i.
- Count dispersion over 100-eligible-pair bins, reset at each section, origin zero,
  including short terminal bins at their correct expected exposure. Sixteen bins.
- Pooled squared coefficient of variation of INTERNAL consecutive hit gaps in
  cumulative expected eligible exposure, normalized by each section's own mean
  internal gap. No cross-section/boundary gaps; sections need >=3 hits. This is
  internal gap regularity, not a period search in rune distance.

999 reference masks, lower-tail plus-one p with inclusive ties; Bonferroni over
exactly these three scales. Flag if min(1,3*min raw p)<=.05. No upper-tail or
post hoc two-sided test substituted for this decision.

## Controls: matched count AND one-site marginals

The four negative plants are exact conditional-Bernoulli draws with 80 hits.
The four positive plants use a random phase and 80 equally spaced grid points
in cumulative conditional expected eligible exposure. They have the SAME total
and expected inclusion probability pi_i at every site as the null, but much
stronger regularity of joint placement. These are site-mask plants, not planted
keys or encrypted English. Separate reference bank, seeds frozen in protocol.

| Control | Raw lower-tail p: section / 100 / gaps | Omnibus adjusted p | Flag |
|---|---|---:|---|
| Bernoulli 0 | .733 / .567 / .727 | 1.000 | no |
| Bernoulli 1 | .575 / .265 / .202 | .606 | no |
| Bernoulli 2 | .878 / .515 / .067 | .201 | no |
| Bernoulli 3 | .082 / .277 / .091 | .246 | no |
| Evenly spaced 0 | .001 / .001 / .001 | .003 floor | yes |
| Evenly spaced 1 | .001 / .001 / .001 | .003 floor | yes |
| Evenly spaced 2 | .001 / .001 / .001 | .003 floor | yes |
| Evenly spaced 3 | .001 / .001 / .001 | .003 floor | yes |

**Gate PASSED: 0/4 Bernoulli flags, 4/4 evenly spaced flags.** Frozen requirement:
zero Bernoulli flags and at least three evenly spaced flags. Four controls/class
are not precise estimates of population size/power. Fully regular 80-HIT plants
do NOT establish sensitivity to ~35 regular hidden repairs mixed with natural
hits. Partial-regularity power remains **unknown**.

Source: controls artifact `controls.json:2-4`; per-case omnibus p at lines
112,221,330,439,548,657,766,875. All control indices and per-scale statistics remain
in the raw artifact; no missed control is omitted.

## LP2 result: no family-adjusted flag

| Frozen scale | Statistic | Null statistics <= observed / 999 | Raw lower p_MC | Three-scale adjusted p |
|---|---:|---:|---:|---:|
| Per section | 1.3365599723 | 23 | .024 | .072 |
| Per 100 eligible pairs | 6.4746299328 | 29 | .030 | .090 |
| Internal gaps | .7987435093 | 686 | .687 | 1.000 |

**Omnibus adjusted p=.072; flag=false.** Source: test artifact `test.json:2-23`.
Counts are somewhat smooth under this null at the section and 100-pair scales,
but neither survives the frozen three-scale penalty. Internal gaps are not in
the low-dispersion tail; compare with the strong evenly spaced controls' gap
statistics .000510-.000606. No statement of equivalence to Bernoulli or controlled
exclusion of partial regularity follows from the nonflag.

The earlier upper-tail section-bootstrap p=.990 is not this test's lower-tail
p. The former used refitted forward-cipher books and a common-multiplier shape
statistic; this uses a fixed-rate conditional Bernoulli site process. Different
nulls/conditioning need not produce complementary Monte Carlo p-values. Do not
combine them as independent evidence or replace the new .024 with the old
upper-tail complement after looking.

## Fixed 100-eligible-pair bins (section-relative ranks, inclusive endpoints)

Expected counts use CONDITIONAL inclusion probabilities and total 80; they are
not the earlier unconditioned section expectations summing to 79.298.

| Section | Eligible ranks | Eligible | Observed | Conditional expected |
|---|---|---:|---:|---:|
| 0.7 | 0-78 | 79 | 6 | 4.988217 |
| 0.8 | 0-99 | 100 | 6 | 6.337194 |
| 0.8 | 100-105 | 6 | 0 | .380273 |
| 0.9 | 0-99 | 100 | 4 | 6.342178 |
| 0.9 | 100-183 | 84 | 6 | 5.327515 |
| 0.11 | 0-99 | 100 | 8 | 6.333424 |
| 0.11 | 100-177 | 78 | 5 | 4.940390 |
| 0.12 | 0-99 | 100 | 5 | 5.795538 |
| 0.13 | 0-99 | 100 | 9 | 6.015803 |
| 0.13 | 100-151 | 52 | 2 | 3.128215 |
| 0.14 | 0-99 | 100 | 6 | 6.111340 |
| 0.14 | 100-153 | 54 | 3 | 3.300139 |
| 0.15 | 0-99 | 100 | 5 | 6.231449 |
| 0.15 | 100-199 | 100 | 9 | 6.231268 |
| 0.15 | 200-299 | 100 | 5 | 6.231381 |
| 0.15 | 300-336 | 37 | 1 | 2.305677 |

Source: test artifact `test.json:5479-5591`; section aggregates at 5428-5477;
all 80 observed sites are also stored by section-relative rune index and eligible
rank. No alternative bins or scales were evaluated on LP2.

## What remains unknown

Historical-selection-adjusted inference; exact forward-cipher dispersion
calibration; uncertainty in prior q_s; sensitivity to partial regularity or
35 true repair events mixed with natural hits; a physical schedule, collision
causality, key consumption, key/plaintext recovery. No new exclusion or solution.
