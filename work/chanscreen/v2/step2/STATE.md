# Step2 checkpoint / handoff — 2026-10-19

**Nothing in LP2 is solved. No LP2 search or campaign has been launched.**

Latest user instruction: save partial results at every checkpoint; start no new
runs longer than10 minutes. This supersedes the earlier30-minute command limit.
Overall limit remains8 HOURS ELAPSED, <=4 CPU threads, NO GPU. All new work stays
in `work/chanscreen/v2/step2/`; pre-existing v1/v2/M04 files remain immutable.
No commands or workers started by this session are currently running.

## 1. Finished and verified

### Intake, immutability, resources

- Checked git status/log, existing processes and all three queue TSVs read-only.
  Existing unrelated dirty files/processes were left alone. No network or git
  mutation, installs, builds, external API calls or GPU work.
- `snapshot.py`, `baseline_sha256.json`, `immutability.json`: ALL **1,926**
  pre-existing chanscreen/v2/M04 files unchanged; no additions outside step2
  within those trees. Verification repeated at delivery.
- `resources.json`: checkpoint elapsed time since first snapshot **19.49 minutes**;
  includes analysis/documentation, not just compute. One CPU worker used, BLAS1.
  Proof audit5.33s; unit suite9.076s; GPU0. Monetary session cost unknown.
- `privacy_scan.json`: PASS,21 files scanned before writing that scan and the
  final manifest. Frozen gate source/protocol hashes matched.
- `artifacts_sha256.json`: SHA-256 manifest of the delivery files existing before
  this STATE.md was requested. This newly added STATE.md is NOT in that earlier
  manifest; do not confuse the earlier manifest with a seal covering this file.

### Threshold/inventory freeze (not a certified deployment rule)

Files: `README.md`, `freeze.py`, `freeze.log`, `thresholds.json`.

- n300:82 windows, N=8,742,403,760 cells,
  T=29.799206297530528 nats.
- n600:66 windows, N=7,036,568,880 cells,
  T=29.5821417922927 nats.
- alpha=.001 PER LENGTH. Four channels, two signs, all offsets including finite
  short suffixes. n300 uses the old inventory; n600 explicitly extends the same
  stride150/end-anchor policy using stored section lengths only. E5 still means
  the82 n300 windows. No LP2 ciphertext scored.
- Threshold JSON is the untouched pre-gate freeze. Its historical pending label
  does NOT override the subsequently recorded E3' FAIL.

### E3' exact proof audit: completed, FAIL for common-null claim

Files: `PROOF.md`, `bounds.py`, `gate.py`, `E3_proof.started`, `E3_proof.json`.
Frozen code/protocol hashes are stored in the result. Preserve the failed attempt.

**PASS:** the exact LR tail bound under EACH CELL'S OWN finite-key uniform-
plaintext null U_cell holds for ALL channels, including skip5 and coin:

    P_(U_cell)(S>=t) <= exp(-t) * sum_c Z_L(c) <= exp(-t).

Checked340,800 enumerated output/model cells,34,080 normalized language event
trees,46,602 exact rational tail inequalities,20,928 common-law equalities for
sufficiently long hold/spend keys. JSON's `output_comparisons` means enumerated
output/model cells, not340,800 independent DP parity tests.

**FAIL:** substituting ONE common anti-repeat ciphertext law W for U_cell at
all campaign offsets. Hold's U is independent of key VALUES but still depends
on finite remaining length and exhaustion. The inventory includes short suffixes.

Fixed, preregistered witnesses (exact fractions retained):
- Q3/key00/n3/q3/5, constant-zero plaintext LM, t=ln20:
  matched-U tail13/450<=1/20; common-W tail169/1350>1/20.
- Q29/key(3,0)/n300/q.81, uniform pi and normalized toy LM uniform over26
  increments3..28: a family of outputs has S=32.6505882975>T300 and common-W
  mass2.3692317941e-13, **2.071278x** its allotted1.1438501669e-13 bound.
- Q3/n300 long witness also refutes at T300. The fixed Q3/n600 event does NOT
  refute at T600; that negative result is preserved explicitly.

Small witness probabilities were checked with event tree AND rational DP; long
family probabilities were derived by exact counting, with representative paths
checked by rational DP. No exponential full enumeration at n300 is claimed.
These toy normalized LMs refute the normalization-only proof, NOT a measured
false-positive guarantee for the actual English LM. Actual library FWER unknown.
No v2 DP bug or cryptanalytic exclusion was demonstrated.

Skip5/coin tiny-key gap diagnostics are finished: Q3/n2/q3/5 keys0000000 versus
0011111 have TV distance1/5; max W/U13/10 for each declared key. This is NOT a
library-wide gap bound. Full-bank gap remains unknown.

### Tests, documentation and human review

- `test_step2.py`, `tests.txt`: **6/6 PASS in9.076 seconds**. Tests intentionally
  assert that the counterexamples persist; passing tests do NOT turn E3' PASS.
- `REVIEW.md`: requested backward.rs invariants, finite boundaries, class closure,
  edge capacity, numeric behavior and ABI preconditions. No original source edit.
  Additional review concern: adapter assumes1D pi/c/key and integer runes, but
  does not explicitly guard every shape/conversion. Existing gate inputs comply.
- `REPORT.md`: full verdict, limitations, costs and approval options; registry
  proposal only. No shared registry or existing phase17 log edits.
- `WORK_LOG.md`: dated session decisions/results in this NEW folder.
- `RUNNING.md`: safe read-only reproduction commands.
- `summary.py`, `summary.json`: read-only audit summary, NOT an E5 candidate
  summary or campaign driver.

## 2. Half-done / blocked work, and exact next command

There is NO half-running computation to resume. All completed proof data and
failure artifacts are already on disk. The partial scope is:

- E3' sanity nulls: **0/5 n300, 0/3 n600** full-bank searches. All maxima unknown.
- E3' real-bank skip5/coin gap: unknown; only exact tiny examples completed.
- E4': **0/200 plants**, no Viterbi/source-stratum/alias/count/first-repair
  measurements. No new stochastic seeds consumed or replaced.
- E5: invariant review completed, but queue and candidate/ranking summary NOT
  built. No launch. The audit `summary.py` is not a substitute for that package.

The stop is the inherited FIRST-FAILED-GATE rule, NOT the clarified wall budget.
Inherited E2 estimates: requested eight sanity nulls~2.019 wall hours at four
workers;200 conditional-stream scans at20k key values~5min scoring-only,
tracebacks/diagnostics/overhead additional and unknown. Full82-window campaign
~14.964 wall hours at four workers and is not authorized to launch.

**Exact next command (safe, read-only, seconds; repository root):**

```powershell
.venv/Scripts/python.exe -B work/chanscreen/v2/step2/summary.py
```

Optional integrity check, also read-only and seconds:

```powershell
.venv/Scripts/python.exe -B work/chanscreen/v2/step2/snapshot.py verify
```

There is NO authorized scientific continuation command after that. Do NOT rerun
`gate.py` or `freeze.py`, delete markers, change the denominator/offset scope,
replace seeds, or launch sanity/power/campaign scans to bypass the failure.

Ask the user to authorize one separately labeled follow-up, preserving this FAIL:
1. Change to a common-null score S_W=log Z_L-log W(c), using the unchanged v2
   engine outputs. Then the normalization theorem is exact under W for every
   channel/finite offset. New statistic needs fresh power gates; English-M04
   and LP2 are still not proven to follow W.
2. Keep S but derive rigorous density corrections / revised offset scope.
   Full-length hold/spend restrictions alone do not fix skip5/coin.
3. Keep T heuristically WITHOUT a certified common-null alpha guarantee and
   explicitly authorize proceeding past the failed proof to the requested tests.

Also clarify the requested wrong-offset count condition: a tail theorem bounds
an EXPECTATION, not every realized count, and positive-plant neighbors may be
non-null aliases. Current frozen protocol keeps it as a literal hard empirical
stop; it was not silently relaxed. At t10 a pass with<=22,026 wrong cells demands
zero exceedances. No such count check has yet been executed.

For any authorized continuation: record the revised protocol before execution,
checkpoint raw outputs after each block, keep all previous files immutable,
<=4 workers, NO GPU, commands/runs <=10 minutes under the latest instruction.

## 3. Decisions not otherwise in a file

**None of the scientific decisions is only in conversation memory.** They are
in README.md, PROOF.md, REPORT.md and WORK_LOG.md. This STATE.md records the new
10-minute ceiling and the post-manifest handoff explicitly.

Important already-filed qualifications to carry forward:
- v1 has no stored n600 M04 sanity ciphertexts. README.md describes a proposed
  deterministic extension of original seeds100..102 preserving their300-rune
  prefix, with no replacement if extension checks fail. It is NOT implemented
  or run; do not pretend stored n600 v1 controls already exist.
- E4' searches only the supplied true stream, so stream identity is provided,
  not recovered among1439 alternatives. Other identification metrics conditional.
- Mid-stream first-rune repair violates the decoder's absent-predecessor initial
  assumption; test it honestly rather than modifying immutable v2 to hide it.
- No score correction, offset filter, new LM fit, GPU repair or campaign package
  was implemented after the failed proof. No unreported null/plant run exists.
