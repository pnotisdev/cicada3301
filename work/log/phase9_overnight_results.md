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

- **kscreen-restarts, kscreen-recurrences, kscreen-multipliers:** no screen reached the 1.40 threshold (best 1.37-1.38), and no hit survived the whole-window
  verification (0 of 8 / 8 / 10 / 15 re-decoded hits keep IoC >= 1.4 and beat their own random offsets). Order-3 recurrences
  (9.2e9 decodes) peaked at 1.368 and the library x 28 multipliers (5.7e9 decodes) at 1.381; with this many decodes the chance maximum
  is higher than the single "matched null" of the report (1.318, far fewer decodes), which is why the verification step decides.
- **prng-all** (a fresh seed per section, all 8 sections, all 2^32 seeds of PHP < 7.1 mt_rand, glibc random() and 2^31 of .NET Random):
  best screen score 21 for all three (random-seed maximum per the score histogram); the 20 best candidates of each re-decode over the whole
  segment to 0.08-0.11 against 0.075-0.078 for random seeds (z +0.9 to +5.5, selection bias), where a true key scores about 0.8.
  php: 2,628 s, glibc 2,451 s, .NET 1,206 s on the 2080 Ti.

## A bug found at 05:00: stream names with control characters broke `verify.py` (fixed, chain restarted)

`kscreen-chain/a7-verify` failed with `KeyError: 'window'` and the runner stopped the campaign. Cause: eight library streams (the binary "An End" hash,
as seed of the four hash constructions x two mappings) have names containing \x0b and \x1c, which `str.splitlines()` treats as line ends, so a TSV
row was cut in two. It only bites when such a stream is among the top hits (here at IoC 1.311 in a7), so the earlier verifications were unaffected.
`verify.py`, `tsvdiff.py` and `step28.py verify` now split on "\n" only. The a7 verification then runs (0 of 10 hits keep IoC >= 1.4). The chain campaign
was restarted by hand (`run kscreen-chain --lane gpu`); the chained waiters for the later campaigns wait for the lane lock and their markers, so nothing was lost.

## CPU lane results (rescreen, dsearch, payload; finished 06:35, all negative)

- **rescreen** (dictionary screens with the corrected word segmentation): screen 1 best 0.155 is a random CONTROL stream; screen 2 has no non-control hit
  above the control maximum; reverse direction: control max 0.167 over 893 keystreams; heading restarts: 893 keystreams, control max 0.975.
- **dsearch** (per-word additive key behind any secret outer alphabet, m = 1-8, gaps {1,2} and {1,2,3}): LP2's best G sits inside the
  four surrogates' range for all 16 settings (z from -2.4 to +2.3; the extremes are what 16 tests give by chance). Positive control (synthetic m = 5): true-D G 2726,
  the search recovers 14 of 29 symbols up to an affine map.
- **payload** (256 corrected bytes): 25 candidate seeds x sha512 / sha3_512 / blake2b: 0 matches; the decryption sweep's best guess
  (AES-192-ecb with a passphrase from the book, printable fraction 0.48, first byte reads as an old-format PGP packet tag) is the kind of coincidence
  that hundreds of passphrase/cipher tries produce and not a decryption.
- **kscreen-chain** (a = 1..28, 8 sections, library / order-2 recurrences / cubic polynomials): largest IoC 1.415 (a = 17, library, section 0.11,
  'sha256-ctr mod :INSTAR', multiplier 28); continued to the end of its window it falls to 1.073 over 1,894 runes (its own random offsets: mean 1.047, max 1.056). No other
  verification passes. `kscreen-chain/a7-verify` had first failed on a control character in a stream name (see above).

## prng-more, window 0.7 (06:20-06:58; seven more generators, all 2^32 seeds, 16 variants each; all negative)

| generator | sweep time | best screen score | best candidate re-decoded over the whole segment (random seeds ~0.077) |
|---|---|---|---|
| py3 (CPython) | 425 s | 22 | 0.080 (z +0.4) |
| mt32 (std::mt19937, PHP >= 7.1) | 324 s | 22 | 0.075 (z -0.3) |
| mt31 | 330 s | 21 | 0.077 (z -0.3) |
| java | 165 s | 21 | 0.093 (z +2.5) |
| msvc | 171 s | 21 | 0.074 (z -0.5) |
| drand48 (Perl) | 171 s | 20 | 0.081 (z +0.2) |
| ruby | 421 s | 20 | 0.067 (z -1.3) |

A true key scores about 0.8. The rest of the GPU queue (kscreen-reverse, prng-more-all, kscreen-step28, prng-step) is still running.

## Backward-key campaign `kscreen-reverse` (a = 0..25 of 0..28 done when the GPU was handed back at 10:00; negative)

Library / order-2 recurrences / cubic polynomials on the sections read from the end, a = 0 (ordinary cipher, backward key) and a = 1..25 (with ciphertext
feedback): largest library IoC 1.387 (a = 8), none reaches the 1.40 rule, and all 26 whole-window verifications report 0 of 10 hits kept. a = 26 (partial), 27 and 28
are still to run (`python jobs/overnight.py run kscreen-reverse --lane gpu` resumes at a26).

## GPU hand-over at 10:00 (user request)

All project GPU jobs were stopped at 10:00 by a watchdog; no lane lock or GPU process remains. To resume, in this order of value:
1. `python jobs/overnight.py run kscreen-reverse --lane gpu` (3 more values of a, ~15 min);
2. `python jobs/overnight.py run prng-bg --lane gpu` (the boundary-free sweeps of every section with a fresh seed per section; ~2 h per generator when the GPU is free;
   window 0.7 is done for all ten generators);
3. `python jobs/overnight.py run prng-step --lane gpu` (step-domain seed sweeps, about 25 h) and `prng-more-all` (dictionary scored, see phase9_boundaries.md: low priority);
4. the CPU lane's `kscreen-hashwords` finishes by itself (about 10:20).
