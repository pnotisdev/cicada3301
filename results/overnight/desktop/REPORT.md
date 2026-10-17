# Overnight campaigns: report from desktop

Generated on desktop at 2026-10-17 06:37:55 by `python jobs/overnight.py`. Thresholds and method: docs/CAMPAIGNS.md.

**Controls:** unit tests and kscreen selftest passed on desktop; null results below are validated.

## setup: Build engines and data (3/3 steps done)

Cargo builds of the three Rust engines and the generated inputs (fast when nothing changed).


## selftest: Regression tests and keystream-screen controls (1/1 steps done)

The 44 unit tests (solved pages, transcription, statistics, engines) and the kscreen plant/recover and random-key null. Nothing else is trusted unless this passes.

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

## kscreen-restarts: Keystream library restarted at headings and page starts (5/5 steps done)

Same library, with the key restarting at each red heading / paragraph start (10 windows) and at each page start (46 windows).

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

## prng-all: Seeded-PRNG pads with a fresh seed per section (6/6 steps done)

phpmt sweeps of every seed of PHP<7.1 mt_rand, glibc random() and .NET System.Random on all 8 sections (the single-section runs only covered LP2 page 0), then full-segment verification of the best candidates.

- php: swept 4294967296 seeds in 2628 s; best score 21; verification:   screen  18 seed   16096334 seg0.7 model 0 map 0 sign  1 atb 1: full 0.096 (random seeds 0.078 +- 0.007, z +2.5)
- glibc: swept 4294967296 seeds in 2451 s; best score 21; verification:   screen  19 seed 2235614708 seg0.15 model 0 map 0 sign -1 atb 1: full 0.082 (random seeds 0.078 +- 0.002, z +2.1)
- net: swept 2147483648 seeds in 1206 s; best score 21; verification:   screen  18 seed  174175237 seg0.15 model 1 map 0 sign -1 atb 1: full 0.086 (random seeds 0.078 +- 0.002, z +3.5)
