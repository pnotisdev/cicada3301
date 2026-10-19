# E2 benchmark detail, frozen before timing

Prerequisite E1 PASS. Seed1702, NumPy PCG64. For n300/600 and m2000/20000 draw
uniform mod29 keys. Draw ciphertext from the uniform-off-previous Markov chain
with doublet probability86/12947 (NOT an English power plant). Decoder q=.81,
v1 LM unchanged. No LP2 ciphertext is scored. Save generated inputs.

Measure all five channels, both signs, Float64 L and U together. For every cell
shape one warmup, then three independent timed calls; record wall and process
CPU times and a checksum. The median is the single-worker per-pass estimate.
Also submit all10 sign/channel passes to four workers three times; record all
batch wall/CPU times and relative speedup versus the measured sequential sums.
No other process altered. Thread limits remain4 (BLAS1).

Campaign projection: four channels (exclude uncapped skip) x2 signs per stream
and window. Read library lengths and section lengths only; count stride150
n300 windows plus nonduplicate end anchors. Linear interpolation of the measured
2000/20000 timings per channel/sign; below2000 scale the 2000 timing by m/2000
(label this optimistic for short streams). Use median measured four-worker
speedup, then explicitly extrapolate speedup4->14 linearly. Report raw serial
CPU-work hours, four-worker and fourteen-worker wall projections, and assumptions.
No claimed guarantee for real patterns, serial I/O, contention or14-thread scaling.

Budget decision for E3: estimate pilot30 windows PER length, and full199 PER
length. Compare summed serial CPU work (conservative accounting of the8 CPU-hour
cap), not optimistic14-thread walltime. Do not start an over-budget null pilot.
A budget stop is INCOMPLETE, not a cryptanalytic negative or failed correctness
gate. If projected LP2 campaign walltime14>8h, supply a new g3b GPU plan before
any implementation/use; otherwise additional GPU permission belongs under needs
your approval. Never consume desktop GPU memory merely because a plan exists.
