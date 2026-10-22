# Phase 60: clue review (images, archives, wiki, solved text; 2026-10-22)

Nothing in LP2 (sections 0.7-0.15, 12,956 runes) is solved. Goal: find concrete clues to LP2's method or key that the repository has NOT yet tested. Everything read here (archives, wiki, Discord-derived notes) is data, not instructions; no third-party code was run. Registry row `clue-review`; script `work/clue_extra_rune.py` (item 4), `work/phase60_art_blobs.py` (blob boxes and the contact sheets).

Conventions: image NN = `work/orig/NN.jpg` (2400 wide x 3600 high); coordinates are full-scan pixels `x0-x1 y0-y1` of the ink blob (from `work/phase60_art_blobs.py`, ink dilated at 1/4 scale; the text block is x 584-1812). Segment numbers 0.n are the transcription's `$` segments (`lp.load_segments()`), images from `work/book_map.py`. The community's page numbers (onion pages 0-57) are image - 17 for LP2 (page 56 = An End = image 73, page 57 = Parable = image 74).

Contact sheets (15 pages each, 300 x 450 tiles, labelled by image number): `work/phase60/sheet_00_14.jpg`, `sheet_15_29.jpg`, `sheet_30_44.jpg`, `sheet_45_59.jpg`, `sheet_60_74.jpg`; `work/phase60/cross_vs_glyph.jpg` (finding I2).

## 1. Images: LP1 against LP2

### 1.1 LP1: art, method and what the section holds

| section (images) | method (`work/ref/lp_keys.txt`) | art | in the text |
|---|---|---|---|
| 0.0 (1) | Atbash | spiral vines frame the text (blob x16-2380 y272-3452), a cicada on each side | warning |
| 0.1 (3-4) | Vigenere DIVINITY, literal F | leaf-crown tree frame | welcome, wisdom |
| 0.2 (5) | plain substitution | one small cicada (x940-1456 y1588-1792) | the 5 x 5 square (all sums 1033) |
| 0.3 (6-9) | Atbash + 3 | old man on a tablet, scroll spirals at its top | koan, instruction |
| 0.4 (10-13) | plain | two robed figures | red numerals 1 and 2 inside the list of errors |
| 0.5 (14-15) | Vigenere FIRFUMFERENFE (= CIRCUMFERENCE, C -> F), literal F | reclining body strip (x0-2400 y3128-3600) on 14, 15, 16; cicada pair (15: x900-1500 y1940-2648) | koan, instruction |
| 0.6 (16) | plain | small cicada, body strip | the 5 x 5 square (3301) |
| An End (73) | phi(prime), literal F | five dots, then the hash | 5 lines of hex |
| Parable (74) | plain | stipple insect (x764-1652 y2052-3128) | 3 lines |

Observations. (a) No one-to-one art -> method rule: the two Atbash sections share spirals (1 and 6), but the two Vigenere sections share nothing (leaf crown against body + cicadas), and cicadas occur on Atbash, Vigenere and plain pages alike. (b) Every plain section carries numbers (0.2 square, 0.4 numerals, 0.6 square): plain <=> numbers, 3 of 3 (Parable is plain without numbers). (c) The enc / plain order is enc enc plain enc plain enc plain.

### 1.2 LP2: eight art parts (identical to the community's "Part 2" sections and to the segments, 0.10 merged into the part of 0.11)

| part | segments / images | art (image, blob) | closing or opening motif |
|---|---|---|---|
| A1 cross | 0.7 / 17-19 | Russian cross, three bars, point-symmetric pair: right x1840-2360 y624-1932, left x40-564 y1668-2976 (sums 2400 / 3600: a 180 degree rotation); same boxes on 19 | insect under the text on 19 |
| A2 spirals | 0.8 / 20-24 | mirrored spiral vines | five dots after the text on 24 |
| A3 branches | 0.9 / 25-31 | bare tree in a margin (31: x28-540 y664-2904) | mayfly on 31 (x1024-1832 y2096-2588) |
| A4 Moebius | 0.10-0.11 / 32-39 | 4 x 4 grid and infinity sign (32), text only | black cross glyph (39: x612-1772 y2212-2648) and body strip (y3128-3600) |
| A5 mayfly | 0.12 / 40-43 | five dots above the text (40: x584-1804 y1140-1668), mirrored winged insects | wing at the top of 44 |
| A6 wing tree | 0.13 / 44-50 | wing (44: x628-1804 y500-872), blurred tree (49: x764-1508 y2276-3144) | blurred tree ends the part (49) |
| A7 cuneiform | 0.14 / 50-56 | wedge numerals (17 13 55 1 = 1033, 3301 in base 60), red numerals 1-5 on 53-55, three dots on 50 and 56 | three dots (56) |
| A8 spiral branches | 0.15 / 57-72 | mirrored spiral-topped vines (70 and 72: x12-588 and x1812-2388 y784-2852), base-60 pages 66-68, cicada (70: x620-1776 y2696-3120; 72: x688-1840 y2764-3188) | the hash page 73 with five dots |

### 1.3 Findings (all new to the repository unless stated)

- **I1. The black glyph on image 39 is the Russian cross of images 17-19, rotated 90 degrees** (same three bars, same small square mark at each bar centre, arrow-like right end; `work/phase60/cross_vs_glyph.jpg`). Phase 9 listed it only as "a black glyph"; the wiki (Symbols page) lists the cross at its pages 1-3 and 23 (its numbering is one off from ours), so the return of the cross is known there. So the cross opens A1 and closes A4 (with a body strip on the same page), and the five-dot figure opens A5 right after (40). Known and re-measured: the five-dot figure is one rigid shape at 24, 40 (flipped) and 73 (rotated) (phase 9).
- **I2. The body strip occurs at 14, 15, 16 (LP1's last pages) and at 39.** In LP1 it closes the solved block; at 39 it closes A4. Reading: "end of a block" marker, not a key.
- **I3. Art is page-invariant inside a part** (phase 9: mirror residual exactly zero on 20-24, 32-38, 45-48, 51-56; the vines of 57-72 are identical). So art cannot be a per-page key stream; it can only select a method or a key per part.
- **I4. LP1's rule (b) fails in LP2.** A7 carries numerals (wedges, red 1-5) and A8 base-60 grids, A4 a grid, but all their ciphertext is flat (`obs-flat`). Numerals in a part therefore do not mark plain text, and no LP2 part looks plain.
- **I5. Layout is uniform.** Full LP2 pages are 12 lines of 21-25 runes (max 277 per page); partial pages are exactly those that end a segment or hold art/numerals. No indentation, line-count or glyph anomaly beyond the marks above. The rune lines wrap inside words, as `lp.word_spans` already assumes.
- **I6. Atbash/spiral parallel**: LP1's two Atbash sections both carry spirals; LP2's spiral parts are A2 and A8. Any Atbash-family key is a sign flip, which the 28-multiplier screens cover (`multipliers`, `chanscreen-step3`, both signs); a page-wise rule that applies pure Atbash only to some pages is excluded by the flat unigrams of every section.

Art -> LP1 method matches proposed and what covers them: spirals -> Atbash (above); leaf and tree art -> Vigenere with a solved-text keyword (`solved-phrase-keys`, `keywords-r4`: negative); cicadas on A8 and the hash page -> phi(prime) as An End (`keywords-r4` row: 4 channels, 48 windows, max -62.5); body/cross/dots -> block markers (restarts tested: `restart-units`, `restart-library`, `typo-restarts`; reuse between blocks is `key-reuse`, untestable).

## 2. Clue ledger (archives, wiki, images, solved text)

"Tested?" gives the registry id, or **no**. Cost = my estimate of CPU time on the existing engine plus coding.

| # | clue | source | possible meaning | tested? | proposed test and control | cost |
|---|---|---|---|---|---|---|
| 1 | **"The key is all around you."** (with @1231507051321, "Good luck", 3301) | Cicada OS `message.txt` and a signed copy `message.txt.asc` (Cicada archive, `assets/2013/cicados/usr_local_bin/`, also "Cicada OS - the shell script.txt"; a 2013 4chan poster read it as CIRCUMFERENCE) | pun on circum-ference = all around; LP1 section 0.5's key IS circumference; "around" = the key is made of the book's surrounding text | **no** (zero mentions in the repository) | see top 5, T3 (LP1 text as running key); also T5 | 0.5 h |
| 2 | 2016: "words are the map, their meaning is the road, their numbers are the direction" | `2016 Message.wiki`, `phase34_2016_message_map.md` | the phase 34 map | `words-map`, `word-jump`, `signs`, `open-direction`, `hashwords`, `layout-rules`, `reverse` (partly); gaps there: rule-chosen pointer step, page/line rules | per phase 34 | - |
| 3 | "THE TOTIENT FUNCTION IS SACRED", "THE PRIMES ARE SACRED" | solved 0.1 | phi(prime) as An End; phi of other numbers | `sacred*`, `recurrences`, `keywords-r4` (phi(prime)); **phi/sigma/pi of LP2's own word sums: no** (`words-map` used raw and prefix sums only) | top 5, T1 | 0.1 h |
| 4 | "DO FOUR UNREASONABLE THINGS EACH DAY" | solved 0.2 instruction | four irrational numbers; "each day" = each page | single constants pi, e, phi, sqrt2, sqrt3, ln2 and pair sums in `lib-sections`, `sacred` (F1); **four-way sums, one constant per page: no** (the Discord "Unreasonable Way" thread is the 464-word table, `discord-464-table`) | top 5, T4 | 1 h |
| 5 | "SHED OUR OWN CIRCUMFERENCES. FIND THE DIVINITY WITHIN AND EMERGE" | Parable | remove the outer layer: word-edge runes, outer alphabet, outer key layer, pi | `nulledge`, `open-unkeyed`, `layer2` (slices open), `open-outer-alphabet` (affine covered), `lib-sections` (pi) | - | - |
| 6 | "JOURNEY DEEP WITHIN AND YOU WILL ARRIVE OUTSIDE"; "ONLY THROUGH GOING WITHIN THAT WE MAY EMERGE" | solved 0.1 | inside-out reading (centre outward), inner layer first, interior of words | route readings after encryption excluded in effect (the word-internal signals exist in transcription order), `phase50-block` (boustrophedon, column-major); inside-out of a section: no, but it is a transposition BEFORE encryption (undetectable, `transposition`) | none useful | - |
| 7 | "DO NOT EDIT OR CHANGE THIS BOOK ... EITHER THE WORDS OR THEIR NUMBERS" | solved 0.0 | words and their Gematria sums are invariants: any key derived from them is legal | `words-map`, `hashwords`, `lp1-prime-sums` | - | - |
| 8 | The three "behaviors": CONSUMPTION, PRESERVATION, ADHERENCE (solved 0.3, the Loss of Divinity) | solved text | key pointer: consume (advance), preserve (hold), adhere (repeat / restart) | the engine channels hold / spend / skip5 / coin (`chanscreen-step3`), restarts (`restart-*`) | none new | - |
| 9 | "AN END ... A PAGE THAT HASHES TO"; "THE I IS THE VOICE OF THE CIRCUMFERENCE"; "KWESTION ALL THINGS" | solved text | page preimage; the rune I; C spelled K | `an-end-archives`, `ai-oracle`, spelling variants in `keywords-r4` | - | - |
| 10 | Page 56 note: the 57th rune, an F, is skipped; "if not skipped garbled" | wiki PAGE 56 / Post-2014 text | literal-F rule | in `lp.py` (An End, F skip 56); LP2 shows no F excess (`obs-flat`) | - | - |
| 11 | 2014 message `message.txt.asc`: trailing-space counts 2 3 5 7 11 13 17 23 29 31 37, **19 missing** (OEIS A194954, "E edition / S edition" = letters 5 and 19) | archive `2014/Liber Primus/.../2014onion7/message.txt.asc`, wiki Possible hints never used | short numeric key; primes with 19 (rune W) skipped | the OEIS stream itself is in the local OEIS dump (`oeis`, partial, no R4); the 11-term string as a key under R4: **no** | top 5, T2 | 0.3 h |
| 12 | 2012 final message: trailing spaces 0 2 3 5 7 11 13 1 1 2 11 0 7 0 5 0 3 2 (up, then down) | archive `2012/additional docs/signed messages/final message for 2012.txt` | same | **no** (R4) | T2 | - |
| 13 | 2015 Planned Parenthood message: asterisks 5 3 2 5 7 | wiki 2015 Twitter Message | same | **no** | T2 | - |
| 14 | 2012 "P.S." 131-digit number | `Possible hints never used.wiki` | key or modulus of a puzzle chain; digits as a key of period 131 | periodic keys <= 400: `periodic` (no R4); R4: **no** | T2 (long key, cost x4) | - |
| 15 | Wiki: Fibonacci-tree sapling with 13 branches, highlighted branches 2 3 5 6 8 10 11 13 | `Symbols_Drawing_Art`, `Ideas and Suggestions` | an 8-term key | `periodic` (no R4) | T2 | - |
| 16 | Cicada OS data blobs: `tmp/folly` = `tmp/wisdom` (3,368 bytes, identical), `DATA/_560.00` (3.99 MB), `DATA/560.17` (1.18 MB), `DATA/560.13` (a git-lfs pointer text) | archive `assets/2013/cicados/` | "all things should be encrypted": random-looking files as key material (unsolved for 13 years) | **no** as streams. Keyless check run here: adjacent-equal bytes z +1.0 (folly), +1.2 (560.17), -0.3 (_560.00): no anti-repeat signature, so they are not the output of LP2's generator | top 5, T5 | 0.3 h (folly), more for the MB files |
| 17 | 7 x 7 magic square (all sums 1033) hidden in `761.mp3` with OpenPuff and the password 33011033 | Titanpad "complete story of onion 5" (archive) | key-like number block; password 33011033 | the 5 x 5 squares: `grids`, `sacred3`; the 7 x 7: **no**; steganography on LP2 scans with OpenPuff: untestable here (closed-source binary; third-party code is not run); `outguess-scan` covers OutGuess only | the 49 numbers as a period-49 key fall under `periodic` (no R4) | - |
| 18 | Cuneiform numerals 17 13 55 1 = 1033, 3301 (images 50-56) | wiki Symbols; `page-scan-audit` | numbers 1033, 3301 | `line-pointers`, `grids`, `cicada_numbers` streams, `sacred3` | - | - |
| 19 | Red numerals 1-5 (53-55); three dots (50, 56); five dots (24, 40, 73) | images | list items, dividers | `typo-restarts`, `restart-library`; reuse across blocks `key-reuse` | - | - |
| 20 | Cookies 167= and 761= (two 64-hex strings, 2013 onion) | `Possible hints never used.wiki` | hashes of "Patience is a virtue"/"The Instar Emergence"? | the hash library has Cicada strings (`lib-sections`); these two values as 32-byte keys: **no** (periodic, no R4) | T2 (add 2 keys) | - |
| 21 | The 2016 image 563 x 569 (both prime), dead oak tree | wiki 2016 Message | prime dimensions | `outguess-scan`, nothing key-like | - | - |
| 22 | Etherpad "untried methods": spaces counted as runes; first rune of a section as the shift of the next; use OutGuess data to relocate runes; spiral as route cipher; translate via Old English; Beaufort | wiki Ideas page | various | `advsep` (spaces), `fingerprint-families` (first-rune autokey), `outguess-scan` (no payload), `phase50-block`, `obs-wordlen` / `mech25` (Old English), Beaufort = a sign (`multipliers`) | - | - |
| 23 | 13- and 14-rune words (CIRCUMFERENCE(S) has 13 and 14 runes); "7 words of that length" | wiki Ideas page (Cicada_Solver) | crib idea | `cribs` (headings only) | a crib needs the key; no testable operation | - | - |
| 24 | Wiki "Count" row: page 56 uses pi(count); the spreadsheet "Modifier" | wiki | the An End method | known | - | - |
| 25 | DJU BEI | wiki, Mike's package | reused key | `signal-interactions`, `djubei-reuse`, `keyless-batch` | - | - |
| 26 | Wiki 2025: "all pages carry OutGuess data; square and rectangle black dots are constant" | `Liber Primus Updates 2025.wiki` | signed payload / obfuscation | `outguess-scan`, `page-scan-audit` (own reader, 0 payloads) | - | - |
| 27 | The community's art parts (Cross, Spirals, Branches, Moebius, Mayfly, Wing tree, Cuneiform, Spiral Branches) | `Liber Primus Part 2 _mostly unsolved_.txt` | one key per part | same as the segments: section-start windows | - | - |
| 28 | **I1**: cross rotated 90 degrees at the end of A4 | images 17-19 and 39 | A1 and the end of A4 are linked (a frame around 0.7-0.11) | **no** | none testable beyond `key-reuse` (undecidable at this size) | - |
| 29 | **I4**: numerals do not mean plain in LP2 | images, flat IoC | LP1 rule fails | `obs-flat` | - | - |
| 30 | **Extra rune as a function of the rest** | item 4 below | check digit, running sum, copy of the previous word | **now: this phase** | done | 1 CPU-min |

## 3. Solved-text phrases that could name an operation

| phrase (where) | concrete transforms it could mean | status |
|---|---|---|
| "Believe nothing ... find your truth ... experience your death" (0.0) | none specific; the body strip is the art for "death" | - |
| "Either the words or their numbers" (0.0) | per-word Gematria sums (G = prime sum, R = index sum) as keys or pointers | `words-map` raw / prefix sums; **phi, sigma, pi of the sums: T1** |
| "Journey deep within and you will arrive outside" (0.1) | read from the middle outward; decrypt twice (inner key, outer key); interior letters of words | transposition before encryption undetectable; two layers `layer2` (slices open) |
| "The primes are sacred. The totient function is sacred. All things should be encrypted." (0.1) | phi(p) = p - 1 stream (An End); phi of other quantities; the KEY itself encrypted (two layers) | `sacred*`, `keywords-r4`; phi of word sums: **T1**; two layers `layer2`, `open-layer2-slices` (open) |
| "Do four unreasonable things each day" (0.2 instruction) | four irrational constants; one per page; "each day" = each page restart | pair sums only: **T4** |
| "Program your mind. Program reality." (0.3), "Command your own self" (0.1) | the key is a program: a generator, an LFSR, a small state machine | `state-machines`, `recurrences`, `prng-*` |
| Consumption / preservation / adherence (0.3) | spend the key / hold it / repeat it | engine channels hold, spend, skip5, coin; restarts |
| "Kwestion all things" (0.4 instruction) | spelling K for C; question the encoding itself | spelling variants in `keywords-r4` |
| "Shed our own circumferences" (Parable) | strip word edges; drop the outer ring of a grid; subtract the circumference constant (2 pi) | `nulledge`; pi streams |
| "Find the divinity within and emerge" (Parable) | the key word DIVINITY (used, 0.1) | in every keyword set |
| "Amass great wealth ... destroy all that you own" (0.3 wisdom) | accumulate (cumulative sums), then discard (restart) | `chain`, `hyp-streams` (cumulative), restarts |
| "Their numbers are the direction" (2016) | sign / direction of the key per word | `signs`, `open-direction` (stage 1 queued) |
| **"The key is all around you" (2013)** | the key is the surrounding book text; or circumference-type words; or the border art | **T3**; art is page-invariant (I3) |

## 4. Top 5 untested clues (prior plausibility x cheapness)

Plausibility 1-5 is my judgment of how Cicada used numbers and words in LP1 (solved methods: Atbash, keyword Vigenere with keys from earlier text, phi(prime)); cost in CPU hours on the existing engine plus coding. Score = plausibility / cost.

### T1. phi, sigma, pi of LP2's own word sums as per-word key streams (plausibility 2.5, cost 0.1 h, score 25)
- Clue: "the totient function is sacred", "their numbers are the direction", and An End's own f = phi(prime). Phase 35 (`words-map`) used only word length, G (prime sum), R (index sum), raw and prefix sums.
- Streams (one value per WORD of the ciphertext as written, walked rune by rune, the phase 35 convention), for the whole book and per section, forwards and reversed, both signs: v = phi(G_w), sigma(G_w), G_w - 1, pi(G_w) (prime counting), nextprime(G_w) - G_w, phi(R_w + 1), each taken mod 29; and the same with the PREVIOUS word's sums (causal); plus prefix sums of each. About 6 families x 4 variants x 2 directions = 48 streams.
- Engine and control: `work/kscreen/phase35.py` (build / controls / run / verify), default engine, IoC >= 1.40 on the first 300 runes then `verify.py` (IoC, A/I oracle, prime sums); control = its independent planter (4 stream cases x 3 windows recovered at IoC >= 1.60); null = 10 shuffles of every stream. Phase 35's run on 24 streams cost 1.1 M decodes.
- Caveat to report with it: the phase 35 engine models the skip rule but not R4's extra unkeyed rune, which would shift a per-word walk; if it is negative, rerun the winners' top 5 through the R4 mid-word arc (`phase59_keywords_r4.py` machinery with a number stream).

### T2. Cicada's published number strings as short periodic keys under R4 (plausibility 2, cost 0.3 h, score 7)
- Clue: Cicada hid prime sequences in the whitespace of signed messages and gave numbers "without use". The phase 59 scan covered 1,940 WORD keywords under R4; the older `periodic` row (periods <= 400) is key-agnostic but drift-aware only for the skip rule, not for R4's extra rune in about 45% of words.
- Keys (value mod 29 as a rune index; also value - 1 mod 29; for primes also "rune whose Gematria prime is the value"): K1 2 3 5 7 11 13 17 23 29 31 37 (2014), and K1' with 19 inserted; K2 0 2 3 5 7 11 13 1 1 2 11 0 7 0 5 0 3 2 (2012); K3 5 3 2 5 7 (2015); K4 2 3 5 6 8 10 11 13 (Fibonacci tree branches); K5 digit strings of 3301, 1033, 33011033, 761, 1595277641, 1259-1031-1229 and the 16-digit community key 2422826321411203; K6 the 49 numbers of the 7 x 7 square; K7 the 131 digits of the 2012 P.S. (cost x 4); K8 the two 32-byte cookie values. About 60 keys with the three maps.
- Engine and control: `work/phase59_keywords_r4.py` with its key list replaced (about 20 lines: its keys come from `sources()`), windows = the 48 n300 windows, hold and spend, both signs, every phase, hit level T300 = 29.80; control = its R4 planter with a numeric key (K1 and one random 11-term key, 12 plants, 44/44 for keywords before); null = random keys of the same lengths. Phase 59 took 4.4 CPU-h for 1,940 keys, so 60 keys take about 8 CPU-min.

### T3. "The key is all around you": the solved LP1 text as the running key (plausibility 2.5, cost 0.5 h, score 5)
- Clue: a Cicada-authored statement (2013) that the repository never used; its word play (circum-ference = around) is LP1 section 0.5's actual key, and LP1's keys come "from earlier text" (DIVINITY, FIRFUMFERENFE). Phase 34 listed the solved plaintext as a running-key book as a visible gap; the booknight list (Liber AL, Blake x2, Emerson, Mabinogion, Agrippa, Gibson's Agrippa, the KJV) does not contain it.
- Text: the plaintext letters of the nine solved sections in book order (from `work/ref/lp_translation.txt` and the `lp.KNOWN` decryptions, digits and hex dropped), about 3.7 k letters, in both spellings (digraph TH ING EO OE EA IA AE as one rune, and letter by letter); variants: read backwards; read cyclically ("all around") so that the key repeats with period about 3.7 k; sections' own texts per window (0.7 with 0.0-0.1, and so on) are NOT a variant (no stated pairing).
- Engine and control: `work/book_key_decoder.py`, stage-1 settings of the booknight run (first 729 runes of the 8 section windows, offsets step 8, skip rule q = 0.81); gate: 12 plants from the same text, a hit needs about +10 z (best gate z +2.9 to +4.4); null: a 3.7 k slice of Emerson. Cost: the text is about 1/300 of a Gutenberg book.
- Limit: a 3.7 k-letter key covers only the first windows once, so power is that of the 729-rune windows; flat unigrams already exclude an English key under any fixed table, the decoder is table-invariant.

### T4. Four unreasonable things: four irrationals combined, or one per page (plausibility 2, cost 1 h, score 2)
- Clue: "do four unreasonable things each day"; irrational = unreasonable. The library has pi, e, phi, sqrt2, sqrt3, ln2 singly and F1 pair sums, but not four-way sums or a per-page rotation.
- Streams (base-29 digits of the fractional part, as `keystreams.constant_digits`, and decimal digits mod 29): the 15 non-empty subset sums and signed combinations (a + b, a - b) of {pi, e, phi, sqrt2} aligned at digit 0; per-page cycles: page k (k = 0 at 0.7's first page) uses constant k mod 4 restarted at digit 0, and the same without restart (continuing offset); both with the page grid of `lp.load_segments` ('%'). About 60 streams.
- Engine and control: the kscreen library pipeline at every offset, then the chanscreen v2 R4 channels for the survivors; control: planted keys from two of the combined streams; null: 300 random streams (existing). Scale from the library's own campaign timing.

### T5. The Cicada OS blobs as key streams (plausibility 1.5, cost 0.3 h for folly, score 5 for that part)
- Clue: "all things should be encrypted"; `folly` and `wisdom` (identical, 3,368 bytes), `_560.00` and `560.17` (megabytes) have been unsolved since 2013. Keyless check (this phase): adjacent-equal byte pairs z +1.0, +1.2, -0.3 against the byte-frequency expectation (the 3 files are not outputs of an anti-repeat generator; prime_echo, an executable, z -5.4, is irrelevant).
- Streams: bytes mod 29 and bytes with rejection (drop bytes >= 232), forwards and reversed (`folly.rev` is shipped), both signs; folly gives about 2.9 k residues (one stream); the MB files only as 30 k-long slices at 30 start points each.
- Engine and control: kscreen library at every offset, then R4 channels for the best; control: plant from the same stream; null: random byte slices. Not run.

Dropped (already covered): the 2016 triad (phase 34 map and 8 rows), DJU BEI, cribs, page numerology, 5-dot / 3-dot restarts, OEIS A194954 itself (in the OEIS screen, partial), pure Atbash / multipliers, keyword families (phase 59), phi(prime) under R4 (phase 59), book codes (phase 31), OutGuess payloads, the Fibonacci tree as a periodic key under the older drift-aware filter (only R4 adds a gap: T2).

## 5. Item 4: is the extra rune a simple function of the others? (`work/clue_extra_rune.py`, `results/analysis/phase60_extra_rune.txt`)

Test: in each of LP2's 2,896 words (2,365 of at least 3 runes), does some rune j equal (target + b) mod 29, for 15 targets x b in {-1, 0, +1} = 45 tests? Targets (rune index and Gematria prime-value domains): sum of the other runes, minus that sum, the same with prime values, the previous word's index sum / prime sum / length / last rune / first rune, the word's index in LP2 and in its section, its length, the position j, length - j, previous word's sum + this word's length. Statistic: number of hit words; null: 2,000 shuffles of all runes over the positions (word boundaries, lengths and rune frequencies kept), also used for the P of the maximum over the 45 tests.

**Result: negative.** Max z +2.08 ("position in word, b = +1"), P(max over 45 tests) = 0.58; the next four are z +1.77, +1.75, +1.63, +1.47. A deficit at one test is the known doublet suppression: "equals the previous word's last rune" 316 hits against 380 expected (z -3.5; deficit 64 words = the gap-doublet deficit of `obs-doublets`, not new).
- **Positive controls** (plant into a shuffled LP2, same 45 tests, fresh null): the relation "rune = sum of the other runes" planted in 45% / 15% of words gives z +48.6 / +15.1 (P 0.000); "previous word's sum" at 45%: z +50.4; "word length" at 15%: z +17.7; "word index" at 15%: z +15.5; every planted relation is the maximum. z grows by about 1 per percent of words planted, so a relation in fewer than about 4% of words would not show.
- **Null control:** 100 fresh shuffles of LP2 judged against the same null: P(max) < 0.05 in 8 of 100 (expected 5).
- **Negative control on solved ciphertext:** the Vigenere sections 1 and 5 (211 words, 834 runes): max z +2.11, P(max) 0.62 (null-like). The Atbash sections 0 and 3 give z +5.9 on "sum of the other runes", which is an artefact of the control, not a result: Atbash is monoalphabetic, so every copy of THE, OF, ... repeats the same hit or miss and the word-independent shuffle null is too narrow there (reported for the record). LP2 has no repeated words, so its null is appropriate.
- **Word lengths and primes:** with Emerson in runes as the length source and the best one-extra-rune model (q = 0.42), LP2's prime-length words are 1,737 observed against 1,767 fitted (z -1.1): no padding to prime lengths; the one-rune words are 83 against 51 fitted (z +4.6, the known one-rune excess, `ai-oracle`), lengths 4, 6, 8 against 5, 7, 11 behave as fitted.

What it does NOT exclude: a relation that involves the key or the plaintext (the other runes enter only as ciphertext here); a function of two or more neighbours not in the list; an extra rune whose value is random (R4's own description); a hit in fewer than about 4% of words.

## 6. Limits of this review

Images were read at reduced resolution (contact sheets plus blob boxes), not rune by rune; faint marks, colour shifts and micro-differences between the mirrored pages beyond `page-scan-audit` were not re-examined. The Discord-derived rows come from earlier phases. The archive was searched for "key", "the key is" and number strings, not read in full. Signatures of `message.txt.asc` copies were not verified in this phase. Nothing here is a result about LP2's method; the ranked list is a plan.
