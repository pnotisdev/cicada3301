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
| rand48 | 18 | 0.09-0.10 (random 0.078) |
| msvc | 18 | same |
| java | 20 | same |
| mt | 19 | same |
| pymt | 20 | same |

**OEIS lane** (`oeis.py`, `seq` generator): the 199,075 OEIS sequences with at least 40 terms (median 63; data from
oeis.org/stripped.gz, CC BY-NC, not committed) as keystreams, at every start offset 0-127, all 28 multipliers, both
signs, Atbash, both anti-repeat models, on the 36-rune starts of all eight unsolved sections (25.5 M (sequence,
offset) pairs x 28 x 8 x 8 windows = 4.6 x 10^10 decodes, 29 min on 12 threads): best score **15**, against **16** for a
matched null of random sequences with the same lengths, and 28 for a planted primes key (which is also found in the
equivalent sequences 2p, 3p, ...). **Negative**: no OEIS sequence is the key's first ~36 terms at any offset.

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
