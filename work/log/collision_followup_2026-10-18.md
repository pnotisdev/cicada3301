# Collision follow-up: single-pass execution authorized by the user

Nothing in LP2 is solved. User authorized exactly one invocation of each mode in
order, with the frozen 95 s cooperative cap, preserving failures. Power failure
would stop the sequence; power passed. Split was conditional on its new power gate.

Detailed results, manifest of all eleven invocations, raw-artifact locations and
file/line citations:

`results/independent/desktop/20261018-collision-followup-summary/REPORT.md`

## Results

- 21/21 identities passed on every invocation, zero skips. Experiment source,
  tests, protocol and seeds unchanged throughout. No retry, background job or GPU.
- Exact reference spend/hold count-test power, 35 hidden true repairs among 80
  independent usable sites: .2606501084 at randomized size .05; nonrandom power
  .2063398528 at size .0340480584. This is not optimal power across all possible
  tests or actual-site power. Frozen >=.80 requirement failed: HOLD discriminator.
- Source-S opportunities: first eligible 22 (4 hits), shared 52 (7 hits), total 74
  (11 hits). Gross predictable S-copy forced-hit contribution at q=.81:
  .61448 / 1.45241 / 2.06690. These are compensator bounds, not realized-hit ceilings
  or a controlled exclusion. No successful second mechanism established.
- Section bootstrap TIMED OUT at 96.1 s (cooperative cap; last progress 81/199).
  No sections.json, no section expectations or heterogeneity p reported, no retry.
  This is incomplete, NOT an LP2 negative.
- Full B=999 plant p-values: .001, .001, .001, .344; null .492. Certificate passed.
- Split-control plant p-values: .292, .595, .718, .221; null .433. Zero of four
  planted split tests flagged; certificate split_passed=false. LP2 split NOT RUN.
  Do not redesign/reseed until a pass; half-size power remains insufficiently
  established. No LP2 stability result, and no independent replication.
- Permitted full-book re-test: max 15.8952686735 nats, mix_I5_T6_w=1/4, zero of
  999 null exceedances, p_MC=.001 (floor). Null median 5.9474051112, empirical p95
  8.3492305313, max 11.3734142921. A selected-hypothesis conditional-Markov-null
  flag, not collision causality, joint model fit, decryption or replication.
- Optional optimism: 190 selected lag-6 affine-map winners, discovery-minus-
  independent count 26.5368421053, MC SE .5134569529. Zero fixed-T6-containing
  selections and zero scores reaching LP2. Fixed-T6, tail-conditioned and true
  observed-80 inflation remain unknown; subtracting 26.54 from 80 is invalid.

## Corrections retained from the preceding human-run package

The old section echo-versus-avoidance correlation in the registry was stale:
`results/independent/desktop/20261018T153415Z-collision-tables-a2d526/correlation_audit.json:84-87`
gives eight contributing sections, deficit Pearson +.3289931019 and fixed-q
Pearson -.3289931019; no significance claim. This is a pre-existing returned
result, not an output recovered from the timed-out section bootstrap.

## Documentation bookkeeping

The first `python scripts/build_overview.py` invocation reported an existing
unregistered result folder: `results/independent: folder has no [[folder]] entry
in the registry`, wrote some overview files and exited 1. Added the missing folder
entry and regenerated successfully. `git diff --check` reported no whitespace
errors (only a pre-existing CRLF warning for the runner REPORT). This correction
changed documentation only; no experimental gate, code, seed or protocol was
modified or retried. The package README now points to the completed results.

## What is NOT excluded / not established

Structured-key and hold-key mechanisms; actual-site discriminator power;
heterogeneity or lack thereof; a successful joint lag5/lag6/S/flat-lag mechanism;
untouched replication; causal identification of collision repair; key/plaintext
recovery. A failed power gate and an incomplete diagnostic are not negatives.
