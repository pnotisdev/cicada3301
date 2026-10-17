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

## Evidence 1b: the clause marks do not behave like sentence ends (`work/wordlen_clauses.py`)

| | clauses | words per clause (mean, CV) | first word of a clause | last word | all words |
|---|---|---|---|---|---|
| LP2 | 168 | 19.7, CV **0.94** | 4.02 runes (z +0.7 against shuffled words) | 4.09 | 3.91 |
| solved sections (the Cicadas' own marks) | 95 | 8.7, CV 0.71 | 3.73 (z +0.5) | 4.80 | 3.62 |
| English prose (sentences) | 3,000 | 16.6, CV 0.70 | **3.14 (z -23)** | 5.61 | 4.09 |

English sentences are shorter-starting (THE, IT, WE, A ...), longer-ending and regular (CV 0.7); LP2's clause lengths have a CV of 0.94, close to the
geometric 0.97 of marks laid down at random, and its first and last words are ordinary words. (The solved sections show neither the start effect nor
the regularity strongly with only 95 clauses, so this control is weaker than the PMI one.) Taken with Evidence 1: LP2's separators and clause marks
look like they were laid over a continuous stream by a process that copies an English-like length distribution, not like the plaintext's own.

## Evidence 2: no simple distribution fits the length histogram (`work/wordlen_parametric.py`)

If the lengths were independent draws from a textbook distribution, one would fit: shifted Poisson G = 482, negative binomial 170, discretised
gamma 124, log-normal 85 (p = 1e-14), Weibull 261, geometric mixture 1406 (df 8-10). The English-derived mechanisms of `wordlen_languages.py` fit
far better (G 17-20, p 0.03-0.07). So the histogram is English-derived (fewer 2-rune words, more 7-8-rune words) while the order carries no
information: consistent with English words in an order unrelated to their lengths, or with separators laid on a continuous stream by a process that
copies an English-like length distribution.

Also tried (`work/wordlen_stoplist.py`): English with its N most frequent word types removed (a list of content words in no sentence order). Best G:
Emerson N = 5: 43 (p 1e-5), Walden N = 5: 71, Plato N = 5: 98, Milton N = 0: 125, KJV N = 10: 301; no N gives a fit (the mechanisms above have G 17-20).

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

## Result of the boundary-free sweeps, window 0.7 (`prng-bg`, 07:33-09:55; negative)

All ten generators over every seed (2^32; .NET 2^31), 16 variants each, first 120 runes of section 0.7, score = bigram log-likelihood (10 ln-odds):
py3 1,234 s, java 736 s, php 799 s, glibc 778 s, mt32 1,017 s, msvc 665 s, drand48 720 s, ruby 1,209 s, mt31 970 s, .NET 335 s (the GPU was shared with the
backward-key campaign, so these are slow). **No candidate reaches +300 for any generator**; the best path after 40 runes never exceeds about +60 over
~10^10 seed/variant pairs per generator (a true key is near +300 at 40 runes and +1200 at 120). So a PRNG-seeded pad of these ten generators starting at the
first unsolved rune is excluded under the single-pad, skip/coin, 16-variant model, WITHOUT relying on LP2's word separators (the earlier dictionary-based
negatives for window 0.7 now have this boundary-free confirmation). The all-section version (a fresh seed per section) was started and cut by the 10:00 GPU hand-over; resume with
`python jobs/overnight.py run prng-bg --lane gpu`.
