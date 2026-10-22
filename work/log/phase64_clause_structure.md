# Phase 64: is LP2's clause structure authored like LP1's? (2026-10-23)

Nothing in LP2 is solved. Script `work/phase64_clause_structure.py` -> `results/analysis/phase64_clause_structure.txt`.

## 1. Plan (written before running)

- Marks counted: '.' (clause / sentence end) and '&' (paragraph end) end a clause; '%' and bare line breaks are not marks; numerals cut words only. LP1 = segments 0-6 (the solved sections' ciphertext keeps the plaintext's marks; 88 clauses, 13 paragraphs, 2,797 runes), LP2 = segments 7-9, 11-15 (167 clauses, 14 paragraphs, 12,947 runes; the caption left out).
- Statistics: mean and CV of clause length in runes, mean words per clause (words cut as in `words()` of phase 22), share of one-word clauses, clauses per paragraph, (last word length - mean word length) as the clause-end position statistic, share of odd rune counts, median clause length; KS of the length distribution; share of clause marks directly before a line / page break.
- LP1 vs LP2: permutation of pooled clauses (paragraphs for the paragraph statistic), 5,000 permutations, two-sided, Holm over the 9 tests. Bootstrap intervals for the means.
- Prose reference: the phase 22/25 corpora spelled as `fam_data.english` does (greedy digraphs, IO -> IA), punctuation as clause marks in two schemes ('sentence' = . ! ?; 'clause' = . , ; : ! ?), paragraph = blank-line block, 300 random windows of LP1's and LP2's rune count; z and percentile of LP1 / LP2 among the windows (16 statistics per scheme: read z beyond about +-3 as real).
- Step 3: LP1 clauses' prime-value sums (decrypted, `lp.PRIME`): share odd and prime, against the prose windows; clause rune count parity and mod 2, 3, 5 uniformity for LP1 and LP2 (Monte Carlo chi2).
- Light CPU, one thread, below-normal priority.

## 2. Results (`results/analysis/phase64_clause_structure.txt`; 30 CPU-s)

**LP1 vs LP2: different.** Mean clause 31.8 runes (LP1) vs 77.5 (LP2), 7.9 vs 17.3 words, median 26 vs 57, KS D 0.38; all P 0.0002 (Holm 0.0018). LP2's clauses are 2.4 times longer, and 52 of its 167 clauses have 100+ runes (LP1: none; its longest is 99).
Not different (Holm > 0.2): CV of length (0.68 vs 0.95), share of one-word clauses (5.7% vs 1.2%, P 0.05), clauses per paragraph (6.8 vs 11.9; 13 and 14 paragraphs, little power), odd rune counts (0.56 vs 0.49). Clause-end position: **(last word - mean word) is +1.49 runes in LP1 and -0.25 in LP2 (P 0.0002)**. Clause marks fall directly before a line / page break in 28% (LP1) and 19% (LP2) of cases against 24% line breaks per word space in LP1.

**Against ordinary English.** LP1 looks like prose: every statistic within about 1.5 sd under both schemes (mean clause 31.8 runes sits at z +0.5 of prose divided at commas and z -1.4 of prose divided at sentence ends: its marks are comma-sized; last-word statistic +0.4 sd). LP2's mean clause length (77.5 runes, 17.3 words) is like prose SENTENCES (88.9 +- 32.9, z -0.3) and 7.9 sd above prose divided at commas (29.4 +- 6.1).
The clause-end statistic is the one that separates LP2 from prose: the word before a clause mark is 1.2-1.4 runes longer than the average word in English (clause scheme +1.42, sentence +1.34; LP1 +1.49) but -0.25 in LP2: z -3.7 (sentence) and -6.6 (clause), below all 300 windows. Clauses per paragraph (z +2.6) and CV of length (z +2.6, clause scheme) are weaker, with only 14 paragraphs.
The clause-final word of LP2 is not longer than the others, as expected if the marks are not tied to the words the way English punctuation is (random runes under the word-length model also give 0).

**Prime-sum trace in lengths (step 3).** With this clause definition 57 of 88 LP1 clauses (0.65) have an odd rune-prime sum and 39 (0.44) a prime sum; prose windows: 0.50 +- 0.08 odd (z +1.7: weak; the clause definition may differ from the authors', test 4 covers the sums). The rune COUNT of the clause shows no trace: odd counts LP1 0.56 (n 88), LP2 0.49 (P 0.76 against 1/2); length mod 2, 3, 5 uniform in LP1 (P 0.34, 0.94, 0.36). LP2 length mod 5: [23, 49, 25, 37, 33], chi2 13.0, P 0.011 (0.07 Bonferroni over the 6 length tests): not significant, listed for the record.

**Reading.** LP2 does not look like LP1: its clauses are 2.4 times longer, like prose sentences, while LP1's are comma-sized; and its clause-final words are not longer than average, unlike both LP1 and English. LP2 is "like neither": sentence-length in clause size, no end-of-clause word-length signature. No length trace of prime-sum authoring appears in either section.

## 3. What is NOT excluded
The clause marks of LP2 may be placed by a rule that does not look at the plaintext's words (the missing end-of-clause signature does not exclude English underneath it: rune words under R4 with extra runes would also dilute it); the authors' LP1 mark definition may be sentence-based only (then the LP1 prose comparison changes); 13 and 14 paragraphs give almost no power for clauses per paragraph; the prose reference is 19th-century and older English from six books, spelled with the project's digraph rule; no test of clause-end letters (only the word length), of marks at line / page ends (layout confounded), or of clause sums (test 4).
