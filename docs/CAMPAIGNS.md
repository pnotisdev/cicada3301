# Overnight campaigns

`jobs/overnight.py` runs the long tests and brute-force searches unattended. Each campaign comes from a
specific finding (or gap) in `PLAN.md`. Each one carries positive controls (planted keys it must recover) and
null controls (random keys under identical settings), so a "nothing found" result means something.

## First time on a new Windows PC

1. Install Python 3.12 (python.org) and Rust (rustup.rs). Accept rustup's offer to install the Visual Studio
   C++ build tools (or have Visual Studio with the C++ workload). If the global Python cannot be written to, use a
   virtual environment in the repository: `python -m venv .venv`, then run everything with `.venv\Scripts\python.exe`.
2. Clone the repository with GitHub Desktop.
3. In PowerShell, from the repository folder, run `python -m pip install -r requirements.txt` (and, for an NVIDIA GPU,
   `python -m pip install -r requirements-gpu.txt`).
4. Run `python jobs/overnight.py run selftest`. It builds everything, exports the data, runs the 71 tests and
   the kscreen controls (about 10 minutes). Continue only if `results/overnight/<machine>/kscreen_selftest.txt` ends with
   `SELFTEST PASSED`.
5. Disable sleep while plugged in (Settings → System → Power).

If you started the all-sections PHP sweep by hand (`results/prng/php_all.tsv`, `php_all.log`), let it finish
before starting `prng-all`. The runner sees the finished file and skips that sweep. Running both at once only
halves the speed of each.

## Running it

From the repository root, on Windows (PowerShell) or Linux:

```
python jobs/overnight.py list            # campaigns, rough hours, what is already done (-v for steps)
python jobs/overnight.py run             # everything, in the order below
python jobs/overnight.py run --hours 9   # start no new step after 9 hours (a step is never cut off)
python jobs/overnight.py run kscreen-sections kscreen-restarts
python jobs/overnight.py report          # rewrite results/overnight/<machine>/REPORT.md
```

- **Setup.** `setup` runs first every time: three cargo builds and the data exports. It takes seconds when
  nothing has changed. The first time on a new machine it needs Python 3.11+ with `requirements.txt`, and Rust
  from rustup.rs.
- **Resume.** A step is finished when its output files exist. They are written only at the end, or renamed
  from `*.part` on success. Stop at any time (Ctrl+C, reboot) and run the same command again; only the
  interrupted step starts over. `--force` reruns finished steps.
- **Threads.** `--threads N` defaults to every logical CPU. Leave one or two free if you use the machine.
- **Output.**
  - Results go under `results/` (see `results/README.md`).
  - Each PC keeps its runner state, logs and report in `results/overnight/<machine>/` (its own folder,
    named by the PC's alias, so two PCs never edit the same file). These are committed: every PC sees every
    log after a pull. The alias is never the computer's real name: put one word, e.g. `desktop`, in the
    git-ignored file `.lp_machine` (or set `LP_MACHINE`). Without either, the runner picks a random
    `pc-xxxxxx` and saves it there. Paths and the computer's name are scrubbed from the logs.
  - The summary, with verdicts, is `results/overnight/<machine>/REPORT.md`.
- **Console.** The runner streams every step's output live, one line per event, as
  `[HH:MM:SS] [k/N step-id device] ...`: `k/N` counts the steps this run will execute, and `device` is `cpu`
  or `cuda`. Engine progress (`P% (n units) R units/s, eta S s`) and the Python screens' `k/N` lines are shown
  as `percent, count, speed, eta`, at most once per 15 s, and the final 100% line is always shown. A step that
  prints nothing for a minute gets a heartbeat line with its elapsed time. The run ends with a summary of
  every step's result and duration and each campaign's verdict lines.
- **Logs.** `results/overnight/<machine>/logs/<step>.log` keeps the same output, with at most one progress line
  per 30 s (plus the final one), so a multi-hour sweep leaves a readable log instead of thousands of updates.
  A step's result file (`stdout_to`) is written in full.
- **Machine.** Keep it plugged in with sleep disabled.

Hours below are rough figures for a 16-thread desktop CPU. The 15 W laptop these were developed on is about
2× slower.

## Campaigns, in run order

| Campaign | Hypothesis tested | Why now | Controls | ~Hours |
|---|---|---|---|---|
| `selftest` | (none) 71 unit tests, plus kscreen plant/recover | Every later null depends on it | 15 planted windows, 5 key families, both models, substituted alphabets; random-key null | 0.2 |
| `analysis` | Periodic key under the skip rule; plaintext word-length conventions | The old lag scan cannot see periods beyond ~60 when skips shift the key | Power curve with planted periodic keys; random-rune null | 0.4 |
| `kscreen-sections` | c = D(p) ± m·k + b for 1,447 library keystreams at every offset, any plaintext language, any alphabet D | Every earlier screen scored English words, which assumes English and an unscrambled alphabet | Matched null: 300 random keystreams | 0.8 |
| `kscreen-restarts` | The same, with the key restarting at the 10 headings or 46 page starts | Restart points are natural for a hand-run scheme | Null over the page windows | 3.6 |
| `kscreen-recurrences` | Every linear recurrence of order ≤ 3 mod 29 from every start state; all polynomial keys up to degree 3 | Fibonacci steps appear on page 30; recurrences are the natural "simple" keystreams | Selftest plants (lin2, poly2); matched null | 7.5 |
| `rescreen` | Dictionary screens 1, 2, reverse and heading restarts | They ran before the word-wrap fix, which split wrapped words (a handicap for a true key) | Built-in random-key controls | 5.7 |
| `dsearch` | Per-word additive key behind any secret outer alphabet, m = 1–8, gaps {1,2} and {1,2,3} | Only gap 1 had been run; more gaps give more pairs and more power | Synthetic F1(5) recovery; 4 surrogates per setting | 6.9 |
| `payload` | Hash identity and 832k passphrase AES/RC4/XOR decryptions | The earlier runs, and the community's, used the 5 wrong bytes | Built-in scoring of known formats | 0.6 |
| `kscreen-multipliers` | The library with all 28 key multipliers (e.g. 3301·k ≡ 24·k) | Multiplied keys are cheap to cover | Matched null | 5.0 |
| `prng-all` | PHP<7.1 `mt_rand`, glibc `random()`, .NET `Random`, a fresh seed per section | Only LP2 page 0 has been swept | Planted seeds (unit tests); `verify_top.py` z-scores | 20+ |
| `kscreen-chain` | Ciphertext feedback c_i = a c_{i-1} + p_i + k_j for a = 1..28: the library, every order-2 recurrence and cubic polynomial on the sections rewritten as c' = c_i - a c_{i-1} | The doublet fingerprint is what such a cipher gives if it avoids a zero shift, and no earlier screen could see it (`work/log/phase9_chain.md`) | Planted feedback keys (a = 1, 7, 28) and wrong-a / random-key nulls (`chain_selftest.py`); matched null per a | 3.0 (1.5 on GPU) |
| `prng-more` | py3 / mt32 / mt31 / java / msvc / drand48 / ruby: every 32-bit seed, two key maps each, 16 variants, window 0.7 (the all-sections pass is `prng-more-all`) | The three swept generators are a small part of what a 2012-14 program would use; the GPU makes the rest exhaustive (`work/log/phase9_gens.md`) | Planted seeds for each generator and map; validated generators (`test_gens.py`); `verify_top.py` z-scores | 7.5 (GPU) |
| `kscreen-reverse` | A key read BACKWARD through the text, ordinary (a = 0) and with ciphertext feedback (a = 1..28): reversed windows + the engines' `dir=back` mode, library / order-2 recurrences / cubic polynomials | Every IoC screen so far read the key forward; the skip rule must be mirrored for a backward key (`phase9_chain.md`) | Planted backward keys recovered at the exact key index, the same ciphertext read forward not found; matched null per a | 3.1 (1.5 on GPU) |
| `prng-more-all` | The `prng-more` generators with a fresh seed per section (all 8 windows at once) | The single-pad assumption (window 0.7) is only one of the ways a program could key the sections | As `prng-more` | 6.1 (GPU) |
| `kscreen-step28` | Relative-rank chain cipher: the plaintext enters the STEP c_i - c_{i-1} and is keyed mod 28 (variant A additive, variant B multiplicative via discrete logs; variant C the rank among the 28 runes other than the previous one; the rare zero step consumes a key value or not): the library x every unit multiplier of Z28 at every offset, plus a periodic-key scan to lag 3,000 | In the c domain the plaintext is a random walk, so every earlier screen was blind to this family (`work/log/research_2026-10-17.md`, C1) | Planted keys (variants A, B, C and both modes) recovered at the exact stream/offset, wrong variant blind, CPU = CUDA, matched nulls (4 replicates), planted periods found (`step28.py selftest`, `step_periodicity.py`) | 0.3 (CUDA only) |
| `prng-step` | The ten generators (php, glibc, .NET, py3, mt32, mt31, java, msvc, drand48, ruby) over all 2^32 seeds, scored in the step domain on the first 240 steps of section 0.7: 144 settings per seed (variants A and C keys mod 28 / B log2 of Z29, both key maps, zero steps spending a key value or not, 12 multipliers) | Research note C2: the ordinary seed sweeps cannot see a key that enters the STEP (`work/log/phase9_step28.md`) | Keys equal the Rust engine for 28 and 29 symbols, scores equal a numpy reference, a planted seed recovered per generator, random ciphertext gives no candidate (`work/tests/test_stepmt.py`) | 14 (about 1.2 h per generator on the GPU; CUDA only) |
| `prng-bg` | The ten generators over all 2^32 seeds (2^31 for .NET) scored WITHOUT word separators: log-likelihood of the decoded 120 runes under an English rune-bigram table, same 16 variants and skip/coin beam; window 0.7, then every section | If LP2's separators are not the plaintext's word boundaries the dictionary sweeps are blind (`work/log/phase9_boundaries.md`: planted seed 33 -> 0) | Generators identical to phpmt.cu, scores equal to a Python reference, planted seeds recovered for all ten generators, random ciphertext gives no candidate (`work/tests/test_bgmt.py`) | 0.3 per generator for 0.7, about 2 for all sections (CUDA only) |
| `kscreen-hashwords` | Hash-seed keystreams (sha256/sha512/md5 counter, sha256 chain, mod 29 and rejection) of every word and two-word phrase of the solved text, upper and lower case: 12,944 streams at every offset on the 8 sections | The library has hash streams for only ~65 Cicada strings | Matched null of 12,944 random streams; verification of the best hits like kscreen-sections | 0.6 on 14 CPU threads (3 h measured) |
| `prng-time` | Generators seeded with a millisecond timestamp of 2012-01 .. 2014-01: `new Random(System.currentTimeMillis())` (Java keeps 48 bits) and `random.seed(int(time.time()*1000))` (CPython: MT19937 with a two-word `init_by_array`; Ruby's `Random.new(ms)` by its documentation, unverified); one sweep per UTC month, newest first, section 0.7, boundary-free bigram score | The 32-bit sweeps cover every `time(NULL)` seed but none of these (`work/log/phase10_prng_time.md`) | Vectors from CPython and the Java specification (119/119), engine keys = independent keys, timestamp seeds planted with independent keys found at rank 1, random ciphertext without candidates (`run_gate.py work.tests.test_prngx_time`; on a GPU `test_bgmt64`, the desktop's 64-bit port); whole-section check against random timestamps of the same month | about 9 on the GPU (`work/phpmt/time_gpu.py`: java, py3, java-abs, ruby); about 210 on a CPU |
| `layer2` | Two layers built from the solved pages' methods (H-LAYER): a keyword Vigenere inside (with or without Welcome's literal-F rule, plain or Atbash alphabet, both signs), a number stream with the skip / coin anti-repeat rule outside. The 115 number streams of the library x the three solved keys (DIVINITY, FIRFUMFERENFE, CIRCUMFERENCE); 20 Cicada streams x 30 Cicada keywords; any keyword of period 2-14 (periodic mode) | The outer layer explains the doublet deficit and hides the inner literal F; kscreen decodes the outer stream but scores a Vigenere text (IoC ~1.1-1.2), so every earlier screen was blind (`work/log/hypotheses_2026-10-17.md`) | `work/layer2/selftest.py`: plants recovered at the exact offset with the right keyword (both alphabets, literal F on/off, skip and coin), a keyword outside the list found through periodic mode, kscreen blind to the plants, random streams below +2.0; matched null of 20 random streams | 13 (CPU only, 16 threads) |

## Decision rules

- **kscreen** (IoC of the decoded letters; English rune text ≈ 1.8, random 1.0):
  - **What counts as a hit.** A hit is any decode reaching IoC ≥ 1.40 on its first 300 runes. Random keys
    reach about 1.30 at most in 10⁷ decodes, and about 1.37 extrapolated to 10¹⁰. All 20,000 English 300-rune
    windows tested scored ≥ 1.45, and planted keys score 1.6–2.1.
  - **Verification.** `verify.py` re-decodes each of the top hits over its whole window. A true key keeps
    IoC ≥ 1.40 (about 1.8 for English); a lucky 300-rune stretch falls back towards 1.05.
  - **Matched control.** Verification also decodes the same keystream at 20 random offsets on the same window,
    and the hit must beat their maximum by 0.15. Structured keystreams (short periods) can let the beam overfit
    in ways random keys do not: plain English decoded with a period-3 recurrence key reached 2.29.
  - **Anything that survives verification is a candidate.** Read the decoded text in `*_verify.txt`. Its "by
    rank" line relabels letters by frequency, in case the plaintext alphabet was also substituted.
- **dsearch:** LP2's best G must beat every surrogate and sit at least 4 standard deviations above their mean.
  So far LP2 has always sat inside the surrogate range.
- **prng-all:** `verify_top.py` re-decodes the 20 best candidates over whole segments against random-seed
  controls. A true key scores about 0.8 against 0.08–0.11 (z ≈ +70); selection bias alone gives z ≈ +2…+5.
- **rescreen:** the best real keystream must beat the random-control maximum. The top hits must then decode to
  English under the exact skip-aware decoder (`attack.decode`).

- **kscreen-step28** (IoC of the decoded classes over 28 symbols; random 1.0, English about 1.8): the window is 300 steps, so the random maximum per window over 10⁹–10¹⁰ settings is about 1.25–1.32 (four null replicates; the exact tail gives a Gumbel-like maximum with location about 1.25 and scale about 0.012). A flagged window must beat every null replicate by 0.02 and reach 1.30, then `step28.py verify` continues the winning setting to the end of the section (a true key stays near 1.8).

- **prng-step** (IoC of 240 decoded classes; random 1.0): the null tail is the exact multinomial tail, heavier than chi-square (P(IoC >= 1.37) = 4e-11 and P(IoC >= 1.45) = 3e-13 per setting; work/tmp/ioc_tail.py), so a random maximum over 6 x 10^11 settings is about 1.42 and the sweep records every setting >= 1.45; a true seed scores about 1.8. `step_verify.py` regenerates the keys of the best candidates with the Rust engine and decodes the section beyond the window: a true seed keeps about 1.8, a chance maximum falls to 1.0.

- **prng-bg** (sum of 10 ln-odds of the bigram table over 120 decoded runes; a true key near +1200, a wrong one far below zero): candidates are the settings >= +300; `bg.py verify` decodes the whole section with Rust key streams and compares the per-rune score with 8 random seeds (a true key keeps about +10 per rune, a wrong one about -10.5).

- **prng-time** (the `bgsweep` score: 10 ln-odds summed over the first 120 decoded runes; a true key near +1000, random rows
  rarely reach 0, the best of 200,000 seeds on random ciphertext +59): rows >= +300 are candidates; `time_verify.py` checks the
  best 10 rows of every month over the whole section with keys rebuilt by independent code, against 8 random timestamps of
  the same month. A candidate needs +2.0 per rune and 5 above every control (a true key keeps about +10).

- **layer2** (mode=bigram: 10 ln-odds per rune of the decoded letters under the English rune-bigram table, first 300 runes of each section; a true key about +7, random decodes about -15, the best of ~10^8 random decodes about -5): `work/layer2/verify.py` re-decodes the best hits over the whole window with a beam of 64 and decodes the same setting at 20 random offsets of the same stream. A candidate must reach +2.0 per rune over the whole window and beat that matched null by 5. Periodic-mode hits (column z-score) are first turned into a keyword (best English shift per column, both alphabets) and then judged by the same rule.

**If something passes:**
1. Rerun its verification by hand.
2. Check that the same key works on a second section.
3. Write it up in `work/log/` before telling anyone.

Every candidate so far, from any method, has been selection noise.

## Findings that shaped this round (2026-10-16)

- **Periodic keys under the skip rule.** "Periodic keys up to lag 6000 are ruled out" assumed no skips. At
  LP2's skip rate (r ≈ 0.028 per rune) a key with period P is found at lags P − Δd, smeared over Δd ≈ r·P.
  `work/drift_period.py` uses a matched filter over those bands (and the bands under 2P, 3P, …). On planted
  periodic keys under the same rule it finds:

  | Period | Detected (Z above the random-text maximum, 8 trials) |
  |---|---|
  | ≤ 400 | 8/8 |
  | 800 | 7/8 |
  | 1600 | 6/8 |
  | 3200 | 0/8 |

  LP2 shows nothing (max Z 3.03 against a random-text maximum of 3.55). Periodic keys are therefore ruled out up to
  about 400 runes, not 6000. Longer periods remain open.
- **Word lengths** (`work/wordlen.py`). LP2's length histogram rejects English in Gematria Primus runes:
  G = 227, p ≈ 10⁻⁴² against Emerson; p ≈ 10⁻³⁵ against the solved LP sections. Two models come closer:

  | Model | p |
  |---|---|
  | English counted in letters (no digraph runes) | 7·10⁻⁸ |
  | English in runes with one extra rune in about 40% of multi-rune words | 0.025 |

  Interpretations to test: nulls or padding inside words, a different plaintext convention, or a language
  other than English. The IoC screens are insensitive to all three, which is why kscreen leads this round.
- **Language and alphabet.** Every earlier keystream screen needed English words spelt in the standard rune
  alphabet. The IoC statistic is unchanged by Atbash, by any fixed relabelling of the plaintext letters, by a
  constant shift and by the language. One kscreen pass covers all of those at once, under both anti-repeat
  models.

## Using a GPU, and lanes

`--device auto` (the default) uses the CUDA ports of the keystream screen and of the seed sweeps if, and only if, the
validation in `docs/GPU_PORT.md` passes on this PC (probe, decode-by-decode selfchecks, planted-key controls; the
record is `results/overnight/<machine>/gpu_validation.txt`). Otherwise the CPU engines run unchanged. `--device cpu`
forces the CPU; `--device cuda` stops if CUDA is unusable. The device of every step is on the console prefix and in
`state.json`. A CUDA step that fails is rerun on the CPU engine. The hour estimates in the table above are for the
CPU; with CUDA the runner divides the screens by 3 and the seed sweeps by 7 (measured, see `GPU_PORT.md`).

`--lane NAME` gives a run its own lock, so two runs can work at once. The GPU does the screens and sweeps with one
CPU thread each, which leaves the CPU free:

```
python jobs/overnight.py run kscreen-restarts kscreen-recurrences kscreen-multipliers prng-all --lane gpu --threads 2
python jobs/overnight.py run rescreen dsearch payload --device cpu --lane cpu --threads 14
```

Never give two lanes the same campaign. Per-step state is merged on write, so lanes can share `state.json`.
