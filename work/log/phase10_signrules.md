# Word-level key-sign rules: 'their numbers are the direction' (2026-10-18, 01:00; results to be completed when the campaign finishes)

Scope: LP2 sections 0.7-0.15, first 300 runes of each at every offset. **Nothing in LP2 is solved.** The January 2016 clue ('their numbers are the direction') and 'EITHER THE WORDS OR THEIR NUMBERS' (0.0), read as: the sign of the key for every rune of a word is decided by a number of
the transcription, c = p + s_w * k. An outside LLM (third-party text, not run) enumerated 112 rules over ten word quantities (three templates of parity, mod-p half splits and comparisons, plus within-word comparisons and length thresholds, each with two orientations) and two mechanisms
(key sign per word; pointer direction per word). Built here: the sign mechanism only.

## What changed from the enumeration, and why

- **Two orientations are one rule.** A global sign flip is the multiplier 28 that every screen tries (mults 1 and 28), so a rule and its negation give the same decodes: 112 -> 56 rules before the next change.
- **Circular rules removed.** A rule an encryptor can apply must use only what it knows before it enciphers the word: the current word's length and positions (word index in the section, in the page, in the clause) and anything of the PREVIOUS words' ciphertext. Rules on the current
  word's own ciphertext numbers (G, R, first / last rune, their GP primes) depend on the sign being chosen; the plaintext word's numbers are not computable by a solver. Kept: 64 rules (parity 11, half splits mod 3 / 5 / 7 on 11 quantities and mod 29 on G and R of the previous word 35, comparisons with the
  previous word 10, previous-word first / last comparisons 2, length thresholds n >= 3, 4, 5 on the current and the previous word 6); 61 after dropping three duplicates of another rule's sign vector.
- **Not built:** the second mechanism (pointer direction per word). It needs the pointer to run backward over key values before the start offset and a convention for where a backward word begins; a larger engine change, to be decided after this result.
- **Partly covered already (corrected by the audit of `phase10_deepseek_round4.md`).** An earlier version of this note said a plant with 25% flipped runes still decodes at 1.61 unsigned; that was one window. Measured (`results/analysis/sign_checks.txt`): the unsigned screen finds a planted key in 2 of 3 windows at 13-18% flipped runes and in none from 33%.
  Rules at or below about 20% flipped runes were therefore already tested by the earlier unsigned screens: C_cur_wp 1.4%, C_cur_ws 5.5%, E_cur_n3 7.6%, E_prev_n3 18.5%, and A_prev_pf / A_prev_pl (95-97% negative, i.e. 3-5% unflipped, nearly the global sign); E_cur_n4 (24%) is borderline. Flip shares of all rules: `work/kscreen/data/signs/rules.tsv` (not tracked).
- **Pointer-direction mechanism: both orientations are needed** (audit A2): negating a direction rule is a reversed key stream, not the multiplier 28.
- **Flat-IoC subset corrected** (audit A4): 5 excluded streams are flat under sign masks (`gematria primes cycle`, `An End hash nibbles`, `primes digit sum`, `payload bytes mod 29` and its reversal); all 61 rules over them: best IoC 1.293, `results/kscreen/signs_extra/`.

## Engine and controls

`work/kscreen/src/main.rs`: an optional `S <+1|-1 per rune>` line per window; rune i is deciphered with key sign s_i (every key value read for that rune, first try, skip and coin, is negated); no S line: decodes byte-identical (the 12 engine tests pass). `gpu.py` refuses S lines.
`work/kscreen/signrules.py` builds the rules and one window file per rule (S lines), a flat-IoC library subset (581 streams: those LP2's flat IoC does not exclude; the others are 60% of the cost and stay non-flat under random-like signs) and `sign_rules.txt` (tracked: the runner reads the names).
**Control** (`sign_selftest.py`, `results/kscreen/sign_selftest.txt`): an independent Python planter (not the engine's `plant`) enciphers held-out English word by word under four rules (E_cur_n4, A_prev_G, B5_prev_R, C_prev_n) with library keys at known offsets, both anti-repeat models and both key signs:
**12 of 12 windows recovered** (best hit = the planted item at the planted offset, IoC 1.60-2.06; re-decode with its signs 1.75-2.02), `signrules.py` reproduces the planter's sign vector from the planted ciphertext, the same ciphertext without its S line stays below 1.40 when 30-70% of the runes are flipped (1.04-1.27),
a decode with another rule's signs at about 50% agreement stays below 1.40 (1.07-1.21), and 30 random keystreams under a rule's signs stay at 1.286.

## Run

Campaign `kscreen-signs` (`python jobs/overnight.py run kscreen-signs --device cpu`): 61 rules x 581 streams x 8 sections at every offset, mults 1 and 28, both anti-repeat models; one rule is 355 M decodes, about 6.4 minutes on 14 CPU threads (about 6.5 h in all); lore-most-plausible templates first (length thresholds, within-word
comparisons, parity, then comparisons and half splits). First rule done by hand: C_prev_n, best IoC 1.331.
Decision rule as for every kscreen: IoC >= 1.40 on the first 300 runes, then whole-window re-decode against the keystream's random offsets (`verify.py`). The total number of decodes is about 2 x 10^10, where random keys reach about 1.37, so the rule has a thin margin.
