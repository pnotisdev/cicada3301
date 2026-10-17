# Two-tap echo mechanisms A and B: what LP2 can and cannot say (2026-10-17, 23:20)

Scope: LP2 sections 0.7-0.15. **Nothing in LP2 is solved.** After the period-5 skeleton was excluded (`phase10_skeleton5.md`), an outside LLM (third-party text, not run as sent) proposed two two-tap mechanisms: A, a ciphertext echo
inside words (copy of the rune 5 back at rate q5, S after S at qS, T(rune 6 back) at q6, T(x) = 24 - 2x) and B, a rewrite of plaintext repeats at distances 5 and 6 as pairs (y, y) / (S, S) / (x, T(x)). Both put structure only at the
distances 5 and 6 inside words, so the controls that killed the skeleton (nothing at other lags, nothing across boundaries) pass by construction.

**What the repository can test.** A and B apply the echo to any rune, so the excess should be spread evenly over the 29 source runes. `work/families/echo_values.py` -> `results/analysis/echo_values.txt`: Q = departure of the per-source-rune
hit excess from an even spread, against 200 shuffles and 100 plants of the uniform echo at the observed within-word rate.

| effect | Q in LP2 | uniform-echo plants: mean / 95th pct | P(plant Q >= LP2 Q) |
|---|---|---|---|
| lag 6, c' = 24 - 2c | 33.7 | 29.4 / 47.2 | 0.25 |
| lag 5, equality (all source runes) | 41.9 | 27.0 / 40.0 | 0.03 |
| lag 5, equality without source rune S | 24.3 | 25.6 / 38.7 | 0.52 |

I expected the 'three pairs drive the lag-6 relation' fragility to contradict the even spread; it does not (counts per source rune are 1-7, too small). The lag-5 excess is concentrated only because of S (11 hits against 2.4), which A and B give a separate branch.
**Neither mechanism is excluded; neither is supported beyond the fit.**

**Why they do not help.** (1) Each has three free rates pinned by three observed numbers (lag-5 coincidences, S-S pairs, lag-6 excess), so a plant that reproduces them tests nothing; the 'derived' S = 15 (= 2^-1 mod 29) and (a, b) = (27, 24) are the observed values renamed.
(2) They describe the 1.5-2.7% anomalies and leave the other 97% of the cipher, the key, as the unsolved additive layer; the library screens (kscreen: planted keys at IoC 1.6-2.0 against a 1.40 threshold) tolerate a few percent of replaced runes, so nothing already run is invalidated
and a 'tap-aware decoder' would only add what those screens do. (3) A's echo replaces plaintext runes by copies, so the plaintext at those positions is gone. A tap-aware decoder is worth building only if a key family for the base layer exists.
(4) A and B are not separable with LP2 alone: B's pair overwrites and A's copies have the same visible statistics.

Conclusion: the anomaly-explaining line has reached the point where further mechanisms are untestable on LP2; the useful constraints it produced are `phase10_echo_position.md` (word-internal, position-uniform) and `phase10_skeleton5.md` (nothing at other lags).
