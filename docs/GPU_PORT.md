# CUDA ports of the engines (RTX 2080 Ti, 11 GB)

Two engines have a CUDA port. The Rust engines stay the reference: a GPU result counts only because the port
reproduces the CPU result decode for decode (gates below), and `jobs/overnight.py` re-checks that on the machine
before it uses the GPU.

| Engine | CPU reference | GPU port | What one thread does |
|---|---|---|---|
| keystream screen | `work/kscreen/src/main.rs` | `work/kscreen/gpu.py`, `kscreen.cu` | one (keystream, start offset, multiplier) task: every model and window |
| seed sweeps (PHP / glibc / .NET, and py3 / mt32 / mt31 / java / msvc / drand48 / ruby) | `work/phpmt/src/main.rs`, `gens.rs` | `work/phpmt/gpu.py`, `phpmt.cu` | one seed: both key maps (160 values each), 8 windows x 16 variants |
| seed sweeps with 64-bit seeds (py3 / ruby / java: millisecond timestamps), boundary-free score | independent Python references (CPython `random`, `java.util.Random` from its specification: `work/phpmt/ref_keys64.py`) and the 32-bit kernel `bgmt.cu` below 2^32 | `work/phpmt/bg64.py`, `bgmt64.cu` (built by `make_bgmt64.py`) | one seed: both key maps, the windows x 16 variants |

Not ported: the annealing key-free alphabet search (`work/walk`, already scales with threads and has no large
independent batch), and the numpy dictionary screens (`work/attack.py`, small).

## Install and use

```
python -m pip install -r requirements-gpu.txt      # cupy-cuda12x; NVRTC comes from CUDA Toolkit 12.x or nvidia-cuda-nvrtc-cu12
python jobs/overnight.py run --device auto         # default: CUDA only if the validation below passes
```

CuPy compiles the `.cu` files with NVRTC at run time (cache in the git-ignored `work/*/target/cupy_cache`), so no
Visual Studio or `nvcc` is needed. `--device cpu` never touches the GPU; `--device cuda` stops if validation
fails. A CUDA step that fails while running is rerun on the CPU engine. Without CUDA (the laptop, CI) nothing
changes and the GPU tests skip themselves.

Kernels are sized to run about 0.3 s each: Windows resets a GPU that is driving a display when one kernel runs for
more than about 2 s (TDR).

## Validation gates (all automated)

`jobs/overnight.py` runs them at the start of every run and writes `results/overnight/<machine>/gpu_validation.txt`:

1. **Probe.** CuPy imports, a device exists, NVRTC compiles and a kernel runs.
2. **Decode by decode (a).** `gpu.py selfcheck` of each port: the CPU engine writes one line per decode
   (`kscreen trace`, `phpmt scores`, `phpmt raw`) and the port must write identical text.
   - kscreen: 40,616 decodes (`s` and runes used) over file, linear-recurrence, polynomial and random keystreams,
     both models, several multipliers. 1,703 of them go through the generic fallback kernel, and the check fails
     if the fallback is never exercised.
   - seed sweeps: the first 160 raw outputs of 496 seeds per generator (including seeds 2^31 and 2^32 - 1), and
     153,088 decode scores per generator.
3. **Planted keys (b).** `work/kscreen/selftest.py --engine cuda`: 15 planted windows (five key families, both
   models, both signs, with and without a substituted alphabet) must come back at their exact offsets, and the
   random-key null must stay under IoC 1.40. The unit tests also plant a seed for each of PHP, glibc and .NET and
   require rank 1 from the GPU sweep.
4. **Aggregates (a).** `work/tests/test_kscreen_gpu.py` and `test_phpmt_gpu.py`: whole screens and sweeps against
   the CPU engine - decode and early-abort counts, the full IoC (or score) histogram, each window's best, and
   the hit lists.

Measured when the ports were written (2026-10-17):

| Check | Result |
|---|---|
| kscreen full screens, GPU vs CPU | identical on 4 screens, 183 M decodes (library, linear recurrences on the heading windows, cubic polynomials, 40 random keystreams on the 46 page windows) |
| seed sweep, php, seeds 0..8 M, 8 windows | score histogram identical over 1.02 G decodes; every hit with score >= 12 identical (1,811) |
| speed, keystream screen | 2.3-4x the full 16-thread CPU on the 8 section windows, 1.8x on the 46 page windows |
| speed, seed sweep | 1.6 M seeds/s against 0.23 M/s: 6.8x. A full 2^32 sweep of all 8 windows is about 45 min instead of 5.4 h |

## 64-bit seeds (`prng-time`, 2026-10-17)

A program run in 2012-2014 that seeded from a MILLISECOND clock is not covered by the 32-bit sweeps: Java's `Random` keeps 48 seed bits and CPython / Ruby seed MT19937 with the two 32-bit words of an integer above 2^32.
`bgmt64.cu` is `bgmt.cu` changed by exact-snippet substitution (`make_bgmt64.py`; the build fails if `bgmt.cu` changes) for the generators py3, ruby and java (and `java-abs`, the second Java map `abs(nextInt()) % 29`):
`mt_state` takes the two-word `init_by_array`, Java takes the whole seed (a seed below 2^32 stays a sign-extended int, so every earlier result is unchanged). The candidate record keeps the low 32 bits of the seed and
`bg64.sweep` restores the rest from the chunk base. Gates (`work/tests/test_bgmt64.py`, `python work/tests/run_gate.py work.tests.test_bgmt64`, 8 tests, none may skip): the kernel text equals the build; keys equal INDEPENDENT
references at 2^31, 2^32 - 1, 2^32, 2^33, 2^40 + 12345, 2^48 - 1 and 25 random 2012-2014 timestamps for all four generators; below 2^32 keys and every decode score equal the 32-bit kernel; above 2^32 every score of
every variant equals the Python reference decoder on the independent keys; seven planted timestamp seeds (one in a chunk straddling 2^32) are recovered at rank 1 with the right map, sign and alphabet; random ciphertext gives
no candidate; the whole-section check (`bg64.py verify`, keys from `ref_keys64.py`) confirms a plant and rejects a wrong seed. Speed on the RTX 2080 Ti, one window: py3 / ruby 6.4 M seeds/s, java 10.8 M seeds/s, so the full
2012-01 .. 2014-02 window (6.58e10 ms timestamps) is about 2.9 h per py3 / ruby and 1.7 h per java map set (`work/phpmt/time_gpu.py`, month by month, resumable). Limits: no Ruby is available, so the ruby keys are checked
against the documented rule on top of CPython's MT19937 only.

## What the kernels do

- **keystream screen.** The beam decoder is a statement-for-statement port, including the vector operations
  whose order matters (swap_remove, appended extras, the merge loop), so ties resolve the same way. The CPU
  engine's sort at the beam cut was made stable (it never triggers on random keys: 0 cuts in 291 M steps).
  Most decodes (98.6% on random keys) need at most 14 states at once. For those, the fast path keeps each
  state's 29 letter counts as packed bytes in shared memory, laid out so that the 32 lanes always hit 32
  different banks. Any decode that needs more states, a count of 255, or runs off the key is queued and redone
  by the generic kernel. This replaced a version in which the whole warp waited for its one slow lane (1.4% of
  decodes -> 36% of warp-steps). Reductions (histogram, per-window best, hit list) are done on the GPU.
- **seed sweeps.** The three generators are re-derived from the Rust code (PHP: the 557-step init chain with only
  the 161 words that are needed kept; glibc: a 32-word ring; .NET: the Knuth table). The key map is
  `(29 * n) >> 31`, which equals the Rust double computation for 31-bit `n`.

## Known limits

- The keystream screen uses the GPU at about 20% of what its instruction count would allow: the beam search
  diverges between lanes and there are only 3-4 resident warps per SM (shared memory). A deeper restructure (one
  decode per warp, a canonical tie-break instead of the Rust vector order) might reach 2x more; it would also
  change the CPU reference, so it was not done.
- The CPU engine's top-hit list used to compare with an unsorted vector entry before each thread's first prune
  (so it could miss a good hit); fixed in the same commit. Per-window bests and histograms were never affected,
  and a hit above the 1.40 threshold could only have been missed if that arbitrary entry was itself above 1.40.
- Profiling with Nsight Compute needs Windows' "GPU performance counters for all users" setting; it was not changed.

## Ideas for further work

- Any new generator (PHP `mt_rand` with offsets, Java `Random`, ISAAC, LFSRs) slots into `phpmt.cu` as another
  `gen_raw`.
- `walk dsearch` could use the GPU for thousands of independent restarts.
