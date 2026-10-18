# Collision follow-up: authorized single-pass execution, 2026-10-18

Nothing in LP2 is solved. Each experiment command ran once, sequentially, with
PYTHONIOENCODING=utf-8 and the unchanged 95-second cooperative cap. No retries,
threshold/seed/code/protocol changes, GPU, background jobs or discriminator.
All 21 unit tests passed on every invocation. FINISHED is required; sections did
not finish. Split was deliberately NOT invoked because its new power gate failed.
The full-book result is a calibrated re-test of a selected hypothesis, not a
replication, joint mechanism fit or identification of collision causality.

All artifact paths below are relative to `results/independent/desktop/`.
Each listed folder contains its original `run.log`, including the failed run.

## Invocation manifest, in actual order

| # | Mode | Folder | Seconds | Outcome / artifact |
|---|---|---|---:|---|
| 1 | power | `20261018T155345Z-collision-followup-power-160fce` | 7.1 | FINISHED; `power.json` |
| 2 | mechanisms | `20261018T155356Z-collision-followup-mechanisms-ef3932` | 2.7 | FINISHED; `mechanisms.json` |
| 3 | sections | `20261018T155406Z-collision-followup-sections-1812ed` | 96.1 | Timeout; log only, no completed section artifact |
| 4 | control 0 | `20261018T155548Z-collision-followup-control-4f1b90` | 56.0 | FINISHED; `case.json` |
| 5 | control 1 | `20261018T155648Z-collision-followup-control-d40611` | 61.5 | FINISHED; `case.json` |
| 6 | control 2 | `20261018T155753Z-collision-followup-control-fbf152` | 46.7 | FINISHED; `case.json` |
| 7 | control 3 | `20261018T155846Z-collision-followup-control-54814b` | 61.7 | FINISHED; `case.json` |
| 8 | control 4 | `20261018T155954Z-collision-followup-control-70a149` | 53.1 | FINISHED; `case.json` |
| 9 | certify | `20261018T160053Z-collision-followup-certify-25137d` | 3.2 | FINISHED; `certificate.json` |
| 10 | test | `20261018T160108Z-collision-followup-test-7c859d` | 30.4 | FINISHED; `test.json` |
| 11 | optimism | `20261018T160142Z-collision-followup-optimism-f9c191` | 58.6 | FINISHED; `optimism.json` |

## E: exact reference power — HOLD the discriminator

Source: power folder / `power.json:120-165`, sensitivity at lines 168-284.
The externally trained top-15-difference count test has p0=0.5172413793 and
p1=0.6463592811 at a real repair under the stipulated reference geometry.
At 80 independent usable sites and exactly 35 hidden real repairs:

- Exact size-.05 randomized-boundary power: **0.2606501084**.
- Conservative nonrandomized power: **0.2063398528**, actual size **0.0340480584**.
- Reject for count >49; randomize with probability .7596464245 at count 49 to
  obtain exact size .05. This is a prospective power calculation, not an executed
  randomized ciphertext test.
- Same fixed difference set, true repairs 20/25/30/35/40: power
  .1408495000 / .1756060573 / .2155910705 / .2606501084 / .3103693027.

The reference power is exact rational finite-sample power for the specified
count-test family, estimated English law, independent sites and uniform
re-collision geometry. It is NOT the optimal power of every possible test and
NOT exact power for the actual selected LP2 sites. Actual-site power is unknown.
The frozen prospective requirement was >=.80: this reference test fails it.
**No spend/hold discriminator was run or proposed.**

## D: S-copy opportunity audit, not a new mechanism-fit result

Source: mechanisms folder / `mechanisms.json:2-29`.

| Mask | Targets | Equality hits | Source-S opportunities | S hits | Gross predictable forced S-hit budget, q=.81 |
|---|---:|---:|---:|---:|---:|
| First eligible | 815 | 36 | 22 | 4 | 891/1450 = .61448 |
| Shared with lag 6 | 1290 | 68 | 52 | 7 | 1053/725 = 1.45241 |
| All lag 5 | 2105 | 104 | 74 | 11 | 2997/1450 = 2.06690 |

Thus a source-S-only collision branch has small gross predictable repair capacity
on the observed history. It is not a ready population explanation of the reported
S excess (~8.6), much less all lag-5 excess (~31) or the first-target total (~8.2).
These compensator bounds are NOT deterministic limits on realized hits or a
controlled statistical exclusion; opportunity counts are themselves random.
The original shared-budget calculation is reproduced: raw log e .1379827854,
adjusted -17.4199009783, reject=false (`mechanisms.json:31-51`). Nothing establishes
a successful smallest second mechanism. Count and likelihood still do not
contradict each other: I5 at full strength overshoots the observed count.

## C: section check INCOMPLETE

Source: sections folder / `run.log:39-41`. Last progress message was 81/199 at
87.7 s; the next budget check stopped at 96.1 s. This is the expected small
overshoot of a cooperative 95 s cap, not an expanded cap. No retry or salvage
run was performed. No completed `sections.json` exists, so section-specific
expectations, heterogeneity p-values and fitted q outputs are **unknown** from
this authorized run. This is not an LP2 negative and not a failure of T6.
Do not turn the eight positive section excesses into a post-selection sign test.

## B/A: changed-code controls and certificate

| Case | Kind | Full maximum, nats | Full p_MC | Full flag | Frozen-rule validation score | Split p_MC | Split flag |
|---|---|---:|---:|---|---:|---:|---|
| 0 | I5 plant | 12.989403 | .001 | yes | -6.900094 | .292 | no |
| 1 | I5 plant | 15.933528 | .001 | yes | -10.180426 | .595 | no |
| 2 | T6 plant | 14.877847 | .001 | yes | -11.525951 | .718 | no |
| 3 | T6 plant | 6.480540 | .344 | no | -.180321 | .221 | no |
| 4 | no-echo null | 5.972646 | .492 | no | -13.986191 | .433 | no |

Source: each case artifact's full and split blocks. Full p lines are 1191 for
case 0, 1195 for cases 1-4; split p lines are 2231 for case 0, 2235 for cases 1-4.
These are synthetic control split tests, NOT an LP2 split result. Every planted
training-half winner was a different affine map, not its planted I5/T6 map:
case 0 (lag5,a23,b16,guarded), case 1 (lag5,a25,b20,guarded), case 2
(lag5,a21,b0,raw), case 3 (lag8,a19,b8,raw). This illustrates selection instability
at the half-book size; it does not identify a universal power rate from four plants.

Certificate source: certify folder / `certificate.json:2-5`:

- passed=true: 3/4 full-book plants and no null flag.
- split_passed=false: 0/4 split plants, below the required 2/4; null not flagged.
- **LP2 split was not run.** No retrospective stability conclusion, positive or
  negative, is available from LP2. No new split or restricted family was tried.

## B: permitted full-book B=999 test

Source: test folder / `test.json:3-10,1188-1191`; FINISHED at `run.log:32`.
Observed maximum **15.8952686735 nats**, winner **mix_I5_T6_w=1/4**.
Null maxima: median **5.9474051112**, empirical 95th percentile (sorted index
floor(.95*(999-1))) **8.3492305313**, maximum **11.3734142921**.
**0/999 exceedances; p_MC=.001**, the grid floor, not zero or p<.001.
The full test flags against its stated conditional Markov null.
The single-rule scores and winning setting are unchanged from the B=99 run.
The first 99 null replicates overlap that run; this is a precision extension,
not independent evidence, a new replication or a decryption.

## C: optional pure-null selection optimism, completed

Source: optimism folder / `optimism.json:14989-14999`.
Across 999 paired-null books, 190 discovery winners selected a lag-6 affine map.
For those selected maps, discovery-minus-independent count averaged
**26.5368421053**, Monte Carlo SE **.5134569529**. This selects whichever affine
map wins; it does NOT measure the selected fixed T6 map's inflation.
There were **zero selections containing fixed T6** and **zero selection scores
reaching 15.8952686735**. Fixed-T6 and observed-tail-conditioned optimism are
therefore **unknown**. The true winner's-curse correction to the observed 80
remains **unknown**. Do not subtract 26.54 from 80.

## Unchanged experiment files

The artifact fingerprints pin the unchanged analysis script, local tests, frozen
protocol, old model/gate/tests, parser, transcription and English corpus. No source
was repaired after a failure, and no failed gate was rerun. Documentation records
results separately; it does not silently revise the frozen protocol.
