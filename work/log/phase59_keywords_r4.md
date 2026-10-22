# Phase 59: keyword keys under R4

Nothing in LP2 is solved. Script `work/phase59_keywords_r4.py`; results `results/analysis/phase59_keywords_r4.txt`, per-task JSON in `results/chanscreen/phase59/`.

## Plan (written before the run)
1. Keywords: every word / clause / 2-3-word phrase / title / first and last line of the solved pages and the 2014 signed messages (phase 50 `sources()`), plus 2-3-word phrases inside signed lines, all spelling variants (C->F, ING->N G, IA->I O), lengths 3-30. A periodic key read at all L offsets covers its rotations, so keys are deduplicated up to rotation and repetition.
2. Engine: the phase-51 mid-word arc (`backward_mid`, kind 3, nu 0.42, repair q 0.81 as the decoder default), key stream = keyword repeated to need_extent + L, offsets 0..L-1, both signs. Channels hold and spend only (key advances once per real rune, as on the solved pages). skip5 / coin are number-stream channels (extent 6x / 3x) and would triple the cost; not run.
3. Windows: every n300 start (0, 300, ..., plus the last full window) of each LP2 section of >= 300 runes. The two DJU BEI copies (flat 6,555 in segment 13, 28 runes in; flat 12,950, last words of segment 15) lie inside the windows 13@0 and 15@3016, so they are covered; no extra windows.
4. phi(prime) = library stream `primes-1 (totient)`, all four channels, all 48 windows. The literal-F variant (plaintext F unencrypted, key not advanced) is not a channel of the engine: not tested.
5. Control: R4 plants (phase 57 planter `make_r4`, hold and spend, cicada and english plaintext) with a keyword key (DIVINITY, FIRFUMFERENFE, CIRCUMFERENCE and 5 random set keywords), searched against the true keyword + 150 other set keywords + 150 random keywords of the same lengths; a matched iid-key plant searched with the true keyword is the null.
6. Hit level: S_guard >= T300 = 29.80 (calibrated for ~13M cells x 8 per window; this scan has ~10^5 cells per window, so T300 is conservative); cells >= 20 are recomputed fresh and listed. A hit goes to `work/kscreen/verify.py` (IoC, A/I oracle, prime clause sums) and to the DJU BEI constraint.
7. DJU BEI constraint: the copies are 6,395 runes apart = 5 x 1279. A periodic key repeats its 6-run only if the number of key runes consumed between the copies is a multiple of L; with no inserted runes that needs L | 6395 (L = 5 only among lengths 3-30), with R4 nulls (about 45% of words) the consumed count is below 6395 and is a multiple of L with probability about 1/L. Checked for any hit only.
8. Budget: first window measured at 322 s for 1,940 keywords (one process, machine shared with the queues) -> 48 windows about 4.3 CPU-h + phi + controls.

## Results
(filled in below)

- **Keywords:** 1,940 distinct periodic keys (up to rotation and repetition; lengths 3-30; solved-page words/clauses/2-3-word phrases/titles/lines, 2014 signed words/lines/2-3-word phrases, spelling variants C->F, ING->N G, IA->I O).
- **Control** (32 + 12 R4 plants, hold and spend, cicada and english plaintext, 12 with sign -1; DIVINITY, FIRFUMFERENFE, CIRCUMFERENCE and 5 random set keywords): the true keyword scores 113.8 to ~175 (median 150.5), 44/44 above T300 = 29.80 with the right sign; the phase is exact in 41/44 and off by one in 3 (window-start pointer ambiguity). Wrong keywords: set keywords max 25.4, random same-length keywords max -45.8; a matched iid-key plant searched with the true keyword: max -93.5.
- **Scan:** 48 windows (every n300 start of sections 0.7-0.15, last full window included; the DJU BEI copies sit in 0.13 @ 0 and 0.15 @ 3016) x 1,940 keywords x hold/spend x both signs x every phase: **max S_guard -63.96** (0.15 @ 1200, "species not who"), 0 cells >= 20, 0 windows >= T300. CPU 4.44 h.
- **phi(prime)** (library stream primes-1) 48 windows, hold/spend/skip5/coin, both signs, every offset: max -62.46.
- **DJU BEI constraint:** no hit, so not applied (6,395 = 5 x 1,279; only L = 5 divides it).
- **Not excluded:** keywords outside this set (other English/Latin words, names), coin/skip5 channels for keywords, the literal-F (F unencrypted, key not advanced) variant, keys with two layers, keyword keys with a different insertion rule than R4's one-null-per-word, windows shorter than 300 (section 0.10 has 9 runes).
