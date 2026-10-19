# chanscreen: frozen gates, protocol v1

Nothing in LP2 is solved. Synthetic engineering only. No campaign may be launched.
All writes are confined here and `work/log/phase17_chanscreen.md`. No downloads,
installs, shared builds, commits or changes to running jobs. CPU <=4 threads;
BLAS 1 thread. A run must finish within 30 minutes; GPU total <=4 hours.

## Specification (frozen before G0)

Alphabet size Q, finite key k[0:m], sign +/-1, initial pointer o in [0,m].
Initial previous ciphertext is absent; plaintext initial distribution pi,
row-stochastic bigram L. State after i outputs is (j, previous plaintext).
Lag is j-o-i; negative lag is allowed. No beam and no lag truncation.
Every output consumes exactly one plaintext. Draw p ONCE from pi/L, then:

* No previous output or attempted x=(p+sign*k[j]) mod Q differs from a:
  emit x, j <- j+1.
* hold: on collision keep x with probability 1-q (advance j); otherwise emit
  uniform among Q-1 other outputs and KEEP j.
* spend: same substitution, but always advance j.
* skip: on each collision keep with probability 1-q; otherwise advance j
  and retry the SAME plaintext. No cap. All remaining finite-key retries are
  traversed. Exhaustion is an absorbing FAILURE outcome, not renormalization.
* skip5: exactly the frozen M04 planter's skip convention, at most five redraws;
  the sixth attempt is emitted unconditionally. This cap is part of the CHANNEL,
  not a numerical approximation. G2 regression uses skip5, not skip.
* coin: on the initial collision consume one additional coin slot (independent
  auxiliary coin, not the slot's value); keep with 1-q, else consume a third
  key and emit its candidate ONCE, even if it repeats. Missing coin/redraw
  slots mean FAILURE. No coin is spent on a noncollision.

Channels are JSON data records selecting these transition kernels; unknown kernels
are rejected, with a reserved extension slot (not an implemented extra hypothesis).
q is the probability of repair, NOT the observed repair fraction.

### Exactness and normalization

Let A_i(j,r) be joint mass of observed prefix and last plaintext r. The recurrence
is A_(i+1)(j',p) += A_i(j,r) L[r,p] K(c_i,j'|p,j,c_(i-1)).
Initialize with pi and j=o; sum over final states. U replaces BOTH pi and L by
1/Q. Score is log Z_L - log Z_U, in nats, not clipped/rounded old score units.
When Z_U=0, the observation is outside channel support and score is undefined
(rejected), not +infinity. Z_L=0 with Z_U>0 gives -infinity.
Finite-key success need not sum to one: success plus all terminated-prefix
FAILURE atoms does. No conditioning on survival. For a fixed key the skip tail
is a product of q over actual consecutive colliding candidates, not (q/Q)^d;
iid-key averaging must NOT be used for a fixed stream. At finite end all residual
mass goes to FAILURE. An infinite all-colliding key with q=1 never emits;
only finite streams are implemented. Float64 forward scaling is arithmetic
stabilization, with log scales restored, not probability renormalization.
No discarded lag mass: residual truncation mass is identically zero by construction.

Proof: each local event partitions probability one (including failure); induction
on output count gives normalized finite prefix trees. Plaintext is drawn once
per emitted output; skip retries leave it unchanged. DP groups precisely the tree
nodes sharing (i,j,r); previous ciphertext is observed, hence no extra hidden
history. Summation distributivity proves equality with the event tree. Hold cycles
advance i, and skip retries advance j, so the finite computation is acyclic.

## G0: exhaustive proof checks

Q=3, all keys of length 0..3, all initial offsets 0..m, both signs, q in
{0,3/5,1}, all outputs of lengths 0..3, five kernels above. Nonuniform rational
pi=(1,2,3)/6 and L rows (1,2,3)/6, (3,1,2)/6, (2,3,1)/6, plus uniform.
Independent event-tree enumeration (does not call DP arcs) versus rational DP:
require EXACT equality; success plus failure exactly 1. Mutations must be caught:
hold spends key, coin omits coin slot, skip drops tail after one retry,
replacement divides by Q rather than Q-1. Every mutation must have a witness.
Any failed assertion: G0 FAIL, stop; never replace seed or tune tolerance.

## G1: numerical reference

NumPy float64 scaled forward recurrence compared with G0 (absolute probability
error <=2e-13; logs on positive masses <=2e-11). Same-environment repeated scores
must be bit-identical. Additional 50 random Q=29 edge cells (fixed seed 1701),
empty input/key, stream ends, q=0/1, both signs; compare to scalar recurrence.
If a CPU accelerator is needed, require same tolerance <=1e-9 nats on 1,000
fixed-seed cells, including 300/600 runes; benchmark separately. No fast math.
Unit suite target <5 minutes. No hardware-cross-platform bit identity is asserted.

## G2: power (freeze before examining any held-out scores)

Reuse `work/m04/m04.py` and `run_baseline.py` read-only for plaintext, encryption,
bank construction, seeds and existing q fits. Do NOT use the old IoC threshold
as a nats threshold. Recompute the 10th-largest-of-200 matched-null maximum
with the NEW score on the SAME calibration seeds and bank sizes. Save it before
held-out. Training L: counts from the training Emerson 0..40% only, add 0.5 to
every bigram and unigram; pi = smoothed unigram. No held-out plaintext in L.

Search eight streams x 16 offsets x two signs x four channels (hold, spend,
skip5, coin) = 1024 cells. All plants and nulls use identical freedom. q for
hold/spend is the existing per-source/key-stratum fit, skip5/coin q=.81.
No early abort, lag band or prefilter in G2. Detection means max S >= T;
not exact-offset identification. Record winning stream/sign/channel/offset,
true-cell score and offset aliases (same stream/sign within 3 offsets), ties,
plaintext accuracy at winner and true cell. Reconstruction uses maximum joint
path under L, solely for accuracy, NEVER as detection score.

Held-out seeds exactly the baseline: 100 hold, 100 spend, 40 skip, 40 coin,
100 matched nulls. Run each ONCE. Acceptance ALL: hold >=90/100, each stratum
>=20/25; null <=5/100; accuracy >=.95 in strictly more than half detected hold
plants at the WINNING cell; spend >=90/100; skip and coin >=36/40 each.
No reruns with other seeds or retuning after failure. Overlapping windows are
not independent passages; report distinct starts. Small bank power is NOT a
full-library guarantee. Training development seeds use prefix `chanscreen-train`.

## G3-G5 (blocked until G2 passes)

G3: CuPy/NVRTC float64 reference-first, no fast math. >=100,000 cells seeded
1703 including all channel/end cases, score absolute tolerance 1e-8 nats,
no support mismatches; float32 requires separate <=1e-3 score test and identical
threshold decisions outside that margin (inside: redo float64). Profile occupancy,
memory and measured throughput; kernel launches <1 second for Windows TDR.
G4: seed prefix chanscreen-cascade-1704, >=1,000 plants, both n=300/600, all
four channels, matched real-size bank (1,439 streams and actual offset lengths).
Require >=98% retention of exact detections at the SAME threshold, per length
and channel as well as pooled; no recalibration on held-out cascade plants.
Possible conservative prefilter: partial-prefix likelihood upper bounds on the
remaining observations and denominator lower bounds from a valid U path. Such
bounds may be too loose; speed and loss remain unknown until measured. Do not
call an unmeasured heuristic bounded-loss. A banded DP must carry rigorous
omitted-mass upper bounds or fall back to full DP; renormalizing the band is invalid.
G5: resumable offset-block queue and frozen summary rule, whole-window then
whole-section verification with controls per docs/CAMPAIGNS.md, cost <=8 GPU h
or explicitly measured smaller scope. DO NOT LAUNCH. No fake runnable package
if an earlier gate is incomplete/failed.

## Execution and recovery

Use `.venv/Scripts/python.exe -B` from repository root. Scripts will put raw
records below this folder and refuse to overwrite gate artifacts. A failed gate
is immutable. Reproduction tests can run independently; that does not authorize
a new confirmatory held-out attempt. See REPORT.md for actual progress and commands.
