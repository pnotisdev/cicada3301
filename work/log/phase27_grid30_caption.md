# Phase 27: what is the page-30 caption ᚠᚢᛚᛗ ᚪᛠᚣᛟᚪ? (2026-10-20)

Segment 0.10 = the 4x4 grid of page 30 (image `work/orig/32.jpg`) plus a 9-rune red caption above it.
Code: `work/grid30_caption.py` (executable form of the family below). Results: `results/grid30_caption/`.

## 1. Caption check
- Transcription `work/ref/lp_verified.txt` line 387 (identical in `lp_master.txt`, no errata touch it):
  `ᚠᚢᛚᛗ-ᚪᛠᚣᛟᚪ.` = two words of 4 + 5 runes, indices [0, 1, 20, 19 | 24, 28, 26, 22, 24].
- Page image 32.jpg (scan numbering from phase 9: image 32 = the page with the grid and the infinity symbol; this is
  "page 30" of the book): the red caption has 9 glyphs, a dot-sized separator between glyph 4 and 5, and a red
  dotted ornament (5x3 squares) at each end. Word split 4 + 5 and the single ᚠ (first glyph, the first rune of the
  caption) match the transcription. I checked word split, rune count and the first glyph by eye on an enlargement;
  I did not template-match each glyph, so glyph identity of runes 2-9 rests on the transcription.
- Gematria sums: word 1 = 149 (= p_35, a member of the grid's prime sequence), word 2 = 489 = 3 x 163, whole 638.

## 2. Preregistered family (written before any scoring; N counted by `python work/grid30_caption.py count`)
Operation on a 9-rune caption c (values 0..28): p = c - s*(key + b) mod 29, s = +-1; optional Atbash
(`post`: p -> 28 - p; `pre`: c -> 28 - c first); optional literal-F skip (a ciphertext ᚠ passes through, and uses no
key position; the solved-page rule in `lp.KNOWN`).
- Pure: plain (1); shift 1..28 (28); atbash+k, k = 0..28 (29).                                         = 58
- Solved keywords: all 17 `lp.KEYWORDS` (DIVINITY, FIRFUMFERENFE, CIRCUMFERENCE, ...), key cycled, every cyclic
  start, s = +-1, 3 Atbash modes, skipF on/off, b = 0.
- Totient-prime stream (p-1) and the plain prime stream, starts 0..15, s = +-1, 3 Atbash modes, skipF on/off, b = 0.
- Grid keys (10 sequences, each mod 29): grid row-major, grid column-major, spiral order (|3301-p_k|), reverse
  spiral, k indices, p_k, reversed p_k, p_k-1, Fibonacci steps (1,1,1,2,...,377), digits of 3301; every cyclic
  start, s = +-1, 3 Atbash modes, skipF on/off, b = 0..28.
- **N = 53,014 decryptions per caption.** (Phase 4 had 5,568 placements; this is a superset in intent, with the solved-page
  rules added; duplicates among the 53,014 outputs are counted, and the calibration uses the same family.)

Scoring of each decrypted 9-rune output (word 1 = runes 1-4, word 2 = runes 5-9), fixed in advance:
- `d2`: both words are in `lp.COMMON_N` (COMMON + the top 10,000 of `ref/english_20k.txt`, spellings merged by
  `lp.normalize`: V/U, K/C, IO/IA, NG/ING ... = the Gematria spelling rules). Primary hit definition.
- `d2s`: strict: both words in the 2,000 most frequent words of length >= 3.   `d1`: at least one word (info only).
- Sum relations, GP sums of the decrypted words: `sab16` both sums in {p_k} (16 terms); `sab48` both in {p_k} u {grid
  values} u {k}; `pp` both sums prime; `sa16`, `sb16`, `sa48`, `sb48` for the single word.
Counting statistic T = number of the N decryptions with the property. Calibration: the identical family on M = 4,000
(i) uniform random 9-rune captions, (ii) 9-rune windows of the LP2 ciphertext (segments 0.7-0.15), (iii) random
permutations of the caption's own runes. p = (1 + #{null T >= observed T}) / (M + 1). A hit counts only if its rule is in
this list and p < 0.01 (the rule is then tested on the other pages).
Plant control: 300 random two-word dictionary plaintexts encrypted with random family members; the family must flag them.

Evidence scale used here (the repository has no written one): Level 0 = no signal, or nothing beyond chance;
1 = post-hoc coincidence; 2 = inside the family but not beating calibration; 3 = beats calibration at p < 0.01 on
this caption alone; 4 = also replicated by the same rule on a second segment; 5 = whole-section verified decoding.

## 3. Results (run 2026-10-20; `results/grid30_caption/{run.log,results.json,observed_hits.txt}`)
Dictionary tables: 1,428 of the 707,281 four-rune strings and 2,035 of the 20.5 M five-rune strings spell a primary-dictionary
word (strict: 447 and 493). Of the 53,014 decryptions, 26,422 are distinct outputs.

| statistic (count over the N = 53,014) | observed | null mean, uniform (M=4,000) | p, uniform | p, LP2 slices | p, caption permutations |
|---|---|---|---|---|---|
| d2: two dictionary words | **0** | 0.008 (P(any) = 0.0023) | 1.0 | 1.0 | 1.0 |
| d2s: strict dictionary | **0** | 0.000 | 1.0 | 1.0 | 1.0 |
| d1: at least one word | 150 | 108 | 0.089 | 0.084 | 0.074 |
| sab16: both sums in {p_k} | 7 | 2.5 | 0.131 | 0.141 | 0.288 |
| sab48: both sums in {p_k, grid values, k} | 27 | 19.3 | 0.209 | 0.213 | 0.369 |
| pp: both sums prime | 2,861 | 911 | 0.091 | 0.098 | 0.371 |
| sa16 / sb16 / sa48 / sb48 (single word) | 615 / 834 / 1,578 / 1,157 | 210 / 646 / 1,075 / 956 | 0.073 / 0.019 / 0.033 / 0.016 | 0.076 / 0.020 / 0.035 / 0.017 | 0.31 / 0.010 / 0.18 / 0.012 |

- **No decryption in the family gives two English words** (and none gives two strict words). The expected number by chance
  is 0.008 per 53,014 (a 4+5 two-word hit is rare with this dictionary; phase 4's estimate was 0.3 expected per 5,568; it
  used a different, looser dictionary (`COMMON_N` weights, 20,000 random pairs), so the two are not comparable). Positive control: 300/300 planted two-word plaintexts, encrypted
  with randomly chosen family members, are flagged by the same code. A null hit would have been detected.
- **Sum relations show nothing after calibration.** The best single numbers (sb16/sb48, p about 0.01-0.02 against the
  random and LP2 nulls) are one of ten correlated statistics, tested against three nulls, with p = 0.2-0.3 against the permutation null in the
  sum-sets that matter (sab16, sab48); the family has heavy internal duplication (26k distinct outputs), which the null
  accounts for. The seven sab16 outputs (e.g. FTHTOE WETHNN; FXUA INGEOENX) are not words.
- **How unusual is "word 1 sums to 149 = p_35"?** Exact over all 29^4 four-rune words: P(sum = 149) = 0.132%;
  P(sum is one of the 16 p_k) = 0.281%; P(in {p_k, grid values, k}) = 1.89%; P(sum prime) = 4.5%. Word 1 alone is a 1-in-356 event for
  the 16-term set, but with two words, three candidate sets and the freedom to look for "something", the look-elsewhere-corrected chance is
  about 0.6% for the p_k set (two words) and 3.8% for the broader set: a post-hoc coincidence, not a significant one, and word 2 (489 = 3 x 163) is in none of the sets.
  (phase 18 also notes sum 638 = 22 x 29, equally post hoc.)

## 4. Verdict
**Level 0-1.** Inside the preregistered family (53,014 decryptions drawn only from the solved pages' rules and the grid's own
numbers) the caption is **not decoded**: zero two-word hits against an expected 0.008, controls working. The 149 = p_35 sum
is a Level 1 coincidence. The caption remains unexplained; it may simply be a title or a signature for the grid rather than a ciphertext. Not excluded: any keyed method not in the
family (an unknown keyword or text, running keys from the LP2 stream, a different alphabet order), the caption as a
non-English/runic-spelling text, and a ciphertext whose key is the *grid image* rather than its numbers.
Limitations: glyph identity of caption runes 2-9 was taken from the transcription; the dictionary is English.
