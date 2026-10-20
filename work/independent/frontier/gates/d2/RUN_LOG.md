# D2 invocation log

Authorization: user approved D2, THEN D1's first gate, each at most two minutes,
each in its own folder. Gate protocol and source were written before execution.
Static AST/path/no-prior-result preflight passed; that was not an experiment.

## One experimental invocation — FINISHED, GATE FAILED

Command, from repository root:

```
PYTHONIOENCODING=utf-8 python -B work/independent/frontier/gates/d2/gate.py
```

External timeout: 120 seconds. Cooperative wall deadline: 90 seconds, including
loading, the sequential native engine calls and checks. Actual elapsed:
**2.680275 seconds** (`result.json:592`). Shell exit1 is the deliberate failed-gate
exit, not a crash; no exception was recorded. No timeout or automatic retry.

Frozen result: **FAILED_RECOVERY_GATE** (`result.json:3`). Summary and retained
failed deep-offset regression: `result.json:593-607`. Four canonical unknown-
keyword controls: one passes; all eight keyword-known references pass. All 144
new native synthetic cells and both equal-size null sensitivities are retained.
The old c1500 synthetic plant still aborts and is counted as failed recovery.

Artifacts: `PROTOCOL.md`, `gate.py`, `result.json`, `plants.json`, `cells.txt`,
`native_cells.txt`, `native_stdout.txt`, `native_stderr.txt`,
`retained_c1500.txt`, `c1500_stdout.txt`, `c1500_stderr.txt`, `REPORT.md`.
All input/code/protocol/binary hashes and exact native argv are in `result.json`.
`NOTES.md` distinguishes the strict failed criterion from the descriptive
flat-forward positive; it does not relax the gate or change its frozen outputs.

There was one foreground controller and at most one computing native child at a
time, no multiprocessing, no GPU, no builds, no downloads and no LP2 search.
No extra seed, keyword, offset, no-abort run or engine patch followed the failure.
All files created for D2 stayed in this directory. The separately approved D1
FIRST gate followed; no D2 calibration or larger sweep was started.
