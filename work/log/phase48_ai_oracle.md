# Phase 48: the A/I oracle (one-rune words -> A or I)

Idea from a community verifier (`work/ref/user_downloads/lp_verify.py`, read as text; **not run, no code copied**; everything below is
re-implemented here, scripts in `work/mech48/`). Nothing in LP2 is solved. Status of this log: a measurement plan plus its results;
every step carries its preregistration, written before the step was run. Step 1 (calibration counts) was run once while exploring
the tools, *before* this file existed, so its preregistration is retrospective for the counting rule only (the rule is the repo's
`lp.word_spans`, fixed in advance of any look at A/I). Steps 2 to 4 were preregistered here first.

## Preregistration (steps 1-4)

**Step 1, calibration.** Word cut = `lp.word_spans` ("page-safe": a bare line or page break inside a word is a typographic wrap, a real
boundary is written `-` or `.`). For each solved section in `lp.KNOWN` (0.0-0.6, 0.16, 0.17), decrypt with the repo's own rule, list
the one-rune words and their plaintext values. Split: deterministic (Atbash/identity/no key: 0.0, 0.2, 0.3, 0.4, 0.6, 0.17) versus
Vigenere-type (0.1 Welcome, 0.5 Koan with FIRFUMFERENFE, 0.16 An End with the prime key). Rate = (A or I)/all one-rune words with a
Wilson 95% interval. Also count LP2's (0.7-0.15) one-rune words with the same cut and list their ciphertext runes, and show how the
count moves if a line break is taken as a word boundary (the community figures, 28 solved and 100 in LP2, will be compared).
Chance level = 2/29 = 6.9% (uniform runes) and, as a second reference, the fraction of A+I among the *plaintext runes* of the solved pages.

**Step 2, statistic and null.** Statistic `O(cand) = (#one-rune words whose candidate plaintext is A or I) / (#one-rune words scored)`
(identity alphabet, shift 0, as in the solved pages). A ciphertext-F one-rune word is scored as it decodes under the skip rule (F stays F,
so it counts as a miss; note what this implies). Null A: random uniform keys, skip rule applied, 10^5 draws on LP2's actual one-rune
ciphertext runes; check against the exact binomial with p = 2/29 (n = non-F one-rune words). Because a uniform random key makes every
decoded value uniform whatever the key index, drift cannot matter for this null; a structured-key null (library stream at random
offsets) is done in step 4. Also the decision threshold: p-value of O under that binomial and the number of one-rune words needed
for p < 1e-4 when O = 0.9. A D/b-invariant variant is defined for use with kscreen hits (whose IoC is invariant under any alphabet
substitution D and shift b): `Opair = max_v mass at {v, v+14 mod 29}` (A=24, I=10 differ by 14), with its null simulated.

**Step 3, re-score past hits.** Inventory: every `results/**/*.tsv` with a `# kscreen` header and `windows=data/segments.txt`
(segment windows only, so one-rune words map cleanly; page / head / stagger windows are counted and skipped), not `pdir`
(pdir hits are mostly nulls by their own summaries and need the D line; they are listed as unscored). Take the 2 best distinct
(item, offset, mult, model) per (file, window). Dedupe identical hits across files. Re-decode the whole segment window with
`kscreen verify` (beam 64, the engine's own skip/coin model 0/1 with the file's header flags), take `plain`, and score O and Opair
on that segment's one-rune words. Report per hit: n one-rune words, O, binomial p. Empirical null: the same procedure on the top hits
of the `*null*` tsv files (random-key / shuffled controls) and the same keystream at 20 random offsets for the top-ranked hits.
Caveat fixed in advance: a beam decode chooses the pointer path by IoC, so O of a decoded window is mildly biased upward; the
empirical null (same decoder on null files) is the yardstick, not the 2/29 binomial. **Flag rule:** O >= 0.5 with >= 5 one-rune words
(O >= 0.5 and beating the null maximum) goes to whole-section verification per `docs/CAMPAIGNS.md`. Segments 0.7 and 0.12 have only 5
one-rune words each: a single hit there can reach O = 1.0 with probability about 1e-6 per decode by chance, but the look-elsewhere
over thousands of hits is not small; the p-values are therefore reported with the number of hits scored.

**Step 4, design only.** Pointer-set DP, no language model: for stream `ks`, offset `o`, multiplier `m`, run the engine's model-0 transition
set (normal / skip-1 / skip-2 with the prev-ciphertext test) over the segment as a *set of reachable pointers* with path counts; at each
one-rune word take the path-weighted fraction of reachable pointers whose decoded value is A or I; sum over the segment's one-rune
words. A cheaper variant scores only the first K one-rune words (small drift). Prototype in numba (one core), measure ms per
stream-offset on a long segment, compare with the IoC screen's cost per stream-offset (`kscreen screen threads=1` on a few items).
Controls: planted-key (English plaintext with its natural one-rune words encrypted under a library stream at a known offset with the
anti-repeat rule, as `kscreen plant` does for IoC) and a random-offset null on the same streams. Power = fraction of planted keys with
statistic above the 99.9th null percentile. Not run at scale.

## Step 1 results (calibration)

Script `work/mech48/calib.py` (and `calib_variants.py`). Page-safe cut, repo decryptions:

| section | kind | runes | one-rune words | A | I | others |
|---|---|---|---|---|---|---|
| 0.0 A Warning | deterministic (Atbash) | 184 | 1 | 1 | 0 | 0 |
| 0.1 Welcome | Vigenere | 515 | 3 | 3 | 0 | 0 |
| 0.2 Some Wisdom | deterministic | 157 | 0 | | | |
| 0.3 A Koan | deterministic (Atbash+3) | 778 | 13 | 9 | 4 | 0 |
| 0.4 Loss of Divinity | deterministic | 755 | 0 | | | |
| 0.5 A Koan | Vigenere | 319 | 9 | 5 | 4 | 0 |
| 0.6 An Instruction | deterministic | 89 | 0 | | | |
| 0.16 An End | Vigenere (primes-1) | 85 | 1 | 1 | 0 | 0 |
| 0.17 Parable | deterministic | 95 | 0 | | | |

| subset | A or I / one-rune words | rate | Wilson 95% |
|---|---|---|---|
| deterministic | 14 / 14 | 100% | 78.5% - 100% |
| Vigenere | 13 / 13 | 100% | 77.2% - 100% |
| all solved | 27 / 27 | 100% | 87.5% - 100% |

**This is not the community's 26/28.** With the repo's decryptions and word cut, the solved pages have 27 one-rune words, all A or I (A: 19, I: 8).
The community's two non-A/I cases presumably come from a different word cut or decryption of the Welcome/Koan pages; unreproduced, see
the open question below. Either way the lower bound is what matters: the rate is at least 87.5% (95%) and in this reading 100%.
Sample size is small and the pages share a few authored sentences (the Koan 0.3 gives 13 of the 27), so "about 90%" for LP2 is an
extrapolation from 5 independent-ish sections.

**LP2 one-rune words**, page-safe cut: **83** (not 100): 0.7: 5, 0.8: 8, 0.9: 11, 0.10: 0, 0.11: 18, 0.12: 5, 0.13: 12, 0.14: 9, 0.15: 15. Their ciphertext runes (per segment: index of rune): in
`work/mech48/calib.py` output; counts per rune: Y 5, M 5, I 5, T 5, P 5, N 4, EA 4, H 4, W 4, others <=3; ciphertext **A occurs only
twice and F once** (see step 2 consequences). If a line break counted as a word boundary there would be 318 "one-rune words" and solved
pages would give 34/83 A or I, so that cut is wrong for the solved pages (it splits words across line wraps), which supports the
page-safe rule. The community's 100 may come from an additional segmentation difference (e.g. numerals or clause marks); not resolved.

Open question (not resolved): the community's 28 and 100 differ from 27 and 83 here. The only other cut tried (line break = boundary) gives
318 and 34/83, which is clearly wrong; a "page-only boundary" variant was written but its edit did not apply, so it was **not run**. Anything
between 83 and 100 one-rune words changes none of the conclusions below, but the exact community figures are unreproduced.

## Step 2 results (statistic and null): `work/mech48/null2.py`, output `null2_output.txt`

LP2's 83 one-rune words: ciphertext F 1, ciphertext A 2, ciphertext I 5. Under the skip rule ciphertext F passes as F and can never be A or I, so
under a strict skip rule the top score is 82/83; that one F word is a small hint about whether F is skipped there (one word, not a test).
Random-key null (10^5 draws): mean fraction 0.0682 (binomial 2/29 = 0.0690 over the 82 non-F words); the tail agrees with the exact binomial
(P(>=10 of 82) MC 0.0558 / binomial 0.0555; P(>=15) 3.5e-4 / 4.5e-4; P(>=20) 0 / 5.6e-7). With O = 0.9 the smallest number of one-rune words giving
p < 1e-4 is 4 (4 of 4); a whole-LP2 oracle of about 75 of 83 has p ~ 1e-77 for a true key. The D/b-invariant `Opair`
(best two values 14 apart) has a null mean of 10.8 of 83 runes (P(>=14) = 0.042, P(>=16) = 0.004): informative only when large.

## Step 3 results (past hits re-scored): `work/mech48/rescore.py`, `rescore_report.py`, `rescore.jsonl`, `rescore_report.txt`

Inventory: 1097 distinct hits (best 2 per file and segment window) from `results/**/*.tsv` with `windows=data/segments.txt`;
665 files with other windows (pages, heads, staggers, direction files) were not scored; no pdir file has segment windows. 789 hits were re-decoded
(beam 64, `kscreen verify`, the file's own flags); 308 were not scored (the decode stops short of the last one-rune word because the keystream ends
before the window does). Of the 789: 610 from real screens, 179 from null files and `rand:` families.

| set | hits | mean O | max O | O >= 0.5 | smallest binomial p |
|---|---|---|---|---|---|
| real hits | 610 | 0.067 (chance 0.069) | **0.40** (2/5 in 0.7 and 0.12; 6/18 in 0.11) | **0** | 9.7e-4 (0.11, lin:3 state 23,6,8; Bonferroni threshold 8e-5) |
| null / random-key hits | 179 | 0.049 | 0.22 | 0 | 3.2e-2 |

Best per segment (real hits): 0.7 2/5, 0.8 2/8, 0.9 3/11, 0.11 6/18, 0.12 2/5, 0.13 3/12, 0.14 2/9, 0.15 4/15. Mean O of beam-decoded outputs equals chance, so the
decoder's IoC-driven path choice does not inflate the statistic. **No past hit is flagged**: none reaches O = 0.5, and the smallest binomial p
over 610 hits is what chance gives (1/610 = 1.6e-3). Limits: only the top 2 hits per file and window; identity alphabet and shift 0 only (D and b are
free in the IoC screen; `Opair` max is 0.60 on real and 0.60 on null hits, no separation), so a hit whose true D is neither identity nor Atbash-like is not tested by O.

## Step 4 (design, pilot scale only): `work/mech48/oracle_screen.py`, `oracle_pilot.py`, `oracle_pilot_max.py`

Prototype: numba, one core, library.ksb streams (580 of 1439 have >= 19000 values). DP over pointer drift d (pointer j = o + i + d), the engine's model-0
transitions (normal; skip-1 / skip-2 when the skipped key value would have reproduced the previous ciphertext), no language model. Two scores:

| variant | planted 0.3 text (13 one-rune words) | planted 0.3+0.5+0.1 (25 words) | null (random offsets, 1000 draws) |
|---|---|---|---|
| path-averaged fraction | planted mean 0.35, power 0.95 | 0.26, power 1.00 | mean 0.068, q99.9 0.24 / 0.16 |
| **best-path count** (Viterbi) | **1.00**, power 1.00 | 0.98 (min 0.56), power 0.97 | mean 0.30 / 0.34, q99.9 0.62 / 0.60, **max 1.00 (13-word case)** |

Planted control: solved plaintexts (0.3, and 0.3+0.5+0.1) encrypted with random library streams and offsets (40 trials each) under the always-skip
anti-repeat rule; null = the same ciphertext scored at 25 random offsets of the same stream (keystream-matched). True offset + 1 still scores
0.85-0.90 under best-path (after the first skip the drift absorbs the shift), so adjacent offsets are not independent.
Findings: (1) the path-averaged score dilutes the true path (every false branch keeps equal weight), so best-path is the score to use;
(2) best-path inflates the null from 0.069 to 0.30-0.34 (a max over a few drift branches per word) and has a heavy tail (one random
offset of a structured stream scored 13/13), so the binomial 2/29 p-values are invalid for it; the null must be measured per stream, or a
conservative p_eff = 0.34 used; (3) power 0.97-1.00 at the q99.9 null threshold for 13-25 one-rune words.

**Look-elsewhere is the binding constraint.** At p_eff = 0.34 with 90% of the words right: 8 words 1.8e-4, 11 words 1.6e-4, 15 words 2.8e-6, 18 words
1.3e-7, 25 words 2.3e-9, all 83 words 1.1e-26. A per-segment screen (5-18 words) over ~1e9 stream-offset-windows therefore yields many false positives and needs a second
stage (IoC, whole-section verification of `docs/CAMPAIGNS.md`): the oracle is a prefilter independent of IoC, not a stand-alone decision. A single
continuous-stream hypothesis across all of LP2 (83 words) would be decisive, but needs the inter-segment pointer rule, which is not known.

**Cost.** Oracle: 3.0 ms per stream-offset over a 3316-rune window (segment 0.15), 0.12 ms for a 300-rune prefix (D = 64, unoptimised, scans the whole drift array).
IoC screen (`kscreen screen`, n = 300, beam 16, abort 150:1.2, 1 thread, 2 library streams x 8 windows): 313,888 decodes in 2.8 s = **about 9 us per decode**.
A 300-rune prefix holds only ~2 one-rune words (LP2 has about 1 per 156 runes), too few for a prefix-only screen, so the oracle needs the whole-segment DP:
about 330x the cost of one IoC decode per stream-offset. A full library sweep of the size of `library_segments.tsv` (4.1e8 decodes) would be ~1.2e6 s (14 days) on one core
unoptimised: usable only as a second-stage filter on IoC survivors or on a restricted stream list. Active-range tracking of the drift array and early abort would
help (estimate, not measured). Not run at scale.

## Summary

| item | result |
|---|---|
| calibration (page-safe cut, repo decryptions) | 27 of 27 one-rune words are A or I (19 A, 8 I); deterministic 14/14, Vigenere 13/13; Wilson 95% lower bound 87.5%; community 26/28 not reproduced |
| LP2 one-rune words | 83 (community: 100); ciphertext F 1, A 2, I 5 |
| null | 2/29 = 6.9%; MC equals binomial; whole-LP2 true key p ~ 1e-77; 4 of 4 already p < 1e-4 |
| past hits (610 real, 179 null) | best O = 0.40 (real) / 0.22 (null); none >= 0.5; none flagged |
| screen design | best-path DP over pointer drift; power 0.97-1.00 (13-25 words); null mean 0.30-0.34, heavy tail; ~330x one IoC decode per stream-offset on a whole segment |
