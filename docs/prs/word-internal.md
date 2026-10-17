# PR: word-internal structure: lag-5 repeated bigrams, and a dictionary test that excludes per-word algebraic keys

**Branch:** `research/word-internal-lag5` (new files only; based on `main` at 72fdf50)

## What this adds
- `work/word_internal_repeats.py` -> `results/analysis/word_internal_repeats.txt`
- `work/word_key_dictionary.py` -> `results/analysis/word_key_dictionary.txt` (19 s)
- `work/tests/test_word_internal.py` (3 tests, 1 s)

## 1. The distance-5 echo is clustered (new evidence beyond `within_word.py`)
`within_word.py` found +3.7 sigma at distance 5 (102 equal pairs of 2,073). The same excess shows up as **repeated
bigrams**: inside words, the bigram at positions (j, j+1) equals the one at (j+5, j+6) **9 times against 1.51 expected**
(Poisson P = 3e-5; a chain-null Monte Carlo with LP2's word structure and doublet rate gives P < 5e-5 in 20,000
streams; x8 for the 8 lags looked at). Lags 2-4 and 6-9 are at chance (7/3.8, 4/2.5, 0/0.85, 1/0.45, 0, 0). Bigram
windows that are not inside one word are at chance too (20 observed, 13.9 expected). The eight words are listed in the
results file; one of them (SDING..SDING) repeats a trigram, and several are 8-10 runes long.

Yardstick: English written in runes has the same internal structure at lag 5 (coincidence 6.4%, bigram-repeat ratio
6.1x chance); LP2's bigram ratio at lag 5 is 6.0x, its coincidence rate is 4.9% (chance 3.5%).

## 2. But it is not a per-word key (dictionary test with controls)
If a word is enciphered c_j = p_j + k_j with a key that has algebraic structure inside the word, the key cancels in a
difference operator and the ciphertext word must be *consistent* with its English plaintext:
Delta(c) = Delta(p) (mod 29). `word_key_dictionary.py` checks every LP2 word against every dictionary word of the same
length (20k-word list spelled in runes, 12,135 spellings) for the families: key constant per word (Caesar shift per
word), arithmetic progression, quadratic (any coefficients, new ones for every word), and a fresh key vector of period
2..7 restarted at every word.

- **LP2: no word of 6+ runes is consistent for any family** beyond the random surrogate (e.g. period 5: 12/159 words of 8
  runes, the surrogate has 11/159, then 0/77, 0/51, 0/28, 0/18).
- **Controls:** dictionary words enciphered under each model are recovered for 70-100% of words (50-70% with extra
  key-pointer jumps of 0.05 per rune, which an anti-repeat rule causes); the dictionary holds 40-86% of English word
  tokens, so a true model would have given many dozens of hits among LP2's 8-12-rune words.
- So the distance-5 echo is **not** a per-word period-5 key, and the same holds for constant, linear, quadratic or
  periodic keys of period <= 7, for English plaintext in the dictionary. (An unknown outer alphabet D is the
  `walk dsearch` case; this test assumes the standard rune alphabet.)
- **Per-word linear recurrences** (`work/word_recurrence.py`, results `word_recurrence_d2.txt`, `_d3.txt`): the same
  consistency test for a key that follows a recurrence k_{j+d} = a_1 k_{j+d-1} + ... + a_d k_j with the same
  coefficients for the whole book and a *fresh initial state for every word* (a Fibonacci/Lucas/Tribonacci/LCG-type key
  re-seeded at each word). All 812 order-2 and all 23,548 order-3 coefficient sets are scanned. LP2's best operator
  has 5 consistent words (order 2) and 6 (order 3), the random surrogate's best has 4 and 6. Planted keys with the
  anti-repeat skip rule are recovered with their true operator at rank 1 (656-672/840 and 553-577/720 words
  consistent against a runner-up of 4-25). This family is not covered by the kscreen recurrence campaign, which runs
  one key stream through a whole section.
- Simulations in section E of the repeats results: a per-word random key of period 5 reproduces the bigram clustering
  but predicts a lag-5 difference histogram that LP2 does not have; an independent "copy rune j-5" process does not
  reproduce the clustering. A period-5 key with pointer jumps of 10-20% matches the coincidence rates at lags 4-5, but
  the dictionary test above excludes it directly.

## Relation to prior work (third-party data, read after the fact)
After running the above I found that the cicada-solvers/aldegonde `hypotheses/` notes (`lag5-digraph-structure.md`,
`within-word-key-sharing.md`, `lag5-back-reference.md`, `line-initial-bias.md`) already contain the same observations:
paired lag-5 matches at separations 1 and 4 (29 and 28 against 17.7 expected over the whole stream; our whole-stream
lag-5 bigram-repeat count is the same 29 vs 15.3), a disproof of an *additive* per-word 5-periodic key from the flat
nonzero lag-5 differences, and the line-initial glyph-width artefact. They also note that an *equality-only*
mechanism survives: positions five apart in a word enciphered with the same *mixed (non-additive)* alphabet, so that
equal plaintext letters give equal ciphertext runes and unequal ones scramble. What this PR adds to that picture:
- the localisation inside words (9 vs 1.5 with the bigram windows inside one word, 20 vs 13.9 elsewhere; Monte Carlo
  P < 5e-5), with an English yardstick: the bigram-repeat ratio at lag 5 is 6.0 in LP2 and 6.1 for English written in
  runes. That is what an equality-only, *plaintext-driven* mechanism predicts; an independent copy process gives
  1.9-3.7 at the same coincidence rate (section E), so copy events are disfavoured;
- a direct dictionary test with planted controls that excludes per-word *algebraic* key families (constant, linear,
  quadratic, periodic <= 7, order-2/3 recurrences) for English plaintext, which complements their histogram argument;
- consequence for the equality-only family: a per-word cycle of arbitrary alphabets leaves almost nothing for a
  dictionary to test (only p_j = p_{j+5} versus c_j = c_{j+5}), which is why no existing screen can see it.

## What this means
A real, small, word-internal repetition at distance five that no simple per-word key explains. It constrains models:
whatever generates the key (or the text) makes equal runes five apart inside a word more often than chance, in runs
of two or three, without making the plaintext consistent with a periodic key. Candidates worth testing next:
a key that depends on the word's own ciphertext (feedback with lag 5), or plaintext that is not dictionary English
at those places (names, numbers, repeated syllables).

## For the reviewer
- Check `bigram_pairs` (windows inside one word only) and the expectation S^2 per pair (S = sum of squared rune
  frequencies); `chain_null` draws steps with P(step 0) = 0.0066, which reproduces LP2's doublet rate and uniform
  marginals.
- Check the operators in `family_op` and the control construction in `encipher`.
- No existing file is modified.
