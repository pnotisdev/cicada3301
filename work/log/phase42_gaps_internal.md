# Phase 42: internal gap map of the LP2 hypothesis space (2026-10-21)

Reading and reasoning only; nothing was run, nothing in LP2 is solved. Sources: `docs/FINDINGS.md`, `docs/NEGATIVE_SPACE.md`, `docs/HYPOTHESES.md`, `docs/registry.toml` (ids below are registry ids; the `gap` field of every row was read), phases 25, 30, 33-40 and `work/kscreen/RELABEL.md`.
Status legend: **T** tested with a planted control (power stated) | **P** partly (scope or power limit stated) | **U** untested | **X** untestable at LP2's size (stated why) | **Q** built/queued, not finished.
Screened data: 8 sections (0.10 is the 9-rune caption), first 300 runes each (kscreen family); chanscreen v2 covers 82 clause-aligned windows spanning the whole text, but only the 4 anti-repeat channels over the 1,439-stream library.

## 1. Taxonomy and coverage

### L1 Plaintext layer
| id | cell | rows | status / power / scope |
|---|---|---|---|
| P1 | English-like, GP digraph spelling | all kscreen, chanscreen | **T** strong (IoC rule is language-free; plants 45/45 at 250-300 runes) |
| P2 | English letter-by-letter spelling | `open-letter-spelling-power` | **T** 200/200 at 300 runes; 90% at 60 |
| P3 | other natural language (Latin, German, French, Spanish, Italian) | NEGATIVE_SPACE 0.8 | **P** IoC lanes 98-100% at 120 runes; short-window lanes (OEIS 36 runes, chanscreen LM trained on English) lose power (27-59% at 48 runes) |
| P4 | Old/Middle English, other languages | `mech25`, wordlen PR | **P** rejected by word-length histogram only; no decode-level test |
| P5 | plaintext FLAT (inner cipher with a long key, compression, base-n/hex/URL content, random-looking code) | none | **X** every IoC screen is blind (assumption SA1); no row can see it |
| P6 | transposition before encryption | `transposition` | character-level: kscreen's IoC is unigram, so it still sees the key (**T** by construction, never planted); chanscreen's bigram LM and every dictionary score would not. Word-order shuffles are harmless to all. Reported as "undetectable" in the row, which is stronger than needed. |
| P7 | nulls/fillers in the plaintext | `nulledge`, `open-unkeyed` | every word-edge **T**; the 42% mixture **X** (offset resolution, measured) |
| P8 | solved-page conventions (literal F, numerals unkeyed, prime sentence sums) | `obs-flat`, `lp1-prime-sums` | literal F: **T** (excluded in a single layer); prime sums: a verifier only, never a search filter |
| P9 | plaintext is a known/quoted text (candidate-plaintext crib by word-length SEQUENCE) | `cribs` (3 phrases), `book-codes` | **U** only fixed phrases were tried; no sequence alignment of LP2's 2,896 word lengths against any text (LP1 solved text included) |
| P10 | plaintext shaped by constraints (prime clause sums as an author's editing rule; "+1 rune in 42%" as the editing device) | `lp1-prime-sums` | **X** needs the plaintext |

### L2 Alphabet layer
| id | cell | rows | status |
|---|---|---|---|
| A1 | additive on GP index mod 29, inner substitution D(p) free | `lib-sections` and all | **T** strong |
| A2 | outer affine relabel (28 multipliers) | `multipliers` | **T** strong |
| A3 | keyword-mixed outer alphabet | `open-outer-alphabet` | **P** 17 solved-page keywords + Atbash, all sections; the 72-setting gate on window 0.7 only; no canonical alphabets |
| A4 | CANONICAL other orders as the addition domain (Latin alphabetical with digraph placement, Elder Futhark, Rune Poem / rune-name order, the numbering of the 2012 materials) | none | **U** (RELABEL.md says the keyword set came from the solved pages' vocabulary, "not blind permutation search") |
| A5 | arbitrary sigma / tableau / key-to-row map | `open-h2`, `layer2` | **P**: drift-aware H2 has 0-6/24 power under the skip rule; **no drift-free run on LP2** (see G3) |
| A6 | other combination domain: XOR on 5-bit indices with rejection, prime-value domain, mod 28/30/31/32 | `step28`, `prime-domain` | step28 **T**; prime-domain only for echo feedback; additive in the prime-value domain and XOR **U** (low prior; XOR + rejection would give a skip-like rate 3/32, not 2.8%) |
| A7 | an extra 30th symbol (separators or marks are cipher symbols) | HYPOTHESES "not worth running" | argued dead (geometric lengths), not tested |

### L3 Key layer
Source:
| id | cell | rows | status |
|---|---|---|---|
| K1 | number streams, constants, Cicada numbers, hashes of Cicada strings (1,447 streams, all offsets, 28 mults, both signs) | `lib-sections`, `multipliers`, `recurrences`, `sacred*`, `hyp-streams` | **T** strong; scope: section starts + 46 pages + 31 sliding windows + 82 clause windows |
| K2 | recurrences order <= 3, polynomials <= 3 | `recurrences` | **T**; order >= 4, sparse taps: **U** (keyless scan has no power for 3-term forms) |
| K3 | seeded PRNGs, 32-bit (10 generators), time seeds, ms stamps, per-page | `prng-*`, `open-bg-sections`, `open-prng-step` | **T** (window-start pad, no discard); 64-bit only py3/ruby/java; ISAAC, filtered LFSR, string/float seeds **U** |
| K4 | passphrase/KDF/OEIS | `hashscan-kdf`, `oeis` | **P** (OEIS 40-51 terms 29% power) |
| K5 | book LETTERS as running key | `book-running-key`, `book-key-decoder` | **T**/**Q**: untuned tables strong; any table: gate 21-28/30-40; six of seven books 0 stage-1 hits, KJV running |
| K6 | numbers COMPUTED from books (sums, word lengths) | `book-number-streams` | **T** 80 streams, 14/14 plants; 36 non-flat streams, other books/transforms **U** |
| K7 | text/book as PLAINTEXT with an unknown key (known-plaintext route) | none | **U** (= P9) |
| K8 | signed 2014-2017 material, payload | `signed-streams`, `payload` | **T** |
| K9 | images/containers of the LP2 scans as key bytes (ICC profile, pixel/dot coordinates, JPEG coefficient streams; only streams > ~400 terms matter, shorter ones are periodic keys) | `page-scan-audit`, `outguess-scan` | **U** as key streams (audit and OutGuess look for payloads, not keys) |
| K10 | human-chosen / hand-made key | none | **X** |
| K11 | true OTP (no recoverable structure) | repository estimate ~50% | **X** |

Shape:
| id | cell | rows | status |
|---|---|---|---|
| S1 | periodic (period <= ~400, 800 step-domain) | `periodic`, `step28` | **T** 8/8 to 400, 0/8 at 3,200 |
| S2 | autokey plaintext/ciphertext lag <= 8; lag-1 feedback all a; long-lag ciphertext (self-key guard) | `fingerprint-families`, `chain`, `ciphertext-key`, `lag-feedback` | **T**; plaintext autokey lag 9-400 and a != +-1 **U/P** (difference IoC at one lag has ~2 sd power; no recursion test) |
| S3 | progressive/multiplicative/cumulative | `fingerprint-families` | **P** "moderate" |
| S4 | two-layer: stream + keyword (H1) | `layer2`, `h5-power-map`, `open-h1` | **P**: recall at >= 1.6 falls 84% (L=2) to 7% (L=20); the H5 negatives "exclude little" (28% average) |
| S5 | per-word / per-line / per-clause fresh key | `per-word-keys`, `restart-units`, `open-clause-windows` | words/lines/pages/clauses restarts **T**; fresh keys of 13-60 runes **X** (below any window's power) |
| S6 | state machines (4,608 x 29) | `state-machines` | **T** |

### L4 Combination rule
Additive Z29 **T** (A1); step-domain **T**; ciphertext feedback **T** (lag 1); Beaufort/Vigenere signs **T** (mult 28, 61 sign rules, 30 periodic templates); multiplicative c = k.D(p) **T** (fixed-point test, chi2 74.1/84 df); tableau/transition table **P** (A5); polygraphic (Hill 2x2 mod 29, Playfair-29, Bifid, aligned digraph blocks) **U** (keyless, minutes: see G7).

### L5 State and repair rules
| id | cell | rows | status |
|---|---|---|---|
| R1 | skip (key advances, plaintext kept), q = 0.81 | engines | **T** |
| R2 | coin/hold/spend/skip5 channels | `chanscreen-step3` | **T** 4 channels, exact summed-path likelihood; 8.74e9 cells, 0 above 0 nats |
| R3 | null rune on collision (H8) | `m04-baseline`, `nulledge` | **T** as partial explanation; spend vs hold not discriminable from LP2 (power 0.26) |
| R4 | uniform repair / wrong map | `mech25` M0, M7 | **T** (gives the deficit, no echoes) |
| R5 | shared repair budget M2 | `mech25` | fits deficit + both echoes' rates; not the S carrier, not word lengths |
| R6 | q other than 0.81, context-dependent q (by page/line/key value) | none | **U**: only a global q and rune-uniformity were checked; no test of WHERE the 19% leftover doublets sit (G1) |
| R7 | repair as plaintext spelling change | = R3 (spend) | covered only as far as spend |
| R8 | echo-two-tap (copy/affine image of c_-5, c_-6 in words) | `echo-two-tap`, `lag-feedback` | **X** (three free rates fit three numbers) |
| R9 | evolving-alphabet walk | `walk-evolving` | **X** at 1.5% (scan needs 6%) |

### L6 Pointer movement
| id | cell | rows | status |
|---|---|---|---|
| M1 | forward / backward | `reverse` | **T** |
| M2 | decimation d = 2..29; six clocks | `hyp-streams`, `clock` | **T**, multipliers dropped for decimation; prime clocks 150-rune windows only |
| M3 | word-level sign flips | `signs` | **T** 61 rules, mults 1/28 only |
| M4 | per-rune periodic signs (period 2-5) | `open-sign-periodic` | **T** |
| M5 | pointer direction by rule (18 conventions) | `open-direction`, `pdir` | **Q** stage 1 (6 conventions, windows 0.7+0.8) queued |
| M6 | layout-number rules (page, line, position) | `layout-rules` | **Q**: 15/15 plants; page rules need later windows |
| M7 | +1 key per word boundary / line / page | `advsep` | **T** |
| M8 | extra advance by word length / constant / next word | `word-jump` | **Q** cost 6 h+, gate failed as defined on 2 low-IoC plants |
| M9 | keyless nulls at word edges; extra advance with prob. nu | `nulledge`, chanscreen edge arc | **T** (100%); edge arc **Q** (285-400 CPU-h, awaits owner) |
| M10 | random jumps from a second stream, not tied to collisions | HYPOTHESES add-on | **U** no decoder |
| M11 | restarts at unknown places inside a section | `open-sliding`, `restart-*` | **P** library only |

### L7 Layout
| id | cell | rows | status |
|---|---|---|---|
| Y1 | restart at page, line, sentence, word, clause, heading, typographic mark | `restart-*`, `typo-restarts`, `open-clause-windows` | **T**; section starts X (control Z 2.7); clauses < 61 runes U |
| Y2 | segmentation depends on the cipher runes | `segmentation-dependence` | **T** down to 6-12% of boundaries; dependence on the KEY stream or on 3+ runes **U** |
| Y3 | reversal inside word/clause/line | `words-map` | **T** (21/21 plants) |
| Y4 | other READING ORDERS: boustrophedon, line order reversed, column-major of the printed grid, words reordered inside a line/clause, page reversal | `layout27` (27 wide only) | **U** (phase 34 says so; phase 35 reversed each unit, not alternate ones) |
| Y5 | the dot/art/numeral figures as carriers | `page-scan-audit`, `phase9_art` | mirror-symmetric reuse only; red numerals 1-5, cuneiform clusters, 5-dot figure **U** as key/pointer sources beyond phase 40 |
| Y6 | numerals as pointers | `book-codes`, phase 40 | **P**; phase 40 line:character run just ended (null A/B files present, no registry row yet) |
| Y7 | 27x27, 464x16x29 table, grille | `layout27`, `discord-464-table` | **T**/explained; grille untestable (unspecified) |

## 2. Where the holes are

### 2.1 Scope limits that recur (and what each hides)
| limit | rows | what it hides | lifts it |
|---|---|---|---|
| First 300 runes of 8 sections (kscreen family) | signs, pdir, nulledge, advsep, wordjump, layout, book-number, signed, phase 35, relabel | 81% of the text for every mechanism except the plain library (sliding 31 windows, 82 clause windows, 46 pages) | a mechanism screen on page or clause windows (cost x3-10), or a key that is continuous (then the section start suffices) |
| 1,447-stream library (flat subset 581) | all stream rows | the key itself | nothing; it is the problem |
| q = 0.81, skip/coin/hold/spend | everything decoded | context-dependent repair | G1 locates the leftovers first |
| English-like plaintext | chanscreen LM, bigram scores, dictionary | non-English at short windows | IoC lanes at >= 120 runes already cover it |
| IoC >= 1.40 on 300 runes | kscreen family | anything giving the decoded window IoC < 1.40: 2 layers, a key right for only 1/3 of the window, plaintext with low IoC | no cheap fix |
| multipliers fixed at {1, 28} for every NEW mechanism | signs, pdir, nulledge, advsep, wordjump, layout, phase 35 | m = 2..27 combined with any non-default pointer rule (alone they are covered by `multipliers`) | a x13 cost per combination |
| one mechanism at a time | every campaign | pairs (2.3) | see G4 |
| window 0.7 only | `prng-bg`, `prng-ms`, `relabel` gate, pdir pilot | later windows | per-row |
| short-window power | headings, OEIS, clauses < 61 | 13-60 rune clauses (about 45+ clauses) | G9 |

### 2.2 Assumptions every test shares (could all be wrong together)
| id | assumption | tests resting on it | evidence for it | what breaks if wrong |
|---|---|---|---|---|
| SA1 | the plaintext layer fed to the keyed step has IoC >= 1.45 | every IoC screen, hit rule, verification | none directly (the word structure suggests language) | all negatives are void for a flat inner layer; indistinguishable from true OTP |
| SA2 | one cipher rune per key position, key moves only at collisions (+ options) | every decoder | the 2.8% skip rate fits | any process where cipher length is not tied to plaintext length |
| SA3 | key is added in the GP index order | kscreen | solved pages (Atbash, Vigenere, totient) | canonical orders (A4), arbitrary sigma (A5) |
| SA4 | the first 300 runes of a section start the key | kscreen family | the solved pages key from their start | later windows, fresh keys per page (pages tested for the library only) |
| SA5 | library streams are reduced to Z29 by the listed maps (mod / reject / base-29 digits) | library | breadth of maps | other reductions (scale b*29/256, prime index) |
| SA6 | transcription is right: independent re-read done, payload errata confirmed | all | phase 39 | a systematic error type (omitted rune) would look like extra "skips" |
| SA7 | the printed page order and left-to-right, top-to-bottom reading | all | none | Y4 |
| SA8 | the separators are plaintext word boundaries | word-based tests, nulledge, advsep, WJ, `mech25` | segmentation-dependence (not on cipher runes) | dependence on the key stream (Y2) |
| SA9 | solved pages' key naming convention (key named elsewhere in the book) | motivates the library | LP2 has no plain page | none; a key named nowhere is the OTP/non-book branch |
| SA10 | the four structural signals are properties of the encryptor, not of the plaintext | repair simulations | phase 38: independent quirks | the S echo "follows English S..S plaintext (0.13 vs 0.149)": plaintext-level causes are still open |

SA1+SA2+SA4 failing together is the most dangerous bundle: an inner flat layer, a key that restarts per page, and a repair that is not a key skip look exactly like a clean OTP.

### 2.3 Pairs of mechanisms, each excluded alone, never together
Tested pairs: K x M (28 mults), K x backward, K x ciphertext feedback, K x signs (m = +-1), K x advsep, K x nulledge (m = 1), K x reversal, K x restarts, K x outer alphabet (window 0.7), K x chanscreen channels, BK x skip rule (table-invariant, so BK x M is free).

| pair | status | why it matters | cost |
|---|---|---|---|
| nulledge x signs / pdir / layout | **U** | "nulls plus sign rules" (the request's example) | 61 rules x 6.4 min = 6.5 h on 14 threads |
| advsep x signs; advsep x nulledge (key-spending null at every edge) | **U** | a word-aware encryptor with a signed key | 6.5 h; 0.5 h |
| signs / pdir / advsep with restarts (page, clause windows) | **U** | page rules are invisible in 300 runes (phase 36) | x3-10 |
| any non-default pointer mechanism x multipliers 2..27 | **U** | "numbers are the direction" with c = p + m k | x13 |
| decimation x multipliers; decimation x skip | **U** (multipliers dropped) | | cheap |
| book key (BK) x advsep / nulledge / signs / pdir | **U** | a book key with the separator consuming a letter is the natural human implementation; BK covers only skip | ~100-480 core-h per book |
| outer alphabet x every non-default mechanism | **U** | | |
| layer2 (keyword) x pointer mechanisms | **U**; layer2 itself recall 7-28% | | |
| reversal / route x signs, advsep | **U** | | |
| H2 x anything | **U** | | |
| restart x chanscreen edge arc | **U** | | |

### 2.4 Cheap keyless facts about the signals that were never measured
1. WHERE the 82 leftover doublets are (line start/end, across `/` and page marks, across clause marks, within word vs gap by position, clustering with each other and with lag-5/6 echo sites, per-page overdispersion against Poisson(1.8)). The deficit (81%) is the best-measured signal, but only its rune and word-gap uniformity is on record. If the rule is active on a subset of positions the statistic changes the engines' q.
2. The positions of the two DJU BEI copies (distance, line/page position, the first copy's context), and the terminal and initial words of each section (is DJU BEI a section terminator? the second copy is the book's last two words).
3. Per-section heterogeneity of all signals at once as a hidden regime variable (partly in `collision-kernel-followup`, by section bootstrap).

## 3. The five positive signals: mechanisms that would produce each

| signal | mechanism | tested? |
|---|---|---|
| **Doublet deficit 81%** | (a) key skip on collision | **T** (engines, q fixed) |
| | (b) hold-key repair (M04) | **T** (engine blind-spot ruled out; spend vs hold X) |
| | (c) null/spend rune on collision | **T** partial |
| | (d) uniform post-hoc repair (M0) | **T** simulation |
| | (e) transition-table / step-domain cipher with native exclusion + 19% "ditto" | step28 **T**; H2(b) **U** on LP2 |
| | (f) plaintext-side spelling change to dodge repeats | = spend |
| | (g) rule active only on a subset of positions (pages, lines) | **U** (G1) |
| | (h) a polygraphic cipher that never emits equal neighbours | **U** (G7) |
| **Lag-6 in-word relation c' = 24 - 2c** | (a) per-word period-6 skeleton | **T** (skeleton5 variant excluded by lags 3,4,7,8) |
| | (b) collision repair as f(c_-6) (M2) | fits rate; **X** vs two-tap |
| | (c) affine lag feedback d = 6 | **T** (plant chi2/n 2.25 vs 0.05) |
| | (d) key recurrence of order >= 6 with multiplier -2 (k_(j+6) = 24 - 2 k_j) | recurrences <= 3 **T**; order 6 **U** (for a sparse 2.7% relation, wrong shape: the relation would hold for all pairs) |
| | (e) plaintext rewriting (copy-edit) | **X** |
| | (f) transcription artefact in long words | not checked: the in-word-only property argues against, split-half replicates agree |
| **Lag-5 S echo (11 vs 2.3)** | (a) English S..S plaintext | matches the rate (0.13 vs 0.149), no cipher simulation keeps S |
| | (b) repair budget M2 | rate only (S5 2-3 vs 11) |
| | (c) -SELVES endings | **T** dead (3 of 11) |
| | (d) S as a special rune of the alphabet (index 15) in a two-tap rule | **X** |
| | (e) rune mis-transcription (ᛋ vs ᛊ-like glyphs) at those 11 sites | **U**, trivial re-read of 11 sites against the scans |
| **Word lengths** | (a) +1 rune in 42% (nulls) | nulledge 100% **T**; 42% **X** |
| | (b) spelling/digraph conventions | **T** no fit |
| | (c) other language / older English | **P** (histogram only) |
| | (d) word-aware encryptor appends a check/terminator rune in some words | **X** |
| | (e) segmentation placed by the cipher (Y2) | **T** to 6-12%; key-dependent **U** |
| | (f) plaintext is a reordered/edited text | **X** |
| | (g) plaintext is a known text whose lengths + noise match | **U** (G5) |
| **DJU BEI** | (a) chance (1.6%, aligned 0.26%) | measured; community figure |
| | (b) deliberate end marker / repeated phrase with equal key phase | **U**: positions, key-phase relation not examined (G7); periodic keys excluded only to ~400 and the distance is probably larger |
| | (c) unencrypted marker | **U** same test |
| | (d) affine image elsewhere | **T** none among 811 maps |

## 4. Ranked untested items

Cost unit: one 14-thread pass of the 581 flat streams x 8 windows x mults 1/28 x 2 models = 355 M decodes = 6.4 min. All items need a planted control, a matched null, and the CLAUDE.md whole-section verification for any hit.

| # | item | why plausible | cheapest controlled test | cost | a negative excludes |
|---|---|---|---|---|---|
| G1 | **Fine structure of the leftover doublets and of the repair rule** | the largest, best-measured signal; its 19% leftovers and layout dependence are unmeasured; location tells whether the repair sees layout, words, page or the key | pre-register ~15 features (line start/end, across `/`, across page/clause marks, in-word vs gap by position, spacing between doublets, distance to lag-5/6 echo sites, per-page overdispersion vs Poisson); null = phase-25 simulations (M0, M2) with LP2's layout; Bonferroni | minutes, 1 core | a layout-aware or position-subset repair rule; fixes q for every later decoder |
| G2 | **Reading-order transforms**: boustrophedon (two parities), line order reversed within page, words reordered within line/clause, page reversal, column-major of the printed line grid | phase 34 lists it untested; "words are the map"; cheap; kscreen's IoC is blind to nothing else about order | phase 35's machinery (transform the 8 windows, default engine, 581 streams); control = plant then apply the transform (9/9 done for reversal); null = 150 random streams per transform | about 8 transforms x 6.4 min x (real + null) = 1.5 h | reading orders of these types for library keys at section starts |
| G3 | **Drift-free H2 (native exclusion)**: arbitrary tableau, transition table, outer sigma or unknown key-to-row map driven by a library stream with NO pointer skip | phase 32 only showed that the statistic has no power under the skip rule; if the deficit is native (H2b) there is no drift and the code had 8/8 power at 300 runes; also generalises every kscreen negative to any sigma and key map | coincidence count of (key value, cipher rune) pairs per window (z 41.7 on plants); control: random tableau and transition table plants, no skip; null: random streams and within-section shuffles; also for raw ranges > 29 | hours CPU (2.9e7 offset-windows x O(300)) | the whole "tableau/outer-alphabet with a stream pointer that never skips" branch; says nothing for skip branches |
| G4 | **Mechanism crossings in the existing engine**: nulledge x signs, advsep x signs, advsep x nulledge, restart windows x pdir/signs, m = 2..27 on the cheapest non-default mechanisms | the request's "known stream + direction", "nulls + sign rules"; each option is gated and bit-identical alone, none combined; word-aware encryptors with signed keys are natural | engine options already stack (identity tests ran); independent planter for each pair (12 windows), matched null per pair | S x NE 6.5 h, S x AS 6.5 h, NE x AS 0.5 h, page windows x3-10, multipliers x13 per pair | any library stream under two mechanisms at once at the section starts |
| G5 | **Word-length sequence alignment (keyless known-plaintext crib)**: LP2's 2,896 word lengths against LP1 solved text, the cited books, Gutenberg slices, allowing the +1 model | the only crib test so far used three fixed phrases; sequences carry ~2.3 bits per word, strong over 30 words; LP1 self-match costs seconds; also tests quoting/reuse by the author | banded DP / seed-and-extend with noise (len or len+1), plants = Emerson slices encrypted-free with the 42% +1 model, null = word-shuffled LP2 | LP1 + cited books: <1 h; Gutenberg-scale: a day of code, CPU hours | LP2 plaintext containing a >= 30-word passage of any searched text |
| G6 | **Canonical alternative alphabet orders** as the addition domain (Latin-alphabetical with digraph placement, Elder Futhark, rune-name order, Rune Poem order, 2012-materials order) | A3 used solved-page keywords only; the one hole left in L2 outside arbitrary sigma; control and pipeline exist | `work/kscreen/relabel_export.py` per order, all 8 sections, library, mults 1/28; control = plant relabelled at 1.67 vs 1.00-1.06 unrelabelled | 10 orders x 8 sections x ~1 min x 14 threads ~ 1-2 h | those orders for any library key at the section starts |
| G7 | **DJU BEI forensics + block fingerprint**: positions and key-phase relation of the two copies, terminal/initial words of every section; parity / mod-k split of the bigram chi-square, aligned-digraph IoC, Hill 2x2 mod 29 | DJU BEI is the one structural duplicate and its second copy is the book's last two words; polygraphic ciphers are the only L4 cell with no test | keyless; control = planted equal-key phrase and planted digraph substitution on English; null = shuffled sections | minutes | an equal-key duplicate or section terminator; aligned polygraphic blocks of size 2-8 (keyed on top would hide them: stated) |
| G8 | **Book key x word-aware pointer** (separator consumes a book letter, or word-final null): extend `book_key_decoder` with known jumps at word boundaries | BK is the only key source with real structure and the only one never combined with word awareness; every book code used line:character with spaces counted | decoder already has the planter/gate; known jumps reduce the beam; gate on the shortest book first (Blake MHH), then the rest | 100-480 core-h | a cited book as running key under any table with the key advancing at word separators |
| G9 | **Clauses of 13-60 runes (about 45+) with a joint LM + Gematria-prime-sum score** against the library | `open-clause-windows` stops at 61 runes; the prime-sum property (60% of clauses <= 40 runes vs 15% chance) is a free extra likelihood term never used as a search filter | chanscreen v2 contract + a prime-sum bonus term; E4-style plants at 13-60 runes with the plaintext chosen to satisfy it; null = shuffled clauses | CPU-hours (small windows); power unknown, expected modest (29% at 36 runes without the bonus) | per-clause library keys of 13-60 runes if the plaintext keeps the prime property |
| G10 | **Long streams from the scans' own data as keys**: ICC profile bytes, JPEG coefficient streams, pixel line sums, ornament coordinates, numeral/dot positions (only terms beyond ~400 are non-periodic) | LP2 has no plain page, hints must be in non-text elements; community observed LP2 JPEG tables + ICC | `kscreen` file streams (bytes mod 29 with reject, base-29 digits, prefix sums), controls as `signed-streams` (18/18) | 1-2 h | scan-derived streams as additive keys at the section starts |
| G11 | **Long-lag plaintext autokey (d = 9-400, a != +-1)** | fingerprint covers lag <= 8, `chain` lag 1; ciphertext key covered for all lags | residual IoC of c_i - a c_(i-d) over (d, a), calibrated null; recursion with unknown primer is a Vigenere on residues | minutes keyless | plaintext autokey at those lags (low power: ~2 sd per lag) |
| G12 | **Layout-number rules on later windows / the 10 page rules** | `layout-rules` open; page rules show 0-1 sign changes in 300 runes | whole-section or page windows with the sign machinery | 2-3 h for the 13 queued line rules; page rules x3-10 | page/half-page signed keys |
| G13 | H1 with drift tracking (keyword L <= 20) | the solved pages used exactly these two pieces; recall of the flat sweep only 7-28% | designed, controls specified; 1-2 days engine | days | two-layer library x keyword |

Not ranked (no test with power exists): flat plaintext / inner layer (P5, SA1), true OTP, per-line/word fresh keys, two-tap echo rules, evolving-alphabet walk, key reuse between sections, transposition before encryption at character level for chanscreen (kscreen is already blind to it, in the good sense).

## 5. Suggested order after 14:00 (CPU/GPU free for the user until then)
1. G1 and G7 first: keyless, minutes, they sharpen q and the repair model that every later decoder assumes.
2. G2 and G6: an hour or two each on the existing engines, closing two named "untested" cells.
3. G5 (LP1 self-match is seconds), then G3 (drift-free H2) as the only way to say anything about tableaux.
4. G4 in the order NE x AS, S x NE, S x AS.
5. G8-G13 when a free CPU block of days exists; G8 needs the KJV screen to finish.
Items that need an owner decision: the word-edge arc campaign (285-400 CPU-h), pdir stage 1 (queued), G8.

Caveats: the phase 40 line-pointer results (null files only) have no registry row yet and are cited as ended without reading their numbers; "never tested" claims rest on registry `gap` fields and the logs named above, not on a grep of every script.
