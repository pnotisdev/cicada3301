# Collision substitutions: finite rules, exact predictions, and identifiability

**Nothing in LP2 is solved. No code, test, simulation or search was executed for
this review. Numerical predictions not already present in a cited input are
`unknown` until the human-run program produces them.** Mathematical expressions
below are derivations, not reported experiments. Only this new subdirectory is
written; no shared document, engine, active job or previous independent tool is edited.

## 0. Evidence, denominators, and corrections

### Observed inputs (do not combine different shuffle runs as exact measurements)

| Quantity | Reported value | Source |
|---|---|---|
| Total runes / corrected words | 12,956 / 2,896 | `results/analysis/families.txt:1` |
| Adjacent transitions / doublets, excluding section seams | 12,947 / 86 | `results/analysis/cicadanotebook_checks_2026-10-17.txt:7-9,36` |
| Within-word equality at lag 5 | 104 / 2,105; shuffle expectation 72.9; excess 31.1 | `results/analysis/echo_position.txt:3-4` |
| Lag-5 equality, earlier word position zero | 36 / 815; expectation 27.8; excess 8.2 | `results/analysis/echo_position.txt:6` |
| Lag-5 S-S | 11; expectation 2.4; excess 8.6 | `results/analysis/echo_position.txt:12-13` |
| Within-word T relation at lag 6 | 80 / 1,290; expectation 44.9; excess 35.1 | `results/analysis/echo_position.txt:21-22` |
| Lag-6 excess-rate uncertainty | 0.0272 +/- 0.0047 per eligible pair | `work/log/phase11_review.md:18-21` |
| Claimed avoided-collision range | 0.0269-0.0282 | `work/log/phase11_review.md:18-21` |
| Cross-word excess, lag 5 / lag 6 | +0.8 / +1.1 | `results/analysis/echo_position.txt:5,23` |
| Alternative shuffle means, lag 5 / lag 6 | 72.4 / 44.3 | `results/analysis/echo_values.txt:3,9` |
| Uniform-echo source-concentration upper-tail frequency, lag 5 / lag 6 | 0.03 / 0.25 | `results/analysis/echo_values.txt:5,11` |
| Same statistic without S | upper-tail frequency 0.52 | `results/analysis/echo_values.txt:14` |

The last three rows mean that a uniform echo is not a **population explanation**
of why S is special, but the existing small-sample concentration test is not an
absolute exclusion of a chance S fluctuation. A reported Monte Carlo zero is not
a probability zero (`results/analysis/echo_values.txt:11`).

**The section correlation cannot be used as printed.**
`work/tmp/echo_vs_skip_rate.py:26-31` estimates avoidance as

    (doublets / rune_count) * q/(1-q), with q fixed,

not `1/29 - doublets/transition_count`. Its denominator is rune count rather than
transition count. It appends only sections with eligible pairs (lines 28-30),
while section 0.10 has none (`work/tmp/echo_vs_skip_rate.txt:5`). Therefore there
are eight contributing sections, not the printed nine. Lines 38-40 divide a
sample covariance by population standard deviations, multiplying Pearson's r by
`m/(m-1)` for `m` contributing sections. The reported r=-0.38 is at
`work/tmp/echo_vs_skip_rate.txt:12`; a corrected, consistently defined value is
**unknown** here. Recompute both the estimator and its uncertainty; do not just
rescale the printed rounded r. A fixed-q estimate based on surviving doublets
also assumes the very collision mechanism under investigation. At a common
denominator, the fixed-q estimator is a positive multiple of the doublet rate,
whereas the deficit estimator is a constant MINUS that rate: their correlations
with any echo-rate vector have opposite signs by algebra. The old negative
correlation is therefore not a direct test of the deficit-rate co-movement in
the question.

The rate match is compatible with H but is not a site identification. Eligible
lag-6 positions are a subset of all output positions; all-book avoided counts
and within-word echo counts must not be equated without this eligibility mask.

## 1. Define the rule BEFORE asking for exact counts

All arithmetic is in F_29. Define `I(x)=x`, `T(x)=24-2x`. At output position i let
`a=C_(i-1)` and `p_i` be the current plaintext rune. A fresh attempted cipher rune
is `X_i=p_i+K_j`. H alone does NOT specify its conditional probability law.
Flat observed unigrams do not imply an iid pad or conditional uniformity. Exact
layout-only means below therefore explicitly use the unread-iid-pad reference
model; they are not universal predictions for every possible Cicada keystream.
An independent coin with probability q attempts repair if
`X_i=a`. No repair coin is used otherwise. At a section's first rune simply emit
its ordinary uniform candidate; section seams are not tested.

For each `d in {1,...,8}`, `g in {I,T}`, define the following **primary 32 rules**:

| Label | Repair when the source is in the SAME word | Key after repair | Plaintext after repair |
|---|---|---|---|
| `I_d, spend` | emit `C_(i-d)` | j+1 | i+1 |
| `T_d, spend` | emit `T(C_(i-d))` | j+1 | i+1 |
| `I_d, hold` | emit `C_(i-d)` | j | i+1 |
| `T_d, hold` | emit `T(C_(i-d))` | j | i+1 |

Ordinary emission always consumes the attempted key. In the **raw** primary
family a substitute equal to a is allowed: that repair attempt simply fails to
avoid a doublet. It must not be counted as a successful avoidance.

Outside source eligibility, a repair emits an auxiliary uniform rune other than
a. This is a specified fallback, not a key redraw. It accounts for the global
anti-repeat rule even in short words. The layout is the OBSERVED ciphertext word
layout; it is not assumed to be English plaintext boundaries (the blind spot in
`docs/NEGATIVE_SPACE.md:12-16`). The source of the fallback randomness in Cicada
is unknown.

The fallback is substantive. If a lag-6-only rule instead leaves collisions
untouched wherever its source is unavailable, then, even with perfect repair at
all eligible targets, expected surviving doublets are at least
`(12947-1290)/29=11657/29`, versus the recorded 86. The two denominators come from
`results/analysis/cicadanotebook_checks_2026-10-17.txt:9,36` and
`results/analysis/echo_position.txt:22`. This is a mathematical event-budget bound
under uniform fresh attempts, not a newly controlled empirical exclusion.

A separately labelled **guarded sensitivity family** uses the same fallback
when `g(C_(i-d))=a`. It changes the output law. It is not silently substituted
for the raw model; the calibration scans both and pays for that choice.

Three predeclared two-tap sensitivity rules choose `I_5` with probability
`w in {1/4,1/2,3/4}` and `T_6` with probability `1-w` on a repair. A chosen tap
which is not yet available uses the fallback. No S-specific branch is fitted.
These are six additional physical rules after the spend/hold choice. They are
not claimed to be derived solutions.

q is a model parameter, not automatically the observed doublet deficit. The
human-run tables use the explicit rational design value `q=81/100`, motivated
by the reported enforcement estimate (`docs/NEGATIVE_SPACE.md:22,82`). Raw
substitutions can fail to avoid a doublet, so this choice must subsequently be
checked against observed doublets, not treated as an exact fit.

### Key accounting is not a cosmetic option

For spend, an unread independent uniform pad gives `X_i` uniform conditional on
all past outputs, for any plaintext independent of the unread pad. The following
sections give exact predictions under that assumption.

For hold, a collision has revealed

    K_j = C_(i-1) - p_i.

If the next ordinary attempt reuses it,

    X_(i+1) = C_(i-1) + (p_(i+1)-p_i).                         (1)

Hence its law depends on plaintext differences. A constant plaintext and an iid
uniform plaintext give different forecasts under the SAME layout and rule.
**Layout-only numerical predictions for hold are unknown, not equal to spend.**
If plaintext too were iid uniform, it would mask the reused key and restore the
fresh-candidate law; that is not an English-plaintext assumption.

'No EXTRA advance' after already consuming the colliding draw is different from
holding the draw. Discarding zero or one additional unread iid pad value has the
same ciphertext law. Reusing the already observed value does not. If a null
instead consumes neither plaintext nor key, it is an insertion, not this H.
The previous `work/independent/echo_nulls.py` models such output-only nulls and
is **not** a test of the substitution family defined here.

## 2. Exact one-step law and conditional forecasts: all templates

Write `rho=q/29`, `delta=(1-q)/29`, `u=(1-delta)/28`, and
`lambda=delta-u=-q/28`. The baseline uniform-off-diagonal anti-repeat kernel is

    K0(y|a) = u + lambda * 1[y=a].                            (2)

It has doublet probability delta. For an eligible raw tap with `R=g(C_(i-d))`,

    Kraw(y|history) = 1/29 + rho*(1[y=R]-1[y=a]).             (3)

Outside eligibility use K0. Formula (3) is normalized and nonnegative for
`0<=q<=1`, including R=a. The guarded version equals (3) for R!=a and K0 for R=a.
For any test relation f, source b=C_(i-l), and any fixed position/rune mask M,

    E[1(C_i=f(b)) | history] = K(f(b)|history).               (4)

Relative to K0 at the SAME history, the raw eligible drift is

    rho * (1[R=f(b)] - 1[f(b)!=a]/28).                       (5)

For guarded taps multiply (5) by `1[R!=a]`. Per-source-rune predictions multiply
by `1[b=x]`; per-target-rune predictions by `1[f(b)=x]`; word-position predictions
by the desired deterministic layout mask. Summing (4) gives an **exact predictable
compensator along the observed history**. It is not the unconditional expected
count of a newly generated whole book; do not label it as one.

For hold replace `1/29` by the unknown conditional attempted-rune law nu_i:

    Khold(y|history) = nu_i(y) + q*nu_i(a)*(1[y=R]-1[y=a]).   (6)

The fallback/guard replace the final point mass by uniform-off-a when applicable.
A hidden-state recursion must propagate the plaintext state, retained key and
output history to determine nu_i. For a correlated/nonuniform key source, nu_i
is also needed in the spend case. Equation (1) shows why it cannot be eliminated
from the assumptions supplied in the question. This is an exact parametrized
prediction, not a missing calculation which layout alone could fix.

## 3. Exact UNCONDITIONAL within-word counts, without 29^8 histories

This section applies to raw spend rules and the fixed two-tap mixtures, under
unread iid uniform pad values. It includes all secondary echoes, overwrites of
would-be natural hits, failed repairs, and word-prefix effects. No first-order
'echo rate times eligible pairs' approximation is needed.

### 3a. A small group and closed two-point recurrence

T has fixed point 8, and `T(x)=8-2*(x-8)`. Its order is 28:
`(-2)^14=-1`, `(-2)^4=16!=1` mod 29, excluding proper divisor orders of 28.
At each local word position the marginal of C is exactly uniform. This follows
inductively from (2)/(3), since both taps are bijections and their sources have
uniform marginals.

For j<i within a word, represent the pair distribution by a vector W[j,i] of
length 28:

    P(C_j=x,C_i=y) = 1/29^2
       + (1/29) sum_h W[j,i,h] * (1[y=T^h(x)]-1/29).        (7)

Set `W[j,j]=e_0`. If a parent precedes j, use
`W[j,parent,h]=W[parent,j,(-h mod 28)]`. Let S shift the vector by one exponent.
For one tap at local position i,

    i<d:   W[j,i] = lambda * W[j,i-1]
    i>=d:  W[j,i] = -rho*W[j,i-1] + rho*S^e W[j,i-d],      (8)

where e=0 for I and e=1 for T. Induction through the actual local positions gives
ALL two-point probabilities. Negative coefficients are algebraic coefficients,
not negative transition probabilities.

For a fixed mixture with tap weights v_t and active total
`s_i=sum_t v_t*1[i>=d_t]`, the exact recurrence is

    W[j,i] = (lambda+rho*s_i/28)*W[j,i-1]
             + rho*sum_(active t) v_t*S^(e_t)W[j,i-d_t].   (9)

Unused repair weight uses the fallback. The guarded kernel contains a product
of past-rune indicators and is not covered by this two-point closure. Its
conditional forecasts remain exact via (4); unconditional guarded counts are
**unknown** here without a higher-order calculation or simulation.

### 3b. Counts at EVERY within-word lag, position, and source rune

Let n_p be the number of real words with length greater than p. Set
`N_l=sum_words max(length-l,0)`. Then `n_p=N_p-N_(p+1)` and a pair at earlier
position j and lag l occurs n_(j+l) times. Initial uniformity at word start is
sufficient; independence between different words is NOT required for these means.
Only the longest local word prefix needs calculation once per rule.

Let `z=sum_h W[j,j+l,h]`. For f=T^r, r=0 for equality and r=1 for T:

    P(C_(j+l)=f(C_j)) = 1/29 + (28/29)*W[j,j+l,r].          (10)

Thus the exact aggregate excess above an iid uniform baseline is

    Delta_(l,r) = (28/29)*sum_j n_(j+l)*W[j,j+l,r].         (11)

For a specified source rune x, the exact per-pair probability is

    x=8:    (1+28*z)/29^2
    x!=8:   (1+29*W[j,j+l,r]-z)/29^2.                      (12)

Multiply (12) by n_(j+l) for its expected count, and subtract n_(j+l)/29^2 for
its iid excess. Group by any desired earlier/target position, word length or
section by replacing n_p with the corresponding real-layout count. Per-target
rune tables follow by x=f^(-1)(target). Full source/target joint cells follow
(7), not an assumption of independence.

Against the *anti-repeat Markov baseline* rather than iid, subtract
`W0[j,j+l]=lambda^l e_0` in (11)/(12). These are distinct from the stored empirical
shuffle means in Section 0. The human report labels both baselines explicitly.

The real pair totals for l=1..9 are

    10060,7247,4882,3237,2105,1290,731,388,201

(`results/analysis/within_word.txt:5-13`); l=10..12 are `92,35,10`
(`results/analysis/skeleton5.txt:14-16`). Consequently the counts of FIRST eligible
targets for the eight taps, n_d, are the following exact differences:

| d | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| n_d | 2813 | 2365 | 1645 | 1132 | 815 | 559 | 343 | 187 |

All entries are derived from `within_word.txt:5-13`, not simulations. At each
first target (earlier position zero), the exact excess versus iid chance is

    I_d: (28/29)*rho*(1-lambda^(d-1)),
    T_d: (28/29)*rho.                                      (12a)

Multiply by n_d for its exact first-position count excess. To compare I_d with
K0 instead, additionally subtract `(28/29)*lambda^d`; T_d's aggregate K0 mean is
already chance. At design q=81/100, T_d's excess in (12a) is exactly
`567/21025` per first-eligible pair: a derived prediction, not a fitted LP2 echo
measurement. All later positions and all off-lags use (8)-(12), not (12a).

The position counts are independently reported in
`results/analysis/echo_position.txt:6-10,24-28`. Beyond the printed pair totals,
actual word lengths and numerical predictions are **unknown** until the human
reads them with the gate. The program does not extrapolate a guessed maximum
length.

Equations (8)-(12), with e/d specified in Section 1, are the exact prediction
for EACH of the 16 raw-spend templates at EVERY within-word lag. The code writes
rational-number tables for all of them, not just the two selected observations.
The other 16 primary physical rules are explicitly marked `unknown: plaintext
law needed`, instead of fabricating hold-key forecasts.

For cross-word or cross-section questions: the same recurrence can be propagated
on the ordered global layout, allowing taps only within a word and resetting at
sections. Numerical cross-word predictions are **unknown** in the short gate;
they are not assumed exactly zero merely because the tap is word-gated. A tap
near a boundary can affect a future cross-boundary pair via ordinary transitions.

## 4. Which rules can reproduce BOTH observations?

### Exact restrictions, not post-hoc story fitting

The following population restrictions use the uniform-fresh-candidate reference
law of Section 3. Correlated-key or hold-key versions without a plaintext/key
law have **unknown** predictions, not these same restrictions by fiat.

* **All pure-copy spend rules I_d fail the lag-6 T mean:** their vectors have only
  exponent zero, so (10) gives exactly chance for every nonidentity T^r at every
  lag, even when equality is correlated. They can make lag-5 equality, not the
  observed T relation as a population effect.
* **I_1 is not an avoidance mechanism inside words:** it substitutes the very rune
  it was meant to avoid. The raw rule produces iid-uniform within-word doublets;
  the guarded version reverts to K0. The reported within-word doublets are 63 in
  10,060 positions (`results/analysis/within_word.txt:5`).
* **T_d has its primary forced relation at lag d**, not at all period-5-equivalent
  lags. Secondary correlations must be calculated by (8), not borrowed from the
  dead skeleton. T_6 is the natural single-tap candidate for lag-6 T, not evidence
  for lag-5 equality. Which finite-sample T_d profiles pass all counts is **unknown**
  until the gate tables and a calibrated goodness-of-fit test are evaluated.
* **No source-blind copy/T rule or fixed mixture singles out S in its population
  forecast.** All maps `x -> 8+s*(x-8)`, s!=0, commute with I/T, preserve uniform
  randomness and the collision test, and act transitively on the non-8 runes.
  The only algebraically distinguished rune is 8 (H), not 15 (S); indices are
  `work/lp.py:17-21`. Equation (12) makes the identical non-8 predictions explicit.
  Naming `2^(-1)=15` does not break this symmetry. A rune-specific branch, nonuniform
  base law, or chance fluctuation would be an additional assumption.
* Existing source-concentration plants give a lag-5 upper-tail frequency of 0.03,
  not a theorem of impossibility (`results/analysis/echo_values.txt:9-14`). Hence
  'no rule derives an S preference' is justified; 'all rules statistically excluded
  by S' is not.

### A new shared-position collision-budget constraint

The lag-5 pairs with earlier position >=1 end at exactly the positions eligible
for lag 6. Their observed count is `104-36=68`; their reported shuffle expectation
is `72.9-27.8=45.1`, so their excess is `22.9`. Adding the lag-6 excess gives
`22.9+35.1=58.0` at the SAME 1,290 targets. These are derived from
`results/analysis/echo_position.txt:4,6,22`; the expectations are rounded Monte
Carlo means, not exact parameters.

At one such target define

    b5=C_(i-5), b6=C_(i-6), A_i=1[b5=T(b6)].
    H_i(y)=1[y=b5]+1[y=T(b6)].

A single substitute can make both hits only when A_i=1. For ANY collision-only
one-substitute rule with a uniform fresh attempt, even one choosing its output
with arbitrary hindsight over the history,

    E[H_i(C_i)|history]
      = 2/29 + rho*(E[H_i(R)|repair,history]-H_i(a))
      <= 2/29 + rho*(1+A_i).                               (13)

This is an exact conditional inequality. The overlap opportunities A_i are
adjacent-T pairs at source positions, not a free coincidence parameter. Their
actual count is **unknown** in the cited logs; the report computes it. Replacing
A_i by 1/29 without checking is an approximation, not an exact prediction.

At design q=81/100, `rho*1290=104490/2900` repair attempts are available at these
shared targets, before lost hits and failed repairs. This fraction is derived
from (3) and the cited 1,290 targets. It is substantially below the observed
sum-excess 58.0 unless overlaps or a statistical fluctuation supply the difference.
A ratio-of-means comparison is NOT a controlled exclusion: proper uncertainty,
source selection, and old-hit losses still matter. The exact recurrence and
matched conditional null are supplied rather than asserting a new negative.

This also diagnoses the naive two-tap mixture: using essentially all the shared
position budget for T_6 leaves no independent budget to generate the additional
lag-5 excess there. Putting I_5 only at the sixth character instead would predict
a special word position, unlike the reported spread (`echo_position.txt:6-10`).
Allowing two outputs per collision, reusing a constrained key, or gating on S
changes the family and must be specified and controlled separately.

### The meaning of 'flat at lags 3,4,7,8'

Do not compare different maps. `results/analysis/skeleton5.txt:1,7-12,19-24` tests
T^(l mod 5), whereas the present primary tables test both I and T at **every**
lag. The broader affine scan is `results/analysis/lag5_affine.txt:1-11`.
For illustration, the dead skeleton's fitted predictions at lags 3/4 include
+62.1/+44.1 against +3.0/-1.1, and at lags 7/8 +14.5/+11.1 against +1.6/-1.1
(`results/analysis/skeleton5.txt:20`). Those are not predictions of a sparse T_6
substitution. All secondary counts for the new family are given by (8)-(12).
No new statement that any rule has passed flatness is made here.

## 5. What a keyless discriminating test can and CANNOT establish

### Exact observational equivalence: collision causality is not identifiable

For the raw spend family define

    B_q(y|a) = (1-q*1[y=a])/(29-q).

Generate a Bernoulli E independent of the attempted plaintext/key, with probability
rho=q/29. If E=0 use B_q. If E=1 emit the tap substitute when eligible, otherwise
uniform-off-a. This independent-overlay generator has kernel

    (1-rho)*B_q + rho*W_i
      = 1/29 - rho*delta_a + rho*W_i,                      (14)

exactly the collision-substitution kernel, including its layout-dependent fallback.
The guarded family works too by taking W_i uniform-off-a when R=a.
Both mechanisms have the SAME parameters and the SAME full ciphertext law.
They differ in the unobserved event label 'a collision caused this'. No keyless
statistic, at any sample size, can separate these two generators. A test of size
alpha has power at most alpha against the identical law. Key advance into unread
independent values also cannot be recovered from this law.

Therefore the requested discriminator can test a **specified substitution kernel
against a specified no-echo null**, not prove 'echo sites ARE avoided collisions'.
The human gate checks (14) exactly; it does not pretend a synthetic method label
is recoverable. Hold-key correlations can differ via (1), but require a plaintext
law before a likelihood or power claim exists.

### A stronger budget falsifier: give the repair rule ALL history-dependent freedom

Equation (13) can be turned into a finite-sample test without pretending the
predictable count is an unconditional mean. For lambda>0, write

    H_i(y)=1[y=b5]+1[y=T(b6)],    m_i=1+A_i.
    B_i(lambda) = (27+2*exp(lambda))/29,         A_i=0,
                  (28+exp(2*lambda))/29,        A_i=1.
    D_i(lambda) = B_i(lambda)
       + (q_max/29)*(exp(lambda*m_i)-exp(lambda*H_i(a))).   (17)

For ANY single collision-only substitute, even an adversarial history-dependent
one, and repair probability <=q_max,

    E[exp(lambda*H_i(C_i)) | past] <= D_i(lambda).

Use q_max=1 so no fitted enforcement parameter is needed. The product of
`exp(lambda*H_i(C_i))/D_i(lambda)` over the predictable eligible targets is a
nonnegative test supermartingale. Averaging those products for the PREDECLARED
lambda values `{1/16,1/8,1/4,1/2,1}` is also an e-value. This pays for arbitrary
choice of the repair output R in the bound, rather than fitting two tap rates
and then calling the fit a control. It is stronger than a generic bounded-mean
inequality because it retains the actual two possible target values and the
old collision hit H_i(a).

The two tested lag/maps were themselves selected on LP2. To cover the logged
choice among all affine maps at all eight lags for EACH target, conservatively
divide this selected-pair e-value by `M=(8*28*29)^2`. Then flag a **budget violation**
only if the adjusted e-value >=20 (design size <=0.05), equivalently the raw
value >=20*M. The finite family is a subset of the repair freedom already
allowed in (17). This corrects the listed lag/map choices, not an unlimited
history of unlogged analyses. It does not assume the S label was predeclared
because S is not used in this statistic.

Its actual LP2 value and power are **unknown** until computed. A small e-value
is not evidence for H. A violation would reject the uniform-fresh-candidate,
one-output collision budget, not the hold-key model, and not all stream ciphers.
Before writing the LP2 e-value, `tables` requires a legal T_6 collision plant not
to flag and a deliberately strong extra overlay to flag, on the same layout.
The positive uses a predeclared one-half extra-overlay probability: it checks
the implementation and threshold wiring, NOT sensitivity at LP2's effect size.
No long search is needed. All controls and failures are logged.
The conditional-randomization test below answers a different question: deviation
from a specified no-echo Markov null.

### A bounded, pre-stated kernel test with matched search freedom

Null H0: within each section, output is a uniform-off-diagonal first-order Markov
chain with unknown doublet probability delta_s. Condition on the OBSERVED number
D_s of doublets and section length n_s. Under H0 the following sampler is exact:
choose D_s transition locations uniformly without replacement; choose the first
rune uniformly; at marked locations repeat, elsewhere draw uniformly among the
other runes. This preserves the doublet deficit EXACTLY, unlike section shuffles.
It does not preserve all empirical rune counts or arbitrary higher-order language
structure; rejection is relative to this stated null only.

Statistic: max conditional-history log-likelihood improvement over K0(q=81/100),
scanning **all nonzero affine multipliers, all shifts, lags 1..8, raw and guarded**,
plus the three predeclared I_5/T_6 mixtures. Every null replicate repeats the same
whole scan; the primary I/T family does not get a free pass for its originally
selected T map. The original affine selection space is documented in
`results/analysis/lag5_affine.txt:1-11`.

With B=99 null replicates, use

    p_MC=(1 + count(null maximum >= observed maximum))/(B+1).

Pre-stated threshold: p_MC<=0.05 flags a **kernel deviation**, not a decryption,
not a winner of a joint-fit contest, and not collision causality. This threshold
and these replicate counts are design choices, not measured performance.

Controls before scoring LP2: unit identities including (7)-(14), a no-echo null
control through the same scan, and four independently generated collision plants
(two I_5 and two T_6) at the stated q and real layouts. Require at least three of
four plant tests to flag. That is a small-sample power gate, NOT an accurate power
estimate; report the individual failures. A fixed null-control realization that
flags fails the gate rather than being resampled. Failure means **underpowered
or incompatible control**, not an LP2 exclusion. The raw-spend family is the only
physical key mode calibrated by this gate.

A joint-fit/exclusion decision needs an additional **model-specific** predictive
check, not just rejection of H0: simulate the chosen rule on the real layout,
compare a simultaneous max residual over I/T counts at every tested lag,
position and source rune, and repeat model/rate selection identically in all
controls. Use all rune labels rather than treating S as predeclared. That joint
fit, its power, and which models survive it are **unknown** here; the short gate
must not label a significant kernel deviation as a model that reproduces BOTH
echoes. The exact mean table is the inexpensive input to that follow-up.

## 6. What the dead F and W3(a) variants do and do not exclude

### F replacement

The reported English reference has F frequency 0.0056 at its reported
`positions>=6`, with 1,013,590 such positions and quoted sd about 0.0001
(`work/tmp/frate_pos6.txt:1-4`). **Important mask defect:** its implementation uses
Latin LETTER positions in ASCII words, not Gematria Primus RUNE positions:
`work/tmp/frate_pos6.py:15-27`. It does not tokenize TH/ING/etc. The corresponding
rune-position F rate is **unknown**, and the corpora are unpinned local copies
(the source says so at line 1). Do not turn its binomial standard error into an
unconditional exclusion of LP2 plaintext.

Under the benchmark's own letter/corpus assumptions it disfavors the event budget
of 'only late plaintext F positions are overwritten', compared with the reported
echo excess rate 0.0272 +/- 0.0047 (`work/log/phase11_review.md:14-15`). A valid
rune-level causal-count bound needs the matching rune mask and plaintext law;
independent accidental echo hits must also be separated from causal overwrites.
The original '>4 sd' wording should not be strengthened here.

This does NOT exclude a collision trigger, other plaintext statistics/languages,
ciphertext-F conditions, key retention, insertions, or output-history substitution.
Also the small solved keyed sample reports F at eligible RUNE positions
3/73=0.0411 (`work/tmp/echo_vs_skip_rate.txt:15-16`; implementation
`work/tmp/echo_vs_skip_rate.py:47-58`): the corpus extrapolation is not a universal
law about every possible LP plaintext. It is not a proof from the alphabet alone.

### Previous-rune twist W3(a): R=T(C_(i-1)), NOT T(C_(i-6))

If a lag-6 hit is causally produced by W3(a), bijectivity gives

    C_i=T(C_(i-1))=T(C_(i-6)) => C_(i-1)=C_(i-6).           (15)

The recorded intersection is 3 of the 80 lag-6 hits
(`work/tmp/w3_sharp_test.txt:1-3`). The source script says approximately ALL 80
should satisfy this (`work/tmp/w3_sharp_test.py:1-4,28-33`); that is too strong:
accidental background hits need not. The correct sharp statement is that **at
most three of those recorded hits can be direct causal W3(a) outputs**. That
cannot serve as the intended direct explanation of the reported excess 35.1
under the otherwise-null background. No assumption that all observed hits are
causal is needed.

For a fresh uniform candidate, its exact conditional drift for the T-at-6 test,
relative to an unmodified uniform candidate, is

    rho * (1[C_(i-1)=C_(i-6)] - 1[C_(i-1)=T(C_(i-6))]).    (16)

Only 67 of the 1,290 eligible histories meet the first condition
(`work/tmp/w3_sharp_test.txt:3`); the second count is **unknown** in those logs.
The first term alone gives the upper predictable contribution `rho*67`, not
`rho*1290`. Directly substituting the rune SIX back has no condition (15), so
this test does not kill T_6. Nor does it kill arbitrary collision-dependent
rewrites, future effects of retained keys, or latent non-null background laws.

Two additional audit caveats: the 'following echo in-word' lines of the W3 script
check that the target belongs to SOME word, not the SAME source word
(`work/tmp/w3_sharp_test.py:40-46`); and the nearest-doublet loop compares a source
index rather than its echo target and includes section seams (lines 49-58).
Do not build a new discriminator on those secondary reported quantities without
correcting their masks. The primary intersection (15) uses genuine same-word
pairs and does not have that particular mask problem.

## 7. Outcome and stop rule

The finite family has substantive, computable constraints; it is not a free
three-rate restatement. A one-for-one substitution does not itself insert a rune
or explain a word-length excess; plaintext boundaries and any length-changing
layer remain separate unknowns. But there is currently **no established rule which
reproduces BOTH echoes, S concentration and the full off-lag profile**. The exact
raw-spend tables are computable cheaply from real word lengths; hold-key numeric
forecasts and guarded unconditional counts need additional assumptions/calculation.
The strongest new discriminators are the shared-position budget/overlap motif,
the H-versus-S symmetry, and the exact conditional-history likelihood. None
recovers a key or plaintext. If controls fail or the short time budget expires,
stop and return the log; do not expand to an overnight search.
