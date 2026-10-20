# step3: adopted contract, controls and the LP2 library campaign (2026-10-19)

**Nothing in LP2 is solved.** Written BEFORE any step3 run. Every file of v1, v2 and v2/step2 stays unchanged (read-only imports).

## Decision (made on the user's instruction)

The user said "try all those 4" after being told that the hold-key campaign and the clause-aligned scan need the chanscreen v2 contract adopted (`../step2/followup/REPORT.md`, "Needs a decision"). Claude reads this as adopting
option 1, the recommended one:

* **Tier-1 acceptance rule: S_guard >= T**, S_guard = min(log Z_L - log Z_U(cell), log Z_L - log W(c)), with W the common anti-repeat law (`../step2/followup/proposal.py`, `guard.py`). By F4 the union bound
  P_W(any cell >= T) <= alpha is exact for all four channels and every finite offset (T = ln(N_cells / alpha)).
* **T300 = 29.799206297530528** (82 windows of 300 runes, N = 8,742,403,760 cells, alpha = 1/1000), frozen in `../step2/thresholds.json`. The n600 inventory is not used.
* Wrong-offset exceedance counts are a **diagnostic**, never a stop. Cells within **k = 20 offsets of the true offset in the true sign, all four channels**, are aliases and are excluded from the count (every exceedance on the saved
  v1 records lay within distance 15 of the true offset); the other sign and all farther offsets are null cells. k is frozen here, before E4.

If the user objects to this reading, discard the campaign results; nothing else depends on them.

## Fixed inputs

* Language model: `../../model.npz` (v1, trained on Emerson 0-40% only). Decoder q = 0.81 for all channels (LP2's 86 doublets in 12,947 transitions give q = 1 - 29 * 0.00664 = 0.807).
* Channels hold, spend, skip5, coin; signs +1 and -1; every offset of every stream (including impossible cells, which score -inf and count in N).
* Library: `work/kscreen/data/library.ksb` as built by the runner: 1,439 streams, 13,326,835 key values (the v2 inventory).
* LP2 windows (campaign `n300`): the 82 windows of `../step2/thresholds.json` (stride 150 inside each section, plus a section-end anchor, 0.10 excluded). No previous ciphertext rune is supplied (the v1 assumption).
* Candidate ranks: **tier 1** = S_guard >= T (a candidate, not a lead); **tier 2** = the top 50 cells per (channel, window) by S_guard, UNVERIFIED ranks.
* A candidate needs, in this order: (1) the cell re-scored by the v1 dense reference (`../../reference.py`) to within 1e-9 nats; (2) the Viterbi plaintext read by eye and its clause sums checked with `work/prime_check.py`;
  (3) whole-section re-decode and a matched null as in `docs/CAMPAIGNS.md`. Only then is it a lead.

## E3 sanity nulls (before the campaign)

Five n300 wrong-key windows from the v1 calibration records, one per source stratum plus one extra (records 0, 50, 100, 150, 175: Cicada/iid, Cicada/library, English/iid, English/library, English/library), each searched against the
full 1,439-stream bank with the campaign code. Criterion: every maximum S_guard < T300. Five windows cannot certify a 0.001 tail rate; they test for gross failures and report the margin. The English-through-M04 ciphertexts are
not proven to follow W.

## E4 plants at library scale (before the campaign)

200 plants: for each channel (hold = M04, spend, skip, coin) 50 plants (25 held Cicada, 25 held Emerson), seed prefix `chanscreen-step3-plant`, signs alternating, a uniformly drawn library stream with enough key extent and a uniformly
drawn offset. The plaintext is encrypted with the v1 independent encryptors (`work/m04/m04.py`) over 300 + e runes, e uniform in 0..99, and the window is the 300 ciphertext runes after the first e (a mid-text window: the decoder gets no
previous rune). Only the planted stream is searched (all offsets, both signs, four channels): stream identity is given, not recovered among 1,439. Reported: detection (S_guard >= T300 at the true cell), the winner's channel, sign and
offset (+-3 aliases), wrong-offset exceedances at t = 0, 5, 10 outside the alias band against N_null e^-t, Viterbi accuracy of the winner. The plants are also scored on their first n runes for n = 60, 80, 100, 150, 200 (a prefix of
a plant is a plant) to give the power of the clause scan. Engineering target (not a result): >= 90% pooled detection and >= 80% per channel. A failure is reported, never tuned away.

## Clause-aligned scan (after the campaign)

Windows: the LP2 clauses (text between '.' marks and '&' breaks, page breaks do not end a clause) of at least 60 runes. T_clause = ln(N_clause / 0.001) with N_clause = windows x 13,326,835 x 8, written to `freeze.json` before the run.
Same engine, rule and candidate chain. Its power at each clause length comes from the prefix plants of E4.

## What is not claimed

No claim about LP2 follows from a negative beyond the stated power: a hold, spend, skip5 or coin key from the library at a 300-rune window with an English-like plaintext. Other streams, other plaintext languages, windows other than
these, restarts inside a window, unequal q are not excluded. The 8-stream-bank power of v1 and the single-stream power of E4 are not full-library identification power.

## Amendment 1: E3 outcome and E3b (written after E3, before E3b runs)

**E3 as frozen did not meet its criterion, for a reason that is my error in choosing the records.** Records 0 and 100 (iid keys) are real nulls: maxima S_guard -102.37 and -100.55. Records 50, 150 and 175 are library-key records:
the v1 harness encrypted them with slices of library streams, which the full 1,439-stream bank contains. The campaign found, for each, exactly the stream that encrypted it, with the hold channel and sign +1: record 50 `sha512-ctr mod :1311`
(S_guard 181.80), 150 `sha512-ctr reject :<256 bytes 50bd24b4>` (218.06), 175 `md5-ctr reject :parable` (227.60). They are library-scale positive controls (3 of 3 identified among 1,439 streams), not nulls. The results are kept
(`results/chanscreen/null/`, `summary_null.txt`); the literal criterion (every maximum below T) fails and is reported as failed.

**E3b** replaces the null evidence: five more iid-key records, one pair per source and one extra: calibration records **10, 30, 110, 130, 145** (iid keys only), full bank, same code. Criterion unchanged: every maximum S_guard < T300.
Together with records 0 and 100 that makes seven iid-key nulls.

## Amendment 2: E4 outcome and the alias-band diagnostic (written after E4, before `e4_bands.py` runs)

E4 as frozen: detection (S_guard >= T300 within +-3 offsets of the true offset, true sign and channel) 200 of 200 (50 of 50 per channel, both plaintext sources); prefixes of the same plants: 194 of 200 at 60 runes, 200 of 200 at 80, 100, 150 and 200 runes;
Viterbi accuracy of the winner mean 0.9906 (198 of 200 at least 0.95); the winner is the true cell (+-3 offsets, same channel) in only 8-21 of 25 per group, the sign is right in 99% (aliases in other channels and at other offsets win).
Engineering target met (>= 90% pooled, >= 80% per channel); not a result about identification among 1,439 streams.

The wrong-offset diagnostic with the frozen band k = 20 shows far more exceedances than N e^-t (269,508 at t = 10 against a bound of 837). It is a diagnostic, not a stop, and its cause is visible: the 94 plants in short streams
(keyword and periodic streams of about 2,000 values) are equivalent at every period, and for hold plants cells up to about +50 offsets from the truth stay above 10 nats (the hold likelihood may re-synchronise by holding the pointer, about -6 nats per hold).
`e4_bands.py` rebuilds the same plants from their seeds and counts cells >= 10 outside wider bands and on the other sign (a genuine null). It changes no threshold, no rule and no plant.

## Amendment 3: faults in the n300 run, and the recomputation check (2026-10-19, written while the campaign runs; changes no threshold, rule or plant)

**What happened.** (1) Step `n300-a` (windows 0-20) was recorded as failed at 15:07: two of its 294 tasks, (window 1, chunk 11) and (window 17, chunk 4), had raised `ValueError('invalid log likelihood')` (the first at about 13:29; the step ran on because the executor finishes the
other tasks before the exception leaves it). Both tasks, re-run in a fresh process over every stream, sign and channel, gave only valid values, and re-run with the campaign code at 16:13 they finished with 0 tier-1 cells. (2) The partial summary of 427 tasks showed **98 tier-1 cells, all in one
task**: window 13 (`0.9@300`), chunk 4, stream 250 `sha256-chain reject :circumference`, hold, sign +1, offsets 5894-5992, best 132.60 at 5944 (task finished 14:29:07). **They do not reproduce**: the campaign engine and the v1 dense reference both give S = -177.19 at offset 5944
(difference 2.2e-12), the Viterbi text is letter soup, the recomputed best over all offsets is -130.15 and no offset reaches T. No window explains the stored value (stream 250 against all 82 windows: best S -44.3). The stored minus the recomputed S is +309.79 at the centre of the band and
smaller at its fringe, which is what one corrupted intermediate value in the backward recursion looks like (its effect spreads over the roughly 100 offsets whose paths pass through that state). Re-running the task with the same code (245 s) gives 0 tier-1 cells and differs from the stored file in
**exactly one of its 400 (stream, sign, channel) rows** (stream 250, hold, +1); the other 399 are identical bit for bit.

**What it means.** A transient fault in single engine calls, not a property of the code or the inputs: 3 faulty tasks (two loud, one silent) in about 430 finished tasks, about 172,000 engine calls, so about 1.7e-5 per call. Four other finished tasks (window, chunk) = (11,12), (4,6), (7,11), (17,3) re-run bit for bit identical.
The cause is not established. Windows logged a display-driver engine timeout at 14:48 and a desktop-compositor heap-corruption crash at 13:56 under the same load, so the machine may be marginal at full load (memory or clocks); nothing here proves it.

**Treatment.** The corrupt file was moved to `results/chanscreen/quarantine/n300_w013_c04_corrupt.npz` and the task recomputed in its place (`work/tmp/refill_w013_c04.py`, log `work/tmp/refill_w013_c04.log`); the two failed tasks were filled the same way
(`work/tmp/rerun_check_n300.py`, log `work/tmp/rerun_check_n300.log`). A failed or non-reproducing task is re-run, never skipped. `summary.py` now recomputes every (window, stream, sign, channel) that has tier-1 cells in a fresh call and prints
`TIER 1 (S_guard >= T): N cells, M of them reproduced by an independent recomputation`, plus a `NOT REPRODUCED` line per group that does not come back; only reproduced cells are candidates.
Controls of the check: the null set (137 real, library-keyed cells) 137 of 137 reproduced; the corrupt task 0 of 98.

**Not covered.** A fault that hides a real hit is not detected: a true cell would be lost only if a fault hit its exact call (about 1e-5), and tasks without tier-1 cells are not audited. A sampled audit of finished tasks (re-run N at random, compare bit for bit) is the way to measure the fault rate; 4 of 4 identical is
all that exists now.

**Outcome of the campaign (2026-10-20).** n300: 1,148 of 1,148 tasks, 0 tier-1 cells. Clause scan: the step exited with an error at 02:15 (five tasks had raised `invalid log likelihood`: windows/chunks (0,10), (3,3), (7,0), (20,9), (27,1)) and its summary, built with the new check, listed one tier-1 cell, window `0.8c@122+174`, stream
`sha512-ctr reject :welcome`, spend, offset 10589, stored 335.11, recomputed best -98.12: not reproduced. The file was moved to `results/chanscreen/quarantine/clause_w005_c04_corrupt.npz`; the six tasks were re-run with `campaign.py run clause --workers 6` in 2.2 minutes without an error, all with 0 candidates, and the summary regenerated:
1,148 of 1,148 tasks, 0 tier-1 cells. Faults in total: 9 of 2,296 tasks (7 errors, 2 silent). The rule is unchanged; a failed or non-reproducing task is re-run, never skipped.
