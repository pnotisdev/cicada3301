# Overnight campaigns

`jobs/overnight.py` runs the long tests and brute-force searches unattended. Each campaign comes from a
specific finding (or gap) in `PLAN.md`. Each one carries positive controls (planted keys it must recover) and
null controls (random keys under identical settings), so a "nothing found" result means something.

## First time on a new Windows PC

1. Install Python 3.12 (python.org) and Rust (rustup.rs). Accept rustup's offer to install the Visual Studio
   C++ build tools.
2. Clone the repository with GitHub Desktop.
3. In PowerShell, from the repository folder, run `python -m pip install -r requirements.txt`.
4. Run `python jobs/overnight.py run selftest`. It builds everything, exports the data, runs the 44 tests and
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
- **Machine.** Keep it plugged in with sleep disabled.

Hours below are rough figures for a 16-thread desktop CPU. The 15 W laptop these were developed on is about
2× slower.

## Campaigns, in run order

| Campaign | Hypothesis tested | Why now | Controls | ~Hours |
|---|---|---|---|---|
| `selftest` | (none) 44 unit tests, plus kscreen plant/recover | Every later null depends on it | 15 planted windows, 5 key families, both models, substituted alphabets; random-key null | 0.2 |
| `analysis` | Periodic key under the skip rule; plaintext word-length conventions | The old lag scan cannot see periods beyond ~60 when skips shift the key | Power curve with planted periodic keys; random-rune null | 0.4 |
| `kscreen-sections` | c = D(p) ± m·k + b for 1,447 library keystreams at every offset, any plaintext language, any alphabet D | Every earlier screen scored English words, which assumes English and an unscrambled alphabet | Matched null: 300 random keystreams | 0.8 |
| `kscreen-restarts` | The same, with the key restarting at the 10 headings or 46 page starts | Restart points are natural for a hand-run scheme | Null over the page windows | 3.6 |
| `kscreen-recurrences` | Every linear recurrence of order ≤ 3 mod 29 from every start state; all polynomial keys up to degree 3 | Fibonacci steps appear on page 30; recurrences are the natural "simple" keystreams | Selftest plants (lin2, poly2); matched null | 7.5 |
| `rescreen` | Dictionary screens 1, 2, reverse and heading restarts | They ran before the word-wrap fix, which split wrapped words (a handicap for a true key) | Built-in random-key controls | 5.7 |
| `dsearch` | Per-word additive key behind any secret outer alphabet, m = 1–8, gaps {1,2} and {1,2,3} | Only gap 1 had been run; more gaps give more pairs and more power | Synthetic F1(5) recovery; 4 surrogates per setting | 6.9 |
| `payload` | Hash identity and 832k passphrase AES/RC4/XOR decryptions | The earlier runs, and the community's, used the 5 wrong bytes | Built-in scoring of known formats | 0.6 |
| `kscreen-multipliers` | The library with all 28 key multipliers (e.g. 3301·k ≡ 24·k) | Multiplied keys are cheap to cover | Matched null | 5.0 |
| `prng-all` | PHP<7.1 `mt_rand`, glibc `random()`, .NET `Random`, a fresh seed per section | Only LP2 page 0 has been swept | Planted seeds (unit tests); `verify_top.py` z-scores | 20+ |

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

## Using a GPU

None of the engines use the GPU. The 2080 Ti would only pay off for `prng-all`, the one multi-night job.
Porting it is planned in `docs/GPU_PORT.md`, with the validation gates any GPU result must pass first.
