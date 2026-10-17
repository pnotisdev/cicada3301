# Phase 9: results of the 2026-10-17 overnight queue (desktop)

Two lanes ran from 00:36: a GPU lane (kscreen restarts / recurrences / multipliers, then the seed sweeps) and a CPU lane
(rescreen, dsearch, payload). Verdicts per campaign are in `results/overnight/desktop/REPORT.md`; this file records the
reading of each result, including checks the campaign rules do not cover. Nothing here is a solution.

## kscreen-restarts: heading windows

The campaign's decision rule (IoC >= 1.40 over the first 300 runes, whole-window verification, a keystream-matched
null of 20 offsets) was calibrated for windows of 300 runes. Two heading windows are shorter (91 and 121 runes), and for
a window that short the maximum over ~4 x 10^8 decodes is a heavy-tailed extreme value that chance puts above 1.4.
So a matched null **per window** was added (`null-heads`, 600 random keystreams, ~4 x 10^8 decodes), plus 24
replicates of the two short windows alone (random keystreams, seeds 100-123):

| Window (runes) | library best | null (24 replicates): min / median / max | reading |
|---|---|---|---|
| head0.13@1433 (91) | 2.118 (sha512-ctr "434", offset 19353) | 1.898 / 1.983 / 2.082 | above every replicate; Gumbel fit p ~ 0.012 for this window; not significant after the number of windows and campaigns; the best offset differs from every other window's, which a shared key restart would not allow |
| head0.14@1468 (121) | 1.722 | 1.650 / 1.726 / 1.865 | equals the null median: nothing |
| the 7 windows of >= 308 runes | 1.26-1.33 | 1.29-1.33 (one null replicate) | no difference from the null |

## Notes on what else was looked at overnight (no cryptanalytic result)

- **Review of the other AI's branch `research/restart-columns`** (merged, tests rewritten): no key restart at any unit
  type; a word-unit bug (wrapped words split) fixed; the line-start anomaly is a layout effect of glyph widths.
- **Section statistics** (`work/segment_stats.py`): all eight unsolved sections show the same doublet deficit (z -4 to -9),
  flat IoC (0.99-1.00) and the same word-length shape, so one mechanism produces the fingerprint in every section.
- **Within-word coincidences** (`work/within_word.py`): distance 1 is the anti-repeat effect (0.63%, -15.5 sigma);
  distance 5 is +3.7 sigma pooled (p ~ 0.002 after looking at 9 distances), with 4 (+2.0) and 7 (+1.1) leaning the same
  way and 6 low (-2.0); it is not concentrated at one word length or position. Weak.
- **Page art** (`work/ornament_dots.py`, `work/log/phase9_art.md`): the border art is exactly mirror-symmetric; the
  five-dot figure (pages 24, 40, 73) is one rigid shape, mirrored or rotated; the three-dot rows (pages 50, 56) are one
  shape at two scales; pages 50-56 carry a six-sign cuneiform-style cluster at the top.
- **Separator layer verified** (`work/separator_audit.py`, `phase9_separators.md`): 9,828 gaps, no missing and no extra
  word separators; the only differences are the tick glyph (4 lone apostrophe ticks, quote ticks) that the transcription
  lacks. Random separator loss cannot explain the word-length deficit (`work/seploss.py`).
- **Research round 2** (`work/log/research_2026-10-17.md`): no public solve, nothing new from Cicada; community work uses the same
  transcription lineage; the chain/step-domain family (flat step stream, no period) has been looked at by aldegonde and
  Zhang only structurally (period, IoC, DFT), not with keystream screens, which `kscreen-chain` now does; the cuneiform
  cluster on images 50-56 reads as base-60 numerals 17,13 / 55,1 = 1033 and 3301 (agent's reading, unchecked by a specialist).

## Second pass (2026-10-17, early morning)

- **Per-window extreme-value null for the page windows** (`work/kscreen/short_window_null.py`, 12 replicates each,
  `results/analysis/short_window_null_pages.txt`): the six page windows shorter than 250 runes that the library screen
  flagged have Gumbel p of 0.19-0.85 (library best 1.40-1.68 against null maxima up to 1.75). All are chance.
- **Backward keys** (`dir=back` in the Rust and CUDA screens): planted backward keys are recovered at the exact key
  index in both engines; the campaign `kscreen-reverse` runs the 29 chain transforms on reversed windows.
- **Branch `research/word-internal-lag5`** (merged, tests rewritten, see `docs/prs/word-internal.md`): the lag-5 repeated
  bigram excess (9 against 1.51) replicates with independent code (`work/lag5_check.py`): permutation P < 1.1e-4 after
  the look-elsewhere over lags 2-8, conditional on the coincidences P = 4e-4 to 5e-3. It is concentrated in 10-rune
  words (lag 5 = half the word: 21 coincidences against 8.8 expected, +4.2 sigma; no other even length does that).
  Mechanism unknown: a per-word key of period 5 is excluded by the dictionary test and by the flat lag-5 difference
  histogram; a per-rune copy process does not give the clustering.
- **Branch `research/wordlen-languages`** (merged, review in `docs/prs/wordlen-languages.md`): the Emerson-based rows
  reproduce exactly (TH spelled as T+H takes G from 223 to 56; fewer 2-rune words fits at p = 0.07). The other-corpus
  table was not reproduced (needs the Gutenberg download). The repository's dictionaries already index every spelling of a
  word (`attack.rune_spellings`), so the screens are not blind to TH as two letters.

## GPU lane results (2026-10-17, 00:36-04:35, all negative)

- **kscreen-restarts, kscreen-recurrences, kscreen-multipliers:** best IoC 1.40 or below in every screen except none above the 1.40 rule that survived
  its whole-window verification (0 of 8 / 8 / 10 / 15 re-decoded hits keep IoC >= 1.4 or beat their own random offsets). Order-3 recurrences
  (9.2e9 decodes) peaked at 1.368 and the library x 28 multipliers (5.7e9 decodes) at 1.381; with this many decodes the chance maximum
  is higher than the single "matched null" of the report (1.318, far fewer decodes), which is why the verification step decides.
- **prng-all** (a fresh seed per section, all 8 sections, all 2^32 seeds of PHP < 7.1 mt_rand, glibc random() and 2^31 of .NET Random):
  best screen score 21 for all three (random-seed maximum per the score histogram); the 20 best candidates of each re-decode over the whole
  segment to 0.08-0.11 against 0.075-0.078 for random seeds (z +0.9 to +5.5, selection bias), where a true key scores about 0.8.
  php: 2,628 s, glibc 2,451 s, .NET 1,206 s on the 2080 Ti.
