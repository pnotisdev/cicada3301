# Phase 6 – Seeded-PRNG pads (2026-10-16)

Engine: `work/phpmt` (Rust). Each seed generates a keystream; 16 cipher variants are decoded with a skip-aware
Viterbi decoder:
- sign ± and Atbash on/off;
- map 0 = the language's own range call, map 1 = raw % 29;
- model 0 = on a collision the next key value is drawn, model 1 = on a collision one value is drawn as a
  coin, then keep or redraw.

A seed is dropped early once the first two words of 3+ runes have been decoded and neither is a dictionary
word. Surviving seeds are scored by the number of runes inside dictionary words (length ≥ 3) in the first
~60 runes.

**Validation before any sweep counted:**
- **Generators bit-exact:**
  - PHP legacy `mt_rand` (`MT_RAND_PHP`): 24 vectors from PHP 8.2.12;
  - glibc `random()`: the published `srand(1)` sequence;
  - .NET `System.Random`: 33 vectors from .NET Framework 4.x via PowerShell.
- **Planted seeds:** recovered at rank 1 for every generator, both models and both maps. They score 35–44,
  while noise reaches at most 14–16 per million seeds.
- **Full-segment check (`verify_top.py`):** a planted key decodes its whole text to 0.815, against 0.111 ±
  0.010 for random seeds (z = +70).

## PHP < 7.1 `mt_rand`, segment 0.7 (LP2 page 0, i.e. a single whole-book pad), all 2³² seeds
- 4,294,967,296 seeds × 16 variants in 5,229 s (about 0.82 M seeds/s on 16 threads, shared CPU).
- Best screening score 21; distribution of the top 4,000: 21 ×2, 19 ×6, 18 ×59, 17 ×160, 16 ×41, 15 ×1,097.
  That is an ordinary extreme for about 6.9·10¹⁰ decodes.
- **Full-segment check of the top 20:** 0.093–0.106 against 0.074–0.079 for random seeds (z +2…+5). The excess
  equals the screening window's own contribution (about 20 dictionary runes out of 729 ≈ 0.027): it is
  selection bias, and a true key would score about 0.8.
- **Result: negative.** No PHP < 7.1 `mt_rand` seed produces an LP2 pad starting at page 0, under any of the
  16 variants or either anti-repeat model.
- Files: `results/prng/php_07.tsv` (top 4,000), `php_07.log`, `php_07_verify.txt`.

## glibc `random()` (= PHP 5 `rand()` on Linux), segment 0.7, all 2³² seeds
- 4,294,967,296 seeds × 16 variants in 5,660 s (0.76–0.95 M seeds/s, shared CPU). Best screening score 21,
  the same noise ceiling as PHP.
- **Full-segment check of the top 20:** 0.088–0.112 against 0.076–0.079 for random seeds (z +1.5…+5.0). This is
  the same selection-bias pattern as PHP; a true key would score about 0.8.
- **Result: negative.** No glibc `random()` seed produces an LP2 pad starting at page 0, under any variant or
  either anti-repeat model.
- Files: `results/prng/glibc_07.tsv`, `glibc_07.log`, `glibc_07_verify.txt`.

## .NET `System.Random`, segment 0.7, all 2³¹ seeds (`Random(int)` uses |seed|)
- 2,147,483,648 seeds × 16 variants in 2,454 s. Best screening score 19.
- **Full-segment check of the top 20:** 0.086–0.110 against 0.076–0.079 for random seeds (z +1.4…+5.0). This is
  the same selection-bias pattern as PHP and glibc; a true key would score about 0.8.
- **Result: negative.** No .NET `System.Random` seed produces an LP2 pad starting at page 0, under any variant
  or either anti-repeat model.
- Files: `results/prng/net_07.tsv`, `net_07.log`, `net_07_verify.txt`.

**All three generators are done for segment 0.7 (one whole-book pad): negative.** A fresh seed per section
(all 8 windows) is the `prng-all` campaign in `jobs/overnight.py`.

## Not covered yet
- A fresh seed per section (`WINDOWS=all` in `jobs/prng_sweeps.sh`: 8 windows, about 8× the time).
- Key offsets ≠ 0 (pad not starting at the first rune of LP2), PHP's own auto-seeding, `mt_srand` with
  values outside 32 bits, and other generators (Java `Random`, ISAAC, LFSRs).
- Plaintexts that are not English: the dictionary score is English-only. Dukotah notes the same limitation.
