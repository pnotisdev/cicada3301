# R4 repair s01: edge-slot plants against the unchanged mid-word decoder (2026-10-23)

Nothing in LP2 is solved. Plants only; no LP2 ciphertext was scored.

## Question
Does the unchanged mid-word decoder (chanscreen v2 mid arc, kind 3, nu 0.42, word-start mask only) still find the planted key when R4's nulls are placed as R4 was FITTED
(slot uniform over 0..L, word edges included, `work/phase57_mechanism.py:77`), rather than interior only (1..L-1) as in every plant so far (`work/phase57_pilot.py:41`)?

## Method
- Code: `work/r4fix/s01_edge_plants.py` (new). `make_r4` is copied from `work/phase57_pilot.py` with a slot-mode parameter; `plant_mid`, `plant_edge`, `lp_pilot_mid` are imported read-only.
  Run: `python -B work/r4fix/s01_edge_plants.py plants --workers 4` (4 workers, below-normal priority), then `... summary`. Probe: `... one --mode interior`.
- Modes (slot = number of plaintext runes before the null, drawn only for multi-rune words with probability 0.45, as phase 57):
  `interior` slot in 1..L-1 (phase 57's exact seed strings `phase57-r4|ch|src|i`, null plant `i + 1000`); `any` slot in 0..L (seeds `r4fix-s01|any|ch|src|i`);
  `edge` slot 0 or L with probability 1/2 each (seeds `r4fix-s01|edge|ch|src|i`). Null plants use index `i + 1000` with an iid key (as phase 57).
- Everything else as phase 57: hold (`m04`) and spend x Cicada / English held plaintext x 3 seeds = 12 plants per mode; library key at a random offset; sign +1 (even index) / -1 (odd);
  repair writes T(c-6) = 24 - 2c(-6) in-word at q 0.81 (q from `frozen.json`, `{ch}|{src}|lib`) when the rune six back is in the same word, else a uniform other rune; the null is a uniform rune
  never equal to its left neighbour and is visible to the anti-repeat rule; n 150 and 300 are prefixes of the same 300-rune window.
- Edge-null bookkeeping (a choice that matters): a null at slot 0 is the first cipher rune of its word, so the word-start flag handed to the decoder is ON the null (the word really starts
  there in the cipher); the word-end flag is on the last null for slot L. The in-word lag-6 repair counts from the first cipher rune of the word, nulls included (as the simulation). For `interior` this is identical to phase 57.
- Decoder: unchanged mid arc (`X.search`, the same call as phase 57), TRUE stream only, both signs, every offset, all four decoder channels searched (hold, spend, skip5, coin); detected =
  S_guard of the true cell (band of +-3 offsets, the plant's own channel and sign) >= T300 = 29.80; "within 3" = true band >= band best over all cells - 3.
- Window start e as in phase 57 (first non-null at or after a random item e0), so windows do not start at word starts, as before.

## Controls
- **Positive (interior reproduces phase 57): PASSED, exactly.** 12/12 detected at n 150 and n 300, 12/12 within 3 nats; band min / median 57.9 / 73.6 (n 150) and 119.5 / 155.2 (n 300),
  identical to `results/analysis/phase57_pilot.txt`; the plants reproduce to full precision (e.g. `m04 cicada 0`: 79.0515 and 170.3310 against phase 57's stored 79.051457 / 170.331043).
- **Null (matched iid-key plant per plant and mode, same layout, true stream searched at every offset / sign / channel):** max winner score
  interior -18.0 (n 150) / -55.8 (n 300) (equal to phase 57: -18.0 / -55.8); any -18.7 / -73.2; edge -16.8 / -70.2. No null is anywhere near T300 = 29.8 (36 null plants x 2 n, 72 searches, none above -16.8).

## Result (12 plants per cell; T300 = 29.80)
| mode | n | detected | true within 3 nats of best | band min / median / max | hold detected | spend detected | matched null max |
|---|---|---|---|---|---|---|---|
| interior | 150 | 12/12 | 12/12 | 57.9 / 73.6 / 87.3 | 6/6 | 6/6 | -18.0 |
| interior | 300 | 12/12 | 12/12 | 119.5 / 155.2 / 179.0 | 6/6 | 6/6 | -55.8 |
| **any** | 150 | **12/12** | 11/12 | 42.1 / 54.2 / 86.3 | 6/6 | 6/6 | -18.7 |
| **any** | 300 | **12/12** | 11/12 | 90.6 / 118.4 / 162.6 | 6/6 | 6/6 | -73.2 |
| edge | 150 | 10/12 | 9/12 | 21.4 / 46.4 / 73.6 | 5/6 | 5/6 | -16.8 |
| edge | 300 | 12/12 | 8/12 | 51.4 / 91.0 / 122.7 | 6/6 | 6/6 | -70.2 |

- In `any` mode 43% (n 150: 43/100 nulls) and 42% (n 300) of the nulls are edge nulls, matching the "41-49%" of the brief; the windows hold 5-8 (n 150) and 8-15 (n 300) edge nulls, 10-16 / 21-34 nulls in total.
- **Cost of edge nulls (score, not detection):** median band 73.6 -> 54.2 (n 150) and 155.2 -> 118.4 (n 300) from interior to any: about -19 and -37 nats; edge only: 46.4 and 91.0.
  Among the 24 any + edge plants the band falls about 1.8 nats (n 150) and 1.9 nats (n 300) per edge null in the window (correlation -0.54 and -0.69). The weakest `any` plant is still 12.3 nats (n 150) / 60.8 nats (n 300) above T300.
- **Detection by number of edge nulls:** all 24 non-interior plants have >= 3 edge nulls in the window (any: 5-8 at n 150, 8-15 at n 300; edge: 8-19 and 18-37), so no window with 0-2 edge nulls exists and the dose-response has no low end.
  n 150: 3-5 edge nulls 4/4 detected (median band 57.3), 6 or more 18/20 (47.1; the two misses are edge-mode plants with 14 and 17 edge nulls: bands 26.9 and 21.4). n 300: 24/24 with 6 or more (median 109.7).
- **Detection by position of the first edge null:** n 150: first edge null at window index 0-9: 13/15, 10-29: 5/5, 30-99: 4/4; n 300: 15/15, 5/5, 4/4. Almost every plant has its first edge null in the first ten runes (an edge null occurs about once per 2-3 words), so
  an early first edge null is the norm and the two n-150 misses are the plants with the first edge null at index 1 and 1. Not enough spread to separate position from count.
- **True cell is not always the winner:** in `any` mode one plant (spend, English, 0) has a wrong cell 8.6 / 11.6 nats above the true band (the wrong cell is in the planted stream and also far above T300); in `edge` mode 3/12 (n 150) and 4/12 (n 300) have a wrong cell
  4.3-11.6 nats above. For a campaign this is a "within 3 nats" issue, not a detection issue: the true cell is above T300 but a nearby wrong cell scores higher, so a real hit would be reported at the wrong offset until the whole-section check.
- The probable reason the unchanged arc survives edge nulls (not tested here): the hold channel (and spend) lets an unexplained rune be a collision repair that does not advance the key, which is right for a null, at the price of the repair probability; the mid-null state absorbs the
  interior nulls. This was not isolated by a mutant test (e.g. decoder with repair disabled).

## Decision
The pre-written rule: detection in `any` mode below about 90% means the R4 negatives (phases 57-60, queued `r4lib`) cover only the interior share and a union arc is needed. **Detection in `any` mode is 12/12 at n 150 and 12/12 at n 300 (>= 90%), so
the rule does not trigger: the R4 negatives with the unchanged mid arc are NOT limited to the interior share, to the extent a plant with R4's fitted slot distribution is found as often.** Caveats the rule does not see:
1. 12/12 on 12 plants has a 95% Wilson lower bound of about 76%, not 90%; the point estimate clears 90% but the sample cannot show it. Doubling the plants per cell would tighten this cheaply (about 15 CPU-minutes per mode).
2. The n 150 margin is thin in the worst plants of `edge` (21-30 nats against T300 29.8, which was frozen for n 300; two misses) and 12-30 nats lower median power in `any` than interior. At n 300 the any-mode band minimum is 90.6, 61 nats above T300.
3. Power fell by about 19-37 nats in the median, so the usable margin for weaker plants (a smaller key family match, other plaintext, repair or null rate) is smaller than the interior plants suggested: an R4 plant that was 'barely found' in the interior setting would be missed with edge nulls.
4. The wrong-cell-above-true cases (up to 11.6 nats) mean offset alone cannot be trusted below whole-section verification.

## What this does NOT exclude
- Anything about LP2's actual key family: plants use library streams at their own key and the true-stream search, which is the decoder's best case; the real LP2 search is against 1,439 streams x offsets and the n-150 whole-library null tail is not measured here.
- Weaker repair / null structure than R4 as specified (q, 0.45, one null per word, null value uniform, repair T value), a null whose value depends on the word, 2 nulls per word, or plants with a different plaintext than the held Cicada / English text.
- The hold / spend channels only (skip5 and coin plants not made); edge nulls with a different word-start flag convention (e.g. the decoder given the word start AFTER the null) were not tried.
- A union arc (null at any cipher position) would still score the `any` plants higher (it models them); this was not built or measured, so the size of the possible gain is unknown. The score loss of about 1.9 nats per edge null is the amount a union arc could regain.
- Whether LP2 wants edge or interior nulls (that is the keyless simulation of lead 2, not this session).

## Files
- `work/r4fix/s01_edge_plants.py` (generator, runner, summary); `work/r4fix/probe_out.txt`, `work/r4fix/run_out.txt` (stdout of the probe and the full run; the `_err.txt` files are empty or stderr).
- `results/r4fix/s01_edge_plants/{interior,any,edge}_{m04,spend}_{cicada,english}_{00,01,02}.json` (36 per-plant records incl. null-plant searches and edge-null positions), `probe.json` (the first interior plant, run alone for timing), `summary.txt`.

## CPU used
Probe 7 s (98 MB peak working set per process). Full run: 36 plants (each with 2 n x 2 plants x 8 passes), 1,621 CPU-seconds summed over the plant records (about 27 CPU-minutes), 4 workers at below-normal priority, about 10 minutes wall.

## Note: corpora check (orchestrator message, 2026-10-23)
`work/ref/corpora/*.txt` was copied into the worktree at 23:42, after my first run (23:33-23:41), so the 18 English-plaintext plants (6 per mode) of that run used whatever the English
loader falls back to without the corpora. I moved those 18 records aside and reran them with the corpora present (`plants`, 4 workers, below-normal, about 8 minutes wall, at most 32 CPU-minutes (4 workers);
stdout `work/r4fix/run2_out.txt`). **Old and new records are identical: maximum absolute difference 0 in every band score and every matched-null score (n 150 and 300, 18 files)**, and the interior
English plants match phase 57's stored values exactly (e.g. 62.05 / 146.91 for `m04 english 0`). So the interior control reproduces phase 57 exactly with the corpora present, and no number in this log changed.
(I did not investigate why the pool is identical in both states; `B.pool('held', 'english')` in `work/chanscreen/` may not read those corpora.) Total CPU for the session is therefore at most about 60 CPU-minutes (1,621 s first run plus the rerun, whose records sum to 1,979 s for the final 36 plants).
