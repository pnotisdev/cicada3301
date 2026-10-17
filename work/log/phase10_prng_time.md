# Phase 10: generators seeded with a millisecond timestamp (prng-time, 2026-10-17, laptop)

Scope: LP2 (sections 0.7-0.15). **Nothing in LP2 is solved.** Proposal 2 of `work/log/hypotheses_2026-10-17.md`.

## Why

Every 32-bit seed of ten generators has been swept (PHP `mt_rand`, glibc `random`, .NET `Random`, Python, MT19937, Java,
MSVC, drand48, Ruby; dictionary and boundary-free scores). That covers every second-resolution `time(NULL)` seed of
any year, but not two common ways a 2012-2014 program seeds from the clock in milliseconds:

| language | call | seed the generator sees | covered before |
|---|---|---|---|
| Java | `new Random(System.currentTimeMillis())` | 48 bits of the long (java.util.Random keeps 48) | no (32-bit seeds only) |
| Python 2/3 | `random.seed(int(time.time() * 1000))` | MT19937 `init_by_array` with the 32-bit words of the int: two words above 2^32 | no (one word only) |
| Ruby | `Random.new(ms)`, `srand(ms)` | the same two-word `init_by_array` | no |
| PHP, C, .NET, Perl | `mt_srand`, `srand`, `new Random(int)`, `srand` | truncated to 32 bits | yes |

The window is 2012-01-01 .. 2014-02-01 UTC (1325376000000 .. 1391212800000 ms), about 6.6e10 seeds per generator, swept
by UTC month, newest first: the book appeared in January 2014, so a key made while it was written comes before that.
The page images carry no EXIF dates and the PDF is a 2017 "Print To PDF" re-render, so there is no tighter bound.

## What was built

- `work/prngx` (engine): `pymt` now seeds like CPython for any integer: the 32-bit words of |n|, least significant
  first (one word below 2^32, so every earlier pymt result is unchanged; two words above). Java needed no change:
  `raw_n` already applies the 48-bit scramble to the whole seed. New: `PRNGX_MAPS=a,b,..` restricts the key maps of
  `sweep` / `bgsweep` (default: all), and `keys <gen> <seed> <map> <count>` prints one seed's key values (reference for
  a GPU port).
- `work/prngx/time_campaign.py`: `list`, `run <gen> <YYYY-MM | YYYY-MM-DD:YYYY-MM-DD>`: one boundary-free sweep
  (`bgsweep`, English rune-bigram score of the first 120 runes of section 0.7, skip and coin models, both signs, plain
  and Atbash), then the whole-section check. Maps: Java 0 `nextInt(29)`, 1 `(int)(nextDouble()*29)`,
  2 `Math.abs(nextInt()) % 29`; Python/Ruby 2 `randrange` / `randint` / `choice` (top 5 bits, rejection), 3 Ruby
  `rand(n)` (low 5 bits, rejection), 5 `random() * 29`. The other MT maps (0, 1, 4) belong to languages that never seed
  with two words and are left out.
- `work/prngx/time_verify.py`: rebuilds a candidate's keys with code independent of the Rust engine (CPython's own
  `random.Random`; the java.util.Random specification in `ref/gen_vectors.py`), decodes the whole section with the
  bigram beam `work/phpmt/bg.py::ref_decode` (which the Rust decoder mirrors) and compares with 8 random timestamps of
  the same month. Candidate: at least +2.0 per rune and 5 above every control (a true key keeps about +10 per rune).
- Campaign `prng-time` in `jobs/overnight.py`: build, vectors, gate (`tests/test_prngx_time.py`), then one step per
  (month, generator), Java and Python alternating, newest month first.

## Validation (all on the laptop)

- **Generators.** `ref/vectors.txt` gained 54 lines: CPython at seeds 2^32, 2012-01-01, mid-2013, 2014-01-01,
  2014-01-07 (in ms), 2^40 + 12345, a negative seed (Python uses |n|) and 2^48 - 1 (raw, `randrange`, `random()`); Java
  at the same seeds plus 42 and 0 (`nextInt()`, `nextInt(29)`, `nextDouble()`). The Java reference is written from the
  specification (no JVM here) and reproduces the published values of seeds 42 and 0. **119 of 119 vectors match**; the
  previous build fails exactly the 24 large-seed Python lines, the large Java seeds already passed.
- **Key streams.** `prngx keys` equals the independent Python keys over 200 values for Java maps 0/1/2 and Python maps
  2/3/5, including two-word seeds, 2^32 and negative seeds (8 cases).
- **Planted timestamp seeds** (English windows, skip / coin, both signs, plain / Atbash): Java 1388534412345 map 0,
  Java 1370000004242 map 1 (coin, sign -1, Atbash), Python 1389052800777 map 2 (coin, sign -1), Python 1325400000123
  map 5 (Atbash): each at rank 1 with the exact seed, map, sign and alphabet, screen score +988 (sweeps of +-100,000 seeds).
  The whole-section check gives +8.11 per rune for both checked plants, against controls of at most -9.9.
- **Null.** Random ciphertext through 200,000 seeds: best +59 (Java) and +58 (Python), against +988 for a plant and the
  +300 floor for a candidate.
- **Tests.** `tests/test_prngx_time.py` (5 tests: vectors, engine keys = independent keys, planted seeds, null, whole-section
  check) pass; the existing `test_prngx.py` and `test_prngx_bg.py` still pass with the new build.

## Speed and cost

Laptop (Ryzen 7 7730U), 6 threads, with another sweep running: Java about 71,000 and Python (3 maps) about 59,000 seeds
per second on section 0.7, i.e. about 12,000 / 10,000 per thread. One UTC month (2.6-2.7e9 seeds) is about 4-5 h per
generator on a 16-thread CPU; the whole window about 210 h for both. **The full window is GPU work.** The desktop's
boundary-free CUDA sweep (`work/phpmt/bgmt.cu`) did 2^32 seeds of a generator in about 18 minutes, so 6.6e10 is about
4.6 h per generator once the kernels take 64-bit seeds.

## GPU port (for the desktop; gates of docs/GPU_PORT.md)

1. Seeds as 64-bit integers in the generator section shared by `phpmt.cu` / `bgmt.cu` / `stepmt.cu` (`lo` and the
   per-thread offset as `unsigned long long`).
2. Java: the scramble `(seed ^ 0x5DEECE66D) & (2^48 - 1)` on the 64-bit seed (no other change).
3. Python: `init_by_array` with key length 2 (`[seed & 0xffffffff, seed >> 32]`) when `seed >= 2^32`.
4. Gates: keys equal to `prngx keys` for the vector seeds of `ref/vectors.txt` and for a sample of random timestamps;
   planted timestamp seeds recovered; random ciphertext without candidates; candidates re-checked with
   `time_verify.py` (CPU, independent keys).

## Demo on LP2 (bounded, not coverage)

The weekend the 2014 round began, 2014-01-04 00:00 to 2014-01-06 00:00 UTC (172.8 million timestamps per generator, 0.26%
of the window), section 0.7, 6 threads each next to another sweep (`results/prngx/time/*_2014-01-04_2014-01-06*`):

| generator | seeds | time | best screen score | rows >= +300 | whole-section check of the best 10 |
|---|---|---|---|---|---|
| java (maps 0, 1, 2) | 172,800,000 | 40 min | +59 | 0 | -8.8 .. -10.5 per rune (controls about -10.5), 0 candidates |
| pymt (maps 2, 3, 5) | 172,800,000 | 48 min | +59 | 0 | -9.4 .. -10.5 per rune (controls about -10.5), 0 candidates |

**Negative.** (+59 is the most a decode keeps when it stops at the 40-rune gate (below +60 after 40 runes), and no decode
ended higher; a planted timestamp seed is near +300 at the gate and scores +988.)

## Not covered

- Seeds from a float (`random.seed(time.time())` hashes the float: about 6.6e13 values per 25 months at microsecond
  resolution), from `System.nanoTime()` or from microsecond timestamps.
- Generators whose seeds are 32-bit anyway (they are in the earlier sweeps).
- A fresh timestamp seed per section: the campaign uses section 0.7 (one pad from the first LP2 rune), like the first
  pass of every earlier sweep.
