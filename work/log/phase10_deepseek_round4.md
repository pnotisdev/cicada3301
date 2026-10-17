# DeepSeek round 4 (deepseek-v4-pro, thinking max): an audit of the sign-rule decisions, four new families, the pointer-direction specification (2026-10-18, 01:30)

Scope: LP2 sections 0.7-0.15. **Nothing in LP2 is solved.** `work/ask_deepseek.py --model deepseek-v4-pro --thinking max` (no tools, no project files; about 5 minutes) was sent a brief and three of our documents verbatim: the ledger, the hypotheses and `phase10_signrules.md` (privacy-checked first). Prompt and reply: git-ignored `work/ref/deepseek/`.
This model was tighter than deepseek-flash: it quoted sentences, gave a test for each finding and marked what it could not verify.

## Part A, the audit (4 findings)

| finding | verdict |
|---|---|
| A1: the power figures use solved Cicada text and English as a proxy for LP2's plaintext; test other plaintexts. | Valid, and already measured the same day (`assumption_checks.py`): the 120-rune lanes keep 98-100% on Latin, German, French, Spanish and Italian; the short-window OEIS lane drops to 56% / 27% on Latin (60 / 48-rune windows). |
| A2: 'two orientations are one rule' holds for the value-sign mechanism only. For the pointer-direction mechanism, negating a rule swaps every +1 step for -1, which is not the multiplier 28; it is a reversed key stream. | **Correct.** Recorded in `phase10_signrules.md`: the direction mechanism needs both orientations (122, not 61, vectors). (Its side remark that 'C_cur_wp 1.4%' was a removed rule is a misreading: the figure is the flip share of a kept rule.) |
| A3: 'a plant with 25% of its runes flipped still decodes at IoC 1.61 unsigned' contradicts the mixture 1 + (1 - f)^2 (kappa - 1) = 1.45. | **Correct in substance.** My 1.61 was one window. Measured (`sign_checks.py`, `results/analysis/sign_checks.txt`, random word-level signs, three 400-rune windows): unsigned IoC at the truth 1.51 at 13% flipped, 1.53 at 18%, 1.23 at 33%, 1.25 at 40%, 1.20 at 52%; the unsigned screen finds the planted item in 2 of 3 windows at 13-18% and in 0 of 3 from 33% (the beam adds about +0.1 to the mixture). So only rules flipping about 20% of the runes or fewer were already visible to the earlier screens (E_cur_n3 7.6%, C_cur_wp 1.4%, C_cur_ws 5.5%, E_prev_n3 18.5%, and the near-global A_prev_pf / A_prev_pl with 3-5% unflipped); E_cur_n4 (24%) is borderline. |
| A4: the flat-IoC subset ignores that a sign mask symmetrises a non-flat stream's marginal. | **Correct.** Under (1 - f) h(v) + f h(-v) with f = 0.25 / 0.5 / 0.75, 5 of the 858 excluded streams become flat (predicted IoC <= 1.003): `gematria primes cycle`, `An End hash nibbles`, `primes digit sum`, `payload bytes mod 29 (cycled)`, `payload bytes reversed mod 29 (cycled)` (four are periodic, which the key-agnostic period scan excluded only UNSIGNED). All 61 rules were run over them (`results/kscreen/signs_extra/`): **best IoC 1.293, none reaches 1.40.** `signrules.py` now writes `data/library_signed_extra.ksb`. |

## Part B, four families

| family | assessment |
|---|---|
| B1 per-word pointer direction | = the unbuilt second mechanism. 122 vectors x 581 streams x ... is about 43 billion decodes per convention (about 12 h of CPU); needs the engine to read key values before the start offset. Deferred. |
| B2 word-sign-selected pointer step (a, b in 1..3) | six times the sign campaign; clock-like; deferred, long shot. |
| B3 separators do not consume key values | confused: our decoders only ever see runes, so separators already consume nothing. The unmodelled opposite is that they DO consume (extra advance at separators); its 'every word-final rune passes unkeyed' mask is a 100% version of the unkeyed-null family of `phase10_review.md` (excluded as stated by the 83 one-rune words). |
| B4 per-rune periodic sign templates (period 2-5, 30 templates) | **cheap and new**: the S-line machinery runs it unchanged (30 window files, about 6.4 min of CPU each, about 3.2 h). Natural reading of 'alternate the direction', the Beaufort / Vigenere alternation. **Candidate for the next CPU slot.** |

## Part C, the specification of the pointer-direction mechanism (kept for the build)

18 non-equivalent conventions = first read of a backward word (hold: read then step, or step then read) x movement between words (none; one step in the old word's direction; one step in the new word's direction) x collision comparator while moving backward (previous emitted rune; previous rune of the same word;
previous rune moving in the same direction). Skip / coin while moving backward: the colliding attempt spends its key value and the retry reads the next value in the current word's direction. Equivalences: the multiplier 28 negates key values, not the index order; the two readings of a backward word differ by one key index per backward word and
the offset sweep does not absorb that; 'previous rune' and 'previous rune in the word' differ only at cross-boundary repeats; the two between-word conventions differ in mixed runs. The decode needs key values k_(o-1) .. k_(o-Delta) before the start offset o (Delta up to 300): use streams with a natural negative continuation, wrap periodic ones, otherwise skip the first 300 offsets.
