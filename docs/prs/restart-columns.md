# PR: key-restart column test, line-layout explanation, repeat spectrum

**Branch:** `research/restart-columns` (new files only; no edits to existing code)

## What this adds
- `work/restart_columns.py`: tests the hypothesis that the key (or its PRNG seed) restarts at the start (or end,
  for a backward key) of every page, paragraph, line, sentence, word or segment. If it does, the j-th rune of every
  unit sits in a column enciphered with the same key value, and English plaintext makes equal pairs in a column
  ~1.8x as common as chance. Exact multinomial variance, so z-scores are calibrated. Positive control: English
  enciphered with a shared restarting key under the skip rule, using LP2's real unit lengths.
- `work/line_layout.py`: explains the one anomaly the test finds.
- `work/repeat_spectrum.py`: repeated k-grams against shuffles.
- `work/tests/test_restart_columns.py` (2 tests, 2 s).
- Outputs in `results/analysis/`.

## Results
- **No key restart at any unit.** LP2 Z_sum (first 20 columns) is -1.1 .. +2.1 for every unit type and direction;
  the planted-restart controls give 17-19 (pages, paragraphs), 60 (sentences), 170 (lines), 236 (words). Only 9
  segments exist, so the segment test is weak (control Z_sum ~2.5); the lag scans cover that case.
- **One anomaly, explained.** Line-initial runes are non-uniform (chi2 78.7 on 28 df; z = +6.7 in column 0; random
  cut points reach at most 4.8 in 2000 tries). Lines hold 17-26 runes, so they are set to a fixed *width*. Fitted
  glyph widths (from line compositions alone) correlate +0.74 with the line-initial enrichment (permutation
  p < 5e-5; EA widest and most enriched, I narrowest and most depleted) and cut chi2 from 78.7 to 36.6 in sample.
  Out of sample (fit on one half of the segments, test on the other) the drop is 39.6 -> 33.3 and 84.9 -> 50.9, so
  part of it is left unexplained; measuring real glyph widths from the page images would settle it. It carries no
  key information (columns 1-59 of the same units are flat).
- **Repeats.** The repeated 6-gram DJU-BEI is what chance gives: expected 0.18 repeated 6-grams in 12,956 random
  runes (P(>=1) = 0.16). No 7+-rune repeat exists. 3-gram repeats are +2.5 sigma high (3580 vs 3436 +- 57,
  p = 0.01), not investigated.

## For the reviewer
- Check the variance formula in `column_stats` and that `simulate_units` implements the skip rule the same way as
  `attack.encrypt_tokens`.
- Open question: measure glyph widths from `work/orig/` to finish the layout explanation.
- No existing file is modified, so this merges cleanly next to the desktop's logging/CUDA work.

## Review (stronger-model pass, 2026-10-17)

Merged locally; nothing in the branch was run before the review. Findings and changes:
- **Variance formula checked.** `column_stats` is the exact multinomial variance of the equal-pair count
  (`n(n-1)(n-2)(T-S^2)` is the covariance of pairs sharing one rune, counted for unordered pairs of pairs). The new
  test draws iid columns from a lumpy distribution (n = 40 and 300, 2,500 trials each) and requires z with mean 0
  +- 0.08 and sd 1 +- 0.07.
- **Bug fixed: word units.** `units_of("word")` split at every `
`, but a bare line break inside a word is a
  typographic wrap (the same bug `lp.word_spans` was fixed for). It made 3,316 fragments instead of the 2,928
  words. Now the units equal `lp.word_spans` (tested per segment). Result of the word rows: still no restart
  (start max z 1.46, Z_sum -1.5; end max z 3.09, Z_sum -0.5; planted restart: Z_sum 237). All other rows are unchanged.
- **Skip rule in the control** matches `attack.encrypt_tokens` (a collision is re-rolled with probability q = 0.82
  and the key pointer advances on every draw); the control also resets the previous-rune memory at a unit start,
  which the real text does not (one rune in 20+ per unit, negligible for this test).
- **Tests rewritten** (6 tests, 3 s): calibration of z, every unit kind partitions the 12,956 runes, words equal
  `lp.word_spans`, unit counts nest, a planted forward restart is found by the forward reading, a planted backward
  restart only by the backward reading, and a continuous key stays under max z 4.5 and |Z_sum| 3.5.
- **Limits that remain.** The test sees only restarts to the SAME key start; a restart at a unit-specific offset
  would look like a continuous key (the drift-aware pairwise scans cover shared-key reuse). The 9-segment test is
  weak. The line-start explanation (glyph widths) is fitted from line compositions only; measured widths from
  `work/orig/` would settle the 51-versus-flat leftover.
