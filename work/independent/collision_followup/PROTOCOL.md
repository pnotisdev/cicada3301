# Frozen follow-up protocol — analysis and human-run tools only

**Nothing in LP2 is solved. This directory is unexecuted/unvalidated.** No Python,
syntax check, unit test, simulation, engine, GPU, API or experiment was run by the
assistant. Only this new directory was written. Existing results and shared docs
were not modified. All new numerical outputs below are **unknown** until a human
returns a FINISHED log. This document is frozen before any new invocation; changing
it invalidates the new controls through the fingerprint.

## 1. What the returned evidence says

Paths below are relative to the repository root. Abbreviate these existing result
folders solely for readability:

- **K** = `results/independent/desktop/20261018T153404Z-anti-repeat-matrix-87cd69`
- **T** = `results/independent/desktop/20261018T153415Z-collision-tables-a2d526`
- **C** = `results/independent/desktop/20261018T153636Z-collision-controls-4fb338`
- **X** = `results/independent/desktop/20261018T153815Z-collision-test-75338b`

The identity gate tested 464 rows and 24,389 prefixes, not English hold-versus-spend
power (K/`run.log:4-9`). The full-search statistic was 15.895269 nats, winner
`mix_I5_T6_w=1/4`, p_MC=.01 at B=99 (X/`run.log:23-27`). This is a deviation from the
stated conditional Markov null within a family chosen from this data, not a
replication and not a causal identification. The original controls were 3/4, with
the second T6 plant missed at p=.34 (C/`run.log:23-29`). Neither 75% population power
nor a precise false-positive rate follows from five controls.

The corrected correlation is +.328993 for deficit and -.328993 for fixed-q across
eight contributing sections (T/`correlation_audit.json:84-87`). They are opposite by
algebra, not independent evidence. No correlation significance claim is warranted.
The adjusted budget log e is -17.419901, raw +.137983, and reject=false
(T/`budget_evalue.json:14-18`). **Non-rejection is not proof that a mechanism fits.**
The predictable upper mean 365973/2900 is not a deterministic ceiling on observed
hits. Do not reject a budget by comparing 148 with that number alone.

## A. Frozen section split: a stability test, not recovered virgin data

Training: **0.7, 0.9, 0.12, 0.14**. Validation: **0.8, 0.11, 0.13, 0.15**.
0.10 is omitted: it has no lag-6 eligible pair. This interleaves the eight
contributing sections in their canonical order. No balancing by observed effect,
rerolling split, reverse-direction second test, or choosing a better half later.

On training only choose the maximum from the **unchanged full family**: 812 affine
maps x 8 lags x raw/guarded, plus three fixed mixtures; q=.81. Ties take the first
maximum in the existing scan order. Freeze all parameters including guard and
mixture weight. On validation compute **that single conditional log-likelihood
ratio** only. Matched null: independently uniform initial rune per section,
exactly the observed number of adjacent doublets in each validation section,
uniformly chosen repeat positions and uniformly chosen off-diagonal runes.
Keep the actual word layout. This is the existing exact conditional Markov null,
not an English null or a shuffle preserving empirical unigrams
(`../collision_substitution/collision_model.py:262-297`).

B=999, seed 2300000+b, b=0..998. Decision: validation score >0 and
(1+# null scores >= validation score)/1000 <=.05. No null replicate reselects on
validation. Conditional on a genuinely untouched training set, one frozen rule
needs no validation-family penalty. **Here the whole LP2 book already informed
family discovery, so this conditional p is a retrospective stability diagnostic,
not an unconditional post-selection replication p.** Only new independent data
or an adequately specified original discovery-selection procedure could repair
that limitation. A frozen protocol today cannot erase it.

Implementation: `analysis.py:27-34,58-117`. Split controls use the SAME split and
selection on each synthetic plant, rather than giving the method the planted rule.
Four plants and one null are fixed to the previous seeds; full-book controls
require >=3/4 flags and no null flag. A separately labelled **coarse** half-power
gate requires >=2/4 stability flags and no null flag. Its precision is unknown;
failure disables the LP2 split command, not a reason to change seeds or thresholds.

## B. B=999 rerun, including changed-code controls

B=999 gives a p grid of .001, **not .001 statistical accuracy**. If zero of 999
nulls exceed, report p_MC=.001 (floor), not p=0 or p<.001. The original seed blocks
are retained; the first 99 null replicates overlap the previous run. This is a
precision extension of the same re-test, not fresh evidence or a second discovery.
The old controls cannot authorize this code: new script, tests, protocol, prior
code, parser, verified transcription and reference corpus are fingerprinted.

Each control is its own foreground invocation (full scan plus split). Do not put
five B=999 cases in a single potentially >2-minute gate. Every invocation has a
95-second cooperative work limit; a failure or timeout is INCOMPLETE, never a
negative, and must not be automatically retried with a bigger cap. Runtime here
is **unknown**. The user's ~30 s estimate applies to a full-scan B=999 test, not
to an independently measured runtime of these changed tools. Checkpoints are
between small bounded steps; this is not a preemptive operating-system kill.
No jobs, subprocesses, installs or background work are launched.

From repository root, manually, one command at a time:

```powershell
$env:PYTHONIOENCODING='utf-8'
python work/independent/collision_followup/analysis.py control --case 0
python work/independent/collision_followup/analysis.py control --case 1
python work/independent/collision_followup/analysis.py control --case 2
python work/independent/collision_followup/analysis.py control --case 3
python work/independent/collision_followup/analysis.py control --case 4
```

Cases 0/1 are I5 plants; 2/3 T6 plants; 4 conditional no-echo null. Keep failures.
Then substitute the five repository-relative output paths, in that order:

```text
python work/independent/collision_followup/analysis.py certify --controls <case0.json> <case1.json> <case2.json> <case3.json> <case4.json>
```

Require `passed=true` in the new FINISHED `certificate.json` for the full test;
also `split_passed=true` for split. These commands do not start one another:

```text
python work/independent/collision_followup/analysis.py test --controls <certificate.json>
python work/independent/collision_followup/analysis.py split --controls <certificate.json>
```

Return all `run.log` files, `case.json` files, certificate and completed test/split
JSON. Outputs use fresh `results/independent/<alias>/<UTC>-collision-followup-.../`
folders through the existing privacy-scrubbing helper. Partial files do not count.

## C. Section prediction, heterogeneity, and selection optimism

The stored section pairs/hits are:

| Section | Eligible | Observed T6 hits | New own-rate expectation |
|---|---:|---:|---|
| 0.7 | 79 | 6 | unknown |
| 0.8 | 106 | 6 | unknown |
| 0.9 | 184 | 10 | unknown |
| 0.11 | 178 | 13 | unknown |
| 0.12 | 100 | 5 | unknown |
| 0.13 | 152 | 11 | unknown |
| 0.14 | 154 | 9 | unknown |
| 0.15 | 337 | 20 | unknown |

Source: T/`correlation_audit.json:2-83`. The aggregate design-q prediction 79.287272
is already measured (T/`run.log:44`); it is not a new section-rate computation.

`sections` uses each section's **whole ordered word layout**, eligible pairs and
own adjacent doublet count, excluding section seams. Merely inserting
q_s=1-29*d_s/(n_s-1) into a raw repair model is inconsistent: raw substitutions can
emit the previous rune. For T6 let h_i(q)=P(T(C[i-6])=C[i-1]) from the two-point
recurrence. The exact mean doublet count is

    D_s(q) = (n_s-1)*(1-q)/29 + q/29 * sum_{local i>=6} h_i(q).

Fit q_s in [0,1] by bounded moment matching D_s(q_s)=observed d_s; boundary fits
are possible and the fitted count is reported. Then compute the within-section
T6 expected count from the exact recurrence, evaluated in floating point.
Also report the common design-q mean and the clipped deficit estimator separately.
This is not an MLE, not a fit of q to the echo count, and not a statement about
structured/nonuniform keys. Cross-word fallback preserves the same doublet law.

Two diagnostics: (i) sum (O_s-E_s)^2/E_s for overall prediction fit;
(ii) remove a common multiplier t=sum O/sum E and use
sum (O_s-t E_s)^2/(t E_s) for section-shape heterogeneity. Neither uses an
independent-pairs chi-square reference. Instead 199 forward raw-T6 books at fitted
q_s, real layout, refit each section's q and recompute both statistics. The resulting
p grid is .005 and the bootstrap is **plug-in, approximate and post-selection**.
Code: `analysis.py:179-272`; identity checks compare its float recurrence against
old exact rational means. Positive heterogeneity and zero-residual null wiring
checks are in `test_followup.py`; the forward bootstrap supplies a model null.
**LP2-sized heterogeneity power is unknown.** This is a diagnostic, not a powered
exclusion of T6 or all repair mechanisms. If a meaningful negative is wanted, a
separately approved heterogeneity-sized plant must establish sensitivity first.

`optimism` draws 999 conditional-null discovery books and independent same-layout
validation books. On each discovery book replay the full affine/lag/guard/mixture
selection; count its selected relation on both books. Record selected lag-6-map
optimism and the actual fixed T6 component when a winning rule contains it, with
sample size and Monte Carlo SE. Fewer than 20 matching selections => **unknown**.
Report how many selection scores reach the already observed 15.895269. With no
such tail matches, tail-conditioned inflation is **unknown**, not extrapolated.

This estimates **pure-null selection optimism**, not the fraction of 80 actual
hits that are false. Choosing any affine relation at lag 6 is not choosing the
fixed map T6; their outputs are labelled separately. A null average cannot be
subtracted from 80 as an unbiased winner's-curse correction under an unknown true
signal. The complete historical discovery process (S selection, word scope,
initial lag search, other experiments) is also not reproduced by this finite scan.
Code: `analysis.py:275-305`.

Optional diagnostic gates, separately, after deciding to use these caveats:

```text
python work/independent/collision_followup/analysis.py sections
python work/independent/collision_followup/analysis.py optimism
```

Return `sections.json` / `optimism.json` plus FINISHED logs. If 95 seconds is
insufficient, stop and redesign smaller blocks; do not extend or auto-resume.

## D. The smallest additional branch is not yet a successful second mechanism

**Count and likelihood do not contradict one another.** I5 at q=.81 predicts
129.381642 lag-5 coincidences, Markov baseline about 72.586, observed 104
(T/`run.log:29`; `results/analysis/echo_position.txt:4`). Observed lies between
baseline and this too-strong alternative. Its log LR can therefore be positive
(+3.170695 raw) without the alternative being a good absolute fit
(X/`test.json:112-124`). Approximate amplitude shrinkage from counts alone is
31.4/56.8, about .55; this is a descriptive ratio, **not** a fitted likelihood
parameter or a correction for selection. Doublet hits, failed avoidance,
unavailable taps, overlap, and the log penalty on all nonhits matter to likelihood
(`../collision_substitution/collision_model.py:156-218`). A positive LR is neither
a goodness-of-fit p nor an estimate of a causal repair fraction.

A homogeneous I5/T6 mixture reallocates ONE repair budget, not two. Matching the
lag-5 excess uses roughly half of I5's full strength; the half-mixture then gives
only +17.402344 lag-6 T hits rather than +34.804513 for pure T6
(T/`run.log:44,53,56`). Conversely w=1/4 wins the observed conditional likelihood,
not a demonstrated joint match to both mean counts. At the first lag-5 target,
T6 is unavailable, so adding a weak I5 branch there costs no T6 repairs. But that
alone predicts a position concentration absent from the remaining +22.9 shared
target excess (`results/analysis/echo_position.txt:4,6-10,22`).

The smallest explicit S-sensitive extra instruction is:

    On an enforced collision, if local>=5 and C[i-5]=S, copy S;
    otherwise use T6, with its existing unavailable-tap fallback.

It has no fitted rate, but it does NOT automatically supply the non-S excess or
the +8.2 first-eligible total. It also diverts shared T6 repairs. A probabilistic
version adds one rate; filling the non-S deficit needs still more structure or a
chance fluctuation. Source-blind I/T mixtures cannot privilege S by their
nonfixed-rune symmetry (`../collision_substitution/DERIVATION.md:315-326`).

For a source-S-only branch, the **gross predictable** forced S-hit budget on any
mask is at most q/29 times its observed source-S opportunities; losses of natural
hits only reduce its incremental benefit. `mechanisms` reports these exact
opportunity counts and bounds at first-eligible, shared and all lag-5 targets,
plus the original conservative budget diagnostic. It does not fit or test this
post-hoc new rule. Its unit/control foundation is the old exact kernel and budget
identities; actual joint-fit and flat-lag power remain **unknown**.

```text
python work/independent/collision_followup/analysis.py mechanisms
```

**Answer to 'the smallest mechanism that supplies all of it': unknown.** The
current evidence does not establish one. A cheap extra branch can be specified;
calling it successful without a joint forward check of lags, source composition,
first targets, doublets and shared budget would overstate the result. No new
broad hypothesis search or uncalibrated S-rule LP2 test is provided.

## E. Spend-versus-hold power BEFORE a discriminator experiment

Let a=C[i-1], R=C[i] at a true repair, D=P[i+1]-P[i] (mod 29). A retained colliding
key implies attempted next output X=a+D, **not necessarily emitted output**.
If X=R and a new repair fires, it changes again. With raw next repair substitute
R' and r0=R-a, r1=R'-a, the exact single-site law, for any externally fixed set A
of differences, is

    hold: P(C[i+1]-a in A)
      = f(A) + q*f(r0)*(1_A(r1)-1_A(r0)).

This includes ineffective repairs r1=r0. If the next tap is unavailable or guarded,
replace 1_A(r1) by the fallback mass off r0. A section-final site has no successor
and is unusable; a word-final site can still have a successor with a fallback.
Under fresh spend candidates the corresponding exact kernel mass is

    spend: |A|/29 + q/29*(1_A(r1)-1_A(r0)),

with the same fallback modification. These equations follow by enumerating the
uniform attempt and repair coin, as in
`../collision_substitution/collision_model.py:36-58,300-322`; the held-key identity
itself is tested at `../collision_substitution/test_collision_model.py:151-157`.
If English plaintext is Markov, f at selected real repairs need not equal its
unconditional marginal. Overlapping sites are not independent trials.

### Precisely defined tractable reference power

No numeric English difference law was attached. A corpus-dependent numeric power
cannot be invented while obeying 'no code run'. Instead `power` computes exact
rational finite-sample power for this **explicit reference experiment**, without
reading the LP2 ciphertext or collecting echo differences:

1. Use only the existing Emerson corpus from SELF-RELIANCE through the end marker,
   alphabetic words, repository rune spelling (IO->IA), including cross-word
   bigrams. Estimate the joint bigram law with add-half per ordered rune pair.
   Thus f(d)=(2*n_d+29)/(2*N_bigrams+841). This is a joint-law difference marginal,
   not an unweighted average of conditional bigram rows.
2. 80 independent, usable, nonoverlapping sites; exactly 35 hidden true repairs,
   labels exchangeable. False sites have background Uniform(29) differences.
   Repair geometry r0,r1 is independently uniform and independent of D at each
   site; it is integrated out, not asserted to be the observed LP2 geometry.
   Then p0=|A|/29 and p1=(1-q/29)*f(A)+(q/29)*p0, q=.81. The q/29 term accounts for
   re-collision under **this reference geometry**; real repair geometry can differ.
3. Rank the 29 differences by external f(d), tie by rune index. For each top-k
   set, k=1..28, compute the size-.05 upper-tail count test. Choose the set with
   highest external-law power, never by LP2 successor differences. No LP2 multiple
   testing occurs in this reference calculation. This is optimal only within
   these 28 count tests, not the full likelihood-ratio experiment.
4. Under spend, Z~Binomial(80,p0). Under hold,
   Z~Binomial(45,p0)+Binomial(35,p1), independently. The exact alternative pmf is

       [z^j] (1-p0+p0*z)^45 * (1-p1+p1*z)^35.

   Select integer k with P0(Z>k)<=.05<P0(Z>=k), and
   gamma=(.05-P0(Z>k))/P0(Z=k). Exact power is
   P1(Z>k)+gamma*P1(Z=k). Also report nonrandomized size-conservative power and
   sensitivity at 20,25,30,35,40 true repairs for the SAME selected A. All arithmetic
   is Fraction, not a Gaussian approximation or Monte Carlo power estimate.

Implementation: `analysis.py:329-399`; independent tiny enumeration and null-size /
strong-plant checks are in `test_followup.py`. This is exact conditional on a
stipulated estimated law and site experiment, not exact knowledge of English.

**Reference numeric power: unknown until evaluated. Actual LP2 discriminator
power: unknown**, even after this calculation, unless usable-site count, repair
selection law, geometry and overlap dependence are specified. Exactly 35 real
repairs is a planning scenario, not a label recovered from the 80 hits. The
35-hit excess alone does not prove exactly 35 true repairs.

The only proposed E invocation is this analytic power prerequisite:

```text
python work/independent/collision_followup/analysis.py power
```

Return `power.json` and FINISHED `run.log`. This command does not read LP2 or run a
discriminator; **no spend/hold LP2 test is implemented or proposed yet**. Before
any such experiment, freeze a justified actual-site law and decision rule and
require prospective power >=.80 at alpha .05, with controlled plants/nulls.
If the reference calculation is already weak, hold the discriminator rather than
spending another selected-data test on an unpowered statistic.
