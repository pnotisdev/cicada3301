# Overnight campaigns: report from desktop

Generated on desktop at 2026-10-17 01:38:13 by `python jobs/overnight.py`. Thresholds and method: docs/CAMPAIGNS.md.

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

Same library, with the key restarting at each red heading / paragraph start (10 windows) and at each page start (46 windows).

- library x 10 heading restarts: best IoC 2.118 (**above threshold, see verification**; 460,443,636 decodes in 2 min)
- library x 46 page restarts: best IoC 1.679 (**above threshold, see verification**; 2,353,378,584 decodes in 22 min)
- matched null (random keystreams, same windows/settings): best 1.597
- verification (library_heads_verify.txt): 15 of 15 re-decoded hits keep IoC >= 1.4 over their whole window and beat their own keystream's random offsets by 0.15 (CANDIDATE - inspect)
- verification (library_pages_verify.txt): 15 of 15 re-decoded hits keep IoC >= 1.4 over their whole window and beat their own keystream's random offsets by 0.15 (CANDIDATE - inspect)

## kscreen-recurrences: Every linear recurrence and polynomial key mod 29 (18/31 steps done)

All linear recurrences of order 1-3 mod 29 (Fibonacci, Lucas, Pell, Tribonacci, Padovan and 23,000 others) from every start state, and all polynomial keys up to degree 3, on the 8 sections.

- order-1 recurrences: best IoC 1.194 (below the 1.40 threshold; 12,544 decodes in 0 min)
- order-2 recurrences: best IoC 1.272 (below the 1.40 threshold; 10,913,280 decodes in 0 min)
- polynomials deg <= 3: best IoC 1.232 (below the 1.40 threshold; 11,316,032 decodes in 0 min)
- order-3 recurrences: not run yet
- matched null (random keystreams, same windows/settings): best 1.318

## rescreen: Dictionary screens rerun with the corrected word segmentation (2/4 steps done)

Screens 1 and 2, the reverse-direction screen and the heading-restart screen were run before the word-wrap fix (wrapped words were split, a handicap for a true key). English-dictionary scoring.

- screen 1 (3 offsets):   0.155  CONTROL random 26                        seg 0.13 off=start    sign=+1 atbash=False b=24
- screen 2 (all offsets): top 20 non-control:
- reverse direction: not run
- heading restarts: not run

## dsearch: Key-free secret-alphabet search, large (0/86 steps done)

walk dsearch: a per-word additive key behind any secret outer alphabet, with m = 1-8 position phases and gap sets {1,2} and {1,2,3} (the earlier runs used gap 1 only), against 4 structure-free surrogates each. Starts with a synthetic positive control that must recover the planted alphabet.

- positive control (synthetic m=5): not run
- not run yet

## payload: The 256-byte payload, corrected bytes (0/2 steps done)

Hash identity tests and 832k passphrase AES/RC4/XOR decryptions, rerun on the corrected payload (5 bytes fixed in Phase 2/research; earlier runs and the community's used the uncorrected bytes).

- hashes: not run
- decryptions: not run

## kscreen-multipliers: Keystream library x every key multiplier (0/2 steps done)

The library again on the 8 sections with all 28 key multipliers (c = p + m*k), e.g. 3301*k = 24*k mod 29.

- library x 28 multipliers: not run yet
- matched null (random keystreams, same windows/settings): best 1.318

## prng-all: Seeded-PRNG pads with a fresh seed per section (0/6 steps done)

phpmt sweeps of every seed of PHP<7.1 mt_rand, glibc random() and .NET System.Random on all 8 sections (the single-section runs only covered LP2 page 0), then full-segment verification of the best candidates.

- php: not run
- glibc: not run
- net: not run

## kscreen-chain: Ciphertext-feedback ciphers c_i = a*c_{i-1} + p_i + k_i, a = 1..28 (1/141 steps done)

The doublet fingerprint (c_i - c_{i-1} flat except that 0 is missing) is what a cipher with ciphertext feedback gives if the encryptor avoids the shift that would repeat a rune. Every earlier screen assumed c = p + k, so none of them could see such a key. For each multiplier a the 8 sections are rewritten as c' = c_i - a*c_{i-1} with the collision check against (1-a)*c_{i-1} (work/kscreen/chain_windows.py) and screened with the 1,447-keystream library, every order-2 linear recurrence and every cubic polynomial, at every offset, both anti-repeat models, any plaintext language and alphabet.

- controls: not run
- not run yet

## prng-more: More seeded-PRNG pads: Python, C++/PHP 7, Java, MSVC, drand48/Perl, Ruby (0/28 steps done)

py3 (CPython random.seed), mt32 / mt31 (std::mt19937, PHP >= 7.1), java (java.util.Random), msvc (rand()), drand48 (drand48, Perl) and ruby (Ruby <= 2.7), each with two natural key mappings, all 2^32 seeds, 16 cipher variants, first on window 0.7 and then with a fresh seed per section (work/phpmt/src/gens.rs; the CUDA port is validated against the Rust engine, which is validated against CPython, NumPy and published vectors).

- window 0.7 (one pad from the start of LP2):
  - py3: not run
  - mt32: not run
  - mt31: not run
  - java: not run
  - msvc: not run
  - drand48: not run
  - ruby: not run
- every section:
  - py3: not run
  - mt32: not run
  - mt31: not run
  - java: not run
  - msvc: not run
  - drand48: not run
  - ruby: not run
