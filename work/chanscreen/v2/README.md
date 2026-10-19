# chanscreen v2: frozen protocol 2026-10-19

Nothing in LP2 is solved. No LP2 search will be launched. All v1 files and M04
are read-only, including failed GPU sources/artifacts. Snapshot:
v1_m04_snapshot.json (all files, including builds; v2 excluded). New writes only
here and dated append-only entries in the phase17 log. No installs/downloads.
Budget: <=4 CPU threads (BLAS1), <=8 CPU compute hours, <=2 GPU hours, each command
<30 min with checkpoints. Stop on the first failed gate; no replacement seeds.

## Claims to prove, not assume

Keep v1 channel definitions, finite failure atoms and score log Z_L - log Z_U.
Let i be number of outputs already emitted; j next key pointer. For i>=1 the
possible previous plaintext symbols at j are a subset of these sets (indices
outside the key are omitted; collision classes require i>=2):

- ordinary: c[i-1]-s*k[j-1], for every channel;
- hold: additionally c[i-2]-s*k[j];
- spend: additionally c[i-2]-s*k[j-1];
- coin kept-collision: additionally c[i-2]-s*k[j-2];
- skip/skip5: no additional class (every emission uses k[j-1]).

All arithmetic mod Q. Coin redraw has the ordinary class. Equal plaintext
symbols merge by SUM, never max; unequal symbols must not merge. This suggests
a stronger bound of two classes, not the proposed three; validate it explicitly.
Sets can include states unreachable from a particular offset, without changing
its likelihood. The terminal j=m is valid after the final emission, but cannot
produce another output. Initial previous ciphertext is absent, as in v1.

Backward recurrence for remaining suffix:
B_n(j,r)=1; B_i(j,r)=sum_(p,h) L[r,p] K_i(c[i],h|p,j) B_(i+1)(h,p).
For n>=1, Z(o)=pi[c[0]-s*k[o]] * B_1(o+1,c[0]-s*k[o]); Z(m)=0.
For n=0, every Z(o)=1, including o=m. This is a transposed finite DAG, not a
maximum-path search. All offsets share B, not a guessed common probability scale.
U has one state per pointer: replace each L entry and pi entry by 1/Q.

Scaling policy: Float64 per-state LOG probabilities with stable two-term
logaddexp, no shared row scaling. Each offset obtains its own log probability.
Uncapped skip runs must retain geometric weights until the finite end; use
log(q)*run_length, not underflowing q**run_length. At q=0/1 use exact support
branches. No numeric tail truncation, beam, or lossy prefilter is authorized.
Logaddexp may round terms too small relative to the same state's leading term;
that is floating-point roundoff, not underflow of one offset due to another.
Accuracy is checked at 1e-9 nats; no claim of exact real arithmetic in float64.

## E0 — exactness, frozen before execution

Use EXACT Fractions on v1's full G0 grid: Q3, all keys length0..3, offsets0..m,
signs +/-1, q=0,3/5,1, channels hold/spend/skip/skip5/coin, n0..3, all outputs,
two language models: uniform and pi=(1,2,3)/6 with rows (1,2,3),(3,1,2),(2,3,1)/6.
Require exact equality of all-offset backward results with BOTH v1 rational
forward and independent event tree. Event-tree success + failure must equal1.
Check sparse forward support and inverse-edge class closure. Also length8
constant keys / n2 for uncapped tails and skip5's actual cap.

Require witnesses detecting four v1 mutations (hold spends, coin omits slot,
skip drops tail, replacement divisor Q) and three new mutations: merge distinct
r classes, set backward terminal mass at j=m to0, normalize a backward row but
omit its scale restoration. Any mismatch, undetected mutant, or refuted R1/R2:
E0 FAIL; stop. No tuning away that result. A reproduction unit suite may rerun
these deterministic checks without overwriting gate records.

## E1 — fixed-input regression

No new plant seeds. Compare every stored cal/held score (200+380 records, 1024
cells each) against all-offset Float64 CPU results, log_L/log_U/score absolute
error <=1e-9, identical support and v1 threshold decisions outside 1e-9 margin.
Inside margin flag as ambiguous, not silently change a decision. Read the frozen
model and q fits. Reuse all 100,020 inputs of v1 gpu_parity.npz, including n300/600,
endpoints, q0/1, both signs, all channels. Compare to the v1 dense reference;
for large volume the v1 Rust accelerator (already reference-gated) is permitted,
with NumPy spot comparisons on deterministic first cells and all long cases.
Checkpoint disjoint record/input blocks; never overwrite results. Fail on any
numerical discrepancy. Additional adversarial log-range case: offsets whose
likelihoods differ by >1000 nats must retain finite scores when mathematically
positive. Exact-zero support must remain zero.

## E2 — measured cost, only after E1

Seed1702, fixed synthetic inputs; n300/600 x m2000/20000 x all five channels,
both signs. One warmup and three timed repetitions; report every duration,
median full L/U pass rate, offsets/s, memory. Use <=4 workers. Count real library
lengths read-only (expected1439; mismatch is an incomplete scope, not silently
adjusted). Proposed ciphertext windows: stride150 at n300 (50% overlap), plus
section-end-anchored window when not already included; exclude shorter section
0.10. This covers every rune of eligible sections with at most150-rune start
misalignment, NOT every possible cipher restart. Count from section lengths,
no ciphertext scoring. CPU14-thread cost is an explicit extrapolation from
measured CPU1/4, not a 14-thread experiment; include null/verification separately.
If extrapolated campaign >8h, only then propose g3b (new frozen protocol, Float64,
NVRTC builtins/no math.h, explicit infinity, <=1s launch, >=100020 parity cells
<=1e-9). Check nvidia-smi first; never displace another process. Float32 prohibited
unless separately gated at <=1e-3 with Float64 fallback in the threshold margin.

## E3 — real-bank null protocol (blocked until E2)

Search all1439 streams at real lengths, every offset, both signs, four channels.
Freeze decoder q=.81 for all channels (no oracle source-specific q), same v1 LM.
Initial null pilot: 30 windows at each n300/600, seed prefix chanscreen-v2-null,
index0..29, M04 ciphertext from independent iid keys NOT inserted into the bank;
plaintext alternating original held Cicada and held Emerson pools. q=.81,
report realized doublets vs86/12947, not force their count. This is a specified
synthetic null, not proof that all LP2 null laws have that rate.
Candidate rule frozen now: S >= T_n, where T_n=max(calibration bank maxima)+10
nats; equivalently >=10 nats margin over observed calibration max. No parametric
tail extrapolation authorized. With30 independent null windows the distribution-
free max-tail resolution is1/31, not a campaign-wise false-positive guarantee.
After pilot, choose sample count ONLY from measured cost: target199 per length
if within remaining compute budget, otherwise stop E3 INCOMPLETE and request
approval; never choose from favorable scores. Threshold finalization requires
all199 per length. Record resulting empirical rule's limits (unknown 1e9-cell
familywise guarantee), do not pretend ten-nat margin proves a tail bound.

LM mismatch: held Cicada is a different source from Emerson training. In E4 use
half plants from each source and report separately, with no LM refit. This is a
source mismatch stratum, NOT a different-language test. Other-language power
remains unknown. No new corpus downloaded or imported as code.

## E4 — library-scale power (blocked)

200 plants: four channels x two lengths x25, each group12 held Cicada /13 held
Emerson. Seed prefix chanscreen-v2-plant; uniformly sampled real library stream
and offset among those with enough key to generate the plant; both signs by
index parity. Check exhaustion and log ineligible generation explicitly, no
replacement seeds. Search whole bank with frozen E3 q/threshold. Acceptance:
>=90% pooled and >=20/25 per channel/length, >half detections have winner plaintext
accuracy>=.95. Record source mismatch power, exact stream/offset/sign/channel,
+/-3 aliases (not proof of equivalence). No threshold/LM tuning. These200 plants
are not the 100 original G2 hold plants and must not be run before E3 is frozen.

## E5 — package only

Only after E4 PASS, write a resumable stream/offset-block queue compatible with
jobs/jobqueue.py, frozen summary rule, real measured scope/cost, whole-window
and whole-section verification with positive and matched-null controls per
existing CAMPAIGNS.md. No LP2 search launched. A failed/incomplete earlier gate
means E5 INCOMPLETE, not a fake runnable campaign.

All later protocols remain blocked if E0 fails. Results and limitations go in
REPORT.md with registry proposals only; shared registry/documents remain untouched.
