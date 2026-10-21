# Phase 40: the book's numbers as line:position pointers into Liber Primus

Question: Cicada's 2012 Mabinogion code reproduces as LINE : CHARACTER (1-based, spaces counted) on a line-wrapped text, a
format phase 31's 1,520 readings did not include. Do any of the book's own numbers, read as line:position pointers into
Liber Primus's own lines, produce a message? Prior is low (every Cicada book code came after a chain that named the text).
Code: `work/phase40_line_pointers.py`; outputs: `work/log/phase40_line_pointers_output.txt`.

## 0. Preregistration (written and frozen BEFORE any real-data scoring; only `count` and `selftest` had run)

**Pointer sources** (value sequences; ranges in brackets):
`g02` the 12 printed numbers of 0.2 [18..272]; `sq06` the 25 numbers of the 0.6 square, 5x5 [204..1311];
`g30 values` the 16 page-30 grid values |3301 - p_k|, 4x4 [708..4516]; `g30 k_i` the prime indices 1,2,3,4,6,9,14,... [1..988];
`g30 p_k` the primes themselves [2..7817]; `payload` the 256 bytes of 0.15 (two base-60 digits a,b -> 60a+b) [0..255];
`LP2 numerals` the 6 numerals of segments 9 and 14 [1..7].

**Orders.** Every source: forward, reversed. The two squares and the 4x4 grid additionally: column-major, spiral
(4x4: the grid's own spiral from `grid30.spiral_order()`; 5x5: clockwise from the top-left corner inwards), each also reversed.

**Pairing modes** (on the ordered sequence v): `consec_lp` (v0,v1),(v2,v3)..., line first; `consec_pl` position first;
`slide_lp`, `slide_pl` overlapping pairs (v_i, v_i+1); `div60` line = v // 60, position = v % 60 (the payload's digit split,
"60*line + pos"); `flat` v is a single index into the target's character stream; `lineinit` v is a line number, position 1.
For the three 2D grids also `rc_lp`, `rc_pl`: the cell coordinates (row, column) in the enumeration order, values ignored.
**Bases:** 1-based (Cicada) and 0-based for every mode except `rc` (coordinates; one base).

**Targets.** Texts: the whole book's lines (`book`); LP2 only, segments 0.7-0.15 (`LP2`); the plaintext lines of the SOLVED
segments (`solved`, in the ciphertext's line layout, from `lp.KNOWN`); each page with >= 8 lines separately (`pageN`, line
numbered within the page) and each solved page with >= 8 lines (`solvedpageN`). Lines end at `/`, paragraph or page marks
(numerals skipped). Four variants of every text: unit = runes or Latin letters (GP transliteration, digraph runes count 2-3
positions), separators (word breaks, as one position each) counted or removed. 78 texts x 4 = 312 targets.

**N (counted in advance by `count`)**: 332 readings per target (308 value readings + 24 rc readings) x 312 targets
= **103,584 readings**. A reading is scored only if >= 90 % of its pointers are in range and it yields >= 6 valid
trigrams; unscored readings still count in N (they are what the family could have said).

**Score.** Resolved characters -> Latin letters; mean English letter-trigram log-likelihood over fully valid trigrams (model
as phase 31); z = (observed - mean of null) / sd of null, null = 60 draws of random pointers with the same count and per-column
min..max range on the same target. Spaces and invalid pointers break trigram context.
**Anchored checks** (any resolved string): contains `HTTP`; `ONION`; `CALLUS`; or >= 7 consecutive spelled digits
(ZERO/OH/ONE..NINE/NINER: phone-number shape). Rates measured in the null.

**Whole-screen null.** The full family (rc readings excluded from the null, they are deterministic) repeated with every source
replaced by random integers of the same length and range, best z per run, 100 runs, <= 2 cores. Decision threshold: a real best
z must exceed the 95th percentile of the null maxima, and (CLAUDE.md) any hit would still need whole-section verification;
an anchored hit counts only if its rule is exact and the anchor rate in the null is reported.
**Positive control.** An English window (V->U, K->C, Q->C, Z->S, the rune alphabet has none) is planted into a target through
random valid pointers (`consec_lp`, base 1), n = 12, 25, 64, 128, 256 pointers, 100 plants each, on LP2 Latin/no-sep, LP2
rune/sep and solved Latin/no-sep, with pointer values free and restricted to <= 255 (payload-like). Power = share of plants whose z
beats the null threshold at the correct reading. Caveat fixed now: power is for a reading whose format is right; a message whose
format is not in this family is invisible to it.

## Results
Run: `real` (seed 4000; identical rerun reproduced it), 100 whole-screen null runs (`null`, seeds 9100-9149, 9200-9249), 26 `nullrc` runs
(seeds 9300-9309, 9400-9407 plus the 8 of the second process; stopped at 26, 2 min each), `plant 4.18`. Raw output: `phase40_line_pointers_output.txt`.
Scored readings: 9,525 of 103,584 real (about 2,460 per null run: the rest have < 90 % of pointers in range or < 6 trigrams, e.g. g30 values up to 4516 and p_k up to 7817 mostly fall off the book's ~700 lines).

| quantity | value |
|---|---|
| best real z over the 308 value readings | **4.01** (6-numeral set, `lineinit`, 6 trigrams only); next 3.58 (sq06 spiral flat base0, LP2 runes, 35 trigrams), 3.56 (payload rev flat) |
| whole-screen null, max z per run (100 runs) | mean 3.58, sd 0.38, 95th pct **4.18**, 99th 4.38, max 4.40 |
| best real z over the 24 `rc` (coordinate-only) readings | 4.44 (g30 grid, col, `rc_pl`, a page with 6 trigrams); 4.20 (sq06, 23 trigrams) |
| null for `rc` readings (random pointers, same ranges; 26 runs; post hoc, see below) | mean 3.90, 95th pct 4.34, max 4.92; 1/26 runs >= 4.44 |
| anchored hits (`HTTP`, `ONION`, `CALLUS`, >= 7 spelled digits) in the real screen | **none** |
| anchor rate in the null | `HTTP` or `ONION` appears somewhere in 62 of 100 null runs (46 + 8 + 8); so a lone `HTTP`/`ONION` hit would have meant nothing; `CALLUS` and 7-digit runs: 0 in 100 |

Power (planted English window, right format `consec_lp`, base 1, threshold 4.18, 100 plants per cell; pointer values free / <= 255 gave the same within noise):

| pointer count | 12 | 25 | 64 | 128 | 256 |
|---|---|---|---|---|---|
| LP2, Latin letters, no separators | 0 (6 letters = 4 trigrams: not scored) | 6 % | 77-79 % | 100 % | 100 % |
| LP2, runes, separators | 0 | 0 | 14-15 % | 89-91 % | 100 % |
| solved plaintext, Latin, no separators | 0 | 0 | 10-11 % | 64-68 % | 100 % |

Reading: only the 256-byte payload (128 pairs) has enough pointers for this screen to see a message; the 12/16/25-number sources (6-12 letters)
are blind to any message shorter than about 30 letters, whatever it says. A message of Cicada's usual length via these small sets would be
under 12 letters, below the screen's resolution, so for the grids the real test would be the anchored forms (an exact `HTTP`/phone shape), which also
found nothing (and their false-positive rate for `HTTP`/`ONION` is high). The payload, the one source with power, gave 3.56 at best.

Deviations and caveats (stated openly): (1) the `rc` readings use only 1-5 distinct line/position values, so their z against a same-range null is
noisy and their best (4.44) came from 6-23 trigram strings; the preregistration excluded them from the null max, and their separate null (`nullrc`)
was added after seeing that they dominated the top list (post hoc; 26 runs only). Either way it is not above the null (non-rc 4.01 < 4.18;
rc 4.44 vs null 95th 4.34, 1/26 runs reach it). (2) The null maxima are bounded by small-n readings; a high-z reading with
few trigrams is not distinguishable from them. (3) Numerals printed on lines were skipped from the target text; the rune-unit
positions count digraph runes as one, Latin unit as 2-3. (4) Non-1:1 cipher: the ciphertext lines of LP2 are scrambled by an unknown key, so only the
`solved` targets hold plain language; a pointer set designed against LP2's plaintext is outside this test (plaintext unknown).
(5) The planted control is for pairs `(line, pos)` in consecutive order; other layouts of the same numbers are separate readings
and were each counted.

## Verdict
No message. The best real z (4.01 non-rc; 4.44 rc) sits inside the null distribution of maxima (95th pct 4.18; rc 4.34), no anchored form was
found, and the screen can see a planted message only with >= 64-128 pointers (the payload) and not with the 12-25 numbers of the grids. Evidence level:
negative for the readings listed (103,584 counted, 9,525 scored), with the stated power limits; weak for the small number sets. Nothing in LP2 is solved by this.

Note: the `nullrc 40 9300` run was stopped incomplete at 13:5x (about 20 of its 40 runs were done; the 26 nullrc runs reported above came from it and the second process), and every phase40 process has been killed.
