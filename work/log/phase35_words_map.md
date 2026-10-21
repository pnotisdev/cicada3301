# Phase 35: LP2's word-length / word-sum sequences as keys, and the ciphertext reversed per word / clause / line (ranks 1 and 3 of phase 34)

Nothing in LP2 is solved. Code `work/kscreen/phase35.py` (build / controls / run / verify / summary), engine = the pdir build (default decode, bit-identical), 2 threads, decision rule unchanged (IoC >= 1.40 on the first 300 runes, then verify.py over the whole window against 20 random offsets of the same stream). Outputs `results/kscreen/phase35/` (controls.txt, summary.txt, *.tsv, *_verify.txt).

## A. LP2's own word sequences as additive key streams
Streams (`data/phase35/words.ksb`, 24): word length n, GP index sum R, GP prime-value sum G of every word of the 8 screened sections, raw mod 29 and prefix sums mod 29, forwards and reversed, for the whole book (2,894 words, sections concatenated) and for section 0.15 (the only section with >= 450 words). One value per WORD, walked rune by rune by the screen. 20 of 24 are predicted flat under English (<= 1.003); the 4 raw-length streams are not (1.08), so they could not be keys of a flat text. Per-page sequences have at most ~60 values and cannot cover a 300-rune window (not run). Section streams are constant shifts of subsequences of the book streams (the screen's shift absorbs them), so they add little.
- Controls (independent planter `pdir_ref.plant`, forward only; held-out English; skip rule q = 0.81, models 0/1, mults 1/28): 4 stream cases x 3 windows, recovered at the planted offset (+-2, the skip alias) with IoC >= 1.60 (1.60-2.11), a different word stream on the same ciphertext stays at 1.19-1.22. (First run: 3 FAIL from two defects of the control design, offset gate without the +-2 alias and a section stream that is a shift of the book stream picked as the "other" stream; fixed, rerun passed.)
- Real: 1.10 M decodes, best IoC **1.2557** (book G prefix forward, seg0.12). Matched null (10 shuffles of every stream, 11.0 M decodes): best 1.3042. verify.py top 10: 0 of 10 kept.

## B. Ciphertext reversed per word / clause / line
Hypothesis: X = reverse-within-unit(p + k). The windows are transformed (runes reversed inside each word / clause ('.' and '&') / line ('\n' and '%') of the transcription; window prev = -1) and run through the DEFAULT engine against the 581 flat library streams, 8 sections, both mults and models, 355 M decodes each. Null: the transformed windows against 150 random keystreams (94 M decodes).
- Controls: held-out English enciphered with a library stream, then reversed per unit (clause and line units synthetic: 6-14 and 4-9 words per unit, because the plain windows carry no clause marks); the pipeline's transform recovers the plant at the exact offset (IoC 1.60-2.07, 9 of 9 windows) and the same plant WITHOUT the transform stays at 1.21-1.26.
- Results (best IoC real / matched null): word **1.3385** / 1.3210; clause **1.3740** / 1.3042; line **1.3669** / 1.3786. None reaches 1.40; the real maxima are inside the null range (the null has 27% of the decodes, the line null still exceeds the line real). verify.py top 10 of each: 0 of 10 kept.

## Verdict
Both negative: **0 hits, 0 verified**. Power: the planters recover keys of the same families at the exact offset in 21 of 21 windows after the fix, so a stream-based key of these two types would have shown.

## Not covered
- Word sequences of the solved sections or of other lengths (per-page, per-line, per-clause values), values taken from the plaintext, mod other moduli, sums of runes per clause or line as streams; per-page streams are too short.
- Reversal combined with other mechanisms (signs, pointer direction, skip variants), reversal of units not given by the transcription's marks (the page grid, the 29-wide layouts), reversal of only some units (e.g. every other word), partial reversals (swap of the two halves).
- A key outside the 581 flat library streams; windows other than the section starts; the control for B uses synthetic clause/line units.
- Looks like the transformed hypothesis was tested at 355 M decodes per unit against about 10^9-10^10 random decodes giving 1.37-1.39 at the top: the clause (1.374) and line (1.367) maxima sit in that noise band.
