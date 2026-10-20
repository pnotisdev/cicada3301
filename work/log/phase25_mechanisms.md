# Phase 25: one word-aware stateful mechanism for LP2's anomalies together (side session, 2026-10-20)

Nothing in LP2 is solved. Scripts: `work/mech25/measure.py` (statistics; calibration against the logged LP2 numbers: lag 6 in-word 80 / 44.5, z +5.32; lag 5 104 / 73.7; doublets 0.63% in-word),
`work/mech25/sim25.py` (mechanisms M0-M7, 60 replicates x 2 plaintext spellings, random key, English plaintext, LP2's section layout, q = 0.81), `work/mech25/fit_and_predict.py`.
Outputs: `results/analysis/mech25.txt`, `results/analysis/mech25_fit.txt`. No registry/PLAN/STATUS edits (as instructed).

## 1. Already excluded (do not repeat)
| Candidate | Row |
|---|---|
| Periodic / per-word-period-5 twist skeleton (predicts lag 3,4,7,8 excess too) | `periodic`, `skeleton5` |
| Plaintext/ciphertext autokey (lag <= 8), Vigenere, per-word key, progressive/multiplicative/cumulative keys | `fingerprint-families`, `per-word-keys` |
| Affine/nonlinear lag-feedback autokey (6496 settings, 4 scopes); prime-domain feedback | `lag-feedback`, `prime-domain` |
| Plaintext-F replacement, collision twist W3(a) (T of the *previous* rune), autokey chain | `echo-mechanisms` |
| Null rune at word ends (deterministic, 0%/100% of edges); extra key advance per word/line/page break | `nulledge`, `advsep` |
| Small state machines (4,608 rules) | `state-machines` |
| Hold-key repair (M04) as a decodable-by-old-engines mechanism | `m04-baseline` |
| Segmentation depending on the runes; position/length schedules inside words | `segmentation-dependence`, `word-position-schedule` |
| Keyless two-tap echo is NOT excluded (untestable alone) | `echo-two-tap` |
Standing facts that constrain any proposal: the lag-6 excess is entirely the r = 0 cell, rate 0.0275/pair = the avoided-collision rate q/29 = 0.0279; lag-5 excess 0.0144/pair; both zero across word gaps (z +0.01, -0.29).

## 2. Mechanisms simulated (c = p + k, k iid uniform; a "would-be repeat" c_i = c_(i-1) is repaired with probability 0.81)
- M0 base: repair = uniform other rune (skip/coin rule).
- M1 t6: repair writes T(c_(i-6)) = 24 - 2c_(i-6) when the rune 6 back is in the same word (else M0).
- M2 t6c5: in-word repair writes T(c_(i-6)) with share a, c_(i-5) with 1-a (one shared repair budget).
- M3 t6+cp5: M1 plus an independent copy of c_(i-5) at rate 0.015 in words (two rules).
- M4 rewind6: repair re-uses the key value of 6 back (k_i := k_(i-6)).
- M5 ins: repair INSERTS T(c_(i-6)) as an extra rune (plaintext not consumed).
- M6 ctr: word-scoped repair counter: 1st repair in a word writes T(c-6), 2nd copies c-6, then uniform.
- M7 xr6: repair = 2c_(i-1) - c_(i-6), negative control for the relation.
Plaintext: Gutenberg English as runes (digraph spelling) and letter by letter. LP2: doublets 0.66% (in-word 0.63%, gap 0.80%), lag 6 80/44.5 (z +5.32; across +0.01), lag 5 104/73.7 (+3.53; across -0.29), S5 11, uni chi2 26.4, bigram chi2 786, max lag z -2.96.

## 3. Results (means of 60 replicates, digraph plaintext; letters in `mech25.txt` is the same pattern)
| Mech | doublets % (in/gap) | lag6 in hits/exp (z) | lag6 across z | lag5 in hits/exp (z) | S5 | uni / bi chi2 | max lag z | verdict |
|---|---|---|---|---|---|---|---|---|
| LP2 | 0.66 (0.63/0.80) | 80/44.5 (+5.3) | +0.0 | 104/73.7 (+3.5) | 11 | 26.4 / 786 | 2.96 | |
| M0 | 0.65 (0.66/0.63) | 37.0/38.3 (-0.2) | -0.0 | 63.2/64.3 (-0.1) | 2.1 | 27.7 / 754 | 2.6 | doublets only |
| M1 | 0.65 (0.65/0.64) | 66.8/38.3 (+4.6) | -0.2 | 64.6/64.0 (+0.1) | 2.7 | 26.1 / 766 | 2.5 | doublets + lag 6; no lag 5 |
| M2 (a=0.7) | 0.65 (0.65/0.66) | 61.0/38.2 (+3.7) | +0.2 | 91.1/63.8 (+3.4) | 2.8 | 27.6 / 752 | 2.6 | doublets + lag 6 + lag 5 |
| M3 | 0.65 (0.65/0.67) | 67.0/38.0 (+4.7) | +0.3 | 86.6/63.8 (+2.8) | 3.1 | 28.0 / 759 | 2.6 | same, two rules |
| M4 | 0.64 | 39.7/38.3 (+0.2) | -0.2 | 61.9/64.0 (-0.3) | 2.2 | 27.9 / 760 | 2.6 | no echo |
| M5 | 0.65 | 68.0/39.0 (+4.7) | +0.1 | 63.4/64.5 (-0.2) | 2.0 | 25.7 / 756 | 2.5 | as M1; word lengths unchanged |
| M6 | 0.63 | 68.3/39.2 (+4.6) | +0.1 | 65.9/65.4 (+0.1) | 2.3 | 27.5 / 764 | 2.6 | as M1 |
| M7 | 0.67 | 37.9/38.3 (-0.1) | +0.4 | 62.1/64.0 (-0.2) | 1.9 | 26.0 / 755 | 2.5 | control: no echo |
Flat unigrams/bigrams and the lag spectrum are reproduced by every mechanism (LP2's values sit inside the spread; the repairs do not disturb them). The mechanism family reproduces the doublet
deficit (flat over word gaps) and the strictly in-word zero-across-gap behavior by construction.

Budget check (`mech25_fit.txt`, 50 replicates per row): LP2 lag 6 excess 0.0275/pair, lag 5 0.0144/pair. M2 a=1.0: 0.0257 +- 0.0078 / 0.0106 +- 0.0049; a=0.8: 0.0203 +- 0.0077 / 0.0138 +- 0.0052;
a=0.7: 0.0188 +- 0.0070 / 0.0132 +- 0.0049. So one repair budget (q/29 per rune) can carry BOTH echoes within about 1 sd at a = 0.8-1.0 (a=1.0 already gives lag 5 +0.0106 because repairs at word position 5 fall back to copy c-5 in my M2; lag-5 pairs are 1.6x the lag-6 pairs). My prior expectation that the two rates exceed the budget was wrong; the budget does not contradict a joint repair, within the noise (sd 0.005-0.008 per replicate).

## 4. What the family does NOT reproduce
1. **S carries the lag-5 echo (11 of 102, z +5.9 in-word, 4 at word position 0):** every mechanism gives S5 = 2-3 (uniform spread of the echo over source runes). Needing 8.6 excess hits from ~73 S-sourced pairs is 0.12 per pair, four times the collision rate; a collision-triggered repair cannot concentrate on S (the S branch is a selected post-hoc look: `echo_values`: P(uniform-echo plant Q >= LP2) 0.03 with S, 0.52 without).
2. **Word lengths:** no collision-linked mechanism changes them. Repairs act at 2.8% of runes; M5 (insert at repairs) moves the histogram G against LP2 from 260.7 (M0) to 268.6 (digraph) and 85.1 to 81.8 (letters): nothing. The +1-rune-in-42%-of-words fit (G 16.5) and the letter-spelling fit (G ~60) stay unexplained by any repair rule; the sim's letter-spelling G is 77-85 vs LP2 only because of English sample differences (LP2 vs Emerson letters is 60).
3. The lag-6 amplitude of M1 (66.8 vs 80) is 2 sd low; M2 a=0.7 is lower still.

## 5. Prediction for an unmeasured LP2 statistic (M1 / M2 repair)
Repairs are independent collision events, so lag-6 hits should be independent Bernoulli over eligible positions (an autokey chain would cluster them). Measured on LP2: words with >= 2 lag-6 hits 6, hits at consecutive positions 3, total 80.
Shuffle null (300): 1.54 +- 1.21 and 0.80 +- 0.92; M1 plants (150): 4.19 +- 2.19 and 2.40 +- 1.70 (hit-matched subset 5.4 +- 2.2). P(M1 >= LP2) = 0.26 (multi-hit), 0.43 (consecutive); P(M1 <= LP2) = 0.83. LP2 sits inside the mechanism's own spread: the prediction is met, but it is a weak, non-discriminating one (a Bernoulli null predicts the same).

## 6. Verdict
No mechanism reproduces all anomalies (S-carry and word lengths fail for the whole family), so **no Level 2 lead**. What survives is Level 1: a word-aware collision repair that writes a function of the rune 6 back (T(c_-6) = 24 - 2c_-6) reproduces the doublet deficit, the lag-6 relation at the observed size (within ~2 sd), zero excess across word gaps, flat unigram/bigram statistics, and with a shared copy-of-5-back branch (a ~ 0.8) the lag-5 echo size too, from one repair budget. It leaves the S carrier, the word-length histogram and any decryption untouched, the relation was selected post hoc (look-elsewhere P 0.005), and a repair that is a function of c_-6 is not distinguishable from the keyless echo family `echo-two-tap` on LP2 alone.
Caveats: English plaintext only (Emerson/Gutenberg), random iid key (no structured key), 50-60 replicates per cell, q = 0.81 fixed, T6 map and lag 6 taken from the data (not independent).

## 7. (A) The S carrier of the in-word lag-5 echo (scripts `lag5_s.py`, `lag5_s2.py`; outputs `results/analysis/lag5_s.txt`, `lag5_s2.txt`)

**LP2:** in-word lag 5: 2105 pairs, 104 equal (0.0494 against chance 0.0350). Source S: 74 pairs, 11 S,S (0.149 against chance 0.032).
**Look-elsewhere:** S is LP2's largest cell over 29 source runes x lags 2..8 (equality, in-word): z +5.14 (11 hits, 2.3 expected); the shuffle null of that maximum (500 shuffles inside sections): median 2.88, 95th 3.89, max 4.75, so P < 0.002 (0 of 500). Next cells: lag 7 B +2.68, lag 5 P +2.58, lag 5 ING +2.46. Over sources alone (1000 shuffles) P < 0.001. The earlier z 5.86 was against a different expected; the calibrated number is this one. S is not a pure chance maximum over the grid I scanned, but the grid does not include other relations (affine maps), other scopes or this decision to look at runes at all; treat as P of order 0.001-0.01 once those are counted.

**Plaintext side (English before encryption, in-word lag 5, pairs counted per word occurrence):**
| Text | spelling | all-rune equal rate | P(S at i given S at i-5) |
|---|---|---|---|
| Emerson | digraph / letters | 0.0633 / 0.0688 | 0.129 / 0.129 |
| Walden | digraph / letters | 0.0604 / 0.0636 | 0.141 / 0.124 |
| Origin | digraph / letters | 0.0636 / 0.0665 | 0.093 / 0.083 |
| Republic | digraph / letters | 0.0589 / 0.0663 | 0.145 / 0.132 |
English plaintext has NO general lag-5 excess (0.059-0.069 is the letter-chance level) but a 3-4x S,S enrichment: -SELVES, THEMSELVES (40 in Emerson), OURSELVES, SENSES, STATES, STANDS, SUCCESS, SELFISHNESS (476 S..S pairs in Emerson, all from words of shape S _ _ _ _ S). LP2's 0.149 (11/74) equals what English S gives (0.13 x 74 = 9.6), so the S carrier looks like S..S plaintext coincidences surviving encryption. But the 11 words as they stand in LP2 (`lag5_s2.txt`, (d)) are not English-shaped and the later S sits at word positions 5-8 (5,5,5,5,6,6,6,7,8,8,8; 4 earlier S at position 0, per section 3 above).

**Cipher mechanisms that preserve it:**
- Period-5 key inside words (k_i = k_(i-5)) in a fraction f of words: the plaintext coincidences survive as equal CIPHER pairs, but with a uniform value (c = p + k), not as S. Simulated (English, LP2 layout, 60 replicates): overall lag-5 excess/pair f=0.3: +0.0068 +- 0.0052, f=0.6: +0.0147 +- 0.0053 (LP2 +0.0144), f=1: +0.0258; **S,S hits 2.5 / 3.2 / 4.2 (LP2 11)**. So f ~ 0.6 reproduces the overall excess but puts the hits on arbitrary values, not S; it predicts the other 28 sources carry the excess in proportion to the plaintext lag-5 equality rate (flat). The key being periodic in 60% of the words also contradicts `skeleton5` (the excess at lags 3/4/7/8 was absent) only partly: a period-5 key gives no lag 3/4/7/8 relation, so it is not excluded by that row, but it makes lag 10 equality (rate ~0.6 x English lag-10) a prediction; not measured here.
- A literal-S rule (S stays S in a fraction g of S): needs g ~ 0.9-1 to give 8.6 excess hits (g^2 x 9.6 = 8.6), but LP2's S count is 434 against 447 +- 21 flat, which allows g <= 0.04 (2 sd). Excluded by the unigram flatness.
- A collision-style repair (section 3) has budget 0.028 per rune; the S carrier needs 0.116 per S-sourced pair. Excluded (unchanged).
- A rule keyed on the rune value S (e.g. "after an S, the rune 5 later repeats S with probability 0.12") was not simulated as it is a fitted description: it has no mechanism and one free parameter per observed cell.

**Level:** the S,S excess is an out-of-sample-unconfirmed observation (Level 0); the plaintext reading explains the RATE (0.149 vs 0.13) but no simulated cipher keeps it on cipher S. Open: whether S,S at lag 5 appears in the SOLVED pages' ciphertext (not tried, they are a different cipher layer).

## 8. (B) Word lengths: plaintext-side explanations (scripts `wordlen25.py`, `wordlen25b.py`; outputs `results/analysis/wordlen25.txt`, `wordlen25b.txt`)
G of LP2's histogram (2,896 words, bins 1..11, 12+, `work/wordlen.py` g_test, df 11) against the histogram of each corpus under each spelling. Noise floor: G between two random halves of LP2's words has mean 11.3, 95th pct 33.5 (half size), so G > ~25 against a full-size model is a real mismatch.
| Corpus | all digraph | all letters | best of 128 digraph subsets |
|---|---|---|---|
| Emerson (en) | 241.5 | 63.3 | 58.2 (AE, IA) |
| Walden (en) | 241.2 | 75.4 | 75.4 (OE) |
| Republic (en) | 270.6 | 82.0 | 76.4 |
| Beowulf translation (en, modern English) | 272.0 | 70.8 | 64.4 |
| Paradise Lost (en) | 130.6 | 107.2 | 83.1 (TH only) |
| Origin of Species (en) | 345.7 | 182.4 | 122.5 |
| KJV (en, archaic) | 469.7 | 233.3 | 233.3 |
| Latin (Aeneid / Caesar) | 1379 / 1070 | 1609 / 1227 | no better |
| German (Faust), Italian (Dante), Spanish, French | 254, 788, 410, 507 | 260, 673, 446, 523 | 253, 660, 406, 507 |
Findings: (1) letter-by-letter spelling is the best plaintext convention for English, but the best single text (Emerson, the corpus the repo used, G 63) is a genre effect: the same convention gives 71-233 on other English texts, so "G 60" is not a property of English-in-letters. (2) The best of 128 digraph subsets (a 128-way selection) gains only 5 on Emerson. (3) Other languages (Latin, German, Italian, Spanish, French; Welsh not run, no clean word list in the repo) are excluded outright (G 253-1609). (4) Archaic English: the KJV (G 233) is worse; no genuine Old/Middle English text is in the repo (Beowulf is a modern translation), so Old-English spellings are NOT tested. (5) Punctuation/numeral runes kept as runes: not tested (no text model; they would add 1-rune words, but LP2 lacks 1-rune words relative to English letters, 2.9% vs 3.0%, and its deficit is at length 2).
Segmentation and insertion models on Emerson letters (one fitted parameter, df 10): glue short words (<= 2 letters) to the following word with probability 0.175: G 34.8 (p 1.3e-4); +1 rune in 19% of multi-rune words: G 28.9 (p 1.3e-3); for reference, +1 rune in 42% of digraph-spelled words: G 16.5 (p 0.085), the only fit that is not rejected. **No plaintext-side spelling or language fits (best p ~1e-8 for plain spelling, 1e-4 to 1e-3 with one fitted segmentation/insertion parameter on top of letter spelling).** Evidence level: Level 0/1 (measured, controlled by the corpus spread and the half-sample floor); no cipher mechanism proposed here explains it.
