# Reproduce the failed-proof audit safely

Nothing in LP2 is solved. E3' proof is FAIL; later searches/queue are blocked.

From repository root, existing environment only; no compilation/install/GPU:

```powershell
.venv/Scripts/python.exe -B work/chanscreen/v2/step2/test_step2.py
.venv/Scripts/python.exe -B work/chanscreen/v2/step2/summary.py
.venv/Scripts/python.exe -B work/chanscreen/v2/step2/snapshot.py verify
```

The six tests take about9 seconds. They recompute deterministic algebra and
confirm the counterexamples, NOT power seeds or null searches. Passing tests
means the recorded E3' FAILURE is reproducible. They read original dependencies
without bytecode writes. No Rust DLL is loaded for this audit.

summary.py is a read-only audit summary, NOT the requested E5 candidate summary.
It reports blocked gates, unknown null maxima/power and inherited cost estimates.
It never reads/scans LP2 ciphertext or invokes jobqueue.

Do NOT rerun freeze.py or gate.py in place: thresholds and the proof attempt
already exist, and write-once checks reject retries. Do not delete markers or
change thresholds to turn the failure into a pass. Frozen code/proof/README
hashes are recorded in E3_proof.json; originals in baseline_sha256.json.

Read these together:
- REPORT.md — verdict, exact witnesses, limitations and approval options.
- PROOF.md — true cell-matched theorem and common-null counterexamples.
- README.md — preregistered thresholds, proof gate and blocked follow-on scope.
- E3_proof.json — exact fractions, full small witness outputs and controls.
- thresholds.json — historical pre-gate values, NOT certified thresholds.
- REVIEW.md — backward.rs invariant and caller-precondition checklist.
- tests.txt / immutability.json / privacy_scan.json / resources.json.

A newly authorized statistical repair must be separately labeled and must leave
this failed gate and all original v1/v2 files unchanged. No campaign queue exists.
