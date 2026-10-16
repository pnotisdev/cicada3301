# Phase 9: is the transcription's separator layer right? (2026-10-17)

Phase 2 checked the runes against the images; the separators (`-` word dot, `.` clause mark) were never checked, although
every word-scoped statistic rests on them (word lengths, the dictionary screens, the seed sweeps' scoring, dsearch).
aldegonde reports that most clean image-versus-transcription disagreements are separators visible in the image and missing
from the transcription (`work/log/research_2026-10-17.md`, section 2.6).

## Audit (`work/separator_audit.py`, `results/analysis/separator_audit.txt`)

For images 15-70: `ocr.segment` gives each line's glyph boxes; a transcription line is paired with a detected line when the
rune counts are equal; for each gap between adjacent glyphs the ink between the two boxes is classified (no blob / one blob /
several). 9,828 gaps are measurable (1,197 are not: boxes touch).

| transcription \ image | none | word dot | clause |
|---|---|---|---|
| none | 7,393 | 4 | 0 |
| word dot | 0 | 2,295 | 9 |
| clause | 0 | 0 | 127 |

- **No separator is missing from the transcription and none is extra.** The 4 "none vs word" cases are blobs of 362 px:
  the tick stamp (images 21, 38, 52, 58), i.e. aldegonde's four lone apostrophe ticks, not word separators. Their words
  (cipher runes) have stem + tail lengths 3+1 (segment 0.8, rune 381), 2+1 (0.11, 1526), 2+1 (0.14, 464), 3+1 (0.15, 449).
- The 9 "word vs clause" cases are word dots next to tick pairs (quote marks) or partial clause marks.
- Ticks (`work/ref/tick_marks.tsv`, 18 gaps) also appear next to separators on images 15 (the solved koan 0.5), 23, 24, 39,
  57, 59, 70: quotation marks, as in the solved koans.
- Caveat: the audit sees only measurable gaps and classifies by blob count; it does not read marks fused to runes.

## Consequence for the word-length anomaly

Missing separators cannot explain it, independently of the audit: if every separator is lost with probability m
(`work/seploss.py`), any m above ~5% fattens the long-word tail far beyond LP2's (12+ runes: 0.9% against 0.7-1.1% for
English), the best fit for English counted in letters is m = 0 (G = 55, p = 3e-8), and for English in Gematria runes m = 0.05
(G = 212). The deficit is selective (2-rune words 15.9% against 20% in letters); the "one extra rune in 40% of multi-rune
words" fit (G = 20.5, p = 0.025) remains the best simple description. The transcription's word boundaries can be trusted.

## Use

The four apostrophe words are weak cribs (plaintext of shape [3 or 2 letters] ' [1 letter]: THAT'S, DON'T, IT'S, WE'D ...)
for filtering key candidates after a screen; they do not locate a key.
