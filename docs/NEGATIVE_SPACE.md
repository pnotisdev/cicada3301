# What is excluded, how well, and what is still open (coverage-and-power ledger, 2026-10-17)

**Nothing in LP2 is solved.** Every negative in this repository is a statement of the form "a planted key of this kind, in this much text, would have been found by this test, and nothing was found".
This ledger lists, per hypothesis family, what was tested, the planted-control power that is on record, what the negative therefore excludes, and what it does NOT exclude. It is built from the logs
named in the last column; where a number is not in a log it is not here. Its purpose is to choose the next tests among the hypotheses that are genuinely open, not to repeat tests whose power is known.

*Status note: `docs/HYPOTHESES.md` and `work/log/phase9_hyp.md`, cited below, are the desktop's second session's work (H1-H12 with their controls); they were still uncommitted when this was written.*

Power legend: **strong** = planted keys of the realistic size are recovered at the exact setting; **partial** = recovered only in some windows or sizes (stated); **none** = the control fails or was
not run (the negative says nothing about the effect size LP2 shows).

## 0. Blind spots that apply to many rows

1. **Dictionary scores are blind if the separators are not the plaintext's word boundaries** (planted seed: score 33 with the English words' own separators, 0 with LP2's word lengths imposed,
   `phase9_boundaries.md`). Affected: `prng-all` (PHP, glibc, .NET, all sections), `prng-more` (window 0.7), `rescreen`, `dsearch`, prngx stage A, the dictionary version of hashscan. **Boundary-free reruns that exist:**
   all ten generators over all 2^32 seeds on window 0.7 (`prng-bg`); hashscan (19.2 M candidates) and the KDF lane (719,280 streams) on window 0.7; the OEIS lane (199,088 sequences, 36-rune windows); epoch-time seeds
   2011-2015 (8 generators) and small seeds below 2^27 (3 generators) on every section; millisecond timestamps for py3 and java (2013-09 .. 2014-01, window 0.7).
2. **IoC screens (kscreen) work on 300-rune windows.** Planted keys: recovered and above their null in 45 of 45 windows of 250-300 runes, but recovered in only 13 of 21 and above the null in 9 of 21 windows of
   0-149 runes (`results/kscreen/typo_plants.txt`). Any restart or heading test on a short window is weak.
3. **Scope of the windows:** the first 300 runes of each of the 8 sections (every offset of every keystream), plus 46 page starts, 10 headings, 22 typographic-mark windows. A key that is right only somewhere
   else is not tested.
4. **The anti-repeat rule is modelled as skip / coin (81%), as ciphertext feedback, as a step-domain rule, or as a null rune (H8).** Each has its own decoder; a mechanism outside these is not decoded.
5. **kscreen is blind to a two-layer cipher** (IoC about 1.1-1.2 after removing the outer layer, threshold 1.40); the laptop's `layer2` and the H1 design address that.
6. **Seed coverage:** 32-bit seeds for the full sweeps, window 0.7 for the exhaustive ones; the 64-bit port covers py3 / ruby / java only.

## 1. Additive key from a known stream (c = D(p) + m k + b, skip / coin)

| Hypothesis | Tested with (scope) | Power on record | Excludes | Does not exclude | Source |
|---|---|---|---|---|---|
| Number-theoretic, constant, lore-hash and keyword streams (1,447 library streams), any start offset, any plaintext language and alphabet, both signs, both models | kscreen, IoC, 409 M decodes; x28 multipliers; backward key (a = 0..28); ciphertext feedback (a = 1..28) | strong: 15/15 planted windows at the exact offset, IoC 1.61-2.06; random maximum 1.31-1.37; feedback and backward plants recovered, wrong a not | any library stream at any offset in the first 300 runes of the 8 sections | streams not in the library; later windows; restarts at unknown places | `phase9_chain.md`, `CAMPAIGNS.md` |
| Linear recurrences of order <= 3, polynomials of degree <= 3 (every start state) | kscreen-recurrences | strong (lin2, poly2 plants) | those families | order >= 4; sparse taps: the keyless residual scan has no power for three-term forms (planted ranks 15, 6,229, 29,640 of 55,440) | `CAMPAIGNS.md`, `phase10_keyless_power.md` |
| Hash streams of the solved text's words and phrases (12,944), hashscan passphrases (19.2 M), KDF passphrases (719,280) | kscreen-hashwords (all sections, IoC); boundary-free bigram score on window 0.7 | strong for the score (true key +10 per rune, wrong -10.5); gates with planted keys | those candidates on 0.7; hashwords on all sections | other sections for hashscan / KDF; other KDF settings; passphrases not in the lists | `phase9_overnight_results.md` |
| OEIS sequences as keys (199,088, mod 29) | boundary-free score, 36-rune windows (sections: all 128 offsets; pages and heads: offsets 0-15) | partial: planted primes found at rank 1, but a true key scores about +360 over 36 runes against the +300 gate and the random best is 181-246 | OEIS sequences at those offsets | longer windows; deeper offsets | `phase9_overnight_results.md` |
| Seeded PRNGs: PHP, glibc, .NET, py3, mt32, mt31, java, msvc, drand48, ruby (two key maps each) | dictionary sweeps (see section 0.1); boundary-free: all 2^32 seeds on window 0.7; time seeds (2011-2015) 8 generators and seeds < 2^27 for 3 generators on every section; ms timestamps py3 / java 2013-09 .. 2014-01 on 0.7 | strong: planted seeds at rank 1 for every generator; independent keys at the 2^32 / 2^48 boundaries | one pad from the start of 0.7 for any 32-bit seed; the listed prioritised ranges on all sections | sections other than 0.7 over the full seed space (boundary-free, 1.1-1.7 h per generator on the 2080 Ti); per-page seeds; the other 20 ms months; ISAAC, filtered LFSRs; string / float seeds | `phase6_prng.md`, `phase9_gens.md`, `phase10_prng_time_gpu.md` |
| Public random tables, deep constants (pi, e, phi, sqrt2 at 10^6 and 3301 x 1033) | kscreen-hyp | strong (12/12 plants) | those blocks | RAND's Million Digits (download not done) | `phase9_hyp.md` |
| Numbers of a text as key (prefix sums of the solved plaintext and Self-Reliance) | kscreen-hyp | strong (plants) | those transforms | Liber AL, Rune Poem (not downloaded); per-word sums and base-10 digits fail flatness | `phase9_hyp.md` |
| Ciphertext as the key (LP2 backward, forward with the self-key guard) | kscreen-hyp | strong (a planted L = 500 autokey found through the guard) | those two streams | other texts' ciphertexts (Welcome's fails flatness) | `phase9_hyp.md` |
| Clocked or decimated key pointer (steps d = 2..29; six clocks from the cipher or deciphered rune) | kscreen-hyp, kscreen-clock | strong (18/18 plants); 150-rune windows only for the prime clocks | those pointers | keys that start beyond the first ~9,000 terms for prime clocks | `phase9_hyp.md` |

## 2. Cipher structure beyond c = p + k

| Hypothesis | Tested with | Power on record | Excludes | Does not exclude | Source |
|---|---|---|---|---|---|
| Ciphertext feedback c_i = a c_(i-1) + p_i + k (lag 1) | kscreen-chain, a = 1..28 (library, order-2 recurrences, cubic polynomials) | strong (a = 1, 7, 28 plants) | lag 1 | lag > 1 with a multiplier: only the differences (a = 1) are covered, flat to lag 400 | `phase9_chain.md` |
| Step-domain cipher (the plaintext enters c_i - c_(i-1), keyed mod 28; variants A, B, C) | library, periodic keys to lag 3,000, recurrences / polynomials over Z28 | strong (plants in both variants; periods 97 and 400 at z 6.5-11) | those; periods up to about 800 | **seed sweeps (`prng-step`, about 25 h): not run** | `phase9_step28.md` |
| Small state machines (4,608 rules x 29 start states, with and without the skip modelled) | IoC and a Viterbi bigram score | strong (planted machines rank first at IoC 1.76 and -3.0 against -3.94) | that family | machines outside it | `phase9_hyp.md` |
| Number-theoretic combinations: s1 + t*s2 and interleaves of 20 streams, functions at the primes, base-29 reciprocals of 3301 / 1033, rational functions of p mod 29 (outside LLM's families) | `kscreen-sacred`: 1,063 streams x 8 sections at every offset | strong (planted keys 24/24 at IoC 1.6-2.06; rule 1.40; best 1.369) | those streams, 300 runes per section | other pairings; order-4 recurrences with chosen coefficients (not built); pointer schemes needing long bases | `phase10_sacred.md` |
| Inverses, discrete logs, g^n and cubes modulo primes = 1 (mod 29), base-29 digit sum (DeepSeek's second batch, 19 periodic streams, period 58-928) | `kscreen-sacred2`: 8 sections at every offset | strong (planted keys 30/30 windows at IoC 1.56-2.10; rule 1.40; best 1.249) | those 19 streams, 300 runes per section | other primes and generators; any non-periodic family | `phase10_sacred.md` |
| Two layers: a keyword inside a number stream (H1, the laptop's `layer2`) | layer2 slices: An End's streams x DIVINITY / FIRFUMFERENFE / CIRCUMFERENCE; 20 streams x any keyword of period 2-14; 20 streams with a solved key folded in (A1: best -5.63, 0/15, plants 12/12, `phase10_layer2_a1.md`) | strong for the bigram mode (9/9 plants); partial for the periodic mode (chance z about 10 overlaps weak plants) | those slices | the library x L <= 20 with drift tracking (designed, not run); seeded generators outside (needs a GPU kernel) | `docs/prs/new-hypotheses.md` |
| Tableau or transition-table ciphers driven by a stream (H2) | not run | - | - | open | `docs/HYPOTHESES.md` |
| Plaintext / ciphertext autokey at lags <= 8; mono; Vigenere with period <= 29; per-word key; progressive, multiplicative, cumulative keys | fingerprint simulations (25 rows x 100 replicates); the laptop's probes | strong for the fingerprint (IoC, differences, lag spectrum); H-PROG moderate; prime keys 'disfavoured' only | those families | longer lags; the fingerprint cannot tell structureless keys apart | `phase9_families.md`, `hypotheses_2026-10-17.md` (branch) |
| Null rune on collision (H8) | word-length fits; kscreen on planted H8 keys | the unchanged kscreen finds them, so earlier negatives stand | - | alive as a partial explanation of word lengths (G 56 -> 40) | `phase9_hyp.md` |
| Evolving-alphabet walk (period-5 alphabets per word, alphabet changes per word, skip on repeat; aldegonde's length-clocked walk) | fingerprint simulation (reproduces the lag-5 echo, not its S concentration); a general fixed-map scan; the AI-campaign repo's annealing (0 of 63 recovered with everything but one permutation given) | none at LP2's effect size: the fixed-map scan detects copy rates of 6%, LP2 shows 1.5% | strong versions (maps copied at 6% or more) | **the one family the fingerprint leaves standing, and no test has power for it**; a model-specific prediction (relations at lags d and d + 5 are powers of one permutation) is not yet checked | `phase9_families.md`, `phase10_keyless_power.md` |
| Per-word keys / per-word recurrences / a secret outer alphabet with a per-word key | cribs; `word_recurrence.py` (orders 2-3); `walk dsearch` (synthetic recovery 29/29) | strong for cribs; the dictionary-based tests are blind if the separators are not words | same word -> same cipher; one key per word; key by position in the word | the word-based tests if the separators are not boundaries | `phase4_crib.md`, `phase6` notes |

## 3. Restarts, reuse and layout

| Hypothesis | Tested with | Power on record | Excludes | Does not exclude | Source |
|---|---|---|---|---|---|
| Key restart at every page, paragraph, line, sentence or word | `restart_columns.py`, `restart_llr.py` | strong: planted restarts give Z 17-236, LP2 -1.1 .. +2.1 | those units | sections (n = 9): control only 2.7 | `docs/prs/restart-columns.md`, `restart-llr.md` |
| Restart at headings and page starts (library) | kscreen-restarts, 46 page windows, 10 headings | strong for the 7 windows of >= 308 runes; partial for the 91- and 121-rune headings (heavy-tailed maximum) | long windows | short heading windows | `phase9_overnight_results.md` |
| Restart at typographic marks (list items, three-dot marks, after red headings) | kscreen-typo (laptop, final push f096a8c) | strong for 250-300 runes (45/45); partial for 91-139 (9/21); shared-key test on the five items: planted shared key seen in at least 3 of 5 lists in 6/6 plants (laptop's pooled test 3/3), LP2: 0 in 3 or more (library and null) | long windows; a library key shared by the list items | one short window (81-139 runes) alone; a key outside the library (the summary's 'CANDIDATE' line is a verify-rule artefact, log 1b) | `phase10_keyless_power.md` |
| Key reuse between sections (two-time pad under skip drift) | `pad_reuse_power.py` (H9) | none: power 0.05-0.42 for a planted full-section reuse | nothing | undecidable from the ciphertext | `phase9_hyp.md` |
| Periodic keys | drift-aware matched filter; step-domain scan | detected 8/8 up to 400, 7/8 at 800, 6/8 at 1,600, 0/8 at 3,200 | periods up to about 400 (800 in the step domain) | longer periods | `CAMPAIGNS.md`, `phase9_step28.md` |
| Transposition | seams; doublet statistics | exact for the seams | transposition AFTER encryption | before encryption (undetectable) | `PLAN.md` |

## 4. Cribs, outside material, community claims

| Claim | Status | Source |
|---|---|---|
| Heading = DIVINITY WITHIN; body = 'FIND YOU ARE ...' | the 13 + 141 key values are in none of 199,088 OEIS sequences (exact difference lookup, planted control found); the body crib's word lengths equal LP2's cipher words exactly, the Fibonacci key is word-choice selection, matrix repeats P 0.05; title cribs (17 section and 55 page openings, 1.5e9 fragments) in the AI-campaign repo: null. Exact crib filters on the seed libraries add nothing beyond the boundary-free window-0.7 sweeps for additive keys | `phase9_community_claims.md` |
| 27 x 27 layout; page numerology; totient walk | no 27-wide structure (sensitive to about 100 hidden mirrors); numerology is chance after counting the choices; the walk rule is undefined | `phase9_community_claims.md` |
| Base-60 payload (256 bytes) | byte-random, not a permutation or S-box; 832,204 AES / RC4 / XOR passphrase decryptions none; hash identity none | `phase4_items4-6.md`, `phase9_hyp.md` |
| Book codes / pointers into public texts | AI-campaign repo: best z 5.2, below its noise replicates; not run here | research notes |

## 5. The observations any open hypothesis must explain

doublet deficit (0.63% against 3.45%, ignores text structure; 81% enforcement); within-word lag-5 echo (z +3.7, carried by rune S, calibrated P 0.007; with the laptop's page-seam fix z +3.75); the lag-6
relation c' = 24 - 2c inside words (z +5.0, P 0.005-0.013 after the look-elsewhere, split-half replicates); word lengths with no serial structure and an English-like histogram ('+1 rune in 42% of
multi-rune words', p 0.085); flat IoC; the repeated 6-gram DJU-BEI (chance: P(>= 1) = 0.16). The lag-5 and lag-6 effects are strictly word-internal (across word boundaries +0.8 and +1.1 hits where a position-independent echo would give +160 and +320; `results/analysis/echo_position.txt`) and flat over the position in the word: a mechanism must know where words begin and end. A per-word period-5 twist skeleton (key state T^(j mod 5), T(x) = 24 - 2x) reproduces both effects but predicts equal excesses at lags 3, 4, 7, 8 that LP2 lacks (lags 3 and 4 about -6 sd together; `results/analysis/skeleton5.txt`), so a periodic per-word key is excluded. Two-tap echo rules (copy / affine image of the rune 5 and 6 back inside words, or a rewrite of plaintext repeats) are NOT excluded and not testable on LP2 alone: three free rates fit three numbers, the excess is spread over the source runes as an even echo predicts (`results/analysis/echo_values.txt`), and they leave the key layer untouched.

## 6. What is left, ranked by whether a test with power exists

| Open hypothesis | A test with power exists? | Cost | Needs |
|---|---|---|---|
| Boundary-free seed sweeps of sections 0.8-0.15 over the FULL seed space (a fresh seed per section) | yes (gated, +10 per rune) | 1.1-1.7 h per generator on the GPU | GPU |
| Per-page seeds over the prioritised ranges (epoch seconds 2011-2015, seeds < 2^27) on the 46 page windows | yes | about 11 minutes per generator | GPU |
| Remaining millisecond-timestamp months (2012-01 .. 2013-06) for py3 / java; java-abs and ruby | yes | about 3.4 h (py3 2.0 h + java 1.4 h), about 4.8 h more for a full java-abs and ruby window | GPU |
| Step-domain seed sweeps (`prng-step`), IoC scoring, ten generators | yes (exact tail, planted seeds) | about 1 h per generator | GPU |
| H1: library x keyword (L <= 20) with a drift-tracking decoder | designed; controls specified | 1-2 days of engine work, then CPU / GPU | new engine |
| H2: tableaux and transition tables (a statistic invariant to the table) | designed (about 30 sigma for the right stream) | with H1 | new engine |
| Sign flips by a rule ('their numbers are the direction'): word length, word sum or key-value parity | yes (decode screen over the library, about 20 rules) | small engine option, then hours | engine option |
| A model-specific test of the length-clocked walk (relations at lags d and d + 5 powers of one permutation) | no at 1.5% (the general scan needs 6%) | - | a larger effect or a decode-based formulation |
| Key reuse between sections | no (power 0.05-0.42) | - | - |
| Alive-but-unexplained: H8 null runes (word lengths), the S-carried echo, the lag-6 relation | observations, not key families | - | a mechanism |

**Reading the table.** Everything above the line of 'engine work' is a seed or stream sweep whose scoring and controls already exist; those are the GPU candidates. The structural hypotheses with real
novelty (H1, H2, sign flips, the walk) need new decoders first, and the walk, the model the fingerprint leaves standing, has no keyless test with power at LP2's effect size.
