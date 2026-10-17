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
