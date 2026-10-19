# Safe reproduction and handoff

Nothing in LP2 is solved. Current state: E0/E1/E2 PASS; E3–E5 INCOMPLETE because
calibration exceeds the frozen budget. No GPU work, no LP2 search.

## Fast suite (no new seeds, no long-run replay)

From repository root, Windows PowerShell, with existing Rust/NumPy installation:

```powershell
New-Item -ItemType Directory -Force work/chanscreen/v2/build | Out-Null
rustc --crate-type cdylib -O work/chanscreen/v2/backward.rs -o work/chanscreen/v2/build/backward.dll
# MSVC's unused debug/linker artifacts can embed local paths; remove them.
Remove-Item work/chanscreen/v2/build/*.pdb, work/chanscreen/v2/build/*.exp -ErrorAction SilentlyContinue
.venv/Scripts/python.exe -B work/chanscreen/v2/test_v2.py
.venv/Scripts/python.exe -B work/chanscreen/v2/snapshot.py verify
.venv/Scripts/python.exe -B work/chanscreen/v2/summary.py
```

Linux build (existing tools only):

```sh
mkdir -p work/chanscreen/v2/build
rustc --crate-type cdylib -O work/chanscreen/v2/backward.rs -o work/chanscreen/v2/build/libbackward.so
python -B work/chanscreen/v2/test_v2.py
```

Measured suite:6 tests,36.15s, zero skips. `snapshot.py verify` is read-only;
never run snapshot creation again to bless a changed v1. The snapshot includes
original binaries/cache files as requested, so a different machine lacking
those files will correctly fail that strict inventory check. Numerical source
reproduction is possible there, but do not silently redefine immutability.

Python `-B` prevents imported v1/M04 code from creating cache files. Always use it.
No runner/setup command or shared-engine rebuild is needed. Missing dependencies
must be reported; do not auto-install. Test suite expects original v1 raw records
locally available; they may be git-ignored, so transferring only tracked code is
not sufficient for full raw-data parity reproduction.

## API: one pass, all offsets

```python
import sys
sys.path.insert(0, 'work/chanscreen/v2')
import numpy as np
from engine import all_offsets
model = np.load('work/chanscreen/model.npz')
# cipher/key: integer sequences in0..28; ch: hold/spend/skip/skip5/coin
# out = all_offsets(cipher, key, +1, .81, 'hold', model['pi'], model['L'])
# out[o,0] = log Z_L(o); out[o,1] = log Z_U(o), for o=0..len(key).
# supported = np.isfinite(out[:,1])
# scores = np.full(len(out), np.nan)
# scores[supported] = out[supported,0] - out[supported,1]
```

U=0 means impossible output under that key/channel; do not rank NaN or turn
0/0 into positive infinity. L=0,U>0 gives score negative infinity. Empty cipher
has both logs0 for all offsets, including the end. Byte-array keys are supported.
The API keeps the absent-previous-ciphertext first-rune convention of v1.

## Gate artifacts and raw outputs

- `v1_m04_snapshot.json`: first-step SHA-256 inventory,1,241 immutable files.
- `README.md`, `E2_README.md`: protocols frozen before respective runs.
- `PROOF.md`: structural proof and tail recurrence.
- `sparse.py`: rational and NumPy sparse all-offset references.
- `backward.rs`, `engine.py`: independent specialized Float64 log-DP accelerator.
- `e0.json`: exactness counts and all seven mutant witnesses.
- `e1_parts/*/result.json` plus NPZ arrays: disjoint fixed-input checkpoints;
  cal/held records store expected and actual two-log arrays, random blocks retain
  their starting input index and both arrays. Inputs stay in immutable v1.
- `e1.json`: aggregate coverage,693,940 scores, no new held-out seed run.
- `e2_rows/`, `e2_inputs.npz`, `e2.json`: every benchmark row, generated benchmark
  inputs and actual library/section LENGTH inventory (not LP2 scores).
- `e3.json`, `blocked.json`: explicit incomplete/budget decisions.
- `summary.py`: read-only aggregation; `summary.json` is the captured result.
- `tests.txt`, `immutability.json`, `privacy_scan.json`: final checks.

Gate runners refuse existing artifacts. Do not erase a started marker or rerun
under another seed. The fast suite rechecks deterministic correctness without
rewriting gate verdicts. A full E1 audit on a separate authorized run may reuse
the fixed inputs but needs a clearly separate output destination, not overwriting
this attempt. No E3 or LP2 campaign driver is supplied as if controls had passed.

## Next decision

Read REPORT.md, especially budget accounting and needs-your-approval. Options:
explicitly authorize a30-window n300 pilot under a wall-time budget; enlarge
CPU budget; or authorize a new g3b GPU calibration path even though the conditional
campaign projection is below8h. Then freeze the follow-up protocol BEFORE reading
real-bank maxima. Do not deploy v1's threshold or refit the LM on mismatch plants.

Any future candidate needs whole-window reconstruction and whole-section checks
with matched controls before it can be considered a lead. Library-scale power,
LM-mismatch power, numeric real-bank threshold and actual14-thread runtime remain
unknown. The speed measurements do not fill those gaps.
