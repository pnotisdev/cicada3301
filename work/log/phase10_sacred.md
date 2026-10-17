# kscreen-sacred: four stream families proposed by an outside LLM (2026-10-17, 22:15)

Scope: LP2 sections 0.7-0.15, the first 300 runes of each at every offset. **Nothing in LP2 is solved.** The outside LLM's five families for the base layer (third-party text; re-implemented, not run as sent) were built by
`work/kscreen/sacred.py` into `work/kscreen/data/sacred.ksb` and screened exactly like the library (`kscreen-sections`): both key signs, both anti-repeat models, mults 1 and 28, beam 16, IoC rule >= 1.40.

**What was built (and what the proposal got wrong).** Streams are dropped when LP2's flat IoC already excludes them as keys (predicted IoC under English > 1.003) or when they equal a library stream up to c -> a c + b.

| family | proposed | built | non-flat (excluded) | duplicates | screened |
|---|---|---|---|---|---|
| F1 s1 + t*s2 and interleaves of 20 core streams | 2,470 | 1,330 (the proposal double-counted the difference case) | 275 | 3 | 1,052 |
| F3 phi / sigma / d / Fibonacci / Lucas / Pell / triangular at p_i - 1, p_i, p_i + 1 | about 100 | 21 | 14 (+1 constant) | 2 (sigma(p) = p + 1, phi(p) = p - 1 are library streams) | 4 |
| F4 base-29 digits of 1/3301, 1/1033, 3301/1033, 1033/3301, 1/(3301*1033) | 24 | 5 (bases 10, 16, 60 digits are not uniform mod 29, so excluded as keys by the flat IoC) | 0 | 1 | 4 |
| F5 rational functions of p mod 29 | 8 | 8 | 3 | 2 | 3 |
| F2 order-4 recurrences with chosen coefficients | about 30 million | not built (the coefficient sets are arbitrary) | | | |

**Control** (`work/kscreen/sacred_selftest.py`, `results/kscreen/sacred_selftest.txt`): one key per family planted into held-out English under the anti-repeat rule (skip and coin models, both signs, with and without plaintext substitution), two plants x
three windows each: **24 of 24 windows recovered** (best hit = the planted item, IoC 1.61-2.06, re-decode at the truth 1.75-2.00). One F4 plant is best at offset 21 and not 846: that stream has period 825.

**Result** (`results/kscreen/sacred_segments.tsv`, `_verify.txt`): 1,063 streams, 629,728,288 decodes (10 min on 12 CPU threads). **Best IoC 1.369** (F1 `pell + 1/2*sigma(n)` on seg0.9); F3 best 1.285, F5 best 1.274, F4 below the 2,000-row cut-off (1.243).
The library's own best was 1.366 on 409 M decodes and the 300-stream random null's 1.318 on 188 M, so 1.369 on 630 M decodes is what extreme values of random keys do (random keys reach about 1.37 extrapolated at 10^10 decodes).
Verification: **0 of 15** re-decoded hits keep IoC >= 1.4 over the whole window. **Negative** for these four families at 300 runes per section.

Not covered: F2; other pairings and ratios of the F1 core streams; pointer schemes that need bases longer than 20,000 values (F_i or i^2 as an index); windows after the first 300 runes of each section. The null was the existing 300-stream random null, smaller than the family.

## Round 2: DeepSeek's second batch, asked directly through the pi harness (22:20)

`work/ask_deepseek.py` (pi, provider deepseek, model deepseek-flash, medium thinking, no tools, no project files, no session; 2 min 51 s) was sent one self-contained prompt: the puzzle facts, the flat-IoC fingerprint, the screen's rule, the excluded list, round 1's result and
the four constraints round 1 had broken (uniform marginal mod 29, no affine duplicates of library streams, exact counts, no base longer than 20,000 values). The prompt and the reply are kept in the git-ignored `work/ref/deepseek/` (third-party text is data).
The reply obeyed the constraints (exact uniformity proofs, exact counts, 'all five are long shots', lore marked UNSURE, no invented citations). Its five families, as rebuilt by `work/kscreen/sacred.py --round 2` (my own code, not run as sent):
G1 n^-1 mod p, G2 discrete log mod p, G3 g^n mod p (p = 59, 233, 349, 523, 929, all = 1 mod 29, whole periods so the stream is exactly uniform), G4 n^3 mod p (p = 59, 233, 929), G5 the sum of the two base-29 digits of n (period 841): **19 streams**, none excluded by the flat IoC, none a duplicate.
All are periodic with period 58-928 (the drift-period scan had already excluded periods up to about 400 key-agnostically, so effectively p = 523 and 929 and the borderline 349 are the open ones).

**Control** (`sacred_selftest.py --set sacred2`, `results/kscreen/sacred2_selftest.txt`): 5 families x 2 plants x 3 windows: **30 of 30 windows recovered**, IoC 1.56-2.10 (periodic streams are found at an equivalent offset, e.g. 24 for the truth 256 at period 58).
**Result** (`results/kscreen/sacred2_segments.tsv`, `_verify.txt`): 1,250,080 decodes (1 s on the CPU; the GPU was not used): **best IoC 1.249** (G1 inverse mod 233, seg0.9); per family G1 1.249, G2 1.214, G3 1.202, G4 1.210, G5 1.213; verification **0 of 15**. **Negative.**
(The random null in the report, 1.318, is the library campaign's 300 streams over 188 M decodes; at 1.25 M decodes the best of random keys is lower, so no comparison is made with it.)

## Round 3: streams from the book's numbers (23:50)

After an outside LLM's leads on the two magic squares (`phase10_squares.md`), the cheap streams they suggest were built with `sacred.py --round 3` and screened like the others:
H1 phi, sigma and d of the progressions 3301 i + 1033 and 1033 i + 3301 (6 built; d(n) is small and not flat, so 2 were dropped by the flat-IoC filter: 4 kept); H2 the primes p_(k i) for k = 58, 87, 116, 174, 348, 464, 1033, 3301 (8 kept; the index multiples from pi(1033) = 6 x 29 and pi(3301) = 16 x 29;
decimations up to 29 were already covered by `kscreen-hyp`); H3 base-29 digits of 1/45415, 45415/1033 and 45415/3301 (3 kept; 45415 is the proposal's unsupported reading of FIRFUMFERENFE as 'vier funf vier eins funf'; n x 45415 is the library's `n` because 45415 = 1 mod 29). **15 streams, none a duplicate.**
Not built: the 25-cycles of phi / sigma of the square's numbers (period 25: excluded by the drift-period scan, which is key-agnostic).

**Control** (`sacred_selftest.py --set sacred3`, `results/kscreen/sacred3_selftest.txt`): 3 families x 2 plants x 3 windows, **18 of 18 recovered**.
**Result** (`results/kscreen/sacred3_segments.tsv`, `_verify.txt`): 6,849,856 decodes (7 s on 12 CPU threads; the GPU was not used by this run): **best IoC 1.273** (H2 p_(464 i) on seg0.11); H1 best 1.265 (sigma(1033i+3301)), H3 best 1.230; verification **0 of 15**. **Negative.**
