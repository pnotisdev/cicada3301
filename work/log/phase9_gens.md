# Phase 9: seven more key generators for the seed sweeps (2026-10-17)

The seed sweeps covered PHP < 7.1 `mt_rand`, glibc `random()` and .NET `Random`. A program that enciphered LP2 with an
anti-repeat check could just as well have used Python, C++, Java, C, Perl or Ruby. With the CUDA sweep (a full 2^32 seeds
of one window in 10-20 minutes) the whole small-seed space of each of these is cheap to cover.

| name | generator, seeding | map 0 | map 1 |
|---|---|---|---|
| `py3` | CPython `random.seed(n)`: MT19937 `init_by_array([n])` | `randrange(29)`: top 5 bits of an output, redraw 29-31 | `int(random() * 29)` (= Python 2's `randrange`) |
| `mt32` | `std::mt19937(n)`, PHP >= 7.1: `init_genrand(n)` | `uniform_int_distribution(0,28)` (Lemire form, GCC >= 11) | `gen() % 29` (= PHP 7 `mt_rand(0,28)`) |
| `mt31` | the same, 31-bit output | `(y >> 1) % 29` (PHP 7 `mt_rand() % 29`) | `floor(29 * (y >> 1) / 2^31)` |
| `java` | `java.util.Random(int n)` (48-bit LCG) | `nextInt(29)` | `(int)(nextDouble() * 29)` |
| `msvc` | MSVC `srand(n); rand()` (x*214013 + 2531011) | `rand() % 29` | `rand() * 29 / 32768` |
| `drand48` | `srand48(n)`, Perl >= 5.20 `srand(n)` | `int(drand48() * 29)` | `lrand48() % 29` |
| `ruby` | Ruby <= 2.7 `Random.new(n)`: `init_by_array([n])` | `rand(29)`: low 5 bits, redraw > 28 | `int(rand() * 29)` (res53) |

Seeds are all 2^32 values (Java and the others read them as the signed 32-bit int a program would pass). Each seed is run
through the same 16 cipher variants as before (sign, Atbash, both key maps, skip / coin model) with the same skip-aware
decoder and dictionary score; the existing sweeps are unchanged.

## Validation

- **The rules** (`work/phpmt/src/gens.rs`) are checked in `work/tests/test_gens.py` against independent references:
  CPython's own `random` module gives `py3` (raw 32-bit stream, `randrange(29)`, `int(random() * 29)`) and Ruby's MT stream;
  NumPy's legacy `RandomState` gives `mt32` / `mt31`; Java, MSVC and drand48 are Python re-implementations of the documented
  algorithms anchored to published first outputs (Java seed 42 -> -1170105035, MSVC `srand(1)` -> 41, 18467, 6334, 26500,
  19169, drand48 seed 1 -> 0.0416303447718782, `std::mt19937` default seed -> 3499211612). 7 generators x 2 maps x 9 seeds
  (including 2^31 and 2^32 - 1) x 160 key values: identical.
- **The CUDA port** (`work/phpmt/phpmt.cu`, `gpu.py`): key values of both maps for 496 seeds per generator and 153,088
  decode scores per generator are identical to the Rust engine (`gpu.py selfcheck`, part of the runner's validation).
- **Planted seeds** (`tests/test_phpmt_gpu.py`): English enciphered with a known seed, for each generator, both maps, both
  signs, Atbash on and off, skip and coin models; the GPU sweep returns the seed at rank 1 (score 35-44 against noise <= 17).
  This found and fixed a bug in the plant mode itself: for the new generators the coin of the coin model must spend a key
  value, as the decoder assumes.
- Speed (RTX 2080 Ti, one window, 16 variants): 4 M seeds in 0.5-1 s, i.e. 10-20 minutes for 2^32 seeds.

## Not covered

Ruby >= 3.0 seeds with `init_genrand` for single-word seeds (equals `mt32` with Ruby's mapping), libc++'s `uniform_int_distribution`,
Python 2 `random.seed` of strings or floats, Java `long` seeds above 2^32, any generator seeded from time or a string. A seed
outside 32 bits is out of reach of this exhaustive method.

## Results

`results/prng/<gen>_07.*` (window 0.7) and `<gen>_all.*` (a fresh seed per section) once the campaign `prng-more` has run;
see `results/overnight/desktop/REPORT.md`.
