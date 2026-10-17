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
