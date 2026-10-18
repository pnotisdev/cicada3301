# M04 hold-key repair: a crossed baseline against the unchanged kscreen engine

**Nothing in LP2 is solved.** This is a synthetic gate, not a search of LP2. It asks one question: if the encryptor avoids a repeated
ciphertext rune by emitting a replacement and KEEPING the key position (M04), do the existing screens still see a planted key?
Specification sources: `work/independent/anti_repeat_matrix/CATALOGUE.md` (M04) and the outside council's experimental
specification. The engine (`work/kscreen`, default options: skip / coin, both signs, `n=300`, `beam=16`, `abort=150:1.2`) is
**not edited**. The plant generator (`m04.py`) is independent of the decoder.

## Channels (all plant a 300-rune window; output i carries plaintext i)

| Channel | On a would-be repeat of the previous OUTPUT | Key position |
|---|---|---|
| **M04 hold** | with probability q emit a uniform rune other than the previous output | kept |
| **spend** | same replacement | advanced (the colliding key value is spent) |
| **skip** (regression) | the repository's model 0 convention: take the next key value; a missed check keeps the doublet (keep 0.19) | advanced |
| **coin** (regression) | the repository's model 1 convention: one key value is spent as a coin, then keep (0.19) or redraw | advanced |

q is NOT assumed to be 0.8074 (that value assumes iid-uniform plaintext and key): it is fitted per (channel, plaintext source, key kind)
on TRAINING plants so that the doublet rate matches LP2's 86 / 12,947 per transition, then frozen.

## Frozen design (written before any calibration or held-out run)

* **Plaintext:** solved Cicada text (training pool: sections 4, 5, 0, 2, 6, 16, 17; held-out pool: sections 1, 3) and Emerson's essays
  (training: first 40% of its runes; held-out: last 40%). Window starts are random inside a pool, so windows overlap; the number of
  distinct starts is reported (passage reuse).
* **Keys:** `iid` uniform, or a random slice of a random stream of the flat-IoC library (`library_flat.ksb`, 581 streams).
  Streams of period <= 8 are flagged (a shift-invariant stream cannot lose alignment).
* **Search (identical for positives and nulls):** a bank of 8 streams (the planted one plus 7 distractors of the same kind), each a slice
  of length 398, so 16 offsets; both signs, both anti-repeat models: 8 x 16 x 2 x 2 = 512 cells. The planted offset is uniform in 0..15.
* **Matched nulls:** the same kind of ciphertext against a bank WITHOUT its key (7 + 1 distractors), through the same code.
* **Calibration:** 200 null searches (50 per plaintext x key stratum) from training plaintext; threshold T = the 10th largest best IoC
  (about 95%). Frozen in `results/analysis/m04_calibration.json` before the held-out run.
* **Held-out:** 100 M04 plants, 100 spend plants (25 per stratum each), 40 skip and 40 coin regression plants (10 per stratum),
  100 matched nulls (25 per stratum); held-out plaintext only.
* **Recorded per plant:** best IoC of the search and its cell; whether the true cell is listed (aborted decodes are not listed) and its
  IoC and rank; **detected** (best IoC >= T); **identified** (best cell is the planted stream within +-3 offsets); best IoC >= 1.40
  (the project's rule); and, by a full decode (beam 64) at the true cell with each model, the plaintext accuracy and key-pointer
  accuracy. These are reported separately (start identification, plaintext recovery, separation from wrong keys).
* **Engineering acceptance (not a result):** the regression controls (skip, coin) must be detected in >= 90% of plants, or the harness
  is invalid and nothing else is read. For a channel: >= 90 of 100 detected and >= 20 of 25 in every stratum counts as visible to the
  unchanged engine; the nulls may flag at most 5 of 100.

## Reading the outcome

* M04 visible (>= 90/100): the old negatives are not weakened by this mechanism at this scope.
* M04 not visible: the unchanged engines have a material blind spot for this channel at this scope. That would justify a bounded
  matching decoder (a fixed-prior summed-path likelihood with the zero-key / one-plaintext transition, checked against exhaustive
  enumeration); it is NOT built here and would be a separate decision. It would not exclude every hold-key construction, and
  nothing here says Cicada used M04.
* spend visible: a spend-key substitution leaves the old negatives intact (checks the claim of `anti_repeat_matrix/MATRIX.md`).

Commands (repository root; `.venv\Scripts\python.exe` on Windows):

```
python work/m04/run_baseline.py fit          # q per stratum (training)       -> results/analysis/m04_q_fit.json
python work/m04/run_baseline.py calibrate    # 200 nulls, threshold T         -> results/analysis/m04_calibration.json
python work/m04/run_baseline.py heldout      # refuses without the two files -> results/analysis/m04_baseline.json, .txt
python -m unittest work/m04/test_m04.py      # run from work/m04 (imports m04)
```

Scratch banks and windows go to `M04_SCRATCH` (default: the system temp folder), never into the repository.
