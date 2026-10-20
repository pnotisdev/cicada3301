# laptop E4 smoke scratch (2026-10-20) - superseded, kept for the record

**Not a result. Nothing in LP2 is solved and no LP2 ciphertext was read.** The desktop ran the real E4 (200 library-scale plants),
the 82-window n300 campaign and the clause scan under `work/chanscreen/v2/step3/PROTOCOL.md` (origin/main 134fdd5, results in
`results/chanscreen/`). This folder is the laptop's own, smaller pipeline check, written before that push was seen.

- `e4_smoke.py`: plant, search the planted stream only (4 channels x 2 signs, all offsets, S_guard = min(S, S_W)), banded exact
  Viterbi. Same rule and T300 = 29.799206297530528 as the desktop's step3. Only the paths, the records folder name and the header differ from the file I ran.
- `alias_tail.py`: regenerates four smoke plants and measures the alias tail (below).
- `records/`: 16 plants on non-protocol seeds (`e4-smoke`: indices 0, 1, 12, 13 for each channel, so both signs and both
  plaintext sources). All 16 detected at the true cell, S_guard 140.9 to 246.8 against T300 = 29.80; winner accuracy .96 to 1.0.
- `E4_PROTOCOL_draft.md`: the protocol I had drafted for a laptop run (n300 only, k = 15, gate rules, Amendment 1). Never frozen
  for a protocol run; the desktop's `PROTOCOL.md` replaces it.

## What the smoke run found (the same structure the desktop reports in its amendment 2)

1. 854 of the 1,439 library streams (59%) are exactly periodic with period <= 64 (542 with period <= 8), so cells at offset + j * period
   read the same key values as the true cell. 8 of the 16 plants had a winner at a different offset: 7 tie the true cell exactly
   (difference <= 2.3e-13) and one (coin) is 1.28 nats higher at another copy. The short-stream plants have 132 to 423 offsets with an
   identical key slice over the span the true path used (`alias_tail.py` lists them).
2. Around the true offset of a hold read on a 20,000-value stream (three hold plants, and a spend plant read by the hold decoder), 31 to
   51 cells stay above 10 nats, spanning d = -3 .. +49 offsets from the truth, and the tail is one-sided: 30 to 48 cells ahead of the
   truth, 0 to 3 behind. S_guard falls by 4.1 to 4.4 nats per offset ahead (fit over d = 1..40), so the tail length is about
   (S_true - 10) / 4.2: predicted 50.6, 31, 49.8, 37.9 against observed 49, 30, 47, 36. So an alias radius of 15 (mine) or 20 (the
   desktop's) is too small for hold, and a wrong-offset count must exclude exact copies and a band of about 60 ahead of the truth.
   The desktop's amendment 2 puts the cost at "about -6 nats per hold"; I measure 4.1 to 4.4 per offset on these four plants and have
   not reconciled the two.
3. No other surprises: both signs and all four channels recovered the plant, including the negative sign (`c = p + sign * k`).

Reproduce (cheap, write-once so existing records are only printed): `python -B work/tmp/laptop_e4_smoke/e4_smoke.py smoke`.
