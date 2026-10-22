# Phase 62: do LP2 sections share keys? (2026-10-23)

Nothing in LP2 is solved. Script `work/phase62_shared_keys.py` -> `results/analysis/phase62_shared_keys.txt`.

## 1. Plan (written before running)

- Sections: the 8 LP2 sections 0.7, 0.8, 0.9, 0.11-0.15 (segments 7, 8, 9, 11-15; segment 10 is the caption). 28 unordered pairs (the difference relation is antisymmetric, so ordered pairs add nothing).
- Model: c = p + k (mod 29). If sections A and B use the same key stream at a relative offset d, aligning c_A[i] with c_B[i+d] cancels k:
  `diff` c_A - c_B = p_A - p_B (same key, or key + constant); `sum` c_A + c_B = p_A + p_B (sign-flipped / Atbash-like key: k_B = -k_A);
  `diff-rev`, `sum-rev` the same with B read backwards (key reversed). A constant shift of the key changes only which residue is the mode, not the statistic.
- Statistic: chi2 of the 29-bin histogram of the combined series over the overlap, z = (X2 - 28) / sqrt(56) (exact null mean 28, variance 56 for flat input), overlap >= 100.
  This is the IoC up to scaling, but comparable across overlap sizes. Maximum over all offsets d and the 4 relations. All histograms for all d at once by FFT cross-correlation of one-hot indicators (exact).
- Windowed variant (drift-tolerant): A cut into blocks of 300 runes (planned 150), each matched against all of B (full-block overlap), maximum over blocks / offsets / relations.
- Positive control: two English rune texts (digraph spelling, `fam_data.english`) at LP2's section lengths under one random key, each relation, three models:
  `plain` (c = p + k); `R4-E` (R4 as phase 57: 45% of words get a null at a uniform slot, collision repair with q 0.81 writing 24 - 2c(-6), key indexed by emitted rune so nulls consume key);
  `R4-P` (same, but the key advances only with plaintext runes: nulls do not consume key, so every null shifts the alignment between sections by one: the drift model).
  Detection = max z above the 95th percentile of the global-maximum null (below).
- Null: A, B shuffled within words (keeps unigram counts and word cuts); for the real data the null of the maximum over all 28 pairs x 4 relations x offsets (and windowed) is
  built from replicates of the whole LP2 shuffled within words, so the correction for pairs, relations and offsets is in the null itself.
- Order: 0.7 vs 0.11 first, then all pairs. Below-normal priority, 1 thread, budget < 1 CPU-hour.

## 2. Results (`results/analysis/phase62_shared_keys.txt`; 1,276 CPU-s, one thread, below-normal priority; selftest: identical / negated / reversed copies found at the right relation and offset)

Changes from the plan: window blocks are 300 runes (not 150); the shuffled-LP2 null has 300 replicates for the full statistic and 100 for the windowed one; thresholds are the 95th percentile of the global maximum over 28 pairs x 4 relations x offsets
(full 7.94, windowed 8.17; 99th 8.70 / 9.31).

**LP2.** 0.7 vs 0.11 (the art link): best z 5.71 (sum, d 1154, overlap 729), 4.50 diff-rev, 3.97 diff, 3.92 sum-rev; windowed best 6.94 (diff-rev). Both are below the 95th percentile of the global null
(P over the global maximum 0.997 for the full pair value). **Every pair of the 28:** best full z 4.2-6.6 and best windowed 4.5-6.9, none above the corrected threshold. Global maxima: full 6.59 (P 0.548), windowed 6.94 (P 0.614).
Nothing to examine. No pair, relation or offset beyond the null.

**Power (positive control, English rune texts under one random key, same test and thresholds).** The difference / sum of two English rune texts is only about 5% above flat (excess chi2 about 0.05 per aligned rune), so the test needs a long overlap:
plain model, equal lengths n, detection: n 500 0.00, 1000 0.05-0.12, 1500 0.38-0.55, 2000 0.80-0.82, 3000 1.00. At LP2's actual pairs (plain model, planted): 0.7-0.11 (729 / 1894; overlap at most 729) 0.00-0.06; 0.8-0.12 0.00-0.31; 0.14-0.15 (1589 / 3316) 0.56-0.69 for diff / sum, 0 for the reversed relations
(the reversed plants need the overlap to cover the reversal, and the key offset I draw is not always inside it: reversed relations are the weakest rows). Independent keys: 0 of 48 above threshold.
**R4 with key indexed by emitted runes (R4-E)**: nulls and repairs only dilute (about 20% of aligned runes are noise): detection 0.12-0.19 at 0.14-0.15, 0 elsewhere. **R4 with key advancing only with plaintext (R4-P, the drift model)**: 0 of 13 pair rows, in both statistics
(a null every ~10 runes shifts the alignment by one, so a shared stretch lasts tens of runes, far less than the 300-rune window and less than any stretch the statistic can see).
The windowed statistic detects nothing in any plant (0-0.06): a 300-run block of an English difference carries too little signal (z about 2-3 against a threshold of 8).

**Reading.** The test has power only for the plain model with long overlaps (>= 2,000 aligned runes; in LP2 only pairs involving 0.15, 0.11, 0.9 reach that, and then only partly), so the clean result is: **no evidence of a shared key under the plain
model for the pairs where it has power; the 0.7-0.11 pair, the main target, has power 0.00-0.06 even in the plain model (729 runes), so it is not tested.** Under R4-P (the model that matches phase 9's skip drift) the test has no power at all: key reuse under drift remains untestable by a difference statistic, as phase 9 found.

## 3. What is NOT excluded

Shared keys for the short pairs (anything involving 0.7, 0.8, 0.12); any key reuse under drift (R4-P); reuse at a multiplied or affine-transformed key (only shift, Atbash-sign and reversal were tried); a key shared with a non-constant relation; reuse of only a fragment (shorter than about 1,500 aligned runes);
within-section key repeats. A likelihood statistic with the known English difference distribution (no constant shift) was not tried; it would raise power only if the key relation has no constant shift.
Level: the null is the within-word shuffle of LP2 (keeps counts and word cuts, destroys any cross-section structure); the plants are simulations of stated models, not evidence about Cicada's method.
