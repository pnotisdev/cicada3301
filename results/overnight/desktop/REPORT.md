# Overnight campaigns: report from desktop

Generated on desktop at 2026-10-17 22:13:17 by `python jobs/overnight.py`. Thresholds and method: docs/CAMPAIGNS.md.

**Controls:** unit tests and kscreen selftest passed on desktop; null results below are validated.

## setup: Build engines and data (3/3 steps done)

Cargo builds of the three Rust engines and the generated inputs (fast when nothing changed).


## selftest: Regression tests and keystream-screen controls (1/1 steps done)

The 71 unit tests (solved pages, transcription, statistics, engines) and the kscreen plant/recover and random-key null. Nothing else is trusted unless this passes.

- unit tests on desktop: passed
- kscreen controls on desktop: SELFTEST PASSED
- kscreen controls through the CUDA port on desktop: SELFTEST PASSED
- GPU validation on desktop: GPU VALIDATION PASSED

## analysis: Fingerprint analyses (2/2 steps done)

Drift-aware periodic-key scan (the old lag scan cannot see periods beyond ~60 under the skip rule) and the word-length model test (LP2 has too few 2-rune words for English in runes).

- drift period scan: verdict: NULL (LP2 max 3.03 vs null max 3.55)
- word lengths:   English runes + null rune in 42% of multi-rune words  3.0  15.6  24.1  17.6  11.8   8.8   6.7   4.6   3.3   2.2   1.2   1.1   G=   16.5 df=10 p=8.52e-02

## kscreen-sections: Keystream library at every offset, LP2 sections (3/3 steps done)

1,447 keystreams (number theory, constants, Cicada numbers, hash streams of Cicada strings and of the corrected payload) at every start offset, both key signs, both anti-repeat models, scored by IoC: any plaintext language, any substituted plaintext alphabet.

- library x 8 sections: best IoC 1.366 (below the 1.40 threshold; 409,283,232 decodes in 19 min)
- matched null (random keystreams, same windows/settings): best 1.318
- verification (library_segments_verify.txt): 0 of 15 re-decoded hits keep IoC >= 1.4 over their whole window and beat their own keystream's random offsets by 0.15 (none: noise)

## kscreen-restarts: Keystream library restarted at headings and page starts (6/6 steps done)

Same library, with the key restarting at each red heading / paragraph start (10 windows) and at each page start (46 windows). Caution: windows shorter than ~250 runes (two heading windows of 91 and 121 runes, two page windows of 131 and 137) exceed the 1.40 threshold by chance after ~10^8 decodes; judge them with the per-window extreme-value null of work/kscreen/short_window_null.py (results/analysis/short_window_null_*.txt), not with 1.40.

- library x 10 heading restarts: best IoC 2.118 (**above threshold, see verification**; 460,443,636 decodes in 2 min)
- library x 46 page restarts: best IoC 1.679 (**above threshold, see verification**; 2,353,378,584 decodes in 22 min)
- matched null (random keystreams, same windows/settings): best 1.597
- verification (library_heads_verify.txt): 15 of 15 re-decoded hits keep IoC >= 1.4 over their whole window and beat their own keystream's random offsets by 0.15 (CANDIDATE - inspect)
- verification (library_pages_verify.txt): 15 of 15 re-decoded hits keep IoC >= 1.4 over their whole window and beat their own keystream's random offsets by 0.15 (CANDIDATE - inspect)

## kscreen-typo: Keystream library restarted at typographic marks (7/8 steps done)

cicadanotebook.com proposed key restarts at the numbered list of 0.14 (items 1-5 and its 10-dot brackets), at the three-dot marks and right after the red headings (work/log/typo_restarts_2026-10-17.md). 22 windows from work/typo_restarts.py; the null has the library's size (1,439 random keystreams of 20,000), because windows under 250 runes are judged against their own maximum. Plants show the power per window length; the solved sections give the known answer (their keys run through the marks); one keystream restarted at every list item is a separate pooled test.

- windows where the library beats its matched null: 5 of 22 (about half expected by chance)

## kscreen-recurrences: Every linear recurrence and polynomial key mod 29 (31/31 steps done)

All linear recurrences of order 1-3 mod 29 (Fibonacci, Lucas, Pell, Tribonacci, Padovan and 23,000 others) from every start state, and all polynomial keys up to degree 3, on the 8 sections.

- order-1 recurrences: best IoC 1.194 (below the 1.40 threshold; 12,544 decodes in 0 min)
- order-2 recurrences: best IoC 1.272 (below the 1.40 threshold; 10,913,280 decodes in 0 min)
- polynomials deg <= 3: best IoC 1.232 (below the 1.40 threshold; 11,316,032 decodes in 0 min)
- order-3 recurrences: best IoC 1.368 (below the 1.40 threshold; 9,188,617,984 decodes in 63 min)
- matched null (random keystreams, same windows/settings): best 1.318
- verification (lin2_segments_verify.txt): 0 of 8 re-decoded hits keep IoC >= 1.4 over their whole window and beat their own keystream's random offsets by 0.15 (none: noise)
- verification (poly3_segments_verify.txt): 0 of 8 re-decoded hits keep IoC >= 1.4 over their whole window and beat their own keystream's random offsets by 0.15 (none: noise)
- verification (lin3_segments_verify.txt): 0 of 10 re-decoded hits keep IoC >= 1.4 over their whole window and beat their own keystream's random offsets by 0.15 (none: noise)

## rescreen: Dictionary screens rerun with the corrected word segmentation (4/4 steps done)

Screens 1 and 2, the reverse-direction screen and the heading-restart screen were run before the word-wrap fix (wrapped words were split, a handicap for a true key). English-dictionary scoring.

- screen 1 (3 offsets):   0.155  CONTROL random 26                        seg 0.13 off=start    sign=+1 atbash=False b=24
- screen 2 (all offsets): top 20 non-control:
- reverse direction: reverse direction: 893 keystreams; control max 0.167
- heading restarts: heading restarts: 893 keystreams; control max 0.975

## dsearch: Key-free secret-alphabet search, large (86/86 steps done)

walk dsearch: a per-word additive key behind any secret outer alphabet, with m = 1-8 position phases and gap sets {1,2} and {1,2,3} (the earlier runs used gap 1 only), against 4 structure-free surrogates each. Starts with a synthetic positive control that must recover the planted alphabet.

- positive control (synthetic m=5):   true-D G 2726; best D agrees with truth on 14 of 29 symbols (up to affine)
- m1_g12: LP2 best G 212; surrogates [226, 210, 207, 213] (z = -0.2)
- m1_g123: LP2 best G 250; surrogates [280, 248, 240, 253] (z = -0.3)
- m2_g12: LP2 best G 303; surrogates [324, 318, 291, 307] (z = -0.5)
- m2_g123: LP2 best G 404; surrogates [405, 382, 364, 378] (z = +1.3)
- m3_g12: LP2 best G 372; surrogates [388, 389, 377, 387] (z = -2.4)
- m3_g123: LP2 best G 488; surrogates [501, 502, 470, 503] (z = -0.4)
- m4_g12: LP2 best G 464; surrogates [477, 482, 454, 471] (z = -0.6)
- m4_g123: LP2 best G 639; surrogates [626, 610, 597, 613] (z = +2.3)
- m5_g12: LP2 best G 538; surrogates [547, 535, 521, 528] (z = +0.5)
- m5_g123: LP2 best G 704; surrogates [728, 714, 689, 715] (z = -0.5)
- m6_g12: LP2 best G 622; surrogates [625, 608, 598, 613] (z = +1.0)
- m6_g123: LP2 best G 828; surrogates [832, 826, 784, 836] (z = +0.4)
- m7_g12: LP2 best G 694; surrogates [696, 682, 669, 706] (z = +0.4)
- m7_g123: LP2 best G 918; surrogates [954, 925, 908, 923] (z = -0.5)
- m8_g12: LP2 best G 768; surrogates [773, 756, 725, 753] (z = +0.8)
- m8_g123: LP2 best G 1047; surrogates [1043, 1037, 1012, 1038] (z = +1.0)

## payload: The 256-byte payload, corrected bytes (2/2 steps done)

Hash identity tests and 832k passphrase AES/RC4/XOR decryptions, rerun on the corrected payload (5 bytes fixed in Phase 2/research; earlier runs and the community's used the uncorrected bytes).

- hashes: tested 25 candidates x ['sha512', 'sha3_512', 'blake2b']: 0 matches
- decryptions:   printable 0.48 magic=pgp-old-packet? AES-192-ecb kdf=md5 pass='the students were enlightened'  b'\xa4\xd1o\x9f\x9f\xa4E\xdc\x10"\x0b\xb1\xbb\x91\x11z\xbb\xc1\xb7\xb3\x0cD\xf5\xd8;)\xab\xe1\x9b\xf4\xe0\xd0'

## kscreen-multipliers: Keystream library x every key multiplier (2/2 steps done)

The library again on the 8 sections with all 28 key multipliers (c = p + m*k), e.g. 3301*k = 24*k mod 29.

- library x 28 multipliers: best IoC 1.381 (below the 1.40 threshold; 5,729,965,248 decodes in 35 min)
- matched null (random keystreams, same windows/settings): best 1.318
- verification (library_segments_allmults_verify.txt): 0 of 15 re-decoded hits keep IoC >= 1.4 over their whole window and beat their own keystream's random offsets by 0.15 (none: noise)

## kscreen-sacred: New stream families from an outside LLM: two-stream combinations, functions at the primes, reciprocals, prime residues (4/4 steps done)

work/kscreen/sacred.py builds streams the library lacks: F1 s1 + t*s2 and interleaves of 20 number-theoretic streams, F3 phi / sigma / d / Fibonacci / Lucas / Pell / triangular read at p_i - 1, p_i, p_i + 1, F4 base-29 digits of 1/3301, 1/1033 and their ratios, F5 rational functions of the prime residue p mod 29. Streams LP2's flat IoC already excludes as keys, and affine duplicates of library streams, are dropped (sacred.tsv). Screened on the 8 sections at every offset like the library (kscreen-sections), against that campaign's 300-stream random null. Controls: work/kscreen/sacred_selftest.py (one planted key per family, recovered). F2 of the proposal (order-4 recurrences with chosen coefficients) is not built.

- controls: SACRED SELFTEST PASSED
- sacred streams x 8 sections: best IoC 1.369 (below the 1.40 threshold; 629,728,288 decodes in 10 min)
- matched null (random keystreams, same windows/settings): best 1.318
- verification (sacred_segments_verify.txt): 0 of 15 re-decoded hits keep IoC >= 1.4 over their whole window and beat their own keystream's random offsets by 0.15 (none: noise)

## prng-all: Seeded-PRNG pads with a fresh seed per section (6/6 steps done)

phpmt sweeps of every seed of PHP<7.1 mt_rand, glibc random() and .NET System.Random on all 8 sections (the single-section runs only covered LP2 page 0), then full-segment verification of the best candidates.

- php: swept 4294967296 seeds in 2628 s; best score 21; verification:   screen  18 seed   16096334 seg0.7 model 0 map 0 sign  1 atb 1: full 0.096 (random seeds 0.078 +- 0.007, z +2.5)
- glibc: swept 4294967296 seeds in 2451 s; best score 21; verification:   screen  19 seed 2235614708 seg0.15 model 0 map 0 sign -1 atb 1: full 0.082 (random seeds 0.078 +- 0.002, z +2.1)
- net: swept 2147483648 seeds in 1206 s; best score 21; verification:   screen  18 seed  174175237 seg0.15 model 1 map 0 sign -1 atb 1: full 0.086 (random seeds 0.078 +- 0.002, z +3.5)

## kscreen-chain: Ciphertext-feedback ciphers c_i = a*c_{i-1} + p_i + k_i, a = 1..28 (141/141 steps done)

The doublet fingerprint (c_i - c_{i-1} flat except that 0 is missing) is what a cipher with ciphertext feedback gives if the encryptor avoids the shift that would repeat a rune. Every earlier screen assumed c = p + k, so none of them could see such a key. For each multiplier a the 8 sections are rewritten as c' = c_i - a*c_{i-1} with the collision check against (1-a)*c_{i-1} (work/kscreen/chain_windows.py) and screened with the 1,447-keystream library, every order-2 linear recurrence and every cubic polynomial, at every offset, both anti-repeat models, any plaintext language and alphabet.

- controls: CHAIN SELFTEST PASSED
- 28/28 multipliers done. best IoC per multiplier (library / order-2 recurrences / cubic polynomials; matched null):
  - a= 1: 1.374 / 1.293 / 1.263; null 1.331
  - a= 2: 1.346 / 1.303 / 1.265; null 1.364
  - a= 3: 1.351 / 1.306 / 1.342; null 1.338
  - a= 4: 1.342 / 1.298 / 1.254; null 1.321
  - a= 5: 1.336 / 1.291 / 1.250; null 1.311
  - a= 6: 1.350 / 1.293 / 1.243; null 1.346
  - a= 7: 1.349 / 1.307 / 1.249; null 1.315
  - a= 8: 1.319 / 1.307 / 1.230; null 1.323
  - a= 9: 1.369 / 1.321 / 1.313; null 1.350
  - a=10: 1.333 / 1.269 / 1.243; null 1.325
  - a=11: 1.349 / 1.285 / 1.239; null 1.357
  - a=12: 1.312 / 1.280 / 1.256; null 1.321
  - a=13: 1.315 / 1.296 / 1.252; null 1.336
  - a=14: 1.353 / 1.306 / 1.250; null 1.322
  - a=15: 1.349 / 1.284 / 1.286; null 1.345
  - a=16: 1.332 / 1.313 / 1.238; null 1.318
  - a=17: 1.415 / 1.313 / 1.228; null 1.320
  - a=18: 1.324 / 1.289 / 1.247; null 1.329
  - a=19: 1.333 / 1.311 / 1.250; null 1.307
  - a=20: 1.365 / 1.284 / 1.265; null 1.328
  - a=21: 1.343 / 1.303 / 1.225; null 1.320
  - a=22: 1.346 / 1.300 / 1.238; null 1.330
  - a=23: 1.336 / 1.289 / 1.251; null 1.366
  - a=24: 1.329 / 1.318 / 1.274; null 1.318
  - a=25: 1.331 / 1.283 / 1.231; null 1.326
  - a=26: 1.347 / 1.295 / 1.234; null 1.343
  - a=27: 1.324 / 1.292 / 1.242; null 1.320
  - a=28: 1.342 / 1.271 / 1.240; null 1.357
- largest: 1.415 (a=17, library); above 1.40 for a = 17: see the verification files

## prng-more: More seeded-PRNG pads, window 0.7: Python, C++/PHP 7, Java, MSVC, drand48/Perl, Ruby (14/14 steps done)

py3 (CPython random.seed), mt32 / mt31 (std::mt19937, PHP >= 7.1), java (java.util.Random), msvc (rand()), drand48 (drand48, Perl) and ruby (Ruby <= 2.7), each with two natural key mappings, all 2^32 seeds, 16 cipher variants (work/phpmt/src/gens.rs; the CUDA port is validated against the Rust engine, which is validated against CPython, NumPy and published vectors). Window 0.7 only: one pad starting at the first unsolved rune.

- window 0.7 (one pad from the start of LP2):
  - java: swept 4294967296 seeds in 165 s; best score 21; verification:   screen  18 seed  731394255 seg0.7 model 1 map 1 sign  1 atb 0: full 0.074 (random seeds 0.076 +- 0.006, z -0.3)
  - msvc: swept 4294967296 seeds in 171 s; best score 21; verification:   screen  18 seed 1629347255 seg0.7 model 0 map 0 sign -1 atb 0: full 0.095 (random seeds 0.077 +- 0.007, z +2.5)
  - drand48: swept 4294967296 seeds in 171 s; best score 20; verification:   screen  18 seed  606886285 seg0.7 model 1 map 1 sign  1 atb 0: full 0.073 (random seeds 0.076 +- 0.006, z -0.5)
  - mt31: swept 4294967296 seeds in 330 s; best score 21; verification:   screen  18 seed 1749727333 seg0.7 model 0 map 0 sign -1 atb 1: full 0.074 (random seeds 0.077 +- 0.008, z -0.5)
  - mt32: swept 4294967296 seeds in 324 s; best score 22; verification:   screen  18 seed 1234791201 seg0.7 model 1 map 1 sign  1 atb 0: full 0.078 (random seeds 0.076 +- 0.006, z +0.3)
  - ruby: swept 4294967296 seeds in 421 s; best score 20; verification:   screen  18 seed 1257362876 seg0.7 model 1 map 0 sign  1 atb 1: full 0.074 (random seeds 0.079 +- 0.007, z -0.8)
  - py3: swept 4294967296 seeds in 425 s; best score 22; verification:   screen  18 seed  818920650 seg0.7 model 0 map 1 sign -1 atb 1: full 0.075 (random seeds 0.076 +- 0.007, z -0.1)

## kscreen-reverse: Key running BACKWARD through the text, with and without ciphertext feedback (a = 0..28) (146/146 steps done)

Every IoC screen so far read the key forward along the text. A key read from the end is covered by reversed windows and the engines' dir=back mode (a re-draw then uses a lower key index, so the used key comes first in pointer order). a = 0 is the ordinary cipher with a backward key; a = 1..28 combine it with ciphertext feedback. Same library, recurrences and polynomials as kscreen-sections; controls: planted backward keys recovered at the exact key index, the same ciphertext read forward not found (work/kscreen/chain_selftest.py).

- controls: CHAIN SELFTEST PASSED
- 29/29 multipliers done. best IoC per multiplier (library / order-2 recurrences / cubic polynomials; matched null):
  - a= 0: 1.332 / 1.315 / 1.249; null 1.344
  - a= 1: 1.328 / 1.290 / 1.225; null 1.338
  - a= 2: 1.320 / 1.306 / 1.270; null 1.311
  - a= 3: 1.333 / 1.280 / 1.242; null 1.327
  - a= 4: 1.349 / 1.274 / 1.234; null 1.329
  - a= 5: 1.338 / 1.317 / 1.262; null 1.317
  - a= 6: 1.335 / 1.289 / 1.259; null 1.352
  - a= 7: 1.343 / 1.294 / 1.252; null 1.340
  - a= 8: 1.387 / 1.307 / 1.254; null 1.335
  - a= 9: 1.338 / 1.291 / 1.294; null 1.322
  - a=10: 1.324 / 1.277 / 1.249; null 1.335
  - a=11: 1.361 / 1.272 / 1.243; null 1.316
  - a=12: 1.322 / 1.297 / 1.248; null 1.348
  - a=13: 1.329 / 1.316 / 1.232; null 1.331
  - a=14: 1.337 / 1.280 / 1.285; null 1.342
  - a=15: 1.325 / 1.320 / 1.243; null 1.321
  - a=16: 1.337 / 1.271 / 1.267; null 1.319
  - a=17: 1.329 / 1.291 / 1.245; null 1.350
  - a=18: 1.361 / 1.285 / 1.288; null 1.333
  - a=19: 1.323 / 1.276 / 1.245; null 1.335
  - a=20: 1.324 / 1.280 / 1.260; null 1.350
  - a=21: 1.334 / 1.291 / 1.250; null 1.310
  - a=22: 1.342 / 1.294 / 1.265; null 1.333
  - a=23: 1.338 / 1.361 / 1.245; null 1.336
  - a=24: 1.338 / 1.292 / 1.241; null 1.357
  - a=25: 1.318 / 1.315 / 1.243; null 1.355
  - a=26: 1.339 / 1.278 / 1.254; null 1.319
  - a=27: 1.322 / 1.302 / 1.245; null 1.359
  - a=28: 1.343 / 1.306 / 1.263; null 1.332
- largest: 1.387 (a=8, library); none reaches the 1.40 threshold

## prng-more-all: More seeded-PRNG pads with a fresh seed per section (0/14 steps done)

py3 (CPython random.seed), mt32 / mt31 (std::mt19937, PHP >= 7.1), java (java.util.Random), msvc (rand()), drand48 (drand48, Perl) and ruby (Ruby <= 2.7), each with two natural key mappings, all 2^32 seeds, 16 cipher variants (work/phpmt/src/gens.rs; the CUDA port is validated against the Rust engine, which is validated against CPython, NumPy and published vectors). A fresh seed per section: all 8 windows at once.

- every section:
  - java: not run
  - msvc: not run
  - drand48: not run
  - mt31: not run
  - mt32: not run
  - ruby: not run
  - py3: not run

## prng-bg: Seeded-PRNG pads with a boundary-free score (English rune-bigram log-likelihood), window 0.7 (and every section) (0/0 steps done)

The dictionary score of the earlier seed sweeps counts words between the transcription's word separators. LP2's word lengths have no serial structure (results/analysis/wordlen_adjacency.txt: mean PMI -0.060 against +0.050 for English and +0.006 for the solved sections), and with LP2's separators imposed on English plaintext a planted seed scores 0 instead of 33 (work/log/phase9_boundaries.md): if the separators are independent of the plaintext words, those sweeps could not see a true key. work/phpmt/bg.py scores a decoded window (120 runes) by the log-likelihood ratio of its plaintext under an English rune-bigram table instead, with the same ten generators, 16 variants and skip/coin beam. Gates: generators identical to phpmt.cu, scores equal to a Python reference, planted seeds recovered for every generator, random ciphertext gives no candidate (work/tests/test_bgmt.py).

- controls (a skipped test counts as failed): GATE PASSED
- py3 (07): swept 4294967296 seeds in 1234 s; best score None; candidates >= 300: 0; best-ranked candidate: no candidate reached the sweep's floor
- java (07): swept 4294967296 seeds in 736 s; best score None; candidates >= 300: 0; best-ranked candidate: no candidate reached the sweep's floor
- php (07): swept 4294967296 seeds in 799 s; best score None; candidates >= 300: 0; best-ranked candidate: no candidate reached the sweep's floor
- glibc (07): swept 4294967296 seeds in 778 s; best score None; candidates >= 300: 0; best-ranked candidate: no candidate reached the sweep's floor
- mt32 (07): swept 4294967296 seeds in 1017 s; best score None; candidates >= 300: 0; best-ranked candidate: no candidate reached the sweep's floor
- msvc (07): swept 4294967296 seeds in 665 s; best score None; candidates >= 300: 0; best-ranked candidate: no candidate reached the sweep's floor
- drand48 (07): swept 4294967296 seeds in 720 s; best score None; candidates >= 300: 0; best-ranked candidate: no candidate reached the sweep's floor
- ruby (07): swept 4294967296 seeds in 1209 s; best score None; candidates >= 300: 0; best-ranked candidate: no candidate reached the sweep's floor
- mt31 (07): swept 4294967296 seeds in 970 s; best score None; candidates >= 300: 0; best-ranked candidate: no candidate reached the sweep's floor
- net (07): swept 2147483648 seeds in 335 s; best score None; candidates >= 300: 0; best-ranked candidate: no candidate reached the sweep's floor
- py3 (all): not run
- java (all): not run
- php (all): not run
- glibc (all): not run
- mt32 (all): not run
- msvc (all): not run
- drand48 (all): not run
- ruby (all): not run
- mt31 (all): not run
- net (all): not run

## kscreen-hashwords: Hash-seed keystreams of every word and phrase of the solved text (4/4 steps done)

The library holds hash streams for only ~65 Cicada strings. work/kscreen/export_hashwords.py adds sha256/sha512/md5 counter streams and the sha256 chain, reduced mod 29 and by rejection, for each of the 809 words and two-word phrases of the solved text in upper and lower case (12,944 streams of 20,000 values), screened at every offset like kscreen-sections, with a null of the same number of random streams.

- 12,944 hash streams x 8 sections: best IoC 1.371 (below the 1.40 threshold; 8,125,932,544 decodes in 108 min)
- matched null (random keystreams, same windows/settings): best 1.364
- verification (library_hashwords_verify.txt): 0 of 15 re-decoded hits keep IoC >= 1.4 over their whole window and beat their own keystream's random offsets by 0.15 (none: noise)

## kscreen-hyp: Untested key families H3-H6 of docs/HYPOTHESES.md (8/8 steps done)

work/kscreen/export_hyp.py: H3 every library stream decimated by d = 2..29; H4 prefix sums and per-word Gematria sums of the solved plaintext and of Self-Reliance; H6 pi, e, phi, sqrt2 digits (bases 10, 29) from positions 10^6 and 3301*1033; H5 ciphertext as key (the keyed solved sections, LP2 read backwards, and LP2's own ciphertext forwards, i.e. long-lag ciphertext autokey and keys from another section; all 28 multipliers). Only streams that keep LP2's flat IoC are screened. LP2's own ciphertext needs the engine's G guard (a window must not be deciphered with itself), which only the Rust engine has. Controls: work/kscreen/hyp_selftest.py.

- controls on desktop: HYP SELFTEST PASSED
- H3 decimations, H4 text numbers, H6 deep constants x 8 sections: best IoC 1.375 (below the 1.40 threshold; 894,992,864 decodes in 27 min)
- H5 solved ciphertexts and LP2 backwards x 28 multipliers: best IoC 1.307 (below the 1.40 threshold; 5,633,152 decodes in 1 min)
- H5 LP2's own ciphertext forwards (guarded) x 28 multipliers: best IoC 1.265 (below the 1.40 threshold; 5,633,152 decodes in 1 min)
- matched null (random keystreams, same windows/settings): best 1.355
- verification (library_hyp_verify.txt): 0 of 15 re-decoded hits keep IoC >= 1.4 over their whole window and beat their own keystream's random offsets by 0.15 (none: noise)
- verification (library_h5_verify.txt): 0 of 8 re-decoded hits keep IoC >= 1.4 over their whole window and beat their own keystream's random offsets by 0.15 (none: noise)
- verification (library_self_verify.txt): 0 of 8 re-decoded hits keep IoC >= 1.4 over their whole window and beat their own keystream's random offsets by 0.15 (none: noise)

## kscreen-clock: Clocked key pointer (H3): the pointer moves on by g(rune) instead of 1 (18/18 steps done)

docs/HYPOTHESES.md H3: after each rune the key pointer advances by 1 + its index, its Gematria prime or prime - 1, read from the cipher rune (c1, cp, ct) or from the deciphered rune (p1, pp, pt; plaintext only without a substitution or shift). Every earlier screen stepped the pointer by one. The 1,447-stream library at every offset on the 8 sections, both signs and both anti-repeat models; the prime clocks use 150-rune windows because they consume about 44 key values per rune. Controls: work/kscreen/clock_selftest.py (planted keys per clock, blindness of the unclocked screen); a 300-stream null per clock.

- controls on desktop: CLOCK SELFTEST PASSED
- clock=c1, library x 8 sections: best IoC 1.317 (below the 1.40 threshold; 236,157,440 decodes in 6 min)
- matched null (random keystreams, same windows/settings): best 1.318
- verification (clock_c1_library_verify.txt): 0 of 15 re-decoded hits keep IoC >= 1.4 over their whole window and beat their own keystream's random offsets by 0.15 (none: noise)
- clock=p1, library x 8 sections: best IoC 1.307 (below the 1.40 threshold; 236,157,440 decodes in 10 min)
- matched null (random keystreams, same windows/settings): best 1.318
- verification (clock_p1_library_verify.txt): 0 of 15 re-decoded hits keep IoC >= 1.4 over their whole window and beat their own keystream's random offsets by 0.15 (none: noise)
- clock=ct, library x 8 sections: best IoC 1.611 (**above threshold, see verification**; 172,162,560 decodes in 4 min)
- matched null (random keystreams, same windows/settings): best 1.593
- verification (clock_ct_library_verify.txt): 0 of 15 re-decoded hits keep IoC >= 1.4 over their whole window and beat their own keystream's random offsets by 0.15 (none: noise)
- clock=cp, library x 8 sections: best IoC 1.593 (**above threshold, see verification**; 172,162,560 decodes in 4 min)
- matched null (random keystreams, same windows/settings): best 1.573
- verification (clock_cp_library_verify.txt): 0 of 15 re-decoded hits keep IoC >= 1.4 over their whole window and beat their own keystream's random offsets by 0.15 (none: noise)
- clock=pt, library x 8 sections: best IoC 1.593 (**above threshold, see verification**; 172,162,560 decodes in 10 min)
- matched null (random keystreams, same windows/settings): best 1.604
- verification (clock_pt_library_verify.txt): 0 of 15 re-decoded hits keep IoC >= 1.4 over their whole window and beat their own keystream's random offsets by 0.15 (none: noise)
- clock=pp, library x 8 sections: best IoC 1.687 (**above threshold, see verification**; 172,162,560 decodes in 10 min)
- matched null (random keystreams, same windows/settings): best 1.619
- verification (clock_pp_library_verify.txt): 0 of 15 re-decoded hits keep IoC >= 1.4 over their whole window and beat their own keystream's random offsets by 0.15 (none: noise)

## kscreen-step28: Relative-rank chain cipher: the plaintext enters the STEP c_i - c_{i-1}, keyed mod 28 (0/0 steps done)

The doublet fingerprint is also what a cipher gives whose ciphertext step is never zero (research note C1, work/log/research_2026-10-17.md): D_i = 1 + (q_i + m*K_j) mod 28 (variant A), 2^(q_i + m*log K_j) (variant B) or the (q_i + m*K_j) mod 28-th of the 28 runes other than c_{i-1} (variant C, rank), with the rare zero step as a 'ditto' that consumes a key value or not. In the c domain the plaintext is a random walk and every earlier screen was blind to it; in the step domain the decoder is a plain subtraction with no beam. work/kscreen/step28.py counts the class histogram at every (stream, offset) for the 1,447-stream library and every unit multiplier of Z28, with planted-key recovery (variants A, B, C and both modes), CPU/CUDA agreement and matched nulls; work/step_periodicity.py scans periodic keys (lags to 3,000).

- controls: SELFTEST PASSED
- 40 windows of 300 steps, 1,447 library streams x every offset x variants A/B/C x modes drop/keep x 12 multipliers: best IoC 1.297 (sec0.9@1200)
- matched null (4 replicates of random streams, same pair count): largest per-window best 1.320; windows where the library beats every replicate by 0.02 and reaches 1.30: none
- native mod-28 library (variants A and C, keys 0..27; export28.py): best IoC 1.315 (sec0.15@2100); largest per-window best in 2 null replicates: 1.315
- verification of the native library (best-ranked window): sec0.15@2100 C/keep m=11 stream #392 'sha256-chain mod :the primes are sacred' offset 6558: window 1.315, beyond (911 steps) 1.010
- verification (the best-ranked window continued to the end of its section): sec0.9@1200 B/drop m=17 stream #571 'sha256-ctr mod :2014' offset 5796: window 1.297, beyond (229 steps) 0.961
- periodic keys (coincidences at lag 2..3000, planted controls and a structured null):   largest z of all scopes and settings: LP2 4.97; 40 random replicates of the same statistic: median 4.49, max 5.48, replicates >= LP2: 4; controls passed

## prng-step: Seeded-PRNG pads for the step-domain cipher, window 0.7: all ten generators (0/0 steps done)

Research note C2: the seed sweeps of the ordinary cipher (c = p + k) cannot see a key that enters the STEP c_i - c_{i-1}. work/phpmt/step.py runs the ten generators of phpmt.cu over all 2^32 seeds and scores, per seed, 144 settings on the first 240 steps of section 0.7 (at key index 0 and 1) (variants A and C with keys mod 28 / variant B with log2 of the non-zero keys of Z29, both key maps, zero steps spending a key value or not, the 12 unit multipliers of Z28) by the index of coincidence of the decoded classes. Gates: keys equal the Rust engine for both alphabets, scores equal the numpy reference, planted seeds recovered for every generator, random ciphertext gives no candidate (work/tests/test_stepmt.py).

- controls (a skipped test counts as failed): not run
- py3: not run
- php: not run
- glibc: not run
- java: not run
- mt32: not run
- net: not run
- msvc: not run
- drand48: not run
- ruby: not run
- mt31: not run

## layer2: Two layers from the solved pages: keyword Vigenere inside, number stream with the anti-repeat rule outside (3/11 steps done)

Hypothesis H-LAYER (work/log/hypotheses_2026-10-17.md): q = p + K[phi mod m] with the literal-F rule of Welcome / Koan 2 (or without), then c = q + S_j with the skip / coin anti-repeat models. The outer layer explains the doublet deficit and the flat statistics, and it hides the inner literal F (LP2 has no F excess); kscreen decodes the outer stream but scores a Vigenere text (IoC ~1.1-1.2), so it is blind. work/layer2 keeps a beam over the outer pointer and the inner phase and scores the decoded letters with an English rune-bigram table (identity and Atbash alphabets): a true key ~ +7 per rune, random ~ -15. Periodic mode covers any keyword of period 2-14 by column coincidences; its hits are checked by estimating the keyword and rescoring. Controls: work/layer2/selftest.py (plants with and without literal F, both alphabets, both models; kscreen blind to them; random streams below +2.0).

- controls: not run
- null: 20 random streams x the solved keys (bigram): not run yet
- core streams x the solved keys DIVINITY / FIRFUMFERENFE / CIRCUMFERENCE (bigram): not run yet
- 20 Cicada streams x 30 Cicada keywords (bigram): not run yet
- core streams x any keyword of period 2-14 (column z): not run yet
- variant A1: 20 streams with a solved key folded in, one pointer (bigram): best -5.6267 per rune (1,159,951,616 decodes in 3 min)
  - verification: 0 of 15 re-decoded hits pass (none: noise)

## prng-time: Generators seeded with a millisecond timestamp of 2012-2014 (Java 48-bit, CPython two-word seeds) (0/51 steps done)

The 32-bit sweeps cover every time(NULL) seed but not new Random(System.currentTimeMillis()) (Java's seed is 48-bit) or random.seed(int(time.time() * 1000)) (CPython seeds MT19937 with two 32-bit words above 2^32). Every UTC month of 2012-01 .. 2014-01, newest first, section 0.7, boundary-free bigram score, then a whole-section check of the best rows with independently built keys against random timestamps. With a validated GPU: work/phpmt/time_gpu.py (the desktop's 64-bit port bgmt64.cu, gate tests/test_bgmt64; java, py3, java-abs, and 'ruby' = Ruby's documented seeding and rand(n) rule on CPython's MT19937, not checked against a Ruby; about 9 h for all). Without one: work/prngx/time_campaign.py on the CPU (gate tests/test_prngx_time: vectors from CPython and the Java specification, seeds planted with independent keys found at rank 1, random ciphertext without candidates; about 210 h, so run the newest months with --hours). Both gates run through run_gate.py and fail on a skipped test.

- gate on desktop: GPU not run; CPU not run
- generator vectors (Java 48-bit and CPython two-word seeds): not run
- GPU java: 7 of 25 months done; candidates after the whole-section check: none
- GPU py3: 7 of 25 months done; candidates after the whole-section check: none
