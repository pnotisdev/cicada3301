# Phase 51: a MID-WORD keyless-null channel for chanscreen v2 (side session, 2026-10-21)

Nothing in LP2 is solved. Build and gate only: **no LP2 ciphertext is scored, no campaign is launched**. No PLAN / registry / STATUS / SESSION_LOG / README edits, no commit.
Motivation: phase 47 (insertion doublets): if LP2's "+1 rune in ~42% of words" is an inserted rune it must sit MID-WORD (edge-only insertion: joint p 0.000; uniform slot: p 0.08).
The phase-24 edge arc (`backward_edge.rs`, kinds nullf / nulli / adv) puts events only at word edges, so it is aimed at the wrong place for that reading.

## 1. The channel (decided before any code)

Per word of cipher length Lc (as the separators ' ', '.', '&' of the window give it): with probability nu = 0.42 the word carries ONE keyless null rune at an INTERIOR cipher position
t in 1 .. Lc-2 (uniform, probability nu / (Lc-2) each); with probability 1-nu it carries none. Words with Lc < 3 have no interior slot and no weight (they cannot carry a null).
The null is emitted uniformly (1/29), consumes no key value, is invisible to the anti-repeat rule (the next real rune is compared with the last REAL cipher rune) and to the language model
(the LM conditions on the last REAL plaintext) - exactly the semantics of the edge arc's null; only the placement prior differs. Mask handed to the decoder = word-start flags only.
Not modelled (same list as phase 24 plus): more than one null per word, null at a word edge (phase 24 covers those), null rune not uniform, nulls in words of Lc < 3, an event before window position 0,
window-cut first / last words are treated as complete words.

## 2. Likelihood

For one word with cipher positions a .. b (Lc = b-a+1 >= 3): P(word) = (1-nu) * P(no null) + sum_{t=a+1}^{b-1} nu/(Lc-2) * P(null at t), each P(.) the usual channel path sum
(hold / spend / skip5 / coin, repair, language model, key pointer). The words are independent in the prior, so the window likelihood is the path sum with a per-word weight, no per-position nu:
* null at interior position: weight nu/(Lc-2) / 29, state flag u 0 -> 1 (at most one per word);
* at the word's last position: weight (1-nu) if u = 0 (no null was placed) else 1; words with Lc < 3: weight 1 throughout.
The uniform-ciphertext model U (denominator of the score) gets the same latent structure, as in phase 24 (nulls are uniform there anyway).

## 3. Cost: state = (u, d) per word, not one state per position

A null is at most one per word and interior, so the "trailing nulls" counter of the edge null is at most 1 and the null's position is never enumerated: the backward pass carries three
states per (position, key pointer): S0 = (no null yet in this word, d = 0), S1 = (null used earlier, last position real), S2 = (null at the previous position, d = 1; the last real rune is two back).
Only the states reachable forward from the window start are computed (a forward boolean pass), so a word of Lc < 3 costs the base and S1 / S2 exist only after the first interior slot.
Class sets (previous-plaintext candidates; the collision classes of the real runes before the last one) hold at most 3 values (ordinary, rune at t-1, rune at t-2 when t-1 could be the null) instead of the
edge arc's run-length-dependent K. Cost therefore grows with the word length only through the number of reachable states (<= 3 per position), not with every position as an independent null
(the "null at every position" variant is 240,000 us/offset in phase 24). Expectation: about 2-3x the base engine per offset (to be measured, section 6).

## 4. Bit-identity

New file `work/chanscreen/v2/backward_mid.rs` `include!`s `backward_edge.rs` verbatim (so its helpers are reused, not copied) and adds the entry `backward_mid(..., kind, cand, nu, wstart)`:
kind 0, 1, 2 dispatch to `backward_edge` unchanged (kind 0 = base body, kinds 1, 2 = the edge arc), kind 3 = mid-word. `backward.rs`, `backward_edge.rs`, `backward.dll`, `backward_edge.dll`
are not touched (SHA-256 checked before / after). Gates: (a) kind 0, 1, 2 of `backward_mid.dll` against `backward.dll` / `backward_edge.dll` on the stored calibration + held records, 0 byte mismatches;
(b) kind 3 with nu = 0 against the base engine (a null with probability 0 must give the base, reported as bit-equal or max |diff|).

## 5. Gates and measurements planned (all recorded below)
G1 dense brute-force reference (`reference_mid.py`: sum over every per-word null placement x the exact event tree, Fractions, written from the encryptors) vs the engine on tiny random cases, with wrong-reading mutants;
G2 bit-identity (4); G3 E4-style plants with mid-word nulls in 42% of multi-rune words (n = 300, 4 channels x 2 sources), detected at the frozen T300 and "true cell within 3 nats of the global best";
G4 power ladder (event rate 0.1 / 0.2 / 0.42 / 0.6 x n = 150 / 300); G5 E3-style null scan (one iid-key window, whole library); G6 cost per window; G7 blindness: the mid-word plants under the edge arc (nullf / nulli / adv) and the base engine.


## 6. Results (all measured 2026-10-21, <= 4 threads, nothing committed; files in `work/chanscreen/v2/` and `results/chanscreen/mid*`)

Files: `backward_mid.rs` (+ `build/backward_mid.dll`), `engine_mid.py`, `reference_mid.py`, `test_mid.py`, `test_mid_scale.py`, `bitcheck_mid.py/.json`, `step4/plant_mid.py`, `step4/null_scan_mid.py`, `step4/cost_mid.py`;
results `results/chanscreen/mid/` (plants, cost.json), `mid_summary.txt`, `mid_ladder/`, `mid_ladder_summary.txt`, `mid_null/`, `mid_null_summary.txt`. The pre-existing `backward.rs`, `backward_edge.rs`, both dlls: SHA-256 identical before / after (pinned in `bitcheck_mid.json`).

**G1 dense reference.** 300 + 400 + 150 random tiny cases (Q 3-4, n <= 9, key <= 10, 4 channels, q in {0, .6, .8, 1}, nu in {0, .4, 1}, word starts at 25%): 1,326 + 1,650 + 712 non-zero cells, worst |log error| 5.3e-15, -inf cells match exactly.
Q = 29, n 10-14, 24 trials (memoised exact reference): 336 cells, worst 1.4e-14. Mutants (null visible to the anti-repeat rule / null consumes a key) disagree with the engine in 31 / 73 of 250 cases.
Limit: reference and engine share one author's reading of the channel.

**G2 bit-identity (a SUBSET, not the full 580-record run of phase 24).** 97 stored calibration + held records (every 6th), 2 bank streams each: kind 0 vs `backward.dll`: 1,940 calls, 0 byte mismatches (incl. uncapped skip); kinds 1 / 2 vs `backward_edge.dll`
(random word-edge masks): 1,552 + 1,552 calls, 0 mismatches; kind 3 with nu = 0 vs the base engine: 1,552 calls, bit-equal (max |diff| 0.0). Edge-mode identity holds by construction (`include!` of the unchanged source) and by this test.

**G3 plants** (`mid_summary.txt`; 48 plants = 6 per channel x source, n = 300, mid-word null in 42% of multi-rune words, median 26 nulls in 63 words; decoder nu 0.42, frozen T300 = 29.80; the decoder never sees which words carry a null).
Mid decoder: **48 of 48 detected, true cell within 3 nats of the global best in 47 of 48** (median band 136-161 nats; the one miss is a `coin` plant at 11/12). Matched iid-key nulls (same words / placement, searched in the same stream): 48, max -57.7, none >= T300.

**G4 power ladder** (`mid_ladder_summary.txt`; 24 plants per rate x n, matched null per plant; T300 used for every n, not calibrated for n = 150):
| plant rate | n = 150 detected / within 3 / median band / null max | n = 300 |
|---|---|---|
| 0.10 | 24/24, 24/24, 90.3, -18.5 | 24/24, 24/24, 178.6, -66.6 |
| 0.20 | 24/24, 24/24, 90.3, -16.0 | 24/24, 24/24, 178.3, -65.3 |
| 0.42 | 24/24, 24/24, 75.6, -15.0 | 24/24, 24/24, 151.0, -65.0 |
| 0.60 | 24/24, 24/24, 67.0, -17.4 | 24/24, 23/24, 136.5, -57.8 |
Every cell of rate 0.1-0.6 x n 150 / 300 is detected (96/96); the decoder's fixed nu = 0.42 is not critical. n = 60 was not run.

**G5 null scan** (`mid_null_summary.txt`): one matched iid-key window (hold encryptor, Cicada plaintext, 28 nulls, 300 runes) against all 1,439 streams, every offset, both signs, 4 channels: **106,626,192 cells, max S_guard -53.79**
(`(p+1)/2`, -1, hold, offset 10,631); 0 cells >= 0, 5, 10 or 20; no flagged cell, so the fresh-recomputation check was not exercised. That is 83.6 nats below T300. One window only: it shows no gross inflation from the placement freedom,
not a 0.001 tail rate; the spend / skip5 / coin ciphertext tails and other plaintext sources are not scanned (phase-24 caveat unchanged). The edge-arc null maxima were -60 to -69; this one is -53.8 (one window each).

**G7 blindness** (same 48 plants, decoders given their own masks; "detected" = true cell >= T300; median band score in nats):
| decoder | detected | true within 3 of best | median band |
|---|---|---|---|
| mid (kind 3) | 48/48 | 47/48 | 149.3 |
| base engine | 12/48 (hold 12/12; spend, skip5, coin 0/12 each) | 12/48 | -244.0 |
| edge nullf | 44/48 | 30/48 | 74.4 |
| edge nulli | 43/48 | 28/48 | 70.6 |
| edge adv | 13/48 | 12/48 | -146.3 |
The edge arc is NOT blind to mid-word nulls: it still detects 44 and 43 of 48 (every hold plant), because the nullf / nulli decoders may place a null at a neighbouring edge and the key drift is small, but it loses a median 74-78 nats against the mid decoder and
its best cell is often not the true one (within 3 nats only 30 and 28 of 48; the others are aliases / other cells scoring higher). The base engine detects only hold (0/12 for the other three channels, band about -250), `adv` is blind except for hold.
So an edge-arc campaign hit on a mid-word source would be read as a weak edge hit with a 70+ nat deficit against the mid arc; the edge-vs-base rule of phase 24 (>= 20 nats) would be satisfied by a mid-word source for hold.

**G6 cost** (`cost_mid.py`, process CPU time, one core, shared PC, m = 20,000, n = 300 window, microseconds per offset per sign, sum over the four channels): base 116, edge null (nullf) 250, **mid-word 432 (3.7x base, 1.7x the edge null)**.
Per channel mid: hold 151, spend 150, skip5 59, coin 72. Memory: three states x (m + 1) x 3 class slots per pass. Campaign planning (NOT launched): 82 n300 windows x 13.33M offsets x 2 signs x 432 us = about 262 CPU-hours
(the phase-24 scaling, 49 h x 3.7, gives about 180 CPU-hours); on 14 workers 13-19 hours. One null-scan window took about 100 minutes of wall time on 4 loaded workers (14 chunks of about 20 minutes).

## 7. What is NOT covered
Anything about LP2 (no ciphertext scored). Not modelled: more than one null per word, null at a word edge (phase 24's arcs), non-uniform null runes, nulls in words of cipher length < 3, an event before window position 0, window-cut first / last words treated as complete,
uncapped skip. The decoder's per-word null probability is a fixed 0.42 over words of cipher length >= 3 (the plant rate is over multi-rune plaintext words); the threshold for n = 150 and 60 is not calibrated; plants use the decoder's own generative model;
the null scan is one window; bit-identity was run on a subset of records. A campaign negative could be quoted only as "no mid-word-arc cell above T in the scanned windows for one interior null in up to 60% of words, library streams, hold/spend/skip5/coin, n >= 150".

## 8. One-window LP2 pilot (2026-10-22; `step4/lp_pilot_mid.py`, `results/chanscreen/mid_lp_pilot/`, `mid_lp_pilot_summary.txt`)
Section 0.7 @ 0 (the first n300 window), page-safe word-start flags of `lp_mask.py`, full library (1,439 streams), hold/spend/skip5/coin, both signs, every offset, decoder nu = 0.42, 4 workers at below-normal priority, about 4 CPU-hours.
**106,626,192 cells, max S_guard -51.62** (`sha256-ctr reject :parable`, -1, hold, offset 5,480); 0 cells >= 0, so no recomputation, no base comparison, nothing for whole-section verification (kscreen/verify.py was not used).
Comparison: the null distribution is the single iid-key window of section 6 (max -53.79, 106.6M cells), which is a DIFFERENT window (hold encryptor, Cicada plaintext, 28 nulls) from this LP2 window; both maxima lie 81-84 nats below T300 = 29.8 and within 2.2 nats of each other.
Reading: window 0.7@0 holds no library stream under the mid-word channel at plant-covered rates (0.1-0.6, hold/spend/skip5/coin); one window of 82, not the campaign. Recommendation: a full mid-word campaign (about 260 CPU-hours) is not justified by this pilot; it is the remaining untested placement of the unkeyed-insertion hypothesis, to be run only when a CPU is free.
