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

## `kscreen-hashwords` (CPU lane, 10:18; negative)

12,944 hash streams (sha256 / sha512 / md5 counter and sha256 chain, mod 29 and rejection, upper and lower case) of every word and two-word phrase of the solved text
at every offset on the 8 sections: 8.1e9 decodes in 108 minutes; best IoC 1.371 (seg 0.13, 'sha512-ctr reject :MESSAGE CONTAINED'), against 1.364 for 12,944 random streams under the
same settings; 0 of 15 re-decoded hits keep IoC >= 1.4 over their whole window (the best one falls to 1.078 over 1,524 runes, its own random offsets average 1.050).

## Boundary-free rescoring of the laptop's hashscan lane (CPU, 10:27-10:40; negative)

`work/hashscan` mode `bgsweep` (decoder `decode_bg`, the Rust port of `work/phpmt/bg.py::ref_decode`): 19.2 M candidate passphrases x 4 hashes x 4 stream conventions x 3 byte maps x 8 cipher variants,
window = first 120 runes of section 0.7. No decode passes the 40-rune gate; best recorded score 54-59 per tier (lore 54, words 58, dates 59, pairs 59, numbers 59); whole-section decodes of the 10 best per tier
score -9.3 to -10.8 per rune against -10.2 to -10.9 for random strings. Files: `results/hashscan/bg_*.tsv|log`, `bg_*_verify.txt`. This replaces the dictionary-scored negative of the laptop for these lists.

## `kscreen-reverse` completed: a = 26..28 on the GPU (13:01-13:16, 15 minutes; negative)

Resumed when the user offered the GPU for jobs under 30 minutes (`python jobs/overnight.py run kscreen-reverse --lane gpu`; the runner estimated 0.4 h, the GPU run took 15 minutes). The controls
step passed first (`CHAIN SELFTEST PASSED`: planted keys recovered, random nulls below 1.4, e.g. a = 7 1.278, a = 28 1.306). Best IoC per step (409 M decodes for the library, matched null of 1,300 random streams):

| a | library | null | order-2 recurrences | cubic polynomials | whole-window verification |
|---|---|---|---|---|---|
| 26 | 1.3391 | 1.3191 | 1.2777 | 1.2544 | 0 of 10 hits kept |
| 27 | 1.3223 | 1.3585 | 1.3016 | 1.2447 | 0 of 10 hits kept |
| 28 | 1.3430 | 1.3320 | 1.3061 | 1.2628 | 0 of 10 hits kept |

With a = 0..25 (above) the campaign is complete (146 of 146 steps): over all 29 values of a, with and without ciphertext feedback, both signs and both anti-repeat models, the key read backward through the
sections gives a largest library IoC of 1.387 (a = 8), none reaches the 1.40 rule, and no whole-window verification keeps a hit. The backward-key family is closed negative for the library, the order-2
recurrences and the cubic polynomials. Files: `results/kscreen/chain/rev_*_a26..28*`, `results/overnight/desktop/logs/kscreen-reverse__a2[678]-*.log`.

A second session ('Advanced hypotheses') was running its own CPU campaign `kscreen-hyp` (lane `hyp`) in the same checkout during this run; its files were not touched or committed here.

## Time-seed and small-integer seed sweeps of every section (GPU, 13:30-13:56; negative)

The user offered the GPU for 30 minutes. The full boundary-free sweep of all section windows costs about 1.7 hours per generator (2^32 seeds, 8 windows, about 0.7 M seeds/s), so a PRIORITISED seed
range was swept instead (`python work/phpmt/bg.py sweep <gen> all <lo> <hi> <out.tsv>`, windows = the 8 section windows 0.7-0.15 without the 9-rune 0.10, a fresh seed per window; the engine gate
`work.tests.test_bgmt` passed first, `results/prng/bgtime_selftest.txt`):

- **Epoch-time seeds** 1,293,840,000 .. 1,420,070,400 (2011-01-01 to 2015-01-01 UTC, 126,230,400 seeds): php 117 s, glibc 103 s, py3 103 s, mt32 100 s, mt31 101 s, msvc 110 s, drand48 109 s, ruby 106 s.
  Java (64-bit millisecond seeds) and .NET (tick-count seeds) do not fit a 32-bit time range and were not swept.
- **Small-integer seeds** 0 .. 2^27 (134,217,728 seeds; dates such as 20131231 or 31122013, round numbers, 3301 and friends): php 117 s, glibc 119 s, py3 114 s; mt32, mt31, msvc, drand48 and ruby were not
  reached (deadline).
- **Result:** 0 candidates at or above the +300 gate in every sweep, so there was nothing to verify (`*_verify.txt`: 'no candidate reached the sweep's floor'). Files: `results/prng/bgtime_<gen>_all.*`,
  `bgsmall_<gen>_all.*`.
- **Scope.** This tests only these seed ranges on sections 0.8-0.15 (0.7 was swept over all seeds before); a miss does not exclude other seeds, other generators, or an additive stream with any other
  source. The remaining GPU work is the full all-section ranges (`prng-bg`, about 1.7 h per generator), `prng-step` (about 25 h) and `prng-more-all`.

## Boundary-free OEIS lane (CPU, 10:39-13:52; negative)

199,088 OEIS sequences (mod 29) as keystreams, 28 multipliers, both signs, skip and coin models, 36-rune windows (`prngx bgsweep seq`): sections with all 128 offsets (8 windows) and pages + heads with
offsets 0-15 (55 windows), each with a matched null of random sequences of the same lengths. Best scores (gate +300): sections real 181, null 192; pages + heads real 246, null 230. Decoding the top rows
with the Python reference (`work/prngx/oeis_bg_verify.py`, `results/prngx/bg_oeis_verify.txt`; it reproduces the sweep's scores exactly) shows no English: the real best (A255575, offset 5, x14,
'EHTSUGTHOFIANDILENT...') and the null best ('NMEGHISATBLIPLTR...') are equally unreadable at about +6 per rune, which is what the skip / coin beam makes of a random sequence over 25.5 million seeds and
55 windows (random sequences at the same settings score -430 +- 100). The OEIS lane is closed as noise; the control of the lane is `work/prngx/oeis_bg_control.py` (planted primes found at rank 1). **Correction (2026-10-17, 23:30, `phase10_deepseek_round3.md`):** a true key scores +7.3 per rune on Cicada's text, so a 36-rune window passes the +300 gate in only about 29% of cases; the lane's negative is weak to partial, not closed.

## KDF lane (CPU, 13:52-14:05; negative)

The laptop's passphrase library (23,976 candidates from `work/hashscan/data/lore.txt`) through RC4 / RC4-drop768, AES-128/256-CTR, ChaCha20, PBKDF2 (SHA-1/256/512, 1 / 1000 / 4096 iterations) and scrypt, two
byte maps: 719,280 key streams, swept on the first 120 runes of section 0.7 (offset 0, 28 multipliers, both signs, Atbash, both anti-repeat models; `prngx bgsweep seq`): 92,067,840 settings in 105 s, best score 58
(the most a decode keeps when it stops at the 40-rune gate; gate +300). Whole-section check of the best 10: -8.85 to -10.19 per rune against -10.4 to -11.0 for random strings through the same stream. Files:
`results/prngx/bg_kdf.*`, `bg_kdf_verify.txt`.

