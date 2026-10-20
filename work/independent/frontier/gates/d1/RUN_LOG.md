# D1 FIRST-gate invocation log

Authorization: user approved D2, THEN D1's first gate, each at most two minutes,
each in its own folder. D2's failed gate was retained, not rerun. This independent
D1 protocol and source were written before its own execution. Static AST/path/
no-prior-result preflight passed; that was not an experimental invocation.

## One invocation — FINISHED, FIRST CORRECTNESS GATE PASSED

Command, from repository root:

```
PYTHONIOENCODING=utf-8 python -B work/independent/frontier/gates/d1/gate.py
```

External timeout120 seconds; cooperative wall deadline90 seconds. Actual elapsed
**0.56956 seconds** (`result.json:2888`). Exit0; no exception, timeout or retry.

Result: **PASS_FIRST_CORRECTNESS_GATE** (`result.json:3`). Exact summary:
`result.json:2889-2896`: 200 exact laws, 4,840 observed-output probability
comparisons, all six deliberately broken DP variants detected. Full per-law
successful/failed masses and exact comparisons remain in the result, together
with the distinct hold/insertion state fixture, offset-prior marginalization
and conditional common-global-normalizer checks (`result.json:2480-2887`).

This was a single foreground Python process, standard library only. It imported
no project modules, launched no engine/subprocess, read no LP2 ciphertext, used
no random seeds and performed no planted-key sensitivity/calibration search.
Hashes of its source, frozen protocol and design documents are in `result.json`.
All files created for D1 stayed here. No shared engine or ledger was changed.

Passing this first gate proves the stated tiny-law implementation checks, NOT
English plaintext/key-family recovery power, real structured-key identifiability,
a null-tail threshold or an LP2 negative. No later calibration or LP2 look was
started; it still requires separate approval. Nothing in LP2 is solved.
