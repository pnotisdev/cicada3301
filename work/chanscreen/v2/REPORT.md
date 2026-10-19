# chanscreen v2 — sparse all-offset engine validated; calibration budget stop

**Nothing in LP2 is solved. No LP2 search was launched.**

R1 and R2 are confirmed for the unchanged v1 channels: two plaintext classes per
pointer suffice (one for skip variants), and a single backward pass scores ALL
start offsets. A Float64 Rust implementation with per-state log probabilities
now runs without a lossy cascade. v1 and M04 are unchanged: **1,241 files verified
against the first-step SHA-256 snapshot**, including the original G3 failure.

## Gate status

| Gate | Status | Evidence |
|---|---|---|
| E0 exactness | **PASS** | 340,800 exact Fraction comparisons against BOTH v1 forward DP and event tree; 96,000 all-offset passes; 34,080 normalized trees; 405 extra finite-tail offset checks; all seven mutations detected. |
| E1 fixed regression | **PASS** | All593,920 stored cal/held scores and all100,020 unchanged seed1703 inputs checked. Largest log error1.319e-11, score error1.274e-11 nats, below1e-9. Support matches. |
| E2 throughput / scope | **PASS** | n300/600 x m2000/20000 x five channels x two signs measured, single-thread and four-worker batches. Real library lengths inventoried. Cost is a projection, not a completed campaign. |
| E3 real-bank null / threshold | **INCOMPLETE** | Preflight cost exceeds remaining authorized compute; zero real-bank null windows evaluated. Numeric threshold and LM-mismatch power unknown. |
| E4 library-scale power | **INCOMPLETE** | No frozen numeric E3 threshold; zero of200 new library-scale plants run. |
| E5 campaign package | **INCOMPLETE** | Blocked by E3/E4. No runnable campaign queue, no LP2 search. |
| g3b | **INCOMPLETE / not triggered** | Campaign projection on14 threads is below8h, so the conditional GPU branch was not entered. No GPU compilation or kernel run. |

No v2 correctness gate failed. This is an explicit **budget stop**, not a tuned
negative or a claim that the entire requested pipeline is complete.

## Exactness and scaling

See `PROOF.md` for the last-event proof of R1, backward DAG recurrence, U's
one-state reduction and linear-time uncapped-skip tail recurrence. The previous
plaintext label is part of the sparse state; distinct labels are never merged.
The all-offsets suffix trellis is independent of the starting offset. Coin's
extra discarded slot and skip5's channel-defined cap are preserved exactly.

Rust precomputes equal-key run ends. For repeated observed outputs, uncapped skip
uses a right-to-left weighted tail recurrence; for nonrepeats only the first
noncolliding key after the run can emit. Thus even long constant-key runs need
O(n*m), not O(n*m*m). No tail mass is silently discarded or renormalized;
exhaustion remains a failure atom under the v1 specification.

Every dynamic value is a Float64 log probability. There is **no shared row scale**
and no band/beam/prefilter. An adversarial test retained finite log probabilities
at offsets separated by **12,433.96 nats**, rather than underflowing the worse
offset because of the better one. Float64 roundoff is still possible; this is
not an arbitrary-precision computation.

The immutable v1 threshold has **one calibration cell within1e-9 of equality**.
It is flagged ambiguous, not silently reassigned. Every tested threshold decision
outside that margin matches. This is not a new calibration or power claim.

E0 mutants: hold spends key, coin omits coin slot, skip drops tail, replacement
uses divisor Q; wrong r-class merge, wrong terminal key-end boundary, omitted
restoration of a backward row's scale. Their exact witness cases are retained
in `e0.json`. Coin reaches only one class in the tiny m<=3 grid; a separate m4
unit test demonstrates its possible two-class support, so the bound is not
inferred merely from the small grid.

## E1 coverage and reproducibility

- Stored v1 records:200 calibration +380 held-out, all1,024 scores each, using
  the stored cipher/bank arrays, v1 model and original stratum-specific q fits.
  No plant regeneration, source refitting, new held-out seeds or retuning.
- All100,020 stored `gpu_parity.npz` inputs checked against the v1 dense Rust
  reference; first10 and **all520 long/plant cases** also checked directly with
  NumPy v1 forward DP. The previously uncomputed v1 GPU arrays were NOT treated
  as expected answers. No GPU result is claimed.
- An additional115,020 tiny offset comparisons check the new Rust arithmetic
  against rational expectations. The all-zero and sparse LM cases are covered
  by unit tests.
- Full gate raw arrays and summaries: `e1_parts/`; inputs remain in immutable v1.
  `e1.json` checks disjoint-block coverage. All blocks run once.
- Unit suite: **6/6 PASS, 36.15 seconds, zero skips**, including full E0 and
  the tiny Rust/scaling checks. It does not rerun the long E1 set or any power
  seeds. `tests.txt`, `RUNNING.md`.

## Measured throughput

A pass computes **both log_L and log_U for every offset**, for one ciphertext,
stream, sign and channel. Table entries average the two sign-specific medians
(each sign: one warmup then three timed calls). Raw individual timings and
checksums are retained in `e2_rows/` and `e2.json`; inputs in `e2_inputs.npz`.

| n | key length | channel | seconds/pass | passes/s | offsets/s, one thread |
|---:|---:|---|---:|---:|---:|
|300|2,000|hold|.063059|15.86|31,716|
|300|2,000|spend|.061570|16.24|32,483|
|300|2,000|skip|.012829|77.95|155,900|
|300|2,000|skip5|.017642|56.68|113,366|
|300|2,000|coin|.015993|62.53|125,055|
|300|20,000|hold|.651674|1.53|30,690|
|300|20,000|spend|.633286|1.58|31,581|
|300|20,000|skip|.133736|7.48|149,548|
|300|20,000|skip5|.157490|6.35|126,992|
|300|20,000|coin|.159284|6.28|125,562|
|600|2,000|hold|.127741|7.83|15,657|
|600|2,000|spend|.112990|8.85|17,701|
|600|2,000|skip|.026005|38.45|76,908|
|600|2,000|skip5|.032842|30.45|60,897|
|600|2,000|coin|.032468|30.80|61,598|
|600|20,000|hold|1.303882|.77|15,339|
|600|20,000|spend|1.324300|.76|15,102|
|600|20,000|skip|.261515|3.82|76,478|
|600|20,000|skip5|.306605|3.26|65,231|
|600|20,000|coin|.323018|3.10|61,916|

Measured median four-worker speedup: **3.244x**, with BLAS limited to one thread.
The existing layer2 CPU process was left running, so timing includes contention.
The exact concurrency of the other job is unknown. Rust scratch is O(m), roughly
104 bytes per pointer plus the log-L table on this64-bit build; adapter output
and key buffers add about20 bytes per pointer (about2.5 MB for m20,000, excluding
Python objects). No n*m traceback storage is needed for scoring.

The n300 hold throughput is about779 times the old39.4 single-cell scores/s,
though the workloads differ: v1 used398-value keys and independent offsets;
v2 amortizes a20,000-value stream over ALL offsets. Do not apply this speedup
to a request for only one offset. Viterbi reconstruction is still a separate
verification operation; it is not used as a search score.

## Library campaign scope and cost — NO SEARCH EXECUTED

Read-only inventory: **1,439 streams, 13,326,835 key values**. n300 windows at
stride150 within each eligible section, plus a nonduplicate section-end anchor:
**82 windows**, excluding the9-rune section0.10. Start lists are in `e2.json`.
Only section lengths were counted; no LP2 ciphertext was passed to a decoder.

Four channels hold/spend/skip5/coin x both signs:

- **943,984 full-stream backward passes**;
- **8,742,403,760 offset/channel/sign/window cells** (including impossible
  finite-key cells, whose likelihood is zero; no heuristic filtering);
- projected serial CPU work: **48.55 CPU-hours**;
- projected wall time at measured four-worker speedup: **14.96 hours**;
- projected wall time at14 threads: **4.28 hours**.

The14-thread number is a **linear extrapolation**, not a14-thread measurement.
Actual SMT scaling, serial overhead, sustained contention, real key structure
and export/checkpoint costs are unknown. Estimates interpolate measured2000/
20000-key timings; sub2000 streams use an explicitly optimistic linear scale.
These are engineering estimates, not a promise of four-hour end-to-end completion.
Null calibration, plant power, candidate verification and traceback are extra.

50% window overlap limits start-position mismatch to150 runes and supplies
section-end coverage. It is NOT evidence of power for arbitrary mid-window
cipher starts. In addition, v1 assumes absent previous ciphertext at the first
observed rune; an internal window cut through an ongoing cipher can violate that
initial-state assumption if its first rune is a repair. That mismatch is untested
and must not be turned into an exclusion after a negative scan.

Because the stated14-thread campaign projection is below8h, the conditional GPU
port plan/attempt g3b was **not** activated. If the14-thread estimate is too
optimistic in practice, that decision must be revisited with permission. The
original v1 `forward.cu` and failed `g3.json` remain byte-for-byte unchanged.

## E3–E5: why work stopped before calibration

Pre-registered E3 candidate rule, unchanged:

    for each n, T_n = max(real-bank calibration maxima) + 10 nats
    candidate requires S >= T_n (at least10 nats over that observed maximum)

**Numeric T_n: unknown.** The old -135.158 nats threshold is NOT deployable.
No tail fit or extrapolated false-positive probability is claimed. A margin of
10 nats is a design choice, not a proven1e9-cell false-positive guarantee.

The frozen v2 protocol is deliberately larger than a single30-window pilot:
30 windows **per length**, then199 per length if budget permits. E2 predicts:

| Work | Estimated serial CPU-work hours |
|---|---:|
| One n300 full-bank null search | .592 |
| One n600 full-bank null search |1.197|
|30 null windows, n300 only |**17.76**|
|30 null windows at each length |**53.66**|
|199 calibration windows at each length |**355.94**|
|200 library-scale recovery plants,100 per length |**178.86**|

The two-length pilot alone would also take about**16.54 wall hours at four
workers**, so it exceeds an8-hour limit even if that limit meant elapsed time
rather than summed CPU work. We conservatively interpret CPU-hours as compute
work; even the original30-window single-length pilot exceeds that budget.
**Zero real-bank nulls and zero new library-scale power plants were run.**

If the intended budget was8 hours of wall time at four workers, the single-length
30-window pilot might fit (~5.47 projected hours), but that is a different scope/
budget interpretation from the frozen conservative protocol and needs an explicit
follow-up decision. No partial pilot was silently substituted for a passing E3.

LM-mismatch stratum was pre-registered as held Cicada (a different source from
the Emerson-trained LM), with held Emerson as the comparison. It has NOT been
measured at library scale. Other-language power remains unknown. Likewise,
exact stream/offset/sign/channel identification, +/-3 aliases and plaintext
recovery at library scale are unknown. v1's100/100 small-bank M04 result remains
valid for its original scope only.

## Resource use, failure records, and immutability

- E0:25.37 s; E1 single-worker checkpoints:2,056.60 s; E2:57.61 s wall,
  84.45 process CPU seconds; unit suite36.15 s. Including setup/audits, recorded
  work is conservatively below0.7 CPU-work hours. Exact total process CPU time
  for E0/E1 was not instrumented; their single-worker wall time is used as an
  upper-bound proxy. Each command stayed below30 minutes.
- GPU compute **0 seconds**. Intake nvidia-smi showed the2080 Ti with3% use and
  7,317 MiB allocated to existing applications. No GPU memory was reserved here.
- No v2 gate failed; deliberate mutant failures are control witnesses, not
  omitted failures. Historical v1 compiler/adapter failures remain preserved.
- `v1_m04_snapshot.json` and `immutability.json`:1,241 original files unchanged,
  no added original-tree files. The phase17 log has dated appended v2 entries.
- Raw v2 regression arrays ~15 MiB. No installs, downloads, external API calls,
  commits, results/** writes or process changes. Existing dirty files/queue
  outputs belong to other work and were left alone.
- An initial privacy scan including binaries caught local-path strings in two
  newly generated MSVC artifacts (`backward.pdb`, `backward.dll.exp`). These
  unused debug/linker files were removed, not merely git-ignored; the DLL and
  source/results were unchanged. The redacted filename-only finding is retained
  in `privacy_initial.json`; final scan in `privacy_scan.json`. Rebuild commands
  now include removal of those nonessential artifacts. This privacy cleanup did
  not rerun or alter a scientific gate.

## Needs your approval

1. Choose the next calibration scope/budget: single-length30-window pilot under
   an explicitly elapsed-time budget; the full two-length CPU pilot (~53.66
   CPU-work h); or a different preregistered calibration design. Do not tune
   scope/threshold after looking at favorable null maxima.
2. Alternatively authorize a **GPU calibration acceleration attempt despite the
   below8h campaign projection**. It must be labelled g3b with its own frozen
   protocol, Float64 parity and resource guards, and preserve v1's failed gate.
   No GPU implementation or repair was attempted under this conditional branch.
3. Additional compute for199-per-length calibration and200 plants cannot be
   promised from the current budget. Break any authorized follow-up into<30-min
   checkpointed commands. No installation/download is currently requested.

## Proposed registry rows — NOT written

- `chanscreen-v2-exact`: finite-key hold/spend/skip/skip5/coin, all offsets,
  sparse previous-plaintext states and exact backward sum; E0 controls340,800
  rational comparisons +405 tails +7 mutants; E1 controls693,940 stored cells
  at max score error1.274e-11. Result PASS; no LP2 key family excluded.
- `chanscreen-v2-throughput`: measured n300/600, m2000/20000, five channels,
  both signs, <=4 workers; n300/m20000 hold30,690 offsets/s one thread;
  3.244x measured four-worker speedup.82-window library projection4.28h at14
  threads, unmeasured extrapolation. No null/power claim at that bank size.
- `chanscreen-v2-library-controls`: E3/E4 INCOMPLETE (budget preflight), zero
  null windows/plants; numeric threshold, best/null, power and LM-mismatch
  effects unknown. Candidate rule symbolic max+10 only. No campaign launched.

Files: this folder; log `work/log/phase17_chanscreen.md`. `RUNNING.md` provides
rebuild, fast suite, immutable-input verification and read-only summary commands.
