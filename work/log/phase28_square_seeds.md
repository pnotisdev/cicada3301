# Phase 28: where do the 0.6 square's seeds come from? (registry open item 14)

Nothing in LP2 is solved. This asks whether ONE rule over Cicada numbers generates the 0.6 square's seeds
{809, 434, 312, 966, 1311, 204} and t = (3301 - 809) / 2 = 1246. Code `work/phase28_square_seeds.py`, output
`work/log/phase28_square_seeds_output.txt`. Read first: `work/log/phase10_squares.md`, `results/analysis/squares_check.txt`.

## What the 0.2 grid shows (inputs known)
- The page text before the grid ("SOME WISDOM. THE PRIMES ARE SACRED. THE TOTIENT FUNCTIAN IS SACRED. ALL THINGS SHOULD BE
  ENCRYPTED. CNOW THIS.") has word sums 198, 270, ... and sentence sums 468, 853, 1039, 1237, 157; none is a seed.
- The 0.2 cells that are numbers (18, 130, 138, 226) are p - 1 of the primes 19, 131, 139, 227, and 366 + 1 = 367 is
  prime too (the page names the totient). 5 of the 13 distinct values have v + 1 prime; chance P(>= 5) = 0.08 for random
  values of the same range (20,000 draws). In the 0.6 square 3 of 13 (312, 966, 280) have v + 1 prime: chance P = 0.30.
  Level 0-1: weak, post hoc, not carried over to 0.6.
- The grid's words are a search for words with prescribed sums (SHADOWS/CABAL, ...); so the cell values were chosen first.
  The 7 numbers (M, m, a, b, c, e, f) are free choices of the author; no input on the page determines them.

## Preregistered family (frozen before scoring)
A rule = (source sequence X, stride s in 1..6, offset o, op = op2 o op1 from 14 unary ops {id, phi, sigma, tau, p_n, pi,
next prime, previous prime, +1, -1, x2, half, 3301 - x, 1033 - x}); it outputs the 7 numbers op(X[o + s i]), i = 0..6.
A rule explains a target 7-set {m, a, b, c, e, f, t} if all 7 appear among the outputs (any order). Sources (33): Gematria-prime sums
of the words, clauses and paragraphs of segments 0-6, 16, 17 decrypted with the library keys (the grids themselves
excluded: the 0.2 words/numbers after CNOW THIS and the 25 printed numbers of 0.6 are the TARGET), all solved words/clauses/
sections/cumulative word sums, the first 600 primes, naturals to 1499, Fibonacci, triangular numbers, the 29 Gematria primes,
20 Cicada constants (3301, 1033, 29, 464, 174, 45415, ...). **5,309,640 rules.** (A first run that leaked the printed
numbers as a source reproduced the seeds trivially, 5/7; removed.)

## Results
| Target | best single rule explains | rules at best | calibration (random 7-sets, same size range, 300 each) |
|---|---|---|---|
| 0.6 seeds + t | 3/7 | 7 (all x2(sigma(n)) windows of the naturals, 1 hit-by-chance triple 312, 434, 204) | max hits: 2 in 258, 3 in 41 sets; **P(max >= 3) = 0.14**; never >= 4 |
| 0.2 seeds + t (inputs known) | 2/7 | 1109 | 2 in 57, 3 in 230, 4 in 13; P(max >= 2) = 1.0 |

Positive control: 12 rules drawn from the family and used as targets were recovered 7/7 (undefined/repeated draws skipped).
The family cannot even reproduce the 0.2 grid, whose inputs are on the page. The 0.6 seeds are at chance level for this
family: the best rule (3/7) is matched or beaten by 14% of random sets. A recipe "counts" only with 7/7 and a calibration
better than the 5 in 5.3 million rules a chance 7/7 would need; none exists.

## Verdict
No rule in a 5.3-million-rule family of text-sum, prime, arithmetic and totient-style operations over Cicada numbers produces
the 0.6 seeds and t, nor the 0.2 grid's own seeds; the best partial hits are at chance. The 0.2 seeds look like free author
choices, so a recipe learned from them has nothing to learn from; the "learn from 0.2, apply to 0.6" route is closed for this
family. **Level 1 (negative, bounded by the family).** Not excluded: recipes using inputs outside the family (e.g. other
books, the images, a hidden parameter), rules that need >2 composed ops or binary combinations of two sources, or seeds
that are simply chosen.
