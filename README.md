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
python -m unittest discover -s work/tests    # 40 tests, about 4 minutes
```

On Linux/macOS, `jobs/setup.sh` does all of the above. The book (`LiberPrimus.pdf`), the 75 original page
images (`work/orig/`) and the text data (`work/ref/`) are committed. The sources are listed in
`scripts/fetch_data.py`, which checks them against pinned SHA-256 hashes.

## Long jobs

| Job | What it does | Rough cost (16 threads) |
|---|---|---|
| `jobs/prng_sweeps.sh` | Tests every seed of PHP<7.1 `mt_rand`, glibc `random()` (PHP 5 `rand()` on Linux) and .NET `System.Random` as the key generator. Each runs 16 cipher variants and 2 anti-repeat models through a skip-aware decoder. `WINDOWS=07`: one whole-book pad; `WINDOWS=all`: a fresh seed per section. | Window 0.7: ~1.5 h per generator; all 8 windows: ~12 h per generator |
| `jobs/walk_dsearch.sh` | Key-free search for a secret outer alphabet behind a per-word additive key, with m = 1…8 position phases. Runs against structure-free surrogates with LP2's word lengths and anti-repeat rule. | ~2 min per run at 300k iterations; scale `ITERS`/`RESTARTS` up |
| `python work/attack.py slide` | Number-theoretic keystreams (primes, φ, π…) at every start offset | ~70 min |
| `python work/heading_screen.py` | The same keystreams restarted at every red heading and paragraph | ~2 h |

Environment knobs: `THREADS`, `GENS`, `WINDOWS`, `ITERS`, `RESTARTS`, `MS`, `GAPSETS`. Results go to
`results/`. The sweep's best candidates are re-decoded over whole segments by `work/phpmt/verify_top.py`
against random-seed controls. A real key stands out at z ≈ +60 or more (planted control: 0.815 against
0.111 ± 0.010).

The engines are CPU code. The seed sweep is embarrassingly parallel, so a CUDA port of
`work/phpmt/src/main.rs` (generator, key mapping, early-abort decoder) is the obvious next step for a GPU
machine.

## Layout

```
LiberPrimus.pdf            the book (print of the 75 original page images)
PLAN.md                    research plan and results, phase by phase
scripts/fetch_data.py      data sources, pinned hashes, builds work/ref/lp_verified.txt from master + errata
jobs/                      setup and long-running jobs for a bigger machine
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
  phpmt/                   Rust: PHP/glibc/.NET seed sweeps (bit-exact generators, validated vectors in ref/)
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
  - flat unigrams, bigrams and every lag up to 6000;
  - doublets suppressed about 5× and boundary-blind;
  - a within-word distance-5 echo (102/2,073, p < 0.001), reproduced from aldegonde;
  - the repeated phrase ᛞᛄᚢ-ᛒᛖᛁ;
  - fewer 2-rune words than English.
- **Ruled out, each with a validated method:**
  - English or solved-text running keys and autokeys;
  - periodic keys up to 6000; key reuse between sections;
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
