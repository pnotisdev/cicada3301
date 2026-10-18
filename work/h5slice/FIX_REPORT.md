# FIX_REPORT.md — H5 init fix session (2026-10-18, session cut short by parent)

## What was done

1. **The fix was applied** to `work/h5slice/h5slice.py`: the sigma-counting coincidence
   init (`beam_coincidence`, free +1/+2/+3 pointer branches scored by the running
   column-coincidence z, the source of blocker B: z ≈ 41σ on BOTH the truth plant and
   random nulls) is **replaced** by a nats-scored init:
   - `beam_coincidence_nats`: beam over the same free branches, scored by the per-column
     **shift-marginalized English log-likelihood** — states keep the log-domain column
     products G[col,v] = Σ logf[(x_i − v) mod 29], score = Σ_col logsumexp_v G[col,v]
     + skips·ln(0.028). The keyword shift of each column is integrated out over the 29
     shifts (uniform prior), so the init stays **w-free** (no keyword knowledge).
   - Per-skip cost = ln(1/0.028) = **3.576 nats** (HYPOTHESES.md:18-20). Per-letter gain
     is bounded by ln(29·f_max) = **1.28 nats** above the uniform-null level (measured
     from the Emerson rune frequencies of work/sim.py, add-0.5 smoothed). A fabricated
     skip therefore can never pay for itself — the mechanism of the old overfit.
   - Measured model constants: H(f) = 2.954 nats (truth LL per rune), uniform-null level
     −4.230 nats per rune → 1.28 nats/rune of drift evidence.
   - The init now feeds its best pointer path into the existing per-column ML shift
     estimate (`est_cols`) and the existing LL-EM (`beam_pass`), unchanged.
   - The EM's internal LL abort is disabled in `decode()`: on the true path the LL is
     mean(logf) per rune exactly, so a margin-above-mean threshold kills the truth plant,
     and nulls overfit the per-column shifts upward so the old uniform-mean threshold
     was a no-op. The init's own checkpoint abort (null level + margin at abort_at
     runes) is the null filter.
   - Bug found and fixed during the session: the init abort must fire ONLY at the
     abort_at checkpoint (`i+1 == abort_at`); the running `>=` check aborts every
     surviving cell on the rune after the checkpoint because the nats score drops
     ~3 nats/rune (the old z score grew with runes, so `>=` was right for it).
   - The old z init is kept as `beam_coincidence_z` (deprecated, for regression
     comparisons). `beam_coincidence_nats_fast` is a **UNTESTED** vectorized-numpy
     rewrite (~20x faster, for the LP2 grid; see Open items).
   - `calib.py` and `run_chunk` call sites were updated to the new `decode()` signature
     (abort_margin now means the init checkpoint margin; `abort_z` removed).

## Which controls ran — HONEST ANSWER

**None of the full controls (a)–(d) ran.** The session was cut short before the control
sweeps. What was verified is a smoke-level subset:

- **Control (a), single-cell part only**: the truth plant (Self-Reliance runes
  3000:3300, totient + DIVINITY at offset 1234, model 0, keep 0.19, seed 42, per
  calib.py) decoded at (1234, 8, model 0) with no abort gives **periodic IoC 1.986**
  (≥ 1.6 ✓) and **wcol = [23,10,1,10,9,10,16,26] = DIVINITY exactly** ✓. The init alone
  finds 8 skips (= the plant's true skip count). The grid search over offsets 0..2000 ×
  L 1..20 × models {0,1} (the "must return exactly (1234, 8, model 0)" part) was NOT
  run.
- **Control (b) (nulls)**: 40 random-window/random-stream decodes at L=8, model 0, with
  the 120-rune checkpoint abort (margin 0.15): **40/40 aborted** (score 0.0) — the old
  z init scored these at z ≈ 41σ, so the overfit is gone at the smoke level. The
  non-aborted tail distribution (the < 1.45 requirement) was NOT measured (every null
  aborted; the smoke loop division-by-zeroed).
- **Control (c)** (no-keyword L=1 plant decoded at L=8): NOT run. Expected to FAIL as
  stated: L=1 is nested in the L=8 model class (w = const is an L=8 keyword), so a
  legitimate fit with all-equal wcol is expected (see README).
- **Control (d)** (wrong-L / wrong-offset < 1.4): NOT run.
- **LP2 first look**: NOT run. No LP2 scores exist.

## Open items / next steps

1. **Verify `beam_coincidence_nats_fast`** against the slow init: same truth pointers
   (skips=8, score −897), decode IoC 1.986 with wcol=DIVINITY, and nulls aborting at the
   120 checkpoint. Then wire it into `decode()`.
2. **Performance**: the verified init costs ~137 ms/decode (Python candidate loop +
   dict merge; profile: 133 ms/call pure bytecode in the function body). The LP2 grid
   (8 windows × 2001 offsets × 19 L × 9 streams = 2,737,368 decodes) needs < ~10
   ms/decode: at 140 ms it is ~13 h on 8 workers. The fast draft targets ~5-8 ms.
3. **Run controls (a), (b), (d)** (at least) with the fast init in place; write
   control.py/control.txt and the registry row.
4. **LP2 first look** with the 60-min/8-worker cap, matched null = 8 random keys on the
   same grid; candidates ≥ 1.6 IoC AND ≥ matched-null max + 0.15 get an in-process
   re-decode and are CANDIDATES, not decryptions.
5. README.md was updated with the fixed algorithm, the smoke numbers, and the open
   items.

## Files

- `work/h5slice/h5slice.py` — fix applied (new init + updated `decode`).
- `work/h5slice/README.md` — updated.
- `work/h5slice/FIX_REPORT.md` — this report.
- `work/h5slice/_smoke.py`, `_dbg.py`, `_dbg2.py` — scratch verification scripts
  (truth plant + null smoke test; beam trajectory; abort isolation). Kept for reuse.
- Nothing was committed (as instructed).
