# PR: prngx: five more seeded-PRNG families and an OEIS integer-sequence lane

**Branch:** `research/prngx-generators` (new crate `work/prngx`, tests, results; no existing file modified)

## What this adds
- `work/prngx` (Rust): the skip-aware dictionary decoder of `work/phpmt` (copied verbatim by `assemble.py`, so
  results are directly comparable) with five more generators, the CLI of phpmt (`vectors | plant | sweep | verify`):

  | gen | what it is | maps (key from raw output) |
  |---|---|---|
  | `mt` | MT19937 `init_genrand(seed)`: C++ `std::mt19937`, PHP >= 7.1 `mt_srand`, numpy `RandomState(seed)` | raw%29, floor(raw*29/2^32), top-5-bit rejection (Python `randrange`), low-5-bit rejection (numpy `randint`), (raw>>1)%29, float53*29 |
  | `pymt` | MT19937 `init_by_array([seed])`: Python `random.seed(int)`, Ruby `Random.new(int)` | same six |
  | `msvc` | Microsoft C `rand()` LCG (15-bit) | v%29, v*29>>15, v*29/32767 |
  | `java` | `java.util.Random(seed)` (48-bit LCG; negative seeds supported) | `nextInt(29)` with its rejection, `(int)(nextDouble()*29)`, abs(nextInt())%29 |
  | `rand48` | `srand48`/Perl `srand`+`rand` (48-bit LCG) | lrand48()%29, floor(29*drand48()) |
  | `seq` | an integer-sequence library (OEIS): key = multiplier * term mod 29 | 28 multipliers |

  Every (map) is decoded under 8 cipher variants (skip/coin anti-repeat model, sign, Atbash).
- **Validation (gates before any sweep counted):** 65 reference vectors from real implementations all match
  (`ref/gen_vectors.py`: numpy and Python for the two MT families including the randrange/randint/float maps;
  published MSVC `srand(1)`/`srand(0)` sequences; published `java.util.Random` values; `srand48(1)`), and the Java
  `nextDouble` reconstruction reproduces the known 0.7275636800328681. Planted seeds are recovered at rank 1 for
  every generator (score 44 against noise <= 20), and `tests/test_prngx.py` (2 tests, 4 s) automates both.
- `campaign.py` (resumable stage A / stage B sweeps), `verify.py` (whole-segment re-decode of the best 20 against
  random-seed controls; flags only above 0.25 because selection noise alone reaches ~0.12), `oeis.py`,
  `short_windows.py`.

## Results
**Stage A: the human-plausible seeds** ([0, 2^27) = small numbers and dates YYYYMMDD, [1.3e9, 1.5e9) = Unix time
2011-2017), key starting on LP2 page 0, 334 M seeds per generator, all maps and variants:

| gen | best screen score (planted 35-44; noise ceiling ~18) | whole-segment top 20 |
|---|---|---|
| rand48 | 18 | 0.085-0.118 (random seeds 0.078; a true key ~0.8) |
| msvc | 18 | 0.082-0.107 |
| java | 20 | 0.085-0.110 |
| mt | 19 | 0.085-0.112 |
| pymt | 20 | 0.086-0.107 |

**OEIS lane** (`oeis.py`, `seq` generator): the 199,075 OEIS sequences with at least 40 terms (median 63; data from
oeis.org/stripped.gz, CC BY-NC, not committed) as keystreams, at every start offset 0-127, all 28 multipliers, both
signs, Atbash, both anti-repeat models, on the 36-rune starts of all eight unsolved sections (25.5 M (sequence,
offset) pairs x 28 x 8 x 8 windows = 4.6 x 10^10 decodes, 29 min on 12 threads): best score **15**, against **16** for a
matched null of random sequences with the same lengths, and 28 for a planted primes key (which is also found in the
equivalent sequences 2p, 3p, ...). **Negative**: no OEIS sequence is the key's first ~36 terms at any offset.

Same lane on the other places a key could restart: the first ~36 runes of 46 page starts and 10 short heading windows
(14-36 runes; 56 windows), start offsets 0-15, same settings (`results/prngx/seq/{oeis,null}_pagesheads_off16.*`, 98 and
112 min): best score **17** (page 56 start, library line 143194 at offset 7) against **19**
for the matched random-sequence null. **Negative.** Only the null was run on this window set; the planted-key control
is the primes plant on the 8-section windows above, and the 14-rune windows have less power than the 36-rune ones.

**KDF / stream-cipher lane** (`kdf_streams.py`, `results/prngx/kdf/`): for each of the 23,976 Cicada-lore strings (the
`hashscan` lore list: Cicada phrases and numbers, every word and 2-4-word phrase of the solved pages, the keyword list,
case/space variants) the keystreams of RC4 and RC4-drop768 (the passphrase as key), AES-128-CTR (key MD5) and AES-256-CTR
(key SHA-256) with a zero nonce, ChaCha20 (key SHA-256), PBKDF2-HMAC-{SHA-1, SHA-256, SHA-512} with an empty salt and
1, 1000 and 4096 iterations, and scrypt (N = 1024, r = 8, p = 1), each turned into key values by two maps (b % 29, and
reject b >= 232 then % 29): 719,280 keystreams through the `seq` lane (start offset 0, 28 multipliers, both signs, Atbash,
both anti-repeat models) on LP2 page 0. The stream generators match test vectors (RC4 "Key"/"Plaintext", the RFC 6070
PBKDF2 vector, AES-CTR first block = AES-ECB of zero) and a planted RC4 passphrase is recovered at rank 1 through the
whole pipeline (`tests/test_kdf_streams.py`). Best screen score 20 (noise ceiling ~20); the whole-section re-decode of
the best 20 (with long streams and random-string controls) gives 0.075-0.089 against 0.078 for random strings.
**Negative.**

**Stage B** (the other 92% of the 32-bit seeds) is queued in `campaign.py` in chunks of 2^28 seeds for `rand48`, `msvc`
and `java` (about 1.7, 2.3 and 3.4 hours on a 16-thread CPU; java also covers the negative ints). Results of the chunks that finished on the laptop are in
`results/prngx/*_b_*.tsv`; the rest is for the desktop (see below). `mt` and `pymt` full sweeps cost ~6 h each on CPU.

## For the reviewer / the desktop GPU
- The `seq`/OEIS lane and the five generators are all embarrassingly parallel; the LCGs (`msvc`, `java`, `rand48`) are
  a few lines of CUDA each and the MT families can reuse the phpmt kernel (full 624-word twist per seed, or the
  PHP-style partial twist for the first ~230 outputs). `campaign.py run stageB` skips finished chunks.
- Open: other conventions of the same generators (e.g. `random.choice`/`shuffle`-based keys, Python `random()` with 32
  vs 53 bits, `rand() % 29` after `srand(time)` on other libcs), PRNG state recovery from the page-0 text assuming a
  *partial* dictionary, and offsets other than 0 (key starting after a title or heading).

## Review (stronger-model pass, 2026-10-17)

Merged locally; the code was read first. Network use exists only in `oeis.py fetch` (oeis.org/stripped.gz, an explicit command, not run by anything else); the other subprocess calls start the
crate's own binary. The crate (no dependencies) builds and all five tests pass (65 reference vectors, planted seeds for five generators, the KDF streams against RC4 / PBKDF2 test vectors, a planted RC4
passphrase through the whole pipeline).
- **Stage B is not needed on the desktop.** `rand48`, `msvc` and `java` are the desktop's `drand48`, `msvc` and `java` generators, whose full 2^32 seed spaces were swept on the GPU for the window 0.7
  with the first two key maps of each (the third map of `msvc` and `java` here, `v*29/32767` and `abs(nextInt())%29`, is not covered), both with the dictionary score (`prng-more`) and with the boundary-free bigram score
  (`prng-bg`, work/log/phase9_boundaries.md): all negative. `mt` (raw%29 and the other five maps) overlaps the desktop's `mt32`/`mt31`/`py3` maps only partly.
- **Same reservation as hashscan:** the decoder is the dictionary one, so every negative of this PR (the 334 M stage-A seeds per generator, the 199,075 OEIS sequences, the 719,280 KDF streams) is a
  dictionary-score negative. The OEIS and KDF lanes are the next candidates for a boundary-free rescore.
- The "primes plant on the 8-section windows" is the only planted control for the page-start and heading windows; the short (14-rune) windows have less power than the 36-rune ones, as the note says.
