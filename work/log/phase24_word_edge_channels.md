# Phase 24: word-edge channels in chanscreen v2 (engine option, gates, plants, power ladder, null scan, cost)

Side session, 2026-10-20/21, <= 2 CPU cores, no LP2 ciphertext scored, nothing committed. **Nothing in LP2 is solved.** This entry builds and gates the arc of
`work/log/phase20_segmentation_plan.md` step 3 (registry row `open-unkeyed`); it does NOT run the LP2 campaign. The independent review is `work/log/phase24_review.md`;
this entry answers its five items (section 8).

## 1. The channel (decided and documented)

Added as a NEW entry point `backward_edge` in `work/chanscreen/v2/backward_edge.rs` (dll `build/backward_edge.dll`; `backward.rs` and `backward.dll` are untouched).
`kind = 0` calls a verbatim copy of the base body, so the default is bit-identical by construction and by test (2.1). Python adapter `engine_edge.py`
(`all_offsets_edge(c, key, sign, q, ch, pi, L, kind, cand, nu)`); the base `engine.py` is unchanged.

* The decoder is handed a candidate mask `cand[i]` (i >= 1) from the word separators; each candidate position independently carries an event with probability `nu`
  (fixed 0.42, as q = 0.81 is fixed in the frozen contract), marginalised exactly in the summed-path likelihood (and in the uniform model U, which gets the same channel structure).
* **kind 1, keyless null.** The rune at a candidate position is a null with probability nu: emitted uniformly (1/29), consumes no key value, is invisible to the anti-repeat
  rule (the next real rune is compared with the last REAL ciphertext rune) and to the language model (the LM conditions on the last REAL plaintext). State = (key pointer j,
  trailing nulls d, previous plaintext class); class sets per (i, j, d) = ordinary class of the last real rune plus the collision class of every earlier real rune a run of
  candidates can hide. `nullf` = candidates are the word-final positions, `nulli` = the word-initial positions (i >= 1). Same code, different mask.
* **kind 2, extra key advance** (`adv`): before the real rune at a candidate position the pointer advances by one extra key value with probability nu (candidates = word-initial positions).
* Channels hold, spend, skip5, coin (the four of the frozen contract). Uncapped `skip` (mode 2) is rejected for kinds 1 and 2 (plants for `skip` are decoded with `skip5`, as in E4).
* Not modelled: an event before window position 0 (an offset shift / unknown start); more than one event per position; events at line or page breaks (only word edges); nulls
  INSIDE words; a null-rune distribution other than uniform. The advance at line / page breaks listed in the registry row is NOT built.

## 2. Gates

### 2.1 Default behaviour bit-identical (`bitcheck_edge.py`, `bitcheck_edge.json`)
All 580 stored calibration and held records (200 + 380), every bank stream, 5 channels (incl. uncapped skip), both signs, q = 0.81 and the record's frozen q, all offsets:
**86,400 calls, 34,473,600 offset cells, 0 byte mismatches** between `backward.dll` and `backward_edge.dll` with `kind = 0`. SHA-256 of both dlls and sources are pinned in
`results/chanscreen/edge/pins.json` (the json of the bitcheck pins only the base files; the dll under test was built 19:13, before the bitcheck started, and was not rebuilt afterwards).

### 2.2 Dense / brute-force reference (`reference_edge.py`, `test_edge.py`, `test_edge_scale.py`)
`reference_edge.py` is an exact Fraction event tree (no memoisation, no class sets), written from the encryptors of `work/m04/m04.py`, not from the DP: latent edge choice x plaintext symbol
(LM) x channel randomness (hold/spend repair, skip5 redraws, coin). `test_edge.py`: 400 random tiny cases (Q 3-4, n <= 5, key <= 8, all four channels, kinds 0/1/2, q in {0, .6, .8, 1},
nu in {0, .4, 1}, forced doublets, 60% candidate density = runs of candidates): 2,022 non-zero cells, **worst |log error| 1.8e-15**, the -inf cells match exactly; an extra run of 150
cases with n 5-7, 75% density: 2,434 cells, worst 3.6e-15. Four wrong-reading mutants (null visible to the anti-repeat rule, null consumes a key value, null restarts the LM, advance ignored)
disagree with the engine in 154-265 of 300 cases, so the test tells the readings apart. `test_edge_scale.py`: Q = 29, n 10-14, key 28-36, 24 trials, memoised exact reference with the explicit
previous plaintext (tests the sparse-class closure at the real alphabet): 334 non-zero cells, worst 1.4e-14. Limits: the reference and the plants share one author's reading of the channels.

## 3. Plants (`step4/plant_edge.py`, `results/chanscreen/edge/`, `edge_summary.txt`)
E4-style: held Cicada / Emerson plaintext (digraph runes) cut at LP2's word lengths (random stretch of a random section 0.7-0.15), enciphered by the m04 encryptors rewritten with a
"last real cipher rune", events at 42% of the words (null after the word = `nullf`, before = `nulli`, extra advance before the word = `adv`; `none` = same words, no events),
window = 300 runes after the first e (0-99), starting at a real rune; the decoder gets the candidate mask only (never which words carry an event). Planted stream searched (4 channels x 2
signs x every offset), frozen T300 = 29.799, nu = 0.42. 12 plants per (kind, channel), 192 plants (6 per channel x source).

* **Edge decoder: 192 of 192 detected** (median band score 139-190 nats), also the `none` plants (48 of 48, median 170-190).
* **Base engine** on the same windows: detects only the hold channel (12/12 nullf and nulli, 2/12 adv); 0/12 for spend, skip5, coin on nullf/nulli/adv: the edge arc is what finds those.
* **Matched nulls** (iid key, same words/events/channel, searched in the same stream): 144 windows, 0 reach T300, maxima between -184 and -65.4. One matched-null record scored 831 on the first
  run (a `nulli` skip5 window, stream `omega(n)`); a fresh recomputation of the same call gave -105.8 twice. It is the transient engine fault of `step3/PROTOCOL.md` Amendment 3 (a non-reproducing
  cell); the record is kept in `results/chanscreen/edge_quarantine/` and the plant was re-run. Rate here 1 of about 4,600 engine calls, the same order as the 1.7e-5 of the campaign
  faults (the PC was under full load). **Any edge hit must be recomputed in a fresh call** (hit rule, section 6).
* "Winner = true cell" is NOT the metric (101/192 in the first summary): 85 of the 91 other winners were exact periodic aliases (keyword streams) with the same score. The metric is "true cell within 3 nats of
  the global best": **192 of 192**.
* Edge minus base score on the true channel: plants with events >= +39.7 nats (hold: nullf +39.7, nulli +46.0, adv +54.5; the other channels >= +232), `none` plants -14.3 to -39.7.
* Wrong-offset exceedances (diagnostic, not a stop): 627k of 17.7M cells at t = 0, all in periodic short streams (same cause as E4's 269,508).

## 4. Power ladder (`step4/ladder_edge.py`, `results/chanscreen/edge_ladder_summary.txt`)
Plant event rate nu_plant in {0.1, 0.2, 0.42, 0.6} (0.1 / 0.2 = events on a quarter / half of the words at the 0.42 rate) against the decoder's 0.42; windows = first 60 / 150 / 300 runes of the
plant; kinds nullf and adv; 24 plants per (kind, nu, n) cell, with a matched iid-key null in the same stream; T300 used for every n (the shorter-window threshold is NOT calibrated; the clause
scan's T would be set from its own cell count).

| kind | n | detected (nu 0.1 / 0.2 / 0.42 / 0.6) | true cell within 3 nats of the global best | matched-null max S_guard |
|---|---|---|---|---|
| nullf | 300 | 24, 24, 24, 24 of 24 | 22-24 of 24 | -65 to -72 |
| nullf | 150 | 24, 24, 24, 24 | 23-24 | -12 to -17 |
| nullf | 60 | 19, 18, 16, 14 | 23-24 | +5.7 to +10.0 |
| adv | 300 | 24, 24, 24, 24 | 24 | -78 to -85 |
| adv | 150 | 24, 24, 24, 24 | 23-24 | -24 to -27 |
| adv | 60 | 21, 18, 21, 18 | 23-24 | +1.4 to +7.2 |

Reading: at n >= 150 the arc detects every plant over the whole range nu_plant 0.1-0.6 (median band 75-96 nats at n = 150, 150-190 at n = 300) and the decoder's nu = 0.42 is not critical; at n = 60
power is 14-21 of 24 and the matched nulls (+1 to +10 nats) are far below T300 (29.8) but the maximum is taken over one stream only. The by-channel table (all nu pooled): n = 300 and 150 are 24/24 in
all eight (kind, channel) rows; n = 60 ranges 13/24 (nullf hold) to 21/24 (adv hold, skip5, coin).

## 5. Null scan (E3-style, the full library; `step4/null_scan_edge.py`, `results/chanscreen/edge_null/`, `edge_null_summary.txt`)
One matched iid-key ciphertext window per kind (nullf, nulli, adv; each the hold encryptor with an iid key, Cicada plaintext, word-edge mask of the plant machinery, 300 runes), searched against all 1,439
streams (13,326,835 key values), every offset, both signs, hold/spend/skip5/coin, decoder nu = 0.42, S_guard as in the frozen contract. **319,878,576 cells** (3 x 106,626,192), 42 tasks, 2 workers, about 7 hours of wall time (a loaded PC).

| kind | max S_guard (argmax) | cells >= 0 | >= 5 | >= 10 | >= 20 | >= T300 |
|---|---|---|---|---|---|---|
| nullf | -69.34 (sha256-chain mod, hold, +1) | 0 | 0 | 0 | 0 | 0 |
| nulli | -60.33 (md5-ctr mod, hold, +1) | 0 | 0 | 0 | 0 | 0 |
| adv | -61.06 (sha512-ctr reject, hold, -1) | 0 | 0 | 0 | 0 | 0 |

The null maxima sit 90-100 nats below T300 (the base engine's own sanity nulls are at -97 to -102). Three windows give three maxima: this shows no gross inflation by the extra latent freedom, it does not certify a
0.001 tail rate, and the tails of the spend / skip5 / coin ciphertext statistics (the window is a hold-encryptor window) and of other plaintext sources are not scanned. No cell reached the flag level (10 nats), so the
fresh-recomputation check was not exercised on this data. More windows can be added with `null_scan_edge.py run --windows N` (resumable; about 3.5 hours per window triple on 2 cores).

## 6. Hit rule, pre-registered here before any LP2 ciphertext is scored by the arc (`step4/hit_rule.py`)
A TIER-1 EDGE HIT needs all of: (1) S_guard >= T (T300 = 29.799; the three kinds triple the number of passes per window to 24, so a family-wise campaign threshold is T = ln(N_cells / alpha) with the tripled N,
about +1.1 nats); (2) reproduction in a fresh recomputation; (3) **edge versus base**: S_edge(cell) minus the best base-engine S over the same stream and sign, all four base channels, offsets within +-3,
>= 20 nats (events present: >= +39.7 on the plants, no events: <= -14.3; the margin 20 was read off these plants and the base maximum over all channels was not measured on them, so it is a pre-registration, not
a calibrated test); a hit the base engine scores about as well supports only the base hypothesis; (4) key-sequence aliases are collapsed (same stream and sign, equal key window of n x channel factor + 16
values = one hit, best member reported); then the whole-section verification chain of `docs/CAMPAIGNS.md` and `step3/PROTOCOL.md` as for the base campaign. Report every hit with "within 3 nats of the global best", not "winner = true offset".

## 7. LP2 word-edge masks (`step4/lp_mask.py`, `results/chanscreen/edge/lp_mask_check.json`)
Built from the master's separators ' ', '.', '&' only; line breaks and page marks are transparent. Check: 55 page marks in sections 0.7-0.15, **32 inside a word** (a rune on both sides, no separator),
reproduced; `lp_words()` of `plant_edge.py` (which cuts at page marks, ~1% too many edges) is used for the PLANTS only, never for an LP2 mask. `window_masks(sec, start, n)` returns the word-final and word-initial masks of an LP2 window
(window 0.9@0: 60 final, 60 initial in 300 runes).

## 8. Cost (`step4/cost.py`, `results/chanscreen/edge/cost.json`; process CPU time, one core, shared PC, n = 300 window with one candidate per word, m = 20,000)
Sum over the four channels, microseconds per offset per sign: base 113, null (nullf or nulli) 239 (x2.1), advance 186 (x1.6). Per channel null: hold 84, spend 78, skip5 34, coin 42 (base 44, 45, 11, 14).
A null with EVERY position a candidate (300 trailing-null states) takes 240,000 us/offset: not usable (the mask is one candidate per word). With the campaign's 49 CPU-hours for the base four channels at n300:
**nullf + nulli + adv ~ 49 x (2.1 + 2.1 + 1.6) = ~285 CPU-hours** (using the absolute microseconds instead, 82 windows x 13.33M offsets x 2 signs: 145 + 145 + 113 = ~403 CPU-hours, because this
PC runs the base at 113 us rather than the 80 us implied by 49 h). 285-400 CPU-hours on 15 workers is about 19-27 hours. Memory per pass: (d_max + 1) x (m + 1) x (d_max + 2) values; d_max = longest run of
consecutive candidates (LP2 word-edge masks: 2-3).

## 9. Review items
1. E3-style null scan and power ladder: sections 5 and 4. 2. Alias collapse and "within 3 nats": section 3 and 6. 3. Page-safe mask: section 7. 4. Edge-vs-base margin pre-registered: section 6.
5. Provenance: SHA-256 of dlls and sources in `results/chanscreen/edge/pins.json` (backward_edge.dll `aedf1f12...`, backward_edge.rs `ff79fa79...`, backward.dll `4f7ea5ef...` unchanged). The 20:08 edit of `plant_edge.py`
changed only the true-cell band in `search()` for matched-null windows (the first version crashed there: an empty slice when no true offset exists, which is why only `none` records, which have no matched null,
existed before 20:08). It did not touch plant generation or scoring; the 18 older records are all `none` plants. A later edit (adds the `true_within3` field) changes no score. Verification: the 18 older `none` records were re-run with the current code into a scratch folder: **0 of 18 differ** in band score, winner score or detection (bit-equal).

## 10. What is NOT covered
Anything about LP2 (no ciphertext scored). Hypotheses outside the arc: nulls inside words, null runes not uniform, events at line / page breaks, more than one event per position, event rates varying along the text,
a start inside an event, uncapped skip, other plaintext languages, stream families outside the library. Plants use the decoder's own generative model (plant nu 0.1-0.6 and window 60-300 are the only variations tested);
shorter windows have no calibrated threshold; the null scan covers the stated number of cells only (a full campaign has ~100 times more windows).
The arc explains `none` plants too (section 3), so a hit is read through the edge-vs-base rule. A campaign negative may be quoted only as "no edge-arc cell above T in the scanned windows for events at <= 60% of word
edges, library streams, hold/spend/skip5/coin, n >= 150".
