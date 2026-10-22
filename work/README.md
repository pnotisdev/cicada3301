# Code map: `work/`

Everything is flat on purpose: scripts import each other by name (`import lp`) and thousands of lines in `work/log/` and `results/` cite them by path, so nothing is moved.
Find a script by what it is for. Each one writes its output into `results/analysis/<script>.txt` unless stated otherwise.
`scripts/build_overview.py --check` fails if a `work/*.py` file is missing from this page.

**Start with:** [`lp.py`](lp.py) (alphabet, transcription, ciphers, scoring, the solved sections) and [`../STATUS.md`](../STATUS.md).

## Engines and libraries (Rust and CUDA are the reference; Python drives them)

| Folder | What |
|---|---|
| `kscreen/` | Rust: language- and alphabet-agnostic keystream screen (IoC under both anti-repeat models); library export, verification, controls (`selftest.py`), sign rules (`signrules.py`), `gpu.py` + `kscreen.cu` CUDA port |
| `kscreen/phase60_t1.py`, `kscreen/phase60_t4t5.py`, `kscreen/phase60_t8.py` | Phase 60 tests: T1 word-sum streams and word-aligned / feedback keys; T4 Cicada OS files and T5 four-irrational streams on the plain library screen; T8 DATA/560.13 and the audio payloads (sampled) |
| `kscreen/phase35.py`, `kscreen/wordjump_control.py`, `kscreen/booknum.py`, `kscreen/layoutrules.py`, `kscreen/dirrules.py`, `kscreen/pdir_*.py` | 2026-10-20/21 extensions of the screen: LP2 word streams and reversed ciphertext (phase 35), word-length pointer jump advsep=3-5 (37), book number streams (33), layout sign / direction rules (36), pointer direction (30) |
| `phase38/` | Phase 38: do LP2's signals interact (isomorphs, S lag-5 x lag-6 overlap, echo-word lengths), pre-registered nulls |
| `phase40_line_pointers.py`, `phase44/` | Phase 40: line:position pointers into LP's own lines; phase 44: keyless batch (doublet fine structure, digraph blocks, 512-bit hashes of held files, word-length alignment) |
| `phase55_s_echo_dissect.py` | Phase 55: dissection of the lag-5 S,S echo (position, length, neighbours, other runes, solved-page control) |
| `phase56_lag6_length_rules.py` | Phase 56: four word-level rules (repair, blocks, key restart, insertion gate) against LP2's lag-6 word-length profile |
| `phase57_mechanism.py` | Phase 57: nine encryption rules (repair, T-repair, null on collision, per-word / per-rune / end nulls, F rule) scored on all LP2 anomalies at once |
| `../scripts/reproduce_signals.py` | Recomputes the numbers of docs/FINDINGS.md section 1 with PASS / FAIL (`--fast` for the unit test) |
| `phase57_pilot.py` | Phase 57: R4 planted control and one-window LP2 pilot (0.15 @ 0, n 150) of the chanscreen v2 mid-word arc |
| `phase58_djubei_reuse.py` | Phase 58: equal 6-runs at key distance 5,700-6,500 in every library stream (DJU BEI as reused key), shuffle null, planted control |
| `phase59_keywords_r4.py` | Phase 59: 1,940 solved-text keywords (and phi(prime)) as periodic keys through the R4 mid-word arc on all 48 n300 LP2 windows, R4 keyword plants as control |
| `clue_extra_rune.py` | Phase 60: is the extra rune of LP2's words a simple function of the other runes, the previous word, the word index or length? 45 tests, shuffle null, planted controls, solved-ciphertext control, prime-length check |
| `phase60_art_blobs.py` | Phase 60: ink-blob boxes of the page art, the five contact sheets in `phase60/`, and the cross-versus-glyph sheet |
| `phase60_t2_numkeys.py` | Phase 60 T2 and T4-under-R4: Cicada's number strings, the 256-byte onion strings and the Cicada OS file folly as short keys through the phase 59 R4 engine (`P60_SET=t2|hex256|folly`) |
| `phase60_t3_lp1key.py` | Phase 60 T3: the solved LP1 plaintext (forwards, reversed, read twice round) as a table-invariant running key, stage 1 of the book-key rule, plant control |
| `phase60_t6_blobs_r4.py` | Phase 60 T6: the megabyte Cicada OS files under R4, every offset of one window, chunked, with R4 plants as control |
| `phase60_t7_xor.py`, `phase60_t7b_xor_classes.py` | Phase 60 T7: XOR-domain keys (three exact conventions): the abandoned unigram lag DP (control only) and the key-class coincidence screen run on the library, number / onion strings and the megabyte files |
| `phase60_t8_r4.py`, `phase60_t8_xor.py`, `phase60_t8_mp3.py` | Phase 60 T8: DATA/560.13 under R4 (start region and sampled blocks) and under the XOR screen; MP3 frame-payload stripper for the audio streams |
| `phase61_unrepair.py` | Phase 61: lag-6 detector D on the R4 simulator (precision / recall), un-repair and guided (hard / R4-aware) decoding on plants with the mid engine and an exact Python decoder |
| `phase62_shared_keys.py` | Phase 62: shared keys between LP2 section pairs (same / sign-flipped / reversed), FFT chi2 over all offsets, max-statistic null, plants under plain / R4 / drifting-R4 keys |
| `phase63_change_points.py` | Phase 63: change-point search (0-2) on per-page doublet / lag-6 / word-length series, permutation and R4 nulls, spliced-q control, one-R4-setting test of the 0.53% vs 0.77% doublet rates |
| `phase64_clause_structure.py` | Phase 64: clause statistics of LP1 vs LP2 (permutation), against ordinary English in runes (two punctuation schemes), length parity / moduli |
| `phase65_prime_clause_score.py` | Phase 65: prime-sum share of clause units (LP1 calibration, LP2 power, rescoring of recorded decodes), clause-final word check |
| `mech48/` | Phase 48: the A/I oracle (one-rune words -> A or I): calibration, re-scoring of kept hits, drift-aware screen design |
| `phpmt/` | Rust: bit-exact seed sweeps for ten generators; `bg.py` boundary-free bigram score, `gpu.py` + `.cu` CUDA ports |
| `walk/` | Rust: word-scoped solver and key-free D-search (`dsearch`) |
| `prngx/` | More generators, the OEIS lane (199,088 sequences), KDF streams |
| `mech25/` | Phase 25: simulated word-aware collision-repair mechanisms (M0-M7) against LP2's doublet deficit, lag-5/6 echoes and word lengths (`results/analysis/mech25.txt`) |
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
| `blake_second_chance.py` | Reproduces the 2012 Blake "second chance" book code (22/22, plate 4 of MHH, plate line breaks) with a re-wrap control |
| `book_key_screen.py` | Phase 23 LP2 screen of the cited books with the table-free beam decoder (stage 1, frozen rule; run by the `booknight` queue) |
| `phase54_lag6_dissect.py` | Phase 54: where the within-word lag-6 relation lives (word length/position, rune, neighbours, section, solved-page control) |
| `phase53_nested_marks.py` | Phase 53: do LP2's marks form open/close pairs for a nested key stack? (shuffle null; no) |
| `discord_cumulative_check.py` | Checks two Discord cipher proposals (2026-10-22) against LP2: structural doublet test and a prime-offset scan with control and null |
| `fetch_uncovering_wiki.py` | Downloads the Uncovering Cicada wiki (129 articles, image list) through its MediaWiki API into the git-ignored `ref/uncovering_cicada/`; images not fetched (the CDN refuses non-browser clients) |
| `iso_extract.py` | Copies one file out of an ISO 9660 image as raw bytes (used for `DATA/560.13` of the 2013 Cicada OS ISO; nothing mounted or run) |
| `zipf_check.py` | Word-frequency (Zipf) checks: repeated ciphertext words by length and the one-rune words, against shuffled / random nulls |
| `book_key_pairs.py` | The same through lag-2..8 rune-pair counts, with a table tuned to flatten the pairs (`results/analysis/book_key_pairs.txt`) |
| `book_key_decoder.py` | Table-invariant, drift-tracking decoder for a candidate book key (table-free beam + exact skip-rule Viterbi EM) and its gate: plants with a flattening table, nulls, power and cost (`results/analysis/book_key_decoder.txt`); no LP2 run |
| `grid30_caption.py` | Phase 27: the page-30 caption against a preregistered family of the solved pages' rules and the grid's numbers (`count`, `run`; `results/grid30_caption/`) |
| `phase26_464_table.py`, `phase26_464_followup.py`, `phase26_clause_tail.py`, `phase26_words.py` | Phase 26: audit of the community "464-word table" (R calibration, selection nulls, removal checks, 928-word carrier pairing test) |
| `phase28_square_seeds.py` | Phase 28: preregistered recipe family for the 0.2 / 0.6 magic-square seeds, calibrated on random target sets |
| `phase31_book_codes.py` | Phase 31: preregistered book-code readings of the book's numbers in four local books, trigram score against random pointer sets |
| `book_key_verify.py`, `book_key_summary_fixed.py` | Phase 23 stage 2: whole-section verification of a book-key screen hit (gate: 13/16 plants, 0/32 nulls); sentinel-safe re-reader of the screen summary |
| `h2_drift_decoder.py` | Phase 32: drift-aware tableau (H2) statistic, a beam over the key pointer; gate only, power too low for a campaign |
| `phase34_clause_ioc.py` | Phase 34: within-clause IoC of LP2 against a shuffle null (a key constant over each clause) |
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
