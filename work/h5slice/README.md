# work/h5slice — H5 first slice (drift-tracking decoder for the two-stack model)

Status: **IN PROGRESS — nothing validated yet. No controls have passed; no LP2 scores exist.**
This README records the design, the measured calibration numbers and the one open
blocking problem (beam overfit in the coincidence init pass). Do not treat any number
below as a result against LP2; nothing has been screened yet.

## Model (docs/HYPOTHESES.md H1, first slice)

    c_i = D(p_i) + t_j + w_(j mod L) + b   (mod 29)

* `t` = the library stream "primes-1 (totient)": `t_n = p_n - 1 mod 29`, p_n the n-th
  prime. Regenerated locally with a sieve (`h5slice.totient`), not read from the library.
* `w` = unknown keyword, period L in 1..20, estimated per column (the constant b is
  absorbed into the column shifts and does not affect any score here).
* Anti-repeat rule on the COMBINED key k = t + w + b (work/layer2's plant semantics):
  * model 0 ("skip"): on a collision the encryptor re-draws with the next key value,
    probability q = 1 - keep = 0.81 per attempt, up to 5 attempts;
  * model 1 ("coin"): on a collision one key value is always spent, then with
    probability 1 - keep the value is re-drawn from the next key value.
* Optional literal-F rule of the solved pages (work/lp.py): a plaintext F is written as
  F and consumes no key value (the pointer does not advance).

## Files

* `h5slice.py` — the decoder (self-contained Python + numpy for the light parts):
  streams (`totient`, `random_stream`), `plant` (independent two-stack encryptor with
  the anti-repeat rule, mirrors work/layer2's plant on the combined key), `decode`
  (two-stage algorithm below), `decode_t_only` (L = 0, the blind old-screen view),
  `periodic_ioc`, `load_windows` (kscreen window format), the multiprocessing sweep
  (`run_sweep`, `init_worker`, `run_chunk`) and `redecode`/`latin_render` for
  verification.
* `calib.py` — the calibration script whose numbers are quoted below.
* `control.py` / `control.txt` — the mandatory controls (a)–(e): **not written/run yet**.

## Algorithm as implemented (`h5slice.decode`)

Outer loop over (offset, L); inner EM over the keyword columns:

1. **Coincidence init pass** (`beam_coincidence`): a beam over FREE pointer branches
   (+1, +2, +3 per rune, plus the literal-F branch), states carrying per-column count
   vectors, scored by the w-free running column-coincidence z = (29·s − d)/√(56·d)
   (work/layer2's periodic z; s, d = ordered equal-letter pairs / pairs within columns).
   The z is shift-invariant, so the pointer alignment is sought before w is known.
   **This pass is the open problem — see "blocker" below.**
2. **Per-column w estimate** (`est_cols`): from the best path's columns
   x_i = c_i − t_{j(i)}, the ML shift per column under the English rune distribution
   (Self-Reliance via work/sim.py, add-0.5 smoothed): w_col = argmax_v Σ logf[(x−v) mod 29]
   — the distribution-aware modal class.
3. **EM over w** (`beam_pass`): beam over the collision-consistent skip branches only
   (work/layer2's `outer_cands` applied to the combined key t + w_est: one skip, then a
   double skip, are offered exactly where the collision is consistent; model 1 offers
   its re-draw branch and advances the pointer by 2 when the ciphertext rune repeats).
   Pruned by cumulative plaintext log-likelihood (the ~0.4 nats/rune of HYPOTHESES.md:22),
   early-aborted when the evidence at rune 120 stays below mean + 0.15 nats/rune.
   w is re-estimated from the best path until stable (max 6 iterations).
4. **Score**: the periodic IoC of the final re-decoded columns
   p_i = c_i − t_{j(i)} − w_(j(i) mod L), i.e. the mean over columns of
   29·Σ n_x(n_x−1) / (n_col(n_col−1)) (HYPOTHESES.md:70-78: ≈1.8 on truth vs 1.0±0.07
   for L=8, n=300). Literal Fs are counted in the column of the current pointer.

## Measured calibration numbers (calib.py, plant = Self-Reliance runes 3000:3300,
totient + DIVINITY at offset 1234, model 0, keep 0.19, seed 42)

* Plain window IoC 1.936 (300 runes); planted cipher IoC 1.016, 3 doublets — the plant
  looks like LP2 (flat IoC, few doublets), as required.
* **Blocker A (solved): the no-skip seed is a trap for LL-EM.** Starting the EM from the
  no-skip pointer, the per-column ML estimate is a compromise over phase mixtures
  (measured: [23,4,11,24,12,26,24,24] vs DIVINITY [23,10,1,10,9,10,16,26]); the LL-EM
  converges to that fixed point (final periodic IoC 1.042, ll/rune −3.63 — the mixture
  text has a peaked unigram distribution but no column coincidence). Conclusion: the
  beam's init must be found with the w-free coincidence objective, not the LL.
* **Blocker B (open): the coincidence init pass overfits.** With free branches the beam
  fabricates coincidence generically — even on random ciphertext + random stream it
  reached z ≈ 41σ (183 skips: it routes nearly every rune to a column where it matches).
  Measured: truth plant z 41.9σ (195 skips); random null z 40.9σ (183 skips). A hard cap
  of 20 skips lowered this (truth 7.0, null 4.3) but early fabrication still beats the
  true path before its coincidence accrues; a per-skip penalty of 0.4σ did not cure the
  null (20 random decodes: mean 10.9σ, max 14.0σ). The early-coincidence gain (one match
  at small d is worth several σ) dominates any flat per-skip σ-penalty. The pass is
  therefore NOT usable as committed; decode() as wired inherits this failure.
* Timing: one full LL-EM decode (n = 300, L = 8, beam 24, max_em 5) = 8.5 ms single
  core. The coincidence pass was not timed before the stop order.
* decode_t_only (t alone, control (b)) and all controls: not run.

## Candidate fixes for blocker B (next work)

1. **Score the init beam in nats, not σ.** With the LL objective each fabricated match
   gains at most log(1/min P(x)) − log(1/29) ≈ 2–3 nats while a skip costs ln(1/0.028)
   ≈ 3.6 nats (HYPOTHESES.md:18-20) — the currency is bounded. This requires w during
   the beam: run the free-branch Viterbi with the per-column ML w re-estimated every
   few runes (online EM), or marginalize w per column over the 29 shifts.
2. Consistency-conditioned branches with a coarse w search: for each column, branch
   points are only ~1/29 of runes; a small multi-start over plausible per-column shifts
   (top-2 ML candidates per column) makes the true skip set available without free
   branches.
3. Penalize per MATCH (not per skip) in the z score, or use the normalized column IoC
   (d-independent early) plus a skip prior, so early fabrication cannot pay for itself.

## Controls to run once blocker B is fixed (control.py → control.txt)

Thresholds are the task's, scored by the periodic IoC of section 4:

* (a) plant Emerson/Self-Reliance, t = totient + w = DIVINITY (L=8), model 0, keep 0.19
  (q = 0.81), fixed offset 1234: the search over offsets 0..2000 × L 1..20 × models {0,1}
  must return exactly (1234, 8, model 0) with periodic IoC ≥ 1.6 (expect ≈1.8–1.9);
  re-decode at truth must give wcol = DIVINITY exactly.
* (b) the same plant decoded with t alone (L = 0, decode_t_only): IoC < 1.2 (blindness
  of the old screen).
* (c) wrong-L (7, 9, 16, …) at the true offset and wrong offsets (±1, ±100): all < 1.4.
* (d) null: 8 random streams × 8 random offsets, L = 8, model 0, random ciphertext
  windows: best periodic IoC < 1.45.
* (e) the plant with the literal-F rule on must be recovered exactly (offset, L) with
  IoC ≥ 1.6.
* Extra: a b = 7 plant decoded at truth (the constant must be absorbed: wcol = DIVINITY
  + 7 mod 29).

## LP2 first look (not run)

Grid: the 8 section windows (first 300 runes of work/kscreen/data/segments.txt, prev from
the W line) × offsets 0..2000 × L 2..20 × models {0, 1}, t = totient, litf = 0; the same
grid on one random stream per window as the matched null (same multiplicity, 38,004
decodes per window/model). 608,304 decodes per stream × 2 (totient + null). Any window
reaching ≥ 1.6 periodic IoC is re-decoded in-process (beam 64, max_em 10) and reported as
a CANDIDATE (not a decryption); the per-window best is compared with the matched null max.

Runtime scaling (measured single-core decode 8.5 ms, before the init pass): ≈1.2M decodes
× ~10–30 ms / 8 workers ≈ 25–75 min wall, with the 120-rune aborts cutting nulls. This
must be re-measured once the init pass is fixed.

## What remains for the full library sweep (campaign design)

1. Fix blocker B; pass controls (a)–(e) above + the blindness and null lines; write the
   numbers into control.txt and the registry row open-h1.
2. LP2 first look as above; report per-window best vs matched null; re-decode and
   whole-section verification for anything ≥ 1.6 per docs/CAMPAIGNS.md (a CANDIDATE is
   not a decryption; only a full-section English verify counts).
3. Library sweep: every stream of work/keystreams.py + the export families (× mult 1,
   28, sign ±1, forward/reverse where meaningful) through the same grid, with its own
   matched-null replicate per stream and the predicted-IoC filter first
   (HYPOTHESES.md:10-14). Cost: ≈1,500 streams × 2 signs × 2001 offsets × 19 L ≈ 10^8
   decodes ≈ 100–300 core-hours in Python — the Rust engine (work/layer2 pattern) is the
   right home once the algorithm is frozen; the Python slice is the reference.
4. Extend later: H2's σ-invariant coincidence statistic, H3 clocked pointers, the
   H1/H2 random-jump add-on, and litf = 1 variants of the LP2 look.
