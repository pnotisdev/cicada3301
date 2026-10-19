# Rebuild, reproduce, continue safely

Nothing in LP2 is solved. **Current stop: G3 FAIL.** Do not rerun G3/G2 or start
G4/G5 without the follow-up decision described in REPORT.md.

Commands below use repository-relative paths, from the repository root. No
installation, network or shared build is needed on the current machine.

## Safe reproduction: CPU suite and read-only result audit

Windows PowerShell (or CMD, omitting the PowerShell-specific directory command):

```powershell
New-Item -ItemType Directory -Force work/chanscreen/build | Out-Null
rustc --crate-type cdylib -O work/chanscreen/cpu.rs -o work/chanscreen/build/cpu.dll
.venv/Scripts/python.exe -B work/chanscreen/test_chanscreen.py
.venv/Scripts/python.exe -B work/chanscreen/audit.py
```

On Linux with Rust and NumPy already installed:

```sh
mkdir -p work/chanscreen/build
rustc --crate-type cdylib -O work/chanscreen/cpu.rs -o work/chanscreen/build/libcpu.so
python -B work/chanscreen/test_chanscreen.py
python -B work/chanscreen/audit.py
```

Measured Windows environment: Python 3.12.0, Rust 1.99.1; NumPy version and input
hashes in `frozen.json`. Cross-platform bit identity is not promised; numerical
parity thresholds remain the same. Suite was 68.49 s, 7 tests, no skips. It
rechecks G0/G1/CPU/traceback/adapter/numerical edge behavior, never G2 held-out
plants, never GPU, and does not overwrite gate artifacts. A missing local
cdylib is an ERROR, not a silently skipped test.

`audit.py` reads existing results; it checks input hashes, all 588 case records,
all 602,112 distinct cells, the chosen maxima and the G2 summary. It prints JSON
but changes nothing. It is not a new power run. Large raw results are intentional:
about 173 MiB in `raw/`, all kept because failures and full selection freedom
must remain auditable. Build/cache files alone are ignored by the local .gitignore.

## API example (one user-supplied synthetic window)

```python
import sys
sys.path.insert(0, 'work/chanscreen')
import numpy as np
import cpu
from reference import score
m = np.load('work/chanscreen/model.npz')
# cipher and key must be sequences of integers in 0..28; off is an absolute
# initial pointer. Choose q explicitly; do not infer it from a result to optimize.
# r = score(cipher, key, off, +1, .81, 'hold', m['pi'], m['L'], engine=cpu.forward)
# r['score'] is None if U cannot emit the observation under this finite key.
```

For the auditable NumPy path, omit `engine=cpu.forward`. For exact tiny rational
checks use `rational_forward` with Fraction-valued pi, L, q. The generic reference
is intentionally slow. `reconstruct.viterbi` is NOT a substitute for summed scoring.

## Original run structure (documentation, NOT a rerun instruction)

1. `gates.py g0`, then `gates.py g1`: write-once gate JSON.
2. `check_cpu.py`: write-once CPU parity/benchmark JSON.
3. `power.py init`: training-only model and source/input manifest.
4. `power.py train`: eight development plants/nulls; first invocation's adapter
   failure preserved, then same training seeds repeated after adapter correction.
5. `power.py cal START COUNT`: four non-overlapping blocks, (0,50), (50,50),
   (100,50), (150,50). All complete.
6. `power.py threshold`: freeze the 10th-largest of 200 maxima before held-out.
7. `power.py held START COUNT`: (0,50), (50,50), (280,50), (330,50), (100,50),
   (150,50), (200,40), (240,40). All complete, each seed evaluated once.
8. `power.py summarize`: writes G2 verdict; all criteria passed.
9. `check_gpu.py`: first invocation failed compiling math.h; STOP, no retries.

Scripts intentionally refuse to overwrite existing gate/threshold files or
re-evaluate attempted power tasks. `.started` without a result means INCOMPLETE;
do not delete the marker and silently repeat a held-out seed. Old scripts are
not a pipeline scheduler: the human/agent must obey the stop gates, not blindly
chain commands after failures. Each power block is <=50 tasks with four workers;
all BLAS pools are fixed at one. No subprocesses/worker processes persist.

## Next AI/human checklist

- Read REPORT.md, README.md, GPU_README.md and the phase17 log first.
- Preserve g3.json and its exact source hashes. No seed/criterion substitutions.
- Ask for approval to continue after G3 failure; keep that follow-up separate and
  labeled. Do not treat a repaired build as an erased failure.
- A future machine must have matching read-only M04 sources, corpus and generated
  flat library; `audit.py` flags missing/changed inputs. Do not auto-regenerate
  shared data while another agent/queue is using it.
- Reuse `gpu_parity.npz` inputs on the authorized repair. Its result arrays are
  uncomputed NaNs, not passing scores. The file includes lengths and modes, so
  padding is not part of a key/ciphertext.
- GPU correctness, real-bank cascade calibration and campaign costs are still
  outstanding. Do not deploy threshold -135.158123 to the real library.
