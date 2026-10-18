# work/h5rs — the Rust engine for the H5 first slice (bit-exact with work/h5slice)

Status: **PARITY GATE PASS (312 checks, 0 fails)** across three Rust engines against the
verified Python reference (`h5slice_nb` init + `h5slice.decode(fast_init=True)`); the truth
cell reproduces exactly (IoC 1.9856, wcol = DIVINITY, 8 skips); the Rust totient is
bit-identical to `h5slice.totient`. Throughput (campaign workhorse = aborting null cells,
engine `fast`, measured on this machine under the multipliers-campaign load):
**3,842 dec/s single-threaded, 16,634 dec/s on 8 threads** (best observed across runs
18.8k; the machine was at ~60-100% total CPU from the campaign + desktop apps). Full truth
decode (init + EM, no abort): 1,167 dec/s single-threaded. The task's **>= 20k dec/s gate
is NOT met under load** (16.6k official / 18.8k best); the CLI and sweep driver below exist
and are parity-gated, but per the task's condition they are provisional until the gate
clears on an idle machine. Details: `parity.txt` (the recorded gate), `parity.py` (the gate
driver).

## What this ports (docs/HYPOTHESES.md H1, first slice)

    c_i = D(p_i) + t_j + w_(j mod L) + b   (mod 29)

* `t` = the library stream "primes-1 (totient)": `t_n = p_n - 1 mod 29`, generated
  internally by a sieve (cross-checked against `h5slice.totient`).
* Decode per (offset, L): a nats-scored coincidence init beam over FREE pointer branches
  (+1/+2/+3 per rune, plus the literal-F branch), scored by the per-column SHIFT-MARGINALIZED
  English log-likelihood `G[col,v] = sum_i logf[(x_i - v) mod 29]`, score =
  `sum_col logsumexp_v G[col,v] + skips*ln(0.028)`; then `est_cols` (per-column ML shift) and
  an EM over the keyword columns with collision-consistency skip branches (model 0 skip with
  keep q = 0.81), scored by the periodic IoC of the final columns (HYPOTHESES.md:70-78).
* Abort (120, 0.9): at the abort_at checkpoint a cell whose best score is below
  `abort_at*(uni + margin) + L*ln(29)` returns without the EM (the recalibrated margin).

The embedded English prior (`logf` = Self-Reliance via work/sim.py, add-0.5 smoothed, and
`uni`, `ln29`, `ln028`) is exported from Python bit-exactly into `src/logf.rs`
(`gen_consts.py`); `parity.py` regenerates and re-verifies it on every run.

## Engines (all three are parity-gated)

* `scalar` — the numba-exact reference port: flat G buffers, one logsumexp of 29 exps per
  candidate, per-pointer merge keeps the FIRST strict maximum, truncation is an ALWAYS-run
  stable sort by -score, the abort fires only at the checkpoint. Same tie-break order as
  `h5slice_nb._kernel`.
* `fastscalar` — the algebraically identical normalized-vector port: the state keeps the
  SUM-1-normalized column vectors `u[col][v] = exp(G - M)/sum`; the score increment of a
  letter with shift q is `ln(sum_v u_v * f[(q-v) mod 29])` (ln(sum u) = 0), so one log per
  candidate, no exponentials, no M/Lc bookkeeping. Scores agree with the reference within
  ~1e-12 nats; the merge/tie-break/abort/traceback semantics are identical.
* `fast` — `fastscalar` + AVX2/FMA (x86_64): SIMD products (bit-identical per lane),
  sequential ascending-v sums (bit-identical to `fastscalar`), copy-on-write arena columns
  (a survivor shares its parent's L-1 columns and writes one new 29-double column - 8x less
  copy traffic), a table-based `fast_ln` for the known sum domain (max error ~2e-13),
  stamp-index merge and a (score-key, candidate-index) tuple sort. `fast` output is
  BIT-IDENTICAL to `fastscalar` on every gate cell.

The reference tie-break semantics are replicated exactly everywhere: per-pointer merge keeps
the first strict maximum in candidate-generation order; truncation sorts by score desc with
first-appearance tie-break (the total order (score desc, t asc) is unique, so the tuple
sort/unstable sort is identical to the reference's stable sort); the abort reads the max
only at the checkpoint; the final best is the first strict maximum.

## Parity gate (parity.py -> parity.txt; 2026-10-18)

* 24 grid cells: offsets {1234, 1000, 1500, 777} x L {7, 8, 12} x models {0, 1}, each with
  init at abort 0 and abort 120 (48 init checks) and full decode at abort 0 and 120
  (48 decode checks) = 96 checks.
* 4 random null windows x random streams (verify_nb phase 4 style): init + decode parity at
  (120, 0.9), 4/4 aborts = 8 checks.
* 104 checks per engine x 3 engines = **312 checks, 0 fails**.
* Gates per cell: init pointer list EXACT, skip count EXACT, score within 1e-9 nats (the
  observed diffs are ~1e-13), decode IoC within 1e-12 (bit-exact in practice), wcol EXACT,
  abort decisions EXACT.
* Truth cell (1234, 8, model 0, no abort): IoC 1.9856, wcol [23,10,1,10,9,10,16,26] =
  DIVINITY, 8 skips - identical in Python and Rust.
* Totient cross-check: `h5rs totient 4000` identical to `h5slice.totient(4000)`.
* Note: `parity.txt` records the gate; after it was recorded, the fast engine's survivor
  sort was changed from a top-b insertion selection to the (key, candidate-index) tuple sort
  (same total order). The final binary re-passed all 104 fast-engine checks (actual_f.txt);
  the scalar/fastscalar engines are unchanged.

## Throughput and projection

Measured on this machine (AMD Ryzen 7 2700X, 16 logical procs) with the engine `fast` on
aborting null cells (random windows x totient, abort (120, 0.9)) - the campaign workhorse
(99.96% of sweep cells abort at the 120 checkpoint):

| measurement (parity.txt run)                  | rate                  |
|-----------------------------------------------|-----------------------|
| null-abort cells, 1 thread                    | 3,842 dec/s           |
| null-abort cells, 8 threads                   | 16,634 dec/s          |
| full truth decode (init + EM), 1 thread       | 1,167 dec/s           |
| repeated runs of the final binary, 8 threads  | 16.2k-18.8k dec/s     |

* **Projection:** 880,000,000 decodes / 16,634 dec/s = 52,903 s = **14.7 h at 8 threads**
  (13.0 h at the best observed 18.8k). CAVEAT: the bench/parity.txt line is mislabeled
  `projection_hours_8_threads` - the printed value is SECONDS, not hours (52,903 s).
* Comparison with Python: `verify_nb` measured 1.47 ms per aborted null init (~680 dec/s
  single-worker), so the Rust fast engine is ~5.6x per core (0.26 ms per cell); against the
  task context's ~2000 dec/s-per-worker figure it is ~1.9x. Against the LP2 look's 4-worker
  wall rates (1,144-1,973 dec/s), the 8-thread Rust wall rate is ~8-15x.

### Why the rate is ~2-5x numba, not 10^5-10^6

The aborting cell does a fixed 120 runes of beam work: per rune, 36 candidates (12-beam x 3
branches) each take one 29-term dot `sum_v u_v * f[(q-v) mod 29]` plus one log, 12 survivors
each write one 29-double column, plus the merge/sort and bookkeeping (~5k uops/rune). Three
things cap the speed:

1. **The dot sum is deliberately sequential ascending-v.** A 4-lane vector accumulation
   passed the 1e-9 score tolerance but flipped an exact-tie beam merge on 2 of the 24 gate
   cells (g1234_7_m0/m1 - the true path dropped out at rune 6, final score off by 1.456
   nats). Bit-parity of the survivor/tie-break order with the reference requires the same
   summation order, so the dominant loop cannot use full-width SIMD reductions.
2. **Zen 1 executes 256-bit AVX2 at half rate** (2x128-bit), so the SIMD products gain less
   than on newer cores.
3. **The machine is shared.** The multipliers campaign (16 threads at ~100%) plus desktop
   apps held total CPU at ~60-100% during the measurements; single-thread runs shared cores
   via SMT and the 8-thread scaling is ~4.3-4.9x.

What was already done to get here: no exponentials (normalized-vector algebra), copy-on-write
arena columns (8x less copy traffic), thread-local scratch (zero allocations per aborting
decode), a table-based fast ln (the 4.3k logs/decode no longer call libm), stamp-index merge
and the tuple-key sort. The remaining headroom (SIMD reductions, fewer logs) breaks the
bit-parity requirement; the engine is compute-bound on the reference algorithm itself.

## CLI

```
h5rs decode <window.txt> <offset> <L> <model> [--engine scalar|fastscalar|fast]
           [--no-abort | --abort <at> <margin>] [--litf] [--beam n] [--max-em n] [--beam-a n]
    -> prints "ioc=<x> wcol=<csv> skips=<n>" or "ABORT"  (totient stream generated internally)
h5rs parity <cells.txt> [actual.txt] [--engine e]        # the gate runner used by parity.py
h5rs sweep <windows.txt> tot|rand:<seed> <off0> <off1> <L0> <L1> <model> <threads> <out.tsv>
           [--hits <t>] [--engine e]                     # the small campaign sweep driver
h5rs bench [--threads T] [--secs S] [--engine e] [--full <truth.txt>]
h5rs totient <n>                                         # cross-check output
```

Window format: kscreen's (W name prev / R runes; L/B lines are ignored - the H5 decode is
word-agnostic); the first 300 runes of each window are used.

## Campaign design (for the later library sweep; NOT run in this task)

* **Grid:** the 8 section windows (first 300 runes of `work/kscreen/data/segments.txt`, prev
  from the W line) x offsets 0..1999 x L 2..20 x models {0,1} x stream, in offset-block-major
  chunks so a wall cap gives every (window, stream, model) the same offset prefix (the
  lp2_look convention).
* **Streams:** the totient pass per window, plus per-window MATCHED NULLS - the same grid on
  uniform random replicate streams (seeds 9000..9007, the lp2_look convention). Full sweep:
  1,447 streams x 8 windows x 2000 offsets x 19 L x 2 models = 880 M decodes.
* **Candidate rule:** a totient-grid cell with periodic IoC >= 1.6 AND >= the window's
  matched-null max + 0.15 is re-decoded WHOLE-WINDOW in Python (`h5slice.redecode`, beam 64,
  max_em 10, verified init) and reported as a CANDIDATE - unverified until the whole-section
  English verification of docs/CAMPAIGNS.md passes. The sweep driver outputs per-window best
  cells and every cell >= the hit threshold for both passes; the candidate assembly (and the
  matched-null maxima) is a thin Python layer over the driver's TSV.
* **Machine budget:** at the measured 16.6k dec/s the full sweep is ~14.7 h at 8 threads
  (~13 h at the best rate); on an idle machine with the same 8 threads it is expected to be
  shorter.

## Semantic divergences found and fixed (all caught by the parity gate)

1. **`_mm256_hadd_pd(pv, pv)` with identical operands is wrong on this target** (LLVM's Zen1
   expansion of same-operand VHADDPD produced [p0+p1, p0+p1, ...] - the first-rune sums were
   off by ~6% and the beam diverged at rune 1). Fixed with register-only lane extraction
   (`vextractf128` + `vunpckhpd`), never hadd with equal inputs.
2. **Stale thread-local stamp ids across decodes** corrupted the merge from the second decode
   onward (stamp ids reset per decode while the stamp array persisted). Fixed with a
   monotonic per-thread stamp base (and starting at 1 - a base of 0 collided with the fresh
   zeroed array on the FIRST decode).
3. **`_mm_shuffle_pd` immediate convention** (the Rust std::arch binding uses 2-bit fields,
   not the classic SSE2 1-bit form) - avoided entirely once the store-based extraction was
   replaced by fix 1.
4. **Vectorized sum-reduction order** (4-lane accumulation) flipped an exact-tie merge on
   g1234_7_m0/m1; reverted to the sequential ascending-v order, making `fast`
   bit-identical to `fastscalar`.
5. **Packed u64 sort key** `(!mb << 8) | t` discarded the top byte of the score bits and
   mis-ordered negative scores; fixed by sorting (u64 score-key, usize candidate-index)
   tuples.
6. **Parity runner argument parsing** (the first positional equal to the default filename
   never advanced the positional counter) - fixed with an explicit counter.
7. **The `decode()` fast-engine dispatch** needed the runtime AVX2/FMA check before the
   `#[target_feature]` call (unsafe-call convention).

## Files

* `src/main.rs` - the whole engine + CLI (std only, no dependencies; layer2 conventions).
* `src/logf.rs` - generated bit-exact Python constants (regenerated by gen_consts.py).
* `parity.py` / `parity.txt` - the mandatory gate and its recorded result (312/0).
* `cells.txt` / `expected.txt` / `actual_{scalar,fastscalar,fast}.txt` - the gate cells,
  the Python reference outputs and the Rust outputs.
* `totient_rs.txt` - the Rust totient cross-check output.
* `data/truth.txt` - the truth plant window (Self-Reliance 3000:3300, totient + DIVINITY,
  offset 1234, model 0, keep 0.19, seed 42) for the CLI/bench.
* `gen_consts.py` - regenerates src/logf.rs from the Python constants.
