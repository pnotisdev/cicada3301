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
