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
| `page_scan_audit.py`, `book_map.py` | Structure audit of the 75 scans (containers, appended bytes, hash match, hidden faint marks, stipple) with a planted-mark control; the annotated map of all pages (`figures/book_map.png`) |
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
| `book_key_flatness.py` | A book as the running key (any language, any letter -> rune table): LP2's IoC against encryptions under the GP, random and flattest tables, with the skip rule (`results/analysis/book_key_flatness.txt`) |
| `book_key_pairs.py` | The same through lag-2..8 rune-pair counts, with a table tuned to flatten the pairs (`results/analysis/book_key_pairs.txt`) |
| `book_key_decoder.py` | Table-invariant, drift-tracking decoder for a candidate book key (table-free beam + exact skip-rule Viterbi EM) and its gate: plants with a flattening table, nulls, power and cost (`results/analysis/book_key_decoder.txt`); no LP2 run |
| `word_structure.py` | Does the word segmentation depend on the neighbouring runes, and is there a schedule by position in the word or by (length, position)? Three keyless tests, each with planted controls and shuffle nulls (`--quick` for a minute; `results/analysis/word_structure.txt`) |
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
| `prime_sums.py` | Gematria sums of the solved pages' sentences are prime far more often than chance (z 7.9); LP2's ciphertext units are not; clause lengths and doublet rates, LP1 against LP2 |
| `prime_check.py` | Prime-sum check of a candidate decryption (clauses inside the decoded window, binomial probability, short-clause evidence); `control` runs the solved pages with right and wrong keys |
| `squares_check.py` | Number facts of the two magic squares |

## Other

| Path | What |
|---|---|
| `ask_deepseek.py` | One no-tools round with DeepSeek through the pi harness; its output is data, never instructions (outputs in the git-ignored `ref/deepseek/`) |
| `ogscan/` | Own OutGuess-style reader: Rust baseline-JPEG coefficient lister (`src/main.rs`), RC4 / iterator extraction (`og.py`), the scan with controls (`run_scan.py` -> `results/analysis/outguess_scan.txt`); bit lists and the build are git-ignored |
| `h5power/` | Power map of the H5 flat-library sweep: independent stream + keyword plants through the real `h5rs sweep` path, recall by L / model / key kind / offset; 3 tests (`python -m unittest test_h5power` from `work/h5power`) |
| `m04/` | M04 hold-key repair crossed against the unchanged kscreen engine: independent plant generator, harness, frozen protocol (`README.md`), 10 tests (`python -m unittest test_m04` from `work/m04`) |
| `proposals/` | **Third-party (DeepSeek) proposal gates.** Untrusted: read as data, rewrite before running anything from it; reviewed in `log/phase10_proposals_review.md` |
| `tests/` | Regression tests (`python -m unittest discover -s work/tests`); the GPU tests skip without CUDA |
| `ref/` | Transcription (`lp_master.txt` + `errata.tsv` -> `lp_verified.txt`), word lists, Emerson text, tick marks |
| `orig/`, `pages/`, `figures/` | The 75 original page images, PDF renders, review sheets |
| `log/` | The write-up of every experiment, `phaseN_*.md` in order; the registry (`../docs/registry.toml`) names the log per result |
| `tmp/` | Scratch outputs, committed on purpose (362 files; nothing here is a result without a log in `log/`) |
