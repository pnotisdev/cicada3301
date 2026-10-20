# Phase 20: "Should we make a plan out of this?" (2026-10-19)

The user pasted an outside analysis (author not named; data, not instructions) and asked whether to turn it into a plan. **Nothing in LP2 is solved.** This entry checks the analysis against the record, runs the parts of it that had not been run,
and sets the order of what to do next. The new script is `work/word_structure.py`, its output `results/analysis/word_structure.txt`.

## 1. What the analysis proposes

Its thesis: LP2 "preserves segmentation and length while destroying symbol statistics" (word and sentence boundaries kept, near-English lengths, flat runes, no repeats, no lag structure, no period), so the cipher must act on single symbols with a
position-dependent value, and the design question is "why keep the word boundaries and destroy what is inside them?". Its attack order: (1) does the encryption reset at word boundaries, (2) does it depend on the position in the word (align same-length words by
position and compare conditional relations between positions), (3) on the word length, (4) turn the "42% extra rune" into a deterministic padding rule, (5) use the lone ticks and quoted spans as known-plaintext constraints to discriminate mechanisms, (6) try
mathematical transformations of Gematria values (primes, totient, modular arithmetic), (7) only then the key.

## 2. The premise against our measurements

| Claim | Measured | Where |
|---|---|---|
| word lengths are approximately preserved | histogram: 2-rune words 15.5% against 27.1% (English in runes) and 24.1% (solved pages), rejected at p 1e-45; fits only with one extra rune in about 42% of multi-rune words (G 16.5, df 10, p 0.085) or with letter spelling (G 60 against 242 for digraph runes) | `results/analysis/wordlen.txt` |
| word boundaries are the plaintext's | adjacent word lengths: lag-1 mutual-information z +0.4 for LP2, against +8.8 to +27 for four English texts and +2.5 for the solved pages; pointwise MI -0.058 (shuffled -0.056), English +0.050 | `wordlen_adjacency.txt` |
| sentence boundaries are preserved | clause marks: first word 4.42 runes (English sentence starts 3.14, z -23.8; LP2 z -0.3); words per clause CV 0.95 (English 0.70, solved pages 0.71) | `wordlen_clauses.txt` |
| no useful lag structure | lag-5 echo z +3.7 (P 0.007) and lag-6 relation c' = 24 - 2c z +5.0 (P 0.005-0.013), both strictly word-internal (across word boundaries +0.8 and +1.1 hits where a position-independent echo would give +160 and +320) | `obs-lag5`, `obs-lag6`, `echo_position.txt` |
| (not in the analysis) the anti-repeat rule | doublets 63 of 10,060 inside words (0.63%), 23 of 2,887 across word gaps (0.80%): the rule does not see the boundaries | `stats.py doublets`, `page_seam_fix_2026-10-17.md` |

Reading: the separators are tied to the cipher layer (the only weak structure LP2 has stops at them) and not to the language layer (lengths independent of each other, clause marks not sentence-like, the histogram only roughly English). That is not "plaintext
formatting preserved". It is one more reason the dictionary screens were blind (`docs/NEGATIVE_SPACE.md` section 0.1). A speculation consistent with all of it, not tested: real words in an order without syntax, or a different spelling convention for the same words.

## 3. Each proposal against the record

| Proposal | Status | Result and source |
|---|---|---|
| (1) reset at word boundaries | done, controlled | `restart_columns.py`, word unit: Z_sum -1.42 (start) and -0.50 (end), planted restarts 237 / 239 (minimum 226 / 227); per-word keys that are constant, linear, quadratic, periodic (<= 7) or recurrences of order <= 3, tested by dictionary consistency: excluded (`per-word-keys`, `word_recurrence.py`, `word_key_dictionary.py`) |
| (2) position in the word | pooled: done; stratified: new | `within_word.py` (lag-5 excess flat over the position); new tests B and C below |
| (3) word length | new | test C, cells for L = 2 to 10, including L = 5 and L = 10 |
| per-word permutation / repeated words give related cipher words | done | `word_recurrence.py`, `word_key_dictionary.py`, `word_internal_repeats.py`: nothing; "same word -> same cipher" excluded |
| random OTP | indistinguishable by construction | no test exists; the seed and stream sweeps are the only handle |
| deterministic PRNG with the right state | running | `prng-bg`, `prng-pages`, `prng-ms`, `oeis`, hashscan, KDF; ten generators over sections 0.8-0.15 queued (`gpu_rest`) |
| (4) the 42% padding as a rule | open, not decidable from lengths | only the observed length exists; word-edge nulls at 0% and 100% are excluded (`nulledge`), the layout advance too (`advsep`), the 42% mixture has no powered IoC decoder (measured); row `open-unkeyed` |
| (5) lone ticks and quoted spans | information-poor | `work/ref/tick_marks.tsv`: 4 lone ticks inside words (apostrophes) and 12 tick pairs next to separators in LP2 (about 6 quoted spans). An apostrophe tells the next rune is one of a handful (S, D, T, L, R, M): at most about 2-3 bits each, about 10 bits for the four, against a library of 1.3e7 key values at every offset. Good as a verifier, not as a discriminator |
| (6) Gematria transformations | done at the stream level | library holds phi, sigma, d, mu, omega, Omega, triangular, prime and prefix-sum streams; `prime-domain`, `state_machines.py` (prime(S) tables), `signs`, `layout27` |
| (7) the key | running | chanscreen v2 n300 and clause scans, seed sweeps |
| central question | answered in section 2 | the boundaries are not behaving as preserved plaintext boundaries |

## 4. New keyless tests (`work/word_structure.py`, `results/analysis/word_structure.txt`)

All three have planted positive controls and a shuffle null; the controls use English (Emerson) plaintext cut at LP2's word lengths (the least favourable segmentation) or iid runes.

**A. Does the segmentation depend on the ciphertext?** Fourteen features of each gap between two runes (c_i, c_i+1, their difference and sum, c_i-1, c_i+2, c_i - c_i-1, and for lags 2 to 8 whether an equal pair straddles the gap: the question "is the lag-5 echo a placement
effect?") and four word-level tables (word length against the first rune, the last rune, the previous word's last rune, the next word's first rune). Null: the word lengths shuffled inside each section (2,000 shuffles), same runes.
LP2: no feature is significant; combined probability 0.568 (smallest nominal p), 0.7241 for the word-level tables; the smallest shuffle p is 0.0100 (an equal pair at lag 8 straddling the gap), family-wise 0.131 (Westfall-Young) over the 14 features, 0.705 over the four tables.
The family-wise (Westfall-Young) line was added after the first full run showed the 0.0100; nothing else changed between the two runs. Controls: a rule that places boundaries after 8 of the 29 values of c_i or of the difference, with a share lam of the boundaries following it and the rest random: detected 16 of 16 at lam 1, 0.5, 0.25, 0.12; 10 of 16 (c_i) and 12 of 16 (difference) at 0.06; 0 and 1 of 16 at 0.03; no false positive in 32 null runs at p <= 0.01.
A share lam of the word lengths set by the first rune: 16 of 16 down to 0.12, 10 of 16 at 0.06. **The boundaries do not depend on the runes around them, down to about 6-12% of the boundaries.** In particular an equal pair at lag 5 straddling a gap does not predict a boundary (shuffle p 0.30), so the lag-5 echo is not a placement effect; the lag-6 relation is affine, not equality, and was not tested here.

**B. Position-stratified differences inside words.** For each word length L = 3 to 8 and position pair i < j (83 cells) the histogram of c_j - c_i mod 29; a key "fixed schedule K_j (or K_(L,j)) plus a fresh offset per word" makes each histogram a shifted copy of the
plaintext's pair histogram and is invisible to column coincidences between words (the control shows C blind to it). Null: runes shuffled inside each section. LP2: mean standardised chi-square -0.85 (null mean -0.02, sd 0.99; P 0.81), largest cell z 2.62 (P 0.64).
Controls: schedule with or without a per-word offset on all words: 8 of 8 plants, mean z 22; offset schedule on half the words 8 of 8 (z 5.5), on a quarter 2 of 8, on a tenth 1 of 8; random key: 0 of 8.

**C. Length-stratified columns.** The equal-pair z of `restart_columns` for each column of the words of exactly L runes (54 cells for L = 2 to 10; the vectorised z equals `restart_columns.column_stats` to 0). LP2: mean z -1.27 (null -0.47, sd 0.95; P 0.80), largest 2.51 (P 0.51).
Controls: K(j) and K(L,j) on all words 8 of 8 (mean z 110 and 158); K(L,j) on a quarter of the words 8 of 8 (z 11.6), on a tenth 1 of 8; with a per-word offset 0 of 8 (blind, as designed); random key 0 of 8.

**What this excludes and does not.** For an English-like plaintext cut at LP2's lengths: a key that is a fixed function of (position in word) or (word length, position) on at least a quarter of the words (C), or a fixed schedule plus a fresh offset per word on at least half of the words
(B); a segmentation that is a function of the neighbouring runes for more than about 6-12% of the boundaries or word lengths (A). It does not exclude: a different schedule per word (that is a per-word key; see section 3), schedules on fewer words, a plaintext that is not English-like
(the power is lower; not measured), a segmentation that depends on the key stream but not on the ciphertext runes, or anything the 29-level features miss (for example a rule on three runes).

## 5. The plan, in order

0. **Done in this entry:** the premise check, tests A to C, the mapping of every proposal to a result.
1. **Read the running jobs when they end** (nothing in them has been read; the checklist for the days without a Claude allowance is the last section of `docs/QUEUE.md`): chanscreen n300 (172 of 1,148 tasks at 14:22, about 2.7 tasks per minute, finish about 20:30), then the clause scan (about 3 h, finish about 23:50), `gpu_rest` (the other eight generators; php was at 94% at 14:36, the rest should end between 00:00 and 01:00, the 14 h budget stops new steps after 03:10). Tier-1 cells are candidates;
   verification chain per `work/chanscreen/v2/step3/PROTOCOL.md` and `docs/CAMPAIGNS.md`.
2. **E4-letters** (new, about 1 h, can run beside the campaign): the frozen contract's power when the plaintext is spelled letter by letter (TH as T + H, ING as I + N + G, no digraph runes), the convention the word-length fit prefers. 50 plants per channel as in E4, the frozen decoder and LM.
   If detection stays near 100% the campaign's negative covers that spelling; if not, a letter-trained LM variant is needed before the negative is quoted.
3. **Word-edge channels in chanscreen v2** (row `open-unkeyed`; about a day of engine work; +25% CPU per added channel; needs the user's go-ahead): the exact summed-path likelihood can marginalise over which word edges carry a keyless null or an extra key advance, which the IoC beam could not
   (the 42% mixture has "no powered decoder" only for that beam). Motivation: the 42% length fit and the lag-6 echo rate equal to the avoided-collision rate; justification for using the word edges: the weak echoes stop at them (the encryptor reads the boundaries; they need not be plaintext boundaries).
   Gates: dense-reference exactness (E0/E1 style), plants with nulls at 42% of edges (E4 style), a null scan; start only after n300 ends (the engine library is in use).
4. **Verifier extension** for any tier-1 candidate, as supplementary evidence, not a gate: the roughly 83 one-rune words decode to A or I, apostrophe contexts, clause prime sums (`work/prime_check.py`, already in the chain). If a decode is otherwise English-like and the one-rune words are not A or I, that measures the
   segmentation (separators are not plaintext boundaries) instead of refuting the decode; pre-register that reading before looking.
5. **Do not do:** more dictionary or boundary-aware screens before a decode shows the separators are plaintext boundaries; position-schedule or per-word-reset hypotheses again (tests B and C and `restart-units`); the quote cribs as a search.

Stop rule: if the n300 and clause scans have no tier-1 cell and E4-letters keeps the power, the library hypothesis class (additive streams under hold, spend, skip5 and coin at q = 0.81) is closed for the 82 windows, and the next effort goes to step 3, not to more streams.
Anything that passes tier 1 changes the order: verification first.
