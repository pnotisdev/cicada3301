# Phase 63: where does LP2's machine change settings? (2026-10-23)

Nothing in LP2 is solved. Script `work/phase63_change_points.py` -> `results/analysis/phase63_change_points.txt`.

## 1. Plan (written before running)

- Units: LP2's pages in book order (a page break is a '%' token; every section start also starts a unit; the 9-rune caption is one unit). A rune pair is attributed to the page of its second rune, a word to the page of its first rune.
- Series per page: (a) in-word doublets / in-word adjacent pairs; (b) across-gap doublets / across-gap pairs; (c) lag-6 hits c_i = 24 - 2c_(i-6) within words, against the page's own expectation (sites x sum_a f_a f_T(a), f = the page's rune frequencies: the shuffle expectation of phase 54);
  (d) word length (mean runes per word; an extra rune in a share f of words raises the mean by about f, so this is the word-length-excess proxy; a Gaussian series with the pooled word-length variance. The phase 57 histogram fit per page has too few words per page).
- Change-point test: Poisson (a-c, rate relative to the exposure) or Gaussian (d) maximum likelihood with 0, 1 or 2 change points over the page order, exact over all positions. Statistics L1 = 2(LL1 - LL0), L2 = 2(LL2 - LL0); BIC choice with penalty 2 ln U per change point.
- Null 1: the units (counts with their exposures) permuted in page order, 2,000 permutations (the search over positions is inside the statistic). Null 2: 500 R4 simulations (planned 200) with ONE fixed setting (phase 57's simulator, q 0.81, checked word null, rate 0.448) at LP2's section layout, the same per-page measurement
  and statistics (page boundaries by rune index). The smallest P over the four series and both change-point counts is calibrated against the permutation null.
- Specific question: one R4 setting for 0.53% doublets in 0.7, 0.8, 0.9, 0.11 (with the caption) and 0.77% in 0.12-0.15: P = share of R4 replicates whose difference of the two group rates is at least LP2's (two-sided around the R4 mean), the same for the lag-6 ratio; equivalent q from rate ~ (1 - q).
- A significant change point is listed against sections and art (`work/book_map.py`). Below-normal priority, 1 thread, < 30 CPU-minutes.

## 2. Results (`results/analysis/phase63_change_points.txt`; 44 CPU-s; 57 pages; 2,000 page-order permutations, 500 R4 simulations at q 0.81)

Per segment (in-word doublet rate %): 0.7 0.35, 0.8 0.45, 0.9 0.52, 0.11 0.69, 0.12 1.13, 0.13 0.68, 0.14 0.65, 0.15 0.58 (counts of 2-15 per segment: very noisy); lag-6 hits / expected 1.4-2.3 everywhere (LP2 total about 1.8, the known excess, no trend); mean word length 4.35-4.61 (0.7 longest 4.61, 0.11 and 0.13 shortest 4.35-4.37).

**Change points: none significant.** 1 / 2 change points, P against the page-order permutations / the R4 simulations: in-word doublets L1 3.81 (page 20) P 0.64 / 0.52, L2 10.6 P 0.46 / 0.34; across-gap doublets L1 3.19 P 0.64 / 0.69, L2 12.6 (pages 11, 25) P 0.080 / 0.138;
lag-6 L1 4.39 P 0.34 / 0.40, L2 6.9 P 0.79 / 0.80; word length L1 2.24 P 0.85 / 0.93, L2 7.4 P 0.75 / 0.92. Smallest P over the 4 series x 2 counts: 0.080, which is exceeded by the minimum in 41% of permutation replicates once the search over series is counted. BIC picks 0 change points for lag-6 and word length (the 1 and 2 picks for the doublet series have no calibrated support).
So no change point to list against the section and art boundaries.

**Power of this test (positive control).** Splicing R4 simulations with q 0.83 up to 0.11 and q 0.75 from 0.12 (the equivalent q of LP2's two groups): the in-word doublet L1 exceeds the R4-null 95th percentile in 0.14 of 100 splices and locates the splice within 3 pages in 0.28. A free change-point search cannot see a doublet shift of this size at LP2's counts (about 12 doublets per segment).

**One R4 setting for both rates?** Group A (0.7, 0.8, 0.9, caption, 0.11) 0.527%, group B (0.12-0.15) 0.766% (all doublets / all adjacent pairs; B - A = +0.238 points). R4 at q 0.81, 500 simulations: A 0.582% (sd 0.101), B 0.595% (sd 0.088), B - A mean +0.012, sd 0.138.
P(B - A at least LP2's) = 0.052 one-sided, 0.106 two-sided around the R4 mean: one fixed setting explains the two rates (a 1.7 sd difference, not significant, and the split was chosen after seeing the data, so it is not independent of the observation). Equivalent q (rate proportional to 1 - q): A 0.830, B 0.753.
The lag-6 hit / expected ratio does not move with it: A 1.85, B 1.76 (B - A -0.09; R4 mean +0.00, sd 0.38; P 0.79); across R4 replicates the doublet and lag-6 differences are uncorrelated (-0.03).

## 3. What is NOT excluded
A change point in the repair probability of the size the groups suggest (q 0.83 -> 0.75) is neither detected nor excluded (power 0.14); changes in the null rate per word are tested only through the mean word length (no per-page fit of the length histogram); page units are 3-15 per section, with a section start counted as a page start; the group split A / B was suggested by the data (hence no independent P); only R4-type simulations (one fixed setting) were used as the null; other settings (key, table) that left no trace in these four series are untouched.
