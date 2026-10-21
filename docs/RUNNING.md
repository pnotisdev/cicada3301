# Running things: setup, tests, campaigns, long jobs, GPU

Moved out of the README (2026-10-18) so that the README can lead with the results. Content unchanged. `docs/CAMPAIGNS.md` explains what each campaign tests; `docs/QUEUE.md` the detached job queues; `docs/GPU_PORT.md` the CUDA gates.

## Quick start

Requirements: Python 3.11+ and Rust (stable). PHP and PowerShell are only needed to regenerate reference
vectors.

```bash
python -m pip install -r requirements.txt
python scripts/fetch_data.py                 # verifies the committed data (or re-downloads it if missing)
python scripts/fetch_data.py --corpora      # the git-ignored books and comparison corpora (docs/SOURCES.md)
(cd work/phpmt && cargo build --release)     # PRNG-pad sweep engine
(cd work/walk  && cargo build --release)     # word-scoped solver and key-free alphabet search
(cd work/kscreen && cargo build --release)   # language-agnostic keystream screen
python -m unittest discover -s work/tests    # 71 tests, about 10 minutes (the 6 GPU tests skip without CUDA)
```

On Linux/macOS, `jobs/setup.sh` does all of the above. On a Windows PC where the global Python is not writable,
use a virtual environment in the repository (`python -m venv .venv`, git-ignored) and run everything with
`.venv\Scripts\python.exe`. The book (`LiberPrimus.pdf`), the 75 original page
images (`work/orig/`) and the text data (`work/ref/`) are committed. The sources are listed in
`scripts/fetch_data.py`, which checks them against pinned SHA-256 hashes.

## Overnight campaigns

```bash
python jobs/overnight.py list               # what exists, rough hours, what is done
python jobs/overnight.py run --hours 9      # run in priority order; resumable; report in results/overnight/<machine>/REPORT.md
```

`jobs/overnight.py` builds everything, runs the regression tests and the controls, and then runs the
campaigns:
- **The new language-agnostic keystream screen (`work/kscreen`).** 1,447 keystreams, every order ≤ 3 linear
  recurrence and every polynomial key mod 29, each at every offset, under both anti-repeat models. It is
  insensitive to the plaintext language and to any substituted plaintext alphabet.
- **The dictionary screens**, rerun with the corrected segmentation.
- **Large D-search runs.**
- **Payload decryptions** on the corrected bytes.
- **PRNG sweeps** with a fresh seed per section.

`docs/CAMPAIGNS.md` explains what each campaign tests, why, its controls and its decision rule.

## Individual long jobs

| Job | What it does | Rough cost (16 threads) |
|---|---|---|
| `jobs/prng_sweeps.sh` | Tests every seed of PHP<7.1 `mt_rand`, glibc `random()` (PHP 5 `rand()` on Linux) and .NET `System.Random` as the key generator. Each runs 16 cipher variants and 2 anti-repeat models through a skip-aware decoder. `WINDOWS=07`: one whole-book pad; `WINDOWS=all`: a fresh seed per section. | Window 0.7: ~1.5 h per generator on a laptop; all 8 windows: ~5 h per generator on a 16-thread desktop, ~45 min on the GPU |
| `jobs/walk_dsearch.sh` | Key-free search for a secret outer alphabet behind a per-word additive key, with m = 1…8 position phases. Runs against structure-free surrogates with LP2's word lengths and anti-repeat rule. | ~2 min per run at 300k iterations; scale `ITERS`/`RESTARTS` up |
| `python work/attack.py slide` | Number-theoretic keystreams (primes, φ, π…) at every start offset | ~70 min |
| `python work/heading_screen.py` | The same keystreams restarted at every red heading and paragraph | ~2 h |

Environment knobs: `THREADS`, `GENS`, `WINDOWS`, `ITERS`, `RESTARTS`, `MS`, `GAPSETS`. Results go to
`results/`. The sweep's best candidates are re-decoded over whole segments by `work/phpmt/verify_top.py`
against random-seed controls. A real key stands out at z ≈ +60 or more (planted control: 0.815 against
0.111 ± 0.010).

### GPU (optional)

The Rust engines are the reference. `work/kscreen/gpu.py` and `work/phpmt/gpu.py` are CUDA ports of the keystream
screen and of the seed sweeps (CuPy, kernels compiled at run time with NVRTC). They reproduce the CPU engines
decode for decode and are validated before every use. Install: `python -m pip install -r requirements-gpu.txt`
(an NVIDIA driver is needed; NVRTC comes from the installed CUDA Toolkit 12.x, or from the pip package
`nvidia-cuda-nvrtc-cu12`). `python jobs/overnight.py run --device auto` (the default) uses CUDA only if the
probe, the decode-by-decode selfchecks and the planted-key controls pass, and otherwise runs the CPU engines
unchanged; `--device cpu` forces the CPU, `--device cuda` stops if CUDA is unusable. Measured on an RTX 2080 Ti
against a 16-thread Ryzen 7 2700X: the keystream screen 1.8–4×, the seed sweeps 6.8×. Details and the validation
gates are in `docs/GPU_PORT.md`.
