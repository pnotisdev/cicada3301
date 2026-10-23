# R4 repair s02: which null-slot rule does LP2 prefer under R4? (2026-10-23)

Nothing in LP2 is solved. Keyless simulation only (LP2's measured statistics are the targets; nothing was decrypted).

**Verdict: LP2 accepts all three slot rules; `interior` (what the decoder implements) is NOT rejected (chi2 6.6, P 0.667, no |z| > 2.1), `any` (phase 57) 6.7 / 0.643, `edge` (0 or L)
8.6 / 0.461 with the gap-doublet count the weakest point (z +2.0). The nine statistics, the doublet placement and the word lengths do not separate the rules, so this simulation
gives no ground to say the current decoder models the wrong slots on these statistics; it also gives none to prefer it.**

## Question
Under R4 (q 0.81, repair writes T(c-6) = 24 - 2 c(-6) in-word, one null per multi-rune word, never equal to its left neighbour, rate r tuned to LP2's 2,896 words), where does the null sit:
`any` slot 0..L (what phase 57 fitted), `interior` 1..L-1 (what the plants and the mid-word decoder use), or `edge` (slot 0 or L, 50/50)?

## Method
- `work/r4fix/s02_slot_rules.py` (new). `simulate`, `run`, `tune` are copies of `work/phase57_mechanism.py` (read-only import of `measure`, `T`, `STATS`); the only change is the slot draw
  (original line 78): `any` = `rng.integers(0, L+1)` (unchanged, so seed 104 reproduces phase 57's R4 stream bit-for-bit), `interior` = `rng.integers(1, max(L,2))`, `edge` = 0 or L with probability 1/2.
  Added from phase 47's definitions: mean length of the word holding an in-word doublet, share of in-word doublets on a word-edge pair (first or last pair of the word).
- Same as phase 57: 500 replicates, LP2 layout (9 sections, 12,956 runes), c = p + k with a flat random key, English digraph plaintext, secant tuning of r on 100-replicate batches (seeds 7, 20-22, 3 steps),
  score seeds 100 (R0) and 104 (all R4 variants), 9 statistics z-scored against the rule's own replicates, combined chi2 = sum z^2, P = share of replicates with chi2 >= LP2's (floor 1/501).
- English corpus: phase 57 used the six-book corpus (`work/ref/corpora/*.txt`, git-ignored). **This worktree lacks those files, so `fam_data.english` here silently falls back to Emerson only
  (word-length G mean 18 instead of 31).** The first run used that fallback and did not reproduce phase 57 (r 0.399 instead of 0.448, G mean 18 instead of 31). The final run reads the
  six books from the main checkout at run time (path found with `git rev-parse --git-common-dir`; `fam_data.WORK` overridden in-process; nothing copied or edited). The Emerson-only run is kept as a supplement.
- Commands (below-normal priority, 2 workers at a time):
  `python -B work/r4fix/s02_slot_rules.py run {R0|any|interior|edge} [--english emerson]` then `python -B work/r4fix/s02_slot_rules.py summary [--english emerson]`.
  Logs `work/r4fix/s02_run_<rule>.log`.

## Controls
- **Positive (`any` reproduces phase 57's R4 row): passed, exactly.** r 0.4484 (phase 57: 0.448); din 60.1 (+0.4), dgap 16.9 (+1.5), t6 76.6 (+0.3), t6x 400.0, oth 67.0, G 30.9 (+0.2), uni 26.4, bi 756.0,
  lagz 1.9 (+1.9); chi2 6.7, P 0.643; T hits by word length 10.8/14.9/15.7/35.2, ending a word 30.9 +- 5.8: every number equals `results/analysis/phase57_mechanism.txt` (bit-identical stream).
  A direct check of the copied `simulate` against the original `phase57_mechanism.run` (100 replicates, rates 0.4 and 0.448) gave identical word counts and doublets.
- **Null (phase 57's R0, uniform repair, no nulls, same harness): passed, exactly.** chi2 117.3, P 0.002, t6 38.5 (+5.5), G 38.8 (+8.9): equals phase 57's R0 row.
- Slot-rule self-test: at r 1 the three rules give the same word count (2,669 / 2,669 / 2,666) and the interior draw stays inside 1..L-1 over 20,000 draws.

## Result (six-book English, 500 replicates, replicate mean (z of LP2))
| rule | r | din | dgap | t6 | t6x | oth | G | uni | bi | lagz | chi2 | P |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R0 uniform repair, no nulls (null) | - | 64.3 (-0.2) | 20.5 (+0.6) | 38.5 (+5.5) | 406.6 | 59.1 (+1.0) | 38.8 (+8.9) | 26.7 | 754.0 | 1.9 (+2.2) | 117.3 | 0.002 |
| R4 `any` 0..L | 0.4484 | 60.1 (+0.4) | 16.9 (+1.5) | 76.6 (+0.3) | 400.0 | 67.0 (-0.3) | 30.9 (+0.2) | 26.4 | 756.0 | 1.9 (+1.9) | 6.7 | 0.643 |
| R4 `interior` 1..L-1 | 0.4471 | 57.8 (+0.7) | 18.6 (+1.0) | 77.6 (+0.2) | 398.8 | 67.3 (-0.4) | 30.2 (+0.2) | 26.4 | 754.5 | 2.0 (+2.1) | 6.6 | 0.667 |
| R4 `edge` 0 or L | 0.4469 | 61.7 (+0.2) | 15.1 (+2.0) | 74.7 (+0.5) | 402.0 | 67.1 (-0.4) | 30.7 (+0.3) | 26.0 | 755.6 | 2.0 (+1.8) | 8.6 | 0.461 |

LP2: din 63, dgap 23, t6 80, t6x 401, oth 65, uni 26.4, bi 785.8, lagz 2.96. The unigram z are -0.0 to +0.0, bigram +0.7 to +0.8 in every row (no rule's concern).

Phase 47's placement statistics (replicate mean +- sd, z of LP2):
| rule | in-word share (LP2 0.73) | edge-pair share (LP2 0.48) | doublet-word length (LP2 6.08) | T hits ending a word (LP2 32) | T hits by word length 7/8/9/10+ (LP2 8/21/20/31) | lag-7 T hits (LP2 22) | chi2 over 12 |
|---|---|---|---|---|---|---|---|
| R0 | 0.76 | 0.55 +- 0.06 (-1.2) | 5.73 +- 0.33 (+1.1) | 16.1 +- 4.4 (+3.7) | 5.9/7.8/8.9/15.8 | 22.1 +- 5.7 | 133.1 |
| `any` | 0.78 | 0.50 +- 0.06 (-0.4) | 6.15 +- 0.35 (-0.2) | 30.9 +- 5.8 (+0.2) | 10.8/14.9/15.7/35.2 | 25.7 +- 5.6 | 7.0 |
| `interior` | 0.76 | 0.51 +- 0.07 (-0.6) | 6.20 +- 0.39 (-0.3) | 31.7 +- 5.9 (+0.0) | 11.4/14.8/15.8/35.7 | 25.9 +- 5.9 | 7.0 |
| `edge` | 0.80 | 0.48 +- 0.07 (-0.1) | 6.09 +- 0.38 (-0.0) | 27.8 +- 5.6 (+0.8) | 9.9/14.1/15.9/34.9 | 25.4 +- 6.0 | 9.2 |

Reading:
- `interior` and `any` are indistinguishable (chi2 6.6 vs 6.7; every statistic within 0.5 z). The tuned rate is the same to 0.001: moving the null off the edges changes the length histogram not at all.
- `edge` is slightly worse: across-gap doublets 15.1 against LP2's 23 (z +2.0; an edge null next to a gap is checked only on one side, and an edge-slot-L null puts the following word's first rune
  under the repair rule), chi2 8.6, P 0.461. It is the one rule that puts a statistic at 2.0, but P 0.46 is no rejection, and in-word share (0.80 vs 0.73) and T hits ending a word (27.8) are the other drifts. The
  Monte-Carlo error of a P near 0.5 with 500 replicates is about 0.02, so `edge` is worse than the other two by about 0.2 in P, a difference that rests on one statistic (dgap) at the 2-sd level.
- Phase 47's rejection of edge-only (C: in-word doublets 41 vs 63, edge-pair share 1.00) does not carry over to this R4 variant: here the edge-pair share is 0.48 (z -0.1) and in-word doublets 61.7. The reason is
  that phase 47's C inserted the null after a q = 1 anti-repeat pass and unseen by it; here the null sits in the flow and is checked, and the T-repair doublet statistics are produced inside the flow. Not
  the same model, so phase 47's verdict on its C stands for its C.
- The edge-pair share cannot separate the rules either: `interior` 0.51 vs `any` 0.50 vs `edge` 0.48 (sd 0.06-0.07); LP2's 30 of 63 is within 0.6 sd of all three.

Supplement, Emerson-only English (what this worktree gives without the main checkout's corpora; `results/r4fix/s02_slot_rules/summary_emerson_only.txt`): chi2 `any` 7.4 (P 0.571), `interior` 6.9 (P 0.593),
`edge` 9.4 (P 0.375), R0 508.9 (P 0.002; G z +21.7 because the Emerson-only histogram is too narrow a model for pooled-G). Same ordering and same conclusion; r 0.399 / 0.397 / 0.397.

## What this does NOT exclude
- It does not say where the null truly is: the nine statistics and the doublet placement are insensitive to the slot. LP2 accepts all three; a slot-resolved statistic (a decoded text, or a keyed test) is needed.
- Only q 0.81, one null per word, uniform slot within the allowed set, flat random key, English digraph plaintext, 500 replicates (P error about 0.02, z error of a count about 0.05).
- Other slot laws (weighted towards the end, position-dependent probability, slot depending on word length) were not run; `edge` is split 50/50 (slot L alone is phase 57's R7: chi2 6.4, P 0.647).
- It says nothing about the power of the interior-only decoder against edge nulls (session s01's question); a decoder that models the wrong slot loses the edge share (41-49% of nulls under `any`, 0% under
  `interior` by construction, 100% under `edge`) whatever these statistics say.
- A fit is not evidence that Cicada used the rule.

## Files
`work/r4fix/s02_slot_rules.py`; `work/r4fix/s02_run_{R0,any,interior,edge}.log`; `results/r4fix/s02_slot_rules/summary.txt` (six-book, main), `summary_emerson_only.txt`, `raw_<rule>.json`, `raw_<rule>_emerson.json`
(per-replicate statistics). CPU: about 4.3 CPU-min for the main run (77 + 73 + 69 + 38 s), 4.1 for the Emerson-only run, 1.5 for the checks: about 10 CPU-minutes, 2 workers at below-normal priority, under 200 MB each.
