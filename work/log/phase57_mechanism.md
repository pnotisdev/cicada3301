# Phase 57: one encryption rule for all of LP2's anomalies? (2026-10-22)

Nothing in LP2 is solved. Scripts `work/phase57_mechanism.py` (simulation, `results/analysis/phase57_mechanism.txt`) and `work/phase57_pilot.py` (planted control and LP2 pilot,
`results/analysis/phase57_pilot.txt`, raw records `results/chanscreen/phase57_plants/`, `results/chanscreen/phase57_lp_pilot/`). Run logs `work/tmp/phase57_*.log`.

Constraints any rule must meet at once: (1) doublets 0.63% (81% of would-be repeats prevented, equally in words and across gaps: LP2 63 in-word, 23 across); (2) in-word lag-6 pairs with
c' = 24 - 2c, 80 against about 45, zero across gaps; (3) word lengths: one extra rune in about 42% of words; (4) everything else flat; (5) DJU BEI.

## 1. Reasoning (written before the simulations)

**(a) What c' = 24 - 2c can mean.** Its fixed point is c = 8 (H): c' - 8 = -2 (c - 8). The relation is "multiply by -2 about H". The multiplier is invariant under every affine relabeling of
the alphabet (shift, Atbash 28 - x, multiplication by m): with x = m c + b the relation stays x' = -2 x + const. So it is not Atbash in disguise (multiplier -1), not a copy (+1),
not multiplication by 2 or by 15 = 2^-1 alone (+2, +15); the doubling AND the sign flip are intrinsic; only the constant 24 depends on the coordinates. In LP1's operations it is
Atbash(2c + 4) = 28 - (2c + 4), or Atbash(c) - c - 4. -2 is a primitive root mod 29 (order 28), so the map has no short cycles.
For c = f(p, k): a hit means c_j is a fixed function of c_(j-6) alone. If c_j carried plaintext through a key (c_j = p_j + k_j), the key would have to be 24 - 2c_(j-6) - p_j, i.e.
depend on the current plaintext, which no key does. A full ciphertext autokey k_j = 24 - 2c_(j-6) gives hits exactly where p_j = 0 (F), and the residual r = c_j + 2c_(j-6) - 24 would equal
p_j everywhere: an English-shaped residual, which the lag-feedback rows exclude (r is flat except the r = 0 cell). So a hit rune carries NO plaintext of its position: it is a null,
or a lossy overwrite (a repair), or the encoding of one fixed plaintext rune. Inside words only means the encryptor looks back only within the current word. The rate per pair
(0.027) equals the rate of prevented collisions (q / 29 = 0.028): the natural reading is the collision repair writing T(c_(j-6)) (phase 25's M1). The plaintext-F reading
(LP1 treats F specially) predicts the rate of F at word positions >= 6, which is far lower (phase 25 measured 0.0056 per pair): simulated anyway as R8.

**(b) What adds a rune to ~42% of words with flat unigrams.** The extra rune must be uniform (a null, or a function of uniform cipher runes). The length histogram fixes its SCALING:
a fit with one extra rune in a fixed share of words is good (G 16.5); an extra rune per rune at a fixed rate (more in long words) is not (phase 47 E: G 160). So the event is per word,
not per rune: a per-word null or check rune, a key indicator per word, or a plaintext-side marker. A key-value event (an inverted F-skip: "when the key rune is in a set, emit a null")
is per rune and should fail; digraph runes split into letters is plaintext-side and already fails (phase 25: best G 58). Where the null sits (word edge or mid-word) the length
histogram cannot say; the doublets can, but only if the null escapes the anti-repeat check (phase 47).

**(c) One rule for both?** Three rates: prevented collisions 0.034 per rune (q 1) or 0.028 (q 0.81); T hits 0.027 per in-word lag-6 pair; extra runes about 0.42-0.45 per word, i.e. about
0.10 per rune. If the inserted rune IS the repair (a null written on collision), the insertion rate is the collision rate: 3x too few extra runes and per-rune scaling (R2). If the
per-word null IS the T rune, every null at word position >= 6 is a hit: about 1.5x too many hits (R5). A rule where 100% anti-repeat plus a per-word null not seen by the check
gives the residual doublets (phase 47's B) ties (1) and (3) together without a separate q. So the expectation was: (1)+(2) from the repair, (3) from a per-word null, and no single trigger
for both. Candidates, each simulated exactly as specified in the script header (c = p + k, k flat random, English digraph plaintext, LP2 layout):

| rule | doublet rule | T relation | extra rune | free rate |
|---|---|---|---|---|
| R0 | q 0.81, uniform repair | none | none | none (reference) |
| R1 | q 0.81 | repair writes T(c-6) in-word (phase 25 M1) | none | none |
| R2 | q 0.81 | the repair is a NULL T(c-6), plaintext re-encrypted with the next key | the repair nulls only | none |
| R3 | q 1 | repair writes T(6 back in the real stream) | one null per word (prob r, uniform slot), added in a later pass, unseen by the check | r |
| R4 | q 0.81 | repair writes T(c-6) | one null per word, uniform slot, written in the flow and checked (never equals the previous rune) | r |
| R5 | q 1, uniform repair | the per-word null's value is T(c-6) | one null per word, later pass | r |
| R6 | q 0.81 | repair writes T(c-6) | a null before any plaintext rune with prob r (key-value event, inverted F-skip) | r |
| R7 | q 0.81 | repair writes T(c-6) | a check rune at the END of a word with prob r, checked | r |
| R8 | q 0.81, uniform repair | plaintext F at word position >= 6 written as T(c-6) | none | none |
Rates r are tuned only to LP2's number of words (2,896); q is fixed (0.81 from the doublet deficit, or 1 where nulls make the residual doublets).

**(d) DJU BEI.** The two copies are at section 0.13 offset 28 and at the very end of 0.15 (offset 3,310). A key restarting at section starts would need equal offsets, so it is not that.
Under any rule with a flat random key a word-aligned repeat of 5+ runes needs both a plaintext repeat and a key repeat: the simulations measure how often it happens.

## 2. Simulation (500 replicates per rule; `results/analysis/phase57_mechanism.txt`)

Positive controls inside the script (`selftest`): q 1 without nulls gives 0 doublets; the T repair at q 1 lifts in-word T hits above 60; nulls at r 1 shorten the word count by > 15%.
The null control is R0 (no echo, no nulls). Nine statistics are scored (z of LP2 against the rule's own replicates; combined chi2 = sum of z^2; P = share of replicates with a combined
chi2 at least as large; floor 1/501 = 0.002). LP2: doublets 63 in-word / 23 across, T hits 80 in-word / 401 across, best other affine lag-6 form 65, unigram chi2 26.4, bigram chi2 786,
max |z| of equality at lags 2-12 = 3.0, word-length G against the rule's pooled histogram (as a replicate would score), 2,896 words.

| rule | r | doublets in / gap | T in-word (z) | best other form | word-length G (z) | lag 2-12 max z (z) | chi2 | P | T hits by word length 7 / 8 / 9 / 10+ (LP2 8 / 21 / 20 / 31) | P(DJU-type repeat) |
|---|---|---|---|---|---|---|---|---|---|---|
| R0 uniform repair | - | 64.3 / 20.5 | 38.5 (+5.5) | 59.1 | 38.8 (+8.9) | 1.9 (+2.2) | 117.3 | 0.002 | 5.9 / 7.8 / 8.9 / 15.8 | 0.002 |
| R1 repair writes T | - | 64.5 / 21.1 | 67.8 (+1.1) | 59.2 | 39.1 (+8.8) | 1.9 (+2.0) | 84.7 | 0.002 | 10.4 / 13.6 / 15.8 / 28.0 | 0.002 |
| R2 collision -> null T | - | 63.9 / 20.7 | 75.0 (+0.4) | 64.3 | 34.2 (+8.0) | 2.0 (+2.0) | 69.6 | 0.002 | 6.0 / 12.7 / 15.4 / 40.9 | 0.002 |
| **R3** q 1 T repair + later-pass word null | 0.448 | 67.6 / 18.2 | 68.5 (+1.1) | 67.4 | 30.4 (+0.1) | 2.1 (+1.4) | **5.7** | **0.717** | 9.4 / 12.8 / 14.4 / 31.9 | 0.000 |
| **R4** T repair + checked word null | 0.448 | 60.1 / 16.9 | 76.6 (+0.3) | 67.0 | 30.9 (+0.2) | 1.9 (+1.9) | **6.7** | **0.643** | 10.8 / 14.9 / 15.7 / 35.2 | 0.000 |
| R5 word null = T(c-6), q 1 | 0.448 | 66.2 / 18.4 | 122.1 (-2.8) | 67.1 | 30.9 (+0.4) | 2.2 (+1.4) | 12.0 | 0.228 | **20.5** / 25.0 / 24.5 / 52.1 | 0.002 |
| R6 T repair + per-rune null | 0.107 / rune | 60.2 / 17.2 | 90.5 (-0.8) | 77.8 (-1.9) | 29.4 (+6.3) | 1.9 (+2.1) | 51.2 | 0.002 | 11.0 / 14.9 / 16.4 / 48.2 | 0.000 |
| **R7** T repair + end check rune | 0.448 | 57.6 / 19.1 | 71.6 (+0.8) | 67.0 | 30.3 (+0.4) | 2.0 (+1.9) | **6.4** | **0.647** | 8.5 / 13.4 / 15.3 / 34.4 | 0.000 |
| R8 plaintext F -> T | - | 63.7 / 20.9 | 44.6 (+4.1) | 59.1 | 37.5 (+9.2) | 1.9 (+1.9) | 106.3 | 0.002 | 9.1 / 8.9 / 9.5 / 17.0 | 0.000 |
Unigram and bigram chi2 are inside every rule's spread (z -0.0 to +0.4 and +0.7 to +1.0); T hits across gaps are 391-408 against LP2's 401 everywhere (z -0.3 to +0.5).

Reading:
- **Word length defeats every rule without a per-word extra rune** (R0, R1, R2, R8: G z +8.0 to +9.2). A per-RUNE event (R6, a key-value trigger such as an inverted F-skip,
  rate tuned to the word count) fails it too (G z +6.3): the extra rune is a word-level event, as phase 47 found for the histogram alone.
- **Three rules fit everything scored** (P 0.64-0.72, no |z| > 2): R3, R4, R7. All three are two-part: the collision repair writing T(c-6) (gives (1) and (2), as phase 25) plus one
  null in about 45% of multi-rune words (gives (3)). R3 needs no separate repair probability: 100% anti-repeat plus a null that the check does not see leaves 86 doublets
  (LP2 86), so the "81%" is then an artifact of the nulls (phase 47's point, now with the T relation in the same model).
- Where the null sits (uniform slot, R3 / R4; word end, R7) and whether the check sees it (R3 vs R4) are NOT separated by the nine scored statistics; two side predictions (below) separate them.
- **No single trigger does both.** The null-on-collision (R2) is the right rate for the T relation but a per-rune, 3x too small insertion (G z +8.0). The per-word null that IS the
  T rune (R5) gets the lengths but 1.5x too many T hits (122 vs 80) and puts them in 7-rune words (20.5 vs LP2 8; every null at slot 6 of a 7-rune word is a hit): rejected by
  the profile (the 7-rune bin is unscored, but 8 vs 20.5 is about -2.9 sd).
- The plaintext-F rule (R8) adds only 6 hits over R0 (44.6 vs 38.5): English F at word positions >= 6 is far too rare, as phase 25 said.
- The unscored section spread of the T hits (hits over in-word lag-6 pairs per section) is 1.4 for LP2 against 6-7 for every rule (LP2 more uniform than 97-99% of replicates).
  Phase 54 reported section heterogeneity (p 0.0005) with a different statistic (per-section shuffle expectations); not reconciled here.
- The lag 2-12 maximum |z| of LP2 (3.0) is at about the 97th percentile under every rule (z +1.4 to +2.2): not rule-specific (the community's distance-11 dip, if real, is not made by any of these rules).

**Two side predictions that split R3 / R4 / R7** (added after the first table; the predictions and LP2's values come from the same run; numbers from the final 500-replicate table): (i) R3's nulls come in a later pass, so a T pair that straddles a null appears at lag 7: R3 predicts **34.5 +- 6.9** in-word lag-7 T hits, LP2 has **22**
(R0 22.1 +- 5.7, R4 25.7 +- 5.6): R3 is about -1.8 sd off. (ii) An end check rune is never a T hit, so R7 predicts fewer hits that end on a word's last rune: **24.0 +- 5.0**,
LP2 **32** (phase 54: an excess, 32 vs 20.1), R4 **30.9 +- 5.8**, R1 28.4, R0 16.1: R7 is about +1.6 sd off. **R4 is the only rule inside 1 sd on both**: the null is written in
the flow (checked against its neighbour, seen by the anti-repeat rule), at any slot of the word; neither split is decisive alone (about 2 sd each).

**DJU BEI.** A word-aligned repeat of an adjacent word pair of 5+ runes appears in at most 1 of 500 replicates of any rule (P <= 0.002; LP2 has one). With a flat key such a repeat needs
the same plaintext under the same key segment, and the copies are at different offsets (0.13 @ 28, 0.15 @ 3,310), so neither a section restart nor any of these rules gives it.
It stays outside the mechanism: a deliberate copy (the book's last words echoing an early phrase), a key segment reused for a repeated phrase, or a 1-in-500 accident.

## 3. The decryption search the best rules imply, planted control, one-window pilot (`work/phase57_pilot.py`)

R3 / R4 / R7 leave the key unconstrained (a flat key fits). A search therefore needs a key family, and the repository's widest one is the chanscreen v2 library (1,439 number streams,
both signs, every offset) with the anti-repeat repair channels hold / spend / skip5 / coin. The mid-word arc (`backward_mid.rs`, phase 51) already models R3 / R4: one interior null in
42% of words, invisible to the anti-repeat rule, repair rune uniform. The T-valued repair costs it nothing (a repair rune carries no plaintext in either reading, and the engine scores it
as 1 of 28 others whatever its value); R4's checked, visible null is the one point the engine does not model. R7 (end check rune) is phase 24's edge arc (`nullf`), pilot-negative before.
No new engine was built: the R4 plants test whether the existing one recovers the rule as specified here.

**Positive control** (12 plants: hold / spend repair x Cicada / English held plaintext x 3, library key at a random offset, +1 / -1 sign, nulls in 45% of words at an interior slot, checked
against the previous rune and visible to the check, repair writes T(c-6) in-word; 0-3 T-valued repairs per 300-rune window, 21-29 nulls): **12 / 12 detected at n 150 and at n 300,
true cell within 3 nats of the global best 12 / 12; band min / median 57.9 / 73.6 (n 150) and 119.5 / 155.2 (n 300)** against T300 = 29.8.
**Null control**: the matched iid-key plant (same layout, random key) searched in the true stream at every offset / sign / channel: max -18.0 (n 150), -55.8 (n 300).

**LP2 pilot**: section 0.15 @ 0, n 150 (the section with the most T hits, 20; not the window of phase 51's pilot, 0.7 @ 0), page-safe word starts of `lp_mask.py`, full library,
both signs, every offset, hold / spend / skip5 / coin, decoder nu 0.42, 3 workers at below-normal priority, **1.61 CPU-hours: 106,626,192 cells, max S_guard -4.88**
(`sha512-ctr mod :0x7A35090F`, +1, hold, offset 18,661); 0 cells >= 0, so nothing to recompute or verify. That is 34.7 nats below T300 and 62.8 below the weakest R4 plant at n 150.
Caveats: T300 was frozen for n 300; at n 150 the whole-library null tail of a real window is not measured (the matched single-stream null is -18.0, phase 51's n-150 ladder nulls
-15 to -18), so -4.9 is not a calibrated p-value, only "far below every plant". One window of about 86 at n 150; library streams only; one interior null per word; R4's checked,
visible null is not modelled by the decoder (the plants show it does not matter at these sizes).

## 4. Verdict

- **Best rule: R4** (combined chi2 6.7, P 0.64 on nine statistics, 500 replicates; R3 and R7 fit the nine equally, chi2 5.7 / 6.4, but miss one side prediction each by 1.6-1.8 sd):
  with probability 0.81 a would-be doublet is repaired by writing T(c-6) = 24 - 2 c(-6) when the rune 6 back is in the same word (else a uniform other rune), and ONE null rune,
  never equal to its left neighbour, is written at a uniform slot in about 45% of multi-rune words. It reproduces constraints (1)-(4) together within noise. It is two rules, not one.
- **The constraint that defeats every single-trigger rule is the word length**: the extra rune is per word (a per-rune trigger fails, G z +6.3) and about 3x more frequent than
  collisions (0.10 vs 0.034 per rune), so a null written on collision is too rare (G z +8.0), and a per-word null that is itself the T rune makes 1.5x too many hits and puts them in
  7-rune words (20.5 vs 8). The doublet deficit and the T relation share one trigger (the collision), the word-length excess needs another.
- **DJU BEI is not produced by any rule** with a flat key (P <= 0.002); it needs a repeated key segment or a deliberate copy.
- **Pilot**: the search these rules imply (library streams under the mid-word arc) recovers 12 / 12 R4 plants and finds nothing in 0.15 @ 0 (max -4.9 vs T300 29.8). Together with
  phase 51 (0.7 @ 0) and phase 24 (edge arc), two windows are negative; the key family, not the cipher structure, is what is unknown.
- Level: simulation of stated rules (Level 1); a fit is not evidence that Cicada used the rule. Not tested: structured keys (a book or a stream) inside the simulation, plaintexts other
  than English digraph spelling, rules with two parameters, the T map's constant as a key-dependent value, a check rune whose VALUE is a function of the word (only its presence is
  modelled), more than one null per word, the community's distance-11 dip.

**Most promising next test**: DJU BEI as a key-reuse probe. No rule with a flat key makes it (P <= 0.002); if it is the same plaintext under a reused key segment, the key holds the
same 6 values (up to sign) at two places separated by about the plaintext distance between 0.13 @ 28 and 0.15 @ 3,310 (6,395 cipher runes apart, about 5,800 key steps once R4's ~10% nulls are removed). That is a
cheap scan of every library stream (and any candidate book) for repeated 6-grams at that separation, with a planted control (a stream with a planted repeat) and a null (shuffled
streams). The mid-word campaign (about 260 CPU-hours) remains the full search these rules imply; with R4 a decoder could add the T sites as a keyed check (at a true T repair,
c(j-1) - k(j) is the lost plaintext rune).
