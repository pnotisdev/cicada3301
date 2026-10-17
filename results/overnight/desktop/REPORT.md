# Overnight campaigns: report from desktop

Generated on desktop at 2026-10-17 05:01:43 by `python jobs/overnight.py`. Thresholds and method: docs/CAMPAIGNS.md.

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
- word lengths:   English runes + null rune in 40% of multi-rune words  3.0  16.1  23.9  17.5  11.7   8.8   6.7   4.6   3.3   2.2   1.2   1.1   G=   20.5 df=10 p=2.51e-02

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

## dsearch: Key-free secret-alphabet search, large (49/86 steps done)

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
- m5_g12: LP2 best G 538; surrogates [547, 535] (z = -0.4)

## payload: The 256-byte payload, corrected bytes (0/2 steps done)

Hash identity tests and 832k passphrase AES/RC4/XOR decryptions, rerun on the corrected payload (5 bytes fixed in Phase 2/research; earlier runs and the community's used the uncorrected bytes).

- hashes: not run
- decryptions: not run

## kscreen-multipliers: Keystream library x every key multiplier (2/2 steps done)

The library again on the 8 sections with all 28 key multipliers (c = p + m*k), e.g. 3301*k = 24*k mod 29.

- library x 28 multipliers: best IoC 1.381 (below the 1.40 threshold; 5,729,965,248 decodes in 35 min)
- matched null (random keystreams, same windows/settings): best 1.318
- verification (library_segments_allmults_verify.txt): 0 of 15 re-decoded hits keep IoC >= 1.4 over their whole window and beat their own keystream's random offsets by 0.15 (none: noise)

## prng-all: Seeded-PRNG pads with a fresh seed per section (6/6 steps done)

phpmt sweeps of every seed of PHP<7.1 mt_rand, glibc random() and .NET System.Random on all 8 sections (the single-section runs only covered LP2 page 0), then full-segment verification of the best candidates.

- php: swept 4294967296 seeds in 2628 s; best score 21; verification:   screen  18 seed   16096334 seg0.7 model 0 map 0 sign  1 atb 1: full 0.096 (random seeds 0.078 +- 0.007, z +2.5)
- glibc: swept 4294967296 seeds in 2451 s; best score 21; verification:   screen  19 seed 2235614708 seg0.15 model 0 map 0 sign -1 atb 1: full 0.082 (random seeds 0.078 +- 0.002, z +2.1)
- net: swept 2147483648 seeds in 1206 s; best score 21; verification:   screen  18 seed  174175237 seg0.15 model 1 map 0 sign -1 atb 1: full 0.086 (random seeds 0.078 +- 0.002, z +3.5)

## kscreen-chain: Ciphertext-feedback ciphers c_i = a*c_{i-1} + p_i + k_i, a = 1..28 (35/141 steps done)

The doublet fingerprint (c_i - c_{i-1} flat except that 0 is missing) is what a cipher with ciphertext feedback gives if the encryptor avoids the shift that would repeat a rune. Every earlier screen assumed c = p + k, so none of them could see such a key. For each multiplier a the 8 sections are rewritten as c' = c_i - a*c_{i-1} with the collision check against (1-a)*c_{i-1} (work/kscreen/chain_windows.py) and screened with the 1,447-keystream library, every order-2 linear recurrence and every cubic polynomial, at every offset, both anti-repeat models, any plaintext language and alphabet.

- controls: CHAIN SELFTEST PASSED
- 7/28 multipliers done. best IoC per multiplier (library / order-2 recurrences / cubic polynomials; matched null):
  - a= 1: 1.374 / 1.293 / 1.263; null 1.331
  - a= 2: 1.346 / 1.303 / 1.265; null 1.364
  - a= 3: 1.351 / 1.306 / 1.342; null 1.338
  - a= 4: 1.342 / 1.298 / 1.254; null 1.321
  - a= 5: 1.336 / 1.291 / 1.250; null 1.311
  - a= 6: 1.350 / 1.293 / 1.243; null 1.346
  - a= 7: 1.349 / 1.307 / 1.249; null 1.315
- largest: 1.374 (a=1, library); none reaches the 1.40 threshold
- failed steps: kscreen-chain/a7-verify (see results/overnight/desktop/logs/)

## prng-more: More seeded-PRNG pads, window 0.7: Python, C++/PHP 7, Java, MSVC, drand48/Perl, Ruby (0/14 steps done)

py3 (CPython random.seed), mt32 / mt31 (std::mt19937, PHP >= 7.1), java (java.util.Random), msvc (rand()), drand48 (drand48, Perl) and ruby (Ruby <= 2.7), each with two natural key mappings, all 2^32 seeds, 16 cipher variants (work/phpmt/src/gens.rs; the CUDA port is validated against the Rust engine, which is validated against CPython, NumPy and published vectors). Window 0.7 only: one pad starting at the first unsolved rune.

- window 0.7 (one pad from the start of LP2):
  - py3: not run
  - mt32: not run
  - mt31: not run
  - java: not run
  - msvc: not run
  - drand48: not run
  - ruby: not run

## kscreen-reverse: Key running BACKWARD through the text, with and without ciphertext feedback (a = 0..28) (1/146 steps done)

Every IoC screen so far read the key forward along the text. A key read from the end is covered by reversed windows and the engines' dir=back mode (a re-draw then uses a lower key index, so the used key comes first in pointer order). a = 0 is the ordinary cipher with a backward key; a = 1..28 combine it with ciphertext feedback. Same library, recurrences and polynomials as kscreen-sections; controls: planted backward keys recovered at the exact key index, the same ciphertext read forward not found (work/kscreen/chain_selftest.py).

- controls: CHAIN SELFTEST PASSED
- not run yet

## prng-more-all: More seeded-PRNG pads with a fresh seed per section (0/14 steps done)

py3 (CPython random.seed), mt32 / mt31 (std::mt19937, PHP >= 7.1), java (java.util.Random), msvc (rand()), drand48 (drand48, Perl) and ruby (Ruby <= 2.7), each with two natural key mappings, all 2^32 seeds, 16 cipher variants (work/phpmt/src/gens.rs; the CUDA port is validated against the Rust engine, which is validated against CPython, NumPy and published vectors). A fresh seed per section: all 8 windows at once.

- every section:
  - py3: not run
  - mt32: not run
  - mt31: not run
  - java: not run
  - msvc: not run
  - drand48: not run
  - ruby: not run

## kscreen-step28: Relative-rank chain cipher: the plaintext enters the STEP c_i - c_{i-1}, keyed mod 28 (6/12 steps done)

The doublet fingerprint is also what a cipher gives whose ciphertext step is never zero (research note C1, work/log/research_2026-10-17.md): D_i = 1 + (q_i + m*K_j) mod 28 (variant A), 2^(q_i + m*log K_j) (variant B) or the (q_i + m*K_j) mod 28-th of the 28 runes other than c_{i-1} (variant C, rank), with the rare zero step as a 'ditto' that consumes a key value or not. In the c domain the plaintext is a random walk and every earlier screen was blind to it; in the step domain the decoder is a plain subtraction with no beam. work/kscreen/step28.py counts the class histogram at every (stream, offset) for the 1,447-stream library and every unit multiplier of Z28, with planted-key recovery (variants A, B, C and both modes), CPU/CUDA agreement and matched nulls; work/step_periodicity.py scans periodic keys (lags to 3,000).

- not run yet (CUDA only)

## prng-step: Seeded-PRNG pads for the step-domain cipher, window 0.7: all ten generators (0/20 steps done)

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
