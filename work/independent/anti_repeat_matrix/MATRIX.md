# The misspecification matrix: what is calculable, and what is unknown

**No experiments have been run. Nothing in LP2 is solved.** Evidence labels R,
I, B, S/C, N and A refer to the file:line sources in `CATALOGUE.md` §0. All other
numbers below are derived from those inputs or explicitly chosen benchmark
settings, not new empirical measurements.

## 1. Do not equate four different things

1. A transition graph can REPRESENT a pointer path.
2. The path can remain in a finite score-pruned BEAM.
3. The resulting decoded symbols can retain plaintext SIGNAL.
4. A search can detect that signal above its selection-matched NULL.

Only the first is fixed by pointer rules alone. The other three depend on the
key sequence, plaintext, pruning, early abort, offset search and emission model.
**Actual expected beam-aligned run lengths and detection powers for unmeasured
cells are unknown.** They cannot be deduced from R and the planted-score range.

A counterexample to universal IoC loss: if K_j=j mod Q, a persistent pointer error
d gives p'_i=p_i-d, a fixed relabelling with IDENTICAL IoC. A structureless wrong
pad can instead destroy that signal. Flat key marginals do not distinguish those
cases. Conversely M06 can have the RIGHT pointer everywhere but corrupt some
plaintext symbols. M09 can have the RIGHT pointer everywhere but the WRONG
emission variable at essentially every position.

The tables below therefore give a precisely defined **reference reset-oracle
phase-prefix length**, not a fictitious measured power matrix. Before the first
avoided-collision site t, set the decoder's next-key pointer and previous-rune
reference equal to truth. Ask whether its UNPRUNED transitions can end that site
at the correct next-key pointer, and continue without ANY intervening phase error.
Stop at the first mismatch; later resynchronization is not counted. No actual
score/prune decision is made. A zero means no uninterrupted continuation from
that aligned state, NOT no possible later recovery or no detectable IoC.

The reference also treats observed word/break masks as EXOGENOUS ciphertext
formatting, not an outcome of an English word-length/insertion process. If those
boundaries are generated jointly with the null locations, their conditional law
is **unknown**; the geometric fixed-mask average is not its posterior prediction.

This reset assumption is consequential for wrong edge/layout readers, which may
already have misaligned before t. Start-offset searches can absorb a leading
constant displacement too. The provided numerical generator labels the reset
explicitly and does not turn it into full-search power.

## 2. The actual repository decoder arcs

Use forward key direction, multiplier absorbed into K, default clock=none, no
self-key G guard and no custom P collision array unless explicitly named. The
flags use valid full-window L/B layout data; their invalid-input fallback is not
silently substituted. Clock's default and transformations are at
`work/kscreen/src/main.rs:89-104`; P/G/S input meanings at `:119-138`. From current key j, observed y, previous comparison a:

**Skip S** (S/C sources):

    emit y-K_j;     next j+1; always available.
    emit y-K_(j+1); next j+2; require (y-K_(j+1))+K_j=a.
    emit y-K_(j+2); next j+3; require BOTH earlier candidates equal a.

**Coin C:**

    emit y-K_j;     next j+1 if y!=a, else next j+2.
    emit y-K_(j+2); next j+3; require (y-K_(j+2))+K_j=a.

The extra branch is still tested at an observed doublet: a failed repair may
consume the longer path. Neither graph has a q parameter or a probabilistic
skip/keep penalty. Mis-specifying q ALONE does not delete a represented path.
S supports two discarded collision draws at one site; it is not a single-path
'always advance once' decoder. The actual beam can nevertheless drop a supported
path (S/C pruning sources).

N1/N2 are flags composed with EITHER S or C, not two additional anti-repeat
models. They omit their deterministic edge rune, consume no key, and retain the
last SCORED previous value (N sources). A1/A2 add their deterministic pre-advance
then use S or C unchanged (A sources). Thus the requested flags give **ten**
concrete decoder configurations, with no N+A combinations assumed calibrated.

## 3. Bare S/C: formula plus derived numbers

Let R be the number of outputs remaining AFTER site t. Define

    G_R(h) = sum_(r=1..R) (1-h)^r
           = (1-h)*(1-(1-h)^R)/h,  h>0;   G_R(0)=R.

If the post-event phase is retained with probability g and each subsequent
output independently preserves it with probability 1-h, expected reset-oracle
length is g*G_R(h). All independence statements here use the catalogue's fresh
uniform-pad reference (M04's numerical variant additionally uses iid plaintext).

| Truth | S: post-first-avoid length | C: post-first-avoid length | Signal interpretation |
|---|---|---|---|
| M01 skip-once | R | 0 | S has complete path support |
| M02 checked until-different | `(1-Q^-2)*G_R(rho/Q^2)` | `((Q-1)/Q^2)*G_R(1/Q-(Q-1)*rho/Q^2)` | S misses only the longer retry tail |
| M03 coin | `G_R((Q-1)/Q^2)/Q` | R | S usually breaks immediately at the first repair |
| M04 hold key | 0 | 0 | Neither graph can consume zero keys at this event |
| M05 +2 only on repair | `G_R(rho)/Q` | `G_R(kappa)` | C survives repairs but fails at kept initial collisions |
| M06 spend-key substitution | R | `G_R(delta)` | Local symbol errors; NOT S pointer drift |
| M07 output-only null | 0 | 0 | Zero-key event absent from both bare graphs |
| M08 plaintext adjustment | R | `G_R(delta)` | Local symbol errors; NOT S pointer drift |
| M09 feedback | R | 0 | Phase table only; ordinary emissions are not plaintext |
| M10 native step domain | not applicable | not applicable | No would-be mod-Q collision event exists |
| M11 word advance | layout formula in §4 | layout formula in §4 | Matching A1+S has length R |
| M12 word+break advance | layout formula in §4 | layout formula in §4 | Matching A2+S has length R |

Useful unbounded-tail benchmarks derived from R (finite windows are shorter):

* For M03 vs S, `g=1/29`, `h=28/841`, so `g*G_infinity(h)=813/812`, about
  **1.001** output. The lucky coin value can equal the colliding key; setting the
  compatibility probability to exactly zero would be wrong.
* For M05 vs S, the limit is `365010/303137`, about **1.204** outputs.
* For M05 vs C, `G_infinity(kappa)=10453585/59379`, about **176.05** outputs.
  This is partial support, not complete blindness at the first repair.
* For M06/M08 vs C, `G_infinity(delta)=12861/86`, about **149.55** outputs.
* M02 vs S has unsupported-tail hazard `10453/315764383`, about **0.0000331**
  per output; its immediate post-repair support is `840/841`. In a design window
  of 300 outputs, the union-bound probability of at least one too-long retry is
  at most `300*10453/315764383`, below **0.010**. This is path truncation only,
  not a measurement of beam pruning.
* M02 vs C has an unbounded reset-oracle mean about **0.96** outputs, given by
  the exact formula in the table. The gate calculates the decimal, not a new run
  of the cipher engine.

All fractions above follow from catalogue parameters derived from R. No new
measurement or claim of a new exclusion is hidden in this table.

## 4. Complete matrix, including the edge/layout readers

The following coefficient tables give a numeric rational function for EVERY
truth/decoder pair. The layout itself is deterministic, not a rate to guess.
Let W_i and n_e(i) be real word-start and edge-null flags, and B_i the MULTIPLICITY
of exported break entries at position i (A/N sources). Repeated line/page entries
must be preserved (`work/kscreen/export.py:39-50`), not converted to a boolean. Put D_0(i)=0, D_1(i)=W_i, D_2(i)=W_i+B_i. For a scalar channel let F_i
be phase-preservation probability at a future site and g_t its conditional
post-first-avoid preservation probability. Then

    L_m,d(t) = g_t * sum_(r=1..R) product_(k=1..r) F_(t+k).       (1)

A backward recurrence evaluates it without enumerating paths:

    V_N=0;  V_i=F_i*(1+V_(i+1));  L(t)=g_t*V_(t+1).            (2)

For stateful rows replace F by the substochastic transition matrix below and
multiply `(1+V_next)` as a vector. These are exact reference expressions, not a
geometric approximation to arbitrary word lengths.

### 4a. M01/M09/M11/M12: once-kernel with a layout offset

Let h=A_truth(i)-D_decoder(i), with A_truth respectively 0,0,W,W+B. Entries are
PHASE support; they may allow a wrong current symbol with a correct next pointer.

| h | F_S(h) | F_C(h) | g_S(h) at an avoided collision | g_C(h) |
|---|---|---|---|---|
| -2 | 0 | 0 | 0 | 0 |
| -1 | alpha | rho | 1 | 1 |
| 0 | 1 | `(Q-1)/Q+alpha/Q` | 1 | 0 |
| 1 | `1/Q` | `kappa+alpha/Q` | `1/Q` | `1/Q` |
| 2 | `(1-alpha)/Q^2` | `(1-alpha)/Q` | 0 | 0 |

Other offsets: zero for this catalogue. A hidden layout draw need only
coincidentally have the colliding value for a skip branch to absorb it. Thus
'wrong layout means mathematically no chance of alignment' is too strong.
Repeated coincidences are rare, and the measured crossed controls remain the
proper empirical power evidence.

### 4b. M02/M03/M05: decoder pre-advance d=D_decoder(i)

Define `P_m=q0*(Q-1)/Q^m` for m>=2; these are M02's repaired total-draw masses.

| Truth | d | F_S | F_C | g_S | g_C |
|---|---|---|---|---|---|
| M02 | 0 | `1-rho/Q^2` | `(Q-1)/Q+P_3` | `1-Q^-2` | `(Q-1)/Q^2` |
| M02 | 1 | `P_2+P_3+P_4` | `P_2+P_4` | `1-Q^-3` | `(Q-1)*(Q^-1+Q^-3)` |
| M02 | 2 | `P_3+P_4+P_5` | `P_3+P_5` | `(1-Q^-3)/Q` | `(Q-1)*(Q^-2+Q^-4)` |
| M03 | 0 | `1-(Q-1)/Q^2` | 1 | `1/Q` | 1 |
| M03 | 1 | `kappa+alpha/Q` | `alpha/Q` | `1/Q` | 0 |
| M03 | 2 | alpha | rho | 1 | 1 |
| M05 | 0 | `1-rho` | `1-kappa` | `1/Q` | 1 |
| M05 | 1 | `alpha/Q` | `alpha/Q` | `1/Q` | 0 |
| M05 | 2 | alpha | rho | 1 | 1 |

All entries are exact rational numbers with Q/parameters supplied in the
catalogue. For M03/M05, d>=3 gives zero. For M02 and ANY d>=1, the general rule is
`F_S=sum(P_m,m=d+1..d+3)`, `F_C=P_(d+1)+P_(d+3)`; replace P_m by
`(Q-1)/Q^(m-1)` for conditional g. Thus coincident word/line/page advances are
handled without assuming a maximum B multiplicity. The gate independently
enumerates decoder-reachable draw prefixes and tests the general formula at the
explicit fixture advances d=0..4; infinite tails are summed geometrically, not
silently dropped.

### 4c. M06/M08 and the positive-key-consumption N columns

For M06/M08, at d=0, `F_S=1`, `F_C=1-delta`, and both g=1. For d>0 both F and g
are zero: truth consumes one key and the incorrect pre-advance cannot be undone.

For N1/N2 on ANY positive-consumption row (all except M04/M07/M10), use its bare
S/C coefficients with decoder pre-advance zero, then

    F_i <- (1-n_e(i))*F_i;    g_t <- (1-n_e(t))*g_t.           (3)

Thus the first forced deletion of a real key-consuming symbol ends this strict
phase prefix. Equation (3), not a guessed average word length, fills those cells.

### 4d. M04 hold key under N1/N2: two comparison states

These numeric matrices use the explicitly iid-plaintext reference; English
values remain **unknown**. States are E (decoder's comparison equals the last
visible output) and U (unequal). A matched masked repair begins in U.

At a forced-null position, for either S or C:

    T_null = rho * [[0,1], [1/(Q-1),(Q-2)/(Q-1)]].

At an unmasked position:

    T_S = [[1-rho,0], [1-rho,0]],
    T_C = [[(Q-1)/Q,0], [1-rho-1/Q,0]].

If the first repair is not at a forced-null position, g=0. If it is, start the
post-event recurrence in U. A correct pointer does not mean the erased original
plaintext symbol was recovered.

### 4e. M07 output-only null under N1/N2

For S, states are NORMAL and PENDING, r=qN/Q. A matched first null begins PENDING.

    T_unmasked = [[1-r,0], [1,0]],
    T_masked   = [[0,r], [0,0]].

Require n_e(t)=1; otherwise g=0. For C the post-first-null prefix is always zero:
the retry emits the last SCORED rune, so C incorrectly spends a coin key there.
Masking that retry also fails, since truth consumes its key at the retry.
Bare/A decoders have no zero-key first-null transition, hence length zero.

### 4f. Explicit ten-column lookup

`U_r(mode,d)` means (1) with row r's coefficients and pre-advance profile d.
`N_er(mode)` means (3); `H_e`/`P_e` mean the stateful hold/null recurrences.
`D_r(mode,d)` means the M06/M08 rule. Every symbol refers to specified rational
coefficients above; none means that actual beam power has been measured.

| Truth | S | C | N1+S | N1+C | N2+S | N2+C | A1+S | A1+C | A2+S | A2+C |
|---|---|---|---|---|---|---|---|---|---|---|
| M01 | R | 0 | N_1r(S) | N_1r(C) | N_2r(S) | N_2r(C) | U_r(S,D1) | U_r(C,D1) | U_r(S,D2) | U_r(C,D2) |
| M02 | bare table | bare table | N_1r(S) | N_1r(C) | N_2r(S) | N_2r(C) | U_r(S,D1) | U_r(C,D1) | U_r(S,D2) | U_r(C,D2) |
| M03 | bare table | R | N_1r(S) | N_1r(C) | N_2r(S) | N_2r(C) | U_r(S,D1) | U_r(C,D1) | U_r(S,D2) | U_r(C,D2) |
| M04 | 0 | 0 | H_1(S) | H_1(C) | H_2(S) | H_2(C) | 0 | 0 | 0 | 0 |
| M05 | bare table | bare table | N_1r(S) | N_1r(C) | N_2r(S) | N_2r(C) | U_r(S,D1) | U_r(C,D1) | U_r(S,D2) | U_r(C,D2) |
| M06 | R | G(delta) | N_1r(S) | N_1r(C) | N_2r(S) | N_2r(C) | D_r(S,D1) | D_r(C,D1) | D_r(S,D2) | D_r(C,D2) |
| M07 | 0 | 0 | P_1 | 0 | P_2 | 0 | 0 | 0 | 0 | 0 |
| M08 | R | G(delta) | N_1r(S) | N_1r(C) | N_2r(S) | N_2r(C) | D_r(S,D1) | D_r(C,D1) | D_r(S,D2) | D_r(C,D2) |
| M09 | R, emission wrong | 0 | N_1r(S) | N_1r(C) | N_2r(S) | N_2r(C) | U_r(S,D1) | U_r(C,D1) | U_r(S,D2) | U_r(C,D2) |
| M10 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| M11 | U_r(S,0) | U_r(C,0) | N_1r(S) | N_1r(C) | N_2r(S) | N_2r(C) | R | 0 | U_r(S,D2) | U_r(C,D2) |
| M12 | U_r(S,0) | U_r(C,0) | N_1r(S) | N_1r(C) | N_2r(S) | N_2r(C) | U_r(S,D1) | U_r(C,D1) | R | 0 |

For M10 one can instead measure until the first ZERO STEP; its bare phase-prefix
hazard is delta, with mean waiting time `12947/86`, about **150.55** outputs.
That is a different event, and the ordinary emission/domain is already wrong.

The human generator evaluates (1)-(3) on the real section-start word/break masks
and writes numerical entries, conditional on each event position. Its compact
summary also averages over a geometric first-event time **while resetting the
oracle before that event**, explicitly ignoring earlier decoder errors. That is
a defined diagnostic, not the unknown actual expected beam run.

## 5. Signal loss: exact formulas where assumptions permit, not fake power

### The first failure is not universally at a mean of Q runes

For M01, M02, M03, M05, M06, M08, M09, M11 and M12 the reference probability of a
successful avoided collision per checked output is rho. Thus mean wait is
`1/rho=375463/10453`, about **35.92**, not Q. In a design 300-check calculation,
would-be initial collisions average `300/29`, about **10.34**, and net repairs
average `300*rho`, about **8.35** (all derived from R). A window with no comparison
before its first rune has one fewer checked position. M07 has a different
attempt/output denominator, and M10 has no such collision event.

### Independent-uniform wrong tail: illustrative EXACT mixture calculation

Suppose m decoded symbols are a correct fixed prefix and the other N-m are iid
uniform, independent of that prefix. Then

    E[IoC_N | prefix] = 1 + m*(m-1)/(N*(N-1))*(IoC_m-1).    (4)

Using the design N=300 and the benchmark IoC_m in I as an ILLUSTRATION:

| Assumed good prefix m | Exact attenuation factor | Illustrative IoC interval |
|---|---|---|
| 29 | 812/89700 | about 1.0054–1.0096 |
| 36 | 1260/89700 | about 1.0084–1.0149 |

These prefix lengths are design examples, not measured survivor lengths. A small
prefix need not have the full-reference IoC; that uncertainty is not removed by
plugging the benchmark into (4). For a geometric failure time, use
`E[M(M-1)]`, NOT `E[M]*(E[M]-1)`. If the first output is safe and subsequent
failures have hazard h, s=1-h,

    E[M] = (1-s^N)/h,
    E[M*(M-1)] = 2*s*(1-N*s^(N-1)+(N-1)*s^N)/h^2.           (5)

Equations (4)-(5) are a scenario calculation. A wrong adaptive beam is not an
independent-uniform tail, and resynchronization is omitted.

### Local spend-key substitution does NOT have the wrong-tail failure

For M06 with S's always-present ordinary branch, each plaintext rune undergoes
an independent channel: unchanged with probability 1-rho, shifted uniformly to
one of the OTHER Q-1 values with probability rho. Its unigram contrast contracts
by `f=1-Q*rho/(Q-1)=352063/362516`. For iid stationary plaintext the exact expected
IoC is

    1 + f^2*(I_plain-1).                                   (6)

This stationary channel calculation gives every output a preceding comparison;
a window with no comparison before its first output has a small boundary
correction. The benchmark range I would become about **1.566–2.000**, still above
its cited screen threshold, under these assumptions. This is not an executed plant or a
power guarantee, but it disproves 'one substitution necessarily loses the whole
remaining key alignment'. M08 has a fixed-shift channel instead. Its exact unigram change needs the
plaintext frequencies, but Cauchy-Schwarz gives a useful iid-reference bound:

    (1-2*rho)^2*(I_plain-1) <= I_adjusted-1 <= I_plain-1.

With I's benchmark range, this bounds M08's ordinary-path IoC to about
**1.535–2.060**, also above the cited screen threshold under this reference.
The lower bound, not a newly measured IoC, is derived from the same R-calibrated
rho. Neither local-error model warrants a blanket pointer-catastrophe claim.

For bigrams, with source joint frequencies B and error channel matrix A,
`B_decoded=A^T B A` and `E[score]=sum(B_decoded[a,b]*table[a,b])`. The true-key
mean alone cannot determine this. B, actual pruning loss and power are unknown
until a controlled reference is specified and tested.

### Bigram wrong-tail illustration, in the RIGHT units

Using the REPORTED benchmark means in B, the crude interpolation is

    score/N approximately -10.5 + (7.3+10.5)*m/N.            (7)

It neglects the bridge bigram and start-row effect. For the design N=300,m=36,
this gives -8.364 score units/rune, or about -0.8364 nominal nats/rune. This is
not a recalculated actual-score expectation. The repo's candidate threshold is
in native scaled units, not literal nats (`work/phpmt/bg.py:41,52-64`).

## 6. Build ranking: structural gaps versus partial support

1. **Hold-key repair, M04:** add a zero-key / one-plaintext transition whose
   inverse plaintext is a-K_j. First specify the repair emission and a fixed
   prior. English conditional nu/rate must be calibrated with the hold state;
   do not recycle the fresh-pad q calibration as a measured English fit.
   Require planted true-key recovery and same-freedom random-key controls before
   any search. This is a real missing transition, not an already tested edge null.
2. **Output-only collision null, M07:** test the mandatory a,R,a motif before
   building a decoder. The repo already reports flat nonadjacent coincidence
   rates (`PLAN.md:123`), so an exact controlled lag-two forecast is cheaper than
   a search. If that variant survives, build its pending state, with zero key AND
   zero plaintext advance, and a fixed-prior marginal likelihood. Do not reuse a
   free per-word maximum-IoC deletion beam: its null overfit is already measured
   (`work/kscreen/NULLEDGE.md:36-43`). Other null mechanisms are not thereby killed.
3. **Repair-only +2, M05:** cheap coin-graph modification: do not spend a coin
   on kept initial collisions. Existing C has substantial partial path support,
   so first measure crossed English plants rather than declare the old negatives
   void. The rates/limits in §3 quantify the mismatch under the reference law.
4. **M06/M08 inverse/error-aware scoring, only if a plant shows need:** S already
   has the correct key phase. Start with a crossed control of the unchanged
   engine. A new decoder is not justified merely by the word 'substitution'.

**Do not build again:** M01; M02's tiny retry tail without evidence of material
pruning loss; M03; M09 feedback; M10 step domain; M11/M12 deterministic layout
advances. Their matching graph/lane already exists. This does NOT mean every seed/hash
family has already been searched in every such domain: coverage is the product
of key family, kernel, layout and window, not the union of separate campaigns.
Feedback's library lane does not automatically validate ordinary seed-sweep
negatives against feedback; step-domain seed coverage likewise requires its own
controls and recorded scope. More keys, broader sweeps and GPU work do not by
themselves answer this misspecification question.

This ranking is structural, not a posterior probability ranking. Actual complete
crossed power values, including all priors, pruning and selection-matched nulls,
remain unknown. No existing negative is globally retracted on these formulas.
