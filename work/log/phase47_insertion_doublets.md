# Phase 47: do inserted runes explain LP2's doublets, and where do they sit? (side session, 2026-10-21)

Nothing in LP2 is solved. Script `work/mech25/insert47.py` (one core), output `results/analysis/insert47.txt`, raw run log `work/tmp/insert47_run.log`.
No PLAN / registry / STATUS / SESSION_LOG / README edits and no commit (as instructed).

## 0. Preregistration (written before the 300-replicate run; a 2-3 replicate smoke test was used only to debug the code)

**Question.** The outside review: if the "+1 rune in about 42% of words" fit is an inserted rune, placed after an anti-repeat rule enforced at 100%, each inserted rune has two unchecked
neighbours, so about N_words x 0.42 x 2/29 doublets appear (LP2 has 86), and the measured "81% enforcement" could be an artifact of insertion. Tension reported: such doublets sit in words
of mean ~5.45, LP2's in-word doublets in words of mean 6.08 (n 63, s.e. 0.32).

**Models** (English rune words from `fam_data.english`, digraph spelling; LP2's 9 sections and 12,956 runes; c = p + k, k iid uniform and consumed by plaintext runes only; random key).
- **A** (repo's current): would-be repeats repaired with q = 0.81 (to a uniform other rune), no insertion.
- **B**: q = 1.0 anti-repeat on the plaintext-length stream, then one uniform rune (no key) inserted in 42% of multi-rune words at a uniform slot 0..L (L+1 slots, word edges included).
- **C**: as B, slot 0 or L only (word edges).
- **D**: as B, pins(L) = clip(a + b (L-2), 0, 1) with (a, b) fitted to LP2's word-length histogram (G, bins 1..11, 12+ as `work/wordlen.py`).
- Extras (not asked): **E** pins = c (L-1) (insertion slot uniform over adjacent pairs); **F** = D with the slope b forced so the analytic doublet-word length is 6.08 (the reviewer's repair),
  a refitted; and **A6 / B6 / C6** = A / B / C with the echo repair (a would-be repeat becomes 24 - 2 c(i-6) when the rune 6 back is in the same word; the repo's M1), to see what insertion does to the lag-6 excess.
- Sections are cut to LP2's length after insertion. 300 replicates per model.

**Statistics** (all measured on the simulated cipher text with LP2's definitions; `measure.py` for lag 5/6): total doublets; in-word / across-gap split (LP2 63 / 23); mean length of the word
holding an in-word doublet (LP2 6.08); share of in-word doublets at a word-edge pair (first or last pair of the word) and the relative position (LP2: 30 of 63 at an edge pair); the word-length histogram:
G of LP2's histogram against each model's pooled histogram; lag-6 / lag-5 in-word z (LP2 +5.32 / +3.53).

**Decision rule** (fixed now).
1. A statistic is *consistent* if LP2's value is inside the model's central 95% interval of the 300 replicates (2.5-97.5 percentiles).
2. A model is *consistent jointly* if all four doublet statistics (in-word count, gap count, doublet-word length, edge share) are inside, the joint Mahalanobis p of (in-word, gap, doublet-word length)
   is >= 0.05, and the word-length G is not rejected at p >= 0.01 against the same-corpus floor (the simulation's multi-book English fits LP2 worse than the repo's Emerson-only English: floor G is reported).
3. Verdict on the word-edge campaign: if only edge-only insertion (C) were consistent, the edge assumption stands; if B/D/F are consistent and C is not, insertions are mid-word and the edge
   campaign's event model is aimed at the wrong place; if only A is consistent, the insertion step is not needed for the doublets and the question stays open; if none is, say that.
4. No result here counts as evidence of any mechanism; it only decides which simulated families reproduce a set of numbers.

Reproduction targets: 81 (= words x 0.42 x 2/29), 5.45, 6.02.

## 1. Reproduction of the reviewer's numbers
| Number | Reviewer | Here |
|---|---|---|
| doublets from insertion, words x 0.42 x 2/29 | 81 (2,813 words) | 83.9 with this repo's 2,896 words; simulated B (q = 1): 80 [64, 98] |
| mean length of words holding such a doublet | 5.45 | simulated B 5.38 [4.83, 6.05] (final length, in-word doublets; analytic 5.38) |
| LP2 pair-weighted mean word length, sum L(L-1)/sum(L-1) | 6.02 | 6.02 |
| G worsening when the rising length dependence is forced | 24 -> 62 | 32.3 -> 63.1 (this run's multi-book English; Emerson-only English gives the repo's 16.5 at r 0.425). Slope scan: G 32.3 at b 0, 39.4 at b +0.04, 55.1 at b +0.08 for doublet-word length 5.38 / 5.80 / 6.05 |
All three reproduce. The unconstrained linear fit D has slope b = -0.005: the histogram alone wants a flat 40% insertion probability, so "D" is B.

## 2. Simulation, 300 replicates per model (intervals: 2.5-97.5 percentiles)
| model | total doublets | in-word | across gap | doublet-word length | edge-pair share | lag-6 z | G of LP2 vs pooled model (df) |
|---|---|---|---|---|---|---|---|
| LP2 | 86 | 63 | 23 | 6.08 | 0.48 | +5.3 | |
| A q .81, no insertion | 85 [68,102] | 64 [49,80] | 21 [13,30] | 5.74 [5.05,6.43] | 0.55 [.44,.66] | -0.1 (excl.) | 226 (11) |
| B q 1, 42%, any slot | 80 [64,98] | 63 [50,77] | 17 [8,27] | 5.38 [4.83,6.05] | 0.58 [.46,.70] | -0.1 | 38.0 (10) |
| C q 1, 42%, edge slots | 77 [58,95] | 41 [29,54] | 36 [23,48] | 5.16 [4.49,5.91] | 1.00 | -0.1 | 36.3 (10) |
| D q 1, linear pins (a .406, b -.005) | 76 [60,92] | 59 [45,74] | 17 [9,25] | 5.32 [4.78,5.85] | 0.58 | 0.0 | 32.0 (9) |
| E pins = .19 (L-1) | 101 [80,120] | 83 [66,100] | 17 [10,26] | 6.50 [5.99,6.95] | 0.44 | 0.0 | 160 (10) |
| F D with b forced to 6.08 | 104 [82,126] | 84 [65,104] | 21 [12,30] | 6.05 [5.49,6.53] | 0.51 | 0.0 | 53.8 (10) |
| A6 / B6 / C6 (echo repair) | 85 / 80 / 76 | 64 / 62 / 40 | 21 / 17 / 36 | 5.74 / 5.40 / 5.18 | .56 / .59 / 1.00 | +4.7 [1.9,7.6] / +3.6 [1.1,6.0] / +4.8 [2.2,7.5] | 231 / 33.5 / 33.1 |
LP2's percentile inside the replicate distribution (inside = 0.025-0.975), joint Mahalanobis p of (in-word, gap, doublet-word length):
| model | in-word | gap | doublet-word len | edge share | joint p |
|---|---|---|---|---|---|
| A | .49 | .72 | .83 | .13 | 0.81 |
| B | .55 | .92 | **.977** | .047 | 0.08 |
| C | **1.000** | **.027** | .997 | **0.000** | 0.000 |
| D | .76 | .93 | **.990** | .053 | 0.033 |
| E | **.013** | .90 | .067 | .73 | 0.020 |
| F | **.017** | .71 | .57 | .28 | 0.20 |
Extra q scan (insertion at q < 1): C with q .90 / .95: gap doublets 43 / 40 against LP2 23 (percentile 0.000 both), in-word edge share .76 / .84 against .48; B with q .90: in-word 90 (percentile 0.000).
The G floor: with this multi-book English the best fit of any insertion model is G 32 (df 10); B's 38.0 is within pooled-sampling noise of its analytic 32.7. A (no insertion) fails the word-length test by G 226.

## 3. Reading against the decision rule
- **A** passes all four doublet statistics (joint p 0.81) and fails the word length (G 226): it is the existing model and says nothing about insertion.
- **B** (q = 1, mid-word or edge insertion, 42%) passes in-word count, gap count and edge share and the word-length fit, and sits at the 97.7th percentile of the doublet-word length (two-sided p about 0.046; joint p 0.08). By the preregistered rule it is a marginal reject on one statistic, an acceptable fit by the joint test: not distinguishable from A on the doublets. The reviewer's 2-sigma tension is confirmed at that size (5.38 against 6.08), not larger.
- **D** is B (fitted slope zero); it has the same doublet-word percentile (.990, joint p 0.033).
- **F** repairs the doublet-word length (6.05) but overproduces in-word doublets (84, 98.3rd percentile) and costs about 20 in G (54 against the floor 32): both the reviewer's trade-off and an extra failure.
- **C** (edge-only insertion) is rejected on every doublet statistic except the total: in-word 41 against 63 (LP2 above all 300 replicates), gap 36 against 23, in-word share .53 against .73, every in-word doublet at an edge pair against 30 of 63 at one; raising the enforcement gap (q .90, .95) makes the gap count worse (43, 40).
- Jointly consistent with LP2 (rule 2): none strictly; A and B are the two that survive the doublet statistics, A without the word lengths, B with them at the one marginal statistic. The echo variants do not change this: mid-word insertion dilutes the lag-6 excess from z +4.7 to +3.6 and LP2's +5.3 stays inside both; edge insertion does not dilute it (+4.8).

## 4. What this means
1. The reviewer's artifact point holds: 100% enforcement plus a 42% inserted rune gives 80 doublets (LP2 86; percentile 0.77), so the doublet count cannot tell "81% enforcement" from "100% enforcement plus insertion". The two models are not separated by the total, the split, the edge share or the echo rates; only the doublet-word length weakly prefers A (0.83 against 0.977).
2. Inserted runes that explain the doublets must be **mid-word as well as at edges** (the doublets reject edge-only; they do not by themselves prove insertion) (B: 79% of its doublets in-word, 58% at an edge pair; LP2 73%, 48%). An edge-only insertion layer (C) with any anti-repeat strength cannot produce LP2's in-word : gap split.
3. **Consequence for the word-edge campaign.** If the campaign is motivated by "the +1 rune is an inserted event at word edges", the doublet data contradict that event model (C: LP2's in-word count is above all 300 replicates, p < 0.003; gap count at the 2.7th percentile; edge share impossible, 1.00 against 0.48). It does not contradict edge events that are *not* the source of the +1 lengths, because under A the doublets need no insertion at all, and the word-length histogram alone cannot say where in a word a rune sits (the fit is the same for any slot). So the campaign's edge-only event model should not be justified by the +1-rune length fit; if the +1 runes are real, the campaign needs a mid-word event variant (positions uniform, 1 rune per 42% of words), and if it keeps edge-only events the justification has to come from another statistic (the preregistered nulledge / advsep nulls already exclude deterministic edge nulls).
4. Not tested: insertion rate 42% was held to the length fit and applied to multi-rune words only; the inserted rune's value was uniform (an inserted echo or copy rune would change the lag statistics); one English corpus family and one spelling; LP2's 63 / 23 split is a single observation (counts of 63 and 23 have Poisson errors 8 and 5), so only the edge-pair share and in-share are 2-sigma-scale discriminators; intervals are for sim replicates of the model, not for fitted-parameter uncertainty. Level 0/1 (simulation of stated models with LP2's layout; the positive control is the reproduction of 81 / 5.45 / 6.02 and A6's lag-6 z recovering +4.7; the null control is the lag-6 z of A, B, C = -0.1).
5. Files: `work/mech25/insert47.py`, `results/analysis/insert47.txt` (main run), `results/analysis/insert47_q.txt` (q scan), logs `work/tmp/insert47_run.log`, `work/tmp/insert47_q_run.log`.
