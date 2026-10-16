# Phase 9: the page art (2026-10-17)

The earlier phases worked from the transcription and OCR. This is a first look at the non-text parts of the 75 page
images (`work/orig/NN.jpg`, 2400 x 3600), made with contact sheets and `work/ornament_dots.py`.

## What the pages show (by image number)

| Pages | Art |
|---|---|
| 15-24 | mirrored spiral borders; page 20 has two paragraphs with red drop caps; five dots at the bottom of page 24 |
| 25-31 | tree drawings in a margin; a mayfly (page 31) |
| 32 | the 4 x 4 number grid, an infinity symbol |
| 33-39 | text only; page 39 ends with a black glyph and a reclining figure |
| 40 | five dots above the text (the page-24 figure upside down) |
| 41-44 | mirrored insect drawings in the margins; an insect wing (page 44) |
| 45-49 | text only; a blurred tree (page 49) |
| 50-56 | numbered section (red numerals 1-5 on 53-55): a six-sign cuneiform-style cluster at the top of 51-56 and bottom of 50; three dots on pages 50 and 56 |
| 57-72 | mirrored leafy trees with small dot groups; the 256-byte base-60 grids on 66-68; a cicada (70, 72) |
| 73 | the hash, and the five-dot figure again |
| 74 | red heading, an insect drawn in stipple |

## Measurements

- **The border art is mirror-symmetric** about x = 1199.5 (e.g. page 20: dots at x = 248 and 2151, 264 and 2135). The
  mirror residual (`results/analysis/ornament_asymmetry.tsv`) is exactly zero on pages 20-24, 32-38, 45-48 and 51-56.
  Pages with a residual are the ones with deliberately asymmetric art (trees, insects, the hash page, the glyph on 39).
- **The five-dot figure is one rigid shape.** Pages 24, 40 and 73: the ten pairwise distances agree to 0.3 px (scale
  1.0000). Page 40 is page 24 flipped vertically (the dot y-pairs sum to 3674.0 for all five); page 73 is the same
  shape rotated. Dot diameter 70 px, area ~3,560 px.
- **The three-dot rows** (pages 50 and 56) are collinear with gap ratio 0.8731 on both, at two scales (417.5 / 478.2 px
  and 196.0 / 224.5 px).
- The stippled red block that ends each red heading and paragraph is the same 13-square pattern everywhere.
- The small dot groups beside the spirals and trees are decoration: 3 + 3 mirrored on pages 20-24, 3 left and 5 right on
  pages 57-72, identical on all of those pages.

## What it means (and does not)

These are reused figures, i.e. divider and decoration marks. Nothing here varies from page to page in a way that could
carry key material. Their placement may still say where sections begin and end: five dots close page 24 and open
page 40 and sit above the hash on page 73; three dots separate paragraphs on pages 50 and 56. The section structure
of the transcription (`$` segments) has not been aligned with the image pages by OCR yet; doing that would show whether
the dividers are the section boundaries.

Open: the six cuneiform-style signs (pages 50-56). They look like Neo-Assyrian-style wedge signs; they are not
identified here. A research agent was asked whether the community has read them
(`work/log/research_2026-10-17.md`).
