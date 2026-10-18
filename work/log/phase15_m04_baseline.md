# Phase 15: the M04 hold-key repair, crossed against the unchanged kscreen engine (2026-10-18)

Scope: a synthetic gate; LP2 is not searched. **Nothing in LP2 is solved.** Question (from `work/independent/anti_repeat_matrix/CATALOGUE.md`, M04, and an outside council's
specification): if the encryptor avoids a repeated ciphertext rune by emitting a replacement and KEEPING the key position, do the existing screens still see a planted key?
Design frozen before any calibration or held-out run: `work/m04/README.md`. Code: `work/m04/m04.py` (independent plant generator and harness), `run_baseline.py`,
`test_m04.py` (10 tests, run from `work/m04`). The engine was not edited (default options: skip / coin, both signs, `n=300`, `beam=16`, `abort=150:1.2`).

## Channels and fitted q

| Channel | On a would-be repeat of the previous output | Key |
|---|---|---|
| M04 hold | with probability q a uniform other rune | kept |
| spend | same | advanced |
| skip / coin (regression) | the repository's model 0 / model 1 conventions, keep 0.19 | advanced |

q was fitted on TRAINING plants (separate plaintext pools) so that the doublet rate equals LP2's 86 / 12,947 per transition: 0.803-0.8125 in all eight (channel, plaintext, key)
strata (`results/analysis/m04_q_fit.json`; the iid-uniform value 0.8074 holds, because a uniform key makes collisions 1/29; the spread is sampling noise, about 4,000 doublets per fit).

## Search (identical for positives and nulls)

A bank of 8 streams of 398 values (planted stream + 7 distractors, iid or random slices of the 581 flat-IoC library streams), 16 offsets, both signs, both models: 512 cells per search
(checked against the engine header). Plaintext: solved Cicada text (training sections 4, 5, 0, 2, 6, 16, 17; held-out 1, 3) and Emerson (training first 40%, held-out last 40%).
Matched nulls: the same ciphertext against a bank without its key. Threshold T = 1.1969, the 10th largest of 200 matched-null maxima (null max 1.2505, median 1.1513), frozen
(`m04_calibration.json`). Held-out: 100 M04, 100 spend, 40 skip, 40 coin plants, 100 matched nulls; 171 distinct Cicada and 190 distinct English window starts (windows overlap).

## Result (`results/analysis/m04_baseline.txt`, per-plant records `m04_records.jsonl`)

| Channel | detected (best IoC >= T) | identified (+-3 offsets) | best >= 1.40 | plaintext accuracy at the true cell | key-pointer accuracy |
|---|---|---|---|---|---|
| **M04 hold** | **14 / 100** | 18 | **0** | mean 0.154, **0 of 100 >= 0.95** | 0.127 |
| spend | 100 / 100 | 100 | 100 | mean 0.969 (95 >= 0.95) | 0.998 |
| skip (regression) | 40 / 40 | 40 | 40 | 0.986 | 0.986 |
| coin (regression) | 40 / 40 | 39 | 40 | 0.987 | 0.979 |
| matched nulls | 2 / 100 | 0 | 0 | - | - |

* The harness works: both regression channels are recovered in every stratum, the nulls flag 2 of 100 (limit 5).
* **The unchanged engines are blind to M04 at this scope.** The 14 detections are about what a few lucky plants give (null rate 2 of 100); the 14 have a mean plaintext accuracy of
  0.265 (max 0.70), i.e. their first repair came late. Overall plaintext accuracy 0.154 equals the theory for a decoder that is right only up to the first held repair
  (first repair after about 39 runes: prefix share 0.130 + chance 0.030 = 0.160, my arithmetic from the plants' mean of 7.7 repairs per window), so the loss of alignment is the
  mechanism, not noise. None of the 380 held-out plants drew a stream of period <= 8, so a shift-invariant stream (which cannot lose alignment) was not tested.
* **A spend-key substitution is NOT a blind spot:** the key advances normally, only about 3% of letters are garbage, and the old screens recover it (100 / 100, plaintext 0.969, pointer 0.998).
  This confirms, by plants, the claim of `anti_repeat_matrix/MATRIX.md` that spend substitution need not lose alignment.

## What it means, and what it does not

* If LP2's repair keeps the key position, then for the key families the old screens covered (kscreen library, recurrences, sacred streams, signs; the seed sweeps and OEIS / hash / KDF
  lanes, which use skip / coin beams) their negatives are not evidence against that family. If it spends the key (the T_6 collision-substitution reading of the echo, spend variant),
  they stand. Spend versus hold cannot be told apart keylessly with any power (reference power 0.26, `work/log/collision_followup_2026-10-18.md`).
* **Nothing here says Cicada used M04.** It is a measured property of our decoders at one scope: 300-rune windows, 8 x 16 bank, default engine options, uniform replacement runes,
  plaintext from solved Cicada text and Emerson. A different replacement rule or window length changes the numbers.
* Next, only as a separate decision: a bounded matching decoder (fixed-prior summed-path likelihood with the zero-key / one-plaintext transition, checked against exhaustive
  enumeration, planted recovery and same-freedom nulls). Caution from earlier work: free pointer-hold freedom inflated the null of `nulledge` to the true-key score (1.75), and the
  gated-null decoder failed on offset resolution for structured keys; a hold transition has the same risk, so the null and the offset resolution must be measured first.
