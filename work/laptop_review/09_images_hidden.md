# Sub-session 9: images and hidden data (laptop review, 2026-10-23)

Scope: keyless checks of the 75 page scans `work/orig/NN.jpg` (LP2 = 17-72, An End = 73, Parable = 74; solved LP1 = 0-16). Nothing in LP2 is solved; nothing here is a result about LP2's method. Scripts (`markers.py`, `pov.py`, `pov2.py`) live in the session scratch folder, not in the repository. CPU used: about 2 CPU-minutes, one process at a time, below-normal priority. No file in `work/orig/` was modified.

## Headline

- Every page is a baseline JPEG (SOF0), 2400 x 3600, with one EOI, no COM, no DRI/RST, no APP1 (so no EXIF or XMP). The only tails are the two already known (5.jpg, 10.jpg).
- The container falls into three groups, and the boundary between two of them is exactly the LP1/LP2 boundary (page 17). This was not logged before (see gap table).
- The nine pages that carry the 2014 OutGuess payloads (0-3, 8, 10-13) are exactly the pages that use the two rare quantisation families and a libjpeg-style JFIF header (1x1 density, units 0). No other page uses those tables.
- A pairs-of-values / DCT-density test (new here) finds nothing on LP2 that stands apart from LP1 or An End. Its positive control shows it sees full sequential LSB embedding (density down about 4x at 25% flips) but does not see the true OutGuess carriers, and its per-page spread is too wide for payloads of 1-3% of coefficients. It is a weak negative, not a clearance.

## 1. Lead table

| lead | source | what it claims | already tested? | concrete test (positive control / null) | rough cost | prior |
|---|---|---|---|---|---|---|
| L1. DCT-domain LSB embedding other than OutGuess (JSteg / sequential-LSB style) on LP2 pages | literature: chi-square attack on sequential J-Steg LSB ([Binghamton J-steg paper](https://dde.binghamton.edu/webstego/data/J-steg.pdf)); not a community claim | a non-OutGuess LSB payload in the DCT bits of LP2 | no for this statistic. `outguess-scan` (TRIED line 92, registry `outguess-scan`) checks OutGuess only; its gap line says AC-only or other embedders are not covered | Run here (section 3): pairs-of-values density on 75 pages. Positive control: in-memory LSB flips on the eligible coefficients (|v| >= 2) at message fractions 0.25 and 0.5 (flip shares 12.5% and 25%): density falls from 0.0184 to 0.0104 and 0.0047 (page 33), 0.0145 to 0.0083 and 0.0035 (page 17), 0.0142 to 0.0080 and 0.0036 (page 4). Null: LP1 non-carriers 4-7, 9, 14-16 and An End 73 | done here; about 2 CPU-min for 75 pages | low: no LP2 page is an outlier (section 3), but the test cannot see 1-3% payloads |
| L2. Calibrated DCT detector (cover model by re-encoding) for L1 at payload sizes of 1-5% | method: Fridrich-style calibration (cover estimate from a re-encoded copy); no community source | an embedder that keeps the global histogram (OutGuess 0.2 does; the carriers here show no density drop) | no | Cover: decode each page with pixels from Pillow (available, 12.0.0), crop 4 px, re-save with the page's own DQT tables and the same sampling (`qtables=` argument), decode coefficients with `pov.py`. Positive control: LSB flips at message fractions 0.02, 0.05 in memory on the page and on its cover. Null: 4-7, 9, 14-16, 73, 74 | about 3-5 CPU-min for 10 pages; needs a Pillow re-encode check first | low-med: calibration is the standard answer to the power problem, but OutGuess-style schemes preserve histograms, which calibration does not fix |
| L3. Double JPEG compression (first-quantisation peaks) on LP2 pages | method: double-quantisation histogram test (Lukas-Fridrich style), no community source | a page was re-encoded after its first compression (an edit, a faint mark, or a 2014 OutGuess re-encode) | partly: `page-scan-audit` (registry, faint marks at pixel level, TRIED line 60) and the quantisation-family reading (community: LP2 keeps original tables) | Histograms of luma coefficients per page from `pov.py`, peak test at multiples of each DQT step. Positive control: a page re-saved at quality 85 then 95 in memory. Null: LP1 non-carriers 4-7, 9, 14-16 | about 1 CPU-min for 75 pages (decode already done) | low: community already reports the original tables on all 58 LP2 pages; a re-encode would have had to keep the same tables |
| L4. 761.mp3 and the OpenPuff claim (magic square, password 33011033) | `work/log/phase60_clue_review.md` row 17; OpenPuff capability: [OpenPuff home](https://embeddedsw.net/OpenPuff_Steganography_Home.html) (lists MP3 carriers; capability only); web search found no 2014 confirmation | the 7 x 7 square (sums 1033) is hidden in 761.mp3 by OpenPuff | yes (clue ledger row 17): untestable, closed-source binary; not run | Keyless part only: hash 761.mp3 found locally and compare its size and SHA-256 with any published value; control: the same pass over other AUDIO files. The extraction itself needs OpenPuff and is proposal only | about 0.1 h for the keyless part | low: the claim is from an archive, the 2014 chain names OutGuess and PGP, and OpenPuff is not used in any confirmed step |
| L5. Thumbnails, EXIF, XMP, comments in the page JPEGs | community (Tumbleson 2024 part 4: no EXIF, comments, quant tables or trailing bytes reported on pages 10-13) | a hidden header or comment | yes, now: none found (section 2). `phase10_prng_time.md` line 20 records no EXIF dates | killed (see below) | done | killed by a measured signal (no APP1, no COM in 75 pages) |
| L6. Page-to-page ICC/JFIF history as a key | community (Discord, Mike: LP2 keeps Artifex sRGB ICC; LP1 OutGuess pages do not) | the container differs between LP1 and LP2 | partly: phase43 item 1(g) (registry commit 325b064) gives the ICC claim, not the three-group split or the JFIF header | Section 2 table; control: the 9 OutGuess carriers are the libjpeg-style group | done | low: the 58 ICC segments are byte-identical (one hash), so the container carries no per-page information |
| L7. File size or dimension numerology (per page bytes vs rune count) | `work/log/research_2026-10-17.md` style numerology; the 2016 563 x 569 image is in TRIED row 21 | sizes or dimensions encode counts | partly: TRIED row 21 and `outguess-scan`; no per-page size vs rune count | Needs the page-to-segment map from `work/book_map.py` (not rerun here). Control: the shuffled rune count per page | about 0.1 h | low: every LP2 page is 2400 x 3600, and sizes track the art (blank pages 0.3 MB, dense art 0.8 MB) |
| L8. Restart markers or DRI segments as a hidden layer | none found | marker-level hiding | no before this session | done here: none in any page | done | killed by a measured signal |

## 2. Image checks: community vs ours

| check | community did it? (source) | we did it? (log) | gap |
|---|---|---|---|
| OutGuess retrieval, default key, seed/len headers | yes: Tumbleson 2024 on pages 10-13 (seed 99/166/150/129, len 1234), and on 14-16 (none) ([Tumbleson part 4](https://connortumbleson.com/2024/12/23/the-cicada-3301-mystery-puzzle-3-solve-part-4/)) | yes: `outguess-scan` (TRIED line 92) | none for the default key; the screen assumes an OutGuess header |
| Binwalk / foremost signature scan of the concatenated page file | yes (Tumbleson, 4 JPEG signatures in one file) | not as a logged step; the 10.jpg tail is decoded by byte equality (`page-scan-audit`) | none material |
| EXIF / XMP / comments / thumbnails | Tumbleson: none reported; our phase10 says no EXIF dates | yes in part (`page-scan-audit`: COM 0); APP1 absence logged here | none |
| Appended data after EOI | yes in part (binwalk offsets) | yes: `page-scan-audit` (5.jpg 360-byte text, 10.jpg four pages) | none |
| Quantisation tables | Discord (Mike): LP2 keep original tables; LP1 OutGuess pages differ (phase43 item 1(g)) | yes: `page-scan-audit`, families 7163be60 / f2d89075 / d1542461 / 722118e9 | none; this session confirms the carrier split (section 2) |
| ICC profile | Discord (Mike): 58 LP2 pages carry an Artifex sRGB profile | not logged before this session | now logged: 58 identical segments on 17-74 |
| JFIF version, units, density | no | not logged before this session | now logged: 1x1 units 0 on the 9 carriers, 400 dpi units 1 on the other 66 |
| Huffman (DHT) tables | no | not logged before this session | now logged (per-page table hashes in `markers.txt`, scratch) |
| DCT coefficient histogram, pairs-of-values chi-square, density | no (search found none for LP) | no before this session | done here: section 3 |
| Double JPEG compression | no | no | not run (L3) |
| Palette / spatial LSB / colour histogram | no | `page-scan-audit`: off-white pixels and faint marks only | spatial LSB is not a useful test after JPEG re-quantisation at these tables (see killed list) |
| Dimensions and file-size numerology | the 2016 image 563 x 569 (community, prime dimensions) | TRIED row 21 (2016 image); LP pages not checked for sizes | per-page size vs rune count not run (L7) |
| Restart markers, DRI | no | no | done: none |

## 3. Results of the checks run

### 3.1 Marker inventory (75 scans, stdlib only; scratch script `markers.py`)
- All SOF0 baseline, 8-bit; 23 pages have 1 component (33-38, 41-42, 45-48, 58-65, 67-69), the rest 3 components.
- DQT families (SHA-1 of the DQT body): {0, 1, 2, 13} use 0b045168/3eb400b3; {3, 8, 10, 11, 12} use bbf6545f/5ca330f6; 4-74 use cbc7b70b/60aec54a (3-component) or cbc7b70b alone (1-component). The first two families are exactly the nine OutGuess carriers.
- JFIF: nine carriers (0-3, 8, 10-13) have density 1x1, units 0 (libjpeg default style). The other 66 pages have 400 dpi, units 1.
- APP2 (ICC, 2,590 bytes, "ICC_PROFILE", "mntrRGB"): present on 17-74 (58 pages), absent on 0-16. The 58 segments are byte-identical (one SHA-1). The boundary falls on page 17, the first LP2 page.
- COM 0, DRI 0, RST 0, APP1 0 on all 75 pages. One EOI per page. Tails: 5.jpg (336,713 bytes) and 10.jpg (3,486,295 bytes), as in `page-scan-audit`.
- Dimensions 2400 x 3600 on all 75 pages.
- Interpretation (inference, not verified against an encoder): the carriers were written by a libjpeg-style encoder with their own quantisation tables; the 400 dpi pages come from another pipeline; the ICC profile was added to LP2 only. None of this is a key.

### 3.2 Pairs-of-values density (luma AC coefficients; scratch scripts `pov.py` and `pov2.py`)
- Pure-Python baseline Huffman decoder (stdlib). Validation: all 75 bitstreams consume to within 0-7 bits of the end of the scan, so the decode is in step. CPU 111 s for 75 pages.
- Statistic: for magnitudes 2k and 2k+1 (k = 1..10), chi-square (a-b)^2/(a+b) summed; "density" = chi2 / nonzero AC count. Under sequential LSB embedding, pairs equalise and the density falls towards 0. Natural pairs are unequal, so the density is large on any cover; the number is only comparable within a quantisation family.
- Densities (chi2 / nonzero AC):
  - LP1 non-carriers 4, 5, 6, 7, 9, 14, 15, 16: 0.0142, 0.0171, 0.0156, 0.0149, 0.0146, 0.0173, 0.0149, 0.0157.
  - LP2 3-component family cbc7b70b (17-32): 0.0145 to 0.0195.
  - LP2 1-component (33-38, 45-48): 0.0184 to 0.0212; (58-65, 67-69): 0.0135 to 0.0169.
  - An End 73: 0.0141. Parable 74: 0.0190.
  - Carriers: 0 0.0162; 1 0.0111; 2 0.0141 (only 25,541 nonzero AC coefficients, so unstable); 3 0.0251; 8 0.0310; 10 0.0277; 11 0.0268; 12 0.0270; 13 0.1016 (an outlier, not interpreted).
- Positive control (in memory, scratch `pov2.py`; flips on the value field LSB of coefficients with |v| >= 2, a random fraction r of them, flip share r/2):

| page | baseline density | r = 0.25 (12.5% flips) | r = 0.5 (25% flips) |
|---|---|---|---|
| 33 (1-comp, LP2) | 0.0184 | 0.0104 | 0.0047 |
| 17 (3-comp, LP2) | 0.0145 | 0.0083 | 0.0035 |
| 4 (3-comp, LP1 non-carrier) | 0.0142 | 0.0080 | 0.0036 |

- Reading: full-capacity LSB embedding drops the density about 4x, so the statistic is sensitive when most coefficients carry a message bit.
- Power problem: within one quantisation family the baseline spread is about 15-20%. A 1-3% payload moves density by roughly 2-6%, far below that spread, so the test cannot exclude a small payload. The true OutGuess carriers are not below the LP1 and LP2 ranges either: their quantisation family (bbf6545f) has no non-carrier to compare with, and within it payload size does not order density (a 140-byte payload on page 8 has the highest value, 0.031; the 31,809-byte payload on page 3 has 0.025; the 1,234-byte payloads on 10-12 have 0.027). OutGuess keeps the coefficient histogram, so a histogram statistic is not expected to see it. This is a finding about the test, not about the pages.
- Result: no LP2 page is an outlier low (minimum 0.0135, page 69, which is inside the LP1 range). This is a weak negative: it does not exclude a sub-percent or histogram-preserving embedder.

## 4. Searched and found nothing
- EXIF, XMP, comment, thumbnail or APP1 segments in any of the 75 pages (no APP1 anywhere; COM 0).
- DRI or restart markers (none), progressive scans (none), second scans (none).
- Trailing data after the first EOI, other than 5.jpg and 10.jpg (already known).
- Per-page ICC variation: none (58 identical segments on 17-74).
- Per-page dimension variation: none (all 2400 x 3600).
- Community reports of EXIF, comments, thumbnails or appended text on LP pages (Tumbleson 2024; search results): nothing.
- Community reports of a chi-square or DCT-statistic analysis of LP pages: none found (web search returned general steganalysis only).
- Community or web evidence of OpenPuff on any 2014 image or on the 2014 pages: none. The only OpenPuff claim is the 761.mp3 archive item (L4).

## 5. Killed by known signal
- Spatial (pixel-domain) LSB or palette hiding: every page is baseline JPEG (measured), and a pixel payload does not survive re-quantisation at these tables. The only embedding family seen in the 2012-2014 chain is DCT-domain (OutGuess). Not tested; killed on the JPEG format.
- Comments, EXIF or thumbnails as a carrier: no such segment exists (measured).
- Per-page ICC or JFIF content as a key: the ICC is byte-identical across all 58 LP2 pages and the JFIF header splits by group, not by page (measured).
- Dimension numerology: all pages 2400 x 3600 (measured).
- Histogram-level LSB detection as a payload finder: killed as a detector by the positive control (the true OutGuess carriers show no drop); kept only as a weak screen against sequential LSB.
- Restart markers as a page-level layer: none present (measured).

## 6. Top 3 untested leads, specified for a later run
1. **Calibrated density on LP2, at payload sizes of 1-5%.** Inputs: `work/orig/17.jpg`, `33.jpg`, `69.jpg`, `73.jpg`, `74.jpg` and the LP1 non-carriers 4, 6, 9, 15 as nulls. Method: decode pixels with Pillow; crop 4 px; re-save with the page's own quantisation tables (Pillow `qtables=`) and the same component count; decode the coefficients of page and cover with `pov.py`; compute density on both; per page report the ratio. Controls: in-memory LSB flips at message fractions 0.02 and 0.05 on the page and on the cover (planted positives, should be found at a density ratio below 0.9 on the calibrated pair); nulls as listed. Stop rule: any LP2 page below the null range by more than 2 sd of the null ratios is a lead; otherwise the test is closed for LSB embedders at 2% and above.
2. **761.mp3 identity check (keyless part of L4).** Input: the local copy of `761.mp3` (the Cicada OS ISO holds an AUDIO folder; the repository does not hold the mp3 itself, so locate it first). Method: size, SHA-256 and first-frame header; compare with any published hash. Control: the same pass over the other AUDIO files, which should show no link to the 33011033 claim. The OpenPuff extraction is out of scope (closed-source binary), so this lead only settles whether the file the claim names is the file we hold.
3. **Double-quantisation test on the LP2 luma histograms (L3).** Input: the per-page luma histograms from `pov.py` (already computed in the run; re-run on 17, 33, 50, 65, 73, 74 plus 4, 9 as nulls). Method: for each page, for each DQT step, the fraction of coefficients at multiples of the step versus the neighbours; a double-compression peak would show at the first-compression steps. Controls: a page re-saved in memory at quality 85 then 95 (must show the peak); nulls on the LP1 non-carriers. Stop rule: no peak on any LP2 page closes the re-encode question for LP2.

## 7. Summary of the checks done here vs the repository
- New here: JFIF density and ICC per page (three groups), DHT and DRI/RST inventory, APP1/COM absence, pairs-of-values density on all 75 pages with positive and null controls, bit-consumption validation of the decoder.
- Already in the repository and confirmed: JPEG structure, quantisation families, tails, faint marks, OutGuess header screen.
- Not run: double-compression test (L3), calibrated density (L2), size-vs-rune numerology (L7), the 761.mp3 hash check (L4).
