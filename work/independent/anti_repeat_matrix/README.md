# Anti-repeat misspecification matrix — human-run only

**UNEXECUTED / UNVALIDATED. Nothing in LP2 is solved.** No analysis scripts,
syntax checks, builds, tests, simulations, benchmarks or cryptanalytic searches
were run by the author. Only this new folder was written; no shared engine,
ledger, old independent package, data or running process was changed.

## Deliverables

* **[CATALOGUE.md](CATALOGUE.md):** twelve concrete physical mechanisms, joint
  conditional kernels and exact plaintext/key-pointer updates. Doublet matching
  is calibrated from the reported count, not the same q reused for every rule.
  Retained-key calibration is explicitly conditional on a plaintext law.
* **[MATRIX.md](MATRIX.md):** the complete twelve-by-ten formula lookup for bare
  skip/coin, both initial/final edge-null modes and both separator-advance modes,
  each flag composed with skip OR coin. Includes derived numbers, signal-loss
  formulas, existing crossed controls, and a ranked build list.
* **[reference.py](reference.py):** rational kernels and phase-support formulas,
  reusing `../collision_substitution/collision_model.py` without modifying it.
* **[gate.py](gate.py):** bounded, deterministic, human-run kernel/arc checks and
  a numerical reference-matrix generator. Standard library only. No installations,
  engine builds, data exports, seed/library searches, network, API, GPU or jobs.

### The important limit

An actual beam's expected aligned run length or detection power is **unknown**
without a plaintext/key law and crossed plants/nulls through that exact beam.
Pointer support is not beam survival, and wrong phase is not invariably lost IoC.
The package does NOT present assumed uniform-noise signal loss as a measured
power matrix. Its complete numerical matrix is instead a precisely labelled
**reset-oracle strict phase-prefix diagnostic** on fixed, exogenous layout masks.
Earlier errors are reset before the hypothetical event; later resynchronization
and pruning are omitted. Native-domain and local corruption warnings are included.

Key corrections, with evidence and derivations in the linked documents:

* Skip/coin are branching graphs, not decoders with a hard-coded repair q.
* A reported +7.3 bigram score/rune is about +0.73 nominal nats, not +7.3 nats;
  the table is also rounded/clipped (`work/phpmt/bg.py:52-64`).
* A retained-key repair has a genuinely missing zero-key/one-plaintext transition.
* A spend-key substitution need not lose pointer alignment at all.
* Repair-only +2 is PARTIALLY visible to coin, not always destroyed at its first
  avoided collision. Its reset-oracle unbounded mean is about 176 subsequent
  outputs under the declared reference (derived from catalogue constants).
* Feedback, step-domain and deterministic layout decoders already exist. Their
  coverage is not automatically transferable to every key family/seed sweep.

## Optional human command — do not run automatically

From the repository root, if the human chooses to authorize this bounded gate:

```powershell
$env:PYTHONIOENCODING='utf-8'
python work/independent/anti_repeat_matrix/gate.py
```

The **110-second default budget is a design cap, NOT a measured runtime**.
Completion within two minutes is targeted but has not been demonstrated. The cap
is checked between bounded work blocks; it is not an OS hard-kill timer. There
is no background continuation, timeout expansion or automatic retry. `--seconds`
may only LOWER the budget or increase it up to 115 seconds, never start a long run.
A timeout/failure is **INCOMPLETE**, not an LP2 negative.

For the still-cheaper arithmetic-only gate, omit the real-layout numerical output:

```powershell
python work/independent/anti_repeat_matrix/gate.py --kernels-only
```

Choose ONE command; the script never starts the older collision or null-alignment
gates. Reading and hashing the shared kernel/helper/source files is read-only;
bytecode writes are disabled before local imports. All run artifacts go in a NEW
`results/independent/<laptop|desktop|manual>/<UTC>-anti-repeat-matrix-<unique>/`.
The existing runner, DeepSeek files and cached engine/export data are not touched.

### What the gate checks

* Exact mass normalization, nonnegative kernels and calibrated means for every
  mechanism and previous rune; null stationary denominator and pending retry.
* Literal exhaustive three-key-prefix forward plants for once, coin and repair-
  only +2; both decoder graphs and relevant extra advances. No random sampling.
* Exhaustive sufficient equality partitions with their exact alphabet
  multiplicities for longer prefixes; the infinite until-loop tail is summed
  geometrically. It is NOT accepted by truncating the true channel.
* Hold-key comparison-state matrices and output-only-null pending-state matrices.
* Native step bijections and feedback collision/reference transformation.
* Positive true-key arc controls, a deliberately wrong-pointer sentinel, a
  deliberately miscalibrated-q sentinel, a retained-key/plaintext counterexample,
  an independent wrong-key null, and exact local-noise IoC attenuation.

These are **local arithmetic/graph controls**, not an English-language search
power calibration. The wrong-key check is unselected and must not be substituted
for a full-search, same-selection null in a cryptanalytic claim.

### Fixed-layout numerical output

The default additionally reads the canonical transcription, without changing it,
and computes all formula cells on first-300-rune section-head windows with enough
runes. Shorter sections and paragraph/page restart windows are not included.
The first output has no previous comparison in this reference. It does not
pretend to emulate the actual export's cross-section initial-prev convention.

Masks use ciphertext words, not guessed English words. Break multiplicities are
preserved, including coincident line/page tokens, as in
`work/kscreen/export.py:39-50` and `work/kscreen/src/main.rs:237-268`. The event-time
average assumes exogenous masks. A generative word-length/insertion model would
need a different conditional law, currently unknown.

The generator reports, for every concrete decoder configuration, the conditional
post-event phase-prefix expectation by possible first-event position and a
geometric event-time-weighted reset average. Its `actual_beam_power` and
`actual_beam_run_length` fields remain **"unknown"**. M10 correctly gives N/A
rather than inventing a mod-29 avoided-collision event in a 28-class native model.

### What to return

Read **run.log first**. Only accept a current-snapshot run containing BOTH:

```text
KERNEL IDENTITY GATE PASSED
FINISHED
```

Then return:

* `run.log`
* `gate.json`
* `kernel_checks.json`
* `theoretical_numbers.json`
* `matrix_summary.json` (default command only)

The detailed `reset_matrix_seg*.json` files can remain local unless a coefficient
or layout question needs them. An existing file, a partial summary or a gate
pass without `FINISHED` is insufficient. Mid-run input/source changes invalidate
the run. No resampling until a control passes.

## Before making any new LP2 exclusion

The ranked gaps are in `MATRIX.md` §6. First specify a bounded crossed English-GP
plant design, including the actual retained-key/plaintext law, matched random-key
searches, pruning/abort, offsets and identical branch/selection freedom. That
follow-up requires separate human authorization; it is NOT implemented or started
here. Existing measurements are cited, not rerun or universally extrapolated.

Do not update the shared empirical ledgers from unexecuted code or these
reference calculations. No full-section plaintext or decryption is claimed.
