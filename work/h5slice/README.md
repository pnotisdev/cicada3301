# work/h5slice — H5 first slice (drift-tracking decoder for the two-stack model)

Status: **CONTROLS PASS, NUMBA INIT VERIFIED AND WIRED, LP2 FIRST LOOK RUN — NO
CANDIDATES.** The nats-scored coincidence init (`beam_coincidence_nats`, blocker B fix)
is unchanged and remains the verified reference. Its numba port (`h5slice_nb.py`) passed
every gate the v3 rewrite passed (48/48 init parity, 24/24 decode parity, truth plant,
40/40 null aborts) and is 15-17x faster than the slow init on this machine; `decode()`
with `fast_init=True` uses it (numpy v3 fallback if numba is missing). Controls (a), (b),
(d) PASS (control.txt). The capped 45-min LP2 first look ran 5,327,600 cells with
partial-grid accounting; best real periodic IoC 1.4840 vs matched-null maxima 1.36-1.53 —
no setting reached the 1.6 candidate bar, so **no candidates** (lp2_look.txt). Details:
`FIX_REPORT.md` (blocker fix), `FAST_REPORT.md` (abort recalibration), `V3_REPORT.md`
(v3 verification + why v3 was not faster), `verify_nb.log` (this session's numba gates).

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

* `h5slice.py` — the decoder: streams (`totient`, `random_stream`), `plant` (independent
  two-stack encryptor with the anti-repeat rule, mirrors work/layer2's plant on the
  combined key), `decode` (two-stage algorithm below; `fast_init=True` = the numba init),
  `beam_coincidence_nats` (the slow, verified nats-scored init — the reference),
  `beam_coincidence_nats_fast` (v3 numpy corr-trick rewrite: parity-verified but only
  1.0-1.1x, superseded by numba; kept as the numba fallback), `beam_coincidence_z`
  (deprecated z-scored init, kept for regression comparisons), `decode_t_only` (L = 0,
  the blind old-screen view), `periodic_ioc`, `load_windows` (kscreen window format), the
  multiprocessing sweep (`run_sweep`, `init_worker`, `run_chunk` — `run_chunk` passes
  `fast_init` through) and `redecode`/`latin_render` for verification.
* `h5slice_nb.py` — the numba port of the init (VERIFIED; exact slow semantics: first
  strict max per pointer, stable sort by -score with the abort checkpoint reading the
  max, 1-D flat buffers). Compiles once, cached on disk.
* `verify_nb.py` / `verify_nb.log` — the numba gate suite (the v3 gates re-run against
  the numba init): 48 init-parity cells, 24 decode-parity cells, truth cell (IoC 1.986,
  wcol = DIVINITY, 8 skips), 40/40 null aborts at (120, 0.9), timing.
* `verify_fast.py` / `verify_fast_v3.log` — the v3 rewrite's gate suite (its 5x speed
  gate FAILED for v3: 1.0-1.1x; the numba port is what met it).
* `control.py` / `control.txt` — the controls (a)-(d) driver and results (see below).
* `lp2_look.py` / `lp2_look.txt` — the capped LP2 first look (45-min cap, 4 workers,
  exact partial-grid accounting) and its report.
* `calib.py` — the calibration script (its numbers are superseded by the sections below).
* `FIX_REPORT.md` — the init-fix session report. `FAST_REPORT.md` — abort recalibration
  (margin 0.9) and the v2/v3 history. `V3_REPORT.md` — v3 verification + speed failure.
* `_smoke.py`, `_dbg.py`, `_dbg2.py`, `_nb_check.py`, `_bench.py`, `_diag_abort.py`,
  `_v3quick.py`, `_prof_v3.py` — scratch scripts from the fix/fast/numba sessions.

## Algorithm as implemented (`h5slice.decode`)

Outer loop over (offset, L); inner EM over the keyword columns:

1. **Nats-scored coincidence init pass** (`beam_coincidence_nats`; the numba port is
   what `fast_init=True` runs): a beam over FREE pointer branches (+1, +2, +3 per rune,
   plus the literal-F branch), scored by the per-column SHIFT-MARGINALIZED English
   log-likelihood: each state keeps the log-domain column products
   G[col, v] = sum_i logf[(x_i - v) mod 29], scored as
   sum_col logsumexp_v G[col, v] + skips * ln(0.028). The keyword shift of each column is
   integrated out over the 29 shifts (uniform prior), so the pass is **w-free** (no
   keyword knowledge). A letter placed in a column adds at most ln(29 f_max) ~ 1.3 nats
   of evidence above the uniform-null level, while one skip costs ln(1/0.028) = 3.58
   nats (HYPOTHESES.md:18-20): a fabricated skip can no longer pay for itself (the old
   z-scored version reached z ~ 41 sigma on both truth and nulls). The beam buys the
   REAL skips on truth because re-alignment is worth ~1.2 nats per later rune.
   Early abort: at the abort_at checkpoint (rune 120) a cell whose best score is below
   the unigram-null level + margin is a dead null and returns without the EM. The
   recalibrated margin is **0.9** (FAST_REPORT.md sec 2: truth δ +1.011 at rune 120 vs
   null tail max δ 0.863; the README's earlier "40/40 abort at margin 0.15" claim was
   wrong — at 0.15 no null aborts and the truth plant dies too).
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

## Numba verification (this session, verify_nb.py -> verify_nb.log)

Compared `h5slice_nb.beam_coincidence_nats_numba` against the slow verified
`beam_coincidence_nats` on the truth plant (Self-Reliance 3000:3300, totient + DIVINITY
at offset 1234, model 0, keep 0.19, seed 42 — the calib.py plant):

* **Init parity, 48 checks** (offsets {1234, 1000, 1500, 777} x L {7, 8, 12} x models
  {0, 1}, each at abort 0 and 120): **48/48 PASS** — exact pointer-list equality, same
  skip count, score diffs ~2e-13 nats (tolerance 1e-6), same abort decisions.
* **Decode parity, 24 cells** (decode(fast_init=True) vs False, abort 120): **24/24**.
* **Truth cell no abort**: both give **IoC 1.986**, **wcol = [23,10,1,10,9,10,16,26] =
  DIVINITY exactly**, **8 skips** (= the plant's true skip count), ll/rune −2.901,
  identical pointers.
* **40 random nulls** (L=8, abort 120/0.9): init + decode parity on all 40, **40/40
  aborted** through the wired numba path.
* One numba bug fixed during the port review: the truncation sort ran only when the
  survivor count exceeded the beam, so the abort checkpoint could read the first-inserted
  candidate instead of the max (the slow reference sorts unconditionally and reads the
  max). The sort now runs always; re-verified 22/22 in `_nb_check.py` before the gates.

### Speed (the >= 5x task gate — MET)

Machine: 16 logical procs, screen campaign load ~97%; Python 3.14.6, numpy 2.5.2,
numba 0.67.0. Numbers vary with the campaign load; verify_nb.log's run at moderate load:

| measurement                          | slow init | numba    | speedup |
|--------------------------------------|-----------|----------|---------|
| truth cell init (300 runes)          | 65.0 ms   | 3.82 ms  | 17.0x   |
| null cell init w/ abort (120 runes)  | 25.4 ms   | 1.47 ms  | 17.3x   |
| truth full decode (init + EM)        | 73.9 ms   | 13.64 ms | 5.4x    |
| null decode w/ abort                 | 25.2 ms   | 1.46 ms  | 17.3x   |

(Under heavier load the same run measured 15.1x / 15.9x / 6.2x / 14.3x; `_nb_check.py`
under full load saw 18.5-23.8x on the init.) The >= 5x gate holds on every measurement;
**the Rust port is not needed for this slice.**

## Controls (control.py -> control.txt; ALL PASS, 2026-10-18)

Abort (120, 0.9), fast_init=True (numba), 4 workers, 45-min cap per grid.

* **(a) truth grid** offsets 0..2000 x L 1..20 x models {0,1} on the truth plant:
  80,040 decodes, 162/162 chunks in 107 s (748 decodes/s wall, 4 workers; 99.98% aborted
  at the 120 checkpoint). **Grid argmax = IoC 1.9856 at exactly (1234, 8, model 0)**;
  re-decode at truth gives **wcol = DIVINITY exactly**. Runners-up ≤ 1.3166 (best wrong
  cell 1.3166 at (182, 10, model 1)). **PASS.**
* **(b) nulls**: 8 random-window/random-stream nulls over the same grid: 640,320
  decodes, 1296/1296 chunks in 560 s (1144 decodes/s wall). Per-null max periodic IoC
  1.2219..1.3537; **global max 1.3537 < 1.45. PASS.**
* **(c) L=1 degeneracy (recorded, not a failure)**: the no-keyword plant (L=1 constant
  key) decoded at L=8 gives IoC 2.1830 with wcol all-equal [7,7,7,7,7,7,7,7] — a
  legitimate fit because a constant keyword IS an L=8 keyword. This is a
  model-identification caveat (a wcol all-equal check flags it), NOT a decoder bug.
* **(d) wrong-L / wrong-offset**: truth plant at L ∈ {7, 9, 16} and at offsets
  ±1, +100: all **abort** (IoC 0.0) < 1.4. **PASS.**

## LP2 first look (lp2_look.py -> lp2_look.txt)

Grid: the 8 section windows (first 300 runes of work/kscreen/data/segments.txt, prev from
the W line) × offsets 0..2000 × L 2..20 × models {0,1} × 9 streams (totient + 8 uniform
matched nulls, seeds 9000..9007) = 5,474,736 cells. Abort (120, 0.9), fast_init=True,
4 workers, **45-min wall cap**; chunks (25 offsets × 19 L) are submitted in
offset-block-major order so the cap gives every (window, stream, model) combo the same
offset prefix, and the report records the exact completed chunks. Candidate rule: a
totient-grid cell with periodic IoC ≥ 1.6 AND ≥ the window's matched-null max + 0.15 is
re-decoded in-process (beam 64, max_em 10, slow verified init) and reported as a
CANDIDATE — flagged UNVERIFIED, not a decryption.

Results (lp2_look.txt, run 2026-10-18; abort 120/0.9, numba fast_init, 4 workers):

* **Partial grid**: 11,216/11,664 chunks = 5,327,600/5,474,736 cells in the 45-min cap
  (2700 s, 1973 decodes/s wall; 99.96% of cells aborted at the 120 checkpoint — 2,244
  cells survived the abort). Coverage: offsets **0..1949** complete for every
  (window, stream, model) combo except seg0.15's 8 matched-null streams (offsets
  0..1924); the only cells NOT run are offsets 1950..2000 for all combos and offsets
  1925..1949 for seg0.15's null streams (147,136 cells).

| window   | best real IoC | @ (off, L, model) | matched-null max | null cells survived | hits >= 1.6 |
|----------|---------------|-------------------|------------------|---------------------|-------------|
| seg0.7   | 1.2683        | (736, 17, 0)      | 1.4714           | 244                 | 0           |
| seg0.8   | 1.3424        | (25, 18, 0)       | 1.4110           | 208                 | 0           |
| seg0.9   | 1.3335        | (1380, 18, 0)     | 1.5306           | 226                 | 0           |
| seg0.11  | 1.4840        | (1160, 19, 1)     | 1.4914           | 322                 | 0           |
| seg0.12  | 1.3114        | (497, 12, 0)      | 1.4776           | 276                 | 0           |
| seg0.13  | 1.2377        | (343, 13, 0)      | 1.3635           | 258                 | 0           |
| seg0.14  | 1.3925        | (1255, 17, 1)     | 1.4500           | 250                 | 0           |
| seg0.15  | 1.3924        | (385, 20, 1)      | 1.4362           | 254                 | 0           |

* **Candidates: NONE.** No totient-grid cell reached periodic IoC 1.6 anywhere on the
  completed grid (0 hits >= 1.6), so the candidate rule (>= 1.6 AND >= matched-null max
  + 0.15) triggered no whole-window re-decodes. The best real cell on LP2 is seg0.11's
  1.4840 at (offset 1160, L 19, model 1), below its own window's matched-null max
  (1.4914) and below the 1.6 bar. The matched-null maxima on the REAL section windows
  (1.36-1.53) sit above control (b)'s random-window null max (1.35) because the real
  ciphertext distribution is not perfectly uniform and more null cells survive the
  abort — this is exactly the effect the matched-null design is there to absorb.
* Interpretation: H5 with the totient stream, first 300 runes per section, offsets
  0..1949, L 2..20, models {0,1}, finds nothing above noise on any LP2 window. That is
  a first-look negative, not an exclusion: litf = 1 variants, the other library streams,
  H2/H3 pointer models and the remaining 51 offset values are still unexamined, and any
  future hit needs whole-section English verification (docs/CAMPAIGNS.md) before it
  counts.

## What remains for the full library sweep (campaign design)

1. ~~Verify the fast init against the slow init; wire it into `decode()`~~ DONE —
   the numba port (h5slice_nb.py) passed all gates and is wired as fast_init=True.
2. ~~Run controls (a)-(d); write control.txt~~ DONE — PASS.
3. ~~Capped LP2 first look~~ DONE — see lp2_look.txt. Anything ≥ 1.6 per window vs its
   matched-null max + 0.15 needs whole-section verification per docs/CAMPAIGNS.md before
   it counts (a CANDIDATE is not a decryption).
4. Library sweep: every stream of work/keystreams.py + the export families (× mult 1,
   28, sign ±1, forward/reverse where meaningful) through the same grid, with its own
   matched-null replicate per stream and the predicted-IoC filter first
   (HYPOTHESES.md:10-14). Cost: ≈1,500 streams × 2 signs × 2001 offsets × 19 L ≈ 10^8
   decodes ≈ 20-60 core-hours in Python at the measured numba rates — the Rust engine
   (work/layer2 pattern) remains the right home for the FULL campaign once the algorithm
   is frozen; the Python numba slice is the reference.
5. Extend later: H2's σ-invariant coincidence statistic, H3 clocked pointers, the
   H1/H2 random-jump add-on, and litf = 1 variants of the LP2 look.
