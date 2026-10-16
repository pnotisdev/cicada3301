# Page-30 grid and caption 0.10 (2026-10-16)

## Solved: how the grid is built
The page-30 grid (segment 0.10) is 4×4. **Every cell equals |3301 − p_k|**, where p_k is the k-th prime and

- k = 1, 2, 3, 4, 6, 9, 14, 22, 35, 56, 90, 145, 234, 378, 611, 988
  (each step between consecutive k is a Fibonacci number: 1, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377),
- p_k = 2, 3, 5, 7, 13, 23, 43, 79, 149, 263, 463, 829, 1481, 2593, 4507, 7817,
- written as a **clockwise spiral**. It starts right of centre at row 2, col 2 (value 3299 = 3301 − 2) and ends at
  the bottom-left corner.

Rank of each cell in the sequence:
```
 6  7  8  9
 5  0  1 10
 4  3  2 11
15 14 13 12
```
The bottom row looked anomalous only because its last two primes are larger than 3301: 4507 − 3301 = 1206 and
7817 − 3301 = 4516. All 16 cells are reproduced exactly (`python work/grid30.py`, `tests/test_grid30.py`).

## Tested and negative
- **Caption ᚠᚢᛚᛗ ᚪᛠᚣᛟᚪ as ciphertext.** I tried keys from the sequence (primes, indices, grid values in both
  orders, primes − 1, Fibonacci, 3301 digits) at every placement, with ± sign, Atbash and all 29 shifts: 5,568
  placements. None gives two dictionary words (about 0.3 expected by chance). The first caption word does have
  Gematria sum 149, which is p_35, a member of the sequence.
- **Grid as a 4×4 Hill-cipher matrix mod 29** (grid, transposed, primes in spiral cells; matrix and inverse; left
  and right multiplication; 4 block offsets; all unsolved segments; 384 variants). Best dictionary score 0.071,
  which is noise (real English about 0.7).
- **Grid numbers as Gematria sums** of unsolved words, clauses, lines and pages: no excess over random target sets
  (words of 2+ runes: 19 hits against 19.9 ± 5.3).
- **Sequence primes and indices as positions** in the unsolved rune stream, the word list, and each segment
  (0- and 1-based): nothing readable.
- **As a long keystream:** the sequence grows too fast to be one. Its slowly growing parts (Fibonacci-step
  indices; 3301 − p_n) reduce mod 29 to sequences already covered by screens 1 and 2.

## Open
- What the grid is for. It may be a signature, or a hint at "primes, Fibonacci, spiral" as the method on other
  pages. The caption ᚠᚢᛚᛗ ᚪᛠᚣᛟᚪ remains unexplained.
