# Phase 26: audit of the "464-word table" claims (Discord thread "The Unreasonable Way", 2026-10)

Nothing in LP2 is solved. This phase tests a numerological/structural claim about the four solved sections and a
proposed two-panel carrier in LP2; it decodes nothing. Third-party files were read as data only (copied to the
git-ignored `work/ref/discord_464/`); no code from them was run. Seven attachments: NUMBER SQUARE.docx (an
unrelated recurrence-relation write-up on `15.jpg`, nothing to do with columns), koan-passage-removal-assessment.txt,
COLUMN_CONTRIBUTIONS.md, grille-and-other-potential-applications.md, SECTION_WORD_TABLE.md,
QUESTION_CONSTRUCTION_FINDINGS.md, CARRIER_FINDINGS.md.

Code: `work/phase26_words.py` (word splitting), `work/phase26_464_table.py`, `work/phase26_464_followup.py`,
`work/phase26_clause_tail.py`. Outputs: `work/log/phase26_464_table_output.txt`, `phase26_464_followup_output.txt`,
`phase26_clause_tail_output.txt`. Seeds fixed; 1 core each.

## 1. Facts: all reproduce exactly (Level 0 facts, independent re-derivation)

| Claim | Repo data | Match |
|---|---|---|
| Warning / Welcome / Koan / Koan 2 = 45 / 124 / 208 / 87 words, 464 total, 1796 runes | 45/124/208/87, 464, 1796 | yes |
| the 464 rune-word lengths (list in the removal note) | identical, element by element | yes |
| 464 = pi(3301) = 16 x 29 | 464 = pi(3301) = 16 x 29 | yes |
| R = 77321/307435 = 0.251503569860 | exact Fraction: 77321/307435 | yes |
| segments 12/13/14 = 224/349/355 = 928 rune-words, 4134 runes, 5 number tokens | same | yes |
| word 464 = ᛋᚠᚾ, word 465 = ᚢᚦᛟᚷᛖᚪᛟᛇᛇ, same line | same runes; only a plain word separator between | yes |

No mismatch. Word = text between word/clause/paragraph marks; line and page breaks do not split a word. The
report's removal result (0.390274; 13 higher; 3 in the koan; 75.1%) and the question note's numbers (net dot
-17195/62, clause 0.2.0.14 = -187.935, share 0.6776) also reproduce exactly.

## 2. Calibration of R = 0.2515

R = sample variance of the 16 column means / (pooled variance / 29); E[R] = 1 exactly under permutation (checked:
4,000,000 permutations, mean 0.9992).

| Null | Result |
|---|---|
| (a) permutation of the same 464 lengths, 16 columns | **P(R <= 0.2515) = 5690/4,000,000 = 1.4e-3** (chi2_15/15 approximation 1.6e-3). Pre-specified single test, two-sided about 2.8e-3 |
| 464-word slices of English prose in GP-rune spelling (Emerson, KJV, Republic, Zarathustra, Origin, Walden, Paradise Lost, Meditations, Ethics, BGE; 228,347 slices, stride 8) | w=16 mean R 1.02, median 0.97, **fraction <= 0.2515 = 0.17%** (0.08-0.38% by book). Widths 29 and 58: 0%. w=8: 2.5% |
| (c) known English structure | Refuted as explanation: English word-length ACF is -0.10 to -0.18 at lag 1 and about 0 beyond; R of English slices centres on 1, not below. Within-row/total variance of the table is 1.000, i.e. rows are not homogeneous either. Shuffling rows leaves R unchanged; shuffling words inside rows gives P = 0.0014 again; shuffling clause order gives P = 0.0016. So the low R is not explained by local autocorrelation, clause structure or row composition. It is a low sum of lag-16k autocorrelations of this particular sequence |
| look-elsewhere A: every non-empty subset of the 9 solved sections x every width 4..64 dividing n (1450 cells) | 25 cells (1.7%) have R <= 0.2515, but small widths are not comparable (w=4: R 0.147 has p = 0.07, w=8: R 0.345 has p = 0.065). By p-value the chosen cell (sections 0,1,3,5; w=16, p = 1.6e-3) is the minimum of the family; with sections shuffled internally, **P(some cell this good) = 0.77** |
| look-elsewhere B: every subset >= 100 words at w=16 (485 cells) | chosen subset ranks 10 of 485 by R; a different subset (0,1,3,6,17) has smaller p (5e-4). Selection null: P(min p <= 1.6e-3) = **0.22** |
| look-elsewhere C: subsets x w = 8..32 | min p 4.9e-6 (sections 1,3,5; w=32); P(some cell as good as the chosen one) ~ 1.0 |

Reading: taken as a single pre-specified test (these four sections, 16 columns) the balance is a 1-in-700 (one-sided)
low value, not explained by any known property of English or of this text's clause structure. But the choices that
led to it (which sections: dropping Some Wisdom, Loss of Divinity, Instruction is defensible as "the encrypted
ones"; which width: 16, tied to 464 = 16 x 29 = pi(3301), a numerological selector chosen independently of R) give
a search space in which an equally good cell appears 22% (subset search at w=16) to 77% (all divisor widths) of the
time under a null. The statistic was found by inspection after the fact. **Level 1 (observation worth recording,
not evidence of construction).** Not excluded: that the authors fixed the sections/width by numerology first and
R second; that is untestable from the thread.

## 3. The passage-removal and question-construction analyses

Removal note (13 of 449 blocks raise R more; 4/193 in the koan; 2.07-3.47%):
- Reproduced exactly, but the percentages are fractions of starts with the target pre-chosen. The target was chosen
  after the fact from 22 clauses.
- Calibration on 588 of 400,000 permuted sequences that have R <= 0.2515 (same selection as the real table): the
  best clause-aligned removal is in the top 3.1% (median) of the 449 starts, the real table's top 2.9%; the real value
  is matched or beaten in 49.5% of look-alikes. In such look-alikes a random 16-block removal gives median R 0.24
  (real 0.28), and 42% (real 75%) of starts raise R at all; the best removal reaches 0.39 (real 0.42).
  The result is what any selected low-R sequence gives. **Level 0-1: no information beyond R itself** (the note
  says as much).

Question-construction note (clause 0.2.0.14 = 67.76% of the net Welcome x koan residual dot):
- Share as a share is uninformative: under koan-length shuffles (clause sizes kept) the largest clause carries >= 67.8% of
  the net with P = 0.52.
- The underlying contribution is not ordinary: the 16-word window's dot is -188 (null sd 37.6) with Welcome fixed
  and koan lengths shuffled (P < 1e-5; min over all 193 windows P = 5e-5). Shuffling both sections gives P = 0.0099.
  The structure-preserving null (the koan kept intact, only its start column varied over 16 offsets) is the fair one:
  the real offset (column 10) has the most negative sliding-window minimum (-193.0 vs next -131.3) and the most
  negative net (-277.3 vs -246.7 and -237.7), rank 1 of 16 for both, p about 0.06 each, same phenomenon as the low R
  (both are the Welcome and koan column deficits cancelling), not independent of it. **Level 1.**
- Narrative claims ("deliberate", "the sentence is a lock") are Level 0 (no testable operation).

## 4. The 928-word two-panel carrier (LP2 segments 12-14)

- Panel 1 (words 1-464) as 29 x 16: R = 0.942 (permutation P = 0.48, English slices 0.47); panel 2: R = 1.181
  (P = 0.73). 29 columns: 1.53 / 1.25. Over all 465 windows of 464 words inside the 928 the minimum R (w=16) is
  0.645, reached by 16% of English slices. **The carrier does not show the table's balance** (Level 1, negative for
  "built like the solved table"; the lengths are those of the ciphertext words, equal to plaintext lengths only if
  the cipher is letterwise).
- The split at word 464/465 has no printed boundary (ordinary separator, same line); the 2 x 464 arithmetic fixes
  nothing else.
- **Preregistered pairing test** (frozen before running, cost under 1 CPU-minute): pair cell j of panel 1 (29 x 16)
  with the cell of panel 2 given by each of 8 layouts (29 x 16 and the transposed 16 x 29, each with identity / flips /
  rot180); statistics: correlation of word lengths, count of identical rune-words; null: panel 2 shuffled (3000);
  decision: Bonferroni over 16 tests (alpha 0.0031).
  Result: smallest p = 0.135, **no detection**; zero identical-word pairs in every layout (null mean 0.0, short-word
  coincidences included). Positive control (random layout, fraction q of panel-2 cells replaced by the paired panel-1
  word): detected 100/100 at q = 0.05, 0.10 and 0.25. Null false positives 3/300 (1%). So any panel-copy or
  word-pairing relation above 5% of cells between the two halves is excluded. **Level 1 (negative, specific layouts).**
- The grille itself: **not testable.** Missing instructions: (i) the hole-set (the GP-sum values of "all three
  magic squares" and the "hollow table" are not given in the attachments, so their masks cannot be rebuilt); (ii) how
  the 29 x 16 hole pattern is applied to a carrier panel (which panel, orientation, whether two panels overlay);
  (iii) what the surviving cells encode (words? first runes? a number readout) and what makes a readout correct
  (the carrier is ciphertext, so a readout still needs a key). Their own sliding-window sweeps report no message.
  Any test I could write without (i)-(iii) would be a search with no positive control. If the thread supplies the
  value sets and a stated readout, a test is cheap (a mask is 464 booleans; null = random masks with the same hole
  count; positive control = a plaintext planted into the carrier cells the mask selects).
- The side-observations in the grille note (311 is the 64th prime; 9% or 26% of random masks as flat) are, by
  the author's own statement, post-hoc: Level 0.

## Evidence scale and verdict

| Finding | Level |
|---|---|
| All counts, lengths, R, 928 split reproduce | 0 (fact check) |
| R = 0.2515 is 1.4e-3 under permutation, 0.17% in English slices, not explained by English structure | 1 |
| Selection-corrected: 22% (subset search) to 77% (divisor-width search) of nulls offer an equally good cell | 1 (down-weights the above) |
| Passage removal percentages | 0-1 (equals what any selected low-R sequence shows) |
| Clause 0.2.0.14 dominance: extreme for fixed Welcome, p about 0.06 under koan-start-column null, same effect as low R | 1 |
| 928-word carrier: no balance, no panel pairing at 5% | 1 (negative) |
| Grille / two-panel reading as a decryption route | 0 (no operation defined) |

Verdict: the numbers are right, and R = 0.25 is a mildly unusual single-test value (about 1 in 700) that survives the
known English-structure explanations, but it is not significant after the choices made and it names no operation.
Nothing here decodes or supports a decoding of LP2; no test of the grille can be run until the hole-set and readout are
specified. Nothing to add to LP2 candidates beyond the negative pairing test.
