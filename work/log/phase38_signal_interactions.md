# Phase 38: do LP2's keyless signals interact? (isomorphs, lag-5 x lag-6 overlap, echo words vs the +1 length model)

Code: `work/phase38/run.py` (reuses `work/mech25/measure.py`, `work/families/fam_data.py`, `work/mech25/sim25.py` conventions). Output: `results/analysis/phase38.txt`.
Nothing in LP2 is solved. This phase measures structure; it decodes nothing.

## 0. Pre-registration (written before any statistic below was computed on LP2)

Only these were looked at before writing: the totals (12,956 runes, 2,896 words, 9 sections), the counts 80 (in-word lag-6 hits), 104 (in-word lag-5 hits), 11 (S,S among them),
and that DJU BEI is runes (23,11,1)(17,18,10), two identical copies. DJU BEI has six DISTINCT runes, so its equality pattern is "all different", which almost every
6-window has: the isomorph test is vacuous for that target. It is still run (reported as the share of windows with that pattern) and the informative form of the
target test is the affine-map search of 1.3.

Conventions: the rune stream is LP2 from `fam_data.lp2()` (c, start, sid). Words are the project's segmentation. Windows never cross a section boundary.

### 1. Isomorph search
1.1 Window pattern: for a window of L runes, the vector of first-occurrence indices (equal runes get the same index). E(window) = number of equal rune pairs (i<j)
inside it. A window is informative if E >= 2.
1.2 Matched pair: two windows of the same L (6 <= L <= 30), same pattern, E >= 2, both inside one section each, non-overlapping (start difference >= L).
Statistics of a run (LP2 or a null text), all over every L and every pair:
  * **Emax** (primary): the largest E of any matched pair.
  * S3: number of maximal matched pairs with E >= 3 (maximal = neither (a,b,L+1) nor (a-1,b-1,L+1) is matched; L=30 counts as maximal).
  * Lbest: the L of the best pair (reported only).
Whole-search calibration: the null distribution is of the same statistic (best over all lengths and pairs) in each null run; p = (1 + #null >= obs)/(1 + n), one-sided.
Nulls: N1 shuffle of runes inside each section (keeps section lengths and rune frequencies); N2 shuffle of the order of whole words inside each section (keeps words,
word lengths, in-word structure). 300 runs each. Decision: an isomorph signal needs p <= 0.01 for Emax against BOTH nulls. Otherwise: no isomorph signal.
1.3 DJU BEI under affine maps: for each of the 812 maps m(c) = a c + b (mod 29), a in 1..28, b in 0..28, the target t = (23,11,1,17,18,10) becomes m(t).
  * Cw(m) = number of adjacent word pairs whose words are exactly m(t[:3]), m(t[3:]);  Cr(m) = number of contiguous occurrences of m(t) in a section, ignoring words.
  * Whole-search statistic: max over the 811 non-identity maps of Cr, and of Cw. Identity gives Cw = 2 (known) and is excluded.
  * Null: N1 and N2, 2,000 runs each; p as above. A non-identity map "hits" only if its Cr >= 1 and the whole-search p <= 0.01. Report also the per-class counts for shifts
    (a=1), reflection (a=28), other a.
1.4 Controls (the same Emax / S3 statistic, 100 runs each, English plaintext of LP2's length and section layout from `fam_data.english`, key read under the skip rule):
  at each cipher rune, c = p + k (mod 29) with k from the key at a pointer; if c would equal the previous cipher rune, with probability 0.81 the pointer jumps one place and
  the rune is recomputed (repeat until it differs or the coin fails), the pointer then moves one on. This gives LP2's 2.8% skips.
  * R0 random-key null: k iid uniform (no key structure; plaintext English, skips as above).
  * P periodic key: period P in {13, 47}, random base key.
  * G progressive key: k_i = base[i mod P] + s * floor(i / P), P in {13, 47}, s = 3 (windows P apart are isomorphic with shift 3 s).
  The test **recovers** a planted key if its Emax exceeds the 99th percentile of R0 in >= 50% of plants. A control that is not recovered means the isomorph negative
  has that limited power (reported as such). Also a "no skip" version of each plant, to show what the skips cost.

### 2. S lag-5 x lag-6 overlap
Sites (position = the later rune i of the pair): S-sites = in-word lag-5 hits with c_i = c_(i-5) = S (11); L6-sites = in-word lag-6 hits c_i = 24 - 2 c_(i-6) (80).
Statistics, computed from the S-sites' side: A = number of S-sites whose word contains >= 1 L6-site; B = number of S-sites with an L6-site within +-1 position (same word);
C = number of S-sites at exactly an L6-site position. From the L6 side (the reverse direction): A', B', C' = the same counts of L6-sites with respect to S-sites.
Null: the sites' distribution over words and word positions is kept: the per-word site pattern of the moved class is permuted among words of the same length
(S pattern moved for A,B,C; L6 pattern moved for A',B',C'), 20,000 permutations. Both tails are reported: P(null >= obs) (co-location), P(null <= obs) (avoidance).
Decision: a **coherent association** = the same-word statistic (A) and the +-1 statistic (B) both have a one-sided P <= 0.025 in the same direction (A' and B' likewise in
the reverse direction as a consistency check; not required). Otherwise: no association detected.
Controls: positive = 200 pseudo-datasets in which each S-site is, with probability 0.5, moved to the position of a random L6-site (co-location planted); the share
detected by the rule is the power. Null = 200 pseudo-datasets drawn from the same permutation null; the share flagged is the false-positive rate (should be <= ~5%).

### 3. Echo-bearing words vs the +1 length model
Word-length histogram bins 1..11, 12+ (as `work/wordlen.py`). Model: Emerson, digraph spelling, `lp.word_to_key`, +1 rune in a fraction r of words; r and the variant
(all words / multi-rune words only) fitted to all 2,896 LP2 words by minimum G (one fitted parameter); r gets a bootstrap interval (1,000 resamples of LP2's words).
Groups: echo-bearing = a word with >= 1 L6-site (E6), with >= 1 in-word lag-5 hit of any rune (E5), or either (EU); non-echo = none of these.
Because only words of >= 6 runes can bear an echo, a group's length histogram is selected by construction. Effect sizes are therefore taken against the **selection
null**: 1,000 shuffles of runes inside sections (word lengths fixed), and in each the same groups are formed. For each group and each of {mean length, fitted r, G against the global model}:
observed minus null mean, the null 2.5-97.5% interval, and the bootstrap interval of the observed value. The key question is the **site-length profile**: the word length of each of the 80 L6-sites
against (i) the null profile (G, shuffle P); (ii) a mixture (1-pi) background + pi * (+1-inserted words: weight n_L * r * ins_(L-1) / q_L, the words that carry an inserted rune),
pi fitted by maximum likelihood, log-likelihood gain over pi=0 with a bootstrap-over-sites interval for pi. Decision: the +1 words carry the echo if pi's interval excludes 0 AND the
profile G against the null has P <= 0.01. If neither, no coupling between echo sites and the +1 word-length effect is detected (power reported by planting pi=0.3 in the null).

### 4. Verdict categories
One mechanism = 2 of 3 couplings detected (an association in 2, or isomorph + one coupling). Independent quirks = no coupling detected with adequate power.
Consequences of a repair process = only if the couplings found match the simulated M1/M5 predictions of phase 25 (not re-simulated here). Evidence levels: Level 0 = measured, Level 1 =
measured against a calibrated null, positive control recovered; "limited power" says which control failed.

## 1. Results (outputs: `results/analysis/phase38_iso.txt`, `phase38_dju.txt`, `phase38_overlap.txt`, `phase38_wordlen.txt`)

Deviations from section 0, all listed here: (a) section 3 asked for fitted r and G for the echo-bearing groups; both are degenerate there (r runs to its 0.8 bound for words selected to be >= 7 runes) and are dropped,
only mean length is reported for those groups; (b) one supplementary line in section 3 (excess profile) is marked "not pre-registered".

### 1.1 Isomorphs (L 6..30, E >= 2): nothing above chance, and the test has little power
| | LP2 | N1 (300 rune shuffles) | N2 (300 word-order shuffles) |
|---|---|---|---|
| Emax | 6 (best pair L=8) | mean 6.45, 99th pct 10, max 10; P(null >= 6) = 0.993 | mean 6.27, 99th 8, max 10; P = 0.960 |
| S3 (maximal pairs, E >= 3) | 2,044 | mean 2,427, 99th 3,115; P = 0.937 | mean 1,977, 99th 2,569; P = 0.355 |
LP2's longest isomorphic pair is at the low end of both nulls (it has no isomorph excess; the N1 deficit in S3 is the doublet suppression, which N1 lacks and N2 keeps). Decision rule (p <= 0.01 against both nulls): **no isomorph signal**.

Controls (English plaintext, skip rule 0.81, 100 runs per cell; share of runs with Emax above the 99th percentile of the random-key run, which is 10):
R0 random key 0.00; periodic P=13 0.03, P=47 0.01; progressive P=13 0.02, P=47 0.02; the same four without skips 0.07, 0.05, 0.11, 0.05. **The planted keys are not recovered (criterion: >= 50%).**
Natural English has too few repeated informative 6+ rune windows at key-multiple distances, and the skip rule cuts the share further (0.07-0.11 without skips). So this isomorph negative excludes only
keys that produce much stronger isomorphs than a P=13/47 periodic or progressive key over English does; it says nothing about those keys themselves. Level 0 (measured, null calibrated, positive control failed).

DJU BEI: the pattern is six distinct runes, which 66.5% of all LP2 6-windows have, so the isomorph form is vacuous. Under all 811 non-identity affine maps, LP2 has **0** contiguous (Cr) and **0** word-aligned (Cw) occurrences of
a*DJUBEI+b (identity: 2 word-aligned copies, the known pair). Chance of any hit among the 811 maps is 1.75% (N1) / 1.25% (N2) for Cr and 0.05% for Cw, so the zero is not informative either way; p = 1.0. **Level 0: DJU BEI has no affine image anywhere in LP2.**

### 1.2 S lag-5 x lag-6 overlap: no association in either direction
11 S,S sites lie in 11 words, the 80 lag-6 sites in 74 words, 2 words contain both.
| statistic (over the 11 S-sites) | obs | chance (sd) | P co-location | P avoidance |
|---|---|---|---|---|
| A same word | 2 | 1.45 (1.04) | 0.44 | 0.85 |
| B within +-1 | 1 | 0.80 (0.83) | 0.57 | 0.82 |
| C exact position | 0 | 0.20 (0.44) | 1.00 | 0.82 |
Reverse direction (80 lag-6 sites, S-sites fixed): A 2 vs 1.73, B 1 vs 0.80, C 0 vs 0.20; P co-location 0.52 / 0.57 / 1.00. Rule (A and B both P <= 0.025 in one direction): not met either way.
Controls: planting co-location (half of the S-sites moved onto L6-site positions) is detected in 85% of 200 pseudo-datasets; null pseudo-datasets are flagged 0 times in 200 (co-location and avoidance). **The two echoes are independent as far as 11 S-sites can show; power for a half-strength co-location is 0.85, for weaker coupling lower.** Level 1 for "no strong coupling".

### 1.3 Echo-bearing words vs the +1 model: no coupling
Global fit: +1 rune in 42.5% of multi-rune words (r bootstrap 95% interval 0.380-0.470), G 16.5 (df 10), i.e. phase 25's fit. Word counts: L6-bearing 74, lag-5-bearing 93, either 149, none 2,747.
| group | mean length obs [bootstrap 95%] | selection null (rune shuffles) mean [2.5-97.5%] | obs - null |
|---|---|---|---|
| L6-bearing | 9.30 [8.99-9.55] | 9.22 [8.74-9.70] | +0.08 |
| lag-5-bearing | 8.85 [8.58-9.18] | 8.56 [8.17-8.98] | +0.29 |
| either | 8.93 [8.70-9.17] | 8.75 [8.46-9.05] | +0.19 |
| non-echo | 4.23 [4.17-4.29] | 4.31 [4.28-4.34] | -0.08 |
Non-echo words alone: fitted r 0.380 [0.345-0.420] (null 0.395), G against the global model 77.6 (null 43.9 [33-57]); the +34 in G over the null is mechanical: LP2 has ~35 more bearing words than chance and they are all long, so removing them takes long-word mass out of the non-echo histogram (the model's 7+ rune tail is then too heavy). The comparison therefore carries no information on coupling.
Echo-bearing words are not longer than chance selection predicts (obs - null inside the null interval for all three; lag-5 +0.29 is at the interval edge).
Site-length profile of the 80 lag-6 sites: observed [lengths 7..12+] 8, 21, 20, 7, 14, 10 against chance (44.6 sites expected per shuffle) 7.5, 10.8, 8.1, 7.2, 5.4, 5.7: G 9.4, P = 0.11. Excess profile (obs - chance, sum 35.4) 0.5, 10.2, 11.9, -0.2, 8.6, 4.3 (lengths 8, 9, 11 carry the excess; post hoc, not significant).
Mixture with +1-inserted words: pi = 0 (bootstrap 0-0.05), likelihood gain 0, and with pi fixed at the excess share 0.44 the fit is worse than the chance profile (log-lik -4.2).
Power: a planted pi = 0.3 is detected at P <= 0.01 in only 15% of runs, because the +1-word profile is close to the chance profile. **So: no evidence the echoes sit in the +1 words, and no power to see it unless the coupling is stronger than pi ~ 0.5.** Level 0/1.

## 2. Verdict
| finding | result | evidence |
|---|---|---|
| isomorphs (L >= 6) | none above 300+300 nulls; LP2 at the low end | Level 0; planted periodic/progressive English keys NOT recovered (<= 11%): low power |
| DJU BEI under 812 affine maps | only the identity (the known pair); 0 other hits | Level 0 (trivial pattern; chance of a hit is ~1.5%) |
| S lag-5 x lag-6 overlap | 2/11 same word vs 1.45 chance; no co-location, no avoidance | Level 1 for no strong coupling (planted 50% co-location detected 85%) |
| echo-bearing words vs +1 | lengths as selection predicts; echo sites not concentrated in +1 words | Level 0/1; pi = 0.3 detectable only 15% |
**Verdict: independent quirks, not shown to be one mechanism.** Neither tested coupling (S5 x L6 co-location, echo x +1 insertion) is detected, and the isomorph search finds no key-periodicity trace (with the caveat that it could not have found the planted weak ones either).
This is not evidence that a repair process does NOT produce them: phase 25's M1/M5 repairs predict a coupling of 2.8%-of-runes size, which the 11-site overlap cannot resolve (power 0.85 only for a 50% co-location). The count of coupling tests that could have said "one mechanism" was 2 and both were null.
Section 4 of the task (a proposal for echo-sites-as-skip-markers) is **not added**: neither (2) nor (3) shows a coherent association.
