# FAST_REPORT.md — fast-init verification session, CUT SHORT by parent (2026-10-18)

Honest status of work/h5slice after the fast-init verification session. The session was
stopped mid-flight: the parity verification and abort recalibration are DONE, the v3
speed rewrite is written but **NOT RUN**, the controls (a)/(b)/(d) and the LP2 first look
did **NOT** run. Do not run any sweep on this code until the steps below are completed.

## 1. What was verified (fast vs slow parity) — on the FIXED v2 vectorized rewrite

`verify_fast.py` (new, kept) compares `beam_coincidence_nats_fast` against the slow
verified `beam_coincidence_nats` on the truth plant (Self-Reliance 3000:3300, totient +
DIVINITY at offset 1234, model 0, keep 0.19, seed 42 — the calib.py plant):

* **Init-level parity, 24 cells** (offsets {1234, 1000, 1500, 777} × L {7, 8, 12} ×
  models {0, 1}), each at abort_at=0 and abort_at=120: **48/48 PASS** — same top pointer
  path (exact list equality), same skip count, same score (|Δ| ≤ 1e-6 nats, in fact
  bit-identical or last-ulp), same abort decisions.
* **Decode-level parity, 24 cells** (decode(fast_init=True) vs False, abort 120):
  **24/24 PASS** — same IoC and same wcol/None.
* **Truth cell, no abort**: both give **IoC 1.986**, **wcol = [23,10,1,10,9,10,16,26] =
  DIVINITY exactly**, ll/rune −2.901, identical pointers. (Reproduces the smoke numbers.)
* **40 random nulls** (L=8, abort 120): fast and slow agree on all 40 (init parity +
  decode parity); **0/40 aborted** — see section 3, the README's "40/40 abort" claim does
  NOT reproduce.
* **Merge tie-break micro-check**: equal (nj, s2) ties resolve to the smallest candidate
  index, matching the slow version's dict-merge semantics.

### Bugs found and fixed in the v2 draft (the task said "three bugs fixed on review"; the
code as found still had these)

1. **Node-id chain corruption (critical).** `parents.extend(ndm[par[surv]].tolist())` ran
   AFTER `ndm[:m2] = ndm[par[surv]]` overwrote slots 0..m2−1 (and par[surv] ⊂ [0,W) with
   W ≤ m2), so parents recorded parent-of-parent ids; worse, `ndm` held *parent* node ids
   instead of each state's OWN node id (the slow version sets `nd2 = len(ks_all)−1` after
   appending). Result: `ndm` stayed −1 forever and the fast path returned an EMPTY
   pointer list. Fixed: `ndm[:m2] = arange(base, base+m2)` (own ids) and
   `parents.extend(pnodes)` with `pnodes = ndm[par[surv]]` read BEFORE the overwrite.
2. **Out-of-bounds read**: `kk = maximum(kidx, 0)` was not clamped, so `ts_arr[kk]` could
   read past the stream when pointers grew beyond tlen (slow version pads with kidx=0).
   Fixed: `kk = minimum(maximum(kidx,0), tlen−1)`; invalid candidates are killed by the
   −1e18 cost either way.
3. **Truncation tie-break divergence**: the truncation sort used unstable `argsort` and
   would tie-break by nj-order instead of the slow version's candidate-index order. Fixed:
   `surv = sort(surv); surv = surv[argsort(-s2[surv], kind="stable")[:B]]`.

### Performance — the open problem (NOT solved at stop time)

Measured on this machine (100% CPU, 16 logical procs: screen campaign + browsers; Python
3.14.6, numpy 2.5.2):

* slow init, truth cell: **167.6 ms** (230.4 ms in _smoke.py; 137 ms was the pre-fix
  claim on an idle machine) — **the fixed v2 fast init: 191.7 ms (0.9×) — SLOWER**.
* null cell with abort 120: slow 170.6 ms, v2 fast 140.7 ms (1.2×).

The Python loop + dict merge were never the bottleneck: the slow version's cost is the
per-rune numpy fancy scatter-add `G2[rows,idx] += MT[ql]`, the matching gather, and
`np.stack(G)` (~74 + 74 + 50 µs of the ~550 µs/rune, load-inflated; micro-numbers in
`_bench.py`). The **≥10x faster** requirement is **NOT met** by v2.

### v3 rewrite (corr trick) — WRITTEN, NOT RUN, UNVERIFIED

`beam_coincidence_nats_fast` was rewritten (v3) to remove the scatter/gather pair via the
log-domain cyclic-correlation identity

    logsumexp_v (g_v + MT[q][v]) = log( Σ_v exp(g_v − m) · f[(q−v) mod 29] ) + m,   m = max_v g_v

(one (N,29) gather + one exp + one 29×29 matmul + one log per rune, preallocated
buffers, cached per-(nb,W) templates, js kept as an int64 array, dict merge with the
slow version's exact first-max/strict-> semantics). Estimated ~55–100 µs/rune under the
current load (3–6× vs slow; possibly better when the campaign finishes), but **nothing
was executed**: parity against the slow init and the timing are UNMEASURED. The
last-ulp differences of the matmul summation vs the slow logsumexp are expected to stay
far inside the 1e-6 nats tolerance, but this is exactly what verify_fast.py must confirm.

**`decode()` safety**: `decode(..., fast_init=...)` defaults to **False** (the verified
slow init). It was briefly defaulted True; reverted in this session so no sweep can pick
up the unverified v3 by accident. After v3 passes verify_fast.py, flip the default back
and re-run the timing phase.

## 2. Abort recalibration — the README smoke claim does NOT reproduce

README.md / FIX_REPORT.md claim "40/40 random nulls abort at the 120-rune checkpoint
(margin 0.15)". Re-running `_smoke.py` on the current code: **0/40 aborted** (non-aborted
IoC mean 1.056, max 1.226; 208.8 ms/decode). The truth parts DO reproduce (IoC 1.986,
DIVINITY exact, 8 skips, score −897.1). The 40/40 claim was almost certainly measured
with the pre-fix running `i+1 >= abort_at` check (a null's score crosses the fixed
threshold around rune 140) — which would also have killed the truth plant around rune
155, so the claim was inconsistent with the code as committed.

Measured init-score distributions (30 nulls per cell, `_diag_abort.py`), as effective
nats/rune above `uni_mean_logf()` = −4.2303, i.e. (score − L·ln29)/runes − uni:

| cell                     | checkpoint 120        | checkpoint 200        |
|--------------------------|-----------------------|-----------------------|
| truth plant, L=8         | δ = **+1.011**        | δ = +1.075 (300: 1.150)|
| null L=2                 | mean +0.592, max +0.701 | mean +0.570, max +0.633 |
| null L=8                 | mean +0.725, max +0.803 | mean +0.679, max +0.775 |
| null L=12                | mean +0.781, max +0.854 | mean +0.718, max +0.802 |
| null L=16                | mean +0.802, max +0.863 | mean +0.757, max +0.805 |
| null L=20                | mean +0.816, max +0.859 | mean +0.785, max +0.822 |

The logsumexp curvature puts nulls ≈0.6–0.86 nats/rune above the "uniform-null level",
so the old margin 0.15 can never abort them; a margin of **≈0.9 at the 120 checkpoint**
separates the truth plant (δ 1.011) from the null tail (max δ 0.863 in 30 samples) with
~0.11–0.15 nats/rune of headroom on both sides. This is the recommended sweep setting
(`abort_at=120, abort_margin=0.9`), to be re-validated on the controls before the LP2
look. A 120 checkpoint separates at ALL L (the L·ln29 terms cancel); a later checkpoint
adds truth headroom but costs 67% more init work.

## 3. Controls (a)/(b)/(d) and LP2 first look — NOT RUN

* control.py / control.txt: not written, not run. Control (a) (grid 2001×20×2 = 80,040
  cells must return exactly (1234, 8, model 0), IoC ≥ 1.6, wcol = DIVINITY), (b) (8 nulls
  over the same grid < 1.45), (d) (wrong-L {7,9,16} and wrong offsets < 1.4) — all
  pending. (c) skipped by instruction (model-class degeneracy).
* LP2 first look (8 windows × 2001 offsets × L 2..20 × 2 models × 9 streams =
  5,474,736 decodes, 60-min/8-worker cap): not run. No LP2 scores exist.

## 4. Budget reality check (for whoever continues)

* Machine was at 100% CPU on 16 logical processors for the whole session (screen
  campaign + firefox/claude/discord). All timings above are load-inflated; the ≥10x and
  <10 ms/decode targets are judged against the load present at measurement time.
* With the verified slow init (~170–230 ms/decode) the LP2 grid is ~2.4 core-months —
  infeasible. With v3 verified at the estimated ~15–30 ms/decode it is still 20–45
  core-hours (partial grid at the 60-min cap). The durable fix is the Rust engine port
  already planned in the README; the Python slice remains the reference.

## 5. Next steps (in order)

1. Run `verify_fast.py` against **v3**: parity (48 init checks, 24 decode cells, truth
   cell IoC 1.986 + DIVINITY, 40 nulls) must pass before anything else; then the timing
   phase (≥10x vs slow). Fix any divergence, do not silently relax the check.
2. If ≥10x cannot be met in numpy-Python under load, either wait for the campaign to
   finish, or go straight to the Rust port (README step 4).
3. Set the abort to `abort_at=120, abort_margin=0.9` (recalibrated; document the change
   and the dead 0.15 claim in README/FIX_REPORT).
4. Write control.py, run controls (a), (b), (d); record in control.txt.
5. Only if all controls pass: the capped LP2 first look (both models, 8 matched nulls,
   60-min/8-worker cap, exact partial-grid accounting).

## Files touched this session (none committed, as instructed)

* `h5slice.py` — v2 bugs fixed; v3 `beam_coincidence_nats_fast` written (UNVERIFIED);
  `decode(fast_init=False)` default restored to the verified slow init.
* `verify_fast.py` — new parity/timing harness (run against v2: all parity PASS, timing
  FAIL for ≥10x).
* `_bench.py` — new micro-benchmarks of the per-rune numpy ops (load-inflated numbers).
* `_diag_abort.py` — new abort-calibration diagnostic (the δ table above).
* `_smoke.py` — untouched; re-run only (truth OK, null abort claim dead).
* `FAST_REPORT.md` — this report.
* `README.md` / `FIX_REPORT.md` — NOT updated (their "40/40 abort", "UNTESTED fast path"
  and performance claims need the rewrite that only the completed steps above justify).
