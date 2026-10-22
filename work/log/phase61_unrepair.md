# Phase 61: un-repair via lag-6 sites (2026-10-22)

Nothing in LP2 is solved. Script `work/phase61_unrepair.py` (outputs `results/analysis/phase61_*.txt`, `results/analysis/phase61_*.json`).

## 1. Plan (written before any run)

Idea 1a: under mechanism R4 (phase 57) a would-be doublet c_i == c_{i-1} is repaired with p 0.81 by writing T(c_{i-6}) = 24 - 2 c_{i-6} when the rune 6 back is in the same word.
A within-word site with c_i = T(c_{i-6}) (detector D) would then mark a repair whose pre-repair rune was c_{i-1}. About 35 of LP2's 80 D sites are expected to be repairs, so D has
to be tested on simulated text first.

What can be gained is bounded before running anything: R4 has about 0.028 repairs per rune (about 360 in LP2), but a T-valued repair needs word position >= 6, so D can see only a
small share of them (the 80 sites, about 35 true). In a 300-rune window that is about 1 D site, about 0.5 of them true. Each true site is worth at most ln(P(y = T | repair) /
P(y | repair, uniform)) = ln 28, about 3.3 nats, to a decoder that knows the mechanism. T300 is 29.8 and plant bands are 120-155 nats at n 300. So the expected gain is of the order of
one nat; the run has to say whether it is even measurable.

Steps:
1. **Detector on simulation** (`sim`): phase 57's simulator (R4, rate 0.448 from the phase 57 table, 250 texts of 12,956 runes, LP2 section layout) with the true repair positions
   recorded (`simulate(..., want=True)` returns T-valued and all repair flags; default call unchanged). D = within-word sites with c_i = T(c_{i-6}). Precision = share of D sites that
   are T-valued repairs; recall of T-valued repairs (1 by construction) and of ALL repairs; D count per text against LP2's 80.
2. **Two uses on plants with a known key** (`plants`): plants as in phase 51 (held plaintext cut at LP2 word lengths, library stream, hold / spend, +1 / -1, English / Cicada) except that
   the repair rune is T(c_{i-6}) in-word (R4) and, for the Rust engine, 45% of words carry one interior null. Null = the matched iid-key cipher (same layout, same repair rule) searched
   in the true stream, as in phase 51. A window without a D site is unchanged by either use, so only windows with >= 1 D site (decided from the cipher alone) are searched; the
   change in the all-window mean is then (share of windows with D) x (change in that stratum).
   (a) un-repair: c_i := c_{i-1} at D sites; scored with the mid engine S_guard (true-sign / true-channel band maximum, matched-null winner) at n 300 and n 150, and the oracle-key
       IoC of the decrypted window against 1,000 random-key decryptions.
   (b) guided decoding: a small Python decoder (exact hold / spend semantics of `reference_mid.py`, no nulls, cross-checked against the Rust base engine) in three variants:
       raw, `hard` (D sites forced to be repairs: the genuine path is removed there) and `aware` (R4 likelihood: in-word position >= 6, repair rune must equal T(c_{i-6})).
       Plants without nulls (so the decoder is exact); the gain is therefore an upper bound for LP2 where nulls add ambiguity.
   Decision: useful only if (true score - null max) improves clearly and reproducibly (paired differences over plants, sign test) over the raw ciphertext.
3. LP2 windows only if step 2 shows a real gain. Otherwise: not run, and that is the result.

## 2. Results (all numbers from `results/analysis/phase61_sim.txt`, `phase61_plants.txt`; raw records in `phase61_rust/` (160 plants) and `phase61_py/` (96 plants))

**Controls.** `python work/phase61_unrepair.py test`: the Python decoder reproduces the Rust base engine (lnL max error 1e-13, lnU identical, hold and spend, both signs); in 40 plants every
T-valued repair is a D site and the literal c_i := c_(i-1) restores the pre-repair rune. The simulator is the null of the detector (its repairs are known); the matched iid-key plant is the null of the scores.

### 2.1 Detector D on the R4 simulator (250 texts of 12,956 runes, LP2 layout, rate 0.448, q 0.81)

| quantity | value |
|---|---|
| D sites per text | 75.4 +- 11.6 (LP2 80, z +0.39: the simulator matches LP2) |
| of which true T-valued repairs | 32.7 +- 6.7 |
| **precision** | **0.433** (per-text 5-95%: 0.34-0.53); 42.8 false sites per text (chance matches) |
| recall of T-valued repairs | 1.000 by construction (every T-valued repair is a D site) |
| **recall of all repairs** | **0.100** (327 repairs per text, 0.0252 per rune; only 10% have a word position >= 6, so only 10% can be T-valued) |
| per 300 / 150-rune window | D 1.75 / 0.87, true 0.76 / 0.38; 83% / 53% of 300-windows have >= 1 D / >= 1 true site |

So D can touch at most 10% of the repairs in a window, and 57% of what it flags is not a repair.

### 2.2 Plants (T-valued repairs; library streams <= 2,100 runes, hold + spend, +-1, English / Cicada plaintext; matched iid-key null in the same stream; paired differences)

**(a) un-repair** (c_i := c_(i-1) at D sites), mid engine S_guard, 160 plants with 45% interior nulls, decoder nu 0.42; windows with a D site 138 (n 300) / 93 (n 150):

| n | true-key band (nats) | matched-null winner | separation (true - null) |
|---|---|---|---|
| 300 | -2.20 (se 0.39), 48 up / 89 down | +0.64 (se 0.26) | **-2.8** |
| 150 | -1.92 (se 0.46), 37 up / 55 down | +0.60 (se 0.24) | **-2.5** |
| 300, windows with a TRUE site (101) | -1.48 (se 0.43) | | |

Raw bands: median 143.6 (n 300) / 69.5 (n 150), raw null winners -117.8 / -55.6, T300 = 29.8. Oracle-key IoC (n 300, 138 windows with a D site): plaintext 0.0626, raw 0.0610, un-repaired 0.0609
(change -0.00003 +- 0.00004), random-key null max 0.0376. Fixing EVERY true repair (the upper bound, not available to D) gives 0.0626 (+0.0016, 1.8 null sd): the repairs cost 0.0016 of an IoC gap of 0.023, and D recovers none of it.

**(b) guided decoding**, Python decoder, 96 plants WITHOUT nulls (exact semantics; an upper bound for LP2, where nulls add ambiguity). Change of (true band - matched-null winner) against the same decoder on the raw ciphertext:

| variant | n 300 (96 plants) | n 150 (96 plants) |
|---|---|---|
| un-repair (a) | -2.95 (se 0.71), 27 up / 62 down | -1.65 (se 0.45), 25 up / 51 down |
| `hard`: D sites forced to be repairs | -9.81 (se 2.44), 38 up / 52 down | -3.75 (se 1.50), 34 up / 42 down |
| `aware`: R4 likelihood (in-word position >= 6: the repair rune must equal T(c_(i-6))) | **+6.46 (se 0.42), 93 up / 1 down** (band +1.62, null winner -4.84) | **+2.78 (se 0.31), 84 up / 11 down** (band +0.97, null winner -1.81) |

Raw separation in the same plants: band median 214.7 (n 300) / 107.6 (n 150), null winner -262.1 / -119.4.

### 2.3 Decision

- **Un-repair at D sites (use a) does not work; it loses.** It costs 2-3 nats of separation at n 300 and n 150 (Rust engine and Python decoder agree), leaves the IoC unchanged, and the
  forced-repair decoder (`hard`) loses 4-10. Reason: 57% of the D sites are chance matches, where the edit destroys a genuine rune, and a true site is only 0.38-0.76 per window; the engine already
  scores a repair rune at its true plaintext (c_(i-1) - key) through its repair path, so the edit adds nothing for the sites that are real.
- **What does help is the mechanism itself, not the detector:** the `aware` likelihood (R4: a repair rune at word position >= 6 is T(c_(i-6)), so the repair path is closed at every other
  position >= 6) raises the separation by +6.5 nats (n 300) and +2.8 (n 150) in 93/96 and 84/96 plants. That is real and reproducible, but small: the raw margin is 215 nats at n 300 against the
  hit level 29.8 (R4 plants in phase 57: 120-155 at n 300, 58-74 at n 150), and the planted-key recovery was already 12/12. It is an upper bound (no nulls in the decoder plants, the generator is
  the decoder's own model, one-stream null), it needs a change of `backward_mid.rs` (per-position repair-rune constraint; the Python decoder takes about 2.7 ms per hold cell against about 0.05 ms for the Rust engine, so a
  library scan with it would cost the order of 100 CPU-hours per window), and it assumes R4 is the true mechanism, which phase 57 only fitted.
- **Step 3 (LP2 windows) was not run:** no use shows a gain worth the engine change; the only gain is an engine-wide +3-6 nats of separation that would also lower the null tail, not a new window.

## 3. What is NOT excluded

Un-repair or guided decoding with a better detector (D uses only the lag-6 T value; a site's word position, the neighbours' letters, or a language model could raise the 43% precision); repairs of other
forms than T(c_(i-6)); nulls inside the guided decoder (only the Rust un-repair test has them); the whole-library null tail (single-stream nulls only); the `aware` likelihood inside the Rust engine
(+3-6 nats of separation, not built); windows with the other channels (skip5, coin). Level: simulation and plants (Level 1); nothing in LP2 was scored.
