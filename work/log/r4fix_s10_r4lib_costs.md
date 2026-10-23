# R4 repair session s10: the queued r4lib, the coverage bound, a decision table and a full-pass cost table (2026-10-23)

Nothing in LP2 is solved. Scope: ideas 4 and 15 of `work/laptop_review/11_next_100.md`. Reading and arithmetic only: no engine, simulation or queue was run, `jobs/queues/` was read and not changed, nothing was committed. The one computation beyond reading was a read-only parse of the LP2 transcript (word lengths, a few seconds). Status of r4lib is from files only.

## 0. Answers in short

- **Idea 4 (should r4lib wait until the decoder is shown to see R4 as fitted?).** Its cost is small: 15.6 CPU-h on the cost model (19.6 with the queue's own planning figure), about 1.1-1.4 h of wall time on 14 workers. The queue cannot reach it before the desktop's pdir, layout and wordjump jobs (section 1), which leaves time for session s01's number to land. Its negative says nothing about R4 until that number is known. Recommendation, not acted on: keep it queued, apply the table in section 3 when s01's summary exists, and hold it only if s01's n300 `any`-mode detection is below 50%.
- **The bound the brief asked for.** Under the brief's all-or-nothing premise (a window is seen only if it has no edge null), an interior-only decoder would cover about 0.03-0.13% of 150-rune windows and about 0.00001-0.0002% of 300-rune windows (section 2.2). I think that premise is too strict: a misplaced edge null should cost the decoder a rune or two, not the window (section 2.3). So the bound is a worst case, not an estimate; s01's `any`-mode detection replaces it.
- **Idea 15 (cost/benefit of a full R4 library pass).** Section 4. Hold/spend costs 2.2-2.8 CPU-h per n300 window; four channels cost 43% more and are not part of R4 as fitted.

## 1. What r4lib runs now

Source: `jobs/queues/r4lib.txt` (read only), `docs/QUEUE.md` (2026-10-22 section), `scripts/restart_queues.ps1`, `work/chanscreen/v2/step4/lp_pilot_mid.py`.

**Windows.** Seven n300 windows at the start of sections (`--sec`, `--start 0`, `--n 300`). Section lengths from the transcription (`work/lp.py` `load_segments()`, read-only):

| window | section runes | status (files only) |
|---|---|---|
| 0.8 @ 0 | 1,145 | pending |
| 0.9 @ 0 | 1,729 | pending |
| 0.11 @ 0 | 1,894 | pending |
| 0.12 @ 0 | 1,021 | pending |
| 0.13 @ 0 | 1,524 | pending |
| 0.14 @ 0 | 1,589 | pending |
| 0.15 @ 0 | 3,316 | pending |

Not in r4lib: 0.7 @ 0 (phase 51 pilot already ran it with all four channels, no hit), 0.10 (9 runes, no n300 window). Phase 57 also ran 0.15 @ 0 with n150 and four channels (no hit); r4lib's 0.15 @ 0 is n300.

**Channels and cells.** hold and spend, both signs, every offset of the full library (1,439 number streams). The phase 51 four-channel count is 106,626,192 cells, so 13,328,274 offsets per sign; hold plus spend gives 53,313,096 cells per window.

**Decoder.** Mid-word arc (`lp_pilot_mid.py`, kind 3), interior null slots only (cipher positions 1..Lc-2), nu 0.42, frozen T300 = 29.80. Hit rule: S_guard >= 29.80, then `work/kscreen/verify.py`. T300 was set in phase 51 against four-channel windows of about 107 M cells (the null scan); hold plus spend has half as many cells, so the threshold is no looser for r4lib.

**CPU.** Per-offset costs measured for n300 (phase 51, G6; microseconds per offset per sign): hold 151, spend 150, skip5 59, coin 72.
- Model: 13,328,274 offsets x 2 signs x (151 + 150) us = 8,025 CPU-s = **2.23 CPU-h per window**; seven windows = **15.6 CPU-h**.
- Cross-check: phase 57's four-channel LP2 pilot took 1.61 CPU-h at n150; scaled to n300 (cost linear in n, assumed) that is 3.22 CPU-h for four channels, and 3.22 x 301/432 = 2.24 CPU-h for hold plus spend. The model agrees.
- The queue header plans **2.8 CPU-h per window**, so **19.6 CPU-h** for seven (about 25% above the model; the phase 51 pilot's wall-clock figure was about 4 CPU-h for four channels, against 3.2 modelled).
- Wall time on 14 workers, if the run had the machine alone: 15.6/14 = 1.1 h to 19.6/14 = 1.4 h.

**Machine.** The desktop. `scripts/restart_queues.ps1` lists r4lib among the five desktop queues (with booknight, pdir, layout, wordjump), `docs/QUEUE.md` describes it in the desktop queue table, and `docs/SESSION_LOG.md` states that overnight work happens on the desktop. The queue file and commit ec2380c carry no machine name. One caveat: commit 9f72af4 adds `jobs/queues/pdir_laptop.txt` ("pdir stage 1 for the LAPTOP ... the desktop's pdir queue is stopped once this one runs"), so pdir may run on the laptop instead. If it does not run on the desktop, r4lib's WAIT gates for pdir, layout and wordjump pass after about two minutes each (the gate is "no python process whose command line contains the text").

**Status: pending.** Files checked:
- no `results/overnight/desktop/queue/r4lib.tsv` and no `r4lib__*.log`;
- no `results/chanscreen/mid_lp_s<sec>_0_n300_hold-spend/` folder and no `mid_lp_s*_summary.txt`;
- `booknight.tsv` ends with QUEUE_DONE (2026-10-23 13:13), so the first WAIT gates are passed;
- no `pdir.tsv`, `layout.tsv` or `wordjump.tsv` in the desktop queue folder, so the chain on the desktop has not started (per `docs/QUEUE.md`, pdir is about 24 h at 14 threads, layout about 3 h, wordjump about 1 h).

Results of r4lib in `results/`: none. Existing mid-arc results are phase 51 (`results/chanscreen/mid_lp_pilot/`, `mid_lp_pilot_summary.txt`) and phase 57 (`results/chanscreen/phase57_*`).

## 2. Coverage arithmetic

### 2.1 Inputs

- LP2 word lengths, read from `work/ref/lp_verified.txt` through `work/lp.py` `load_segments()`, sections 0.7-0.15 (as `work/chanscreen/v2/step4/lp_mask.py`; words split at ' ', '.' and '&'; line and page marks transparent). Result: 12,947 runes (plus 9 in 0.10 = 12,956), **2,894 words**, mean word length **4.474** (the logged 4.47 agrees). The brief says 2,896 words; I did not chase the difference of two, which changes no number here.
- Single-rune words: 2.87%. Multi-rune words: 2,811, i.e. **0.2171 per rune**.
- Edge share e. Under the R4 fit the null slot is uniform over 0..L (`work/phase57_mechanism.py:77`, `work/r4fix/s01_edge_plants.py` mode `any`), so a null in a word of length L is at an edge with probability 2/(L+1). Weighting by LP2's multi-rune word counts gives **e = 0.414**, the low end of the brief's 0.41-0.49 range. I use e = 0.41, 0.45, 0.49.
- nu = 0.45 nulls per multi-rune word (the R4 fit's rate is 0.448).
- Multi-rune words per window: K = 0.2171 n, so **K = 32.6 (n = 150)** and **K = 65.1 (n = 300)**. Assumption: the average density holds for any window; partial words at a window's cut edges are counted as full words (error about one word).

### 2.2 The bound (brief's premise)

Premise: the decoder sees R4 in a window only if no null in the window sits at a word edge. Words are independent, and a multi-rune word has an edge null with probability nu x e, so

P(no edge null in window) = (1 - nu e)^K.

| e | P(edge null) per multi-rune word | expected edge nulls per window, n150 / n300 | P(no edge null), n150 | P(no edge null), n300 |
|---|---|---|---|---|
| 0.41 | 0.185 | 6.0 / 12.0 | 1.3 x 10^-3 (0.13%) | 1.7 x 10^-6 |
| 0.45 | 0.203 | 6.6 / 13.2 | 6.3 x 10^-4 (0.06%) | 4.0 x 10^-7 |
| 0.49 | 0.221 | 7.2 / 14.4 | 3.0 x 10^-4 (0.03%) | 9.0 x 10^-8 |

A Poisson approximation exp(-K nu e) gives values 2-4 times higher at n150 and 3-5 times higher at n300; the product form is shown. **This is a bound, to be replaced by session s01's measured detection rate.** Under the premise, every R4 test with an interior-only decoder (r4lib, phase 51's 0.7 @ 0, phase 57's 0.15 @ 0) would cover almost no R4-as-fitted window, and their negatives would say almost nothing about R4.

### 2.3 Why the premise is probably too strict (reasoning and one measured scale; not measured for this decoder)

(a) The decoder's own path. Per phase 51 (`work/log/phase51_midword_channel.md` section 2), a word of cipher length Lc >= 3 may carry one null at an interior position t in 1..Lc-2, with weight nu/(Lc-2) and emission 1/29, and the key pointer advances once per real rune (hold and spend). Take an R4 word of L plaintext runes with its null at the END (cipher length Lc = L+1). The decoder can place its null at t = Lc-2 instead. Then the real runes consume L key values, the same as the truth, so the next word stays aligned. The cost is one lost plaintext rune (the true last rune is read as the null) and one garbled decode (the true null read as a real rune). A null at the START of a word is absorbed at t = 1 at a cost of about two runes. So an edge null should cost the decoder about one or two runes locally, not the rest of the window.

(b) A measured scale for the reverse mismatch. Phase 51 G7 (`work/log/phase51_midword_channel.md`, section 6): the edge arc decoders (`nullf`, which can only place nulls at word edges) still detect 44 of 48 mid-word-null plants, with median band 74 nats, against 149 for the mid decoder. That is a decoder meeting nulls it cannot place, and it loses about half its band, roughly 3 nats per misplaced null over about 26 nulls per window. Applied to R4 windows: about 12 edge nulls per 300 runes would take about 36 nats off the phase 57 R4 band minimum of 119.5 (n300), leaving about 80, against T300 = 29.8. At n150, about 6 misplaced nulls take about 18 nats off the phase 57 median of 73.6 (n150, threshold not calibrated), leaving about 55.

(c) Reading: under (a) and (b) the interior-only decoder should still detect most R4-as-fitted windows, and the bound in 2.2 is a worst case. Whether that holds is exactly what s01's `any`-mode plants measure (mode `any` = slot uniform over 0..L, the R4 fit; `edge` = slot 0 or L only, as a stress test). This is a prediction, not a result.

### 2.4 Which results the bound touches

- r4lib (n300, seven windows, hold and spend, interior decoder): as in section 1.
- phase 51 pilot (0.7 @ 0, n300, four channels): the same decoder, no R4-specific hit; `work/log/phase51_midword_channel.md` section 8.
- phase 57 pilot (0.15 @ 0, n150, four channels): `results/analysis/phase57_pilot.txt`, max S_guard -4.88.

## 3. Decision table for r4lib

Input d = session s01's detection rate in `any` mode at n300 (the n that r4lib uses). s01's summary was not written when I looked: `results/r4fix/s01_edge_plants/` held partial per-plant JSON files only. I did not read the partial files, so d is not known here.

| s01 `any`-mode detection d (n300) | what to do with r4lib | CPU-h for the seven windows | what the negative means |
|---|---|---|---|
| d >= 90% | keep as queued | spend 15.6 (model) to 19.6 (queue planning); saved 0; about 1.1-1.4 h wall | a real negative for R4 as fitted, at power d |
| 50% <= d < 90% | run as queued, label the result "interior-only decoder, R4 `any` detection d = X%" | spend the same; saved 0 | excludes only about d of the R4-as-fitted windows |
| d < 50% | hold it (behind a union arc, or dropped as an R4 test) | saved now: 15.6-19.6; a union-arc run of the same seven windows later costs about 18.7-29.4 (factor 1.2-1.5 on the model or planning figure, section 4) | as it stands, it would exclude almost nothing about R4 |

The row that matters is the first: with the premise corrected by 2.3, the expected outcome is d >= 90%. The CPU saved by holding is small (about 1 h of wall time); the real cost of running it uninformatively is that the result would be quoted as an R4 negative.

**Answer to idea 4.** r4lib should not be held for the queue's sake: its CPU is small, the desktop chain reaches it only after about a day, and s01 can finish first. What should wait is the claim. Record the result with s01's d attached, and hold the run only on d < 50%.

## 4. Cost/benefit table of a full R4 library pass

Basis: model 2.23 CPU-h per n300 window for hold plus spend (section 1); queue planning 2.8; four channels 3.20 (model) and 4.0 (queue scale, 3.20 x 1.25). The union-arc factor 1.2-1.5 times the mid arc is an **assumption**, not measured: phase 24 measured the edge arc at 250 us per offset per sign for four channels against 432 us for the mid arc (`work/log/phase51_midword_channel.md` section 6), so a union arc with both null sites could cost more or less than that range.

| scope | channels | arc | CPU-h (model) | CPU-h (queue planning) | wall h on 14 workers (model) | what it buys |
|---|---|---|---|---|---|---|
| 7 windows (r4lib) | hold, spend | mid (interior) | 15.6 | 19.6 | 1.1-1.4 | the library under R4 at the seven untested section starts; interior-only detection |
| 48 windows (the phase 59-60 set) | hold, spend | mid | 107 | 134 | 7.6-9.6 | every n300 start of every section of 300+ runes, interior-only |
| 48 windows | four | mid | 154 | 192 | 11-14 | as above plus skip5 and coin (not part of R4 as fitted) |
| 82 windows (the chanscreen set) | hold, spend | mid | 183 | 230 | 13-16 | the full set, interior-only |
| 82 windows | four | mid | 262 | 328 | 19-23 | as above plus skip5 and coin |
| 48 windows | hold, spend | union, x1.2-1.5 (assumed) | 128-161 | 161-202 | 9.2-11.5 | R4 with nulls at any slot (the R4 fit), if the union arc passes its gates |
| 82 windows | hold, spend | union, x1.2-1.5 (assumed) | 219-274 | 276-344 | 15.7-19.6 | the full set with the R4 fit's any-slot nulls |
| 82 windows | four | union, x1.2-1.5 (assumed) | 315-394 | not stated | 22-28 | the most complete; the least likely to be needed |

Notes:
- Hold and spend versus four channels: skip5 and coin add 43% (432 / 301 us per offset). The R4 plants (`work/phase57_pilot.py`) and the R4 simulation (`work/phase57_mechanism.py`) use only the hold and spend key rules, so the extra channels buy nothing for R4 as fitted. Keep hold and spend for R4; spend the rest only on other key families.
- Windows already scanned under the mid arc: 0.7 @ 0 (phase 51, four channels, n300), 0.15 @ 0 (phase 57, four channels, n150), and the keyword scan of phase 59 (48 windows, hold and spend, keyword keys, not the library: 4.44 CPU-h measured, not comparable per window).
- The 82-window set is the chanscreen campaign set (`docs/QUEUE.md`, `work/log/phase51_midword_channel.md` section 6); the 48-window set is the phase 59 set. Neither count was re-derived here.
- A full R4 pass is not expensive in CPU terms (13-16 wall hours on 14 workers for the mid arc, hold and spend, 82 windows). Its cost is the decoder work (the union arc's gates), not the CPU.

## 5. Recommendation (not acted on; the owner decides)

1. Keep r4lib as queued. Do not edit `jobs/queues/`.
2. Read s01's `any`-mode summary (n300) before the desktop reaches r4lib. Apply the table in section 3. Attach s01's d to any r4lib result.
3. Expect the d >= 90% row (section 2.3). If it holds, r4lib stands as an R4 test, and the earlier interior-only negatives (phase 51, phase 57) should be re-described as R4 tests at the same power.
4. Before any full R4 pass (section 4), decide whether a union arc is worth building. Its cost factor is unmeasured.
5. Settle which PC runs pdir. If the desktop's pdir, layout and wordjump are not running, r4lib's WAIT gates pass within minutes of launch and r4lib starts at once, not after about a day.

## 6. Files and CPU

- Written: this log only (`work/log/r4fix_s10_r4lib_costs.md`).
- Read: `work/r4fix/00_brief.md`, `work/laptop_review/11_next_100.md` (ideas 4 and 15), `jobs/queues/r4lib.txt`, `jobs/queues/pdir_laptop.txt`, `docs/QUEUE.md`, `docs/CAMPAIGNS.md`, `docs/SESSION_LOG.md`, `scripts/restart_queues.ps1`, `work/phase57_pilot.py`, `work/phase57_mechanism.py`, `work/chanscreen/v2/step4/lp_pilot_mid.py`, `work/chanscreen/v2/step4/plant_mid.py`, `work/chanscreen/v2/step4/lp_mask.py`, `work/lp.py`, `results/analysis/phase57_pilot.txt`, `work/log/phase51_midword_channel.md`, `work/log/phase57_mechanism.md`, `work/log/phase58_djubei_reuse.md`, `work/log/phase59_keywords_r4.md`, `work/log/phase60_clue_review.md`, the desktop queue state files (`results/overnight/desktop/queue/*.tsv`, listing only), and the git log for ec2380c, 9f72af4 and the r4lib history.
- Not read: partial outputs of s01 and s02 under `results/r4fix/` (the s01 summary is pending).
- Not done: no engine, simulation or queue; no registry, PLAN, STATUS or FINDINGS edits; no commit.
- CPU: one read-only parse of the LP2 transcript (seconds).
