# Phase 9: which cipher families can produce LP2's statistical fingerprint? (2026-10-17, 12:20)

Every key search so far assumed a family and looked for its key. This study asks the other question: which families can produce LP2's statistics at all, before any key search.
Code: `work/families/` (`fam_data.py` real LP2 and English plaintext, `fam_fingerprint.py` the statistics, `fam_sims.py` the simulators, `run_families.py` the table,
`lag5_affine.py` a side scan); gate `work/tests/test_families.py` (6 tests, pass); results `results/analysis/families.txt`, `results/analysis/lag5_affine.txt`.

## Method

- **Fingerprint** (computed identically on the real text and on every simulated replicate; pairs never cross a section; LP2 = sections 0.7-0.15, 12,956 runes, 2,928 words by
  `lp.word_spans`). Real values: IoC 1.000; doublets inside words 0.628% (63 of 10,028) and across word seams 0.788%; within-word lag-5 z +3.65 (102 equal of 2,073); largest
  |z| of the other within-word lags 1.99; largest per-rune Poisson z of the lag-5 coincidences ('maxz5') 4.22 (rune S); repeated word types of 3+ runes 15; largest IoC of the
  lag-m differences (m = 1..8) 1.024; largest lag z over lags 2..40 1.49; IoC of word-initial runes 0.998. The gate reproduces the project's own counts
  (`within_word.txt`: 63 / 10,028 and 102 / 2,073).
- **Plaintext:** English as runes (greedy digraphs, IO -> IA) from six Gutenberg texts (1.6 million runes, git-ignored `work/ref/corpora`), windows of 12,956 runes with LP2's section
  structure. **Segmentation:** 'lp2' imposes LP2's word cuts on the English rune stream; 'natural' keeps the English words. The lag-1 correlation of adjacent word lengths is -0.008
  for LP2 and -0.149 +- 0.033 for English words in the same sections (LP2 is 4 sd away), so the separators are not English word boundaries and the 'lp2' table is the one to read
  (the 'natural' table agrees on every conclusion below).
- **Families (25 rows, 100 replicates each):** random runes; plain English; one substitution alphabet; Vigenere with period 3, 11, 29, 97; additive random running key with avoid-repeat
  probability q = 0, 0.5, 0.81, 1 (any structureless keystream is this class); plaintext autokey m = 1, 5; ciphertext autokey m = 1, 5; the same key by position in the word;
  'alphawalk': a fresh random alphabet for each of p phases inside every word (p = 4, 5, 6), the phase advancing when the rune would repeat its predecessor (skip on repeat, probability q per
  rune, 0 or 0.81); 'echo': running key (q = 0.81) plus a copy c_i = c_(i-5) inside words with probability 0.005, 0.015, 0.03 (a calibration of the lag-5 effect size, not a cipher).
- **Reproduced** = the real LP2 value lies within 2.5 standard deviations of the replicates, per statistic. A nearest-centroid classifier (train on half the replicates, test on the other
  half) shows what the fingerprint can separate; the lag-5 statistics are calibrated against 1,500 random texts and 1,500 shuffles of LP2's own runes.

**A bug caught on the way (disclosed).** The first full run's `alphawalk` rows with q = 0.81 had a doublet rate of 0.13% instead of 0.66%: the retry loop stopped as soon as no replicate
needed a skip, so the effective skip probability depended on the number of replicates (it was right at 8 replicates and wrong at 100). Fixed (one coin per rune), regression test added
(`test_alphawalk_skip_probability_does_not_depend_on_the_number_of_replicates`, at 3 and 100 replicates); the table below is the corrected run.

## Result (segmentation 'lp2', 100 replicates per row)

| family | reproduced | fails |
|---|---|---|
| random runes | 6/10 | doublets (0.63% against 3.5%), z5, maxz5 |
| plain English; one substitution alphabet | 1/10 | IoC 1.78, repeated words 142, lag spectrum, word-initial IoC |
| Vigenere L = 3 / 11 / 29 | 2-5/10 | lag spectrum (z 12-16 against 1.5), doublets; L = 3 also IoC and repeated words |
| Vigenere L = 97; additive running key q = 0 / 0.5 | 6/10 | doublets (not removed), z5, maxz5 |
| **additive running key, q = 0.81** | **8/10** | z5, maxz5 |
| additive running key, q = 1 | 6/10 | doublets (none at all, 0 against 0.63%), z5, maxz5 |
| plaintext autokey m = 1 | 4/10 | IoC 1.12, doublets 4.3%, repeated words 66, word-initial IoC |
| plaintext autokey m = 5 | 6/10 | doublets, lag spectrum (z 15) |
| ciphertext autokey m = 1 / 5 | 4-5/10 | lag-m difference IoC 1.78 (against 1.02), doublets, z5 |
| key by position in the word | 4/10 | IoC, repeated words 144, word-initial IoC 1.78 |
| alphawalk p = 4 / 6, q = 0 | 5/10 | doublets, z5 (excess moves to lag 4 / 6, zoth 7.2 / 5.5) |
| alphawalk p = 4, q = 0.81 | 7/10 | z5 (-0.4), zoth 6.5, maxz5 |
| alphawalk p = 6, q = 0.81 | 8/10 | z5 (+0.8), maxz5 |
| alphawalk p = 5, q = 0 | 7/10 | doublets, maxz5 |
| **alphawalk p = 5, q = 0.81** | **9/10** | maxz5 |
| echo 0.005 / 0.015 / 0.03 (q = 0.81) | 8 / 9 / 9 of 10 | maxz5 (and z5 for 0.005) |

1. **A structureless additive key is one equivalence class.** Any PRNG, hash stream, OEIS sequence or book-code key without structure gives 'random + avoid-repeat'; the fingerprint
   cannot tell them apart (random and q = 0 are identical by construction, which is why the classifier cannot separate them; overall accuracy 0.79 over 25 rows). Only decryption tests
   can discriminate keystream sources, which is what the sweeps do.
2. **Families the fingerprint excludes** (three or more constraints failed with large margins): plaintext and ciphertext autokeys, a single alphabet, a per-word key, Vigenere with period
   3, 11 or 29 (periods 97 and longer are the business of the periodicity scans, which stop at about 400 runes).
3. **The doublet deficit needs an explicit avoid-repeat rule at about 81%**; no family produces it natively (q = 0 gives 3.45%; q = 1 gives none, LP2 has 0.63%). The rate is the same
   inside words and across seams, which is what the stream-level rule gives.
4. **The within-word lag-5 effect** is reproduced by period-5 alphabets per word with skip-on-repeat (z5 about 5.9 in simulation against 3.65 real, inside 2.5 sd; the real effect is
   about 60% of a clean period-5 leak) and by a lag-5 copy probability of about 0.015 (z5 +3.6). Period 4 and 6 do not give lag 5 (z5 -0.4 and +0.8, zoth 6.5 and 4.2), so the lag
   specificity of the real effect (z4, z6 at chance) matches period 5. The fingerprint sees a copy probability of 0.015 in 70% of replicates, 0.03 in all, 0.005 in 2%.
5. **Nothing that otherwise fits reproduces the concentration of the echo on one rune (maxz5):** every row that passes the other statistics fails it (z +2.5 to +3.9); the three rows not flagged on it (Vigenere L = 11, plaintext autokey m = 1, per-word key; wide maxz5 spread) each fail four or five other statistics. Calibrated chance of maxz5 >= 4.22 under a random text with LP2's
   word structure and under LP2's own runes shuffled inside sections: 0.0073 (the earlier Poisson estimate, P 3e-5 per rune cell times 232 cells, agrees); z5 >= 3.65 was never reached in 1,500
   draws, so the pair is below 1/1500. Random per-word alphabets cannot concentrate coincidences on a cipher rune; a mechanism has to contain a fixed element (S).
6. **Where the real LP2 sits:** nearest rows (squared standardised distance) echo 0.015 (11.2), echo 0.005 (14.4), alphawalk p = 5, q = 0.81 (15.6), additive key q = 0.81 (19.1).

## Side scan: affine relations between runes at a fixed distance (`work/families/lag5_affine.py`)

For lags 1..8 and the 812 relations c' = a c + b (mod 29) on within-word pairs (equality is a = 1, b = 0), calibrated on 1,000 shuffles of LP2 inside sections:

- Lag 5: equality is the leading named relation (z +3.59); the best of 812 is z +3.85 (P 0.10), so the lag-5 effect looks like an equality echo, not another relation.
- **Lag 6: c' = 27 c + 24 (that is c' = 24 - 2c) has z +5.04 (77 pairs against 43.7 expected), P = 0.002 for the best of 812 at that lag and P = 0.013 over all 8 lags.** The excess is
  diffuse (14 of the 29 rune pairs carry 3 or more), specific to lag 6 (the same relation at lags 4, 5, 7: 118 / 110, 58 / 71.5, 22 / 24.6), positive in all eight sections (z +0.9 to +2.8).
  Split-half replication (best relation of four sections scored in the other four, 70 directed splits): mean held-out z +0.54 against a shuffle null 0.00 +- 0.29 (P 0.035); the lag-6 relation is
  the half-best in 20% of the splits. It is exploratory (found by searching 6,500 relations on the data), unreplicated, and no cipher model here predicts it: treat it as a lead only.

## Limits

English plaintext only; additive, alphabet-per-phase and feedback families only (a small parameter grid); the classifier uses the same statistics. The fingerprint is a screen for families,
not a test of any key. A family that passes all ten statistics except the S concentration is not thereby supported: the table says what each family cannot do.

## Next

A mechanism family that contains a fixed element (alphabets that share S, or an affine step between phases) and is tested for BOTH the lag-5 S concentration and the lag-6 relation; the
prediction must be written down before it is run. Until then the search side (the seed and stream sweeps) is unaffected: it needs a decryption test either way.
