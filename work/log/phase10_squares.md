# The two magic squares: an outside LLM's number leads, checked (2026-10-17, 23:25)

Scope: the book's number grids, not LP2's ciphertext. **Nothing in LP2 is solved.** A DeepSeek answer (third-party text, kept out of the repository) argued that the key is built from the book's own numbers and listed number facts about the two squares as leads.
`work/squares_check.py` -> `results/analysis/squares_check.txt` recomputes them. **Every number it quoted is true:**

- Both squares are 5x5, magic (all rows, columns and both diagonals sum to 1033 for the 0.2 grid and 3301 for the 0.6 / page-14 square) and **centrally symmetric (c[i][j] = c[4-i][4-j]) with 13 distinct values** (12 pairs and the centre). The same template, with different
  numbers and sums. The repository had recorded 'both are magic squares' only; this shared template was not noted (no earlier mention in the docs or logs). It suggests one construction recipe with two inputs, the first with known inputs (Gematria sums of the 0.2 words and numbers).
- pi(1033) = 174 = 6 x 29 and pi(3301) = 464 = 16 x 29 (1033 is the 174th prime, 3301 the 464th). The 140th prime is 809, the centre of the 0.6 square; sigma(139) = 140.
- Four values of the 0.6 square have a prime factor above 109, so are not products of Gematria Primus primes: 278 = 2 x 139, 626 = 2 x 313, 934 = 2 x 467, 809; 139 + 313 + 467 + 809 = 1728 = 12^3, and 3301 - 1728 = 1573 = 11^2 x 13. phi(278) = 138 and phi(626) = 312 are numbers of the 0.2 and 0.6 squares.
- The cuneiform numerals read 17,13 and 55,1 in base 60 = 1033 and 3301 (already in `research_2026-10-17.md`).

**What this does and does not establish.** None of it decrypts anything or defines a key stream. The facts are post hoc: the pool of properties one can check on a handful of integers is large (index multiples of any small number, factorisations, sums of subsets, perfect cubes). For the index fact, with
about 10 candidate properties, the chance that two given primes both show one is about 10 / 29^2 = 1%; the base rate in 1000..4000 is the expected 1/29 (13 of 382 primes). It is a curiosity with a small chance probability, not evidence about LP2. The shared template of the two squares is the one structural observation here: a
construction can be learned from the square whose inputs are known (0.2) and applied to the other, which would then be a recipe the book prints just before the ciphertext. Not attempted.

**Already covered, so not new:** the squares' rows and columns, the 1033 square and the page-30 grid as cyclic keys (library); any key of period up to about 400 (so the 25-cycle of phi or sigma of the 25 square values, and similar) by the drift-period scan, which is key-agnostic; per-section screens of the whole library including 0.14.
**Open and cheap (not built):** phi, sigma and d of the progressions 3301 i + 1033 and 1033 i + 3301; prime streams p_(k i) with k from the index facts (58, 87, 116, 174, 348, 464, ...; decimations up to 29 are already covered by `kscreen-hyp`); numbers derived from 45415 (the proposal's reading of FIRFUMFERENFE, unsupported). **Open and expensive:** the tableau (H2) built from the square, which needs the drift-tracking engine; sign flips by word length, sum or parity.
