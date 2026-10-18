# Phase 12: outer-alphabet gate, prime-space domain, and the unkeyed-insertion decoder (2026-10-18)

Scope: LP2 sections 0.7-0.15, 12,956 runes. **Nothing in LP2 is solved.** Three fronts ran this round (two
subagents + one background gate), all controlled; files in `work/tmp/` and `results/kscreen/`.

## 1. Outer-alphabet gate (H1 of `work/log/phase11_review.md`): 72 sigma settings x the library on window 0.7

`work/tmp/relabel_gate.py` -> `work/tmp/relabel_gate/summary.txt`, 72 tsvs. Each sigma: relabel the 0.7 window by
sigma_inv (`work/kscreen/relabel_export.py`), then the ordinary screen on the 1,447-stream library, mults 1,28,
models 0,1 (both key signs, both anti-repeat models). 51,108,548 decodes per sigma, 72 x about 55 s.

- **Best 1.3811** at sigma aff:8:0 and aff:21:0 (the same hit: `sha256-ctr mod :1311` offset 14398, one with
  mult 28, the other with mult 1; 21 = -8 mod 29, so the two transforms are the sign mirror of the ciphertext
  term). Second 1.3669 (kw:PRIMES). All 72 settings stay below the 1.40 rule.
- **Null:** rand:300:300 on the same window, same options: best 1.2874 (`work/tmp/relabel_gate/null.tsv`). The
  library's own structured streams sit above the random null (the known overfit effect, `docs/CAMPAIGNS.md:103-105`),
  and 1.3811 matches the plain library's own noise level on one window (the 8-section best is 1.366,
  `docs/registry.toml` lib-sections row).
- **Shift-equivalence found:** the 29 reflections (aff:28:r) all score identically (1.3087 each): p_r = r - c - k
  is a fixed shift of p_28, absorbed by the screen's plaintext-substitution freedom. 29 rotations are likewise
  redundant (`work/kscreen/RELABEL.md:43-46`). The 72 settings therefore carry **44 distinct** information
  settings (26 multipliers, 1 reflection, 17 keywords).
- **Verdict:** negative for the family "outer sigma in {26 affine multipliers, Atbash, 17 keyword alphabets} with
  a library key starting within the first 300 runes of section 0.7" (plant control from
  `work/tmp/relabel_control.txt`: the same machinery recovers a planted sigma at 1.6702). NOT excluded: sections
  0.8-0.15 with these sigmas (about 5 h CPU / 1.5-2 h GPU for the 44 distinct settings), sigmas outside the 72,
  and keys outside the library.

## 2. Prime-space and mixed-domain affine feedback: excluded (`work/tmp/prime_scan_report.md`)

The arithmetic-domain variant of the audit's rune-order assumption (A1 agent). Sweep of
r = (PRIME[c_(i+d)] - a*PRIME[c_i] - b) mod 29 for d = 1..8, all (a, b), within-word pairs, 200-shuffle null;
plus the mixed domains index->prime and prime->index at d = 5, 6.

- LP2 never beats its null: per-domain real max chi2 4152.1 / 953.5 / 40.8 vs combined null max 4423.8 /
  1106.3 / 60.8; the marginal-cancelling same-a z-scores top out at 3.24, 2.60, 3.22 over 336 effective settings
  (look-elsewhere P 0.22-0.85): chance.
- Plant (d=6, a=1, solved keyed sections): chi2/n = 1.97 vs LP2's 0.44 (4.5x power), z 13.9, 0/200 null
  exceedances; residual recovers the plaintext primes at 83.6% of positions (57/57 on unambiguous residues).
- Two information-loss channels of the prime alphabet found: PRIME mod 29 covers only 24 of 29 residues
  (16.4% unrepresentable) and 13.7% ambiguous. An End is null-like (low power).
- **Verdict:** the GP prime order is not the arithmetic domain; GP index order remains the working domain
  (consistent with the index-space lag-6 echo having no prime-space counterpart).

## 3. The unkeyed-insertion decoder (`nulledge`): a powered decoder may not exist as formulated

A2 agent built `nulledge=0|1|2` in `work/kscreen` (0 off; 1 = every word-final rune is a keyless null: not
scored, no key advance; 2 = word-initial). Key measurement (`work/tmp/nulledge_control.txt`):

- **The 42% insertion rate defeats both decoder shapes.** Deterministic word-edge reading (the literal spec):
  plant with a null at every word edge recovers 1.670/1.667 at the exact offset, blindness 1.207/1.219, rand null
  1.355/1.325 - controls pass - but the same reading on a plant with nulls at only 42% of word edges scores 1.27:
  the first null-free word misaligns the pointer and the rest of the window is lost. A per-word beam variant
  (each edge rune MAY be a null) recovers the 42% plant at 1.71 but inflates the random-key null to 1.75: the
  per-word null freedom is key-phase freedom, which cherry-picks phases on random keys.
- So under the IoC framework the "42% of words carry one keyless rune" family has no powered decoder: exact
  reading misaligns, free reading overfits (1.75 > 1.71). This is a measured power statement, not an absence of
  effort; the family moves toward "untestable as formulated" unless a decoder with a word-scoped null prior AND a
  matched null that spends the same freedom is built (the overfit measurement says its null would be about 1.75,
  above any true-key score).
- LP2 screens with nulledge=1/2 against the library: see A2's final report.

## 5. nulledge LP2 screens and the verification of the one rule-trip (`results/kscreen/nulledge1_segments.tsv`)

- nulledge=1 (word-final nulls, 8 section windows, library, mults 1, models 0,1, 204,434,192 decodes):
  best 1.4163 at seg0.14, `sha256-chain reject :<128 bytes 33363336>`, offset 19564, mult 1, model 1 -
  against the matched null (rand:300:401, same option) best 1.3901. Only +0.026 over the null (the verification
  rule needs +0.15), and the scored window has about 229 letters: the known short-window heavy tail
  (`docs/CAMPAIGNS.md:99-100`: windows under about 250 runes exceed 1.40 by chance after ~10^8 decodes).
- Whole-window verification (`kscreen verify ... seg0.14 nulledge=1 controls=20`): IoC falls to **1.0384** with
  8 pointer jumps against the matched random-offset controls (mean 1.0749, max 1.1264). Not a candidate: the
  1.4163 was selection noise.
- **nulledge=2 (word-initial nulls):** best 1.4294 (seg0.11, `sha256-chain mod :2014`, offset 18146) vs the
  matched null (rand:300:402) best 1.3849 - +0.045 over the null, below the +0.15 margin, and every whole-window
  re-decode falls to 1.037-1.063 against matched controls max 1.067-1.146: all flagged hits are noise
  (`results/kscreen/nulledge2_segments_verify.txt`); nulledge=1's remaining hits likewise (1.392 -> 1.041,
  1.368 -> 1.042, ...).
- **Selftest after the engine change: SELFTEST PASSED** (`results/overnight/desktop/kscreen_selftest.txt`);
  nulledge=0 output is bit-identical to the pre-change binary (screen / trace / verify).
- **Verdict (registry row `nulledge`):** deterministic word-edge nulls at 0% and 100% of the word edges are
  excluded for LP2 against the library (both variants, both models); the ~42% mixture - the word-length model's
  actual rate - has NO powered single-window IoC decoder: the free per-word beam recovers the 42% plant (1.71)
  but inflates the random-key null to 1.75 (per-word null freedom = key-phase freedom), and the deterministic
  reading misaligns at the first null-free word (1.27). Untestable as formulated; a decoder would need a
  word-scoped null prior with a matched null that spends the same freedom, whose measured ceiling (1.75) sits
  above any true-key score.

## 4. Word-final echo targets: the word-end null story is dead (`work/tmp/echo_word_final.txt`)

If the lag-6 echo were a null rune (value T(c_(i-6))) inserted at word ends (the H2-null mechanism), the echo
targets would concentrate at word-final positions (expected about 54.5 of 80). Observed 32 of 80 word-final
against 34.7 expected by chance (z -0.6); lag-5: 37 of 104 against 40.3 expected. The echoes sit at uniform
in-word positions; the word-end insertion mechanism is excluded for them.

## 6. New observation: DJU->BEI, the only repeated adjacent word-pair, ends the book (`work/tmp/pair_repeat.txt`)

- The two DJU-BEI occurrences are word-aligned: 0.13 words [28:31] DJU + [31:34] BEI and 0.15 words
  [3310:3313] DJU + [3313:3316] BEI (`work/tmp/dju_words.txt`); DJU and BEI each occur exactly twice in all of
  LP2, both times as this pair (`work/tmp/dju_counts.txt`).
- Over all 2,887 adjacent word-pairs of LP2, DJU->BEI is the ONLY pair that occurs twice. Within-section
  word-shuffle null (1,000 replicates, exact for the word multisets): P(any pair >= 2) = 0.016; P(DJU->BEI >= 2)
  = 0 of 1,000. The second occurrence is the book's final two words (0.15 ends ... CEAIMCX DJU BEI).
- This corrects the older '6-gram repeat chance 0.16' statement (registry obs-flat row updated): the repeat is
  word-aligned, unique among all pairs, and book-ending - the three facts together are what any explanation of
  the book's structure must address (a deliberate ending echo of 0.13's sixth word, key reuse between those two
  positions, or a word-scoped key convention - none decided).

## 7. All-sections keyword relabel and the layout pointer advance (both negative)

- **Keyword alphabets x all sections** (`work/tmp/relabel_all_summary.txt`, `results/kscreen/relabel_all_*.tsv`):
  17 keywords + Atbash, 8 section windows, both key signs and models, about 3.6 B decodes: best 1.3895 (kw:KOAN),
  kw:PRIMES 1.3773, kw:FIRFUMFERENFE 1.3669, atbash 1.3663 - all below 1.40; matched null
  (`results/kscreen/relabel_all_null.tsv`) 1.3346. B lines (separator positions, added for advsep) pass through
  the relabel front-end unchanged.
- **Affine outer sigmas are redundant (verified algebraically, 2026-10-18).** For sigma(x) = a*x + b, the ordinary
  screen with key multiplier a decodes c - a*k = a*p + b, a permutation of the plaintext, so its IoC equals the
  relabelled screen's: the `multipliers` row (all 28 multipliers x the library on all sections, 5.7 B decodes,
  negative, best 1.381 vs null 1.318) already closes every affine sigma. The planned all-sections affine-multiplier
  rerun was cancelled as redundant (the second model's MATH.md makes the same claim). Only arbitrary non-affine
  permutations sigma remain open, which is not a sweepable family.
- **Layout pointer advance** (`advsep=1|2` in work/kscreen, `work/kscreen/ADVSEP.md`, `work/tmp/advsep_report.md`):
  controls passed (blindness 1.213 / 1.097 at truth, recovery 1.667 at offset 100, null 1.286, B-line plant
  1.659; selftest passed). LP2: advsep=1 best 1.3191 below its matched null 1.3682 (no power); advsep=2 best
  1.3288 vs null 1.3055; 0 of 5 and 0 of 5 top hits keep IoC >= 1.40 whole-window (all fall to 1.04-1.15):
  **excluded** - no library key hides behind one extra key value per word boundary, with or without one extra
  per line / page break.

## 8. Review of the second model's work/independent (agent verdicts, `work/tmp/independent_review.md`)

- **Affine outer sigmas redundant: CONFIRMED with full rigor.** All 28 x 29 x 28 = 22,736 (a, b, m') settings:
  decoding sigma_inv(c) with multiplier m' is elementwise the sigma-image of decoding the plain ciphertext with
  m = a*m' mod 29, with identical pointer paths, collision/coin weights and IoC (|delta| < 1e-12); every engine
  branch is a mod-29 equality test. Each pending relabel setting equals an unrelabelled screen at a multiplier
  inside the completed 28-multiplier campaign (`docs/registry.toml` multipliers row): nothing to run. Caveat: the
  library export has since grown 1,439 -> 1,447 streams, so a CURRENT-library multipliers rerun is a library
  refresh (about 35 min GPU / 2 h CPU), not new affine coverage - queued behind the sign campaign.
- **PGP bytes:** 7A35090F = b"z5\t\x0f" (correct; z5z5 would be 7A357A35), but the string is already in the repo
  as keystream hash seeds (`work/grid60.py:105`, `work/prng_screen.py:85`) and thousands of screened streams;
  the Z5-book provenance remains external and unverified.
- **Lag-6-gated keyless-null statistic (echo_nulls): real idea, broken gate.** The summed-path statistic with a
  fixed null prior fixes the free-beam overfit: on a Welcome x totient plant it separates truth from 16 random
  keys at z = +45.9 (rank p = 0.059; rho-freedom inflation only +10..+35 nats vs the free per-word beam's
  1.7547-IoC blowup, `work/tmp/nulledge_report.md:25-29`). BUT its gate fails as specified: (a) on the totient
  stream the true offset 3 is not separated from offset 4 at n = 300 (S(4) = +206.01 vs S(3) = +205.70 - the
  plant's skip redraws let wrong offsets realign at the first redraw site, margin ~2 nats x first-redraw
  position); (b) gate replicas on random keys with their own criterion: 3 of 6 plants fail the >= 10-nat gate.
  Do not authorize a screen from this gate. If pursued: require neighbor-offset separation (+/-1..3), a
  totient/structured-key plant control, and neighbor offsets in the verify controls. Bugs listed in
  `work/tmp/independent_review.md` (offset-valley arc design echo_nulls.py:65-86,213-260; random-key-only plants;
  ~44% chance of zero nulls per unconditioned plant). collision_substitution passed static review (no
  arithmetic bugs found; not executed).

## Registry / status updates

- `open-outer-alphabet`: 0.7 gate AND the all-sections keyword run both negative; the 26 affine multipliers on
  sections 0.8-0.15 remain open.
- New rows: `advsep` (excluded), `prime-domain` (excluded), `nulledge` (excluded for 0%/100% word-edge variants;
  the 42% mixture untestable as formulated, measured).
- `echo-mechanisms`: word-end null insertion excluded for the echoes (targets not word-final, 32/80 vs 34.7).
- `obs-flat`: DJU-BEI sharpened to the word-aligned pair DJU->BEI (section 6).
