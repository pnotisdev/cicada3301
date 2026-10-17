# PR: LLR restart test, the limit of two-text alignment, red headings under all affine maps

**Branch:** `research/restart-llr` (new files; builds on the merged `restart_columns.py`)

## What this adds
- `work/restart_llr.py` -> `results/analysis/restart_llr.txt`: the key-restart column test with the full plaintext-
  difference log-likelihood ratio, T_j = sum over pairs w(c_u - c_v), w(d) = log(29 Q(d)) with Q(d) = sum_x f(x) f(x-d)
  (English rune frequencies). The equal-pair count of `restart_columns.py` uses only the d = 0 bin; the LLR uses all of
  Q (KL(Q || uniform) = 0.0235 nats per pair, 2.6x the 0.0091 of the equality indicator). Null: Monte Carlo draws from
  LP2's rune distribution per column; positive control: English enciphered with one random key restarted at every
  unit under the skip rule with LP2's real unit lengths.
- `work/heading_affine.py` -> `results/analysis/heading_affine.txt`: each red heading of >= 8 runes (12 of the 17 red
  runs of `red_runs.py`: section starts and mid-section headings) under all 812 affine maps x -> m x + b (every Caesar
  shift, Atbash and every multiplier), dictionary-word score, against 60 random stretches of the same length.
- `work/tests/test_restart_llr.py` (2 tests, 12 s).

## Results
| unit | n | LP2 Z_sum (start / end) | restart control Z_sum (mean / min) | continuous-key null, max |Z_sum| |
|---|---|---|---|---|
| paragraph | 60 | +1.1 / -0.7 | 27.7 / 20.2 | 1.5 |
| page | 57 | +1.1 / -0.7 | 23.9 / 17.9 | 1.8 |
| sentence | 212 | +0.9 / -1.6 | 83.0 / 69.2 | 2.9 |
| **section** | **9** | +1.0 / +0.4 | **2.7 / 0.7** (start), 3.8 / 2.0 (end) | 2.0 |

- **No key restart at paragraphs, pages or sentences** (LP2 is 20x below the control). Lines and words were done with
  equal-pair counting (`restart_columns.py`: controls 170 and 240).
- **A restart at the 9 section starts cannot be tested**: with 36 pairs per column and the key drifting by ~0.03 per
  rune, the control gives only Z_sum = 2.7 (min 0.7). The earlier "no key reuse between segments" came from lag scans
  that lose the same signal to drift; it should be read as "not excluded" for restarts, and the segment-level evidence
  against a shared key is the flat lag spectrum only.
- **Why two texts cannot be aligned further than the first ~30 runes** (a dead end worth recording; the DP I wrote is not
  included because it cannot work): aligning two ciphertexts that share a key under the skip rule needs the skip
  positions of both texts. The information per aligned pair is KL(Q||U) = 0.0235 nats; the uncertainty of the alignment
  path is H(s) = 0.128 nats per rune per text at s = 0.028, i.e. 0.255 for a pair. A banded dynamic program (gap cost
  log(s/(1-s)) = -3.5 per skip) therefore scored 0.9 nats on a perfectly shared 700-rune pair (z = -0.5). Only the first
  ~30 columns (small drift) carry usable signal, which is what the column tests use.
- **Red headings are not an affine cipher of English**: no heading stands out from the best-of-812 null (z -1.5 ..
  +2.4; the best, page 22, equals the null's maximum 0.46 vs 0.47). Short strings are very noisy (a random 9-16 rune
  stretch reaches 0.4-0.8 under some map), so only a clean dictionary hit would have counted.

## For the reviewer
- Check `stat_T`/`column_z` (Monte Carlo null per column from the pooled rune distribution) and that the controls use
  the same unit lengths as LP2.
- Open: a restart test for the 9 sections that uses the first ~30 columns of every pair with the forward algorithm over
  the skip path (the optimal statistic); my estimate is that it cannot beat Z ~ 4 for English plaintext.
