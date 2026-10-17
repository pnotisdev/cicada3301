# DeepSeek round 3: the ledger read by the outside LLM, and what its audit found (2026-10-17, 23:30)

Scope: LP2 sections 0.7-0.15. **Nothing in LP2 is solved.** `work/ask_deepseek.py` (pi, deepseek-flash, medium thinking, no tools, no project files; 4 min 13 s) was sent a self-contained brief plus two of our documents verbatim, `docs/NEGATIVE_SPACE.md` and
`docs/HYPOTHESES.md` (privacy-checked first: no names or absolute paths), and asked for (A) up to 5 hypotheses outside the ledger and (B) an audit of up to 3 ledger entries. Prompt and reply: git-ignored `work/ref/deepseek/` (third-party text is data).

## Part B, the audit: one hit, one near-miss, one already known

| claim | verdict |
|---|---|
| **B3** The OEIS row's exclusion is overbroad: 'a true key scores about +360 over 36 runes against the +300 gate'. | **Correct, and stronger than it said.** `work/families/true_key_score.py` -> `results/analysis/true_key_score.txt`: a correct key decodes to the plaintext, whose boundary-free score on Cicada's own solved text is **+7.3 per rune** (all solved sections; Emerson in sample +7.8, five held-out books +7.1 to +7.9), not +10. A 36-rune window therefore scores about +263 on average and passes the +300 gate in only **29%** of windows (solved text; 14-50% by section; 5th percentile +176). The OEIS lane (36-rune windows, gate +300) had about 29% power per window: about 94% if the key restarts at every one of the 8 sections (8 windows at offsets 0-127), 29% for a continuous pad. Its negative is partial, not strong. |
| B2 'one pad from the start of 0.7' leaves 'a seed plus an unknown discard offset' unstated under 'does not exclude'. | Fair as a wording gap: the sweeps start the pad at the first output. Now listed under 'does not exclude'. Not tested (every offset multiplies the cost). |
| B1 The H8 control may not test H8: a null insertion shifts ciphertext and key indices, which the forward-only skip decoder cannot undo. | **Does not hold for H8 as defined.** In `work/null_insertion.py` the null is emitted in place of the colliding attempt, which has already spent its key value; the real rune uses the next one, so ciphertext and key indices stay aligned and a decoder that never skips reads it (the log says so: null with key j, real rune with key j + 1). The variant in which the null spends no key value re-emits the same rune after it (c, N, c) and gives a lag-2 excess LP2 lacks (`docs/HYPOTHESES.md`, H8, which the reply had in its prompt). The docstring 'no key value spent' was misleading and is fixed. |

**What stands and what changes.** The 120-rune boundary-free sweeps (all PRNG sweeps, hashscan and the KDF lane: windows of 120 runes, abort after 40 runes below +60, gate +300) are unaffected: on solved Cicada text every 120-rune window scores at least +300 and the 5th
percentile is +496 to +807 (+658 or more on the held-out books); the first 40 runes pass the +60 abort rule in 99.6-100% of windows. The ledger's figures 'about +10 per rune' and 'about +1200 over 120 runes' were Emerson-in-sample optimism; the measured values are +7.3 and about +880. Only the OEIS lane
(36-rune windows) lost power. **Remedy, not yet run:** rerun the OEIS lane on 120-rune windows (the abort rule makes the cost about the same as before, a few CPU hours).

## Part A, the five new families

| family | streams | assessment |
|---|---|---|
| A1 g^i mod 3301 reduced mod 29, g a primitive root of 3301 | 800 (period 3300) | new, uniform (counts 113 / 114), cheap |
| A2 i^e mod 3301 reduced mod 29, e coprime to 3300 | 799 (period 3301) | new, uniform, cheap |
| A3 AES-CTR / ChaCha20 / Salsa20 from 10 passphrases | 30 | **duplicate**: the KDF lane already ran 23,976 passphrases through RC4, AES-128/256-CTR, ChaCha20, PBKDF2 and scrypt (719,280 streams, 120-rune windows); only Salsa20 is new |
| A4 Josephus elimination order for N = 12956, step 2..29, mod 29 | 28 | uniform within 1; arbitrary motivation |
| A5 floor(i sqrt p) mod 29 for 12 primes | 12 | quasi-linear key (steps of 2 or 3 mod 29), marginal to be checked by the flat-IoC filter |

The reply was honest ('all five are long shots', lore marked UNSURE, no invented citations). A1, A2, A4, A5 (1,639 streams) are cheap to build with `sacred.py`; not built in this entry.
