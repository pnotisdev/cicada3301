# E4 protocol (n300): conditional-stream power at library scale — frozen before the run

Source: `../step2/README.md` section "E4' conditional-stream power", with the departures listed under "Scope". Nothing in LP2
is solved and no LP2 ciphertext is read here. Code: `e4.py`. Records: `e4_records/` (git-ignored, hashes in `e4_sha256.json`).

## Plants

- 100 plants = 25 per channel (hold, spend, skip5, coin) at n = 300. Within a channel, index 0..11 use the held Cicada
  pool and 12..24 the held Emerson pool (`run_baseline.pool('held', src)`); the encryption sign is +1 for even and -1 for
  odd index (`c = p + sign * k`, the engine's convention in `reference.py`; passed to the encryptors as `mult`).
- Seed: `run_baseline.seed_of('chanscreen-step2-plant', channel, 300, index)`. One `random.Random(seed)` draws, in this
  order: the plaintext window, the library stream (uniform over the streams with m >= need), the offset (uniform over
  0..m-need), then the encryptor's own draws. need = n (hold, spend), 6n (skip5), 3n (coin); all 1,439 streams qualify.
- Encryptors are the unchanged v1 ones (`m04.enc_m04`, `enc_spend`, `enc_skip` = skip5, `enc_coin`). Generator q for hold
  and spend is the original v1 fit for the stratum `channel|source|lib` (`../frozen.json`), not a refit; skip5 and coin have
  none. The decoder uses q = .81 for every channel.

## Search and score

- For each plant, the planted stream only: 4 channels x 2 signs, one all-offsets backward pass each (8 passes), the v2
  engine and the v1 model (`../model.npz`, trained on training Emerson only).
- Detection statistic: S_guard = min(S, S_W) (`../v2/step2/followup/guard.py`), threshold T300 = 29.799206297530528
  (`T_nats` in `../v2/step2/thresholds.json`). True cell = (the plant's channel, the plant's sign, the plant's offset).
- Winner = the cell with the largest S_guard over the 8 passes. Accuracy = plaintext agreement of an exact banded Viterbi
  on the key slice the cell can reach (n+2 values for hold/spend, 6n+6 skip5, 3n+3 coin; identical to the full-key
  Viterbi because the pointer cannot leave that slice), for the winner and for the true cell.

## Gate (all must hold; any failure stops the chain and is reported, not tuned)

1. Pooled detection (true cell S_guard >= T300): at least 90 of 100.
2. At least 20 of 25 in every channel.
3. Among detected plants, more than half have winner accuracy >= .95.
4. Wrong-offset count, alias radius k = 15 (frozen before E4): over all 800 passes, the number of cells with
   |offset - true offset| > 15 that are not exact copies of the true cell (Amendment 1) and have S_guard >= t is at most the
   sum over passes of N_out * exp(-t), for t = 0, 5, 10 (N_out = number of such cells in the pass). Counts are a bound on
   an expectation, not per pass; they are summed.

## Reported, not gated

Exact (channel, sign, offset) of the winner, +-3 and +-15 offset classes, rank of the true cell in its pass, the distance
histogram of every cell at S_guard >= 10 and >= T300 (the real alias profile over the whole stream), plain S next to
S_guard, per-source and per-sign strata, accuracies.

## Amendment 1 (2026-10-20, after the smoke run, before any protocol seed was run)

The smoke run (16 plants, seed prefix `e4-smoke`, all detected, true-cell S_guard 140.9 to 246.8) showed that in 8 of 16
plants the winner sits at a different offset with an identical score. Cause, measured: 854 of the 1,439 library streams
(59%; 542 with period <= 8) are exactly periodic with period <= 64, so the cells at offset + j*period read the same key values
and are exact copies of the true cell, not null trials; a hard G4 count would fail by construction. Changes, all made before
the protocol run and none touching seeds, T300, k or gates 1-3:
- A cell is an exact copy of the true cell when its key slice equals the true slice over the span of key values the true path
  consumed (`key_used`, from the encryptor). Copies are excluded from the G4 count (and from the alias histogram) and are
  reported separately (`copies`, `n_copies_beyond_15`, `winner.copy_of_truth`).
- The true cell's rank is counted with a 1e-6 tolerance because exact copies tie up to float noise (2e-13 seen).
- No claim is made about identifying the offset among exact copies: they are the same hypothesis.

## Scope and what this does NOT establish

- n300 only: the campaign is n300 only, and the three n600 sanity windows of step2 were not run, so n600 plants would
  have no null check. The 200-plant (n300 + n600) design of step2 is therefore halved.
- Conditional power: the stream is known. It does not measure identification among 1,439 streams (that is the separate
  end-to-end control). Plants are single-source, uniform-stream, 300 rune windows of a 1,293-rune Cicada pool (windows
  overlap) and 122,777 Emerson runes; q is the v1 fit. The step2 "first repair" initialization test is NOT run here; it
  matters for mid-section windows, not for section starts.
- Any code change after the first protocol run is declared in `REPORT.md` with its reason, and all 100 plants are rerun
  on the same seeds. A smoke test on non-protocol seeds (`e4-smoke`) is allowed before the run and is not a result.
