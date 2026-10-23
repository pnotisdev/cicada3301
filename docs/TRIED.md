# Everything tried on LP2, by date

**Nothing in LP2 (sections 0.7-0.15, 12,956 runes) is solved.** One line per test: date - what was tried - result.
Dates are when the work was first committed. Details, controls and what each test does NOT exclude: `docs/registry.toml`
(row ids in brackets), `STATUS.md`, and the logs in `work/log/`. "Negative" means the planted control was recovered and
LP2 did not beat its random-key null.

## 2026-10-16

- 2026-10-16 - Transcription re-read by independent OCR - confirmed; 1 rune-order error on a solved page, 5 byte errors in the 256-byte payload [obs-transcription]
- 2026-10-16 - Doublet count - 0.66% vs 3.45% expected: ~81% of repeats prevented [obs-doublets]
- 2026-10-16 - Unigrams, bigrams, every lag, literal-F excess - all flat; LP2 does not use the solved pages' literal-F rule in one layer [obs-flat]
- 2026-10-16 - Key library: 1,447 streams (number theory, constants, Cicada numbers, hashes) - 409 M decodes, 0 hits [lib-sections]
- 2026-10-16 - Library x all 28 key multipliers - 5.7 bn decodes, 0 hits [multipliers]
- 2026-10-16 - Linear recurrences order 1-3 and polynomials up to degree 3 - 9.2 bn decodes, 0 hits [recurrences]
- 2026-10-16 - Per-word keys (constant, linear, quadratic, periodic, recurrences) - excluded [per-word-keys]
- 2026-10-16 - Periodic keys with skip-drift-aware filter - null [periodic]
- 2026-10-16 - Seed sweeps of PHP, glibc, .NET and 7 more generators, dictionary score - nothing above the random-seed maximum [prng-dict]
- 2026-10-16 - Transposition after encryption - excluded [transposition]
- 2026-10-16 - Secret outer alphabet behind a per-word key - indistinguishable from surrogates [dsearch]
- 2026-10-16 - The 256-byte payload - byte-random; no hash match, no decryption [payload]
- 2026-10-16 - Page-30 grid, the 1033 word square, the 3301 square - explained puzzle furniture, not keys [grids]
- 2026-10-16 - Page-30 grid caption (two words) - 0 decryptions [grid30-caption]

## 2026-10-17

- 2026-10-17 - Autokeys (lag <= 8), monoalphabetic, Vigenere (period <= 29), progressive, multiplicative, cumulative keys - none reproduces LP2 [fingerprint-families]
- 2026-10-17 - Ciphertext feedback c_i = a*c_(i-1) + p_i + k - best falls to 1.07 over its window [chain]
- 2026-10-17 - Ciphertext as key (solved ciphertexts, LP2 backwards/forwards) - best 1.31, 0 hits [ciphertext-key]
- 2026-10-17 - Key running backwards, with/without feedback - best 1.387 [reverse]
- 2026-10-17 - Clocked key pointers (advance by 1 + index, prime, prime - 1) - inside matched nulls [clock]
- 2026-10-17 - Key restart at every page, paragraph, line, sentence, word - null [restart-units]
- 2026-10-17 - Restart at the 10 red headings and 46 page starts - flagged windows not significant after correction [restart-library]
- 2026-10-17 - Restart at list items, three-dot marks, after headings - chance level [typo-restarts]
- 2026-10-17 - Decimated library, word sums, pi/e/phi/sqrt2 at 10^6, 3301 x 1033 - 0 hits [hyp-streams]
- 2026-10-17 - Combinations of number-theory streams, functions at primes (1,063 streams) - 0 hits [sacred]
- 2026-10-17 - Inverses, discrete logs, cubes mod primes (19 streams) - 0 hits [sacred2]
- 2026-10-17 - Book-derived streams (phi/sigma of 3301i+1033 etc.) - 0 hits [sacred3]
- 2026-10-17 - Hash streams of all 12,944 words and phrases of the solved text - 8.1 bn decodes, 0 hits [hashwords]
- 2026-10-17 - 19.2 M passphrases and 719 k KDFs into hash streams - 0 candidates [hashscan-kdf]
- 2026-10-17 - 199,088 OEIS sequences as keys - no candidate [oeis]
- 2026-10-17 - Ten generators over all 2^32 seeds, boundary-free score - 0 candidates [prngx]
- 2026-10-17 - Fresh seed per section, ten generators, full seed space - 0 candidates [open-bg-sections]
- 2026-10-17 - Epoch-second seeds 2011-2015 and seeds below 2^27, every section - 0 candidates [prng-time]
- 2026-10-17 - Millisecond timestamps 2012-2014 (Java, CPython, Ruby, 25 months each) - 0 candidates [prng-ms]
- 2026-10-17 - Human-plausible seeds (334 M per generator) - stage A negative, stage B partly run [prng-bg]
- 2026-10-17 - Step-domain seed sweeps, ten generators, IoC score - 0 candidates [open-prng-step]
- 2026-10-17 - Step-domain cipher (plaintext in c_i - c_(i-1)) - inside null [step28]
- 2026-10-17 - Dictionary screens with corrected word segmentation - best hits are random controls [rescreen]
- 2026-10-17 - Small state machines (4,608 rules x 29 states) - none fits [state-machines]
- 2026-10-17 - Two layers: keyword Vigenere inside a number stream - 0 of 15 hits pass [layer2]
- 2026-10-17 - Book codes: 1,520 pointer readings into 4 books - best inside null maxima [book-codes]
- 2026-10-17 - Cribs (DIVINITY WITHIN heading, title cribs) - in none of the sequences [cribs]
- 2026-10-17 - 27 x 27 layout, page numerology, totient walk - no structure; numerology is chance [layout27]
- 2026-10-17 - Per-word period-5 twist skeleton - excluded (missing lag 3/4 excess) [skeleton5]
- 2026-10-17 - Origin of the 0.6 square's seeds - analysis, 0 hits [square-06]
- 2026-10-17 - Lag-5 echo inside words (rune S) - observed then; dropped 2026-10-22 as selection chance [obs-lag5]
- 2026-10-17 - Lag-6 relation c' = 24 - 2c inside words - observed, z +5.3 (the strongest signal) [obs-lag6]
- 2026-10-17 - Word lengths - too few 2-rune words; best fit +1 rune in ~42% of words [obs-wordlen]
- 2026-10-17 - Page scans: containers, appended bytes, faint marks - 05.jpg holds its own magic square; nothing else [page-scan-audit]
- 2026-10-17 - Two-tap echo rules, key reuse between sections, evolving-alphabet walk - not testable on LP2 alone [echo-two-tap, key-reuse, walk-evolving]
- 2026-10-17 - Left open then: H1 library x keyword, H2 tableau ciphers, OEIS long terms, Rune Poem, RAND digits [open-h1, open-h2, open-oeis-short, open-sources]

## 2026-10-18

- 2026-10-18 - Extra key step per word boundary / line / page break - below 1.40, 0 verified [advsep]
- 2026-10-18 - Keyless word-edge nulls (edge runes consume no key) - every flagged hit falls to ~1.04 [nulledge]
- 2026-10-18 - Affine lag-feedback autokey within words (6,496 settings, nonlinear maps) - only the doublet deficit itself [lag-feedback]
- 2026-10-18 - Same in the prime-value domain - never beats its null [prime-domain]
- 2026-10-18 - Named lag-6 echo mechanisms (F replacement, collision twist, autokey chain) - all excluded [echo-mechanisms]
- 2026-10-18 - Collision-substitution kernels, fixed halves - observed, not a key [collision-kernel-followup]
- 2026-10-18 - Hold-key repair vs the unchanged engines - engines lose alignment: led to chanscreen v2 [m04-baseline]
- 2026-10-18 - Recall of the keyword x library sweep - power falls from 84% (L 2) to 7% (L 20) [h5-power-map]
- 2026-10-18 - Periodic sign templates (Beaufort/Vigenere alternation, 25 templates) - best 1.400, 0 verified [open-sign-periodic]
- 2026-10-18 - Key starting mid-page (staggered windows) - best 1.332, 0 hits [open-sliding]
- 2026-10-18 - Per-page seeds, 8 generators - 0 candidates [prng-pages]
- 2026-10-18 - "Their numbers are the direction": 61 word-level sign rules - best 1.388 [signs]
- 2026-10-18 - Pointer direction by the words' numbers (pilot) - negative on the slice; full run queued [open-direction]
- 2026-10-18 - Unkeyed insertions / extra key steps at separators (pilot) - no cell reaches 0 [open-unkeyed]

## 2026-10-19

- 2026-10-19 - chanscreen v2: hold/spend/skip/coin channels, 82 windows, 8.7 bn cells - 0 cells reach the hit level [chanscreen-step3]
- 2026-10-19 - Key restart at every clause mark (likelihood score) - 0 tier-1 cells [open-clause-windows]

## 2026-10-20

- 2026-10-20 - Book letters as running key under the rune table or any untuned table (17 texts, 6 languages) - excluded by flatness [book-running-key]
- 2026-10-20 - Table-free book-key decoder: Liber AL, Blake x2, Emerson, Mabinogion, Agrippa 1651, Gibson's Agrippa, and the KJV (finished 2026-10-23) - 0 hits [book-key-decoder]
- 2026-10-20 - Cited books as number streams (cumulative sums, word lengths) - best 1.346, 0 hits [book-number-streams]
- 2026-10-20 - Signed 2014 payloads and hex blobs as keys (272 streams) - best 1.297 [signed-streams]
- 2026-10-20 - OutGuess payloads in the LP2 page scans - none in any of the 56 pages [outguess-scan]
- 2026-10-20 - Book's own numbers as line:position pointers - no message [line-pointers]
- 2026-10-20 - Layout sign rules (page/line parity, mod 3) - 4 of 13 run, negative; rest queued [layout-rules]
- 2026-10-20 - "Its words are the map": jump by word length at boundaries - inside nulls [word-jump]
- 2026-10-20 - LP2's own word lengths/sums as keys; ciphertext reversed per word/clause/line - nothing reaches 1.40 [words-map]
- 2026-10-20 - Does word segmentation depend on the ciphertext? - no [segmentation-dependence]
- 2026-10-20 - Relations by position and word length - none [word-position-schedule]
- 2026-10-20 - Prime clause sums of the solved pages - 36 of 76 prime (z 7.9): a verifier; confirmed authored by the 2013 audio tag [lp1-prime-sums]
- 2026-10-20 - One collision-repair mechanism for all signals (M0-M7) - repairs fit, word lengths do not [mech25]
- 2026-10-20 - Power check with letter-spelled plaintext - 200/200 detected [open-letter-spelling-power]
- 2026-10-20 - Community 464-word table - balance is a selection effect [discord-464-table]
- 2026-10-20 - Cicada's 2012 Mabinogion book code reproduced (line:character on Cicada's own line wrap) [book-codes, work/log/phase31_book_codes.md]

## 2026-10-21

- 2026-10-21 - A/I oracle: one-rune words decrypt to A or I (27/27 on solved pages) - verifier; no kept hit reaches it [ai-oracle]
- 2026-10-21 - Insertion after a 100% anti-repeat rule - edge-only insertion rejected, mid-word marginal [insertion-doublets]
- 2026-10-21 - Keyless batch: doublet fine structure, DJU BEI, digraph blocks, An End's hash over every held file - all null [keyless-batch]
- 2026-10-21 - Signal interactions (isomorphs, S x lag-6, echo words vs length) - no coupling [signal-interactions]
- 2026-10-21 - Mike's period 13 on pages 54-55; the 1033.jpg blob - P 0.26 after selection; blob is an added mark [period13-and-1033]
- 2026-10-21 - Gibson's Agrippa: Cicada's 2012 code reproduced; as a book key 0 hits [book-codes, book-key-decoder]
- 2026-10-21 - Community leads (CicadaPG hash, page-55 affine, TRUTH overlay) - not reproduced or chance [work/log/phase26-27]
- 2026-10-21 - Signed 2016 and 2017 messages - verify against Cicada's key; no key inside [work/log/phase44*]
- 2026-10-21 - Uncovering Cicada wiki (129 articles) - read as data [docs/SOURCES.md]

## 2026-10-22

- 2026-10-22 - Phase 50: reading-order transforms, 20 alphabet orders (incl. 15 OEIS prime orders from the Mayfly document), sign rules - no candidate [phase50-block]
- 2026-10-22 - Cicada's key habits: solved-page words/phrases/lines as Vigenere keys with spelling variants - best 1.332 [solved-phrase-keys]
- 2026-10-22 - An End's SHA-512 vs 124,017 digests of archived onion captures - no match [an-end-archives]
- 2026-10-22 - Mid-word insertion channel, one-window LP2 pilot - best -51.6 vs hit level 29.8 [work/log/phase51_midword_channel.md]
- 2026-10-22 - Open/close bracket marks for a key stack (GEB idea) - none exist [nested-marks]
- 2026-10-22 - Discord ciphers: avaster's cumulative prime cipher, DCPH's book + random skip - excluded (gap-doublet test: 23 of 86 doublets cross word gaps) [discord-cumulative]
- 2026-10-22 - Lag-6 dissection - real (z +5.3), no fixed slot, no repair marker [lag6-dissect]
- 2026-10-22 - Lag-5 S echo dissection - P 0.021 after 203 cuts: dropped [s-echo-dissect]
- 2026-10-22 - Word-level rules for the lag-6 length profile - two rules fit, nothing singled out [lag6-length-rules]
- 2026-10-22 - Mechanism search, nine rules on all signals - R4 fits (repair 24 - 2c(-6) + one extra rune in ~45% of words); pilot negative [mechanism-search]
- 2026-10-22 - DJU BEI as reused key stretch - no stream explains it [djubei-reuse]
- 2026-10-22 - 1,940 solved-text keywords and phi(prime) under R4 - best -64 vs 29.8 [keywords-r4]
- 2026-10-22 - Cicada's 2012 Blake "second chance" code reproduced 22/22 (plate 4, plate line breaks); 2014 GEB code format dialogue:speech:word:letter [book-codes]
- 2026-10-22 - Clue review: all page images, archives, wiki; extra rune as a checksum of its word - negative [clue-review]
- 2026-10-22 - Clue tests: phi/sigma/pi of word sums; Cicada number strings and onion strings under R4; LP1 text as running key; Cicada OS files; four irrationals combined; XOR-domain keys; Cicada OS files under R4 - all negative [p60-wordsums, p60-numkeys-r4, p60-lp1-key, p60-cicada-blobs, p60-irrationals, p60-xor-keys, p60-blobs-r4]
- 2026-10-22 - Cicada OS ISO fetched; DATA/560.13 (118.8 MB) recovered (hash matches) and screened with the audio files as keys (additive, XOR, R4) - uniformly random bytes, 0 hits [docs/SOURCES.md, clue-review]
- 2026-10-22 - One-command reproduction of every published signal - 34/34 pass [reproduce-signals]

- 2026-10-22 - Zipf / word frequencies: do cipher words repeat like a code, are one-rune words uneven? - no: repeats as random, one-rune words uniform (P 0.85) [zipf-words]

## 2026-10-24

- 2026-10-24 - Does the R4 decoder see R4 as fitted (nulls at word edges too)? Plants only - yes: 12/12 at n 150 and 300, recall 45/48 at n 150, 16/24 at n 100; R4 negatives stand; slot rule, two-null share and null check not decidable from LP2; literal F on R4 excluded by the F share; union arc built and gated (+5-11 nats margin) [r4-decoder-coverage]

## Still running (2026-10-22)

- KJV as a table-free book key finished 2026-10-23: 0 hits. Running: pointer direction by the words' numbers (18 conventions), then the remaining layout sign rules and word jump.
