# Phase 32: a drift-aware statistic for H2 (tableau / transition-table ciphers): spec and gate

Nothing in LP2 is solved. LP2 was NOT touched; this is a prototype gated on synthetic plants, 1 core.
Code `work/h2_drift_decoder.py` (new; imports `work/book_key_flatness.py` read-only and mimics `work/book_key_decoder.py`, which it does not modify).
Outputs: `work/log/phase32_h2_drift_output_729_1524.txt`; the n = 300 and diagnostic runs are quoted below.

## Spec
Model (H2a, `docs/HYPOTHESES.md`): c_i = T[v_j][p_i], v a library stream (range R), T an unknown tableau (any 29 permutations, additive tableaux
included), key pointer j advancing one per rune plus a skip when the anti-repeat rule fires (q = 0.81).

- **Integrated out:** the tableau. At the right stream and offset the ciphertext runes under each key value are a *relabelling* of the plaintext,
  so a class's rune counts n_a are a permuted plaintext histogram. The class is scored by the sequential Dirichlet-multinomial predictive
  29 (n_a + alpha) / (n + 29 alpha) against uniform, alpha = 1.22 (chosen so E sum theta^2 = 0.061, English's sum f^2). This is invariant to T and
  to any key-value -> row map and needs no plaintext model. (The phase 23 beam integrates a *shift* per class, 29 hypotheses; this integrates a
  permutation, far more freedom: that is the price of generality.)
- **Beam tracks:** the key pointer, +0/+1/+2 per rune, skip cost ln(0.81/29) each, the best `per_ptr` = 8 histories per pointer, 64 states, first 8
  pointers free (stride 8 per screen), as phase 23. State = R x 29 class counts (int16).
- **Cost:** O(1) per branch (no logsumexp over 29 shifts, unlike phase 23); measured 26 ms (n = 300), 67-117 ms (729), 130-148 ms (1,524) per decode on 1 core,
  i.e. ~0.09 ms per rune per decode, ~0.011 ms per rune per stream-offset at stride 8 (about the same as phase 23's 0.033 ms/rune/offset divided by three; the EM
  stage is not built). For R > 64 the state would be R x 29: use hashed bins or the pair-count form.
- **Old statistic** (work/proposals/h2_coincidence): pairs with equal key value and equal cipher rune, no drift, z against 40 random offsets.

## Gate (plants: Emerson digraph runes, random permutation tableaux or additive tableaux, skip rule q = 0.81, streams: uniform R = 29 and primes mod 29;
threshold mu + 4.5 sd of 300 uniform-key ciphers against random offsets; 24 plants per cell)
| window | tableau | stream | new beam power | path accuracy (median; >= 0.9) | nulls above threshold (wrong offset / uniform key) | old coincidence z > 4.5 |
|---|---|---|---|---|---|---|
| 300 | random permutations | uniform | 0/24 | 0.18; 0 | 0 / 0 | 0/24 |
| 300 | random permutations | primes mod 29 | 1/24 | 0.00; 1 | 0 / 0 | 0/24 |
| 300 | additive | uniform | 1/24 | 0.29; 0 | 0 / 0 | 0/24 |
| 300 | additive | primes mod 29 | 0/24 | 0.02; 0 | 0 / 0 | 0/24 |
| 729 | random permutations | uniform | 1/24 | 0.05; 1 | 0 / 0 | 0/24 |
| 729 | random permutations | primes | 2/24 | 0.03; 0 | 0 / 0 | 0/24 |
| 729 | additive | uniform | 4/24 | 0.02; 0 | 0 / 0 | 0/24 |
| 729 | additive | primes | 6/24 | 0.02; 1 | 0 / 0 | 0/24 |
| 1,524 | random permutations | uniform | 2/24 | 0.02; 0 | 0 / 0 | 0/24 |
| 1,524 | random permutations | primes | 4/24 | 0.00; 1 | 0 / 0 | 0/24 |
| 1,524 | additive | uniform | 3/24 | 0.01; 0 | 0 / 0 | 0/24 |
| 1,524 | additive | primes | 4/24 | 0.00; 0 | 0 / 0 | 0/24 |
Diagnostics (6 plants each, uniform stream, random permutations; z = against 15 wrong offsets of the same ciphertext):
- n = 3,316, beam 64: 2/6 locked (path accuracy 0.85, z +35); the other 4 lost the path (accuracy ~0). n = 6,000: 2/6 (z +59 to +70).
- n = 1,524 with beam 64 / 512 / 2,048 (per-pointer 8 / 64 / 256): locked 2/6, 0-1/6, 1/6. A wider beam does not help.
- **Sanity (no skip rule, q = 0):** n = 300: path accuracy 1.00, beam z +3.8 to +17.5, old coincidence z +4.3 to +8.4 (8/8); n = 729: beam z +15 to +36,
  old +10 to +23 (8/8). So the code is right and the old statistic works without skips (it reproduces the earlier z ~ 40 at 1,600 runes); **with the skip rule
  the old statistic is dead (z ~ 0 at every length) and the new beam recovers only when it locks on in the first ~300 runes.**

## Why it fails and what that costs
Without the skip rule the evidence rate is 0.04-0.12 nats per rune (n = 300-729); the skip rule costs ~0.1 nats per rune, and in the first stretch the classes hold
only a few runes each, so early skips are indistinguishable from stays and the path is lost (accuracy ~0 in the failures). Lock-on is a coin flip decided by the first
~300 runes, independent of the beam width. Per class (R = 29) the information needs n of several thousand runes; R = 256 is worse by 9 times. The hypothesis in
HYPOTHESES.md that H2 is "trackable" (0.4 nats per class of plain English) assumed classes already populated; with R = 29 and n = 1,600 it is ~55 runes per class
at the end and ~0 at the start. The shift-structured decoder (phase 23) is better placed because the 29 class distributions share one shape.

## Verdict
- Gate numbers: power 0-6/24 at 300-1,524 runes (nulls 0 above threshold; false positives not the problem), ~1/3 lock-on at 3,316-6,000 runes; old statistic 0/24 everywhere with the skip rule.
- Cost for a campaign: ~0.011 ms per rune per stream-offset; a 1,600-rune window per section x thousands of library streams x ~1e4-1e6 offsets is 1e2-1e4 core-hours
  at power under 0.2. **Not worth a campaign as built.** Level 1 (negative for this statistic and these lengths).
- What would change it: (i) a way to start the beam where the classes are full, e.g. run it backwards from the section end or from a crib, or seed with known plaintext
  words; (ii) a smaller effective R (key values folded to ~7 classes) at the price of a weaker model; (iii) a stream whose offset is already constrained (a skip-free
  segment of LP2 would give the 4-8x higher z of the q = 0 rows). None is built. H2 stays open and untested on LP2 (unchanged).
