# V3_REPORT.md — v3 verification session, STOPPED by parent at budget expiry (2026-10-18)

Honest status: **v3 parity is VERIFIED (after fixing one real bug), but v3 is NOT faster
(1.0-1.1x vs the slow init) - the task's >=5x gate FAILS.** Controls (a)/(b)/(d), the LP2
first look, and the README update did **NOT** run. Session stopped by the parent on budget
expiry before the follow-up optimization attempt could be verified.

## 1. v3 bug found and fixed (before verification)

`beam_coincidence_nats_fast` had a state-carry bug: after the survivor write, `Lcm` and
`Mmax` rows were refreshed ONLY for the column that just received a letter; all other
columns kept the previous row-slot occupant's stale values, so the next rune's
`lse1 = Lcm[par, col]` read a stale column logsumexp and corrupted every score. Fixed in
`h5slice.py` by copying the FULL parent rows (`Lcm[:m2] = Lcm[par[surv]]`,
`Mmax[:m2] = Mmax[par[surv]]`) before the column update. This is the only v3 bug found.

## 2. Parity verdict — PASS on every cell

`verify_fast.py` (updated to the recalibrated abort `abort_at=120, abort_margin=0.9` and
the task's 5x timing gate; full output in `verify_fast_v3.log`):

* **Phase 1, init parity, 48 checks** (offsets {1234, 1000, 1500, 777} x L {7, 8, 12} x
  models {0, 1}, each at abort 0 and 120): **48/48 PASS** — exact pointer-list equality,
  same skip count, same score within 1e-6 nats (measured ~2e-13), same abort decisions.
* **Phase 2, decode parity, 24 cells** (fast_init True vs False, abort 120): **24/24 PASS**.
* **Phase 3, truth cell no abort**: both slow and fast give **IoC 1.986**,
  **wcol = [23,10,1,10,9,10,16,26] = DIVINITY exactly**, ll/rune -2.901, identical
  pointers. (Reproduces the smoke numbers.)
* **Phase 4, 40 random nulls** (L=8, abort 120/0.9): slow and fast agree on all 40; with
  the RECALIBRATED margin **40/40 aborted** (the truth cell survives the same abort).
  The recalibrated abort is thereby re-confirmed: nulls die at the 120 checkpoint, the
  truth plant passes.
* **Phase 5, merge tie-break micro-check**: ok.
* Extra (from the pre-harness quick check): (1234, L=16) and (1234, L=7) abort at
  (120, 0.9) in BOTH versions — the L=16 super-period degeneracy does not threaten
  control (a)'s argmax.

## 3. Speed verdict — FAIL (the >=5x gate is not met here)

Machine: 16 logical processors at ~100% load (screen campaign), Python 3.14.6,
numpy 2.5.2, numba 0.67.0 present.

| measurement                          | slow init  | v3 fast    | speedup |
|--------------------------------------|------------|------------|---------|
| truth cell init (300 runes)          | 107.1 ms   | 98.6 ms    | 1.1x    |
| null cell init w/ abort (120 runes)  | 45.7 ms    | 46.8 ms    | 1.0x    |
| full truth decode (init+EM)          | 119.6 ms   | 122.7 ms   | 1.0x    |
| null decode w/ abort                 | 44.6 ms    | 44.4 ms    | 1.0x    |

**Task gate: >=5x. Measured: 1.0-1.1x. FAIL -> per the task, stop after verification and
report; a Rust port becomes the recommendation.**

## 4. Why v3 is not faster (profiled)

cProfile on the v3 init: ~88 ms/decode of pure function-body time; 600 `np.tile` calls
per decode (the `_toff/_costt.setdefault(...)` defaults are evaluated eagerly EVERY rune);
~20 numpy calls per rune, each costing ~20-170 us under the saturated CPU
(`_bench.py` re-run: candidate build 64 us, direct lse2 74 us, merge 78 us, corr matmul
128 us, survivor update 68 us). The corr trick removed the slow version's scatter-add
pair, but per-call numpy overhead under load eats the entire gain. In numpy-Python the
per-rune call-count floor (~10-20 calls x ~10 us) makes 5x (<= ~74 us/rune on aborted
cells) implausible while the campaign saturates the machine.

## 5. Follow-up started but NOT verified (parent stopped the session)

* `h5slice_nb.py` (NEW): a numba port of the init with exactly the slow version's
  semantics (merge = first strict max per pointer, stable truncation by -score, abort
  only at the checkpoint; buffers flattened to 1-D). One compile-time typing bug was
  found and fixed (2-D `G` indexed flatly), but the parity check (`_nb_check.py`,
  scratch) was **NOT run** - the numba path is UNVERIFIED and must not be wired in yet.
  Expected 10-50x if parity holds (numba 0.67.0 is installed).
* `control.py` (NEW): controls (a)/(b)/(d) + the (c) degeneracy record, 4 workers,
  45-min cap per grid, exact partial-grid accounting, writes `control.txt`. Written but
  **NOT run**; `control.txt` does not exist.

## 6. What did NOT run — honest list

* Controls (a), (b), (d): NOT run. No control numbers exist.
* Control (c): NOT run (only the record-the-degeneracy note is written in control.py).
* LP2 first look: NOT run. No LP2 scores exist. At the measured 44 ms/decode the grid
  (1,216,608 cells on 4 workers) is ~3.7 h; controls (b) alone ~2 h.
* `decode(fast_init=True)` was NOT wired as the default (v3 failed the 5x gate; the
  default remains the verified slow init).
* `README.md` / `FIX_REPORT.md` NOT updated.

## 7. Recommendation

Rust port of `beam_coincidence_nats` (the README's planned step 4), OR verify
`h5slice_nb.py`'s numba kernel against the slow reference (reuse `_nb_check.py` +
`verify_fast.py` phase 8; 48 init cells + 24 decode cells + truth + 40 nulls, same
1e-6-nats tolerance) and wire it only if parity passes and speedup >= 5x. Then run
`control.py` and the LP2 look.

## Files touched this session (none committed)

* `h5slice.py` — v3 Lcm/Mmax staleness bug fixed (verified by the harness).
* `verify_fast.py` — margin 0.9, 5x gate, phase 7 decode-level timing added;
  `verify_fast_v3.log` = the run.
* `h5slice_nb.py` — NEW numba init port (UNVERIFIED, do not wire yet).
* `control.py` — NEW controls driver (NOT run).
* `_v3quick.py`, `_prof_v3.py`, `_nb_check.py` — scratch.
