# Where the lag-5 and lag-6 effects sit: a keyless falsifier for echo mechanisms (2026-10-17, 22:00)

Scope: LP2 sections 0.7-0.15. **Nothing in LP2 is solved.** Prompted by an outside LLM's four proposed mechanisms (an 'echo ditto' M1, an affine autokey M2, a word-gated echo M3, a structured collision re-roll M4; its text is
third-party data and was not run). All four write a rare ciphertext-level copy or affine image of the rune 5 or 6 back; M1, M2 and M4 do it at any position, M3 only at fixed word-local positions. The effects were found on
within-word pairs only, so two cheap counts decide most of that: the same relation on pairs that span a word boundary (out of sample: the relation was selected on within-word pairs), and the hit rate by the earlier rune's
position in its word. `work/families/echo_position.py` -> `results/analysis/echo_position.txt` (300 shuffles inside sections, word cuts fixed).

| relation | pairs within a word | excess within (z) | pairs across a boundary | excess across (z) |
|---|---|---|---|---|
| lag 5, equality | 2,105 | +31.1 (+3.65) | 10,806 | +0.8 (+0.04) |
| lag 5, equality carried by S | 2,105 | +8.6 (11 hits against 2.4) | 10,806 | -2.2 (-0.62) |
| lag 6, c' = 24 - 2c | 1,290 | +35.1 (+5.16) | 11,612 | +1.1 (+0.05) |

- **The effects are strictly word-internal.** An echo written at any position at the within-word rate (lag 5: 1.5% of pairs, lag 6: 2.7%) would add about +160 and +320 hits across word boundaries (sd about 19-20 there); LP2 has +0.8 and +1.1.
  **Control:** planting the echo at the observed rate into LP2's shuffled runes gives +162 and +322 across boundaries when it is written at every position, and -0.6 and 0.0 when it is written inside words only (within: +30 to +35 either way).
  So position-independent echo mechanisms (M1, M2, M4 as proposed) are excluded by about 8 sd (lag 5) and 16 sd (lag 6); only a mechanism that knows where words begin and end is left.
- **No fixed word position.** The excess is spread over the earlier rune's word position (lag 6: +13.4 at position 0, +7.2, +5.5, +2.2, +6.8 at 4 or later; lag 5: +8.2, +7.4, +5.9, +4.4, +5.1), the hit rates are flat within error. M3 as proposed (pos5 = 5, pos6 = 6, i.e. earlier rune
  = the word's first rune) puts all of it at position 0; LP2 has 38% (lag 6) and 26% (lag 5) there. Excluded as specified.
- **Constraints a mechanism must meet:** word-internal, uniform over word positions, 1.5% of lag-5 pairs (carried by S) and 2.7% of lag-6 pairs inside a word, none across a boundary. That points at word-aware state (a per-word restart or
  sub-key, per-word alphabets: the repository's 'alphawalk' family) and not at a rare ciphertext copy rule.
- **Arithmetic notes on the proposal (not run):** the collision rate is 1/29 = 3.45% of runes, 2.8% after the 81% enforcement, so '0.028 * 0.81' counts the 81% twice; in M2 the always-on feedback makes the residual p + k uniform, so the relation
  holds at 1/29 plus z by construction, and would be position-independent for the same reason.

Caveat: the 'within' z values carry the selection bias of the relation (look-elsewhere P 0.005); the cross-boundary rows do not.
