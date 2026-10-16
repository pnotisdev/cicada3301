# Phase 4 item 3 – crib-driven analysis and constraint solver (2026-10-16)

**Result: negative.** The one-rune-word and word-pattern cribs rule out several key models outright. No periodic
key and no reuse of the same key was found.

Tools: `work/crib.py` (dictionary, deductions, scans), `work/cribsolve.py` (constraint solver),
tests in `tests/test_crib.py`.

## Deductions from the cribs (independent of any key family)
| Model | Test | Result |
|---|---|---|
| Same plaintext word → same cipher word | distinct 2-rune cipher words: 445 of 621 (a random key gives 439, deterministic encryption about 28) | ruled out |
| One key value per word | doublets inside words: 0.62% (a word-level shift keeps English's 2.85%) | ruled out |
| Key set by position inside the word | the 99 one-rune words use all 29 runes (the model allows 2; 318 before the 2026-10-16 word-wrap fix) | ruled out |
| Key restarts each line or page | same-position coincidence 3.48% / 3.46% (reuse would give 6.2%) | ruled out |

## Scans for key reuse (FFT coincidence counting)
- **S1, periodic key or reuse within a segment, every lag 2–6000.** Best z = +3.6, or +3.9 when allowing up to
  15 skips of drift. Shuffled controls reach +4.0 and +3.7. No signal.
- **S2, the same key in two segments, every pair and offset.** Best z = +4.5. The shuffled control reaches +5.0.
  No signal.

## Constraint solver
Words are assigned most-constrained-first, the key values they imply are propagated, and words with no dictionary
fit become wildcards (forced only, never branched on). Depth-first branch-and-bound handles small problems and a
beam search (width 100–200) handles large ones.

On synthetic tests:
- Periodic L = 37 over 600 runes: 100% recovered in 0.3 s. A wrong period has no consistent solution.
- Periodic L = 99 over 1,200 runes (beam): 94% recovered and 8% of words unexplained. A wrong period leaves 70%.
- Periodic L = 1322 over 3,316 runes (beam): −2.43 per rune and 8% unexplained. A wrong period gives −5.28 and 37%.
- Two texts sharing one key over 300 runes (two-time pad, beam): 87% recovered.

## Applied to the strongest scan candidates
- **Key reuse, the top 5 segment pairs and offsets:** −4.0 to −4.6 per rune. A true shared key gives −2.4 and a
  wrong offset −4.05. Gibberish.
- **Periodic, the top 12 lags × all long-enough segments × Atbash on/off (76 runs):** all at wrong-period level.
- **Segment 0.15 at L = 1322 looked better at first. That was an artefact:** the beam had a 300 s time limit, and
  under full CPU load it stopped early, so undecided words did not count as unexplained. Rerun to completion
  against matched controls:

| Run (3,316 runes) | Score per rune | Unexplained |
|---|---|---|
| synthetic, true period | −2.43 | 8% |
| synthetic, wrong period | −5.28 | 37% |
| real 0.15, L = 1322 | −5.00 | 34% |
| real 0.15, L = 1350 (not flagged by the scan) | −5.15 | 35% |
| same word structure, shuffled runes (2 seeds) | −5.08 / −5.11 | 35–36% |
| same word structure, random runes (2 seeds) | −5.04 / −5.14 | 36% |

The time limit is now off by default, and `Problem.quality()` counts only words that were actually decided.

## What is still not covered
- Keys that change in ways other than repetition, for example a key that depends on the plaintext.
- Periodic keys combined with the collision-skip rule beyond the drift tolerance of the scan (about 15 skips).
