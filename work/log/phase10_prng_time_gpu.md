# Phase 10: the 64-bit CUDA port of the boundary-free sweep (prng-time, 2026-10-17 14:20)

Scope: LP2 (sections 0.7-0.15). **Nothing in LP2 is solved.** The user asked for the port proposed by the laptop's branch `research/new-hypotheses` (reviewed in `docs/prs/new-hypotheses.md`, not merged) with
the gates of `docs/GPU_PORT.md`. The laptop's Rust changes (two-word `pymt`, `prngx keys`) are not on `main`, so the port was gated against INDEPENDENT references instead, which is stricter.

## What was built (all new files; no validated kernel or gate was changed)

- `work/phpmt/make_bgmt64.py` -> `bgmt64.cu`: `bgmt.cu` with seven exact-snippet substitutions (each must occur the stated number of times): `mt_state` takes a 64-bit seed and runs `init_by_array` with the two
  32-bit words when the seed is 2^32 or more (one word below, as before); Java takes the whole seed through `JSEED` (a seed below 2^32 stays a sign-extended int); `JALT=1` swaps Java's second map for `abs(nextInt()) % 29`
  (as prngx does: wrapping abs, unsigned %); the kernel passes the 64-bit seed to `gen_keys`. The candidate record keeps the low 32 bits.
- `work/phpmt/bg64.py`: `sweep <py3|ruby|java|java-abs> <07|all> <lo> <hi> <out.tsv>` (seeds below 2^63; the chunk base restores the high bits of each recorded seed), `verify` (whole-section decode with independent keys, 8 random
  timestamps as controls, CANDIDATE needs +2.0 per rune and 5 above every control), `probe`.
- `work/phpmt/ref_keys64.py`: independent key streams (CPython's `random` for py3 and, with the documented rule, ruby; `java.util.Random` written from its specification, which reproduces the published values of seeds 42 and 0)
  and a planter that ports the encryption rule of the Rust `plant` mode.
- `work/phpmt/time_gpu.py`: the 25 UTC months 2012-01 .. 2014-01 newest first, resumable, `--hours` budget.
- `work/tests/test_bgmt64.py`: the gate (8 tests).

## Gates (`python work/tests/run_gate.py work.tests.test_bgmt64`: 8 tests OK, 0 skipped)

1. `bgmt64.cu` equals what `make_bgmt64.py` builds; the reference generators reproduce the published Java values.
2. Kernel keys = independent references for py3, ruby, java, java-abs at 2^31, 2^32 - 1, 2^32, 2^32 + 1, 2^33 - 1, 2^33, 1325376000000, 1388534412345, 1391212800000, 2^40 + 12345, 2^41, 2^48 - 1 and 25 random
   timestamps of 2012-2014 (both maps, 160 values).
3. Below 2^32 the 64-bit kernel's keys and all decode scores equal the validated 32-bit kernel (py3, ruby, java; seeds 3000-3005, 2^31 - 1, 2^31, 2^32 - 2).
4. Above 2^32 (2^32 + 5, 1388534412345, 2^40 + 1) every score of all 16 variants equals `bg.ref_decode` on the independent keys, for all four generators.
5. Seven planted timestamp seeds (py3 maps 0 and 1, ruby, java maps 0 and 1, java-abs, and py3 at 2^32 + 1234 in a chunk that straddles 2^32) are recovered at rank 1 (seed, map, sign, alphabet; score above +300, every other
   row below 150), planted by the independent planter.
6. Random ciphertext: 0 candidates in 300,000 seeds at 1388534400000 and across 2^32 for every generator.
7. The whole-section check confirms a plant (+7.28 per rune against controls -12.4 +- 1.8) and rejects the neighbouring seed (-9.32).
One test failed on its first run because of a wrong string match in the test itself (a tab after the seed, not a space); the check it tests had worked. Fixed, rerun clean.

## Demo (2014-01-04 00:00 .. 2014-01-06 00:00 UTC, 172.8 M millisecond timestamps per generator, section 0.7, boundary-free, +300 floor)

| generator | time | speed | candidates |
|---|---|---|---|
| py3 (maps randrange, random()) | 27 s | 6.4 M seeds/s | 0 |
| java (nextInt(29), nextDouble) | 16 s | 10.8 M seeds/s | 0 |
| java-abs (nextInt(29), abs(nextInt()) % 29) | 16 s | 10.8 M seeds/s | 0 |
| ruby (rand(29), float) | 27 s | 6.4 M seeds/s | 0 |

The laptop's CPU sweep of the same window (py3 and java, 40-48 min each) also found nothing: the two agree. Files: `results/prng/time_gpu/`.

## Cost of the full window

2012-01-01 .. 2014-02-01 UTC = 6.58e10 timestamps: about 2.9 h per py3 or ruby, 1.7 h per java map set (java and java-abs share map 0, so 3.4 h for both): `python work/phpmt/time_gpu.py run <gen> --hours H`
(month by month, newest first, resumable, whole-section check of each month's best rows). All four generators: about 9 h. Not started: it is the user's GPU time to allocate.

## Limits

Section 0.7 only (one pad from the first LP2 rune), like the first pass of every earlier sweep. No Ruby is available: the ruby keys are the documented rule on top of CPython's MT19937 (rand(29) = low 5 bits with rejection,
float = res53), unconfirmed against a Ruby. Seeds from a float (`random.seed(time.time())`), `System.nanoTime()` or microseconds are outside the window. The port is not wired into the laptop branch's `prng-time` campaign
(unmerged); when that branch merges, its month steps can call `bg64.py sweep` instead of the CPU `bgsweep`.
