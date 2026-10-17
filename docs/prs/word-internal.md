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
- Simulations in section E of the repeats results: a per-word random key of period 5 reproduces the bigram clustering
  but predicts a lag-5 difference histogram that LP2 does not have; an independent "copy rune j-5" process does not
  reproduce the clustering. A period-5 key with pointer jumps of 10-20% matches the coincidence rates at lags 4-5, but
  the dictionary test above excludes it directly.

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

## Review (stronger-model pass, 2026-10-17)

Merged locally; the branch's tests were rewritten before anything was run. Both scripts were then re-run and
reproduce the committed result files byte for byte (`word_key_dictionary.py` 12 s, `word_internal_repeats.py
--reps 20000` 53 s). Findings:
- **The lag-5 clustering replicates with code that does not use the branch's counters** (`work/lag5_check.py`,
  `results/analysis/lag5_check.txt`): inside words, 9 repeated bigrams at lag 5 against 1.51 expected. Three nulls:
  analytic Poisson (3.0e-5), a permutation null that shuffles the runes inside each section (10,000 shuffles: 1 in
  10,001 reaches 9 at lag 5; after the look-elsewhere over lags 2-8, P < 1.1e-4, the limit of the resolution), and a
  null that conditions on the observed coincidences: of the 66 lag-5 coincidences whose next position is still inside
  the word, 9 (13.6%) are followed by another coincidence, against 3.5% by chance (binomial P = 4.4e-4; if the
  baseline is the observed lag-5 rate 4.9% instead, P is about 4e-3). So the excess is in the clustering, not only in
  the higher coincidence rate. The bigger the conditioning, the weaker: the honest summary is P of 1e-4 to 4e-3
  depending on the null, before the look-elsewhere over how the data were sliced. One signal, small numbers (9 events).
- **Where it sits** (`lag5_position.txt`, `lag_by_length.txt`, `lag5_len10_words.txt`, exploratory slicing, so read the
  p-values as descriptive): the lag-5 coincidence rate rises mildly with the start position j (4.3% at j=0 to 6.7% at
  j=4) and is 8.2% (21 of 255, +4.2 sigma) in 10-rune words, where lag 5 is exactly half the word; no other even length
  shows a half-word excess (6: +1.4, 8: +0.9, 12: +0.7, 14: +0.3). 16 of the 51 ten-rune words have a lag-5
  coincidence. Slicing by word length and lag is ~80 cells, so this is a lead for a prespecified test, not a result.
- **The dictionary test is as strong as stated, with one caveat.** Operators, controls and the surrogate are
  correct (new tests: the operators annihilate each key family; a period-5 key is not detected as a constant shift).
  The caveat is that it excludes keys that hold across the whole word. A key that is periodic only inside part of the
  word, or a mixture of words that follow it and words that do not, would pass the "at least one consistent dictionary
  word" screen for most words; the planted rate falls from 70-100% to 50-70% with only 5% pointer jumps. The
  histogram argument (a period-5 key aligned in more than about 25% of the pairs makes the lag-5 differences
  non-flat, which LP2's are not) is the stronger exclusion and I checked its scaling: chi2/df about 17.5 at 15,000
  pairs for a fully aligned key scales to roughly 2.3 at LP2's 2,073 pairs, and to 1.5 at 49% alignment, against 0.96
  +- 0.27 observed.
- **Mixed evidence on alignment.** The coincidence rate says about half of the lag-5 pairs behave like English
  (4.9% between chance 3.5% and English 6.4%); the bigram ratio says all of them (6.0 against English 6.1). These are
  roughly 2 sigma apart, so the data fit a copy process that comes in runs of two to three better than either the
  branch's per-rune copy model or a per-word key.
- **Tests rewritten** (8 tests, 0.5 s): both counters against a brute-force count on a 3-letter alphabet, the branch's
  counter against ours, a planted copy-run control (2% of long words) that must give P < 1e-4, a random-word null that
  must stay above 1e-3 over five seeds, the algebra of the key families, planted dictionary keys found and a wrong
  family not found, and the chain null's doublet rate.
- **Not done:** a prespecified test of the half-word hypothesis on fresh data (LP1 plaintexts are English, not
  comparable); a model with copy runs fitted to coincidence rate, bigram ratio and the flat difference histogram
  together.
