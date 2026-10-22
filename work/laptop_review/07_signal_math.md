# 07 Math of the signal: which mechanisms make c(j) + 2 c(j-6) = 24 (mod 29) inside words? (laptop review, sub-session 7; local only)

Nothing in LP2 (sections 0.7-0.15, 12,956 runes) is solved. This file reasons about the lag-6 relation (`obs-lag6`, `lag6-dissect`, phase 25 / 54 / 56 / 57) and decides which mechanism families can produce it. Everything was read from files in the repository; the only computation was a handful of tiny keyless numpy scripts on LP2's own runes (about 20 CPU-seconds in total, 2 threads, below-normal priority, kept in the scratch area, not in the repo). Every number marked "my check" comes from them; each has its control or null stated. "T" below is the map T(c) = 24 - 2c (mod 29) on Gematria Primus indices (F=0).

## 0. Headline findings

1. **A pervasive key-side recurrence is dead; the residual is the proof, not the rate.** If the key obeyed k_j = -2 k_(j-6) + b inside each word (lagged-Fibonacci, period-6 key with multiplier -2, order-6 LFSR with all other taps zero), the cipher residual r = c_j + 2c_(j-6) - 24 equals p_j + 2p_(j-6) + const, an English-combination law, not a plaintext law (so the old `lag-feedback` plant, which was a ciphertext autokey with residual = plaintext, never tested THIS). My check, English digraph runes (28,461 in-word lag-6 pairs): the best cell has probability 0.0514 (next 0.0495, mean 0.0345), so at the best constant it gives 66.4 hits in LP2's 1,290 pairs (LP2: 80, -1.7 sd; chance 44.5). The rate alone does not kill it. The other 28 cells do: their chi-square against flat is 89.9 +/- 14.2 under the recurrence (200 draws of 1,290 pairs, random key, top cell dropped), LP2 has 36.5 (flat expectation 27 +/- 7.3). That is -3.8 sd below the recurrence and +1.3 sd above flat. Positive control for the statistic: the same simulation gives 89.9, i.e. it does detect a recurrence; random-key simulation reproduces the formula cell (0.0514 at the predicted cell). Caveat: English plaintext; a plaintext whose lag-6 combination were one spike on an otherwise flat background would need a fixed plaintext pattern AND a key relation (two coincidences), see section 2.
2. **No scalar-state generator can make lag-6 multiplier -2.** -2 is a quadratic non-residue mod 29 (29 = 5 mod 8 makes 2 a non-residue, 29 = 1 mod 4 makes -1 a residue; squares mod 29 are 1 4 5 6 7 9 13 16 20 22 23 24 25 28 and 27 = -2 is not among them). Any affine step x -> a x + b iterated six times has multiplier a^6, always a square. So T cannot be six steps of one LCG-like key step (k_j = a k_(j-1) + b), nor two steps of a lag-3 map. T is a cube: S(x) = 3x + 13 has S^3 = T (27 = -2, 13 x (1 + 3 + 9) = 169 = 24), so "three steps of a lag-2 map" is the only decomposition with a small lag; my check of the cell c_j = 3 c_(j-2) + 13 at in-word lag 2: 262 hits vs 250.1 expected (z +0.76, n 7,247). Killed.
3. **Not a statistical artefact of the null.** Exact Poisson-binomial tail of the 80 hits (per-pair probabilities from LP2's own unigrams, 1,290 pairs, mean 44.47): P(X >= 80) = 6.2e-7; times 6,496 (8 lags x 812 affine relations) 0.004, times 812 only 5e-4. Within-word shuffle (300 shuffles, max over 812 relations at lag 6): LP2 max z +5.33 vs null median 3.24, 95th 4.12, P 0.003 (one shuffle in 300 reaches it; floor 1/300). No other lag 1-12 is individually significant (P 0.09-0.92; lag 10 P 0.030, lag 12 P 0.087; across the 12 lags the best is about 0.3). Duplicate-word inflation is absent: 815 words of >= 6 runes, 815 distinct; hits on distinct words of >= 7 runes: 80 of 1,290 (unchanged). The word-length mix cannot matter: under a flat iid null the per-pair rate is 1/29 whatever the lengths (independence 44.49, within-word shuffle 45.68, R0 simulation 38.5 on shorter words: z +5.3 to +5.5 in every case).
4. **Direction and constant.** The relation is causal in direction: reverse form c_(j-6) = 24 - 2c_j has 44 hits (chance 44.5), forward 80 (my check; only 2 pairs satisfy both). The constant 24 is universal across sections: per section, T's count is first or tied-first in 5 of 8 sections with data, and the sum over sections of the best constant other than 24 is 85 vs a flat null 85.5 +/- 3.9 (P 0.59); sum of per-section maxima 86 vs 85.7 +/- 3.9. So the constant is not a per-section key offset.
5. **One loose flag from my grid (new, weak).** T counted at rune-lag 5 across exactly one word gap (same section): 7,369 pairs, 307 hits vs 254.2 expected, z +3.37 (+53). It is not "the separator counts as a cell" (that predicts +200 here and also +180 at lag 6 across one gap, observed +4, and at lag 4 across two gaps, observed -11). Over the 47 cells (rune-lag 1-12 x 0-4 gaps) a non-lag-6 cell this large has post-hoc P about 0.02. See lead L1.

## 1. Lead table

| id | lead | source | what it claims | already tested? | concrete test (positive control; null) | cost | prior |
|---|---|---|---|---|---|---|---|
| L1 | T across ONE word gap at rune-lag 5 (cell-lag 6 with the gap as a cell), 7,369 pairs, +53 | my check (T-cell grid over rune-lag 1-12 x 0-4 gaps); `segmentation-dependence` (equal pairs straddling gaps, lags 2-8, T not tested); `obs-lag6` ("zero excess across gaps" is rune-lag 6 only) | a weak lookback that sometimes crosses a gap; carried by plain word spaces (292 vs 241.0, z +3.34), clause dots 14 vs 12.2, line/page wraps irrelevant; 8 of 8 sections at or above expectation; 5 of 5 gap positions positive (z +2.1, +1.0, +2.5, +1.4, +0.5) | no | spec B below | seconds (keyless) + 0.5 CPU-h if R4 replicates are used | low: P about 0.02 after 47 cells, rate 0.007/pair is a quarter of the in-word rate, no mechanism |
| L2 | In-word T at lag 9 (14 vs 7.0, z +2.7, n 201) and lag 3 (192 vs 168.4, z +1.9) | my check, C2 table | odd multiples of 3 all positive: lag 3 +1.85, lag 6 +5.42, lag 9 +2.72, lag 12 +1.14 (1 hit, 10 pairs) | no (`lag-feedback` covers d <= 8 with 4 scopes but tests the residual chi-square, not the T cell at 3 and 9) | fold into spec B: same grid, same null | seconds | low: lag 9 top-of-812 is P 0.34, T cell alone P about 0.003 x 12 lags = 0.04; the excess RATE per pair (0.005 at lag 3, 0.0275 at 6, 0.035 at 9) is not constant |
| L3 | R4-calibrated T grid: simulate R4 (and R3, R7) replicates, compute the whole (rune-lag, gaps) T grid and the max over 812 at every lag | `work/phase57_mechanism.py` (500 replicates per rule exist; the grid statistics were never computed on them) | tells whether lags 3, 5, 9 and the (5,1) cell are R4-typical; R3 / R4 / R7 differ in lag 7 and word-final hits, maybe also in (g,k) cells | no | positive control: R4 with a planted gap-crossing lookback of weight w = 0.26 must give the (5,1) excess; null: R4 as specified (P(non-lag-6 cell >= 3.37 among 46) under it) | 0.5-1 CPU-h | low-med: costs little and makes the lag-7 and word-final side predictions less than 2 sd each sharper |
| L4 | T-site keyed check over a whole section (80 sites) | `phase57_mechanism.md` closing note (idea only) | at a true repair c(j-1) - k(j) is the lost plaintext rune: English-shaped (IoC 1.79) | no (never implemented) | spec C below | engine work, 1-2 days; CPU small | low: roughly 0.1-0.3 nats per site (my rough estimate, not computed), 1.9 sites per 300-rune window, so useless as a screen; only a whole-section verifier |
| L5 | Which coordinates does the repair live in? T is affine in GP INDEX order, not in the prime domain | my check C9; `prime-domain` | T mapped to prime values mod 29: best affine agreement of P[T(c)] with a P[c] + b is 7 of 29 vs median 5, 95th 8 over the 812 index-affine maps (T rank 50 of 812) | partly (`prime-domain` tested dense feedback, not this) | none needed; decoders keep GP index arithmetic mod 29 | seconds | n/a (supports the existing decoder coordinates) |
| L6 | Hybrid: key recurrence in a share s of words plus random elsewhere | derived, section 2 | closed form: hit rate 0.0345 + s (0.0514 - 0.0345) <= 0.0514 < 0.062 for every s <= 1 with English plaintext | no | none (closed form); would need a non-English plaintext with a spike law | 0 | very low |
| L7 | LCG / affine step key with T = a^d | derived (finding 2) | impossible for every even lag d (a^d is a square, -2 is not); for odd d a unique a exists (d = 3: a = 3 only in the sense S^3 = T, i.e. a lag-2 step applied three times, tested null: z +0.76) | no | none further; the d = 1, 3, 5, 7 cells are in the lag 1-12 scan (no T excess at lags 1, 3, 5, 7) | seconds | very low |
| L8 | Per-section constants | my check | universal constant 24 | no | done (finding 4) | seconds | n/a |

(L1, L2 rank "cheap and keyless, low prior"; L3 is the efficient follow-up; none changes the R4 picture.)

## 2. Algebra: what each mechanism predicts

Notation: c = p + k with k flat; hit = c_j = T(c_(j-6)); q = 0.81 enforcement, rate q/29 = 0.028 per rune; LP2 excess 0.0275 per in-word lag-6 pair (80 vs 44.5 on 1,290 pairs).

**Pervasive key relation k_j = a k_(j-d) + b.** c_j - a c_(j-d) - b = p_j - a p_(j-d). With a = -2, d = 6 the T relation holds exactly when p_j + 2p_(j-6) = t, a cell of the English combination law (max 0.0514, above). The residual has the combination's full shape; flat only if plaintext were flat. With more taps (order-6 LFSR) the residual combines 3 to 7 plaintext runes, near uniform, and the two-tap T relation then does not exist at all: a general LFSR gives NO lag-6 T relation. So the only variant that makes T is the degenerate two-tap one, and it is excluded by the flat remaining 28 cells (finding 1). It also does nothing for the doublet deficit.

**Plaintext-side cause.** With a flat iid key the residual c_j + 2c_(j-6) - 24 = (p_j + 2p_(j-6) - 24) + (k_j + 2k_(j-6)) is uniform whatever the plaintext. A fixed English pattern at distance 6 therefore cannot show in the cipher unless the key obeys a relation (see above) or the plaintext itself is autokeyed (flatness already excludes plaintext autokeys, G11 in `08_loose_ends.md`).

**Ciphertext autokey** c_j = p_j + 24 - 2c_(j-6): the residual is the plaintext (chi2/n 2.25 in the old plant, LP2 0.44) and F would be the hit rune; `lag-feedback`, `echo-mechanisms` exclude it, `obs-flat` (458 F vs 447) too.

**Period-6 key per word** k_j = k_(j-6): equal runes at lag 6 (phase 56 rule B: 54.6 vs LP2 32; no T). With multiplier -2 it is the pervasive relation.

**Collision-linked repair writing T(c_(j-6)) in the cipher stream, inside the word (R1, R4).** Rate per eligible pair = q/29 by construction (0.028), zero across gaps because the repair only looks inside the word, doublet deficit equal in words and across gaps because the trigger is the collision whatever its position. Positions j < 6 write something else (uniform): this is why the across-gap rune-lag-6 excess is zero. Profile: uniform per pair, so 2x chance everywhere (phase 56: R1 bins 10.4 / 14.0 / 16.1 / 28.2 vs LP2 8 / 21 / 20 / 31, chi2(6) 5.7, P 0.48); the 7-rune bin (8 vs 8.0 chance, vs 10-12 expected from the rule) is -0.8 to -1.2 sd.

**Same repair, lookback counted in the plaintext-aligned stream (R3's later-pass nulls).** An extra rune between source and target pushes the pair to cipher lag 7; fraction straddled about 0.45 x 6/(L+1) (about 0.3 for L = 8-9). Predicted lag-7 T hits 34.5 +/- 6.9 (phase 57); LP2 22 vs 25.2 independence expectation (my check: z -0.65 at lag 7, and the lag-7 excess is -3.2 +/- 5.0 against +10 expected from smear: about -2.6 sd by my arithmetic, -1.8 sd in phase 57's own table). No lag-5 smear exists in any variant (an extra rune only lengthens), and LP2 lag 5 is -1.6 sd. Verdict: disfavoured about 2 sd, not excluded.

**Rewind repair** (k_j := k_(j-6), M4): c_j - c_(j-6) = p_j - p_(j-6), no T (39.7 vs 38.3).

**Plaintext-F rule** (R8): 44.6 hits vs 80 (z +4.1 short).

**Unlinked sparse echo c_j = T(c_(j-6)) at 0.027 per in-word pair** (`echo-two-tap`): fits every number the repair fits, untestable on LP2 alone; its rate matches q/29 to within +/- 17% with no mechanism, one matched free parameter.

**Repairs at j < 6 using an anchor** (word's first rune, or a 6-register ring initialised per word): if the repair wrote T of the rune min(j, 6) back, the cell c_j = T(c_0) would be elevated at every position 1..5 by about 0.028 x 800-2,800 words. My check (words 2,813 / 2,365 / 1,645 / 1,132 / 815, T cell z +0.93 / +0.16 / +2.06 / -0.17 / -1.56 at j = 1..5; scan of all 812 affine relations at every j = 1..11: max z 4.54 vs within-word-shuffle null of that maximum mean 4.78, 95th 5.63, P 0.75). Positive control: 10 plants of repairs at q 0.028 per position (anchor for j < 6, lag 6 beyond) on within-word-shuffled LP2: planted T-cell z at j = 1..5 has a minimum of 2.5 to 10.2 (mean of the minimum 3.9), overall max z mean 8.1. LP2's five values (largest +2.06) are all below the weakest planted value (2.5, over all 10 plants and all five positions). Constant per-position rune (ring register initialised to a constant): positional unigram scan over 696 cells (positions 0-11 from the start, 0-5 from the end): max |z| 3.49 (a 696-cell flat maximum is about 3.2); planted constant at j = 1..5 at 0.028 gives z 7.5-8.7 in 20/20 plants. Both excluded.

**Digraph or position-dependent rule:** a digraph (p_(j-1), p_j) rule has range 1; schedules by position excluded in `word-position-schedule`; nothing at lag 6 specifically.

**Doublet deficit** (equal in and between words): only the collision-linked variants explain it; recurrence, plaintext and key-schedule mechanisms leave doublets at 3.45% and need a separate rule.

### Mechanism vs predictions

| mechanism | lag-6 rate in-word | across gaps | profile by position / length | lag 5 / 7 smear | doublets | verdict |
|---|---|---|---|---|---|---|
| pervasive key recurrence k_j = -2k_(j-6) + b, per-word restart (lagged Fibonacci, LFSR with other taps 0, period-6 with multiplier -2) | 0.0514 max = 66 hits (LP2 80, -1.7 sd) | zero if restarted per word | uniform for all words >= 7 | none | not explained | **excluded**: other 28 residual cells chi2 89.9 +/- 14.2 vs LP2 36.5 |
| order-6 LFSR with real other taps | none (residual 3-7 plaintext runes, near uniform) | none | none | none | not explained | cannot make T |
| plaintext pattern + flat key | none (residual uniform) | none | none | none | not explained | impossible |
| ciphertext autokey (pervasive) | any, but residual = plaintext | zero only if word-scoped | uniform | none | not explained | excluded (`lag-feedback`) |
| period-6 key, equal values | equal runes, not T | - | - | - | - | excluded (phase 56 B, 54.6 vs 32 equal) |
| LCG / scalar-state step, T = a^6 | impossible: T non-residue | - | - | - | - | impossible (algebra) |
| ring / anchor repair (j < 6 looks at c_0) | adds 0.028 x words at each j = 1..5 | - | elevated at j = 1..5 | none | yes | excluded (z -1.6 to +2.1, planted min 3.9 mean) |
| **R4: collision-linked repair T(c-6) in the cipher stream + one checked null per word** | 0.028 x 1,290 = 36 excess (76.6 simulated) | zero by rule (looks only in-word) | per-pair uniform; 7-rune bin 10.8 vs 8 | none at 5; no smear at 7 (25.7 vs 22) | yes (63 in / 23 gap) | **best fit**; two rules; the "why T, lag 6, in-word only" is not derived |
| R3: same, lookback in the plaintext-aligned stream, later-pass null | 68.5 | zero | uniform | lag 7: 34.5 +/- 6.9 vs 22 (about -2 sd) | yes | disfavoured about 2 sd |
| R7: end check rune | 71.6 | zero | fewer word-final hits: 24.0 vs LP2 32 | none | yes | disfavoured 1.6 sd |
| R5: per-word null equal to T | 122 (z -2.8) | zero | 7-rune bin 20.5 vs 8 | - | yes | rejected |
| unlinked sparse echo at 0.027 | fits | zero by rule | fits | none | none | not excluded, not testable alone |
| plaintext-F rule (R8) | 44.6 | zero | lower | - | no | rejected |
| separator-as-a-cell lookback | would add about +180 at (6,1) and +200 at (5,1) | no (observed +4, +53, -11) | - | - | - | rejected (rate); the (5,1) +53 is flagged as L1 |

### Why exactly -2 and 24?

- **Intrinsic:** the multiplier -2, invariant under every affine relabelling of the alphabet (shift, Atbash 28 - x, any multiplication m) as phase 57 shows. -2 is a primitive root mod 29 (order 28), so T plus its fixed point H (index 8) is one 28-cycle plus a point. It is a quadratic non-residue (finding 2). It has the unique cube root x -> 3x + 13, a unique fifth root and so on, no square root and no sixth root.
- **Coordinate-dependent:** the constant. In index coordinates 24; with y = c - 8 (centre H) T is y -> -2y; with y = c + 2 it is y -> 1 - 2y; with y = c + 1 it is y -> -2(y + 1). None is distinguished.
- **Natural closed forms:** Atbash applied to 2c + 4; 2 x Atbash(c) + 26; Atbash(c) - c - 4. None uses a Gematria value: the multiplier 2 appears as the prime of F (2), but T acts on INDICES. My check: the prime-domain affine map best fitting T agrees on 7 of 29 runes (null median 5, 95th 8, T rank 50 of 812 index-affine maps; control: the identity map reaches 29 of 29). The phi(prime) = prime - 1 shift is a constant shift in that domain and is covered by the same affine search. So -2 is not read off Gematria prime values, phi(prime) or Atbash alone; it needs a doubling that no Cicada operation on the solved pages uses. T on runes (my table): F>A U>OE TH>L O>E R>T C>X G>EO W>I H>H N>G I>R J>TH EO>F P>IA X>AE S>D T>ING B>M E>B M>S L>P ING>J OE>N D>W A>C AE>O Y>U IA>EA EA>Y; no vowel or word-structure pattern.
- **What T does tell a decoder:** the repair (if it is one) is written in GP INDEX arithmetic mod 29, not in the prime or alphabetical domain: consistent with the repository's decoders (Level 0).

## 3. Top 3 untested leads, specified to run later

**A. (L3, then L1/L2) R4-calibrated T grid.**
- Data: LP2 runes with the project's word cut; section ids; word gaps.
- Statistic: for rune-lag g = 1..12 and word-gap counts k = 0..4 (same section), z of the T cell with per-pair probabilities f[T(c)] from LP2 unigrams (hits minus expectation over sqrt of the sum of p(1-p)); also the max z over the 812 affine relations at each in-word lag.
- Nulls: (i) the repository's R4 replicates (500, `work/phase57_mechanism.py` settings: q 0.81, T repair, one checked null at slot 0..L in 0.448 of multi-rune words) with the same statistic; (ii) the same with the interior-only slot rule; (iii) within-word shuffles for the in-word cells and word-order shuffles within sections for the gap cells.
- Positive control: the same R4 with a planted gap-crossing lookback (repairs at word positions 0-4 write T(c) of the rune 5 back across the gap with probability w = 0.26) must reproduce an excess of about +53 on 7,369 pairs; interior null control: R4 as specified, expect the (5,1) cell z within +/- 2.
- Decision: if P(max over the 46 non-lag-6 cells >= 3.37 | R4) >= 0.05 drop L1, L2; else dissect (gap type, position, section) and ask for a mechanism where the lookback counts the separator in a quarter of the cases.
- Cost: 0.5-1 CPU-h.

**B. (L1) Gap-crossing replication on structure, not on data.** No second LP2 exists, so the replication is mechanistic: the solved pages 0.0-0.6 (2,797 runes) as negative control for the SAME fixed statistic (T at rune-lag 5, one gap), and a fixed pre-registered prediction for any future relation: in-word lag-6 excess rate 0.0275/pair, (5,1) 0.0072/pair, (6,1) 0 +/- 0.0012, (4,2) <= 0. The solved-page control costs seconds; a result there tells nothing for LP2 but shows whether the cell is a generic property of Cicada's separators.

**C. (L4) T sites as a whole-section keyed verifier.** For a candidate (stream, sign, offset) that survives the existing hit rule and `work/kscreen/verify.py`, compute for each in-section T hit the lost plaintext q_j = c_(j-1) - sign x k at the aligned key index (alignment from the decode); score S = sum ln(rho x 29 f_En(q) + 1 - rho) with rho 0.44 (35 repairs among 80 hits). Positive control: R4 plants over a full section (0.15, 3,316 runes, 20 sites expected): expect a few nats on average (rough), i.e. only a weak confirmation, not a screen. Null: matched iid-key plant. Cost: a function in the existing decoder; no new search.

## 4. Checked and nothing (do not repeat)

- In-word T relation at lags 1-12 and across gaps (rune-lag): only lag 6 (+5.42) and the weak cells above; lag 5 -1.61, lag 7 -0.65, lag 8 -0.67 in-word.
- Affine scan at in-word lags 1-12 with a within-word shuffle null for the max over 812 relations: only lag 6 is significant (P 0.003 vs the floor 1/300).
- Second-best lag-6 relation: (14, 9) 65 hits z +3.07, i.e. the null maximum.
- Anchor relation c_j vs word-initial rune, j = 1..11, all 812 affine forms: nothing (P 0.75); planted control above.
- Positional unigram (position 0-11 from the start, 0-5 from the end): flat (max |z| 3.49 over 696 cells).
- Line / page wraps inside the window: in-word lag-6 hits with a wrap 22 vs 11.2 (z +3.3, 325 pairs), without 58 vs 33.3 (z +4.4, 965 pairs): proportional (27.5% of hits vs 25.2% of pairs). The lookback counts runes, not printed lines.
- Gap type for the (5,1) cell: word spaces carry all of it; clause dots 14 vs 12.2.
- Per-section constant, reverse direction, duplicate words: finding 3 and 4.
- Cube-root cell at lag 2 (S(x) = 3x + 13): z +0.76.
- Gematria prime domain: nothing (7 of 29).
- Not run: 3-tap sparse scans (a key LFSR with 3 taps leaves a near-uniform residual, so a scan has almost no power; no test is proposed), lag-12 T iterate (only 10 in-word pairs), non-English plaintext models in the recurrence prediction.

## 5. Killed by known signal

- **Pervasive key-side recurrences (lagged Fibonacci, order-6 LFSR, period-6 key with multiplier -2):** flat residual at 28 cells (chi2 36.5 vs predicted 89.9 +/- 14.2) and a rate ceiling of 0.0514 < 0.0620; no doublet effect.
- **Plaintext-side patterns with a flat key:** residual uniform by construction.
- **LCG / any scalar affine step as the key:** multiplier a^6 is a square, -2 is not.
- **Ciphertext autokeys:** residual = plaintext, excluded by `lag-feedback` plants (chi2/n 2.25 vs LP2 0.44).
- **Per-word period-6 equal key:** equal runes at lag 6 (LP2 32 vs 54.6 predicted).
- **Ring / anchor repairs and constant per-position repairs:** table above.
- **Repair that counts separators as cells:** (6,1) +4, (4,2) -11 against +180 predicted.
- **R5 (null = T):** 1.5x too many hits, in 7-rune words (phase 57).

Open and unchanged: the "why T, why 6, why only inside words, why at the collision" of R4 is not derived by any construction above; R4 remains a statistical fit of two rules (Level 1), not evidence for Cicada's method.
