# Phase 13: the corrected gated-null gate and the H5 drift-decoder first slice (2026-10-18)

Scope: LP2 sections 0.7-0.15. **Nothing in LP2 is solved.** Two builds from round 6-7 completed; both are honest
partials with measured blockers. Files: `work/tmp/gated_null_*.py|json|md`, `work/h5slice/`.

## 1. The corrected gated-null gate: FAILS - no LP2 screen authorized (`work/tmp/gated_null_report.md`)

The fixed-prior summed statistic (reimplemented from the second model's idea, with the review's required fixes)
was gated on planted controls:

- **The overfit fix works.** DP validated against a closed-form oracle; Viterbi recovers the plant (296/300
  letters = 98.7%, null recall 6/10). Against random keys: z(S_true) = +18.11 (64-setting grid) / +15.67
  (16-setting grid) - the free-beam's 1.75-IoC inflation does not recur.
- **But the gate fails on structured keys, permanently.** The corrected gate (neighbor offsets +/-1..3 AND the
  matched-null side, >= 10 nats) fails all three totient plants with margins 8.33-8.71 nats, and the margin is
  CONSTANT in n (8.40/8.37/8.36 at n = 300/600/900): the statistic cannot resolve a +/-1 key offset on a
  totient-structured key at any window length - the +1 neighbor realigns for free via one decoder null at the
  first eligible position, the -1 neighbor at the first hidden skip redraw. 5 of 12 random-key plants spuriously
  pass the gate (the reviewer's coin-flip reproduces).
- **Verdict:** the 42%-of-words keyless-null mixture remains untestable, now for the measured reason of OFFSET
  RESOLUTION on structured keys (not null inflation). The only paths left: a bigram-scored statistic (the
  reviewer's variant) with a load-bearing value gate, or a null prior conditioned on something the key does not
  share. One caveat on the exact tables (wrong plaintext prefix window; the fix is applied but not re-run;
  the verdict direction is corroborated by the independent review's -0.3-nat measurement on the true window).

## 2. H5 drift-decoder first slice: built, not validated - one real blocker (`work/h5slice/README.md`)- **Delivered:** `work/h5slice/h5slice.py` - self-contained totient stream, independent two-stack planter with
  layer2's anti-repeat models and the literal-F rule, two-stage decode (w-free coincidence init pass, then EM over
  the keyword columns with collision-consistency skip branches), periodic-IoC scoring per
  `docs/HYPOTHESES.md:70-78`. Calibration: plant (Self-Reliance x totient + DIVINITY, offset 1234) gives plain IoC
  1.936 vs cipher IoC 1.016 - LP2-like; LL-EM decode 8.5 ms single-core.
- **Blocker found:** (1) solved - seeding the EM from the no-skip pointer traps it in a mixture fixed point
  (wcol [23,4,11,24,12,26,24,24] vs DIVINITY [23,10,1,10,9,10,16,26], periodic IoC 1.042); (2) OPEN - the
  coincidence init pass with free pointer branches fabricates coincidence generically (z about 41 sigma on BOTH
  the truth plant and random nulls): with ~3 free pointer choices per rune the beam routes each rune to a
  matching column; a skip cap and a flat per-skip sigma-penalty do not cure it. The fix (specified): score the
  init beam in nats with a bounded per-match gain (about 2-3 nats vs the 3.6-nat skip cost,
  `docs/HYPOTHESES.md:18-24`), or consistency-conditioned branches with a small multi-start over the top-2
  per-column ML shifts.
- **Not run:** the (a)-(e) controls and the LP2 first look. Projected LP2 grid (8 windows x 2,001 offsets x
  19 L x 2 models + matched null, about 1.2 M decodes): 25-75 min on 8 workers, unvalidated.

## 2b. H5 init-beam fix applied: the overfit is gone at the smoke level (`work/h5slice/FIX_REPORT.md`)

- **The fix:** `beam_coincidence_nats` - a beam over the free +1/+2/+3 pointer branches scored by the per-column
  SHIFT-MARGINALIZED English log-likelihood (w integrated out over all 29 shifts per column, so the init stays
  w-free); per-skip cost ln(1/0.028) = 3.576 nats; per-letter gain bounded by ln(29*f_max) = 1.28 nats. A
  fabricated skip can no longer pay for itself. Two bugs fixed on the way (the abort checkpoint must fire only at
  abort_at; the EM's internal LL abort is disabled because truth LL = mean(logf)/rune exactly).
- **Verified (smoke level):** truth plant (Self-Reliance x totient + DIVINITY, offset 1234, model 0): periodic
  IoC **1.986**, wcol = DIVINITY **exactly**, init finds 8 skips = the plant's true count; 40/40 random nulls
  abort at the 120-rune checkpoint (they scored z ~ 41 before the fix).
- **Open blocker - performance:** the verified init costs ~137 ms/decode; the LP2 grid (2.7 M decodes) needs
  < ~10 ms. `beam_coincidence_nats_fast` (a ~20x vectorized rewrite, three bugs fixed on review) is in
  work/h5slice/h5slice.py marked UNTESTED. Next: verify fast vs slow, run the (a)/(b)/(d) controls, then the
  capped 60-min LP2 first look with 8 matched-null streams (candidates: IoC >= 1.6 AND >= matched-null max +
  0.15, in-process re-decode).

- **Fast path parity verified, speed not met, abort recalibrated** (`work/h5slice/FAST_REPORT.md`): the fixed
  v2 rewrite agrees with the slow init on 48/48 init checks, 24/24 decode cells, the truth plant (IoC 1.986,
  wcol = DIVINITY, 8 skips) and 40 nulls (<= 1e-6 nats; three real bugs found and fixed: node-id chain
  corruption, an unclamped index, an unstable sort). Speed: 191.7 ms vs 167.6 ms (0.9x) - numpy scatter/gather
  is the bottleneck; v3 (cyclic-correlation rewrite) written but UNVERIFIED, decode() defaults to the slow init.
  CORRECTION to the earlier smoke claim: '40/40 nulls abort at 120 (margin 0.15)' does not reproduce on the
  current code (0/40 abort; nulls sit 0.59-0.86 nats/rune above the null level at rune 120, truth delta
  +1.011); recalibrated abort: abort_at=120, abort_margin=0.9. Controls (a)/(b)/(d) and the LP2 first look still
  not run. Next: verify v3 (parity + speed); if numpy-Python cannot reach >= 10x, port the init to the layer2
  Rust pattern; then controls and the capped LP2 look.

- **v3 verified, speed fails; numba port is the path** (`work/h5slice/V3_REPORT.md`): v3 (correlation-trick) parity
  PASS after fixing one real bug (stale Lcm/Mmax rows in the survivor update): 48/48 init, 24/24 decode, truth
  IoC 1.986 wcol = DIVINITY, 40/40 nulls abort with the recalibrated abort (120, 0.9); the L=16 super-period
  degeneracy aborts too, so control (a)'s argmax is safe. Speed on the loaded machine: 1.0-1.1x - the 5x gate
  FAILS (~20 numpy calls per rune at 20-170 us under a saturated CPU). Controls (a)/(b)/(d) and the LP2 look
  NOT run (control.py written, unexecuted; the grid would be ~3.7 h at 44 ms/decode). NEW LEAD:
  work/h5slice/h5slice_nb.py, a numba port (numba 0.67 installed) with exact slow semantics, one compile bug
  fixed, parity UNVERIFIED, expected 10-50x; verify with _nb_check.py before wiring.

## 2c. H5 pipeline COMPLETE: numba verified, all controls pass, LP2 first look negative (`work/h5slice/verify_nb.log`, `control.txt`, `lp2_look.txt`)

- **Numba parity PASS**: 48/48 init, 24/24 decode, truth (IoC 1.986, wcol = DIVINITY, 8 skips), 40/40 null
  aborts at (120, 0.9); one numba bug fixed (the truncation sort must run unconditionally so the abort
  checkpoint reads the max). **Speedups 5.4-17.3x** (truth init 65.0 -> 3.82 ms, null decode 25.2 -> 1.46 ms):
  the 5x gate is met on every measurement; no Rust port needed for this slice.
- **Controls ALL PASS** (abort 120/0.9, 4 workers): (a) the truth grid argmax is EXACTLY (1234, 8, model 0)
  with IoC 1.9856 and wcol = DIVINITY (runners-up <= 1.3166); (b) 8 random nulls on the same grid: global max
  1.3537 < 1.45; (c) the L=1/L=8 degeneracy recorded as a model-class note (no-keyword plant at L=8 -> IoC
  2.1830, all-equal wcol); (d) wrong-L {7,9,16} and offsets +-1/+100 all abort.
- **LP2 first look: PARTIAL GRID, NO candidates.** 5,327,600/5,474,736 cells in the 45-min cap (offsets
  0..1949 complete for every (window, stream, model) except seg0.15's nulls at 0..1924; only offsets 1950..2000
  and 1925..1949 for seg0.15's nulls unrun). Best real periodic IoC per window 1.2377-1.4840 vs matched-null
  max 1.3635-1.5306; the best real cell anywhere (seg0.11, 1.4840 at (1160, 19, model 1)) sits below its own
  matched null and below 1.6: **zero cells reached 1.6, zero candidates**. A first-look negative for
  H5/totient on the first 300 runes of the 8 sections (L 2..20, both models, offsets 0..1949) - NOT an
  exclusion: litf=1, the other library streams, H2/H3-style keys and the missing offsets remain.

## 2d. H5 Rust port: parity-clean, ~14.7 h for the full library sweep (`work/h5rs/README.md`, `parity.txt`)

- **Parity PASS: 312 checks, 0 fails.** Three engines (scalar = numba-exact port; fastscalar = no-exponentials;
  fast = AVX2 + copy-on-write arena + table ln, bit-identical to fastscalar) match h5slice_nb exactly on 24
  grid cells (offsets {1234,1000,1500,777} x L {7,8,12} x models {0,1}, init and full decode at abort 0 and 120),
  the truth cell (IoC 1.9856, wcol = DIVINITY, 8 skips) and 4 random null windows (4/4 aborts); totient
  bit-identical. Seven real divergences caught and fixed (a Zen1 VHADDPD miscompile, stale thread-local stamp
  ids, a shuffle-immediate convention, a tie-flipping vector reduction reverted to sequential order for
  bit-exact ties, a packed sort key truncation, arg-parse and AVX2 dispatch bugs).
- **Throughput: 3,842 dec/s single-threaded, 16,634 dec/s on 8 threads under load** (best 18.8k); the full
  880M-decode library sweep = 14.7 h at 8 threads (the parity.txt label says hours but the value is seconds).
  The rate is ~5.6x the numba reference - the per-candidate dot sum must stay sequential for bit-exact
  tie-break parity, and the machine was loaded. The >= 20k dec/s gate is NOT met under load; the CLI and sweep
  driver exist and are parity-gated but provisional - re-measure on an idle machine before a campaign.

## Registry / status updates

- `nulledge` row: gap updated - the 42% mixture is untestable for the measured reason of offset resolution on
  structured keys (gated-null row files).
- `open-h1` row: the first slice exists with its blocker; the fix (nats-scored init beam) is the next step.
