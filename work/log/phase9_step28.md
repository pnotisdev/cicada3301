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
in a 3000-step section only reaches z about 4.4, a limit of the data, not of the code); random sections give a maximum z of 4.4. LP2: largest
z 3.69 (section 0.15, lag 58) and 3.59 over all sections concatenated. No periodic key with a period up to about 800 in any of the four settings.
This also excludes every order <= 2 linear recurrence and every polynomial key over Z28 (their periods are at most 784).

**Not covered.** Seed sweeps of the PRNGs in the step domain (research note C2); order-3 recurrences over Z28; windows other than the tiling.

## Seed sweeps in the step domain (research note C2): `work/phpmt/step.py`, `stepmt.cu`, campaign `prng-step`

For each seed of the ten generators the kernel builds the key values for 28 symbols (rand%28, randrange(28), nextInt(28), ...; variant A)
and for 29 symbols (variant B reads log2 of the non-zero values), then scores 96 settings on the first 240 steps of section 0.7 by the
index of coincidence of the decoded classes. 2^32 seeds take about an hour per generator on the 2080 Ti (1.3 million seeds per second).

- **Null tail.** The IoC of n counts over 28 classes is (chi2_27 + n - 28)/(n - 1), so the upper tail is chi-square, not Gaussian: at 128
  steps P(IoC >= 1.42) is 3e-7 (45 hits in 1.9e7 random settings), a random maximum over 4e11 settings is about 1.6, and a planted seed
  at 1.8 would barely clear it. At 240 steps the random maximum is about 1.33 and a planted seed is 15 standard deviations above it, so the
  window is 240 steps and each seed needs 256 key values (K = 256). The same correction applies to the library screen of `step28.py`: its
  null maxima (1.26-1.32 in 300-step windows over 2.5e10 settings) are what chi-square predicts.
- **Generators with K = 256.** The legacy PHP generator's first reload uses the already-twisted words from output 227 on; the kernel handles it
  (`tw[]` in `gen_raw`), and the key test compares 256 values of every generator, both alphabets, against the Rust `keysn` mode.
- **Rust.** `gens::set_km` / `km()` give the generators' key alphabet (29 = every earlier sweep, unchanged: all ten generators' 29-symbol key
  dumps are byte-identical to the previous build; 28 = the step classes). `phpmt keys ... [km]` and the new `phpmt keysn <gen> <lo> <hi> <out> <km> <count>`
  dump keys; `work/tests/test_gens.py` checks the 28-symbol keys of the seven new generators against CPython, NumPy and the documented algorithms
  (php, glibc and .NET follow the same raw-output rules).
- **Gates (`work/tests/test_stepmt.py`, 5 tests):** keys equal the Rust engine (3 seed ranges including the 2^31 and 2^32 edges, 10 generators, 2 alphabets);
  every score of 96 settings x 4 windows equals a numpy reference built from step28.py; a planted seed is recovered at rank 1 with its exact setting
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
