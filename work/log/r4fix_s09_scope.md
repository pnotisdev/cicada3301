# R4 repair session s09: scope of ideas 10-13 (planning only)

Nothing in LP2 (sections 0.7-0.15, 12,956 runes) is solved. This session ran nothing: no engine, no simulation, no queue, no script beyond reading. The commands named below do not exist yet; they are the interface the run sessions should build. Every CPU figure is arithmetic on measured costs quoted from the records, with the source given.

Question: for ideas 10-13 of `work/laptop_review/11_next_100.md` (R4 x the 26 other multipliers; R4 on stride windows; R4 coin and skip5 channels; R4 x page and clause starts with about 60 Cicada-named streams), what exactly would run, how many cells and CPU-hours it costs, which planted controls and nulls exist, what it adds to the record, what it depends on, and in which order to run it.

Read: `work/r4fix/00_brief.md`; `work/phase57_pilot.py`; `work/chanscreen/v2/step4/lp_pilot_mid.py`; `work/chanscreen/v2/step4/plant_mid.py`; `work/chanscreen/v2/step4/plant_edge.py` (need_extent, step); `work/chanscreen/v2/step3/common.py` (CHANNELS, SIGNS, T300); `work/log/phase57_mechanism.md`; `work/log/phase51_midword_channel.md`; `work/log/phase59_keywords_r4.md`; `work/log/phase60_clue_review.md` (T2, T6, T8 and the per-cell timing lines); `docs/registry.toml` rows `lib-sections`, `multipliers`, `restart-units`, `restart-library`, `open-clause-windows`, `keywords-r4`, `p60-numkeys-r4`, `p60-blobs-r4`; `docs/QUEUE.md`; `jobs/queues/r4lib.txt` (read only); `results/analysis/phase57_pilot.txt`; `work/laptop_review/08_loose_ends.md` (sections 0, 1 leads 1-5, 4 A-C); `work/laptop_review/11_next_100.md` ideas 10-13. Read but not relied on: `work/r4fix/s01_edge_plants.py` and `s02_slot_rules.py` (other sessions' files, not inspected beyond their names).

## 0. Summary

- Ideas 10-13 all decode with the unchanged interior mid arc (`lp_pilot_mid.py` / `engine_mid`, nu 0.42, word-start flags only). None of them can be read as a result until s01 says whether that arc sees R4 with edge-slot nulls. If it does not, every idea here waits for a union arc (08 section 4 A).
- Cheapest first: idea 13 (about 10 CPU-h planned, reuses the phase 57 plant generator without change). Largest gap in the record: idea 11 (40 library windows that have never been run under any key model, 112 CPU-h planned, so run a cheap R4-free companion and one pilot window first). Idea 10 costs 36 CPU-h per window for a family with no clue pointing at it. Idea 12 needs R4 plant code that does not exist for skip5 and coin.
- Three figures in the records do not survive the arithmetic and should be corrected (section 5): the cost of idea 13 in `11_next_100.md` (2-5 h; the stated inputs give about 8-10 h, or 300+ h if the streams have 0.5 M offsets each); lead 12's "about 3x" for coin and skip5 (the brief's timings imply about 1.44x in total); and the R4 slot model of the mid arc (section 2).
- Found while reading (not in the 08 list): `lp_pilot_mid.py` forces the first word-start flag of every window to 1, which is wrong for a window cut inside a word; stride windows (idea 11) need the true flag.

## 1. Cost model (used for every number below)

Cell = one (stream offset, sign, channel) decode of one window under the mid arc.

| quantity | value | source |
|---|---|---|
| per cell, mid arc, n300 | 155 us | phase 60 log: "0.155 ms per offset and (window, sign, channel)" (phase 59 engine); check: the phase 60 T8 R4 window (19.7 M offsets x 4 cells x 155 us = 3.4 h) against the recorded 3.56 h |
| per cell, mid arc, n150, hold+spend | 75 us | brief: "about 301 us per offset for hold+spend at n150" = 301 / 4 cells |
| per cell, n150, four channels averaged | 54 us | phase 57 LP pilot: 1.61 CPU-h, 106,626,192 cells (= 432 us per offset, both signs, four channels) |
| linear fit used for other n | 0.52 us x n per cell | through 75 us (n150) and 155 us (n300) |
| offsets, library, n150 | 13,328,274 | 106,626,192 cells / 8 (phase 57 pilot, 1,439 streams, four channels, both signs) |
| offsets, library, n300 | 13.11 M | each stream loses 150 offsets (need extent 1 x n + 16 for hold and spend, `plant_edge.py:76`) |
| one library window, n300, hold+spend, both signs | 52.4 M cells = 2.26 CPU-h raw | 13.11 M x 4 cells x 155 us; the registry planning figure (`r4lib`) is 2.8 CPU-h, so the planning factor is 1.24 |
| skip5 + coin relative to hold + spend | 0.44 (central), 1.0 (upper) | 432 / 301 = 1.44 total, so the two extra channels are 0.44 of hold+spend, if the brief's 301 and 432 are on the same basis. Not measured per channel in any record. |

Two checks that fail and why they matter:
- Periodic keys do not fit the cell model. Phase 59 measured 4.44 CPU-h for 1,940 keywords over 48 windows (hold+spend, both signs, every phase); the cell model gives about 0.3 h. Use measured costs for keywords, number strings and MB files, not the model.
- Lead 12 in `08_loose_ends.md` says coin and skip5 cost "about 3x" the hold/spend runs. The channel count alone gives 2x (total) or 1x (extra). Only the key-extent factors (coin 3n+16, skip 6n+16 in `plant_edge.py:76`) give anything near 3x, and those change the offsets for finite streams only, not the cost per cell.

## 2. Shared dependencies and prerequisites

1. **s01 (edge-slot plants).** Every idea uses the interior arc. If s01 finds the arc blind to edge nulls (08 section 4 A: detection below about 90% in the 0..L mode), all four ideas wait for a union arc. The union arc's cost per cell is unmeasured; this plan assumes it is no more than the mid arc. If it is dearer, every CPU-h figure below scales by that factor.
2. **s02 (slot rule, interior 1..L-1 against 0..L).** It changes the plant model for all four ideas, not their cell counts. The plants here inherit `plant_mid.py:47` (`randrange(1, L)`) unless s02 changes the generator.
3. **s03 and s08.** The brief names them as dependencies but does not say what they cover. I did not read their files and assume neither changes the arc or the library export. If either does, redo the table.
4. **Library export.** Ideas 10, 11 and 13 use the 1,439-stream export. The registry says 1,447 in some rows (`08` lead 5). The 8 extra streams would add about 0.6% to each count here; run them through the n300 screen once, in the same batch.
5. **Word-start flags at window starts.** `lp_pilot_mid.py` sets `_W['ws'] = [1] + [brk[start + i] ...]`, so the first rune of every window is treated as a word start. Correct for the section starts that were run, but wrong for a stride window cut inside a word (idea 11). Use `brk[start]` for the first flag, and use the same convention in the plants. The expected effect is one rune per window, to be checked with the controls. Page and clause starts (idea 13) should be word starts by construction; confirm from `data/pages.txt` and the clause marks before running.
6. **Plant code for the new channels.** `make_r4` (`work/phase57_pilot.py:24-70`) implements the R4 repair for hold and spend only. `plant_edge.py:79-100` has skip and coin steps, but no R4 repair in them. Idea 12 needs a written rule for what R4's repair does when the channel redraws the key, before any plant can be generated.

## 3. The four ideas

### Idea 10. R4 x the 26 key multipliers other than +-1 (library, mid arc)

- **What runs.** Pre-map each library stream: k' = m x k (mod 29) for m = 2..14 (13 maps). The engine's sign (+1, -1) covers m and 29 - m, so 13 maps x 2 signs = the 26 multipliers 2..27. Hold and spend, n300, every offset, both signs. Hit rule S_guard >= T300 = 29.80, then `work/kscreen/verify.py`.
- **Proposed command (not written).** `python -B work/r4fix/s09_mult_r4.py run --sec 15 --start 0 --n 150 --channels hold --maps 2-14 --workers 14` (pilot); full run per window with `--n 300 --channels hold,spend`.
- **Cells.** Per n300 window: 13.11 M offsets x 13 maps x 2 signs x 2 channels = 682 M cells. Pilot (0.15@0, n150, hold only): 13.33 M x 26 cells = 347 M cells.
- **CPU-h.** Per n300 window: 682 M x 155 us = 29.4 h raw, x 1.24 planning = 36 CPU-h (= 13 x the 2.8 h of one `r4lib` window). All 8 section starts: about 290 CPU-h. Pilot: 347 M x 75 us = 7.2 CPU-h (5 h if the 54 us four-channel figure applies).
- **Controls.** Positive: no mid-arc plant exists at any multiplier other than 1 and 28 (`make_r4` draws `mult = 1 if i % 2 == 0 else 28`). Build 13 new plants with `mult` = one of 2..14 (or 15..27 equivalently), using the `make_r4` rule otherwise, and check the decoder recovers each at its map and sign. Second control: the mult-1 decoder on an m-plant must fail, which shows the map matters. Null: matched iid-key plant for each map (phase 57 nulls: -18.0 at n150, -55.8 at n300) plus 50 random library streams.
- **What it adds.** The `multipliers` row (registry) is R4-free, section starts only (5,729,965,248 kscreen decodes, 0 of 15 verified). No mid-arc run at multipliers other than 1 and 28 exists. The r4lib queue covers only 1 and 28.
- **Depends on.** s01, s02, library export.
- **Priority: low.** 36 CPU-h per window for a family no clue points at; the R4-free 28-multiplier run was negative; run it only after idea 11's pilot.

### Idea 11. R4 on the library at stride windows (not only section starts)

- **What runs.** The 40 stride windows of sections 0.7-0.15 that are not section starts. The 48 windows of `keywords-r4` are every n300 start (0, 300, ..., plus the last full window) of each section of at least 300 runes; 8 of them are section starts (already covered by `r4lib` and phase 51/57). Windows: 0.13@300 and the other stride starts, including 0.15@3016 (the last full window). Hold and spend, n300, both signs, all 1,439 streams, every offset. Hit rule as idea 10.
- **Proposed command (not written).** `python -B work/r4fix/s09_stride_lib.py run --windows stride --channels hold,spend --workers 14`. Pilot: `--windows 0.13@300` only.
- **Cells.** Per window: 52.4 M (13.11 M x 4). All 40: 2.10 G cells.
- **CPU-h.** 2.26 raw per window, 2.8 planned: 40 windows = 90 raw, 112 planned. Adding skip5 and coin at 0.44 of hold+spend: 161 planned for four channels. Pilot window: 2.8 CPU-h.
- **Companion (R4-free, not one of the four ideas).** The library stride scan without R4 on kscreen costs about 9 s per window and multiplier (`multipliers` row: 35 min for 8 windows x 28 multipliers), so mults 1 and 28 on 40 windows is about 6 CPU-min. It checks the window set and the flags before the R4 run. It cannot show anything about R4 keys.
- **Controls.** Positive: the phase 57 R4 plants (12 of 12 at n150 and n300; band minimum 57.9 and 119.5 nats) and the phase 51 interior plants (48 of 48 in the pilot). They are random windows, so they are valid stride-window controls once the window start is at a stride point (the plant design already restarts the key at the window). Null: matched iid-key plant per window (phase 57 null max -18.0 at n150, -55.8 at n300) and 50 random library streams of the same length (08 section 4 C).
- **What it adds.** No registry row covers any library window except the section starts (`lib-sections`: first 300 runes of the 8 sections; `multipliers` and `open-clause-windows` also section or clause starts only). The gap column of those rows says "windows other than the section starts". So idea 11 is a window-set gap, not only an R4 gap: the R4-free stride scan would be new too. `keywords-r4` covers stride windows, but for keywords only.
- **Depends on.** s01; word-flag fix (section 2.5); library export.
- **Priority: medium.** It is the largest part of the library window set that has never been run. The cost (112 CPU-h planned) means: run the R4-free companion and the pilot window first, then the other 39.

### Idea 12. R4 coin and skip5 channels for keywords, number strings and MB files

- **What runs.** The two channels that `keywords-r4`, `p60-numkeys-r4` and `p60-blobs-r4` did not run (they ran hold and spend only):
  - keywords: the 1,940 phase 59 keywords x 48 windows, both signs, every phase;
  - number strings: the 70 keys of phase 60 T2 (50 number keys and 20 onion-string keys) x 48 windows;
  - MB files: the 8 streams of phase 60 T6 (560.17 and _560.00, bytes mod 29 and rejection, forwards and backwards), 19.7 M offsets in total, window 0.7@0 first (the one window that ran), then the other 7 section starts.
- **Proposed command (not written).** `python -B work/r4fix/s09_skip_coin_r4.py run --family keywords,numkeys,mb --channels skip5,coin --windows sec-starts`.
- **Prerequisite.** A written R4 rule for the skip5 and coin channels (section 2.6). Without it there are no plants and no positive control for these channels.
- **Cells.** MB, one window: 19.7 M offsets x 2 signs x 2 channels = 79 M cells. Keywords and number strings: periodic keys, so cells are per phase; use the measured costs.
- **CPU-h (incremental, skip5 + coin only).**

| family | hold+spend measured | skip5+coin central (0.44x) | upper (1.0x) |
|---|---|---|---|
| keywords, 48 windows | 4.44 h (phase 59) | 2.0 h | 4.4 h |
| number strings and onion strings, 48 windows | 0.21 h (0.12 + 0.09, phase 60 T2) | 0.09 h | 0.21 h |
| MB files, window 0.7@0 | 3.56 h (phase 60 T6) | 1.6 h | 3.6 h |
| MB files, 8 section starts | about 28 h (phase 60 T6) | 12.4 h | 28 h |

  Total: about 3.7 h for one MB window (8.2 upper); about 14.5 h for all eight MB windows (32.6 upper).
- **Controls.** Positive: the existing R4 plants of each family, regenerated for skip5 and coin: 44 keyword plants (phase 59; recovered at 113.8+ nats, T300 29.8), 32 + 24 number-string plants (phase 60 T2; true scores 113-183), 8 MB plants (phase 60 T6; 106.6-168.7 nats). Null: wrong keys (keyword max 25.4; number keys 24.9, with the MB decoy aliases up to 119), random keys (-45.8; -37 / -74; -65), iid-key plants (-93.5; -96 / -84; -72).
- **What it adds.** The keyword, number and MB negatives under R4 cover hold and spend only. Library coverage of all four channels exists for two windows (phase 51 at 0.7@0, phase 57 at 0.15@0). Adds skip5 and coin for the number families.
- **Depends on.** s01; the plant rule (section 2.6).
- **Priority: low.** CPU is small (about 4 h for keywords, under 0.5 h for numbers), but the plant rule must be written first and the prior is low; the hold/spend negatives on the same keys already carry most of the weight.

### Idea 13. R4 x page starts (46) and clause starts (82) with about 60 Cicada-named streams

- **What runs.** 128 restart windows: 46 page starts (`data/pages.txt`; 12,956 / 46 = 282 runes on average if the pages tile LP2) and 82 clause windows (61-559 runes; I assumed an average of 150, which is the main uncertainty). About 60 named streams (list in `08` section 4 C: primes, totient, pi(n), n, n^2, Fibonacci, base-29 digits of pi, e, phi, sqrt 2, sqrt 3, ln 2, the 20 streams of `layer2 periodic_core20`, the 1033 / 3301 families, hash chains of "An End", "welcome", "instar", the PGP key id). Hold and spend, both signs, every offset. Window length = page or clause length (capped at 300 for pages). Hit rule as idea 10.
- **Proposed command (not written).** `python -B work/r4fix/s09_restart_r4.py run --starts pages,clauses --streams named60 --channels hold,spend --workers 14`.
- **Named-stream list.** Not in the repository as a file. Build it from `library.ksb` names where a stream is already in the library; do not regenerate streams. Exclude the megabyte files (below).
- **Cells.** 60 streams x 9,264 offsets (library average, n150, 13.33 M / 1,439) = 556 K offsets per window; x 4 cells x 128 windows = 285 M cells.
- **CPU-h.** Sum over windows of n_w = 12,972 (pages) + 12,300 (clauses) = 25,272 rune-windows. CPU = 556 K x 4 x 0.52 us x 25,272 = 29,200 s = 8.1 CPU-h raw, 10 planned. If clause windows average 300 runes instead of 150, 12 raw, 15 planned.
- **Controls.** Positive: the phase 57 R4 plants already restart the key at the window start (12 of 12 recovered); select the window's first word at a page or clause start for the control set, and reuse the phase 51 restart control (24 of 24 at n of 150 or more; 08 section 4 C). Null: matched iid-key plant per window (phase 57 null max -18.0 at n150, -55.8 at n300) and 50 random library streams of the same lengths.
- **What it adds.** `restart-library` (kscreen, R4-free, 46 page starts with the library: pages best 1.679, the short page windows read as chance) and `open-clause-windows` (R4-free, 82 clause windows, four channels, 1,439 streams: 0 tier-1 cells) already cover restarts without insertions on the full library. Idea 13 adds R4-tolerant restarts for the named subset only.
- **Excluded from this idea: the megabyte files.** Each MB stream has 19.7 M offsets; at this window set that is about 290 CPU-h per stream (19.7 M x 4 x 0.52 us x 25,272 = 1.04 M s). The periodic streams (primes, keyword-like sequences) cost per phase, not per offset, so the library average does not apply to them; measure them before adding.
- **Depends on.** s01; the named-stream list; word-start flags at page and clause starts (section 2.5).
- **Priority: medium, first of the four.** Cheapest (about 10 CPU-h), reuses the phase 57 generator unchanged, and the named streams are the candidates most likely to match an author's choice, even though each is still a low prior.

## 4. Table

| idea | command (proposed, not written) | cells | CPU-h | controls | depends on | priority |
|---|---|---|---|---|---|---|
| 10 | `s09_mult_r4.py run --sec 15 --start 0 --n 150 --channels hold --maps 2-14` (pilot); then n300 hold,spend per window | 347 M (pilot); 682 M per n300 window | 7.2 pilot; 36 per window; about 290 for 8 windows | 13 new R4 plants (one per map); mult-1 decoder must fail on m-plants; matched iid-key null (-18.0 / -55.8); 50 random keys | s01, s02, library export | low |
| 11 | `s09_stride_lib.py run --windows stride --channels hold,spend` (pilot 0.13@300 first; R4-free companion about 6 CPU-min) | 2.10 G (40 windows x 52.4 M) | 112 planned (90 raw); 161 with four channels; pilot 2.8 | phase 57 (12/12) and phase 51 (48/48) plants at stride starts; matched iid null (-18.0 / -55.8); 50 random keys | s01, word-flag fix, library export | medium (gap; run pilot first) |
| 12 | `s09_skip_coin_r4.py run --family keywords,numkeys,mb --channels skip5,coin` | 79 M (MB, one window); keyword and number cells per phase | about 3.7 for one MB window (8.2 upper); about 14.5 for all eight (32.6 upper) | regenerated R4 plants: 44 keyword, 56 number, 8 MB (113.8+, 113-183, 106.6-168.7 nats); wrong-key max 25.4 / 24.9; iid nulls -93.5 / -96 / -72 | s01, skip5/coin R4 rule (not yet written) | low |
| 13 | `s09_restart_r4.py run --starts pages,clauses --streams named60 --channels hold,spend` | 285 M (128 windows x 60 streams x 4 cells x 9,264 offsets) | 8.1 raw, 10 planned (12-15 if clauses average 300) | phase 57 plants restarted at page/clause starts (12/12); phase 51 restart control (24/24, n of 150+); matched iid null per window; 50 random keys | s01, named-60 list, word-flag check | medium (cheapest) |

Suggested order if s01 finds the arc sees edge nulls: idea 13 (10 h); the R4-free stride companion (6 CPU-min) and idea 11 pilot window (2.8 h); idea 10 pilot (7 h); then idea 11 in full (112 h); idea 12 last, after its plant rule is written. If s01 finds the arc blind, none of these runs before a union arc is built and gated (08 section 4 A).

## 5. Findings that change the plan

1. **Idea 13's cost in `11_next_100.md` is wrong by 3-4x.** It says 2-5 CPU-h. The 08 inputs ("60 streams x about 0.5 M offsets x 2 signs x 128 windows") give 320 CPU-h at the measured cost. With the library-average stream length (9,264 offsets) it is 8-10 CPU-h. The 0.5 M figure needs the real stream lengths; check them before the run, and correct the number in the idea and in `08`.
2. **Lead 12's "3x" is not reproduced.** From the brief's timings, skip5 and coin add about 0.44 of the hold+spend cost (1.44x in total); the record does not measure the channels separately. Measure one stream per channel (a short run, not done here) before costing idea 12 further.
3. **The mid arc's window flags.** `lp_pilot_mid.py` forces the first word-start flag to 1. Affects any stride window cut inside a word (idea 11). Expected small; check it with a control that cuts a plant at a mid-word point.
4. **R4 plants exist for hold and spend only.** `make_r4` (phase 57) has no skip5 or coin path, and `plant_edge.py`'s skip and coin steps have no R4 repair. Any R4 claim about those channels has no positive control yet.
5. **Ideas 10, 11 and 13 are window-set gaps as well as R4 gaps.** The library has been run under every key model on the section starts only (`lib-sections`, `multipliers`, `open-clause-windows` and the R4 pilots), so R4 on the stride windows adds windows the record has never had. The R4-free stride scan is cheap (about 6 CPU-min) and should come first.
6. **Periodic keys do not follow the cell model** (section 1): their cost is about 2.7 ms per cell against 0.155 ms for a long stream. Use the measured keyword cost (4.44 h).

## 6. What was not checked

- The named-stream list for idea 13 (not in the repository as a file); the stream lengths; the clause-window lengths (only the 61-559 range is recorded, I assumed 150 on average).
- The page lengths (only the mean, 282, from 12,956 / 46, assuming the pages tile LP2).
- The per-channel timing (section 1, the 0.44 factor). It is inferred from the brief's two figures; no record measures hold, spend, skip5 and coin separately.
- Whether `jobs/queues/r4lib.txt` has run (08 says it is queued; I did not check `results/`).
- The contents of `work/r4fix/s01_edge_plants.py` and `s02_slot_rules.py`, and any definition of s03 or s08.
- Cost of a union arc (not measured).

## 7. Files and CPU

- Written: this file only (`work/log/r4fix_s09_scope.md`). No code, no results directory, no change to any registry, queue, PLAN, STATUS, README or docs file.
- CPU used: none. Reads and arithmetic only.
