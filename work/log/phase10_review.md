# Project review: what the negatives rest on, and what we may have missed (2026-10-18, 02:00)

Scope: LP2 sections 0.7-0.15 and every lane of the project. **Nothing in LP2 is solved.** Read in full: the ledger, the hypotheses, the plan, the campaigns and the session log; checked numerically by `work/families/assumption_checks.py` -> `results/analysis/assumption_checks.txt`.

## Assumptions that hold (checked)

- **The IoC rule.** A correct key decodes to the plaintext; on Cicada's solved text every 300-rune window has IoC >= 1.571 (mean 1.80), on 100-rune windows 99.1% are >= 1.40 (min 1.371). The kscreen rule (>= 1.40 on 300 runes) loses nothing on Cicada's own text.
- **The 120-rune boundary-free lanes (PRNG, hashscan, KDF) are language-robust.** With the English bigram table a true key passes the +300 gate in 98.2% (Latin, Caesar), 99.1% (Vergil), 99.8% (German), 100% (French), 99.9% (Spanish), 99.6% (Italian) of 120-rune windows (English 100%); the 40-rune abort rule keeps 96-99%.
- **No literal F in LP2.** The solved keystream sections write plaintext F as F (it consumes no key value). LP2 has 458 ciphertext F in 12,956 runes (expected 447 +- 21, z +0.5); a literal plaintext F (about 2% of English runes) would add about 260. So LP2 does not use the solved pages' literal-F convention in a single layer; every hypothesis of the form 'the same program as the solved pages with another key' is excluded as stated.

## Gaps found

1. **The OEIS lane's power is for English-like plaintext only** (new caveat; its short windows are the weak ones). True key passes +300 on 60-rune windows: Cicada 96.9%, English 97-99%, French 87%, Spanish 76%, German 70%, Italian 68%, Latin 56%; on 48-rune windows: 81%, 84-90%, 59%, 42%, 35%, 38%, 27%. The ledger's 97% / 81% hold only if LP2's plaintext is English-like.
2. **Unkeyed insertions are not decoded by any screen.** Every decoder moves the key pointer forward only, at a consistent collision. A rune inserted WITHOUT consuming a key value shifts ciphertext and key indices by one for the rest of the window and no skip can undo it. H8 as defined is aligned (the null spends the colliding attempt's key value;
   `docs/HYPOTHESES.md`), and its variant 'c, N, c' is excluded by the lag-2 count. But the word-length fit '+1 rune in about 42% of multi-rune words' (not rejected, p 0.085) is tested only as a length model: an extra rune at word ends without a key value (a check character, a padding rune) would look exactly like that
   and would blind every screen. An outside LLM's audit raised this against H8; it does not hold for H8, but it names a real family. **Proposed:** an engine option `stay` (at flagged word-final or word-initial runes the beam may treat the rune as a null that moves no pointer and scores nothing) with the usual planted control; est. 3-4 h of engine work, about 7 min of CPU per variant.
3. **Layout-driven pointer advance is not modelled and not documented**: an extra key advance at each word separator, line break or page break (a program that enciphers the separator as a symbol). The solved stream page (0.16) shows the pointer running over runes only, so the prior is low; the test is cheap with a per-rune extra-advance line.
4. **The pointer-direction mechanism of the sign family is not built** (design pending an outside LLM's conventions); **H1 / H2** (the drift-tracking decoder; tableaux) remain the large structural blind spots.
5. **Open GPU work** (running or queued): ms months py3 2012-01 .. 2013-02 and java 2012-01 .. 2012-12; page sweeps for the other 7 generators; small-integer seeds on pages; `prng-step`.

## Housekeeping found (fixed in this commit unless noted)

Duplicate numbering in ledger section 0; a stale '+10 per rune' in the hash row; '46 page windows' (the set is 44: pages that start inside an unsolved section and have 120 runes of their own); the sign-flip and per-page rows of section 6 out of date; library size quoted as 1,447 in places and 1,439 in the export (not reconciled);
pending decision for the user: the laptop's commits carry the author name of its git setup (`docs/SESSION_LOG.md`, section 7); the `layer2/combined` runner estimate is 0.6 h but takes 201 s (not changed).
