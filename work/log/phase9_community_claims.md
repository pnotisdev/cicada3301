# Phase 9: community claims handed over on 2026-10-17 (729 matrix, page numerology, the 'FIND YOU ARE' crib)

Third-party material. Read as data; none of its code was run and none of its files is committed. The PDFs ("27 x 27", "Matrix-Onion Volume 1", "Wow") were converted
to text in the scratchpad only. All numbers below come from the scripts named in each section; outputs are in `results/analysis/`.

## 0. What was read

| source | what it claims | testable here? |
|---|---|---|
| repo "27x27 Map, 3-Rune Nodes, Totient Decryption" (README, `rules/01-03`) and the PDF "27 x 27" | the first 729 runes (section 0.7) are a 27 x 27 grid, 13 shells + centre; mirrored 3-rune nodes, phi / Moebius phases, walk rule; 'AS I GO, THE WEATHER TURNS COLD' | only the layout; the walk distance rule is stated to be undefined ("which distance to use"), the repo has no test or control |
| PDFs "Matrix-Onion Volume 1" and "Wow" | a 154-rune crib for the start of 0.7: heading DIVINITY WITHIN, body 'FIND YOU ARE NECESSARILY ALONE WHEN YOU ARE BORN AND CANNOT COMMUNICATE IT IN ANY WAY FOREVER AFTER REMEMBER TO THINK OF ALL YOU VALUE IN ONE WORD JUST RECITE YOUR ANSWER NOW'; Fibonacci key, 4 x 4 key matrices, totient / checksum identities | yes (arithmetic is exact; the evidence is selection-prone) |
| a post: 2016 hint image 563 x 569 px = row / column sums of the 121-rune page, 1,136-byte OutGuess payload = a 5 x 5 ring sum; two tree pages 121 and 76 runes; DJUBEI -> TRUTH; OFLOENG -> EARTH | numerology on page grids and page differences | yes (hint dimensions, payload size and which pages carry a tree are premises I cannot check here) |
| `murphyaidanbusiness-ux/liberprimus` | a 14-lane AI campaign (A-N), all null, with planted-key controls; six structural constraints | cross-check of our results; see section 4 |
| `HhWolfling/Gematria-Primus-Lattice-Resonance` | a "matrix engine" (1033 Newton node, toroidal harmonics, 64 Hz pilot tone); no finding, no statistic, no null | nothing to test |
| `ToldByNun/Parcae` | a C++20 / CUDA toolkit for Z29 cipher search; solved pages as fixtures; no new decryption | no claim to test |
| `Sovi11/kryptos-k4-cryptanalysis` | Kryptos K4 negative-space archive (about 1e9 crib-consistency tests, omnibus statistic with selection accounted for); a short LP status | method only: it says that a statistic needs a chance figure after selection |

## 1. The 27 x 27 layout (`work/grid729_check.py` -> `results/analysis/grid729_check.txt`)

Section 0.7 has exactly 729 runes and its first 27 runes are the first row of the shared grid image (checked). Two keyless tests with shuffle nulls:

- Lag spectrum inside 0.7, lags 1-60: lag 27: 27 equal pairs against 25 expected (z +0.4); lags 26 / 28 / 54 / 56 within |z| 1.6. Lag 1 has the known doublet deficit (4 against 26, z -4.3).
  The largest lag is 35 (42 against 25, z +3.5; the maximum of 59 z-scores exceeds 2.9 in about 5% of cases); in sections 0.8-0.15 together lag 35 gives 413 against 418.7
  (z -0.3): it does not replicate.
- Mirrored triples a-b-a along rows, columns and both diagonals of a width-w grid, w = 20..34, 300 shuffles each: w = 27 has 507 against 513 (z -0.3); no width exceeds |z| 2.1
  (w = 22: 459 against 503, z -2.1). Sensitivity: the same count finds 40 forced mirrors at z +2.1, 100 at +3.2 and 200 at +6.9, so a 27 x 27 layout with fewer than about 100 hidden
  mirrors would not be seen. The test excludes heavy mirroring only.
- The arithmetic of the PDF is right (729 = 27 squared; the 13 shell perimeters 104 - 8r add to 728, plus the centre; GP of DIVINITY WITHIN = GP of A CROSSROADS = 491; 491 and 143 are
  both 27 mod 29), and none of it is evidence: those are identities between numbers chosen after the fact. The walk itself (distance rule undefined, steps chosen from phi values and
  Moebius signs) leaves far too many free choices to be tested as stated; the author calls it unverified.

## 2. Page numerology (`work/page_numerology.py` -> `results/analysis/page_numerology.txt`, seed 11; a second seed gives the same counts within noise)

**A. The 121-rune page** (reproduced exactly: first row 563, first column 569, page 6,045). Shuffles of the page's own runes, 1e6:

| statement | chance |
|---|---|
| first row = 563 and first column = 569 | 2.1e-5 (21 hits; seed 5: 2.7e-5) |
| ANY row = 563 and ANY column = 569 (either order) | 3.0e-3 (6.0e-3) |
| a 5 x 5 circumference = 1136 (the page has exactly one, at row 4, column 4) | 0.009 |
| some k x k circumference, k = 3..11, = 1136 (k = 5 chosen after the fact) | 0.154 |
| pi(1136) = 189 = GP(LAW) | 30 of 9,908 dictionary words have GP sum 189 |

The row / column pair is the one genuinely low number (about 1e-5 for the first row and column; 1e-3 to 1e-2 once the choice of line is free), and it rests on the hint
image being 563 x 569 px, which I could not check. The ring and LAW statements are unremarkable once k and the word are free. Nothing here is a mechanism or decrypts anything.

**B. The two tree pages (121 and 76 runes).** 121 + 76 = 197 is the 45th prime, 121 - 76 = 45 and the side sums 11 + 11 + 4 + 19 = 45 are reproduced. Over all 2,701
pairs of the 74 non-empty page pieces: pi(sum) = difference holds for 9 pairs, side-sum = difference for 37, both for 1 (this pair), against 0.12 expected, so the pair is
unusual among pairs, but the relations were picked knowing it. The 76-rune page does lack O N T Y (GP sum 198) and its last 4 x 19 column sums to 198: the chance of that last
column is 0.012, of some row or column 0.21, and it is the only page with exactly four unused runes. Whether these two are the tree pages is a premise I cannot check.

**C. Page differences** (DJUBEI -> TRUTH, OFLOENG -> EARTH): both occur and give exactly the quoted difference strings. In LP2 (sections 0.7-0.15, 12,956 runes) there are only
5 maximal repeats of 5 or more runes (random expectation about 4); a 9,472-spelling dictionary of 4-9-rune words finds a word in the difference of 2 of them (these two) where
0.5 are expected by chance (about 9% per alignment, both directions); P(2 or more) = 0.07. Both words are 4 runes, both spelled with a digraph split (E-A-R-TH). Under any
additive key the difference of two ciphertexts is the difference of two plaintexts, which no cipher model predicts to spell a word; the result is within chance.

## 3. The 'FIND YOU ARE' crib (`work/crib_matrix_check.py`, `work/crib_fluency_null.py`, `work/crib_exact_lookup.py`)

**Reproduction (positive control for my parsing).** With the heading as the first 13 runes (cipher words of 8 and 5 runes = DIVINITY, WITHIN) and the 141-rune body, K = C - P mod 29
gives FIND 2 1 26 2, YOU 3 8 21, ARE 8 5 13; the block sums 89 / 115 / 230 (= 434) and 491 after CANNOT; the five 4 x 4 matrices (S0 115/17/61/46/32/83 ... S4 192/41/72/62/51/141);
the repeated values 32, 41, 51, 54, 201; exactly five word-aligned 16-rune spans. Every number quoted in the PDFs is reproduced, so the arithmetic is exact.

**What the fit to the word structure really is.** All 32 inner crib word boundaries are cipher separators, but 4 cipher separators fall INSIDE crib words (FOREVER 1+6, THINK 3+1, WORD 2+2,
ANSWER 5+1). If separators are plaintext word boundaries, the crib contradicts them at four places; if not, the 'fit to the preserved word structure' is not a fit to it (my
`phase9_boundaries.md` evidence says LP2's separators carry no English serial structure). Either way a fluent phrase fitting a length pattern is not rare: the most fluent English
sentence with the crib's exact 33 rune lengths (word-bigram model from the Gutenberg texts, Viterbi) scores -3.30 per word; 60 random permutations of those lengths give -3.30 +- 0.08, 58 of 60
windows of 33 consecutive LP2 cipher words at random places give -3.41 +- 0.14, the real location -3.39. The crib phrase itself scores -6.85 (the optimum is a Bible-style
collocation salad, not a meaningful sentence), so the control shows only that fits exist for every pattern, not that the crib is bad.

**The Fibonacci claim is selection.** The first 14 body keys (FIND YOU ARE and the start of NECESSARILY) are all Fibonacci residues mod 29 (10 of 29 residues; 3.4e-7 by chance), but for exactly the same
criterion the FIND slot admits 20 dictionary spellings (CIND, COOL, CORD, DOOR, FIND, FOOD, FOOL, FORD, FOUL, FOUR ...), the YOU slot 28, the ARE slot 39, and the NECESSARILY slot (8 of 11
in the set) 6, so there were 20 x 28 x 39 = 21,840 three-word openings with an equally 'perfect' key. The effect does not persist: only 53 of the remaining 127 body keys are in the set
(chance 44), where a true Fibonacci key would give about 127. For random words of the same rune lengths on the same ciphertext (20,000 draws) the first 14 keys have 4.8 in the set on average
and never 14.

**The matrix network and the checkpoints.** Values repeated across the five matrices: 5 observed, null mean 2.4, P(5 or more) = 0.05 (regions and spans were fixed in advance by the
authors, but the family of statistics tried before is unknown). 491 as a running key sum after CANNOT: the real key averages 10.0 per rune over those 49 runes against 14 for a random
word choice (the expected sum is 686 and 491 never occurred after CANNOT in 20,000 draws), which is the signature of words chosen for small / Fibonacci keys; at any of the 33 word ends 491 occurs in 2.1% of null draws.
Plaintext = ciphertext at 6 positions (K = 0) against 4.9 expected.

**An exact test the crib allows** (`crib_exact_lookup.py`). A known key can be looked up exactly: a stream m * a(n+o) + b has differences m * (a(n+o+1) - a(n+o)) and the constant b drops out, so
12 key differences are matched against the 13.5 million differences of the 199,088 OEIS sequences (mod 29) under all 28 multipliers; an accidental match has chance 29^-12 per place. Control:
primes at offset 5 x 3 + 11 are found. Heading key (13 values) and five stretches of the body key (up to 37 differences): 0 places. This excludes OEIS (with a shift and a multiplier, no skips)
as the keystream if the crib is right; it does not test the crib.

**Reading.** The crib is a selected phrase: the Fibonacci evidence is explained by the freedom of word choice, the matrix repeats are a 5% event at best, the fit to the word structure is
available for any pattern, and the one place where the crib could be tested independently, a key rule that predicts the next words, is missing (the authors say so: "the ordered
key values are still obtained only after an English candidate is tested"). The heading itself, DIVINITY WITHIN, is a better-motivated guess (the last page says to find the divinity within; the
heading has exactly the 8 + 5 rune lengths; a post-hoc candidate; an 8-then-5 word-length pair opens 0.33% of adjacent word pairs in LP2, so the length match alone is worth about 1 in 300 per candidate phrase tried), but its key [21 27 17 22 26 9 11 3 8 16 16 11 25] has no structure I can find.
A crib of this size is exactly what the exact test above, and the lanes M and N of the AI campaign below, are for; both are negative.

## 4. The AI campaign repo (`murphyaidanbusiness-ux/liberprimus`: README, REPORT.md, research/SYNTHESIS.md only)

Agrees with this project: flat IoC; doublet deficit (86 against 447 expected, 0.66%); repeated cipher words at chance; adjacent word lengths independent; within-word lag-5 echo (4.9% against 3.45%,
z +3.75; ours: carried by rune S, 11 of 102 pairs); 14 lanes null with planted-key controls, among them era PRNGs (G, about 16.9 million streams), hash / KDF streams (B), title cribs at 17
section and 55 page openings (M, about 1.5e9 fragments) and full-position crib dragging (N, about 2e10 fragments, control: a running English key is found from any 20-rune crib).
Where it differs: it concludes that only an evolving-alphabet walk with skip-on-repeat is consistent with all constraints; our boundary-free sweeps assume an additive key with a skip
rule and are not evidence on that family. Its remaining open leads (book-code pointers into Self-Reliance / Liber AL; the glibc / PHP / Java / MSVC cells) are covered here for the PRNGs
(prng-all, prng-more, boundary-free prng-bg for window 0.7), not for book codes. The Kryptos repo's rule that a statistic needs a chance figure after selection is what Sections 2 and 3 apply.

## Standing conclusion

None of the community claims read on 2026-10-17 decrypts anything or survives a selection-aware null as a mechanism. Two numbers stay on the list of oddities, with their caveats: first row 563 / first
column 569 on the 121-rune page (1e-5 for the fixed lines; about 6e-3 for any row and column; hint-image size unchecked), and the unique pair of tree pages satisfying two page-count relations (1 of 2,701 pairs; the
relations were chosen with that pair in view). What would change the picture: a rule that PREDICTS key values (or words) in an independent segment, as the 'Wow' document itself says.
