# Porting the seed sweep to the GPU (RTX 2080 Ti, 11 GB)

The CPU engine (`work/phpmt/src/main.rs`, `mode_sweep`) does about 0.85 M seeds/s for one window on 16 threads.
Every seed is independent, so the sweep maps directly onto CUDA threads. A 2080 Ti should reach tens to
hundreds of millions of seeds per second. That turns a full 2³² × 8-window × 3-generator campaign into minutes
and makes wider seed spaces (offsets, 2³²+) reachable.

## Kernel outline (one thread = one seed)
1. **Generate K = 160 outputs.**
   - PHP legacy MT: initialise `s[0..557]` with the 1812433253 recurrence (`fast_outputs`), then
     `out[i] = temper(twist_php(s[i+397], s[i], s[i+1])) >> 1` for i < 160. No full 624-word state is needed.
   - glibc: `r[0..504]` with the 16807 recurrence for i < 31, then `r[i] = r[i-31] + r[i-3]`; output
     `r[344+i] >> 1`.
   - .NET: the 56-entry Knuth table (`net_fill`).

   Keep state in registers and local memory; about 2.2 KB per thread for PHP.
2. **Map to keys.** Use `floor(29 * n / 2^31)` (PHP/glibc range call), `(int)(n * (1/2147483647.0) * 29)` (.NET),
   or `n % 29`. Do it in fp64 to stay bit-exact, or integer-exact: `(29 * (u64)n) >> 31` equals the PHP
   double formula for 31-bit n. Prove that on the CPU first.
3. **Decode.** For each window (constant memory: runes, word ends, `abort1/abort2`) and each of the 16 variants,
   run `decode_fast`. It has small fixed arrays (≤16 states), two early aborts, and dictionary membership by
   binary search over the sorted per-length code arrays in global memory (12,135 u64 codes, about 97 KB; fits
   L2).
4. **Collect candidates.** Write `(score, seed, window, variant)` only when the score reaches a threshold (for
   example ≥ 18; noise peaks around 14–16 per 10⁶ seeds and a planted key scores 35–44). Use an atomic counter
   into a preallocated buffer.

## Validation (must pass before any null counts)
- Bit-exactness: compare the first 160 outputs of every generator against `work/phpmt/ref/vectors.txt` and
  `net_vectors.txt` (the CPU `vectors` and `vectors_other` modes do this).
- Plant and recover: `phpmt plant <gen> …` and then the GPU sweep over a range containing the seed. It must
  return the planted seed at rank 1 for both models and both mappings (see `tests/test_phpmt.py`).
- Cross-check against the CPU: sweep the same 10⁸-seed range on both and compare the candidate sets above the
  threshold.

## Beyond the seed sweep
- `walk dsearch` (key-free alphabet search) runs millions of steps per second already; the GPU helps more by
  running thousands of independent restarts.
- Any new generator (PHP `mt_rand` with offsets, Java `Random`, ISAAC, LFSRs) slots into the same kernel as a
  different step 1.
