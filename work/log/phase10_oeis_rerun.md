# OEIS lane rerun with windows long enough to detect a true key (2026-10-17, 23:50)

Scope: LP2 sections 0.7-0.15 (8 section windows). **Nothing in LP2 is solved.** After the audit in `phase10_deepseek_round3.md` (a correct key scores +7.3 per rune on Cicada's text, so the original 36-rune windows passed the +300 gate in only 29% of cases), the lane was rerun with longer windows.
**120 runes was impossible:** the OEIS file holds only the first terms of each sequence (min 40, median 63; only 0.5% have 124 or more). Each sequence is read with the longest window it can cover (`work/prngx/oeis_rerun.py`):

| set | sequences | window | true key passes +300 (solved Cicada text) | seeds (sequence x 128 offsets) | real sweep | matched null (random sequences of the same lengths) |
|---|---|---|---|---|---|---|
| A: 64 or more terms | 98,667 | 60 runes | 96.9% | 12,629,376 | best 75 (1,104 s) | best 129 (1,218 s) |
| B: 52-63 terms | 46,891 | 48 runes | 81.3% | 6,002,048 | best 128 (323 s) | best 124 (314 s) |
| C: 40-51 terms | 53,530 | 36 runes (the original lane, not rerun) | 28.7% | | best 181-246 | |

28 multipliers, both signs, skip and coin models, section windows at all 128 start offsets; `prngx bgsweep seq` on 12 CPU threads (no GPU port exists for the sequence lane).
**Control** (`oeis_rerun.py control`): primes planted at offset 5 among 400 random sequences come back at rank 1 for both lengths (score 515 at 60 runes, 406 at 48 runes; best other 57).
**Verification** (`oeis_bg_verify.py`, `results/prngx/bg_oeis_A60_verify.txt`, `bg_oeis_B48_verify.txt`): the Python reference reproduces the sweep's best scores (75 / 75 / 61 and 126 / 122 / 122) and the decodes are not English (+1.0 to +2.6 per rune; the same settings on random sequences give about -570 to -750 per rune). A few
sub-threshold rows (score 59) do not reproduce: the engine keeps a partial decode when a sequence runs out of terms, the reference demands a full one; irrelevant at the +300 gate.

**Result: negative, and now a real negative for 146k of the 199k sequences.** Best scores 75 and 128 against the +300 gate (a true key would be near +440 and +350), no better than the nulls. Weighted by sequences the per-window power of the lane is about 75% (98,667 x 0.97 + 46,891 x 0.81 + 53,530 x 0.29, over 199,088), up from 29%. A sequence of n terms
can only show a true key at start offsets up to n minus the window length, so a key that begins late in a short sequence is not covered. Pages and headings (55 windows, offsets 0-15) were not rerun; neither were the 53,530 sequences with 40-51 terms (their weak spot stays 29%).
