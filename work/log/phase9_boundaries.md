# Phase 9: are LP2's word separators the plaintext's word boundaries? (2026-10-17, ~07:30)

**Why it matters.** Every dictionary-based search in this project (the phpmt seed sweeps `prng-all`, `prng-more`; the dictionary screens of `rescreen`;
`dsearch`) scores a decoded window by counting dictionary words that sit exactly between the transcription's word separators. If the separators are
not the plaintext's word boundaries, a true key would decode to English that is cut at the wrong places, and those searches could not see it. The
IoC-based screens (`kscreen-*`, `kscreen-chain`, `kscreen-step28`, `prng-step`, the periodicity scans) use no boundaries and are unaffected.

## Evidence 1: the word-length sequence has no serial structure (`work/wordlen_adjacency.py`, `results/analysis/wordlen_adjacency.txt`)

In running text adjacent word lengths are correlated (a short function word is followed by a longer word, long words rarely follow long words).
Lag-1 Pearson correlation and mutual information against shuffles inside each section / chunk, and the mean pointwise mutual information of adjacent
length pairs under an English table trained on 40,000 Emerson words:

| sequence | n words | lag-1 r (z) | lag-1 MI (z) | mean PMI under the English table (shuffled null) |
|---|---|---|---|---|
| LP2 unsolved, 0.7-0.15 | 2,928 | -0.008 (-0.4) | 0.0177 (+0.6) | **-0.060** (-0.056 +- 0.007; z -0.7) |
| solved sections 0-6, 16, 17 | 743 | -0.086 (-2.9) | 0.0954 (+2.1) | +0.006 (-0.061 +- 0.016; z **+4.2**) |
| English (Emerson), runes | 3,000 | -0.148 (-8.4) | 0.0644 (+18.6) | held-out English **+0.050** |
| English KJV / Walden / Milton, runes | 3,000 each | -0.17 / -0.12 / -0.11 (z -6.5 to -10) | z +8.8 to +15 | |
| Latin (Caesar) / German (Faust, verse) | 3,000 each | -0.044 (-2.4) / -0.007 (-0.6) | +2.2 / +6.0 | |

The solved sections (words placed by the Cicadas) have English-like serial structure; LP2 has none. An English-like LP2 would score about +0.05 on
the last column, LP2 scores -0.060 (about 15 standard deviations lower). German verse shows that a language can have a weak lag-1 correlation but it
still shows mutual information (z +6); LP2 shows neither.

## Evidence 2: no simple distribution fits the length histogram (`work/wordlen_parametric.py`)

If the lengths were independent draws from a textbook distribution, one would fit: shifted Poisson G = 482, negative binomial 170, discretised
gamma 124, log-normal 85 (p = 1e-14), Weibull 261, geometric mixture 1406 (df 8-10). The English-derived mechanisms of `wordlen_languages.py` fit
far better (G 17-20, p 0.03-0.07). So the histogram is English-derived (fewer 2-rune words, more 7-8-rune words) while the order carries no
information: consistent with English words in an order unrelated to their lengths, or with separators laid on a continuous stream by a process that
copies an English-like length distribution.

## Evidence 3: what it does to the sweeps (the consequence test)

English (Emerson, 395 runes) enciphered under PHP mt_rand seed 777777 (map 0, model 1), swept over 150,000 seeds with the Rust engine:

| word separators of the window | planted seed's best score | best score of any other seed |
|---|---|---|
| the English words' own | **33** | 11 |
| LP2 section 0.7's word lengths imposed on the same runes | **0** | 8 |

(`work/tmp/boundary_test/`.) The dictionary score is blind to a true key if LP2's separators are not word boundaries. Everything that rests on it
(prng-all: PHP, glibc, .NET; prng-more window 0.7: py3, mt32, mt31, java, msvc, drand48, ruby; rescreen; dsearch) is then a non-result, not a negative.

## Evidence against (be fair)

The lag-5 repeated-bigram excess (`docs/prs/word-internal.md`) sits inside words: 9 against 1.5 expected in windows lying inside one word, 20 against
13.9 in the other windows. If the separators were random cuts of a stream, the echo should not prefer within-word windows (about 10% of all windows);
7.5 of the 13.5 excess pairs fall in them (P about 0.003 by Poisson, if the within-word windows were a random tenth of all windows). So the separators are not independent of the cipher structure either. The two
observations (no serial structure in lengths, an echo that respects the separators) are not yet reconciled; shuffled word ORDER with intact words
would explain the first and keep the dictionary score working.

## Remedy

`work/phpmt/bg.py` + `bgmt.cu` (generated from phpmt.cu by `make_bgmt.py`): the same ten generators, key maps, 16 variants and skip/coin beam, but the
score is the log-likelihood ratio of the decoded window (120 runes) under an English rune-bigram table (`data/bigram.txt`, 10 ln-odds, trained on
Emerson), no separators. A true key scores about +10 per rune, a wrong one about -12. Gates (`work/tests/test_bgmt.py`): generator section identical to
phpmt.cu's, every score of every variant equals a Python reference on the Rust key values, a planted seed is recovered at rank 1 for all ten generators,
random ciphertext gives no candidate. 2^32 seeds take 6-17 minutes per generator and window on the 2080 Ti. Campaign `prng-bg`.
