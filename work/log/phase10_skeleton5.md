# The period-5 twist skeleton against LP2 (2026-10-17, 22:40)

Scope: LP2 sections 0.7-0.15. **Nothing in LP2 is solved.** An outside LLM (third-party text, re-implemented here, not run as sent) answered the word-internal result of `phase10_echo_position.md` with a 'forced skeleton': inside a word the
state cycles with period 5 (5 = 0 and 6 = 1 mod 5), the rune at in-word index j is T^(j mod 5)(M_w(p)) with T(x) = 24 - 2x (mod 29) and M_w a per-word affine key (W1: from the word's Gematria sum; W2: from its first and last rune),
plus a collision rule that applies T. Whatever M_w is, the skeleton makes a prediction at EVERY lag: for a pair inside a word with equal plaintext runes, c_i = T^d(c_(i-L)), d = (in-word index of i) - (in-word index of i - L) mod 5
(L = 5: equality; L = 6: the relation c' = 24 - 2c). The relation is fixed in advance (no look-elsewhere), and the excess is about P(equal plaintext runes at that distance inside a word) - 1/29 per pair.

`work/families/skeleton5.py` -> `results/analysis/skeleton5.txt`: hits of c_i = T^d(c_(i-L)) over the within-word pairs of LP2 for L = 1..12 against 100 shuffles inside sections; plants = the proposal's W1 written out again, on English
words, 10 each, at p = 1.0, the proposal's own point (p = 0.9, qT = 0.15) and p = 0.7, each against the p = 0 plant on the same text (so pair counts match). The strength of each setting is fitted to lags 5 and 6 alone.

| lag | pairs | LP2 excess (z) | W1 at the strength fitted to lags 5, 6: predicted | z of (LP2 - prediction) |
|---|---|---|---|---|
| 3 | 4,882 | +3.0 (+0.24) | +57 to +62 | -4.4 to -4.8 |
| 4 | 3,237 | -1.1 (-0.10) | +44 to +46 | -4.1 to -4.3 |
| 5 | 2,105 | +32.9 (+4.00) | fitted | |
| 6 | 1,290 | +29.6 (+4.68) | fitted | |
| 7 | 731 | +1.6 (+0.34) | +10 to +15 | -1.8 to -2.6 |
| 8 | 388 | -1.1 (-0.32) | +11 to +12 | -3.6 to -3.9 |

- **The skeleton is excluded.** It reproduces the two effects it was built from (by fitting their strength) but predicts equally large excesses at lags 3, 4, 7 and 8, where LP2 has none: lags 3 and 4 alone are about -6 sd together at the fitted strength, and about -3 sd
  at half the fitted strength (the fit uses the two selected effects, so it is a little too strong). Lag 2 has no prediction (English repeats at distance 2 inside words are not above chance). The lag-1 prediction (+170 to +330, observed +10.5) is not used:
  most of it comes from the proposal's own collision rule (T applied at a would-be repeat), not from the skeleton.
- **S concentration not produced.** The lag-5 S-S coincidences inside words: LP2 11 (shuffle mean 2.4); W1 plants 3.1-3.6, the p = 0 plant 2.3. The proposed 'window {S, M, B, E, O}' story is not what the plant does.
- **W3 (twist at in-word collisions, no classes) is not excluded by this test** (it has no skeleton). It needs the whole collision budget (a relation excess of 2.7% per pair against 0.81 x 3.45% = 2.8% available, so uA must be about 0.97), derives no S
  concentration (the proposal says so), and its 'sharp' kill rule (no relation site at a surviving doublet) has no power: even all 86 doublets would carry about 2.3 relation sites at 2.7%.
- **Net:** a word-aware mechanism has to explain lag 5 (S) and lag 6 and nothing at lags 1-4, 7-12 inside words. A per-word periodic key does not; the repository's earlier 'alphawalk' also matched lag 5 only.

Caveat: the plants use English from `work/ref` with its own word-length structure; the per-pair excess rates are scaled to LP2's pair counts. The lags 5 and 6 effects themselves keep their look-elsewhere P of 0.005-0.010.
