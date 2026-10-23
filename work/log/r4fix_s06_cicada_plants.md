# R4 repair s06: R4 plants with Cicada's literal-F habit added (2026-10-23/24)

Nothing in LP2 is solved. Plants only; no LP2 ciphertext was scored.

## Question
Idea 9 of `work/laptop_review/11_next_100.md`. The R4 plants use Cicada solved-page text or English, enciphered with a plain advancing key. On the solved pages Cicada writes a plaintext F as F and does not advance
the key (sections 0.1, 0.5, An End). Would the unchanged mid arc still find R4 plants if Cicada had combined R4 with that rule, which the decoder does not model? And does LP2's own F count already rule that combination out?

## Method
- Code `work/r4fix/s06_cicada_plants.py` (new): `make_r4` copied from s01 (`work/r4fix/s01_edge_plants.py`, mode `any`: null slot 0..L, repair T(c-6) at q 0.81 from `frozen.json`, nulls 45% of multi-rune words), one switch added: `literal_f`. Everything else imported read-only (`plant_mid.search`, s01).
  Commands: `python -B work/r4fix/s06_cicada_plants.py one` (probe), `... plants --workers 3` (3 workers, below-normal priority), `... fshare`, `... summary`.
- **Literal-F rule, precisely.** At a plaintext rune with Gematria 0 (F): the cipher rune is F (0) and the key pointer does not advance (hold and spend alike). Interaction choices, all mine, none tested against alternatives:
  1. a literal F is clear text, so it is NOT subject to the anti-repeat check and is never repaired (it can equal the previous cipher rune: a doublet `FF`, or an enciphered 0 followed by a literal F);
  2. it is an ordinary cipher rune for everything after it: the next rune's collision check sees it as `prev`; the in-word lag-6 repair reads it (T(0) = 24); word-start / word-end flags are unchanged;
  3. nulls are unchanged (uniform, never equal to the left neighbour, so a null can be F by chance); an enciphered non-F rune that equals 0 is an ordinary cipher F, indistinguishable from a literal F;
  4. rng draws are not spent on a literal F, so the lf stream and its paired ctl stream share layout, plaintext, key stream and offset (all drawn before the cipher loop) but not the later repair / null values;
  5. the window start is moved past nulls AND literal F (the decoder's true offset is the key index at the first window rune, and a literal F has none).
  The null for the lf condition is the matched iid-key plant of the same kind (index + 1000, literal-F rule on, random key).
- **Plants.** Conditions `lf` and `ctl` (same function with `literal_f` False = s01 `any`) x channel hold (`m04`) / spend x plaintext Cicada / English x seeds 0-5 = 24 plants each. Seed strings are s01's `r4fix-s01|any|ch|src|i`
  (so seeds 0-2 of `ctl` ARE s01's `any` plants). n 150 and 300 (prefixes of one 300-rune window), library key at a random offset, sign +1 for even index and -1 for odd.
- **Decoder** unchanged mid arc (`X.search`), TRUE stream only, every offset, both signs, all four channels; detected = S_guard of the true band (plant's channel, sign, +-3 offsets) >= T300 = 29.80; "within 3" = true band >= global best - 3.
- The F share was also measured without any search on 150 fresh layouts per source and condition (indices 2000-2149, hold), 62,000 cipher runes per row (`fshare`).

## Controls
- **Positive (the same seeds without the literal-F rule): PASSED.** ctl detects 24/24 at n 150 and 24/24 at n 300; seeds 0-2 reproduce s01's stored `any` records exactly (12 plants, maximum absolute difference 0 in every band and matched-null score at n 150 and 300).
  The new seeds 3-5 behave alike (band median 59.3 / 120.9, range 42.1-86.3 / 90.6-162.8).
- **Null (matched iid-key plants, true stream searched at every offset, sign, channel): PASSED.** Winner maximum, lf: -20.8 (n 150) and -72.5 (n 300) (Cicada), -22.9 / -73.5 (English); ctl: -18.7 / -67.9. No null within 40 nats of T300 = 29.8 (48 plants x 2 n = 96 searches).
- **Signal check (F in clear): present and large.** See the result; this is also the answer to whether the question matters.

## Result

### Step 1 (no new CPU): s01's records split by plaintext source (6 plants per cell, `any` and `interior`)
| mode | src | n 150 detected / within 3 / band min-med-max | n 300 detected / within 3 / band min-med-max |
|---|---|---|---|
| interior | Cicada | 6/6, 6/6, 57.9 / 77.9 / 87.3 | 6/6, 6/6, 119.5 / 151.6 / 179.0 |
| interior | English | 6/6, 6/6, 62.1 / 71.5 / 84.8 | 6/6, 6/6, 131.9 / 152.7 / 166.3 |
| any | Cicada | 6/6, 6/6, 45.6 / 53.2 / 86.3 | 6/6, 6/6, 90.6 / 119.1 / 162.6 |
| any | English | 6/6, 5/6, 42.1 / 56.6 / 70.5 | 6/6, 5/6, 93.6 / 118.1 / 125.8 |
Detection does not differ by source (all 24/24); band medians differ by 1-5 nats at n 150 and 0-1 at n 300 between sources, not beyond what 6 plants show. The one "within 3" miss in `any` is an English plant, as in s01.

### Step 2: literal-F plants (T300 = 29.80; 24 plants per row)
| cond | n | src | detected | within 3 nats | band min / median / max | F in window (median; literal) |
|---|---|---|---|---|---|---|
| ctl | 150 | all | 24/24 | 22/24 | 42.1 / 59.3 / 86.3 | 4 (0) |
| **lf** | 150 | all | **22/24** | 19/24 | 21.3 / 50.9 / 73.3 | 8 (3) |
| lf | 150 | Cicada | 12/12 | 10/12 | 36.0 / 55.2 / 73.3 | 6 (2) |
| lf | 150 | English | 10/12 | 9/12 | 21.3 / 47.3 / 69.1 | 10 (4) |
| ctl | 300 | all | 24/24 | 20/24 | 90.6 / 120.9 / 162.8 | 9 (0) |
| **lf** | 300 | all | **23/24** | 16/24 | 24.2 / 102.0 / 150.0 | 16 (5) |
| lf | 300 | Cicada | 12/12 | 9/12 | 82.9 / 120.8 / 150.0 | 12 (4) |
| lf | 300 | English | 11/12 | 7/12 | 24.2 / 89.9 / 128.9 | 19 (7) |
(by channel: hold lf 11/12 and 12/12, spend lf 11/12 and 11/12; ctl 12/12 each.)
- **Cost of the unmodelled literal F:** paired by seed, band lf - ctl has median -9.6 (n 150, lower in 20/24) and -17.0 (n 300, lower in 21/24); about -3.3 nats (n 150) and -6.1 nats (n 300) per literal F in the window
  (correlation -0.39 / -0.55 over the 24 lf plants; a window holds 0-7 literal F at n 150, 3-12 at n 300). Roughly one decoder desynchronisation per F, as expected, but the decoder survives it: Cicada-plaintext plants (fewer F: 1.6% of plaintext runes) are 12/12 at both n, English (2.7%) 10/12 and 11/12.
- **Misses (3 of 48 plant-n cells):** lf hold English 0 at n 150: the true band is the global winner at 27.7, 2.1 nats under T300; lf spend English 3 at n 150 and n 300: the true band under the spend channel is 21.3 / 24.2, but the same stream, offset 1896 and sign at the HOLD channel scores
  46.0 / 90.4 (the winner of the whole search). So the key is still found in the planted stream (any-channel winner >= T300 in 23/24 at n 150 and 24/24 at n 300, against 24/24 and 24/24 for ctl); only the plant's own channel is wrong. A real campaign reports any cell >= T300, so the hit would be raised and then fail or pass whole-section verification.
  Within-3 falls from 22/24 and 20/24 (ctl) to 19/24 and 16/24: more wrong-cell winners above the true band (band-minus-best up to 66 nats in the miss above), so the offset / channel of a hit would be less reliable.
- The lf plants at n 150 are thin only for English with many F (min 21.3); the n 300 median band is 102 against T300 29.8.

### Step 3: F share, the signal check (`results/r4fix/s06_cicada_plants/fshare.txt`; LP2: 458 F in 12,956 runes = 3.535%, flat expectation 447)
| plants | plaintext F share | F share of the cipher stream (all runes incl. nulls) | expected F in 12,956 runes | LP2's 458 |
|---|---|---|---|---|
| lf Cicada | 1.62% | 5.19% +- 0.09% | 672 | z -8.5 |
| lf English | 2.71% | 6.24% +- 0.10% | 809 | z -12.7 |
| ctl Cicada | 1.62% | 3.70% +- 0.08% | 479 | z -1.0 |
| ctl English | 2.71% | 3.85% +- 0.08% | 499 | z -1.9 |
A literal-F cipher shows a clear F excess (a third to a half again as many F as the control, +1.5 to +2.4 points); LP2 does not (z -8.5 to -12.7 against the lf plants, -1 to -2 against the controls). The control's own F share is a little above the flat 3.45%
(nulls and repair runes are not all uniform), and LP2's 3.535% sits at or below it.
**Reading: LP2's F flatness (registry `obs-flat`) already excludes a literal-F rule layered on R4 with ordinary plaintext.** A literal-F cipher puts the plaintext F share on top of the roughly 3.5% a uniform stream gives;
for LP2's 3.54% to fit, the plaintext F share would have to be under about 0.4% (at the 95% level, taking the flat 3.45% baseline: 3.54% + 1.645 x 0.16% - 3.45%, divided by 0.97), against 1.6% for the Cicada text here and 2.7% for English. So the power result below is largely moot for LP2:
the decoder keeps most of its power on such plants, but LP2 does not look like one.

## Decision / reading
- If Cicada had used R4 with literal F on LP2, the unchanged mid arc would still have detected 22/24 (n 150) and 23/24 (n 300) such plants in the own-channel band (24/24 and 24/24 as a hit at any cell in the planted stream, with one channel mislabel), lower median power by about 10 nats (n 150) and 17 nats (n 300).
  It is not a blind spot of the size the edge slots might have been.
- That variant is anyway excluded by LP2's F count unless LP2's plaintext has almost no F. Neither the s01 nor this result changes any negative; no change to `r4lib` is indicated by this question.

## What this does NOT exclude
- Other literal-F interactions (a literal F that IS repaired when it equals the previous rune; the key advancing past an F; F kept literal only inside certain words; the repair counting only non-F runes, or T applied to the last non-F rune). I did not try them; the lf plants' doublet `FF` rate is not what LP2 shows.
- A plaintext with almost no F (a different language, a transliteration with F spelled as another rune), for which the F excess would vanish and the plants would reduce to the ctl condition (24/24).
- Weaker or different key families, nulls, or repair rates than R4 as specified; the true-stream-only search (decoder's best case, one stream, not the 1,439-stream library null at n 150, which is unmeasured); six plants per cell: 24/24 vs 22/24 is not a statistically resolved difference (Wilson 95% lower bound for 22/24 is 74%, for 24/24 86%).
- The F-excess check uses LP2's total only (458 / 12,956), not per section or per word position; it assumes the plant's plaintext F share. It is not a test of any other literal rune.
- The ctl F share above 3.45% (3.70 / 3.85%) was not explained (not isolated: nulls, repair runes, key-stream non-uniformity of the library are candidates).

## Files
- `work/r4fix/s06_cicada_plants.py`; stdout / stderr of the runs `work/r4fix/s06_{probe,run,fshare}_{out,err}.txt` (the err files are empty).
- `results/r4fix/s06_cicada_plants/{lf,ctl}_{m04,spend}_{cicada,english}_{00..05}.json` (48 per-plant records incl. matched-null searches), `probe.json`, `summary.txt`, `fshare.txt`.

## CPU used
Probe 6.6 s. Full run: 48 plants, 2,527 s summed per-plant time (wall time per plant under 3 contending workers; CPU is at most that, about 42 CPU-minutes), 3 workers at below-normal priority, about 15 min wall; `fshare` a few CPU-seconds-to-minutes (generation only, no decoder search). Peak memory not re-measured (s01: about 98 MB per process).
