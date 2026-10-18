# koan_sums — pre-registered close-out of the squares line

**Hypothesis, fixed in advance.** The 0.6 square's seven free parameters (the unexplained
seeds {809, 434, 312, 966, 1311, 204} plus the derived t = 1246) might be Gematria sums of
the 0.5 koan's plaintext (the page before 0.6, whose key was itself a transform of
CIRCUMFERENCE — "the process must be apparent" would point there).

**Family, stated in advance.** Inputs: segment 0.5's solved plaintext (the repo's KNOWN[5]
decryption), word segmentation from the transcription.

| Family | Quantity | Size |
|---|---|---|
| F1 | GP-prime sums of single words | ~190 (printed) |
| F2 | sums of two consecutive words | #words - 1 |
| F3 | clause sums ('.'-delimited) | ~8-10 (printed) |

Targets: the 0.6 square's free parameters {809, 434, 312, 966, 1311, 204} + t = 1246 (7
targets), and — as a looser check with its own count — the 13 distinct square values and
the 25 cells. Chance baseline: 200 shuffles of the word sums, same target check.

**Sanity checks (must pass for the run to count):** UOICE = 121, MASTER = 358,
CIRCUMFERENCE = 398, THE = 149.

**Verdict.** PASS if the sanity checks hold and the hit counts are printed against the
shuffled null. The conclusion (hits above chance or not) is the finding: above chance
revives the squares line; at chance it is closed for good.

**Cost.** seconds on CPU.
