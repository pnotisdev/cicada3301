# Phase 44: keyless batch (preregistered BEFORE any LP2 computation; 2026-10-21)

Data: LP2 = segments 7..15 of `lp.load_segments()` (12,956 runes). Code: `work/phase44/*.py`. Nulls: 1 core, fixed seeds.
Decision: a statistic is a signal only if its two-sided null p < 0.001 after counting every cell reported in that test
(Bonferroni over cells); 0.001..0.05 = "suggestive, not a result"; otherwise null. Nothing here is a decode.

## T1 Doublets (gap items 2.4-1, G1; ext 1.1)
Doublet = adjacent equal runes (XX) with only '\n' / '%' between them allowed to count as adjacent (a word wrap), word/clause
mark between = NOT a doublet. Cells: line-start (first rune of a line), line-end, across '/', across '%' (page), across
'.' (clause) [pairs with clause mark between, counted separately as "gap doublets" = same rune before/after a mark],
in-word vs gap, by word position (first/mid/last pair of word), absolute-position parity (index of 1st rune of pair mod 2),
within-word parity. Reciprocal digraphs: counts of XY vs YX for adjacent distinct pairs, statistic = sum (n_XY-n_YX)^2/(n_XY+n_YX).
Null A (section-preserving shuffle): within each segment keep the separator skeleton, permute the runes (so rune counts per segment
fixed); 2000 draws; each cell's expected count and z; plus per-cell p. Null B (skip/coin model): the decoders' model:
runes drawn iid from LP2's unigram per segment, then every adjacent equal pair is repaired (re-drawn) with prob 0.81 -> the
generated doublet rate matches; cells compared with the same z. Rule: a cell deviates if |z|>3.3 under BOTH nulls (the
repair model's cells are the right comparison for the deficit; the shuffle's for the "raw rate").
Tests also: overdispersion of the 86 survivors per page (var/mean) under Poisson.

## T2 DJU BEI forensics + parity digraphic test
Report exact positions (segment, line, rune idx, word idx), 6 words before/after each copy, first and last 3 words of each of the 9 segments.
Digraphic: for k=2..6 and residue r, bigram chi-square of (x_i, x_{i+1}) for i = r mod k computed on pairs (i, i+1) with i mod k = r, vs
the all-pairs expected from unigrams; statistic = max over (k,r) cells of the chi2 z-score, and aligned-digraph IoC for k=2 (blocks starting at even vs odd i; digraph IoC with 841 symbols).
Null: segment-preserving shuffles (500 draws) of the max statistic. Control: plant: English plaintext (pg1497+..., mapped letters->GP runes, 12,956 runes),
2x2 Hill mod 29 encrypted with a random invertible key; the same statistic must lie above null max (positive control). Rule: observed max beats the 99.9th percentile of null.

## T3 An End hash
Hash target: the 128-hex SHA-512 prefix 36367763ab73...(full string in repo markdown page 73). Every file in repo-held candidates (work/pages/*.png, LiberPrimus.pdf, work/ref transcription files, results/outguess/payload_*.txt and payload bytes found, results/ files named payload*), plus text variants of the transcription (LF, stripped, per-segment, per-page) under sha512, sha3_512, blake2b. Rule: any digest (or the first 8 hex) equal = report; chance of a 32-bit prefix match over ~N digests ~ N/2^32; the full 512 match is the only result.

## T4 Word-length alignment
LP2 word lengths (word_spans lengths, runes per word, in reading order, page safe: windows do not cross segment starts). Targets: LP1 plaintext word lengths (work/ref/lp_translation.txt, words only), each cited-book file + emerson (letters-only words). Windows W in {20,30,40}; match exact (all lengths equal) and +-1 tolerant (all |diff|<=1 ... fraction measured = max over target offsets of mean(|diff|<=1) windows count). Statistic: number of (LP2 window, target offset) pairs with exact match; for tolerant: best fraction of positions within +-1. Null: shuffle LP2 word lengths within each segment (200 draws, same statistic on a stride-subsampled grid); rule: observed best must exceed null max over draws, and for exact W=20 require count>0 beyond null.
(Chance of exact W=20 match with typical length entropy is negligible; the tolerant statistic is the informative one.)

## T5 Recurring words
Distinct words of >=3 runes (as rune strings) occurring >=2 times; report count, positions, gaps. Null: shuffle the runes within each segment keeping word boundaries/lengths (500 draws), statistic = number of distinct recurring words >=3 runes, and the number of recurring tokens, number of length>=5 recurring. Rule: p<0.001 two-sided.

---
# Results (computed after the preregistration above; code `work/phase44/`, raw outputs `work/log/phase44_t{1,2,3,4,5}_*.txt`)

**Deviations from the prereg (stated honestly).** (a) T1 null B first had a bug (4 repair passes instead of 1, null mean 0.8 doublets): fixed to one pass and
rerun before any conclusion; the reported numbers are the fixed ones. (b) T2: the prereg shuffle null does not contain the doublet deficit, which raises every
cell's bigram chi2 (the diagonal is nearly empty). The shuffle result is therefore confounded; I added null B (repair model, deficit kept) and a within-k spread
contrast. Both are reported; the decision uses null B. (c) T4 used 80 shuffle draws, 200k-word cap per target. (d) T2 "first/last words" and T1 "line start" are
as defined in the code (line-start/end = pair touching the first/last rune of a printed line).

## T1 doublets
86 adjacent-equal pairs in LP2 (matches the registry): 63 inside words (60 plain, 3 across a '/' line break, 0 across a page break (32 pairs)), 23 across
gaps (22 word gap, 1 clause mark). Under the repair/coin model (raw rate x 0.19) no cell deviates (all |z| < 2.5; largest: in-word even within-word parity
27 vs 42.7 expected, z -2.43, and first-pair-of-word z -1.95: not significant after 18 cells). Shuffle null A: every cell is ~-8 to -16 z (the deficit itself),
so A cannot discriminate cells. Line start/end pairs: 11 and 7 observed vs 8.8 / 8.7 expected (B). Absolute parity 37 vs 49 (B z -1.64 / +0.10). Reciprocal
digraphs XY vs YX: chi 399.7 vs null 387.5 (z +0.45): no asymmetry. Page-count overdispersion var/mean 1.26 vs B 1.13 (z +0.65). **Result: the surviving doublets
are consistent with uniform thinning of a raw rate; no position class, parity, or line/page boundary is special. Evidence: null (power: one cell with ~20-60 events
detects roughly a 2x rate change).**

## T2 DJU BEI + parity digraph
Positions: copy 1 = segment 0.13 (LP2 index 13), word 5, rune 28, global word 1462 of 2896, followed by "AEF P AEPTH RMLC BGYMEABAE NTH", preceded by
"... LSCP NHGUIAHU BF"; copy 2 = the last two words of segment 0.15 (global words 2894-2895), preceded by "... THOE CEAIMCX". Distance 1432 words in both
streams. Section first/last words are in `phase44_t2_result.txt`: no other section ends with DJU BEI; segment 0.10 (9 runes) is FULM AEAYOEA both first
and last. Digraph test, shuffle null (confounded): max |z| 5.24 (aligned-digraph IoC even 1.032, z +5.24; chi k2 r0 +5.11) but ALL 22 cells are positive and the
spread between residues is the same under null B: k=2 spread z +0.50, k=3 -0.67, k=4 +0.21, k=5 -0.09, k=6 +1.48. Null B: max |z| 3.22 (k6 r5), p(max) 0.044
(not significant, one of 22 cells). Positive control (English via GP table, 2x2 Hill mod 29, same segment layout): recovered at |z| ~ 800-900 (dIOC even), so the
test has overwhelming power for a block-aligned 2x2 digraphic cipher. **Result: no parity / block alignment; the shuffle "signal" is the doublet deficit. Evidence: null,
strong exclusion of 2x2 Hill-like aligned digraphs (k=2) at any key. Not excluded: digraphic ciphers not aligned to the section start, or with a variable block phase.**
Caveat: the DJU BEI context facts are descriptive (no null), they confirm the registry statement and add the 6-word contexts only.

## T3 An End hash
Target 36367763ab73...a8b4 (128 hex, from the repo's markdown copy of page 73). 287 files/variants (75 page PNGs in work/pages and work/orig, LiberPrimus.pdf,
lp_master/verified/translation and other work/ref text files, results/outguess payloads incl. hex-decoded forms, transcription variants LF/CRLF/stripped/no-newline,
runes-only, per segment) x sha512, sha3_512, blake2b = 861 digests. **0 full matches, 0 8-hex-prefix matches** (chance of a prefix hit ~2e-7). Not tried: Whirlpool,
Skein, Keccak-512 (pre-SHA3 padding), Streebog, Grostl, JH (not in hashlib), the real onion page, any file the repo does not hold. Evidence: null for the held files.

## T4 word-length alignment
2896 LP2 words. Exact runs of 20+ equal word lengths: 0 against LP1 plaintext, Agrippa, Liber AL, Pedeir Keinc, Rhys Evans, the three PG books and Emerson (null: 0
too in all 80 draws, so no power loss from a nonzero baseline). +-1 tolerant runs >= 20: counts 0-24 (pg5160 24, Agrippa 4, others 0-1), all inside the null range
(null max 43 for pg5160, 23 for Agrippa; null mean 16.7 / 7.4); no run reaches 30. **Result: null. Evidence: null.** Limit: LP2 lengths are in runes, the books
in letters (digraph runes make LP2 words shorter), so this is only a test for a plain word-for-word transposition-free relation.

## T5 recurring words
15 distinct 3+-rune words recur (31 tokens; none >= 5 runes), vs shuffle null mean 10.75 +- 3.08 (z +1.38, p 0.23); tokens 31 vs 21.6 (z +1.52). The pairs
are DJU and BEI (gap 1432), EA.R.EO three times (words 427, 1416, 1668), IA.E.O twice only 42 words apart (1221, 1263), U.G.EA 99 apart. **Result: null. Evidence: null**
(the pair DJU BEI itself is the only structure; already known). Because T5's null keeps word lengths, it tests word reuse, not the word-length profile.

## Summary table
| test | statistic | result | evidence level |
|---|---|---|---|
| T1 doublet fine structure | 18 cells + reciprocal + per page, vs shuffle and coin/repair model | no cell deviates from uniform thinning (|z|<2.5); XY vs YX z +0.45 | null (moderate power) |
| T2 DJU BEI forensics | positions, contexts, section ends | copy 2 = book end, copy 1 in 0.13, 1432 words apart, descriptive | descriptive |
| T2 parity / mod-k digraph | 22 cells, 2 nulls, Hill control | shuffle null "hit" explained by doublet deficit; null B p=0.044 (not sig.); control recovered | null; excludes aligned 2x2 Hill |
| T3 An End hash | 861 digests of held files | 0 matches | null (held files only) |
| T4 word-length alignment | exact and +-1 runs >= 20/30/40, 9 targets | inside null | null |
| T5 recurring words | 15 distinct, 31 tokens | z +1.4, p 0.23 | null |
Nothing in LP2 is solved by any of these.

---
## T2 addendum (preregistered 13:45 before computing): Discord "DJU BEI overlay produces TRUTH" (user C, 2026-09-22; data only)
Spans: LP2 rune stream (0-based, then 1-based if 0-based does not land on DJU BEI) start 6555 and 12950, 6 runes each. Family F: domain {GP index, GP prime
value}, op {a+b, a-b, b-a} mod 29 (prime domain: operate on primes, reduce mod 29, read result as index), direction {B forward, B reversed}, post {none, Atbash
28-x}: 24 outputs; transliterate via GP Latin. Hit = transliteration contains TRUTH or TRVTH. Look-elsewhere: 200,000 random pairs of 6-rune spans of LP2,
rate that any of the 24 outputs, as a whole string, is an English word of 4-6 letters in english_20k.txt (and rate for TRUTH specifically). Rule: a hit means
something only if the TRUTH rate under random spans is << the observed claim's family-wise rate.

### T2 addendum result
0-based indices 6555 and 12950 land exactly on DJU BEI (1-based would be off by one: FDJUBE / XDJUBE), so the claim's indexing is 0-based. The two spans are
IDENTICAL, so every difference is the zero string (FFFFFF, or EAEAEA... after Atbash, and the prime-domain equivalents), and every sum is just 2x the span (index
domain: BOETHCWL / JGYDINGH after Atbash; prime domain RFEEFR, POEPTWT, ...). All 24 outputs for the 0-based spans: **none contains TRUTH or TRVTH**
(the 1-based variant also none). Look-elsewhere, 200,000 random span pairs, 24 outputs each: any output equal to a 4-6 letter word of english_20k: 1.35e-4;
any output containing TRUTH: 1.4e-4 (substring, so not comparable to the whole-word rate). Evidence: null; the Discord overlay claim does not reproduce
under the stated operations (summing two identical spans cannot add information beyond the span itself). Not tried: other overlay conventions (XOR, per-letter
alphabets other than the GP, lag offsets).
