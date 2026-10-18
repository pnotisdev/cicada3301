# Phase 16: what a negative H5 flat-library sweep could and could not exclude (2026-10-19)

Scope: a synthetic power map; LP2 is not searched. **Nothing in LP2 is solved.** Code: `work/h5power/h5power.py` (independent planter, harness around the REAL `h5rs sweep` path, 3 tests).
Trigger: GPT's D2 gate (`work/independent/frontier/gates/d2/`) recovered only 1 of 4 canonical unknown-keyword controls (all 8 keyword-known controls passed; the L = 20 plant aborted at the init),
and the retained c1500 plant still aborts. Question: how likely is the planned campaign (`work/h5rs/CAMPAIGN.md`) to flag a true stream + keyword layer at all?

## Method

6,000 plants (10 keyword lengths L = 2..20 x 2 anti-repeat models x iid or flat-library slices x solved Cicada text or Emerson, 150 per cell of L x model x kind; 300 runes, keyword uniform, keep 0.19, key pointer advancing as
in the repository's skip / coin conventions, true offset uniform in 0..1999). Each plant is searched with the campaign's engine settings (fast, campaign abort) over the TRUE offset +-1, all L = 2..20 and both models
(restricting the offsets does not change a cell's score; it only drops other offsets' chance cells, which the campaign null covers). Recovered at X = the true cell (offset, L, either model) has IoC >= X: 1.6 is the campaign's fixed
floor; 1.8 is about its campaign-size floor (1.77 / 1.83 on seg0.8, `work/h5rs/CAMPAIGN.md`). Output: `results/analysis/h5_power_map.txt` and `.json` (per-plant records).

## Result

| L | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 13 | 16 | 20 |
|---|---|---|---|---|---|---|---|---|---|---|
| recall at >= 1.6 | 84% | 75% | 67% | 63% | 57% | 41% | 32% | 19% | 14% | 7% |
| recall at >= 1.8 | 48% | 43% | 41% | 40% | 39% | 27% | 23% | 13% | 8% | 4% |

* By model: skip 58% (>= 1.6) / 36% (>= 1.8); coin 34% / 21%. At L = 13 skip 29%, coin 9%; at L = 20 skip 12%, coin 3% (>= 1.6).
* No dependence on the true offset (43.6-48.4% over five 400-offset bands) and none on iid versus library keys (46%): the c1500 miss is not a systematic deep-offset failure at the pooled level.
* Among recovered plants the true-cell IoC has median about 1.8-1.85 (quartiles 1.76-1.89 at L = 2). My reading: the plaintext's own IoC at 300 runes is about 1.8 +- 0.1, so a floor of 1.77-1.83 rejects roughly 40-50% of even
  perfectly decoded windows; the recall loss at L = 2 between 1.6 and 1.8 is sampling of the plaintext IoC, not decoder failure. DeepSeek's plants (IoC 1.85-1.99 at the true cell) sit at the favourable end of this range.
* Consistent with GPT's D2: the L = 20 plant fails at the init abort and the L = 13 skip plant reaches IoC 1.807 at the true cell.

## What it means

* **A negative sweep excludes little.** With a floor near 1.8 the overall recall is 28%; at L = 13 it is about 13%, at L >= 16 under 10%. The sweep is a lottery ticket for short keywords with a skip repeat, not a test that can close H5.
* The engine hard-codes a 300-rune window (`work/h5rs/src/main.rs` truncates to 300). Longer windows (every section but 0.10 has more than 600 runes) would raise recall and lower the null maximum; that needs engine work and a new parity gate.
* Design consequence, `jobs/queues/night2.txt`: flat library L = 2..13 only (L >= 14 costs 37% of the time for under 14% recall), the 858 streams excluded by the standalone flat-IoC filter at L = 2..8 (a keyword can flatten them;
  GPT's D2 algebra), one matched null at the real size (581 streams, L 2..13) for the floors, layer2 last.

## Limits

My plants only: uniform random keywords (a real keyword such as DIVINITY is not uniform), no literal F, solved Cicada text and Emerson as plaintext, skip / coin only; window 300; the engine's tie-flips and the init beam are part of what is measured.
Per-window floors other than seg0.8 are unmeasured (the null sweep in the queue measures them). 95% Wilson intervals are in the result file (about +-4 points per L).
