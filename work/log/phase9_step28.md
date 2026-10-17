# Phase 9: the step-domain (relative-rank) chain cipher, research note C1 (2026-10-17)

**Model.** The ciphertext step D_i = c_i - c_{i-1} (mod 29) is never zero except for a rare "ditto", and the plaintext enters the
step, keyed mod 28 (`work/kscreen/step28.py`, docstring): variant A D_i = 1 + (q_i + m K_j) mod 28; variant B D_i = 2^(q_i + m log2 K_j)
mod 29 (2 is a primitive root mod 29; key values 0 have no log and are dropped). The zero steps are the 0.66% doublets; mode `drop`
spends no key value on them, mode `keep` spends one. m runs over the 12 units of Z28. This reproduces the whole fingerprint (flat
unigrams, doublets 5x suppressed at lag 1 only, no word-boundary effect) with no ad hoc skip rule.

**Why the existing screens could not see it.** c_i is a cumulative sum of plaintext and key (a random walk); a c-domain screen subtracts
a stationary keystream from c and the plaintext's walk stays. In the step domain the decoder is a plain subtraction (no beam), the class
histogram of (J_t - m K[o + idx_t]) mod 28 is counted at every (stream, offset), and its IoC is about 1.8 for English under the true key.

**Controls (all pass; `step28.py selftest`, `work/tests/test_step28.py`).**
- Planted keys in both variants and both modes, multipliers 1 and 5, are recovered at the exact stream and offset with IoC 1.57-1.86
  (a window of 300 steps; the random maximum is about 1.30).
- A key planted in variant A is invisible to the variant B decoder (best IoC 1.17).
- The CUDA kernel equals the CPU reference setting by setting (best IoC, stream, offset) on random libraries and real windows.
- Encrypting and decoding with the key returns the plaintext classes exactly (including dittos).

**Library screen (interactive first pass, 2026-10-17 morning; the campaign `kscreen-step28` repeats it with the final file format).**
40 windows of 300 steps tiling the 8 sections; 1,447 library streams (1.29 x 10^7 stream/offset pairs); variants A and B, modes drop and
keep, 12 multipliers: best IoC 1.297 (sec0.9@1200). Four matched null replicates (655 random streams of 20,000 = the same number of pairs)
reach per-window maxima up to 1.32 (sec0.12@300 in one of them), so nothing stands out. Negative. It takes 2.5 minutes on the 2080 Ti
(0.07 s per window and setting), so the family can be widened cheaply.

**Periodic keys (`work/step_periodicity.py`, `results/analysis/step_periodicity.txt`).** Coincidence of the step classes at lag 2..3000, per
section and over the concatenated sections, both variants and modes. Controls: planted periods 97 and 400 found at z 6.5-11 (a period of 1200
in a 3000-step section only reaches z about 4.4, a limit of the data, not of the code); 20 random sections give a maximum z of 4.7 (median 4.05; other runs reached 5.3-5.5, so 4-4.5 is what chance gives for the largest of ~3,000 lags x settings). LP2: largest
z 3.69 (section 0.15, lag 58) and 3.59 over all sections concatenated. No periodic key with a period up to about 800 in any of the four settings.
This also excludes every order <= 2 linear recurrence and every polynomial key over Z28 (their periods are at most 784).

**Not covered.** Seed sweeps of the PRNGs in the step domain (research note C2); order-3 recurrences over Z28; windows other than the tiling.

## Seed sweeps in the step domain (research note C2): `work/phpmt/step.py`, `stepmt.cu`, campaign `prng-step`

For each seed of the ten generators the kernel builds the key values for 28 symbols (rand%28, randrange(28), nextInt(28), ...; variant A)
and for 29 symbols (variant B reads log2 of the non-zero values), then scores 144 settings on the first 240 steps of section 0.7 by the
index of coincidence of the decoded classes. 2^32 seeds take about an hour per generator on the 2080 Ti (1.3 million seeds per second).

- **Null tail (corrected after an independent review).** The IoC of n counts over 28 classes is a multinomial statistic, not a chi-square
  with 27 degrees of freedom: its upper tail is heavier. Exact tail by dynamic programming over (draws, sum of squared counts), checked by
  Monte Carlo (`work/tmp/ioc_tail.py`; the review's own DP agreed): at n = 240, P(IoC >= 1.30) = 4.5e-9, 1.37: 4.4e-11, 1.40: 7.0e-12, 1.45: 3.2e-13
  (chi-square would say 4e-10, 6.6e-13, 3.8e-14, 3.1e-16). A random maximum over 4 x 10^11 settings (96 per seed) is therefore about 1.417
  and over 6 x 10^11 (144 per seed) about 1.424, NOT 1.33. The sweep floor is 1.45 (about 0.2 chance candidates per generator and window); a true
  seed scores about 1.8. At 128 steps a planted seed would not have cleared the random maximum, which is why the window is 240 steps
  (K = 256 key values per seed). The library screen of `step28.py` (300-step windows, 2.5e10 settings, null maxima 1.26-1.32 per window) is
  consistent with the exact tail (Gumbel-like, location about 1.25, scale about 0.012); the earlier sentence that chi-square predicts those maxima was wrong.
- **Generators with K = 256.** The legacy PHP generator's first reload uses the already-twisted words from output 227 on; the kernel handles it
  (`tw[]` in `gen_raw`), and the key test compares 256 values of every generator, both alphabets, against the Rust `keysn` mode.
- **Rust.** `gens::set_km` / `km()` give the generators' key alphabet (29 = every earlier sweep, unchanged: all ten generators' 29-symbol key
  dumps are byte-identical to the previous build; 28 = the step classes). `phpmt keys ... [km]` and the new `phpmt keysn <gen> <lo> <hi> <out> <km> <count>`
  dump keys; `work/tests/test_gens.py` checks the 28-symbol keys of the seven new generators against CPython, NumPy and the documented algorithms
  (php, glibc and .NET follow the same raw-output rules).
- **Gates (`work/tests/test_stepmt.py`, 5 tests):** keys equal the Rust engine (3 seed ranges including the 2^31 and 2^32 edges, 10 generators, 2 alphabets);
  every score of 144 settings x 4 windows equals a numpy reference built from step28.py; a planted seed is recovered at rank 1 with its exact setting
  for every generator and both variants; random ciphertext over 2 x 10^5 seeds gives no candidate; the verifier regenerates keys and keeps a true
  seed at IoC 1.8 beyond the window while a neighbouring seed falls to 1.0.
- **A mistake worth recording:** a multiplier that is not a unit of Z28 (7, for instance) leaves only four key values and inflates every IoC to
  about 1.26; the sweeps use the 12 units only (the debugging test used 7 by mistake and looked like a leak).

**Variant C (rank), added later the same morning.** The cipher "never repeat the previous rune" can also be built as a rank: c_i is the
r_i-th of the 28 runes other than c_{i-1}, in alphabet order, r_i = (q_i + m K_j) mod 28. This is not a translation-equivariant function of the
step, so it is a different decoder from variant A: J_i = c_i - [c_i > c_{i-1}]. It is in `step28.py` (planted keys recovered in both modes, the
other variants blind), in the periodicity scan and in the seed sweeps (144 settings per seed and window). Periodicity result with a
structured null (random sections of LP2's lengths with the anti-repeat rule, 40 replicates, the same 6 settings x per-section and concatenated
scans): LP2's largest z is 4.97 (variant C, concatenated sections, lag 781 in non-zero steps), 5 of 40 random replicates reach it: nothing.
A planted-seed gate note: a multiplier m and m + 14 differ only where the key is odd, and English keeps about 77% of its coincidences under a
shift of 14 classes, so on 240 steps the two can swap places (once in 30 plants); the long verification separates them.

## Two cheap structural checks on keys that depend on the word layout (exploratory, with planted controls)

- `work/tmp/word_index_poly.py` (`results/analysis/word_index_poly.txt`): for each position j = 0..5 inside the words, the stream of the j-th
  rune of every word in book order, minus a1*w + a2*w^2 (mod 29, w = word index), 841 pairs: best IoC 1.008-1.040 against 1.012-1.043 for
  shuffled word orders. Planted control (English first runes + 3w + 5w^2): recovered, IoC 1.89. No polynomial-in-the-word-index key.
- `work/tmp/grid_key.py` (`results/analysis/grid_key.txt`): the whole book decoded with key a*w + b*j + c*w*j (24,389 triples; w = word index,
  j = position in the word): best IoC 1.0030 against 1.0036 for a shuffled book; planted control (English + 4w + 7j + 2wj) recovered, IoC 1.76.
  Both ignore the anti-repeat rule's pointer jumps, so they test keys indexed by the layout, not pointer-driven ones.

## Independent code review of the step-domain work (2026-10-17, a second agent; every number below was rechecked)

Confirmed and fixed: (1) the null tail (above): the exact multinomial tail is heavier than chi-square, the sweep floor is now 1.45 and the
docs say so; (2) the runner showed the LAST line of the verification files, i.e. the 8th/10th-ranked row, not the best: now the first data row;
(3) `prng-step/controls` could pass with every test skipped (no CuPy or Rust build): it now runs `work/tests/run_gate.py`, which fails on a
skipped test; (4) `make_windows("all")` crashed on section 0.10 (9 runes): sections shorter than NS + 2 are skipped; (5) the sweep for section 0.7
only tested key index 0 at step 1; a pad that begins at the first rune (whose own step cannot be read) puts key index 1 there: window `sec0.7@1+1`
added, so the `07` sweep is 2 windows (about 2.5 h per generator); the verifier understands the "+1"; (6) the periodicity scan had no positive
control for the concatenated-sections path (added) and an optimistic "about 4 by chance" header (corrected).
Acknowledged, not fixed: the library holds 29-valued streams, so variants A and C read `v % 28` (see the native mod-28 library below if present);
the sweep is fragile to a third convention for the zero step (121 good steps before the first zero step in the 0.7 window is about chance level);
both screens assume an uninterrupted key of at least 240-300 steps (a key that restarts per page or line is invisible); Java seeds above 2^31 as
`long` are not covered; A and B are identical in the periodicity scan (J_B is a bijection of J_A), so only A and C are independent there.

## Native mod-28 library (answering review remark 5)

`work/kscreen/export28.py` rebuilds the library with the alphabet size patched to 28 (primes, recurrences and constants' digits in base 28, hash
counter/chain bytes reduced mod 28, keywords reduced mod 28): 1,446 streams with values 0..27. Variants A and C on it (40 windows of 300 steps,
12 multipliers, drop/keep): best IoC 1.315 (sec0.15@2100); two matched nulls of 655 random streams reach 1.315 and 1.310; the best window
continued to the end of its section falls to 1.01 beyond the window (`results/kscreen/step28_library28*.tsv`, `step28_library28_verify.txt`).
Negative. The campaign `kscreen-step28` repeats these steps.
