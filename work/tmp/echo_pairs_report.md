# LP2 echo-pair enumeration and lag-6/lag-5 residual inspection

Scope: LP2 = sections 0.7-0.15 (segment indexes 7..15), 12956 runes, 2896 words (project word cuts, work/lp.word_spans). Scratch outputs in work/tmp/; nothing committed.

## Restated repo facts (cited)

- Lag-6 within-word excess of c' = 24 - 2c mod 29: 80 hits / 1290 pairs, 44.9 expected, z +5.16; cross-word 401/11612, z +0.05 (results/analysis/echo_position.txt:21-23).

- Lag-5 within-word equality: 104/2105, 72.9 expected, z +3.65; carried by S: 11 (S,S) pairs, 2.4 expected, z +5.86 (echo_position.txt:3-4,13).

- Echo-inside-words-only control: the within-word excess reappears with no cross-word spillover, so the signal is consistent with an echo confined to words (echo_position.txt:32-37).

- Lag-6 hit sources concentrated: Q 33.7 vs shuffle 95th pct 24.5; largest sources 7,3,16 (results/analysis/echo_values.txt:3-6). Lag-5: Q 41.9 vs shuffle 95th pct 29.6, largest sources 15,13,21 (echo_values.txt:9-12).

- GP mapping: 0=F 15=S 18=E 24=A, 29 letters (work/lp.py:17-24). IoC = normalised coincidence, random 1.0, English ~1.7-1.9 (work/lp.py:107-115).

## 1. Hit enumeration

- Lag-6 hits enumerated: 80 (must equal 80). Table: work/tmp/echo_pairs_lag6.txt (sec, word_no, word_start, word_len, pair_pos, c1, c2, c1_lat, c2_lat, word_runes, word_latin, ctx_before8, ctx_after8).

- Lag-5 hits enumerated: 104 (must equal 104), of which 11 are (S,S) (must equal 11). Table: work/tmp/echo_pairs_lag5.txt (adds ss flag column).

## 2. Structure checks

### a. Section concentration (null: hits proportional to within-word pairs at risk)

lag-6 chi2 = 1.39, df=8, p = 0.994; pairs 1290, hits 80

| sec | pairs | hits | expected | obs-exp |
|---|---|---|---|---|
| 0.7 | 79 | 6 | 4.90 | +1.1 |
| 0.8 | 106 | 6 | 6.57 | -0.6 |
| 0.9 | 184 | 10 | 11.41 | -1.4 |
| 0.10 | 0 | 0 | 0.00 | +0.0 |
| 0.11 | 178 | 13 | 11.04 | +2.0 |
| 0.12 | 100 | 5 | 6.20 | -1.2 |
| 0.13 | 152 | 11 | 9.43 | +1.6 |
| 0.14 | 154 | 9 | 9.55 | -0.6 |
| 0.15 | 337 | 20 | 20.90 | -0.9 |
| total | | 80 | | |

lag-5 chi2 = 4.32, df=8, p = 0.827; pairs 2105, hits 104

| sec | pairs | hits | expected | obs-exp |
|---|---|---|---|---|
| 0.7 | 135 | 7 | 6.67 | +0.3 |
| 0.8 | 183 | 5 | 9.04 | -4.0 |
| 0.9 | 291 | 18 | 14.38 | +3.6 |
| 0.10 | 0 | 0 | 0.00 | +0.0 |
| 0.11 | 295 | 18 | 14.57 | +3.4 |
| 0.12 | 168 | 8 | 8.30 | -0.3 |
| 0.13 | 241 | 9 | 11.91 | -2.9 |
| 0.14 | 250 | 13 | 12.35 | +0.6 |
| 0.15 | 542 | 26 | 26.78 | -0.8 |
| total | | 104 | | |

### b. Word repetition

- General repetition rate (ciphertext word strings, all 2896 LP2 words): 285 occurrences (9.8%) sit in word strings that appear >= 2 times; 120 distinct repeated strings.

- Lag-6: 74 hit-bearing word occurrences, 0 of them in repeated strings. Repeated hit-bearing words: none

- Lag-5: 93 hit-bearing word occurrences, 0 in repeated strings. Repeated: none

- Length-controlled (hits need L >= lag+1): lag-6 eligible words 559, 0 (0.0%) in repeated strings, hit-bearing 74 with 0 in repeated strings, hypergeometric p(X <= 0) = 1.0000. lag-5: eligible 815, 0 (0.0%) repeated, hit-bearing 93, 0 repeated, p = 1.0000. Independent check: no LP2 ciphertext word of length >= 6 repeats at all, so the 9.8% overall repetition rate lives entirely in short words (L <= 5); the zero repeated hit-bearing words is a length effect, not an echo property.

### c. Word-length distribution of hit-bearing words vs all words

(null per length: binomial P(>=1 hit) = 1 - (28/29)^(L-lag))

| L | words | lag6 hit-bearing | lag6 expected | lag5 hit-bearing | lag5 expected |
|---|---|---|---|---|---|
| 1 | 83 | 0 | 0.00 | 0 | 0.00 |
| 2 | 448 | 0 | 0.00 | 0 | 0.00 |
| 3 | 720 | 0 | 0.00 | 0 | 0.00 |
| 4 | 513 | 0 | 0.00 | 0 | 0.00 |
| 5 | 317 | 0 | 0.00 | 0 | 0.00 |
| 6 | 256 | 0 | 0.00 | 9 | 8.83 |
| 7 | 216 | 8 | 7.45 | 18 | 14.64 |
| 8 | 156 | 21 | 10.57 | 18 | 15.59 |
| 9 | 78 | 18 | 7.79 | 15 | 10.21 |
| 10 | 52 | 6 | 6.81 | 16 | 8.37 |
| 11 | 32 | 13 | 5.15 | 7 | 6.08 |
| 12 | 18 | 6 | 3.42 | 5 | 3.92 |
| 13 | 4 | 1 | 0.87 | 3 | 0.98 |
| 14 | 3 | 1 | 0.73 | 2 | 0.81 |

lag-6 chi2 (cells with expected>=1, df=5) = 37.70, p = 4.3e-07; lag-5 chi2 = 10.79, p = 0.10. Note: long-word excess follows mechanically from the position-in-word effect (a pair at position p needs L >= p+lag+1).

### d. Position of first rune of the pair inside the word

(null: hits proportional to pairs at risk per position; shuffle z-values already in repo, not re-run)

| pos | lag6 pairs | lag6 hits | lag5 pairs | lag5 hits |
|---|---|---|---|---|
| 0 | 559 | 33 | 815 | 36 |
| 1 | 343 | 19 | 559 | 27 |
| 2 | 187 | 12 | 343 | 18 |
| 3 | 109 | 6 | 187 | 11 |
| 4+ | 92 | 10 | 201 | 12 |

Repo z per position: lag-6 +2.98/+2.06/+2.18/+1.14/+3.71 (echo_position.txt:24-28); lag-5 +1.66/+1.65/+1.83/+1.72/+1.95 (echo_position.txt:6-10).

### e. Multiple hits per word

- lag-6: words with >=2 hits: observed 6, expected by binomial on pairs-per-word 1.64 (Poisson p = 0.007); words: S/P/T/F/P/U/ING/Y/ING/X/IA (0.7 w13, 2 hits); C/B/U/OE/C/B/L/N/OE/ING/X/O (0.11 w76, 2 hits); EO/R/N/S/O/O/C/A/E/Y/E/E (0.13 w19, 2 hits); P/H/ING/E/D/OE/O/H/J (0.13 w176, 2 hits); M/L/I/TH/T/EA/S/N/G/L (0.15 w314, 2 hits); W/ING/H/T/X/AE/I/J/U (0.15 w349, 2 hits)

- lag-5: observed 9, expected 3.05 (Poisson p = 0.004); words: ING/P/O/A/Y/ING/P/S (0.9 w100, 2 hits); W/IA/EA/R/AE/W/IA/D/A/TH/C (0.9 w106, 2 hits); W/B/M/R/N/M/H/M/I/N/A/D (0.11 w422, 2 hits); EA/Y/P/OE/TH/S/Y/P (0.12 w172, 2 hits); N/A/EA/O/A/N/A/TH/G/O (0.13 w43, 2 hits); U/P/S/TH/I/C/P/S/I/W (0.14 w342, 2 hits); E/S/EO/TH/TH/E/S (0.15 w730, 2 hits); P/OE/J/A/ING/P/TH/P/A/ING (0.14 w161, 3 hits); S/D/ING/G/L/S/D/ING (0.15 w561, 3 hits)

### f. The 11 (S,S) lag-5 pairs

| sec | word_no | L | pair_pos | word | ends_word | starts_pos0 |
|---|---|---|---|---|---|---|
| 0.7 | 59 | 8 | 0 | S/OE/R/U/W/S/L/IA | False | True |
| 0.8 | 167 | 10 | 3 | W/I/IA/S/P/L/TH/A/S/J | False | False |
| 0.9 | 99 | 12 | 1 | A/S/IA/TH/S/TH/S/F/M/G/D/EA | False | False |
| 0.11 | 326 | 8 | 1 | O/S/T/M/R/Y/S/X | False | False |
| 0.14 | 283 | 12 | 3 | ING/N/C/S/N/D/EO/N/S/I/C/IA | False | False |
| 0.14 | 342 | 10 | 2 | U/P/S/TH/I/C/P/S/I/W | False | False |
| 0.15 | 55 | 6 | 0 | S/Y/M/D/Y/S | True | True |
| 0.15 | 411 | 10 | 3 | F/U/X/S/X/I/TH/AE/S/M | False | False |
| 0.15 | 561 | 8 | 0 | S/D/ING/G/L/S/D/ING | False | True |
| 0.15 | 587 | 6 | 0 | S/O/EA/C/E/S | True | True |
| 0.15 | 730 | 7 | 1 | E/S/EO/TH/TH/E/S | True | False |

- pair at last two positions of word: 3/11 (repo claim '3 of 11 end word-final S' VERIFIED). - pair starts at word position 0: 4/11 (repo echo_position.txt:18 says 4 at position 0). - section 0.15 holds 5/11 SS pairs vs 2.8 expected from pairs at risk (Poisson p = 0.16) — not significant.

### g. Adjacency to numerals (# tokens)

Note: with work/lp.word_spans cuts a # token always terminates the current word, so no word can contain a numeral; only adjacency (numeral immediately before/after the word) is testable. Only 15 LP2 words are numeral-adjacent at all.

- lag-6: numeral-adjacent hit-bearing 0 / numeral-adjacent total 15; non-adjacent hit-bearing 74 / non-adjacent total 2881; Fisher two-sided p = 1.000 (expected adjacent hit-bearing ~ 0.38)

- lag-5: numeral-adjacent hit-bearing 0 / 15; non-adjacent 93 / 2881; Fisher p = 1.000

## 3. Residual inspection

Residuals: lag-6 r_j = (c_{j+6} + 2 c_j - 24) mod 29 for words L>=7 (a hit <=> r=0, i.e. F); lag-5 r_j = (c_{j+5} - c_j) mod 29 for words L>=6 (a hit <=> r=0). Full per-word tables: work/tmp/lag6_residuals.txt (1290 letters) and work/tmp/lag5_residuals.txt (2105 letters).

### (i) unigram top 10 (lag-6)

| letter | count |
|---|---|
| F | 80 |
| T | 57 |
| W | 54 |
| A | 53 |
| L | 52 |
| B | 51 |
| C | 51 |
| S | 50 |
| ING | 49 |
| G | 49 |

### (i) unigram top 10 (lag-5)

| letter | count |
|---|---|
| F | 104 |
| J | 85 |
| D | 81 |
| P | 79 |
| EA | 79 |
| EO | 78 |
| R | 77 |
| G | 77 |
| U | 76 |
| C | 75 |

### (ii) IoC vs 100 in-section shuffles (same word cuts)

| | LP2 IoC | shuffle IoC range (100) | LP2 top letter | shuffle top-count range |
|---|---|---|---|---|
| lag-6 | 1.029 | 0.986..1.018 (mean 1.000) | F=80 | 52..80 (mean 58.8) |
| lag-5 | 1.004 | 0.992..1.015 (mean 1.000) | F=104 | 82..104 (mean 90.4) |

Dictionary matches (residual word normalises into work/lp.COMMON_N, len>=3): lag-6 2/187 (shuffle range 0..6 (mean 2.6)); lag-5 6/343 (shuffle range 0..11 (mean 5.5)).

### (iii) eye-scan

- Alphabetical +/-1 runs of length >= 4 in the pooled residual sequence, lag-6: none

- lag-5: A/D/OE/ING @11:240

- Repeated residual words (len>=3, count>=2), lag-6: none

- lag-5: none

- Striking lag-6 residual words (vowel-weighted heuristic, single-letter spellings): EURU (0.11 w363), BAOJ (0.15 w683), HATO (0.15 w462), RYEJ (0.14 w164), OOWR (0.13 w47), EYNX (0.13 w43), FUAP (0.11 w196), FURY (0.8 w83), ABNYP (0.13 w123), XUBGA (0.9 w93), XAICBN (0.8 w248), NGWO (0.15 w193), FWCU (0.15 w183), YCMN (0.14 w257), GWLE (0.14 w128), MYGC (0.13 w70), ECTH (0.11 w407), HEPX (0.8 w99), CSYL (0.7 w155), DPESF (0.15 w660)

- Striking lag-5 residual words: EIYI (0.15 w648), EEOX (0.15 w349), ODUI (0.14 w141), NOII (0.13 w313), OOYC (0.13 w213), OCEBU (0.13 w44), YYAJD (0.9 w287), DYEUF (0.7 w90), MYIP (0.15 w367), AJYP (0.13 w329), OXJU (0.9 w307), OJFU (0.9 w235), GCUI (0.8 w89), SOLE (0.7 w67), IUJFC (0.15 w411), YACRX (0.15 w124), FFOOH (0.13 w43), EYPJN (0.8 w137), LUSODSP (0.13 w19), YPLJJRU (0.8 w248)

- Dictionary-matching residual words lag-6: THAT, BBC

- lag-5: HOW, SOLE, DOS, ACA, ATA, HAD

## 4. Honest read

**Nothing in LP2 is solved; these are descriptive statistics of the known echo signal.**

- Enumeration reproduces the repo counts exactly: 80 lag-6 hits, 104 lag-5 hits, 11 (S,S).

- (a) No section concentration: lag-6 chi2 1.39 (df 8, p 0.99), lag-5 chi2 4.32 (p 0.83). Hits spread across sections exactly in proportion to pairs at risk.

- (b) No hit-bearing ciphertext word string occurs twice anywhere in LP2 (0/74 lag-6, 0/93 lag-5). This is fully explained by word length, not by the echo: no LP2 word of length >= 6 repeats at all (0/815 verified independently), while the ~10% overall repetition rate lives entirely in short words (L <= 5). The repetition test is therefore null-informative: hits neither prefer nor avoid repeated spellings; every hit-bearing word is a distinct long ciphertext word.

- (c) Hit-bearing words skew long (L 8-12 over-represented, lag-6 chi2 37.7); this follows mechanically from (d) — the strongest lag-6 excess sits at pair position 4+, which requires L >= 11 — so it is not an independent structure.

- (d) Position tables match echo_position.txt:24-28 / 6-10 exactly (z's cited above, not re-run).

- (e) Words with >=2 hits: lag-6 6 vs 1.64 expected (Poisson p 0.007); lag-5 9 vs 3.05 (p 0.004). Nominally significant clustering; caveat: echo_values.txt:3-6 shows the hit excess is concentrated on a few source runes (7,3,16 for lag-6), which both inflates per-word hit counts where those letters sit and breaks the iid binomial assumption, so these p-values are optimistic.

- (f) SS pairs: 3/11 end at the word's last two positions (repo claim VERIFIED), 4/11 start at word position 0, 5/11 sit in section 0.15 (vs 2.8 expected, p 0.16) — no additional structure.

- (g) Only 15 LP2 words are numeral-adjacent; 0 of them bear hits (expected ~0.4). The sample is too small to say anything (Fisher p ~ 1). No avoidance is demonstrable; hits neither prefer nor avoid numeral-adjacent words.

**Residual verdict — is r plaintext? No evidence for it.**

- Lag-6 pooled IoC 1.029 vs 100 in-section shuffles with the same word cuts: 0.986..1.018 (mean 1.000). LP2 sits just above the shuffle max, but the F cell alone carries 4343 of the total excess of 1640 (265%); F is r=0, which is the echo relation itself (a hit <=> r=0), so the IoC elevation is the known signal, not new structure. Non-F residual letters are at or below random uniformity.

- Lag-5: IoC 1.004 inside shuffle range 0.992..1.015; F=104 carries 5446 of the total excess 651 (837%) — same story (the SS and equality hits are all r=0).

- English check: IoC 1.0 vs 1.7-1.9 for English rune text; dictionary matches lag-6 2/187 (shuffle mean 2.6, range 0..6), lag-5 6/343 (shuffle mean 5.5) — both at chance. The 'THAT'/'BBC' (lag-6) and 'HOW'/'SOLE'/'HAD' (lag-5) matches are the chance-level dictionary hits. One descending run A-D-OE-ING (lag-5, ~0.1 expected) is unremarkable. No repeated residual words of length >= 3 in either lag.

- Bottom line: the lag-6 residual r_j = (c_{j+6} + 2 c_j - 24) mod 29 is uniform noise plus an excess at r=0 — the very cell that defines the echo. It does NOT look like plaintext: no English IoC, no dictionary over-hits, no repeated residual words, no alphabetical runs beyond chance. If the echo mechanism is real, r=0 (F) is where it lives; the other 28 residual letters show nothing.

