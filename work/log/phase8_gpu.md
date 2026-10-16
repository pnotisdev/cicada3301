# Phase 8: CUDA ports of the keystream screen and the seed sweeps (2026-10-17)

Hardware: RTX 2080 Ti (Turing, cc 7.5, 68 SMs, 11 GB), driver with CUDA 13.4, CUDA Toolkit 12.6 installed, CuPy
14.2 (`cupy-cuda12x`) with kernels compiled at run time by NVRTC. CPU for comparison: Ryzen 7 2700X, 8 cores /
16 threads, 32 GB. Gates and results in `docs/GPU_PORT.md`; this file is the working record.

## CPU baseline on this PC

- kscreen: 1.4 M decodes/s with 16 threads (`screen data/segments.txt rand:60:11`: 37.7 M decodes in 27 s). The
  laptop did 0.36 M/s, so this PC is 3.5x faster before any GPU. The campaign hour estimates in `docs/CAMPAIGNS.md`
  (3.6 + 7.5 + 5.0 h) were for the laptop-era figures; at 1.4 M/s they are about 0.65 + 1.8 + 1.1 h.
- seed sweep: 222 k seeds/s for all 8 windows x 16 variants (8 M seeds in 36 s), so a full 2^32 sweep is 5.4 h, glibc
  the same, .NET (2^31) 2.7 h: `prng-all` is ~13.5 h on the CPU. That is where a GPU pays most.

## Two problems found in the CPU engine on the way

1. **Top-hit list.** `mode_screen` rejected a hit with `ioc > hits[top - 1].ioc`, but between the first `top` and
   `2 * top` entries the vector is unsorted, so `hits[top - 1]` was an arbitrary entry. A thread could therefore drop a
   hit that belonged in the top 2000, and the list depended on thread scheduling (two runs gave different lists,
   histograms and window bests did not). Fixed with an explicit threshold updated at each prune. Effect on earlier
   results: none for per-window bests, histograms, run counts or any "best IoC" taken from the window lines; a hit
   above the 1.40 decision threshold could only have been missed if that arbitrary entry was itself above 1.40.
2. **Unstable sort at the beam cut.** `sort_unstable_by` is not reproducible on a GPU. It was replaced by the stable
   `sort_by`. Old and new binaries gave identical output on 4 screens (~180 M decodes), because the cut never occurs
   on random keys: an instrumented kernel counted 0 cuts in 291 M steps (mean 3.85 states per step; per-decode peak
   median 7, 98.6% <= 16).

## kscreen port: how it got from 1.4x to 2-4x

| Version | Decodes/s on 16 random-key windows | Note |
|---|---|---|
| CPU, 16 threads | 1.4 M | reference |
| first port (states in local memory) | 1.9 M | exact from the start; 255 registers, 5.7 KB local per thread, 100 W of 250 W |
| + shared-memory letter counts, fallback inside the same thread | 2.2 M | exact; a warp waits whenever one of its 32 lanes needs the generic path (36% of warp-steps at a 1.4% fallback rate) |
| + fallback queued for a second kernel | 4.1 M (16 slots), 5.2 M (14 slots) | exact; fast kernel 53 registers |

Tried and not kept: capping registers (NVRTC ignored `--maxrregcount`), fewer or more beam slots (the beam width
itself changed nothing: it never fills), ablations of the count update, dedup and key loads (they change the
state counts, so they say nothing). Nsight Compute is installed but Windows denies GPU performance counters
(`ERR_NVGPUCTRPERM`) without a driver setting that was not changed.

Real runs (GPU lane, 2026-10-17): see `results/overnight/desktop/logs/` and `REPORT.md`.

## Seed-sweep port

First run: the PHP raw outputs were all correct except output 159 (my loop stopped one step early); fixed.
After that every generator matched on the first try: raw outputs, 153,088 scores each, and the 8 M-seed PHP sweep
(histogram identical over 1.02 G decodes). 1.6 M seeds/s against 0.23 M/s. Not optimised further: a full
all-section sweep is about 45 min per 2^32 seeds.

## Not done

- A canonical, order-independent tie-break for the beam (would let the kscreen kernel use one warp per decode);
  estimated gain ~2x on a screen that is now ~1 h of the queue.
- CuPy port of the numpy dictionary screens (`attack.fast_screen_batch`): left on the CPU.
