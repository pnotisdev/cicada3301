# work/h5slice — H5 first slice (drift-tracking decoder for the two-stack model)

Status: **IN PROGRESS — init fix applied, single-cell truth verified; CONTROLS (a)–(d) NOT
yet run; no LP2 scores exist.** Blocker B (the coincidence init overfit) is fixed in
principle: the nats-scored init recovers the truth plant's pointers and wcol exactly in a
smoke test. The controls and the LP2 first look are blocked on ONE practical issue: the
verified implementation costs ~140 ms/decode and the LP2 grid (2.7M decodes) needs
<~10 ms/decode. A ~20x faster vectorized rewrite exists as
`beam_coincidence_nats_fast` (**UNTESTED**) and must be verified against the slow version
before the sweeps run. Details in `FIX_REPORT.md`.

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
  (two-stage algorithm below), `beam_coincidence_nats` (the fixed nats-scored init),
  `beam_coincidence_nats_fast` (UNTESTED vectorized draft, ~20x faster),
  `beam_coincidence_z` (the deprecated z-scored init, kept for regression comparisons),
  `decode_t_only` (L = 0, the blind old-screen view), `periodic_ioc`, `load_windows`
  (kscreen window format), the multiprocessing sweep (`run_sweep`, `init_worker`,
  `run_chunk`) and `redecode`/`latin_render` for verification.
* `calib.py` — the calibration script (needs its numbers re-measured once the fast init
  is verified; the smoke numbers below are from `_smoke.py`).
* `control.py` / `control.txt` — the mandatory controls (a)–(e): **not written/run yet**.
* `FIX_REPORT.md` — the init-fix session report: what was changed, what was verified,
  what is still open.
* `_smoke.py`, `_dbg.py`, `_dbg2.py` — scratch scripts from the fix session (truth plant
  + null smoke test; init beam trajectory; abort isolation).

## Algorithm as implemented (`h5slice.decode`)

Outer loop over (offset, L); inner EM over the keyword columns:

1. **Nats-scored coincidence init pass** (`beam_coincidence_nats`, the fix for blocker B):
   a beam over FREE pointer branches (+1, +2, +3 per rune, plus the literal-F branch),
   scored by the per-column SHIFT-MARGINALIZED English log-likelihood: each state keeps
   the log-domain column products G[col, v] = sum_i logf[(x_i - v) mod 29], scored as
   sum_col logsumexp_v G[col, v] + skips * ln(0.028). The keyword shift of each column is
   integrated out over the 29 shifts (uniform prior), so the pass is **w-free** (no
   keyword knowledge). A letter placed in a column adds at most ln(29 f_max) ~ 1.3 nats
   of evidence above the uniform-null level, while one skip costs ln(1/0.028) = 3.58
   nats (HYPOTHESES.md:18-20): a fabricated skip can no longer pay for itself (the old
   z-scored version reached z ~ 41 sigma on both truth and nulls). The beam buys the
   REAL skips on truth because re-alignment is worth ~1.2 nats per later rune.
   Early abort: at the abort_at checkpoint (e.g. rune 120) a cell whose best mean score
   is below the unigram-null level + margin is a dead null and returns without the EM.
2. **Per-column w estimate** (`est_cols`): from the best path's columns
   x_i = c_i − t_{j(i)}, the ML shift per column under the English rune distribution
   (Self-Reliance via work/sim.py, add-0.5 smoothed): w_col = argmax_v Σ logf[(x−v) mod 29]
   — the distribution-aware modal class.
3. **EM over w** (`beam_pass`): beam over the collision-consistent skip branches only
   (work/layer2's `outer_cands` applied to the combined key t + w_est: one skip, then a
   double skip, are offered exactly where the collision is consistent; model 1 offers
   its re-draw branch and advances the pointer by 2 when the ciphertext rune repeats).
   Pruned by cumulative plaintext log-likelihood; w is re-estimated from the best path
   until stable (max 6 iterations). The EM's own LL abort is NOT used: on the true path
   the LL equals mean(logf) per rune exactly, so any margin-above-mean threshold would
   kill the truth plant (and the uniform-mean level the old code used is a no-op on
   nulls, which overfit the per-column shifts upward).
4. **Score**: the periodic IoC of the final re-decoded columns
   p_i = c_i − t_{j(i)} − w_(j(i) mod L), i.e. the mean over columns of
   29·Σ n_x(n_x−1) / (n_col(n_col−1)) (HYPOTHESES.md:70-78: ≈1.8 on truth vs 1.0±0.07
   for L=8, n=300). Literal Fs are counted in the column of the current pointer.

## Calibration numbers measured so far (fix session, `_smoke.py`/`_dbg.py`; NOT the
full control set)

Plant = Self-Reliance runes 3000:3300, totient + DIVINITY at offset 1234, model 0,
keep 0.19, seed 42 (per calib.py).

* Model constants: H(f) = 2.954 nats (truth-path LL per rune), uniform-null level
  (1/29)Σlogf = −4.230 nats per rune → ~1.28 nats/rune of drift evidence; per-letter
  gain bound ln(29 f_max) = 1.28 nats < 3.58 nats per skip.
* **Truth plant, single cell (1234, 8, model 0), no abort**: periodic IoC **1.986**,
  wcol = **[23, 10, 1, 10, 9, 10, 16, 26] = DIVINITY exactly**, ~140 ms/decode.
* **Truth plant init alone**: 8 skips found (= the plant's true skip count), score
  −897 nats (−2.99/rune) vs the no-skip null level −1242 nats (−4.14/rune): the beam
  tracks the true drift, and the separation at rune 120 is −359 vs the abort threshold
  −463 (margin 0.15) — wide.
* **Nulls (random windows + random streams, L=8)**: 40/40 aborted at the 120-rune
  checkpoint (ioc 0.0) with abort margin 0.15 — the overfit is gone (the old z init
  scored random nulls at z ≈ 41σ; these return no score at all). The non-aborted tail
  distribution has NOT been measured yet (the smoke loop division-by-zeroed because
  every null aborted).
* **Blocker A (solved, unchanged)**: the no-skip seed is a trap for LL-EM; the init
  must be found with the w-free objective, which is what step 1 now does.
* **Blocker B (fixed in principle)**: the z-scored free-branch init is replaced by the
  nats-scored shift-marginalized init above. Verified on the truth plant (IoC 1.986,
  DIVINITY exact) and on nulls (all abort).
* **Performance — THE open issue**: the verified init costs ~137 ms/decode (Python
  loops in the candidate build + dict merge; the EM adds ~10 ms on survivors). The LP2
  grid (8 windows x 2001 offsets x 19 L x 9 streams = 2.7M decodes) needs the whole
  decode at < ~10 ms. `beam_coincidence_nats_fast` is a vectorized rewrite aimed at
  ~5-8 ms/decode, currently UNTESTED: verify it against the slow version (same truth
  pointers, same null aborts) and then wire it into `decode()` before any sweep.
* decode_t_only (t alone, control (b) of the old list) and controls (c), (d), (e): not
  run.

## Controls to run once the fast init is verified (control.py → control.txt)

Thresholds are the task's, scored by the periodic IoC of the final columns:

* (a) plant Emerson/Self-Reliance, t = totient + w = DIVINITY (L=8), model 0, keep 0.19
  (q = 0.81), fixed offset 1234: the search over offsets 0..2000 x L 1..20 x models
  {0,1} must return exactly (1234, 8, model 0) with periodic IoC ≥ 1.6 (expect ≈1.9–2.0;
  the single-cell decode already gives 1.986 with wcol = DIVINITY); re-decode at truth
  must give wcol = DIVINITY exactly.
* (b) random-key nulls: ≥ 8 uniform random keys x random windows, same settings (L=8,
  model 0), best periodic IoC < 1.45.
* (c) the no-keyword plant (same t, L=1 constant key) decoded with L=8 must stay < 1.4
  — NOTE: L=1 is nested in the L=8 model class (w = const is an L=8 keyword), so this
  control is expected to FAIL as stated (the decode is a legitimate fit with all-equal
  wcol); if so, report it as a model-identification caveat (a wcol-degeneracy check
  flags it) rather than a decoder bug.
* (d) wrong-L (7, 9, 16, …) at the true offset and wrong offsets (±1, ±100): all < 1.4.
* (e) the plant with the literal-F rule on must be recovered exactly (offset, L) with
  IoC ≥ 1.6.

## LP2 first look (not run)

Grid: the 8 section windows (first 300 runes of work/kscreen/data/segments.txt, prev from
the W line) × offsets 0..2000 × L 2..20 × model 0, t = totient, litf = 0; the same grid
on 8 random streams as the matched null. 8 × 2001 × 19 × 9 = 2,737,368 decodes. Any
window ≥ 1.6 periodic IoC AND ≥ its matched-null max + 0.15 is re-decoded in-process
(beam 64, max_em 10) and reported as a CANDIDATE (not a decryption); the per-window best
is compared with the matched null max.

Runtime scaling: at the verified ~140 ms/decode the grid is ~13 h on 8 workers —
infeasible. With the verified fast init (~5-8 ms/decode) it is ~35-55 min and the init
abort (null cells die at rune 120) keeps it near the low end. Cap 60 min on 8 workers;
report the partial and the scaling if it does not finish.

## What remains for the full library sweep (campaign design)

1. Verify `beam_coincidence_nats_fast` against the slow init (truth pointers + null
   aborts); wire it into `decode()`; re-measure calib timing.
2. Run controls (a)–(e) above (at least (a), (b), (d) gate the LP2 run); write the
   numbers into control.txt and the registry row.
3. LP2 first look as above; report per-window best vs matched null; re-decode and
   whole-section verification for anything ≥ 1.6 per docs/CAMPAIGNS.md (a CANDIDATE is
   not a decryption; only a full-section English verify counts).
4. Library sweep: every stream of work/keystreams.py + the export families (× mult 1,
   28, sign ±1, forward/reverse where meaningful) through the same grid, with its own
   matched-null replicate per stream and the predicted-IoC filter first
   (HYPOTHESES.md:10-14). Cost: ≈1,500 streams × 2 signs × 2001 offsets × 19 L ≈ 10^8
   decodes ≈ 100–300 core-hours in Python — the Rust engine (work/layer2 pattern) is the
   right home once the algorithm is frozen; the Python slice is the reference.
5. Extend later: H2's σ-invariant coincidence statistic, H3 clocked pointers, the
   H1/H2 random-jump add-on, and litf = 1 variants of the LP2 look.
