# G3 protocol supplement, frozen before GPU execution

G2 PASS is a prerequisite. No G2 seeds rerun. Float64 ONLY: float32 is not
implemented or accepted, and mixed-precision speed is unknown. Full pointer
range, no band/cap except the channel-defined skip5. No fast math; NVRTC
--fmad=false, --std=c++14. Scaled positive forward sums and restored log scales
are used instead of unscaled products. Support-zero must agree with CPU.

Layout: one block of 128 threads per cell; global A/B [cell,pointer,plaintext],
row contiguous; each thread handles pointers in stride128 and computes the two
possible plaintext predictions. Scatter uses double atomicAdd, so reduction order
is not bit-identical; absolute likelihood/score tolerance is 1e-8 nats. Final mass
uses fixed 128-lane shared-memory tree. Block has 128 doubles shared plus scalars.
Double atomics require compute capability >=6.0. Model table shared read-only
in global memory; numerator and denominator evaluated separately.

Frozen parity dataset: NumPy seed1703. 100,000 random cells: first 99,500 lengths
0..12, finite keys 0..20, Q=29, q cycling 0,.81,1, offsets including stream end,
both signs, all five channels. Constant-key every seventh case. Last 500 cells:
n=300/600 alternating, m=n+20, q=.81, both signs, all five channels. Additional
20 independent M04-harness training plants, five each hold/spend/skip5/coin,
both signs. CPU checks log_L, log_U AND their difference. Any failed assertion
or GPU runtime/compiler error is G3 FAIL: stop, no alternate seeds or kernel tuning.
Probe/compile is part of G3, not silently skipped.

Batch <=128 cells. The longest measured device launch must be <1s (Windows TDR
safety). If not, stop rather than retry with smaller batches. Record event times,
end-to-end rates, kernel attributes and device resource limits; occupancy bound
from registers/shared memory/threads is an estimate, not profiler-measured
achieved occupancy. Benchmark full normalized scores on the long parity cases;
do not use short-case throughput to estimate the library. Keep all input/output
arrays and errors in gpu_parity.npz plus g3.json. A golden CPU check and positive
plant cross-check are mandatory; speed alone does not pass correctness.

This is a correctness-first kernel, not yet a cascade or campaign engine.
No campaign null thresholds or library power claims follow from G3.
