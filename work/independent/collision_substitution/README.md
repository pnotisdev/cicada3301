# Collision substitution H — derivation and human-run gate

**Status: UNEXECUTED / UNVALIDATED. Nothing in LP2 is solved.** No Python,
syntax check, test, simulation or search was run to prepare this directory.
No shared docs/engines, existing independent tools, DeepSeek files or processes
were changed. These are substitutions (plaintext advances), not the output-only
null insertions in the older `../echo_nulls.py` experiment.

Read **`DERIVATION.md`** for the cited evidence and exact assumptions. In brief:

* The primary family is copy or T-image at lags 1–8, with either spending or
  retaining the colliding key. This defines the rules; it does not supply a
  plaintext/key probability law by itself.
* Under an unread iid uniform pad, **raw spend-key** means have an exact small
  two-point recurrence. The tables cover every within-word lag and earlier
  position in the real layout, with each source rune's mean. The non-8 source
  runes share the SAME mean by symmetry, so they are compressed into a class:
  the reported value is for EACH rune separately, not the class total.
* Holding the colliding key needs plaintext differences. Those numerical means
  are **unknown**, not copied from the spend case. Guarded rules have exact
  conditional kernels but their unconditional means are also marked unknown.
* Copy-only fresh-candidate rules cannot create the nonidentity T mean. No
  source-blind I/T rule derives an S preference under the reference law. Which
  templates survive the full simultaneous profile is **unknown**, not 'solved'.
* The shared-position lag-5/6 budget and an overlap motif give a new falsifier.
  It gives a repair rule arbitrary history-dependent output freedom and pays
  for the logged affine/lag pair selection. A non-rejection is not support for H.
* Collision-triggered repair is **exactly observationally equivalent** to a
  specified independent-overlay generator. No keyless method can identify the
  unobserved collision cause in that reference model. The optional test below
  tests a kernel against a no-echo null, not that causal label.
* The prior section-correlation calculation has denominator/count/normalization
  defects. Also the large F-rate calculation used Latin-letter positions, not
  GP-rune positions. Neither old result should be strengthened without repair.
  The W3(a) causal-site intersection remains informative, but applies to
  substituting T(previous output), not to T(six outputs back).

## Human step 1 — cheap exact tables, NOT an LP2 solve/search

From repository root, if you choose to run it:

```powershell
$env:PYTHONIOENCODING='utf-8'
python work/independent/collision_substitution/gate.py tables
```

This first runs its local unit identities (including an independent tiny forward
probability enumerator). Then it reads the committed transcription/layout. A legal
collision null and a deliberately strong out-of-family overlay must pass before
it writes the LP2 budget e-value. These are wiring controls, not an estimate of
LP2-sized power. The output also includes exact rational means, observed I/T
profiles, corrected section-correlation diagnostics and the W3 direct-site
intersection. Observed word cuts gate taps; they are not assumed to be English
plaintext boundaries.

It uses the standard library and NumPy for the later kernel statistic's unit
check. **No auto-install, network, API, GPU, build or engine launch.** If NumPy is
absent the gate stops; do not install anything on our behalf without deciding to.
The foreground wall budget is a design cap, not a runtime estimate. Runtime is
**unknown** until the human run. On timeout return the log; do not expand the
budget or start an overnight run automatically.

Fresh output folder, never an existing campaign's files:

```text
results/independent/<laptop|desktop|manual>/<UTC>-collision-tables-<unique>/
```

Please return **`run.log` first**, then these small artifacts if it finishes:

* `table_manifest.json`
* `exact_aggregate_means.json`
* `budget_evalue.json` and `budget_controls.json`
* `correlation_audit.json`
* `intersections.json`

Also retained locally: `exact_position_means.json` and `observed_profiles.json`.
Their detailed per-position/per-source arrays need not be pasted into an API
conversation unless requested. Fractions are exact numerator/denominator strings;
log summaries are rounded. Markov-baseline, iid-baseline and exact empirical
permutation expectations are different and labelled separately.

**`FINISHED` is required.** Partial artifacts or a failed unit gate are not new
LP2 negatives. Tables give means, not a joint-fit confidence region. No template
is automatically accepted because it matches a single count.

## Optional human step 2 — controls only, after reviewing step 1

Do not start this automatically:

```powershell
python work/independent/collision_substitution/gate.py controls
```

Predeclared specification and decision rule: `DERIVATION.md` §5. Four forward
collision plants and one no-echo null control, each tested against independent
conditional-null replicates. The null preserves each section's doublet count
exactly. EVERY replicate repeats the full affine/lag/raw-versus-guarded scan,
including the same three fixed mixture choices. This is not an unconstrained
shuffle which erases the very anti-repeat rule being tested.

Return `run.log` and `controls.json`; individual `plant_*.json` and
`null_control.json` are retained too. Require **`CONTROLS PASSED` and `FINISHED`**.
A failure or timeout is an underpowered/incomplete calibration, NOT an LP2
negative. Do not change seeds until a pass appears. The power estimate is coarse
and explicitly labelled unknown beyond the small control sample.

## Optional human step 3 — separately authorize the LP2 kernel test

Only with a current passing `controls.json`:

```powershell
python work/independent/collision_substitution/gate.py test --controls <repository-relative-controls.json>
```

Return `run.log` and completed `test.json`. A flag is only deviation from the
specified conditional Markov null; a non-flag is not a powered exclusion of all
H variants. It does not prove a both-echo fit, rule out structured keys, choose
spend versus hold, identify collision causality, recover a key or read plaintext.
A full per-rule joint predictive check would need a further human decision.

All invocations use a short foreground budget and fresh logs. Hashes tie controls
to this directory's Python files, the existing logging helper, parser and verified
transcription. Changed inputs/code invalidate controls; changes during a run
abort. `python -O` is rejected. No shared registry/result overview is regenerated
because there are currently **no new measured results**.
