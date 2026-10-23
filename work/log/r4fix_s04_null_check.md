# R4 repair s04: how is R4's null checked, and is the check visible to the anti-repeat rule? (2026-10-23)

Nothing in LP2 is solved. Keyless simulation; LP2's ciphertext was used only for its measured statistics (layout, doublets, word lengths), nothing was decrypted.
Idea 7 of `work/laptop_review/11_next_100.md`.

## Question
Phase 57's R4 writes one null per ~45% of multi-rune words, "never equal to its left neighbour". Which of these does LP2 prefer, and do they change what a decoder must expect?
- null check: `left` (redrawn if equal to the previous cipher rune; phase 57 R4), `both` (also redrawn if equal to the next real rune: the encryptor writes the word first, then inserts), `none`;
- visibility: `visible` (the anti-repeat rule compares the next real rune with the previous cipher rune, a null included; phase 57 R4) vs `invisible` (compares with the last REAL rune; the phase 51 decoder's assumption).

## Method
`work/r4fix/s04_null_check.py` (own copy of phase 57's `simulate`/`tune`/`score`; `work/r4fix/r4sim.py` NOT imported: its test run in `_err.txt` showed one failing test when I started, so I followed the brief's fallback). Imports `phase57_mechanism` (measure, T, STATS), `fam_data`, `measure` read-only.
- Fixed as in R4: q 0.81, T repair writing T(c[-6]) (cipher-word basis in all six settings, so only the two factors vary), slot uniform 0..L (word edges included), one null in a multi-rune word with probability r, key fresh per step, English digraph plaintext (six-book corpus, 607,561 runes), LP2 layout (12,956 runes, 9 sections), 500 replicates, r tuned to 2,896 words (phase 57's secant: seeds 7 / 20-22, 100 replicates, 3 steps). Primary seed 104 for every setting.
- `both`: the next real rune before repair = plaintext rune + the key it will use (key drawn one step ahead); a null whose neighbour is unknowable at that moment (adjacent null, or the next rune later repaired onto the null's value) is redrawn in place afterwards. Adjacent nulls (null at slot L of a word, null at slot 0 of the next) are about 1% of nulls.
- `invisible`: `prevc = lastreal` in the collision test and in the uniform / T-repair exclusion; the null check itself always looks at the actual left neighbour.
- Ground truth of null positions is recorded (RN), giving doublet rates on pairs involving a null vs not. Phase 47's doublet-word length and edge-pair share added (LP2: 6.08 and 0.476 = 30/63).
- Score: phase 57's nine statistics (z of LP2 against the setting's own replicates, combined chi2, P = share of replicates with chi2 >= LP2's). Also an 11-statistic version (+ doublet-word length, edge share), per-statistic two-sided tails, and a secondary run with q refitted so the mean total doublet count equals LP2's 86 (secant, 100 replicates per step; rate unchanged; seed 204).
- Commands (two workers, below-normal priority; the script sets its own priority class):
  `python -B work/r4fix/s04_null_check.py selftest`;
  `python -B work/r4fix/s04_null_check.py run left-visible both-invisible none-visible` and `... run left-invisible both-visible none-invisible` (settings `left-visible` etc.);
  `python -B work/r4fix/s04_null_check.py report` -> `results/r4fix/s04_null_check/summary.txt`.
- Corpus note (orchestrator): until the git-ignored `work/ref/corpora/*.txt` were copied into the worktree, `fam_data.english` fell back to Emerson only (r 0.399). My `english_multi()` reads the corpora from the main checkout (located by `git rev-parse --git-common-dir`; nothing copied) and `make_ctx` asserts 607,561 runes. I checked that the worktree copy now gives the same 607,561 runes, so no rerun was needed; the tuned r is 0.4484, as in phase 57.

## Controls
- **Positive (left + visible = phase 57's R4 row):** the simulator is bit-identical to `phase57_mechanism.simulate(rule R4)` for seed 104 (assertion in `selftest`, 6 replicates), tuned r 0.4484 (phase 57: 0.448), and the 500-replicate row reproduces the published one exactly: din 60.1, dgap 16.9, t6 76.6, t6x 400.0, oth 67.0, G 30.9, uni 26.4, bi 756.0, lagz 1.9, **chi2 6.7, P 0.643** (published 6.7 / 0.643); every mean agrees to the printed digit (lagz's +1.9 se is only the rounding of 1.9x against the published 1.9).
- **Ground-truth checks of the settings** (40 replicates, q 1, r 0.6): `left` and `both`: 0 doublets with a null equal to its left neighbour (`none`: ~1/29 of such pairs, 2,138 of 64,427 = 0.033); `both`: 0 null-equals-right as well, visible or invisible; visible: the next real rune never repeats a null (`left`-visible, `both`-visible 0); `left`-invisible: next real rune repeats the null in 2,218 of 62,588 pairs (0.035 = 1/29); `none`-invisible 2,136 / 2,133.
- **Null control:** rate of doublets on pairs without a null is 0.0066 (in-word) / 0.0065 (gap) in all six settings, i.e. the repair alone, as expected.
- **Discrimination check:** pseudo-LP2 from both + invisible (single replicate, seed 4242) plus 30 more from it (seed 4243) and 30 from left + visible (seeds 4343/4344), each scored against all six settings (see results).
- NOT done: a cross-check of the five non-R4 settings against the independent `r4sim.py` (not imported, see above). Their semantics are checked only by the ground-truth assertions above.

## Results (500 replicates, q 0.81; `results/r4fix/s04_null_check/summary.txt`)
| setting | doublets in / gap (LP2 63 / 23) | z din / dgap | doublet-word length / edge share (LP2 6.08 / 0.48) | chi2 (9 stats) | P | P (11 stats) | phase 51 decoder's assumption (invisible) |
|---|---|---|---|---|---|---|---|
| left, visible (= R4) | 60.1 / 16.9 | +0.4 / +1.5 | 6.15 / 0.50 | 6.7 | 0.643 | 0.780 | no |
| left, invisible | 87.6 / 24.4 | -2.5 / -0.3 | 5.91 / 0.53 | 9.5 | 0.395 | 0.471 | yes |
| both, visible | 53.2 / 15.4 | +1.3 / +1.9 | 6.23 / 0.49 | 10.5 | 0.309 | 0.449 | no |
| both, invisible | 53.4 / 15.5 | +1.3 / +2.0 | 6.20 / 0.50 | 9.8 | 0.351 | 0.497 | yes |
| none, visible | 93.4 / 26.4 | -3.0 / -0.7 | 5.88 / 0.53 | 13.8 | 0.148 | 0.162 | no |
| none, invisible | 120.0 / 33.7 | -4.9 / -1.8 | 5.77 / 0.54 | 30.2 | 0.002 | 0.002 | yes |
The other seven statistics (t6, t6x, oth, G, uni, bi, lagz) are identical across settings within noise (z of LP2 -0.4 to +2.0): the null's check changes only the doublet counts and their placement.
Doublet rate on pairs involving a null (in-word / gap), against 1/29 = 0.0345 unchecked: left-visible 0.0033 / 0.0030, left-invisible 0.0176 / 0.0172 (null == right neighbour 0.0354), both 0.0000 / 0.0000 (either visibility), none-visible 0.0206 / 0.0208 (null == left 0.0344), none-invisible 0.0344 / 0.0345. Pairs without a null: 0.0066 / 0.0065 everywhere. Not observable in LP2.
Doublet-word length and edge share do not separate the settings (5.8-6.2 vs LP2 6.08, 0.49-0.54 vs 0.48; all inside 1.4 sd).
Two-sided tails of the in-word doublet count alone: left-invisible 0.008, none-visible 0.004, none-invisible 0.000, the other three 0.20-0.70. So the combined chi2 (P > 0.05) accepts five settings at q 0.81, but three of those five fail the doublet count itself; only left-visible, both-visible and both-invisible fit it (gap count 0.07-0.18 at the edge for `both`).

**q refitted** (q such that mean total doublets = 86): left-visible 0.788, left-invisible 0.882, both-visible 0.763, both-invisible 0.763, none-visible 0.894, none-invisible 0.998 (q 1 gives 85). All six then fit: chi2 4.7-6.6, P 0.62-0.83. So the null's check cannot be separated from the repair probability: R3 (q 1, unchecked, invisible null) is the `none-invisible` corner.

**Discrimination check.** Pseudo-LP2 from both + invisible (seed 4242: din 58, dgap 20, t6 86): scored P = 0.67 (left-visible), 0.09 (left-invisible), 0.46 (both-visible), **0.51 (both-invisible, the truth)**, 0.04 (none-visible), 0.002 (none-invisible); lowest chi2 is left-visible, not the truth. Over 30 pseudo-LP2 from both + invisible the truth has the lowest chi2 in 12 of 30 (left-visible 8, both-visible 10) and is accepted 29/30, but left-visible and both-visible are accepted 29/30 too; left-invisible 7/30, none-visible 3/30, none-invisible 0/30. From left + visible (30): truth lowest in 16, accepted 27; both-visible accepted 24, both-invisible 24, left-invisible 17, none-visible 8, none-invisible 0. The statistics rule out only the unchecked, invisible corner at q 0.81 and weaken the others' fit; they do not identify the check or the visibility.

## Verdict
- **Not decidable from LP2's statistics** between `left`/`both` and `visible`/`invisible` (pseudo-LP2 test: the true setting is the best fit in 12/30 and 16/30 of cases, and its neighbours are accepted as often).
- At the stated q 0.81, by the brief's criterion (P > 0.05 on the nine statistics) LP2 accepts left-visible (0.643), left-invisible (0.395), both-visible (0.309), both-invisible (0.351) and none-visible (0.148); it rejects none-invisible (0.002). Stricter, on the in-word doublet count alone, left-invisible (87.6 vs 63, tail 0.008) and none-visible (93.4, 0.004) also fail. With q refitted to LP2's 86 doublets every setting is accepted (P 0.62-0.83).
- **The phase 51 decoder's invisible-null assumption is consistent with accepted settings**: both-invisible (P 0.351, doublet count fine), left-invisible (P 0.395 at q 0.81 but too many in-word doublets; P 0.80 at q 0.88), none-invisible (only at q ~1, which is phase 57's R3).
- What the setting changes for a decoder: under `both` no doublet touches a null; under `left` a null never repeats its left neighbour, but the next real rune repeats it at 1/29 if the null is invisible (0.035 of such pairs) and never if visible; under `none` equal neighbours around a null occur at ~1/29 per side (less on the right if visible). Pairs without a null are unchanged (0.0066).

## What this does NOT exclude
Anything outside this grid: the T repair on the cipher-word basis only (R3's real-stream basis not crossed); one null per word, slots 0..L only; q 0.81 or the refit only (q is a free knob); English digraph plaintext, iid key (a structured key is not simulated); no cross-check of the five non-R4 settings against `r4sim.py`; the 63 / 23 split and the 0.48 edge share are single counts with sd 8 / 5 / 0.07, too coarse to separate the settings. No decryption was done.

## Files
`work/r4fix/s04_null_check.py`; `results/r4fix/s04_null_check/summary.txt`, `raw_<setting>.json` (per-replicate statistics, six settings, includes pseudo-LP2 replicates), `s04_runA.log`, `s04_runB.log`; this log.
CPU: selftest 34 s; run workers 140 + 163 + 102 s and 127 + 156 + 111 s (about 13.9 CPU-minutes in total, 2 processes, below normal priority), report a few seconds.
