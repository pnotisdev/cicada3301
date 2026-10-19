# Step2 follow-up F1-F4: a repaired acceptance rule (diagnostics, not adopted)

**Nothing in LP2 is solved. No LP2 ciphertext was scored; no null, plant or campaign was run.**

GPT wrote F1-F3, their protocols and F4's protocol and code on 2026-10-19 (`PROTOCOL.md`,
`F3_PROTOCOL.md`, `F4_PROTOCOL.md`). Claude reviewed `f4.py` against its frozen protocol
and ran it once per part, unchanged, the same day. The E3' proof FAIL (`../REPORT.md`) stands.
Every file outside this folder is unchanged against `baseline.json` (`immutability.json`).

## Why a repair was needed

The v2 score is S = log Z_L - log Z_U(cell). Under each cell's own uniform-plaintext null
U_cell, P(S >= t) <= e^-t holds exactly for every channel. A campaign union bound needs one
common ciphertext law W for all cells, and U_cell differs from the anti-repeat law W near the
key end (hold) and with key content (skip5, coin). E3' found exact counterexamples, including a
toy normalized LM at Q29/n300 whose event mass is 2.07 times the per-cell bound at T300.

## Results

| Part | What | Result |
|---|---|---|
| F1 | Common-null score S_W = log Z_L - log W(c), checked on the full Q3 grid (keys 0..3, all offsets, both signs, q 0/.6/1, five channels, n 0..3, two LMs) | **PASS**: 340,800 cells, 48,696 exact rational tail bounds under W, 20,928 no-exhaustion hold/spend W equalities, Rust float vs exact <= 1.8e-15 nats. The Q29/n300 E3' witness has S = 32.65 > T300 but S_W = -1031.6. |
| F2 | Reuse of the 380 saved v1 held records (no new decoding) at T300 = 29.799 | **Descriptive**: 280/280 true cells at T for S and for S_W; nulls 0/100 for both; null maxima -132.15 (S) and -132.12 (S_W). |
| F3 | Exact finite-hold survival factor; conservative skip5/coin density bound | **PASS**: exact equalities for m 0..4 (397,122 hold, 397,122 spend); float log-CDF vs Rust U <= 2.2e-11 nats at n300/600. Worst-case skip5/coin penalty 8.53 nats (n300), 17.08 (n600). |
| F4 | Guard rule S_guard = min(S, S_W) = log Z_L - max(log Z_U, log W) | **PASS**: 340,800 cells, 48,708 exact tail bounds, each checked under BOTH U_cell and W; 46,488 uniform-LM controls all have ratio <= 1; float implementation vs the saved F1 exact arrays <= 1.8e-15 nats with identical rejected cells. Saved held records: 280/280 true cells still at T300 in every stratum, nulls 0/100, null max -132.15. |

## What F4 establishes

exp(S_guard) <= Z_L/Z_U on U-supported outputs and <= Z_L/W on W-supported outputs, so its
expectation is at most 1 under U_cell, under W and under any mixture of the two. With
T = ln(N_cells/alpha) the union bound P_W(any cell >= T) <= alpha is therefore **exact for all
four channels and every finite offset**; no skip5/coin gap is assumed away. The guard can only
remove candidates of the old rule. On the saved held data it removed none.

What it does NOT establish: that English-through-M04 wrong-key ciphertexts or LP2 follow W
(the E3 sanity nulls must measure that); power at library scale (1,439 streams); and the
true-detection rate in F2/F4 reuses one small 8-stream bank with source-specific q fits.

## The wrong-offset count check cannot be a hard stop as written

The requested check count(S >= t) <= (m-1) e^-t on the true stream fails on the saved
positives: at t = 10, 403 of 2,240 passes (275 of 280 records) for S_guard, 404 for S. The v1
records store only the 15 offsets within +-15 of the true offset, and every one of the 2,325
original-score exceedances at t = 10 lies at distance 1..15 from it (most at +-1..+-4, mostly
hold-channel passes over spend and M04 plants). These are alias cells of the true key, not
null trials, and the theorem bounds an expectation, not a realized count. A usable rule must
exclude a neighbourhood of the true offset or report the count as a diagnostic.

## Needs a decision before E3-E5

1. **Adopt S_guard >= T as the tier-1 acceptance rule** (recommended): it is the only option
   with an exact common-null bound for all channels and it keeps the v2 engine unchanged.
2. Keep S with the F3 density corrections (raises T by up to 8.53 / 17.08 nats for skip5/coin).
3. Keep S at T as a heuristic with no certified alpha.

And: count wrong-offset exceedances outside +-k of the true offset (k to be frozen before E4),
or keep the count as a diagnostic only.

## Files

`f1.py`..`f4.py`, `proposal.py` (S_W), `guard.py` (S_guard), per-part `*.started` / `*.json`
results, `checkpoints/`, raw arrays `f1_*.npz`, `f3_long.npz`, `f4_numeric_*.npz`,
`f2_scores.npz`, `f4_guard_scores.npz`, records `f2_records/`, `f2_pass_counts.json`,
`f4_guard_pass_counts.json`; `test_followup.py` / `tests.txt` (unit suite); `deliver.py`
(immutability, privacy, artifact hashes).
