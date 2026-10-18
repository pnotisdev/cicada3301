# Independent review of work/independent/ (2026-10-19, executed by the reviewing agent)

**Nothing in LP2 is solved.** This is a review of the second AI's un-run analysis package
(`work/independent/`). Per project rules the reviewed code was read as data and never
imported or executed; every check below was reimplemented from scratch in my own scripts:

* `work/tmp/ind_review_claim1.py` — affine redundancy check (all 28x29x28 = 22,736 settings)
* `work/tmp/ind_review_claim3.py` — reimplementation of the lag-6 gated-null forward statistic + planted/null experiment
* `work/tmp/ind_review_claim3_gate.py` — replica of the gate's own margin criterion on random keys
* `work/tmp/ind_review_claim3_debug{2,3}.py` — mechanism forensics (plant vs decoder pointer paths)

No commit was made. Nothing in the reviewed folder was modified.

---

## Claim 1 — Affine outer alphabets are redundant after the all-28-multiplier screen: CONFIRMED

The claim (work/independent/MATH.md:43-90): for sigma(x) = a*x + b over F_29,
screening the sigma-relabelled ciphertext with multiplier m' is IoC-identical to
screening the unrelabelled ciphertext with multiplier m = a*m' mod 29, with the same
key-pointer paths and collision events.

My reimplementation verified, for **every** (a, b, m') in 1..28 x 0..28 x 1..28
(22,736 settings, two independent plants with inner multipliers m0=1 and m0=7):

* `tB == sigma(tA)` elementwise, where tA = decode(sigma_inv(page), m'), tB = decode(page, a*m')
  (the front-end convention sigma_inv is work/kscreen/RELABEL.md:22-27);
* identical key-pointer sequences;
* pairwise-identical arc/collision weights (skip q=0.81), hence identical IoC
  (|ioc(tA)-ioc(tB)| < 1e-12), identical beam merges and Viterbi decisions.

This matches the engine semantics exactly: every branch in `ioc_beam`
(work/kscreen/src/main.rs:583-651) is a mod-29 equality test, and its score is a
coincidence count — both invariant under a bijection applied to ciphertext, prev chain
and residuals. The parent's own measurement (all 29 reflections score identically,
work/log/phase12_review2.md:19-22, docs/registry.toml:722) is the a=28 case of this identity.

**Consequence: the pending "26 affine multipliers x all 8 sections" run
(docs/registry.toml:723-724, work/log/phase12_review2.md:111-114) is redundant and
should NOT be run.** Each of its settings (sigma aff:a:0, screen multiplier m' in
{1,28}) is IoC-identical to the unrelabelled screen with multiplier m = a*m' mod 29 in
{1..28} on the same windows, library, offsets and models — and the completed
"multipliers" screen already covered the 8 section windows x the library x every
multiplier x both models (docs/registry.toml:67-79). Atbash: m'=1 -> m=28, m'=28 -> m=1
(MATH.md:70-71 is right). Shifts b: absorbed as plaintext shifts (a=1 -> m=m').

Caveats (do not weaken the verdict): (i) identical IoC requires the same windows,
library items, offsets and models — the pending run qualifies; (ii) relabelled windows
must carry no P/S/G lines, which relabel_export enforces (RELABEL.md:29-32); (iii) the
historical runs show library item counts 1,447 vs 1,439, so if the library was
refreshed since the multipliers screen, the pending run would re-screen a few new
STREAMS — that is a library-refresh question, not new affine coverage; (iv) the
counter-control is real: a non-affine permutation has no fixed multiplier removing the
key for all (p,k) (verified; increments {1,2,28} for the 0<->1 swap), so the keyword
alphabets already run (phase12_review2.md:110-113) are NOT redundant by this argument.

Verdict: **CONFIRMED. Cancel/skip the pending 26-affine run.**

---

## Claim 2 — PGP bytes 7A35090F: reading CORRECT; but the string IS pinned in the repo

Byte reading (work/independent/MATH.md:10-19): `7A`='z' (122), `35`='5' (53),
`09`=TAB, `0F`=SHIFT IN (U+000F): `bytes.fromhex("7A35090F") == b"z5\t\x0f"`, not
`z5z5` (that would be 7A357A35; uppercase Z5 = 5A35). Verified: correct. The
"short OpenPGP key identifier, not the signature's message" caution is also right.

Repo pinning: the task asked whether anything pins the string. **Yes.**
`work/grid60.py:105` and `work/prng_screen.py:85` use `"7A35090F"` and `"0x7A35090F"`
as hash-seed strings for keystream generators, and `results/kscreen/*.tsv` contain
thousands of rows naming derived streams (`sha256-ctr mod :7A35090F`, etc.).
`docs/` has zero occurrences. So the repo already treats the string as a
Cicada-related number for keystream generation; the README's "comes from outside
material" (work/independent/README.md:14-15) concerns the PGP-clue provenance only,
and that provenance is indeed not established anywhere in the repo. The Z5 book lead
remains unverified, as the folder itself says.

Verdict: **CONFIRMED on the byte reading; corrected on repo pinning (the string IS in
the repo as keystream seed material — work/grid60.py:105, work/prng_screen.py:85).**

---

## Claim 3 — the lag-6-value-gated keyless-null decoder: SPLIT — null control CONFIRMED, power as specified REFUTED

I reimplemented the exact forward statistic from the specification
(work/independent/MATH.md:106-184, echo_nulls.py:65-168): states
(key pointer, previous plaintext, previous-output-was-null), exact log-sum-exp over
paths, English bigram model on the committed Emerson reference with 0.5 pseudocounts
(manual_common.py:97-116), uniform model 1/29, null value T(c_(i-6)) = 24-2c mod 29,
rho = 0.0272 per eligible position, no consecutive nulls, skip q = 0.81.
Validated against an oracle: a no-skip/no-null plant decodes at the true offset with
S = +217.67 == the direct bigram sum, aligned == planted plaintext exactly.

Setup: Welcome plaintext (lp.KNOWN[1][1]) first 300 runes, IoC 1.6702; totient
(primes-1) library stream (work/keystreams.py:44), offset 3, mult 1, no atbash;
LP2 section 0.7 word layout for the first 300 positions (30 eligible lag-6 positions,
consistent with 1,290 pairs / 12,956 runes book-wide, results/analysis/echo_position.txt:21-23).
Search grid = their gate's: 8 offsets x {1,28} x {F,T} x {0, 0.0272} = 64 settings/key.
One forward call: ~41-57 ms.

### 3a. Null-control side (their anti-inflation claim vs the nulledge baseline): CONFIRMED

Plant A (1 null planted at rho per eligible position): S(true, rho=RHO) = +205.50 vs
S(true, rho=0) = +156.33 — the null model adds +49.2 nats at the true alignment.
Viterbi at the true setting: accuracy 296/300 = 98.7% (their gate needs >= 98%),
planted-null recall 1/1, 0 false deletions, decoded IoC 1.677 (planted text IoC 1.670).

Plant B (null control, no nulls planted): S(true, rho=0) = +205.70; the rho=RHO
variant scores +205.10, i.e. the null freedom is not exploitable at the true setting.

Random-key matched nulls (16 keys x the same 64 settings, the shuffled-key design of
their screen, echo_nulls.py:393-401): bests mean -345.8 (A) / -346.6 (B), sd 12.0 /
12.7, max -314.1 / -319.4. z-score of the true S: **+45.9 / +43.6**; Monte Carlo rank
p = 0.059 (0 of 16 nulls reach the true score). The rho-freedom inflation on random
keys (best full grid minus best rho=0-only) is small: mean +10.0 / +4.4 nats, max
+34.9 / +21.5 nats — the fixed prior does spend a little pointer-phase freedom, but
the null's best stays ~525 nats below the true-key S.

**The free per-word beam's failure does not recur.** The parent's baseline
(work/tmp/nulledge_report.md:25-29): the beam's random-key null reached IoC 1.7547,
at the truth's level (1.71). Here the gated statistic's random-key null stays 525 nats
(~46 sd) below the truth. The "sum instead of maximize, fixed prior" design fixes the
beam's overfit — this part of the folder's claim is measured, not assumed.

### 3b. Power/separation at the specified screen settings: REFUTED

On the **totient stream — the screen's default stream** — the statistic does NOT
separate the true offset 3 from offset 4 at n=300:

* Plant B: S(offset 3) = +205.70 vs S(offset 4) = **+206.01** (wrong offset HIGHER by
  0.31 nats); Plant A: +205.50 vs +205.86. Margin = **-0.35 / -0.32 nats**, against
  the gate's >= 10-nat requirement (echo_nulls.py:255-260).

Mechanism (measured, not conjectured; work/tmp/ind_review_claim3_debug3.py): the
plant's hidden redraws (skip rule) are at positions [4, 31, 117, 175, 202, 274, 285].
At a redraw site the decoder's probability-1 "direct" arc consumes one key while the
aligned path's redraw arc consumes two, so a +1 offset error is entirely erased at the
FIRST redraw site: the offset-4 Viterbi pointers equal the plant's from position 4
onward (diffs only at positions 0-3), and it reads the true plaintext, paying only the
bigram cost of positions 0..3. On the totient key the first redraw sits at position 4
for 5 of 6 seeds (the collision at position 4 is deterministic: the plaintext diff
there equals the key gap), so the valley is ~0 nats deep. Seed sweep: first redraw at
pos 4 -> margin -0.3 nats (5 seeds); pos 144 -> margin +90.3 nats (seed 20004). On
random keys the wrong offset reads p + (key difference) garbage, so the margin tracks
roughly 2 nats x (first redraw position).

Gate replica on random keys (their exact criterion, 2 keys x 8 offsets x 8 variants;
work/tmp/ind_review_claim3_gate.py): margins +33.8, **+1.7, +8.0, +4.0**, +34.9, +22.5
-> **3 of 6 plants FAIL the gate's own >= 10-nat threshold**, each failure tied to a
first redraw in the first ~7 positions. (My replica used section 0.7's layout for all
reps; their gate cycles layouts — this cannot change the mechanism or the verdict.)
So the gate as specified is a coin flip on its own random-key plants, and because it
only ever plants random keys it can never see the totient degeneracy — i.e. it cannot
certify power for the screen it authorizes.

Verdict: **CONFIRMED for the null control (anti-inflation) and for the null layer
itself (the decoder genuinely finds a planted null when aligned); REFUTED as a
powered gate for the screen's settings** — on the totient stream the true alignment
is not separated from its +1 neighbor (margin -0.3 nats vs a required +10), and the
gate fails 3/6 of its own random-key plants. The forward core is implemented
correctly (oracle check passes); the flaw is the statistic's offset valley from the
skip rule's hidden pointer freedom. **The gate should not authorize the screen; the
screen's flag rule would compare a +205-ish true offset against shuffled-key nulls of
~-346 (which destroy the gap structure), so it could flag while misidentifying the
offset — and the 20 unsearched-offset controls in `verify` would not catch a +1
offset error because offsets near the truth benefit from the same realignment.**

Additional power caveat: only 30 eligible positions in the first 300 runes of section
0.7, so at rho = 0.0272 the expected null count per screen window is ~0.8 — the
screen would be searching for ~1 null in 300 runes.

---

## Bugs found (static review + the experiments above)

1. **Offset-valley / gate-threshold flaw (design, echo_nulls.py:65-86, 213-260).**
   The exact-forward arcs give probability 1 to the direct reading at hidden redraw
   sites, letting a wrong offset erase its error at the first redraw; the gate's
   10-nat margin is below the valley depth (~2 nats x distance to the first redraw)
   whenever the first redraw is in the first ~5 positions. Measured: 3/6 random-key
   plants fail the gate's own criterion; totient plants fail by construction (-0.3).
   The README's interpretation of a gate failure ("prevents wasting a large sweep on
   an unpowered model", work/independent/README.md:61) misattributes this failure mode.
2. **Gate coverage gap (echo_nulls.py:239-260).** Plants use random keys only; the
   screen's default stream is totient. The gate cannot certify power for the screen's
   actual key family (where the margin is -0.3 nats, not >= 10).
3. **Power-statement weakness (echo_nulls.py:226-236).** With ~30 eligible positions
   per 300-rune window, six unconditioned plants have ~44% chance each of planting
   zero nulls; only two reps are conditioned on >= 1 null. A passing gate would say
   little about the null layer at the real rate.
4. **README provenance wording (work/independent/README.md:14-15).** "The file claims
   it comes from outside material" is misleading: the string 7A35090F is already
   pinned in the repo as keystream hash-seed material (work/grid60.py:105,
   work/prng_screen.py:85); only the PGP-clue provenance is external.
5. No arithmetic bugs were found by static reading in `collision_substitution/`
   (kernel (14), the e-value bound (17), the n_d table and the scan() score formulas
   all check out on paper against DERIVATION.md); its code was NOT executed in this
   review (budget and instructions), so its runtime behavior remains unverified.
6. Minor: `audit.py:61-66` re-checks the equality-pattern invariance only on one
   synthetic plant; harmless, since my independent 22,736-setting check confirms it.

## What is worth promoting into the main workflow (after rewrite)

1. **MATH.md §2 -> act on it now.** Skip the 26-affine x all-sections run. If a
   library refresh since the multipliers screen is wanted, rerun the multipliers
   screen on the current library — not the affine relabels. Record the affine
   redundancy in the `open-outer-alphabet` registry row and close it.
2. **Claim 2 -> one-line correction.** Note in the registry/README that 7A35090F is
   already used as keystream hash-seed material in the repo (grid60/prng_screen); the
   Z5 book lead itself stays unverified and low-priority.
3. **Claim 3 -> promote the idea, not the gate.** The fixed-prior summed-path
   statistic genuinely fixes the nulledge beam's overfit (null stays 525 nats below
   truth vs IoC 1.75 = truth) and recovers a planted gated null (98.7% accuracy,
   recall 1/1, +49.2 nats from the null model). But before any screen: (a) fix the
   offset valley — require separation from NEIGHBOR offsets (e.g. margin over offsets
   +/-1..3), add a totient/structured-key plant as a required control, and re-tune the
   10-nat threshold (the valley is ~2 nats x first-redraw distance); (b) the verify
   step's unsearched-offset controls must include the +/-1 neighbors, not only random
   offsets. Do not run `echo_nulls.py gate/screen` as currently written.
4. **collision_substitution/:** static review only; the exact raw-spend mean tables
   are the cheap, legitimate piece, but its gate must be human-run and separately
   reviewed before anything else (its own README says exactly this). No promotion yet.
