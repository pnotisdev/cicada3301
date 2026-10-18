# Human-run independent tools — NOT RUN / NOT VALIDATED

**Nothing in LP2 is solved.** These files were written and statically reviewed only.
No new script, selftest, benchmark, experiment, build, or search was executed by
the assistant. There are deliberately no fabricated result logs.

Everything here is separate from `work/tmp/relabel_all.py`, `work/kscreen/`, the
shared README/ledger and existing runner state. Do not stop the active job to use
this package. The tools use one foreground CPU process, no GPU, API or network.
Even so, wait for CPU-heavy work to finish before starting a likelihood search.

## Read this first

* **PGP clue:** `7A35090F` is `z5`, TAB, control byte `0F`, not `z5z5`. A Z5 book
  remains a weak, unverified source lead, not a recovered key. No book was fetched.
* **New mathematical finding:** affine outer alphabets, including Atbash, are
  redundant after the completed all-key-multiplier screen. Non-affine keyword
  alphabets in the active job are NOT redundant by that argument.
* **New experiment:** a tightly specified lag-6-value-gated keyless-null decoder.
  It sums alignment probabilities rather than maximizing IoC over freely chosen
  deletions. Whether it actually has power is unknown until the human runs its gate.
* Full equations, controls, prior-result comparisons, limitations and decision
  rules are in [MATH.md](MATH.md). The independent review is also recorded in
  [`../log/independent_human_run_review.md`](../log/independent_human_run_review.md).

## Cheapest useful order

Run from the **repository root in PowerShell**, with the same Python environment
already used for this project. Standard library only; no install/build is needed.
If this PC requires the venv, substitute `.venv\Scripts\python.exe` for `python`.

```powershell
$env:PYTHONIOENCODING='utf-8'
python work/independent/audit.py
```

This checks the byte interpretation and the affine identity on synthetic data.
It does not search LP2. **Send back its `run.log` first** if you want the least
expensive review loop. There is no need to start all commands at once.

### 1. Validate the proposed null decoder before searching anything

```powershell
python work/independent/echo_nulls.py gate
```

This runs only this directory's unit tests and synthetic controls. LP2's **layout**
is used for power controls, but no LP2 ciphertext is searched for a key. The two
uniform-plaintext controls repeat the same finite search as the planted controls.
Two diagnostic plants are explicitly conditioned to contain a null; six ordinary
plants are not. All failures and that distinction are logged.

* A skipped test fails the gate. Plant/null failure also fails it.
* It prints its fresh output folder and writes `gate.json` there.
* Only an ending `GATE PASSED` with `FINISHED` permits the screen.
* An interrupted/timed-out run is **INCOMPLETE**, not evidence against a cipher.
* Runtime is **unbenchmarked**. Default hard wall budget: 900 seconds. Only a
  human can choose a larger budget, e.g. `gate --seconds 1800`.

Please send back `run.log` and `gate.json` before spending time on a search.
A failed gate is useful: it prevents wasting a large sweep on an unpowered model.

### 2. Small, explicit LP2 search — only after the gate passes

Paste the **actual repository-relative** `gate.json` path printed by the gate:

```powershell
$gate = 'results/independent/desktop/PASTE-THE-GATE-FOLDER/gate.json'
python work/independent/echo_nulls.py screen --gate $gate
```

Default scope: section 0.7, 300 runes, totient-prime stream, offsets 0..15, two key
signs, identity/Atbash plaintext orientation, null rate 0 or 0.0272. That is **128
settings**, repeated on the real ciphertext and **19 shuffled-key null searches**:
2,560 likelihood decodes, not billions. No new seed/word-list expansion.

* Budget: one CPU process, 1,800 seconds, maximum 256 settings per search.
* Gate hashes must still match code, toolkit, corpus and transcription.
* Every run creates new files. Nothing resumes or overwrites another experiment.
* `screen.json` exists only after ALL null searches finish. `definition.json` or
  `scores.json` alone means incomplete controls. **Do not call that a negative.**
* The score is a new, unclipped log-likelihood ratio in **nats**, not the old
  10-log-odds score or an IoC score. Thresholds are not interchangeable.
* The minimum descriptive Monte Carlo rank with 19 nulls is 0.05. A flag is not
  a statistically authenticated discovery, particularly for an LP2-selected model.
* Temporal key structure is not preserved by shuffling; full verification uses
  unsearched offsets of the SAME key stream as an additional control.

An explicitly bounded alternative, not recommended until the first logs are reviewed:

```powershell
python work/independent/echo_nulls.py screen --gate $gate --streams primes,totient --offsets 0:8
```

Or select **1–4 explicit item indices** from an ALREADY generated library. This
reads it only; it does not import/export/build the actively edited engine:

```powershell
python work/independent/echo_nulls.py screen --gate $gate --library work/kscreen/data/library.ksb --items 0,1 --offsets 0:8
```

These commands are examples, NOT a queue to run automatically. If the library is
missing, do not rebuild it beside the active job; use the built-in streams or wait.

### 3. Whole-section verification — separate human decision

Only a completed search provides a usable `screen.json`:

```powershell
$screen = 'results/independent/desktop/PASTE-THE-SCREEN-FOLDER/screen.json'
python work/independent/echo_nulls.py verify --screen $screen
```

It re-decodes rank 1 over the **entire section**, tests the previously unseen tail,
and runs 20 random unsearched offsets of the same stream. Use `--rank 2` only for
an explicitly chosen alternative; do not keep trying ranks until something looks
English. The full decoded path is saved even if it fails, labelled unverified.

A numerical survivor must meet both language-score checks and the project's full
IoC / matched-control margins. It still needs independent reproduction and another
section. This command cannot declare a solve. Default wall budget: 1,800 seconds;
state-budget exhaustion stops rather than silently approximating a negative.

### Optional: cheap Z5 source preflight, not a book-code search

Only if you already have a lawful plain UTF-8 transcription, place it in
`work/independent/sources/`. That subfolder is locally git-ignored. Do not copy a
PDF, fetch copyrighted books for this test, or commit any third-party source.

```powershell
python work/independent/source_gate.py --text work/independent/sources/z5-volume1.txt
python work/independent/source_gate.py --text work/independent/sources/z5-volume2.txt
```

Each invocation has its own log. It records the input hash, sizes and marginal
statistics, not book contents. It tests only the independent-marginals prediction
for a plain additive book-text running key, with two spelling conventions and
both signs. A prediction inconsistent with flatness is **triage, not a formal
skip-aware exclusion**. Book codes, hashes, tables, source authenticity and
bibliographic identification are not tested.

## Logs to return

Every command prints its output directory, then writes:

```
results/independent/<laptop|desktop|manual>/<UTC-time>-<command>-<unique-id>/
    run.log                 live, timestamped, privacy-scrubbed, UTF-8
    ...                     command-specific JSON / decoded output
```

Send `run.log` plus:

| Command | Additional useful file |
|---|---|
| `audit.py` | `audit.json` |
| `echo_nulls.py gate` | `gate.json` (or the last `plant_*.json` if interrupted) |
| `echo_nulls.py screen` | `screen.json`; absent = incomplete |
| `echo_nulls.py verify` | `verify.json`, `decoded.txt` |
| `source_gate.py` | `source_preflight.json` |

No real computer name, home/repository absolute path, credentials or API calls
are needed. If `.lp_machine` is absent or is not `laptop`/`desktop`, outputs use
`manual`; these scripts never change the alias file.

After results have been reviewed, their scope/control/failures should be added to
`PLAN.md`, `docs/registry.toml`, and the generated overviews through the normal
project workflow. They have **not** been inserted into the shared ledger as if
already run. Do not regenerate shared documents while another agent is editing
them without coordination.
