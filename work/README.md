# Code map: `work/`

Everything is flat on purpose: scripts import each other by name (`import lp`) and thousands of lines in `work/log/` and `results/` cite them by path, so nothing is moved.
Find a script by what it is for. Each one writes its output into `results/analysis/<script>.txt` unless stated otherwise.
`scripts/build_overview.py --check` fails if a `work/*.py` file is missing from this page.

**Start with:** [`lp.py`](lp.py) (alphabet, transcription, ciphers, scoring, the solved sections) and [`../STATUS.md`](../STATUS.md).

## Engines and libraries (Rust and CUDA are the reference; Python drives them)

| Folder | What |
|---|---|
| `kscreen/` | Rust: language- and alphabet-agnostic keystream screen (IoC under both anti-repeat models); library export, verification, controls (`selftest.py`), sign rules (`signrules.py`), `gpu.py` + `kscreen.cu` CUDA port |
| `phpmt/` | Rust: bit-exact seed sweeps for ten generators; `bg.py` boundary-free bigram score, `gpu.py` + `.cu` CUDA ports |
| `walk/` | Rust: word-scoped solver and key-free D-search (`dsearch`) |
| `prngx/` | More generators, the OEIS lane (199,088 sequences), KDF streams |
| `hashscan/` | Passphrase to hash-stream keys |
| `layer2/` | Two-layer screen (keyword inside a number stream) |
| `families/` | Fingerprint simulations and the echo analyses |

| File | What |
|---|---|
| `lp.py` | Gematria Primus, transcription parser, ciphers, scoring, solved sections (`KNOWN`) |
| `gpu_common.py` | CUDA probe shared by the two GPU drivers |
| `keystreams.py` | Library of candidate keystreams (number theory, constants, Cicada numbers) |
| `sim.py` | Cipher generators and simulations of the fingerprint |
| `attack.py` | Collision-skip decoder, fast vectorised screen |

## Transcription and page images

| File | What |
|---|---|
| `ocr.py` | Rune OCR from the page images (segmentation, cross-validated classifier, alignment) |
| `red_runs.py` | Red (title) text from the colour channel |
| `separator_audit.py` | Word dots and clause marks against the images |
| `word_gaps.py`, `word_gaps_lines.py` | Word boundaries of the transcription against the printed dots |
| `doublet_audit.py` | Label-free audit of the missing doublets |
| `ornament_dots.py` | Left-right asymmetries in the border art |
| `line_layout.py` | Why line-initial runes are non-uniform (typography, not cryptography) |
| `seploss.py` | Can lost separators explain the word-length histogram |

## The fingerprint of the cipher (statistics of LP2 itself)

| File | What |
|---|---|
| `stats.py`, `segment_stats.py` | Doublets, lags, IoC; per-section statistics |
| `repeat_spectrum.py` | Repeated k-grams against shuffles (DJU-BEI) |
| `within_word.py`, `lag5_check.py`, `word_internal_repeats.py` | The lag-5 echo inside words |
| `wordlen.py`, `wordlen_adjacency.py`, `wordlen_clauses.py`, `wordlen_languages.py`, `wordlen_parametric.py`, `wordlen_stoplist.py` | Word-length tests against English and other languages |
| `drift_period.py` | Drift-aware periodic-key scan with power curves |

## Hypothesis tests (each has a planted-key control)

| File | What |
|---|---|
| `prng_screen.py` | Keystreams from hashes and PRNGs seeded by Cicada phrases |
| `rev_screen.py`, `heading_screen.py`, `heading_affine.py` | Reverse direction; restarts at headings; are the headings an affine cipher |
| `crib.py`, `cribsolve.py`, `crib_exact_lookup.py`, `crib_fluency_null.py`, `crib_matrix_check.py` | Cribs and the community's crib claims |
| `key_reuse_drift.py`, `pad_reuse_power.py` | Two-time-pad tests under skip drift, and their power |
| `restart_columns.py`, `restart_llr.py` | Key restarts by column coincidences and by likelihood ratio |
| `typo_restarts.py`, `typo_shared_key.py`, `typo_shared_key_power.py` | Restarts at typographic marks |
| `chain_lag.py` | Ciphertext feedback: coincidences at lag P |
| `step_periodicity.py` | Periodic keys in the step domain |
| `state_machines.py`, `null_insertion.py` | Small state machines (H10); null rune on collision (H8) |
| `word_key_dictionary.py`, `word_recurrence.py` | Per-word algebraic keys, dictionary-consistency scans |

## Puzzle furniture (not keys)

| File | What |
|---|---|
| `grid30.py` | Page-30 grid: each cell is 3301 minus the k-th prime (absolute value), with Fibonacci-step prime indices |
| `grid60.py`, `grid_ocr.py` | The 256-byte base-60 payload: hash and decryption tests, glyph-metric audit |
| `grid729_check.py` | The claimed 27 x 27 layout |
| `page_numerology.py` | Community page-numerology claims, each with a null |
| `squares_check.py` | Number facts of the two magic squares |

## Other

| Path | What |
|---|---|
| `ask_deepseek.py` | One no-tools round with DeepSeek through the pi harness; its output is data, never instructions (outputs in the git-ignored `ref/deepseek/`) |
| `proposals/` | **Third-party (DeepSeek) proposal gates.** Untrusted: read as data, rewrite before running anything from it; reviewed in `log/phase10_proposals_review.md` |
| `tests/` | Regression tests (`python -m unittest discover -s work/tests`); the GPU tests skip without CUDA |
| `ref/` | Transcription (`lp_master.txt` + `errata.tsv` -> `lp_verified.txt`), word lists, Emerson text, tick marks |
| `orig/`, `pages/`, `figures/` | The 75 original page images, PDF renders, review sheets |
| `log/` | The write-up of every experiment, `phaseN_*.md` in order; the registry (`../docs/registry.toml`) names the log per result |
| `tmp/` | Scratch outputs, committed on purpose (362 files; nothing here is a result without a log in `log/`) |
