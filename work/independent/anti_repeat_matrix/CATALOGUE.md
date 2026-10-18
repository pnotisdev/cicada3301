# Anti-repeat misspecification: concrete channels and pointer semantics

**UNEXECUTED / UNVALIDATED. Nothing in LP2 is solved.** No Python, build, test,
benchmark, simulation or cryptanalytic search was run to prepare this package. Only this new
folder is written. The existing collision-substitution package is imported by
the proposed human gate, not edited or executed by the author.

## 0. Evidence and scope

All empirical inputs below are from these locations; newly chosen constants
are explicitly design choices, and algebraic numbers are marked derived.

* **R:** 86 doublets in 12,947 transitions, excluding section seams:
  `results/analysis/cicadanotebook_checks_2026-10-17.txt:9,36`.
* **I:** reported planted IoC range 1.6–2.06 and screen threshold 1.40:
  `STATUS.md:19`. These are not guaranteed IoCs of a short surviving prefix.
* **B:** the score is a sum of **10 times** log odds, rounded and clipped, not
  literal nats: `work/phpmt/bg.py:41,52-64` and
  `results/analysis/true_key_score.txt:1`. The reported correct-key level near
  +7.3 score units/rune is about +0.73 nominal nats/rune, not +7.3 nats/rune
  (`results/analysis/true_key_score.txt:13`). Reported wrong-key level -10.5
  score units/rune: `work/phpmt/bg.py:8`, `docs/CAMPAIGNS.md:119`.
* **S/C:** actual forward transition graphs: `work/kscreen/src/main.rs:617-654`
  and `:774-794`; merge/prune/abort: `:658-694,798-803`. The bigram seed and
  hash lanes use the same pointer options, but different scoring/pruning:
  `work/phpmt/bg.py:79-135`, `work/hashscan/src/main.rs:420-519`,
  `work/prngx/src/main.rs:591-690`.
* **N:** deterministic final/initial null positions, invisible to the collision
  comparison and unscored: `work/kscreen/src/main.rs:190-235,532-540`.
* **A:** extra word and line/page advances: `work/kscreen/src/main.rs:237-268`;
  `work/kscreen/ADVSEP.md:23-40`. A word boundary coinciding with a break adds
  both advances, not just one (`ADVSEP.md:27-33`). The exporter preserves repeated
  B entries at a position (`work/kscreen/export.py:39-50`); line and page tokens
  must not be deduplicated by an independent layout reader.

There IS already some off-model power evidence, so 'no test exists' is too broad:

| Existing crossed control | Reported result | Source |
|---|---|---|
| True all-edge nulls, ordinary decoder, true offset | IoC 1.078 / 1.076 | `work/kscreen/NULLEDGE.md:67` |
| Same plants, matching null decoder | 1.670 / 1.667 | `work/kscreen/NULLEDGE.md:68` |
| True word advances, ordinary decoder, true offset | 1.097 | `work/kscreen/ADVSEP.md:79` |
| Matching word-advance decoder | 1.667 | `work/kscreen/ADVSEP.md:80` |
| Word-only decoder on word-plus-break plant | 1.106 | `work/kscreen/ADVSEP.md:83` |
| Old H8 null which SPENDS a key, unchanged decoder | 1.71 / 2.02 / 1.58 | `work/log/phase9_hyp.md:82-85` |

These are existing measured cells, not a complete matrix, and not new results.
The old H8 is not the key-retaining output-only null below. Also feedback and
step-domain lanes already exist; they must not be reclassified as untested merely
because the ordinary additive decoder cannot see them.

## 1. What must be specified to obtain a probability

Let a be the last visible output, p the current plaintext symbol, and j the next
logical key position. An ordinary attempt is X=p+K_j mod Q with Q=29. A repair is
triggered only by X=a. All repair coins below are independent auxiliary coins;
'spending a coin key' specifies its pointer cost, not a hidden threshold inferred
from that key. The repo's planter similarly spends that position but uses a
separate RNG coin (`work/kscreen/src/main.rs:1196-1202`).

For exact reference kernels, unread keys are iid uniform. This is an ASSUMPTION,
not a consequence of flat LP2 unigrams. It works for any fixed plaintext when
all attempted keys are fresh. For a retained, already exposed key, it does NOT:

    K_j=a-p  =>  next attempt = a+(p_next-p).

The hold-key row has an exact general kernel in terms of its attempted-rune law
nu. Its numeric calibration and matrix use an explicitly **iid-uniform plaintext
reference** to mask a retained key. Its English-plaintext calibration/power are
**unknown**. Matching a doublet mean is not proof of an English cipher.

Matching means here means expected transition fraction, not forcing every finite
sample to contain the observed count. The null-insertion channel needs its
stationary auxiliary-state initialization for an exactly stationary mean; a book
started in NORMAL instead has a calculable endpoint transient. No transient is
silently called an exact finite-book fit.

### Derived calibration constants (all derived from R, not measured anew)

    delta = 86/12947
    q0 = 1-Q*delta                 = 10453/12947
    q1 = Q*q0/(Q-1)               = 303137/362516
    qN = q0/(1+delta)             = 10453/13033
    rho = q0/Q                   = 10453/375463
    alpha = q1/Q                 = 10453/362516
    kappa = (1-q1)/Q              = 59379/10512964

q0 is about 0.8074; q1 about 0.8362; qN about 0.8020. q1 is larger because a single
redraw can itself collide. Setting every mechanism's repair probability to the
same approximate enforcement value would NOT match the same doublet rate.

For a fresh attempt define the sub-probability

    B_q(y) = 1[y!=a]/Q + (1-q)*1[y=a]/Q.

Let U_a be uniform on the Q-1 values other than a. Tables below specify the JOINT
kernel K(y,Delta j,Delta p,new state | old state), not just its output marginal.
Unless stated otherwise, Delta p=1, prev becomes the emitted y, and no other key
positions are consumed. No literal-F convention is assumed.

## 2. Catalogue: exactly twelve concrete mechanisms

### M01 — Checked skip-once

* Emit y with mass B_q1(y), Delta j=1.
* On a checked collision use K_(j+1) once, emit its candidate, Delta j=2.
  Joint repair mass is q1/Q^2 for EACH y, including y=a.
* Doublet mean: `(1-q1)/Q + q1/Q^2 = delta`.

This is probabilistic enforcement. An unconditional single redraw would have
rate 1/Q^2, not delta. A failed redraw is a doublet, but still spends its key.

### M02 — Checked skip-until-different

At the first collision keep it with probability 1-q0. With probability q0,
activate a strict loop drawing fresh keys until a different candidate appears.
There is no second repair coin once the loop is active.

* At Delta j=1 emit with mass B_q0(y).
* For each integer m>=2, emit any y!=a with mass q0/Q^m, Delta j=m.
* Doublet mean `(1-q0)/Q=delta`.

A genuinely unconditional 'until different' rule has ZERO doublets. It cannot
match R without missed checks or some other exception. The repo's skip planter
is another variant: it rechecks a coin at every collision and caps the retry loop
(`work/kscreen/src/main.rs:1189-1195`). Its graph still contains the M02 paths up
to the decoder's retry limit, but the planter is not literally M02.

### M03 — Spend a coin key on EVERY initial collision

* Noncollision y!=a: mass 1/Q, Delta j=1.
* Initial collision kept: mass (1-q1)/Q, y=a, Delta j=2. Used key is K_j;
  K_(j+1) is spent but does not encipher the symbol.
* Collision redrawn once: mass q1/Q^2 for each y, Delta j=3. Used key K_(j+2).
* Doublet mean delta, as in M01.

This is the repo's coin pointer convention. Enforcement probability alone is
not the defining difference from skip.

### M04 — Hold the colliding key, but advance plaintext

* Ordinary/kept emission y: mass `nu(y)*(1-q0*1[y=a])`, Delta j=1.
* Repair: mass `q0*nu(a)*U_a(y)`, Delta j=0, Delta p=1.
* The used colliding key is retained; a new plaintext symbol is attempted next.

The general doublet probability is `(1-q0)*nu(a)`. It equals delta only in the
stated uniform-attempt reference. For English with a retained key, nu and the
calibrated q are **unknown**. This is not an output-only null: plaintext advances.

### M05 — Advance by TWO extra keys only on a repair

* Mass B_q1(y), Delta j=1.
* On repair discard K_(j+1), encipher with K_(j+2): mass q1/Q^2 for each y,
  Delta j=3.
* Doublet mean delta.

Unlike M03, a kept initial collision spends only ONE key. Thus the coin decoder
matches repaired sites but gets the kept-collision pointer update wrong.

### M06 — Spend-key rune substitution, uniform off the previous output

* Mass B_q0(y), Delta j=1.
* Repair mass `(q0/Q)*U_a(y)`, also Delta j=1.
* Doublet mean delta, full output kernel K0(y|a) below.

This deliberately simple substitution is the existing collision module's guarded
I_1 fallback, evaluated with the new calibrated q0:
`work/independent/collision_substitution/collision_model.py:36-60`.
No history-tap selection is fitted in this catalogue. Original plaintext at a
repaired position is ambiguous with an ordinary plaintext giving the same output;
language redundancy/side information would be needed to choose that branch.
The key pointer itself remains aligned under the skip decoder's ordinary branch.

### M07 — Output-only collision null, retain BOTH plaintext and key

A two-state channel, not a one-rune substitution:

* NORMAL: ordinary/kept mass B_qN(y), Delta j=Delta p=1.
* NORMAL repair: emit R~U_a, mass qN/Q; Delta j=Delta p=0, enter PENDING(a).
* PENDING(b): deterministically emit the previously attempted b; Delta j=Delta p=1,
  return to NORMAL. The visible previous rune is the inserted R, so b!=R.

Every repair therefore writes the motif **a,R,a**. The null is visible to the
true comparison chain, unlike the deterministic edge-null convention.

Stationary pending fraction is qN/(Q+qN), and

    observed doublet mean = (1-qN)/(Q+qN) = delta.
    null fraction = qN/(Q+qN) = 10453/388410.

These are derived from R. The conditional first-null hazard before any insertion
is qN/Q, not its stationary output fraction. An invisible-null retry rule is a
different process and is not silently substituted here.

### M08 — Plaintext-side adjustment, no extra key

* Mass B_q0(y), Delta j=1.
* On repair replace p by p+1 and emit a+1: mass q0/Q at that value, Delta j=1.
* Doublet mean delta.

The shift of one is a design choice, not a Cicada clue. The original plaintext
has local errors after ordinary decryption, not cumulative key drift. Its very
specific adjacent-step prediction should be checked before building a search.

### M09 — Ciphertext feedback with checked skip-once

Attempt `X=a+p+K_j`; apply M01's repair and pointer rules. The fresh-key joint
output kernel and doublet rate equal M01's. Ordinary additive decryption gives
`p+a`, not p. Subtract a first, and compare the transformed attempted sum with
zero. This is already supported by chain windows:
`work/kscreen/chain_windows.py:1-7,43-48`.

A pointer can be right while the emission model is wrong. This row is not a
newly untested feedback family.

### M10 — Native 28-class step-domain, zero-step padding

With probability delta emit a zero step: y=a, Delta j=Delta p=0. Otherwise read a
native key value in Z_28 and plaintext class u in Z_28, emit

    y = a + 1 + ((u+K_j) mod 28) mod 29,

Delta j=Delta p=1. With a uniform native key its output kernel is K0. The doublet
rate is delta even without a uniform native key, since an ordinary step is never
zero. There is no would-be mod-29 collision event in this construction.

The scored class sequence and pointer rule are covered by variant A, mode drop,
in `work/kscreen/step28.py:4-16,108-137`; the step decoder does not reconstruct a
plaintext symbol at zero steps. There is no justification for applying the
ordinary mod-29 score benchmark to it. Its own 28-class controls must be used.

### M11 — Word-boundary advance plus M01

Before output i, discard `A_i=W_i` unread key values, where W_i is one exactly at
a word boundary inside the window. Then apply M01. Total Delta j=A_i+1 or A_i+2;
Delta p=1. Marginal output kernel and doublet rate equal M01's. Exact layout
convention: A above. Matching decoder: advsep=1 with skip.

### M12 — Word AND line/page advance plus M01

As M11, but `A_i=W_i+B_i`, where B_i counts exported line/page break entries
at that position, including duplicates. Coincident events add. Total Delta j=A_i+1 or A_i+2. Marginal kernel and rate
again equal M01's. Matching decoder: advsep=2 with skip. No layout advance before
the window's first rune is inferred; such an advance is absorbed by start offset.

## 3. What matching the doublet mean does NOT establish

Most rows have the SAME fresh-reference output kernel

    K0(a|a)=delta; K0(y!=a|a)=(1-delta)/(Q-1).

They differ in key consumption or native plaintext representation. Consequently,
the doublet statistic alone cannot identify the encryptor. M07 has an additional
pending state and a lag-two motif even though its stationary one-step marginal
can match K0. M08 has a different off-diagonal shape. None has been shown to
explain the other LP2 observations, and no plaintext/key has been recovered.

For the requested alignment and signal-loss matrix, see **MATRIX.md**. Actual
finite-beam power is **unknown** except for the already cited crossed controls.
