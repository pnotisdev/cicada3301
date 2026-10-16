# Liber Primus (Cicada 3301): cryptanalysis workspace

Tools, data and results from a systematic attempt on the unsolved part of Cicada 3301's *Liber Primus*
(the 2014 rune book). **The unsolved pages are still unsolved.** This repository is built so that every
claim can be re-run and every negative result comes with a positive control showing the method would have
found a real answer.

- `PLAN.md` holds the full research plan and every phase's results.
- `work/log/` holds detailed write-ups per experiment.
- `work/log/research_2026-10-16.md` covers how this relates to the community's work: Dukotah, Wulfic,
  aldegonde/cicada-solvers.

## Quick start

Requirements: Python 3.11+ and Rust (stable). PHP and PowerShell are only needed to regenerate reference
vectors.

```bash
python -m pip install -r requirements.txt
python scripts/fetch_data.py                 # verifies the committed data (or re-downloads it if missing)
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

## Layout

```
LiberPrimus.pdf            the book (print of the 75 original page images)
PLAN.md                    research plan and results, phase by phase
scripts/fetch_data.py      data sources, pinned hashes, builds work/ref/lp_verified.txt from master + errata
jobs/                      overnight.py campaign runner; setup and older shell jobs
docs/                      CAMPAIGNS.md (what the overnight runs test), GPU_PORT.md
results/                   outputs of long runs (sweep candidate lists, search logs)
work/
  lp.py                    Gematria Primus, transcription parser, ciphers, scoring, solved sections (KNOWN)
  ocr.py                   rune OCR from the page images: segmentation, cross-validated classifier, alignment
  grid_ocr.py grid60.py    the 256-byte base-60 payload on pp. 64-66: glyph-metric audit, hash / AES tests
  grid30.py                the page-30 4x4 grid: |3301 - p_k| with Fibonacci-step prime indices, spiral
  stats.py sim.py          statistics of the unsolved text; cipher-generator simulations
  attack.py keystreams.py  collision-skip decoder, fast vectorised screen, keystream library
  crib.py cribsolve.py     crib deductions, key-reuse scans, constraint solver (periodic / two-time pad)
  prng_screen.py rev_screen.py heading_screen.py red_runs.py doublet_audit.py
  drift_period.py          periodic-key scan that allows for the skip rule's key drift, with power curves
  wordlen.py               word-length test: LP2 vs English in runes / in letters / with nulls
  kscreen/                 Rust: language- and alphabet-agnostic keystream screen (IoC under both anti-repeat
                           models), keystream library export, verification, selftest; gpu.py + kscreen.cu: CUDA port
  phpmt/                   Rust: PHP/glibc/.NET seed sweeps (bit-exact generators, validated vectors in ref/);
                           gpu.py + phpmt.cu: CUDA port
  gpu_common.py            CUDA probe shared by the two GPU drivers
  walk/                    Rust: word-scoped solver (annealing) and key-free D-search (dsearch)
  ref/                     transcription (rtkd/iddqd), errata, word list, Emerson text
  orig/                    the 75 original page images
  log/                     write-ups of each experiment
  tests/                   regression tests (solved pages, transcription, statistics, engines)
```

## What is established (short version)

- **Solved sections:** every one reproduces exactly. Plaintext F is never encrypted and does not consume a key
  position.
- **Transcription:** an independent OCR re-read confirms the LP2 transcription. Corrections found:
  - one rune-order error on a solved page (BELIEVE);
  - **5 byte errors in the 256-byte base-60 payload**, 3 of which are also in Dukotah's `canon_256.bin`;
  - no merged doublets anywhere (the anti-repeat filter is real).
- **The cipher's fingerprint:**
  - flat unigrams and bigrams, and no coincidence peak at any lag up to 6000 (but see the periodic-key
    caveat below);
  - doublets suppressed about 5× and boundary-blind;
  - a within-word distance-5 echo (102/2,073, p < 0.001), reproduced from aldegonde;
  - the repeated phrase ᛞᛄᚢ-ᛒᛖᛁ;
  - fewer 2-rune words than English. The length histogram rejects English in runes (p ≈ 10⁻⁴²). The best
    simple fit is one extra rune in about 40% of multi-rune words (p = 0.025).
- **Ruled out, each with a validated method:**
  - English or solved-text running keys and autokeys;
  - periodic keys up to about 400 runes. That limit comes from a drift-aware scan, because under the skip
    rule the old lag scan only covers about 60. Key reuse between sections;
  - about 1,000 number-theoretic and Cicada-number keystreams at every offset, both reading directions;
  - keyword keys; hash and PRNG keys seeded with Cicada phrases;
  - transposition after encryption;
  - a per-word additive key behind a secret alphabet (D-search: LP2 ≈ surrogates).
- **Explained puzzle furniture:**
  - the page-30 grid (|3301 − p_k|, Fibonacci-step prime indices, spiral);
  - the Some Wisdom word square (1033);
  - the page-14 square (3301).

## Sources

Transcription and images: [rtkd/iddqd](https://github.com/rtkd/iddqd). Community research this builds on:
[Dukotah/cicada3301](https://github.com/Dukotah/cicada3301),
[Wulfic/Cicada3301-Liber_Primus](https://github.com/Wulfic/Cicada3301-Liber_Primus),
[cicada-solvers](https://github.com/cicada-solvers) (aldegonde, Red_Rune_Cribs, iddqd). Word frequencies:
[first20hours/google-10000-english](https://github.com/first20hours/google-10000-english). Emerson, *Essays:
First Series*: Project Gutenberg #2944.
