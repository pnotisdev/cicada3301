# Phase 55: dissecting the lag-5 S echo (side session, 2026-10-22)

Nothing in LP2 is solved. Script `work/phase55_s_echo_dissect.py` (seed 55, 10,000 draws per null), output `results/analysis/phase55_s_echo_dissect.txt`.

## Plan (written before the run)
Reproduce the 11 in-word S,S pairs at lag 5, then test against two nulls: W (runes shuffled inside each word) and X (runes shuffled across a section, word lengths kept).
Tests: (1) lag-5 coincidence count per rune, with the cut count 7 lags x 29 runes = 203 as a min-p correction; (2) rune frequency per word-position class
(first, second, middle, second-to-last, last; words of 5+ runes; chi2 against W) and per word length (2..7, 8+; chi2 against X), each corrected over the 29 runes;
(3) the runes at offsets -1, +1..+4, +6 from the first S; (4) lengths of the S,S words against the length-weighted expectation (a window needs L >= 6, weight L - 5);
(5) the same lag, position and length tests for all 29 runes; (6) the solved pages 0-6 (ciphertext runes) as negative control.
Not done: the neighbour test for the other 28 runes (too few sites), and a comparison with the English-letter length model beyond the length-weighted expectation.

## Numbers (LP2: 12,956 runes, 2,896 words)
- Reproduced: 11 S,S pairs at lag 5 (null mean 1.77 under W, 2.36 under X). Uncorrected p 0.0001 (W), 0.0003 (X). Corrected over 203 cuts: P < 0.0001 (W), **P 0.021 (X)**. The X null is the more conservative.
  The next-best lag-5 runes are P, ING, A with 7 coincidences each (uncorrected p 0.005-0.03), so S is the strongest rune but the others are not flat.
- Position: S counts first/second/middle/penult/last 32/39/113/39/31 against 36.7/36.7/107/36.7/36.7; chi2 2.1, p 0.70. S has no favoured position. Best of 29 runes: I p 0.045, corrected P 0.73.
- Length: S counts by length 2..7,8+ 32/64/82/47/56/45/106 against 30/73/69/53/52/51/105; chi2 5.4, p 0.48. Best of 29: H p 0.008, corrected P 0.20.
- S share of runes: 3.35% in LP2, 5.36% in the solved pages. S is not over-represented.
- Sites: words of length 8,10,12,8,12,10,6,10,8,6,7 (mean 8.82; expected for lag-5 windows 8.61); first S at word position 0,3,1,1,3,2,0,3,0,0,1. Nothing about them is unusual.
- Neighbours: runes at -1, +1..+4, +6 show no fixed rune at any offset (the most common is TH, 3 of 11 at +3, 2 at +2, 1 each at +1 and +4, as expected for a common rune). The lag-5 echo at neighbouring offsets (-1,+1,+2,+3,+4): 2,1,1,0,0 of 11. The S,S echo is not part of a longer echoed block.
- Solved pages (negative control): 1 S,S pair at lag 5 (null 0.63), p 0.49. The control's own cell scan shows lag-5 E (8 coincidences, p 0.003) and position/length anomalies of F and U, which the cuts-corrected P does not discount (position P 0.00, length P 0.003); these are the known F/U effects of the solved key, so the control is not clean for position or length, but is clean for S at lag 5.

## Verdict
The S excess at lag 5 survives its cuts only moderately (P 0.02 against the conservative X null, not 0.002). It has no position, no length and no neighbour signature, S is no more frequent in LP2 than in the solved text,
and the 11 words are as long as lag-5 windows predict. No insertion rule follows: nothing here says S is a marker or filler rune. Most likely explanation open: the carried echo of obs-lag5 is a weak, S-only coincidence
(chance after selection of S out of 29 is not excluded at P 0.02) with no handle for a simulation. A later session could simulate "S inserted at a uniform slot in about 42% of words" only as a null, since the evidence gives no S-specific rule.
