# Phase 10: keyless tests and what their power really is (2026-10-17, 19:10)

Scope: LP2 (sections 0.7-0.15). **Nothing in LP2 is solved.** The user's direction: stop open-ended generation, test specific hypotheses that nobody (including us) has exhausted. Three tests were run on the
main-branch data with the rule "measure the detection threshold with a planted control BEFORE reading a negative". The result is as much about the tests as about LP2.

## 1. The laptop's `kscreen-typo` checkpoint (research/new-hypotheses f7b8998, 46843a2, pushed while the campaign was still running)

Hypothesis (cicadanotebook.com): the key restarts at typographic marks. 22 windows: the five numbered-list items of 0.14 (91-139 runes), the whole list, five three-dot marks, ten places after red headings;
the 1,447-keystream library at every offset against a matched null of 1,439 random keystreams. As pushed: windows of 250-300 runes (15): library best IoC 1.285-1.359 against null maxima 1.29-1.43, far below the 1.40
rule, and planted keys clear their null in 45 of 45 of these windows (a strong negative); windows under 150 runes (7): every library best is at or below its window's null maximum, but planted keys are recovered in only 13 of
21 cases and clear their null in 9 of 21 (a weak negative). Solved sections: the true keys run straight through their three-dot marks (restart or skip at the mark: 61-209 of 66-209 runes wrong). The final push (f096a8c, 19:26) added the null of items 4-5,
the pooled test and the summary; its write-up `typo_restarts_2026-10-17.md` still says PENDING_CONTROLS / PENDING_RESULTS. Final numbers in 1b.

**Shared-key test on the five item lists** (`work/typo_shared_key.py`, `results/analysis/typo_shared_key.txt`): a restart with the same library keystream and offset would put that setting in each item's top-2,000 list.
Observed: 0 settings in two or more of the five lists (chance 0.76 for two, 3e-5 for three); the random null (items 1-5): one setting in two lists, none in three (chance 0.35 and 6e-6). **Power** (`work/typo_shared_key_power.py`, `results/analysis/typo_shared_key_power.txt`): a library
key planted at the same offset into English twins of the five items is in the top 2,000 of at least 3 of the 5 lists in 6 of 6 plants (ranks 1-8 for the 139-rune item, 18-41 for the 91-rune item, 399-735 for the
98-rune item, 3-8 and 1-2 for the others; one plant missing from one list), and the test then reports settings in 3 lists. So the test can see a shared key, and its zero is a genuine negative for library keystreams. (My first
power attempt was wrong: kscreen's `plant` mode shifts the offset by 997 per window, so a lookup of one offset in all items could not match; each item is now planted separately.)

## 1b. The laptop's final results (f096a8c), read as data on 2026-10-17 19:40

- **Pooled test (the laptop's own, same idea as mine with a counter offset added):** one library keystream restarted at every list item, offset equal in all items (d = 0) or offset + k for item k (d = 1): library 0 settings in 3 or more
  of the 5 lists (d = 0: 0 in two lists; d = 1: 1 in two lists, 'e digits' at offset 7953), random null 0 in 3 or more. Planted controls 3 of 3 pass (true key above the cut-off of 4, 5 and 5 of 5 lists). With my own run on the
  final lists (0 in two or more lists, power 6 of 6) this is a negative for a library key shared by the five items; it does not test a key that is not in the library.
- **Matched null per window (`typo_summary.txt`):** the library beats its matched null (best of 1,439 random keystreams) in 5 of 22 windows, all of 282-300 runes, by 0.003-0.037 IoC (best library value 1.359, rule 1.40, planted keys
  1.6-2.0 in these windows); in all 7 windows of 81-139 runes the library best is at or below the null best (for example 2.023 against 2.121 for the 81 runes after the red heading of 0.13). Two windows tie (1.879, 1.718).
  Planted controls: 44 of 45 recovered and 45 of 45 above the null at 250-300 runes; 13 of 21 and 9 of 21 below 150 runes (the three keys planted into the 81-rune window are not above its null in any case).
- **The summary's last line, 'verification: 14 of 15 re-decoded hits keep IoC >= 1.4 ... (CANDIDATE - inspect)', is an artefact of the verify rule, not a candidate.** All 15 hits are in windows of 81-96 runes (the 14 that pass the rule and one it labels noise), whose
  random null reaches 2.09-2.22 (every hit sits at 1.9-2.02, below its window's null best); the rule compares a hit with the SAME keystream at 20 random offsets (max 1.2-1.37) and not with the best of the 29 million
  settings screened, so any short-window maximum passes it. The decodes are letter soup built from repeated AE / TH / ING pairs (the beam picks high-frequency pairs), no word, and none was verified over a whole section
  (the CLAUDE.md rule). I did not run the rule on the null's hits. Suggested rule for the laptop: a hit must exceed the window's matched null best, then be verified over the whole section.
- **Not interpreted:** at the common cut-off (IoC 1.7185) the lists hold 1,090 library rows and 2,000 null rows, 1.2 times the null's rate per setting screened (1.12e9 against 2.48e9 settings), carried by the 81-rune window (896
  against 1,507 rows, 1.3 times); the other short windows give 0.8-1.2 times. A single true key adds one row, not hundreds, so this is a composition difference between the library's streams and uniform random streams; no test was made.
- **Known answers (`typo_known.txt`):** the published keys of 0.5 and 0.16 run straight through their three-dot marks (restart or skip at the mark: 28-209 of 33-209 runes wrong), so the mark itself is not a restart in the solved sections.
- **Privacy:** the added lines of f096a8c are clean except one comment line in the header of `typo_summary.txt` and its log that names the interpreter by a home-relative (tilde) path, no user name; to scrub at merge.

Conclusion for the hypothesis 'the key restarts at typographic marks': excluded for library keystreams in windows of 250-300 runes (three-dot marks, text after headings, the whole list) with the controls above, and for a
library key shared by the five short list items; NOT excluded for a single short window (81-139 runes), which no test here can rank.

## 2. A general fixed map between runes at a fixed distance (`work/families/perm_relations.py`, `results/analysis/perm_relations.txt`)

Generalises the affine scan (`lag5_affine.py`, equality and a c + b only): for each relation family (within words at distance 1-12, across the section at distance 1-12, the same position of word w and w+m for
m = 1-3, the first runes of word w and w+m) the permutation of the 29 runes with the largest excess of pair counts over independence is found by the assignment problem and calibrated on 1,000 shuffles of LP2.
Result: nothing. The best family (within words, distance 9, 192 pairs) is z +15.3 with P 0.027 for that family; over all 30 families P(null best >= observed) = 0.68. Even the lag-5 effect only reaches P 0.056 in this
framework. **Power:** with a planted fixed map (equality or a random permutation) at distance 5 inside words, the scan detects a copy probability of 0.06 in 20 of 20 texts, 0.03 in 4-5 of 20, **0.015 (LP2's lag-5 effect size)
in 0-1 of 20**. So this scan excludes strong evolving-alphabet maps between words and positions (copy rate of about 6% or more), not a map as weak as the one LP2 shows.

## 3. A sparse-tap linear recurrence in the key (`work/families/tap_recurrence.py`, `results/analysis/tap_recurrence.txt`)

Hypothesis: k_i = a k_(i-d1) + b k_(i-d2) + beta (mod 29), taps 1 <= d1 < d2 <= 12 (66 pairs), (a, b) != (0, 0): 55,440 forms; the residual c_i - a c_(i-d1) - b c_(i-d2) cancels the key and keeps a mix of plaintext letters, so its
IoC exceeds 1 if the recurrence holds (the two taps of the observed within-word effects are 5 and 6; the earlier recurrence screens covered contiguous orders up to 3). Result: the best forms are the known doublet deficit
(taps (1, x), a = 1, b = 0: IoC of the step 1.024, z +42 anywhere, +22 inside words) and, inside words, the known lag-6 relation (taps (5, 6), a = 0, b = -2: IoC 1.027, z +4.5); no new form. **Power: poor.** Planted
recurrences in English under the skip rule: a two-term unit-coefficient form is seen (taps (5, 6), a = 1, b = 0: z +69), three-term forms are not (a = 3, b = 2: z +4.6, rank 15 of 55,440; a = 5, b = 1: z +1.3, rank 6,229;
a = 1, b = 1: z -0.2, rank 29,640): a mix of three English letters is too close to uniform at n = 13,000. This agrees with the AI-campaign repo's remark that seed-agnostic LFSR / lagged-Fibonacci scans are underpowered.
The negative therefore excludes biased two-term relations only. (A first run used the wrong scale for z, off by sqrt(n); the null comparison was unaffected, the numbers above are the corrected ones.)

## What this says about method

- A statistic computed on the ciphertext alone leaves the plaintext as noise, so it sees only strong effects (copy rates of several percent, two-term relations). Both scans failed their own planted controls at the effect size
  LP2 actually shows (1.5%), which is the honest reason to read them as 'excludes strong versions only'.
- Tests that DECODE with an explicit key family (kscreen) have far more power (planted keys at IoC 1.6-2.0), but need an enumerable key family. The specific hypotheses worth running are therefore the ones that can be
  turned into a finite key family and a decode screen, or into a crib.
- Next: a coverage-and-power ledger (for every family tried, the smallest effect its null excludes), to list the hypotheses that are still open.
