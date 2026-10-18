# Prespecified echo-site dispersion, 2026-10-18

Nothing in LP2 is solved. User asked for fixed scales (section, per 100 eligible
pairs, gaps) and Bernoulli versus evenly spaced controls. Frozen before actual
site-statistic calculation: `work/independent/echo_dispersion/PROTOCOL.md`.

Full decisions, controls, all raw-artifact paths, file/line citations and fixed-bin
table: `results/independent/desktop/20261018-echo-dispersion-summary/REPORT.md`.

## Execution

Controls once: 11.6 s, FINISHED; permitted test once: 7.2 s, FINISHED. Both passed
28/28 tests, zero skips. No code/protocol/rate/seed edits, retries, failures,
background jobs, GPU, network, engine runs or spend/hold discriminator.
Unchanged 95 s cooperative cap each. Before/after fingerprints matched.

## Frozen model and controls

T6 within-word HIT sites only (not identified repair events). 80 total, 1290
eligible. Independent inhomogeneous Bernoulli site indicators before conditioning
on total 80. Raw-T6 one-point marginals by word position, prior section-specific
own-doublet q_s frozen. Exact conditional sampling and inclusion marginals pi_i
from Poisson-binomial dynamic programming, with small exact-enumeration checks.

Three lower-tail scales: section count dispersion, disjoint per-section bins of
100 eligible pairs (zero origin; short tails included), internal gap CV in
conditional expected eligible exposure. Bonferroni across exactly three scales.

0/4 Bernoulli negatives flag; 4/4 random-phase systematic evenly spaced positives
flag. Positive and negative controls share total 80 and every site's inclusion
marginal; joint regularity differs. All positive per-scale raw p=.001 floor,
adjusted .003 floor. Coarse gate passes; four controls/class do not precisely
estimate population false-positive rate or power. Fully regular 80-hit plants
are not a power measurement for 35 regular hidden repairs mixed with chance hits.

## LP2 results, B=999

| Scale | Statistic | Lower exceedances / 999 | Raw p | Bonferroni p |
|---|---:|---:|---:|---:|
| Section | 1.3365599723 | 23 | .024 | .072 |
| 100 eligible pairs | 6.4746299328 | 29 | .030 | .090 |
| Internal gaps | .7987435093 | 686 | .687 | 1.000 |

Omnibus adjusted p=.072, **no flag**. Counts are somewhat smooth, but no
family-adjusted departure. Gaps do not exhibit the low CV of fully regular plants.
No conclusion of equivalence, partial-regularity exclusion or a deterministic
schedule is warranted. No alternative scale, bin offset or tail was evaluated.

## What is NOT established

A no-flag result does not validate Bernoulli or exclude weak/partial regularity.
Forward-cipher hit dependencies and q_s uncertainty are not modeled by this
site-process null. The prior forward-model upper-tail bootstrap p=.990 is not
complementary to the new Bernoulli conditional lower-tail p=.024; do not combine
them as independent evidence. Hypothesis motivated by previous same-data
smoothness; no untouched replication or historical-selection correction.
No true repair sites identified, key consumption inferred, key/plaintext recovered,
new mechanism excluded, or LP2 text solved. Partial-regularity power remains unknown.
