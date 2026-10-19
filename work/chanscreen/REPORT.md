# chanscreen report — stopped at G3 failure

**Nothing in LP2 is solved. No LP2 search or campaign was run.**

A matching summed-path decoder now passes the requested small-bank M04 power
gate. The GPU port is **unvalidated**: its first NVRTC compilation failed because
`math.h` was unavailable. Per the stop rule, no workaround or retry was attempted.
The cascade and campaign package are not built. This is a reproducible partial
delivery, not the requested finished high-throughput engine.

## Gates

| Gate | Status | Measured result |
|---|---|---|
| G0 specification / exhaustive checks | **PASS** | 340,800 exact rational probability comparisons; 34,080 normalized event trees; 45 additional long-tail checks. All four broken-transition mutations detected. 13.51 s. |
| G1 NumPy reference | **PASS** | 230,040 tiny-alphabet comparisons, 50 Q=29 edge cells; max probability error 5.55e-17. Repeated calls bit-identical in this environment. |
| G1 CPU acceleration | **PASS** | 1,000 Rust/reference parity cells; max log error 3.55e-15 nats. Additional genuinely branching 300/600-rune tests in suite. |
| G2 frozen M04 power | **PASS** | M04 100/100, every stratum 25/25; null 4/100; all detected M04 winners >=.95 plaintext accuracy; regression channels recovered. |
| G3 GPU | **FAIL** | NVRTC generated-source line 2: cannot open `math.h`. 0 parity cells completed; 0 device kernel seconds. No throughput/occupancy measurement. |
| G4 cascade | **INCOMPLETE** | Blocked by G3 failure; no calibrated prefilter, no measured cascade loss, no real-bank-size null. |
| G5 campaign package | **INCOMPLETE** | Blocked; no runnable production queue or approved candidate threshold. **DO NOT LAUNCH.** |

Frozen protocols: `README.md`, `GPU_README.md`. Raw gates: `g0.json`, `g1.json`,
`g1_cpu.json`, `g2.json`, `g3.json`. Tests: **7/7 passed in 68.49 seconds**, zero
skips (`tests_corrected.txt`). The suite does not import/run the GPU or rerun G2.

## What is implemented

- Channels as data (`channels.json`): hold, spend, uncapped skip, harness skip5,
  coin; unknown extension kernel rejected rather than silently approximated.
  This is a catalogue of predefined kernels, not an arbitrary matrix compiler:
  Rust/CUDA specialize the frozen names/modes. Adding or changing a kernel
  requires corresponding implementation and fresh correctness gates, not just
  a JSON edit.
- Independent rational event tree and full-state rational DP; NumPy scaled
  float64 reference; dependency-free Rust CPU cdylib; full-state Viterbi
  traceback used only for plaintext-accuracy diagnostics.
- State includes absolute pointer and previous plaintext. Absolute pointer is
  equivalent to signed lag; hold naturally produces negative lag.
- Full finite key range: **no lag pruning or tail cutoff**. Skip-until-end residual
  goes to exhaustion, not a survivor-renormalized probability. G0 explicitly
  sums complete outputs plus terminated-prefix failure atoms to one.
- The finite observed-output likelihood excludes failure paths because they did
  not emit that output, not because their probability was redistributed. Both
  L and U use the identical channel and finite-key convention.
- q=0/1, both signs, first rune, empty window/key, and stream ends covered.
- Algebraic normalization is exact. Float64 arithmetic is approximate, with
  tested error bounds at these gates, not an arbitrary-precision guarantee.
  `discarded_tail_mass=0` means no **algorithmic** truncation; it does not claim
  zero floating-point roundoff/underflow on every possible input.

## G2: power, reconstruction, and offset aliases

Same read-only M04 plants, banks, seeds, q fits and plaintext pools. L uses only
training Emerson (first 40%), normalized bigram/unigram counts with +0.5 smoothing.
No rounded/clipped old bigram table and no held-out text in L. See `frozen.json`
for hashes of inputs, code and model. The original IoC threshold was NOT reused
as a nats threshold: its calibration procedure and seeds were reused instead.

Each positive and null searches **8 streams x16 offsets x2 signs x4 channels =
1,024 cells**. This is twice the baseline's model count; selection freedom is
paid for in the new calibration. No beam, early abort, prefilter or offset oracle.
The detector is the maximum of the normalized **summed-path** scores; Viterbi is
only a reconstruction diagnostic after selection.

Calibration: 200 matched wrong-key searches, 10th-largest maximum:
**T = -135.15812268992306 nats**. Calibration maximum -123.567331, median -149.381151.
A negative T is legitimate here: wrong-key decodes usually favor U strongly;
T is an empirical selected-bank threshold, not a universal Bayes-factor cutoff.

| Held-out group | Detected | Per stratum (Cicada/iid, Cicada/library, Emerson/iid, Emerson/library) | Detected with winner accuracy >=.95 | Mean winner accuracy | Exact stream/sign/offset | Within +/-3 offset class |
|---|---:|---|---:|---:|---:|---:|
| M04 hold | **100/100** | 25,25,25,25 | **100/100** | **.988633** | 98/100 | 100/100 |
| Spend substitution | 100/100 | 25,25,25,25 | 100/100 | .981600 | 100/100 | 100/100 |
| Skip5 regression | 40/40 | 10,10,10,10 | 40/40 | .999250 | 40/40 | 40/40 |
| Coin regression | 40/40 | 10,10,10,10 | 40/40 | .999250 | 39/40 | 40/40 |
| Matched wrong-key nulls | **4/100** | 2,0,2,0 | — | — | — | — |

M04 mean true-cell accuracy .988800. M04 winner scores 153.031366..244.845968;
held-out null maxima -162.232152..-132.153705. All 100 null winning channels were
hold: extra path freedom does elevate its wrong-key score relative to the other
channels, but the selection-matched small-bank null still meets the frozen size
criterion. This does NOT establish size at the full library's maximum.

Offset aliases: held record 1 starts at 10 but wins at 9; record 81 starts at 13
but wins at 11. Coin record 278 starts at 14 but wins at 12. Detection is not
exact-offset identification. The recorded +/-3 class is an operational metric,
not a proof that all those offsets have identical output distributions.

All 380 held-out cases evaluated once. Execution order: hold 0..99, nulls
280..379, then spend/regression 100..279. Nulls were run early so a failed size
gate could stop further work; no model/threshold change followed any inspection.
171 distinct Cicada and 190 distinct Emerson window starts, matching the baseline.
Overlapping plaintext windows are not 100 independent passages. Plants use the
baseline's positive encryption sign; the search tests both signs, and numerical
parity/round-trip controls cover negative signs. Held-out power stratified by
negative encryption sign remains unknown.

## Failures and corrections (preserved)

1. Training-only integration initially failed: M04 supplies byte-array keys,
   whereas NumPy tried to parse `bytes` as a scalar integer. No score or held-out
   result existed. Corrected the ctypes adapter to convert bytes/bytearray to
   an integer sequence; added a regression test. Repeated the SAME training
   seeds, not replacement seeds. Original adapter, manifest, all eight started
   markers and explanation: `history/training_integration_failure/`. No Rust,
   channel, threshold or statistical criterion was tuned. The original G1 CPU
   hash predates that adapter-only correction; corrected suite and `frozen.json`
   cover the code actually used for G2.
2. **G3 compiler failure, final stopping point.** CuPy imported and NVRTC was
   invoked, but the header include failed before a device launch. `gpu_parity.npz`
   retains all 100,020 generated inputs and NaN placeholders for uncomputed CPU/GPU
   arrays; it is NOT a parity result. `g3.json` retains the compiler diagnostic
   with its temporary directory removed for privacy. No fallback or retry.

## Throughput, resources and library cost

- CPU-only standalone benchmark: hold 39.4, spend 48.9, skip5 48.8, coin 48.3
  **normalized scores/s** (each score includes L and U), one calling thread.
- Actual calibration: 204,800 scores /1,260.45 s = **162.48 scores/s on four
  workers**, including Python validation and raw-record output.
- Held-out: 389,120 scores in 2,892.92 s, **134.51 scores/s**, including winning
  and true-cell Viterbi traceback for positives.
- Training + calibration + held-out batch time: 4,212.37 s, about **70.21 min**,
  split into individual runs of about 5–8 min, never a >30-min single run.
  Suite/build/reporting time is additional. The existing CPU queue was untouched.
- Raw scores: **602,112**, including training. `audit.json` independently verifies
  record counts, cell uniqueness, selected maxima, model/input hashes and the
  frozen calibration records. Raw text/data footprint about 178 MB plus ~4 MB
  compressed G3 inputs; build products are locally ignored.
- GPU kernel time **0**; GPU throughput, measured occupancy and 8-hour scope:
  **unknown**. Source proposes 128-thread blocks, per-cell full global A/B
  buffers. At batch128,m620,Q29 the two buffers alone would occupy
  36,882,432 bytes; this is a layout calculation, not measured performance.

**Optimistic CPU projection, not a campaign estimate:** at the measured small-bank
rate, 2e8 cells cost **341.9 h on four workers**, or **1,367.7 h** if four channels
make 8e8 normalized scores. Real 20,000-value keys, n=600, null calibration and
verification can cost more; no linear scaling claim from 398-value slices.
For 8 hours the required rate is 6,944 cells/s per 2e8-cell scope, or 27,778/s for
four such channels. No measured GPU rate or cascade retention supports that yet.
A justified smaller *campaign* scope is therefore also unknown. The only powered
measured scope is the 1,024-cell synthetic harness.

## What remains / handoff

1. Review `forward.cu` line 2 and the local NVRTC include environment. A plausible
   minimal repair is to remove the unnecessary C header and use NVRTC's CUDA
   math built-ins, while replacing the `INFINITY` macro with an explicit supported
   double-infinity expression. **Untested hypothesis**, not an asserted fix.
   Do not install packages or change machine configuration without permission.
2. Preserve the failed G3 artifact and original source hashes. A separately
   authorized follow-up must label the revised implementation/protocol; never
   erase failure markers to make this attempt appear to pass. Reuse the frozen
   parity inputs, not a fresh seed selected to pass. No need to rerun G2 merely
   to test a GPU math-header change.
3. Pass >=100,000 decode-by-decode GPU comparisons, long-window stability,
   planted controls, launch-time safety, resource/occupancy analysis and throughput.
   Float32 is deliberately unsupported until separately gated.
4. Design and calibrate a cascade. The README's possible likelihood upper/lower
   bounds are a design sketch ONLY; no useful bound or >=98% retention is proved.
   Fixed lag bands must carry valid omitted-mass bounds or fall back to full DP.
   Full-bank matched maxima are required; the threshold here is not deployable.
5. Only then produce a resumable `jobs/jobqueue.py` offset-block package and
   frozen candidate summary. Whole-window and whole-section checks with controls
   remain mandatory. No candidate or decryption was claimed here.

### Needs your approval

- **Continuation after the failed G3 gate**, even for the proposed small compiler
  repair. This session stopped rather than tuning away a failure.
- Any future single run >30 minutes or cumulative GPU use >4 hours. No such run
  was used here, and no long-run duration request can be justified before GPU
  throughput is known.
- Nothing is awaiting an installation/download. No external API calls were made
  by project scripts. This session's harness/API dollar cost is **unknown** to
  the code; the user's credit balance was not queried.

## Proposed registry entries — NOT written to shared registry

- `chanscreen-reference`: scope finite-stream additive hold/spend/skip/coin,
  exact summed L/U model; control exhaustive Q=3 tree/DP, mutations, Q29 numerical
  parity; result G0/G1 PASS; not excluded any LP2 key/channel; files this folder,
  logs `work/log/phase17_chanscreen.md`.
- `chanscreen-m04-power`: scope n300, bank8 x16 offsets x2 signs x4 channels;
  control 100 M04 +100 spend +80 regression +100 null, original held-out seeds;
  best M04 max244.845968 nats, threshold -135.158123, null max -132.153705;
  result G2 PASS (100/100 M04, null4/100, accuracy .988633); NOT excluded other
  languages/alphabets, replacements, larger banks, n600, unknown initial history,
  arbitrary key models; no LP2 search.
- `chanscreen-gpu`: scope unvalidated full-state float64 CUDA port; control
  planned 100,020 cells; result G3 FAIL at compiler include, 0 cells evaluated;
  best/throughput unknown; G4/G5 blocked. No cryptanalytic negative follows.

## Navigation / reproduction

`RUNNING.md` has safe rebuild, suite and read-only audit commands. `raw/` keeps
all plants, null banks, outputs, plaintexts, pointers, aliases and per-cell scores.
No shared documents, existing engines, data files, other agents' folders, running
processes or queue outputs were edited. No commits, network access or downloads.
The branch matched locally recorded origin/main at intake; no remote freshness
claim is made without a fetch.
