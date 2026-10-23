# R4 repair s08: a union null arc (null at any cipher slot 0..Lc-1 of a word) for chanscreen v2 (2026-10-23)

Nothing in LP2 is solved. Build and gate only: no LP2 ciphertext is scored (LP2 word LENGTHS are read to lay out the plants, as in every earlier plant).

## Question
R4 as fitted draws its one null per word from slots 0..L of the L+1 cipher runes, word edges included. The mid arc (kind 3) only allows interior cipher positions 1..Lc-2.
Build the decoder that covers R4 as fitted (the "union arc") and gate it like the mid arc.

## Semantic decisions (written BEFORE any code)
Per word of cipher length Lc (word starts = the `wstart` flags, position 0 always starts a word; Lc = number of cipher runes up to the next start):
1. **Placement.** Lc >= 2: with probability nu the word carries ONE keyless null at cipher position t in 0..Lc-1, probability nu/Lc each (t = 0: before the first real rune of the word,
   t = Lc-1: after the last one); with probability 1-nu none. Weights sum to 1 per word: (1-nu) + Lc * nu/Lc.
2. **Lc = 1: no null, weight 1.** A one-rune cipher word is a one-rune plaintext word (R4 gives nulls only to multi-rune plaintext words, `r4sim` `min_word` 2), so it cannot carry a null.
   (A null-only "word" does not exist in R4.) Consequence: Lc = 2 does carry a null slot in the decoder although R4 would only produce Lc >= 3 for a null-carrying 2-rune plaintext word; a cipher
   word of length 2 is a plaintext word of length 2 with no null in R4. The decoder follows the brief (Lc >= 2) and so gives Lc = 2 words a null probability nu that R4 never produces; this is a mild
   mis-specification of the prior (not measured separately; the plants below include 2-rune words and are still detected).
3. **Everything else as the mid arc (kind 3):** the null is emitted uniformly (1/Q), consumes NO key value, is invisible to the anti-repeat rule (the next real rune is compared with the last
   REAL cipher rune, even across a word gap) and to the language model (the LM conditions on the last REAL plaintext); channels hold / spend / skip5 / coin with the same edge weights; mask =
   word-start flags only; uncapped skip unsupported. Words are independent in the prior, so the window likelihood is a path sum with per-word weights (no per-position nu).
4. **Nulls at consecutive positions.** A null at the last position of word A and one at the first position of word B are two adjacent nulls (still at most one per word). The real rune after both is
   compared with the real rune before both. This is what the mid arc could not meet (its nulls are interior, so never adjacent).
5. **Window edges.** The window's first word starts at position 0 (as the mid arc). Unlike the mid arc (null never before window position 0 / "no event before position 0") the union arc ALLOWS a null at
   position 0 of the window when the first word has Lc >= 2: position 0 is then a null, c[1] is the first real rune with key[o] (no anti-repeat comparison, language model starts from pi). This is the
   same semantics the dense reference gives for free. The cut first / last words of a window are treated as complete words (as mid).
6. **Restricted placements** (for the reduction gate): `place` = 0 any slot 0..Lc-1 (weight nu/Lc, Lc >= 2); 1 interior slots 1..Lc-2 (nu/(Lc-2), Lc >= 3, else weight 1) = the mid arc;
   2 edge slots {0, Lc-1} (nu/2 each, Lc >= 2; distinct slots) as a diagnostic. nu = 0 gives the base engine.

## State machine
State before position i: (u, d): u = a null already used in the current word; d = number of trailing nulls (0, 1, 2; 2 only as end-of-word-A null + start-of-word-B null).
Five states A=(0,0), B=(1,0), C=(1,1), D=(0,1), E=(1,2) (mid had S0, S1, S2 = A, B, C). Real rune at i: next state A (word ends or u = 0) or B; weight ln(1-nu) when it is the last position of
a word with a slot set and u = 0. Null at i (u = 0, slot allowed): weight nu/|slots| / Q; A -> C (word continues) or D (null at the last position, a new word follows); D -> E.
Class sets (previous-plaintext candidates: the ordinary class plus the collision class of the real rune before the last real one) have up to 4 values (ordinary + c[t-1], c[t-2], c[t-3] where the
runs of nulls allow it), against 3 in mid.

## Method
Files: `work/r4fix/s08_backward_union.rs` (the DLL; it includes `work/chanscreen/v2/backward_edge.rs` verbatim for its helpers), `s08_engine_union.py` (ctypes adapter
`all_offsets_union(c, key, sign, q, ch, pi, L, nu, wstart, place='any')`, same output as `all_offsets_mid`), `s08_reference_union.py` (dense reference; the event tree `prob_nulls` is imported read-only
from `work/chanscreen/v2/reference_mid.py`, the placement enumeration is new), `s08_test_union.py` (G1-G3, cost), `s08_power_union.py` (G4).
Build: `rustc --crate-type cdylib -O work/r4fix/s08_backward_union.rs -o work/r4fix/build/backward_union.dll` (rustc 1.87; .pdb/.exp deleted; no existing DLL was rebuilt or overwritten).
Run: `python -B work/r4fix/s08_test_union.py` (G1-G3), `... cost`, `python -B work/r4fix/s08_power_union.py run --workers 2` then `summary`. Test RNG seeds: G1 7 / 10 / 12 / 8 / 9, G2 21, G3 11 (in the code).
Plants (G4): `work/r4fix/r4sim.py` with `slots='any'`; its own tests pass (`python -B work/r4fix/test_r4sim.py`: 12 tests OK in 53 s, run here; `results/r4fix/s08_union_arc/r4sim_tests.txt`).
Plant parameters: nu 0.45 of multi-rune words, one null, slot uniform 0..L, null value uniform and never equal to its left neighbour (`null_check` left), visible to the anti-repeat rule (`null_visible` True),
repair writes T(c[-6]) = 24 - 2c in the same word (`lag_basis` cipher) at q from `frozen.json` (about 0.81), channel hold (`m04`) or spend, library stream at a random offset, sign + / - alternating, held
plaintext (3 Cicada + 3 English per channel) cut at LP2 word lengths of a random section (plaintext length = the LP2 word length, as phase 57 and s01), seeds `sha256("r4fix-s08|ch|src|idx")`, 12 plants.
Decoder: union arc (place 'any') and mid arc (kind 3), both nu 0.42, word-start flags only, hold / spend / skip5 / coin, both signs, every offset of the planted stream; the window is 300 cipher runes from the
first real rune at or after item e0 (0..99), n 150 is its prefix; threshold T300 = 29.80 (frozen for n 300 and used at n 150, as in phases 51/57/s01). Null control: a matched plant (index + 1000, iid random key,
its own words and layout) searched in the true plant's stream with the union arc. 2 worker processes at below-normal priority.

## Gates
**G1 (fast vs dense reference, Fractions): PASSED.** Worst absolute error in log likelihood (L and U columns) **3.6e-15**, tolerance 1e-12; zero-support cells match exactly.
| set | trials | non-zero cells | worst error |
|---|---|---|---|
| place any, Q 3-4, n <= 7, key <= 8, word starts at 25% / 50% | 400 (100 per channel, 200 per sign) | 1,884 | 3.6e-15 |
| place any, words of 2-3 runes (starts at 40% / 50%), n <= 8 | 300 | 1,306 | 3.6e-15 |
| place any, Q = 6, n <= 6 | 80 | 308 | 1.8e-15 |
| place interior (the mid arc's placement) | 200 | 850 | 3.6e-15 |
| place edge only | 200 | 924 | 3.6e-15 |

q in {0, .6, .8, 1}, nu in {0, .33, .4, 1}. Of the 400 + 300 any-placement trials 139 had a pair of adjacent words that both carry a slot (so the adjacent-null states D and E are reachable), 357 had a first word of >= 2 runes
(null at window position 0 possible), 503 had a one-rune word. Limit: reference and engine share one author's reading of the channel; Q = 29 was not checked against the dense reference (too slow in Fractions);
the real-model Q = 29 checks are the engine-to-engine G2 comparisons below.
Sensitivity of the gate (hand-made Rust mutants in scratch, not kept): disabling the second class hop (a run of two adjacent nulls), disabling the null at window position 0, and routing D -> E to the wrong state are each
caught by the dense-word set (first failing trial 188, 0 and 107 of 300). The plain 400-trial "any" set caught the second-hop mutant only at trial 352, which is why the dense-word set was added.

**G2 (reductions, real 29-rune model, 240 random windows n <= 40, key <= 30, four channels, both signs, q in {0,.6,.81,1}, nu in {.1,.42,.9}): PASSED, bit-equal.**
- place interior vs `backward_mid` kind 3: 2,666 finite cells, max |diff| 0.0 (support identical).
- nu = 0 vs the base engine (`engine.all_offsets`, backward.dll) for place any / interior / edge: 6,714 finite cells, max |diff| 0.0 (support identical).

**G3 (mutant witnesses, 250 random small cases, Q 3, nu 0.4, q 0.8): PASSED.** The engine disagrees with the dense reference under each wrong reading: null visible to the anti-repeat rule in **105** / 250 cases,
null consumes a key value **117**, mid-arc (interior) weights used where "any" is meant **107**, unnormalised weights (nu per slot) **117**.

**G4 (R4 plants with the null slot 0..L, 12 plants = 6 hold + 6 spend, T300 = 29.80; `results/r4fix/s08_union_arc/g4_summary.txt`): PASSED.** Edge nulls are 44% (n 150: 71 of 163) and 41% (n 300: 137 of 332) of the nulls in the windows.
| n | channel | decoder | detected | true within 3 nats of best | band min / median / max | matched iid-key null max (union) |
|---|---|---|---|---|---|---|
| 150 | hold | union | **6/6** | 6/6 | 55.7 / 72.1 / 77.2 | -15.8 (0/6 >= T300) |
| 150 | hold | mid | 6/6 | 6/6 | 52.3 / 69.0 / 72.7 | |
| 150 | spend | union | **6/6** | 6/6 | 43.5 / 54.7 / 99.4 | -17.1 (0/6) |
| 150 | spend | mid | 6/6 | 5/6 | 31.7 / 58.9 / 95.1 | |
| 300 | hold | union | **6/6** | 6/6 | 113.2 / 147.4 / 156.7 | -63.9 (0/6) |
| 300 | hold | mid | 6/6 | 6/6 | 76.8 / 138.2 / 147.4 | |
| 300 | spend | union | **6/6** | 6/6 | 79.9 / 124.6 / 165.4 | -57.0 (0/6) |
| 300 | spend | mid | 6/6 | **1/6** | 51.3 / 118.3 / 152.6 | |

Pooled over the 12 plants: median band union 62.8 vs mid 58.6 (n 150; median difference +4.6, union >= mid in 11/12) and union 126.2 vs mid 120.0 (n 300; median difference +11.3, union >= mid in 12/12).
All 12 plants are detected by both arcs at both n, so the pass criterion (the union arc detects the true cell) is met, but detection does not separate the arcs: the gain is in score and in locating the cell.
- Spend plants at n 300: the mid arc's best cell is a different cell in 5 of 6 plants (up to 13.8 nats above its true band; plant `spend cicada 0`: true band 51.3, best 65.1); the union arc's true cell is within 3 nats of its best in 6/6.
  This matters for a campaign (a hit reported at the wrong offset until the whole-section check), not for detection.
- The union gain is larger the more edge nulls the window holds (plant `m04 cicada 1` at n 300: 29 nulls, 15 of them edge: union 113.2 vs mid 76.8, 36.4 nats; plant `m04 english 5`: 8 edge nulls of 26: 127.8 vs 125.4).
  One plant (`spend cicada 2`, n 150) has mid above union (58.9 vs 54.7), both detected.
- Matched iid-key nulls (12, union arc, searched in the planted stream, all 8 passes, every offset): max winner score -15.8 (n 150) and -57.0 (n 300); none within 45 nats of T300. This is 12 nulls, not a whole-library null scan;
  the union arc sums over more placements than the mid arc, so a null tail could in principle be heavier; no inflation shows in 12 windows, a tail rate is not measured.
- Compare s01 (mid arc, `any` mode, 12 plants): band median 54.2 / 118.4 (n 150 / 300); here the mid arc's medians are 58.6 / 120.0 (different seeds and generator, same order).

**Cost (`cost`, process CPU time, one core, shared and loaded laptop, n 300 window, m = 20,000, microseconds per offset per sign, sum over the four channels; two runs, so only the ratios are used).**
| run | base | mid kind 3 | union interior | union any | ratio union any / mid |
|---|---|---|---|---|---|
| 1 | 116 | 752 | 695 | 1,123 | 1.49 |
| 2 | 176 | 692 | 631 | 793 | 1.15 |

Phase 51 measured 432 for the mid arc on a quieter machine, so the absolute numbers here are inflated about 1.6x; the union arc costs 1.15-1.5x the mid arc. Union with interior placement is about as fast as mid.
A campaign with the union arc would cost about 1.2-1.5x the mid arc's 260 CPU-hours (planning figure from phase 51 times the ratio; nothing run). Run 1 per channel (union any): hold 414, spend 416, skip5 113, coin 180 microseconds.

## Result
G1, G2, G3, G4 all pass; no tolerance was loosened. The union arc is a drop-in decoder for R4 as fitted: it equals the mid arc under interior-only placement and the base engine at nu = 0 (bit-equal on the real model), matches the dense
reference to 3.6e-15 for every placement, finds 12/12 R4 plants with edge-inclusive nulls at n 150 and 300 (the mid arc also finds 12/12), scores them 4.6 (n 150) and 11.3 (n 300) nats higher in the median, and puts the true cell
within 3 nats of its best cell in 24/24 searches against the mid arc's 18/24 (spend, n 300: 1/6 vs 6/6).
Reading for the R4 negatives (phases 57-60, queued `r4lib`): consistent with s01. The mid arc is not blind to edge nulls at these sizes, so those negatives are not overturned by this; the union arc adds score margin
(4.6-11.3 nats in the median, up to 36 nats in a null-rich window) and better localisation at 1.15-1.5x the cost. It was NOT run on LP2 here.

## What this does NOT exclude / not covered
- No LP2 ciphertext was scored; the union arc was not run on any library campaign; its whole-library null tail is not measured (12 matched nulls, max -15.8 / -57.0).
- Plants use the decoder's channel family (one null per word, uniform value, hold / spend repair at q about 0.81, T-valued repairs). R4's null is checked against its left neighbour and visible to the anti-repeat rule; the arc models an unchecked,
  invisible null (as the mid arc), and the 12 plants show this does not matter at n 150-300. Not modelled: more than one null per word, nulls in a word of Lc = 1, non-uniform null runes, uncapped skip, the null probability's dependence on word
  length (R4 gives Lc = 2 words no null, the arc gives them nu), window-cut words treated as complete, the T-valued repair as a keyed check.
- 12 plants (6 per channel) are a small sample: 6/6 has a 95% Wilson lower bound of about 61%. skip5 and coin plants were not made, so skip5 / coin power under edge nulls is untested; their correctness is covered by G1 and G2 only.
- T300 was frozen for n 300; at n 150 the threshold is not calibrated.
- G1 compares against a reference written by the same author as the engine; Q = 29 exactness against the dense reference was not tested.

## Files
Code: `work/r4fix/s08_backward_union.rs`, `s08_engine_union.py`, `s08_reference_union.py`, `s08_test_union.py`, `s08_power_union.py`; build output `work/r4fix/build/backward_union.dll` (+ `.dll.lib`).
Results: `results/r4fix/s08_union_arc/` (`g1_g3_test.json`, `cost_run1.json`, `cost_run2.json`, `g4_*.json` per plant, `g4_summary.txt`, `r4sim_tests.txt`).
CPU: about 28 CPU-minutes in total (G4 1,399 CPU-s over 2 workers; G1-G3 about 12 s per run, three runs; two cost runs about 1 min each; r4sim tests 53 s). The G4 workers, the r4sim tests and cost run 1 ran at below-normal priority; the G1-G3 runs (about 12 s) and cost run 2 (one process, about 1 min) ran at normal priority.
