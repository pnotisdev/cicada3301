# Research: cicadanotebook.com (2026-10-17, laptop)

Scope: LP2 (sections 0.7-0.15). **Nothing in LP2 is solved**, by them or by us. The site was read as data in the
in-app browser (home, guide, journal, sources, name, ethos, the evidence index and two data files), and its 79 session
reports by three read-only research agents (sessions 1-26, 27-52, 53-79). No code from the site was downloaded or run, and
none of its files are committed. Figures quoted from the site are attributed to it; checks run here are labelled OURS and
come from `work/tmp/hyp/` (outputs in `results/analysis/`).

Conventions: their "section k" is our 0.(7+k), so their section 3 is our nine-rune 0.10, which they usually leave out
(12,947 runes and 12,939 transitions instead of our 12,956 and 12,947). Their "LP2 page n" is image n + 17, which is our
transcription page n + 15. Offsets count from zero.

## 0. Summary

- **What it is.** An independent, AI-assisted notebook: 79 sessions, each with a plan fixed in advance, constructed-message
  controls, real results and limits. Its standards are close to ours. **No session claims a solution**, and the author
  rejects every near-miss they find (e.g. the "ALL THINGS" length fit, the period-30 doublet peak, page period 42).
- **One correction to us, now verified in the images.** Our word splitter (`lp.word_spans`) ends a word at every page break.
  In the transcription an unmarked page break is a wrap, the same as an unmarked line break. All 32 unmarked page breaks in
  LP2 show no separator dot in the images, while all 21 marked ones do (section 4.1). Corrected counts: **2,896 words and
  83 one-rune words** (not 2,928 and 99), with lag-5 at z +3.75. The site's inventory matches ours token by token.
- **Confirmed on our data:** rune counts; 86 doublets, section by section, against the same expectations; the repeated
  phrase ᛞᛄᚢ ᛒᛖᛁ at runes 6,555 and 12,950; no rune errors; the corrected base-60 payload is byte-identical to theirs.
- **Corrected in the other direction:** the 1033 / 3301 cuneiform stamp appears 7 times (images 50-56), not 4 (section 4.2).
- **Separators:** the site's transcription, a newer version from the same lineage, has a three-dot class. The 5 three-dot
  marks it reports in the unsolved part are visible in our images too, and our master writes each of them as a plain word
  dot. Words and runes are unchanged; this matters only for punctuation-restart models (section 4.3).
- **Worth adopting: exact keyless bounds.** These rule out whole cipher families without any key search. We reproduced each
  one with planted and null controls:
  - **Doublet floor:** an additive key that ignores the text cannot give fewer than about 207 doublets on English in the
    standard rune order (181-226 per text, 121-172 for five other languages), against LP2's 86. A keyed alphabet can get
    under the floor; section 4.4 gives the search result.
  - **Ciphertext-feedback barrier:** any cipher whose plaintext rune is fixed by the current and the previous ciphertext rune
    gives at most 5.53% for the most frequent plaintext rune. English's E is about 12.5%.
  - **Whole words:** no word of 4 or more runes ever repeats (1,645 words), so no fixed word-level cipher fits.
- **Ideas we have not run:**
  - restarts at typography (red marks, list items, headings, three-dot marks), with the full stream library and the
    site's known-answer controls;
  - bigram-preserving (Euler-trail) surrogate nulls;
  - one-rune words as hard filters;
  - a key-reuse scan anchored on the repeated phrase.

## 1. What the site is

An independent notebook by one author working with ChatGPT ("I bring the questions ... AI helps explore them"). The
author started from a 2012 interest in Cicada and Bitcoin; a link between them is explicitly not established. It has 79
numbered sessions and 644 evidence files (code, JSON, images). Each session has a frozen plan, controls (constructed
messages decrypted exactly), real results and limits, and every session ends in "no new plaintext".

Sources:
- the CicadaSolvers archive;
- the master rune transcription, cicada-solvers/iddqd (SHA-256 b0b2e13c…, retrieved 2026-09-18). It is a newer version
  of the lineage ours comes from (rtkd/iddqd f2267b0): it adds a three-dot separator class and apostrophes;
- the page images from iBotPeaches/cicada_3301, with a SHA-256 recorded per image. The images the agents compared (17, 19,
  50, 56, 73) are byte-identical to our `work/orig` copies;
- English benchmarks: five decoded LP1 groups (about 1,960 runes) plus the solved LP2 page 57.

The usual protocol:
1. Train a small rune language model on LP1.
2. Fit parameters on a word-aligned prefix of at most 256 runes.
3. Decode the untouched rest of the section without refitting.
4. Recover a planted key on page 57, almost always at rank 1.

Shuffle nulls appear only in some sessions. Their whole-section check is a language-model score on the held-out rest,
which is weaker than our whole-section verification, but their exact bounds need no scoring at all.

## 2. The 79 sessions at a glance

"Covered" means our toolkit already ran an equivalent test. "New" means the method is not in our toolkit.

| Sessions | Topic | Their result | Relation to us |
|---|---|---|---|
| 1-2 | Arithmetic streams: primes, p−1, Fibonacci, φ, squares. Offsets 0-256, F rules, resets by line, page, paragraph, clause or word. The base-60 block as a cyclic key | Negative (2.98 M + 1.19 M settings); the page-56 decode ranked 1st | Covered by the kscreen library (about 1,450 streams). Clause and paragraph resets are only partly covered |
| 3 | 43 streams from the page-15 square: \|3301 − p[F(n)]\|, F[p(n)], 464 walks | Negative, offsets 0-16 only | Possibly new streams; check the library |
| 4, 14 | Feedback on word features (word ordinal, length, previous word's sums); word-organised prime and φ schedules | Negative | Special cases of our per-word keys (Phase 9 families) |
| 5, 66-67 | Changing alphabets (move-to-front or back, swap, rotate); previous-symbol exclusion; Euler-trail surrogates that keep each page's adjacent-pair counts | Changing alphabets closed by exact bounds (at most 3.9-5.9% for the top plaintext rune; with section resets, English forces at least 5.7% equal neighbours, against LP2's 0.665%) | New family, now closed. The Euler-trail null is new to us |
| 6-7, 32, 51-53 | The repeated phrase: periodic keys anchored on both copies (global distance 6,395, page 42, section 3,282); two-time pad; recurrence probability; position-only schedules; page period 42 | Negative. Under independent keys a repeated 6-rune two-word phrase has probability ≤ 4·10⁻⁴ (0-2 of 4,999 simulations) | Probability reproduced, 4.3·10⁻⁵ (section 4.6) |
| 8, 15, 21-24 | Old English and Latin; rune-name, literary-phrase, Solitaire and Stephenson keys | Negative | Covered (IoC 1.000, keyword lists) |
| 9, 16 | Cuneiform 1033 / 3301 as keys; motif count | Negative; they count 4 copies | Our count is 7 (section 4.2) |
| 10-12 | Survey; the Agrippa decoder on the payload; the 2012 book cipher | Negative (36-40% ASCII, longest run 5) | Their payload bytes equal our corrected ones, so it is closed for us too |
| 13, 36 | Boundary stripping; word-length self-quotation against solved text | Negative (p 0.97) | — |
| 17-20, 55-57, 62-63 | Typography: numbered list items 1-5 (pages 36-38); red 10- and 13-dot marks; headings; restarts at marks; replays after separator corrections | Negative. On solved text, restarting at marks breaks the known decodes (second koan: 0 errors with the true schedule, 197-204 wrong with restarts) | Our restart lanes use few streams. Their solved-text numbers are ready-made positive controls |
| 25-31, 48 | Doublets: rate by distance, location in words, per section, periodic phase, bursts, "a doublet marks one letter" | Lag 1 only; no location effect; no clustering; no AAA runs; sections not significantly different (Pearson 5.35, p 0.62) | Agrees with Phase 3. Per-section numbers reproduced (section 4.4) |
| 26 | Successor preferences after removing doublets | None beyond uniform | Agrees (χ² 786 against 760 ± 45) |
| 33-35, 39-40, 46-47 | Exact frequency barrier for feedback ciphers: previous rune; periods 2-3; two previous runes; reset per word; exponential multiplier; plaintext feedback | All excluded; memory 2 or more is not constrained | New method. Reproduced, 716 runes = 5.53% (section 4.5) |
| 37-38, 58-61, 73-74 | Images: JPEG structure; an OutGuess crash (an artefact, header FF FF FF FF); image-first re-reading of 9 pages; separator pixel inventory; three-dot screen; glyph reader | No rune errors. Separator-class discrepancies in their master and against ours | Three-dot marks confirmed in our images (section 4.3) |
| 41 | Whole-word repetition | LP1 has 1,385 equal pairs where LP2 has about 10 at matched size; no LP2 word of 4+ runes repeats | Reproduced (section 4.6) |
| 42-45, 54, 68-72, 78-79 | One-rune words: apostrophes; the 83-token inventory; schedules that must turn them into A or I; how many must break the rule; fixed homophonic tables; group-repeat channel; square-state channel | 83 tokens over 28 runes (never C). A fixed table would need 63 of 83 exceptions. The channels fail on held-out text | Inventory reproduced token by token (section 4.1) |
| 49-50 | SHA-256 counter keystreams, decoded with a beam that allows 0-2 skipped key symbols | Negative | Hash keys covered by hashscan. The skip-aware beam is close to our layer2 and bgsweep decoders |
| 64-65 | Berkeley remailer posts against signed Cicada messages | No shared word sequence | Historical only |
| 75-77 | Doublet floor for additive keys that ignore the text | Excluded for LP1-like English (floor 106-170) | Reproduced and extended (section 4.4) |

## 3. Their facts against ours

| Quantity | Site | Ours | Status |
|---|---|---|---|
| Runes, 0.7-0.15 | 12,947 (without 0.10) | 12,956 | Same; 0.10 has 9 runes |
| Doublets | 86 against 445.14 | 86 against 445.36 (0.10 adds 0.22) | Same, section by section |
| Words | 2,896 (2,894 without 0.10) | 2,928 until today; 2,896 corrected | **Ours was wrong** (section 4.1) |
| One-rune words | 83 over 28 runes; never C | 99 until today; 83 corrected, same tokens, never C | **Ours was wrong** |
| Repeated phrase | ᛞᛄᚢ ᛒᛖᛁ at 6,555 and 12,950 (the last 6 runes) | Same | Same |
| Rune errors in the images | None (9 pages re-read image-first; all disputes upheld) | None beyond our errata | Same |
| Base-60 payload | Verified block SHA-256 3b9b07d9… | Byte-identical to our corrected `lp_verified.txt` payload | Same |
| Cuneiform stamp | 4 copies | 7 (images 50-56) | **Theirs undercounts** (section 4.2) |
| Three-dot separators, unsolved part | 5 locations (images 22, 28, 37, 55, 63) | Visible in our images; written '-' in our master | Different transcription class (section 4.3) |
| IoC, within-word lag 5 | IoC ≈ 1.00; lag-5 peak noted (d5 = 477 of 12,939 at distance 5) | IoC 1.000; within-word lag 5 z +3.75 | Consistent |

## 4. Data comparison run here (OURS)

### 4.1 The one-rune words: 83, not 99 (a page-seam bug in our word splitter)

The site's image-audited inventory (sessions 42-43) has 83 one-rune tokens over 28 runes. Ours has said 99 since the
line-wrap fix of Phase 3. A position-by-position comparison (`work/tmp/hyp/singleton_compare.py`, in their page and rune
offset coordinates; their page 0 is our image 17) gives:

- in 0.7-0.14, all 68 of their tokens are ours too, at the same page and offset and with the same rune (68/68);
- our 11 extra tokens there, and 5 extra in 0.15, all sit at the first or last rune of a page.

**Cause.** `lp.word_spans`, and every helper modelled on it, treats a page break as a word boundary. LP2 runs over
transcription pages 15-70. Of the 55 page breaks inside it:

| Page breaks | Count |
|---|---|
| Rune on both sides, no '-' or '.' on either side | 32 |
| '-' or '.' at the end of the page | 19 |
| '-' at the start of the next page (28→29, 32→33) | 2 |
| Bordering the rune-less number-square page 65 | 2 |

The transcription writes a boundary at a line end as '-' or '.', so a bare break is a wrap. Positive control on the solved
sections: every word split by a page break decrypts to a single English word (WH|O, ADHEREN|CE, STOP|PED, ASCE|D =
"asked").

**Image check** (`work/tmp/hyp/page_seam_dots.py`, output `results/analysis/page_seams_2026-10-17.txt`). The detector
counts separator-sized ink components (the size rule of `work/word_gaps.py`) within 1.2 rune heights after the last glyph
of a line, or before the first glyph of the next one. It was calibrated on every line end inside the LP2 pages:

| Line ends | Count | Dot found |
|---|---|---|
| Mark after the last rune | 121 | 120 after the last glyph |
| Mark before the next line | 30 | 30 before the next first glyph |
| No mark (wrap) | 388 | 4 on either side (1.0% false positives) |

| Page breaks | Count | Dot after the last glyph | Dot before the next page's first glyph |
|---|---|---|---|
| Mark at the end of the page | 19 | 19 | 1 |
| Mark at the start of the next page | 2 | 0 | 2 |
| **No mark (the 32 in question)** | **32** | **0** | **0** |

The transcription is right and our splitter was wrong. With page breaks treated as wraps (`work/tmp/hyp/notebook_checks.py`,
section 1):

| Quantity | Page break = boundary (until now) | Page break = wrap (corrected) |
|---|---|---|
| Words | 2,928 | 2,896 |
| One-rune words | 99 | **83**, by section 5 / 8 / 11 / 0 / 18 / 5 / 12 / 9 / 15 (the site's counts exactly) |
| 2-rune share | 15.9% | 15.5% |
| Mean word length | 4.425 | 4.474 |
| Within-word lag-5 coincidences | 102 of 2,073 pairs, z +3.67 | 104 of 2,105, z +3.75 |

No conclusion changes: the lag-5 excess and the word-length shape stand. But every word-level count in `PLAN.md` and the
logs used the old convention. The toolkit fix (`lp.word_spans` and the exports built on it) was done the same day as a
separate change: `work/log/page_seam_fix_2026-10-17.md`.

### 4.2 The cuneiform stamp: seven copies, not four

The site's name page counts four copies of the 1033 / 3301 inscription (LP2 pages 33, 35, 38, 39). A contact sheet of
images 49-57 (`work/tmp/hyp/cuneiform_check.png`) shows it on image 50 (bottom) and images 51-56 (top). That is LP2 pages
33-39, seven copies, as our research note of the morning said.

### 4.3 Three-dot separators

The site's newer transcription has a separator class ';' for three-dot marks. It reports 5 of them in the unsolved part
that our master writes as a plain word dot '-'. Counting separator-sized components with our detector, all 5 are in our
images:

| Image (their LP2 page) | Line(s), 0-based | Dots counted |
|---|---|---|
| 22 (5) | 4/5 | 3 at the end of line 4, 1 at the start of line 5 |
| 28 (11) | 10/11 | 3 at the end of line 10, 1 at the start of line 11 |
| 37 (20) | 5/6 | 1 at the end of line 5, 3 at the start of line 6 |
| 55 (38) | 1 | a 3-dot gap inside the line |
| 63 (46) | 4 | a 3-dot gap inside the line, gap 9. Our `results/analysis/separator_audit.txt` had flagged it as "word against clause" (three small blobs) |

Our detector counts dots; it does not see their arrangement. The 3 + 1 groups at line breaks could equally be one four-dot
clause mark split by the wrap. Either way the effect is limited:
- every mark is a word boundary in both transcriptions, so words and runes are unchanged;
- only models that restart a key at punctuation are affected;
- on solved pages, the site shows that keys run straight through three-dot marks (their sessions 60-62).

A full diff of their newer master against ours would need a download (the user's OK).

### 4.4 Doublets: per section, and the floor for keys that ignore the text

The output is in `results/analysis/cicadanotebook_checks_2026-10-17.txt`, sections 2, 3 and 3b.

**Per section**, observed against Σ n(n−1)/N, the exact expectation for a random reordering of the section:

| Section | 0.7 | 0.8 | 0.9 | 0.10 | 0.11 | 0.12 | 0.13 | 0.14 | 0.15 | Total |
|---|---|---|---|---|---|---|---|---|---|---|
| Observed | 4 | 6 | 9 | 0 | 10 | 11 | 13 | 12 | 21 | 86 |
| Expected | 24.81 | 39.62 | 59.55 | 0.22 | 65.30 | 34.96 | 52.11 | 54.55 | 114.24 | 445.36 |

This is the site's table exactly (session 29). Split in halves, 0.7-0.11 keeps 15.3% of its expected doublets and
0.12-0.15 keeps 22.3%: their "57 against 39.5" (session 25). Across all sections the difference is not significant
(Pearson 5.35 on 7 df, p 0.62; session 29).

**The floor** (their sessions 75-77). Suppose c = p + k, or k − p, or a·p + b + k with fixed a and b, and the key's
increments are independent of the plaintext's. Then P(doublet) = Σ_j q(j)·p(−j) ≥ min_d p(d) at every position, where p
is the plaintext-increment distribution and q the key-increment distribution. This holds whatever the key: periodic,
running key, PRNG, hash, OEIS. Floor = 12,947 × min_d p(d), with English converted to runes as in `work/sim.py`:

| Reference | Runes | min_d p(d) | Floor (doublets) |
|---|---|---|---|
| LP1 plaintext, 0.0-0.6 | 2,797 | 1.323% | 171 |
| English, 12 texts pooled | 7.54 M | 1.600% (d = 18) | **207** |
| Each English text | 15 k - 3.0 M | 1.40-1.74% | 181-226 |
| Italian, French, Spanish, German, Latin (6 texts) | 0.12-1.6 M | 0.94-1.33% | 121-172 |
| **LP2 observed** | | | **86** |

Controls:
- **Positive:** the constant key step that attains the floor, on 582 English windows of LP2's length: mean 207.3 doublets,
  minimum 123, 1st percentile 142. Even choosing the best step separately for each window (which uses the plaintext)
  never goes below 87.
- **Null:** a uniform random key gives a mean of 448.9.

So in the standard rune order, or any affine relabelling of it (Atbash included), **no additive key that ignores the text
can produce LP2's doublet count**. The encryption must look at the text or the ciphertext, which is the collision or skip
rule that `PLAN.md` already assumes, or feedback. This generalises our Phase 3 simulations from specific generators to
every key.

**Keyed alphabets** (`work/tmp/hyp/keyed_floor.py`). With an arbitrary rune permutation s before the key (c = s(p) + k),
the bound becomes the cheapest 29-cycle of English bigram probabilities. That is at least 0.134% (an assignment bound) and
at most 0.149% (a cycle found by annealing), about 19 doublets. So the floor alone does not exclude keyed alphabets. LP2
also needs the other 28 difference bins flat. For each alphabet the search fits the best key-increment distribution q ≥ 0
to all 29 bins, and hill-climbs over alphabets:

| Text | Doublets | χ² at the planted alphabet | Best χ² found by the search |
|---|---|---|---|
| Standard order (LP2) | 86 | — | 506.8 (the floor again) |
| Planted family member 1 | 363 | 56.4 | 1.5 |
| Planted family member 2 | 474 | 33.8 | 9.6 |
| Planted family member 3 | 524 | 24.2 | 0.8 |
| Collision-rule text 1 (English, uniform key, 81% of repeats redrawn: the model that matches LP2) | 89 | — | 66.4 |
| Collision-rule text 2 | 72 | — | 104.5 |
| **LP2, keyed alphabet** | 86 | — | **56.6**; the fitted model predicts 126 doublets, and the doublet bin carries 19 of the 56.6 |

The planted members are English windows with a random alphabet, a random sparse q and a random-walk key. The search finds
better fits for them than their true alphabet does, so the family is flexible enough to over-fit its own histograms.

No alphabet found reproduces 86 doublets with the other bins flat. But LP2's misfit is within the range of true family
members (24-56), so this lag-1 test **cannot exclude keyed alphabets**. The question stays open, at low priority: it needs
both a designed alphabet and a designed key-step distribution, where the collision rule needs neither. A sharper test would
minimise the doublet bin subject to flat other bins, or add the lag-2 and unigram statistics.

### 4.5 The ciphertext-feedback barrier

Their session 33: p_i = π(c_i) − π(c_{i−1}) + r for an unknown rune permutation π, relaxed to an arbitrary bijection σ_x
for each previous rune x with σ_x(x) = r. Output bin r collects every doublet, and each other bin receives one
off-diagonal cell from every row. Sending the j-th largest cell of every row to bin j gives the most concentrated
histogram possible: it majorises every other, and entropy is Schur-concave.

| Quantity | Value |
|---|---|
| **LP2 bound** | no plaintext rune above 716 of 12,947 = **5.53%**; entropy at least 4.7895 bits (the site: 716, 5.53%, 4.7894) |
| LP1 plaintext, actual | top rune 12.51%, entropy 4.268 bits |
| Positive controls: English through the cipher with a random π (3 runs) | bound 14.64 / 13.38 / 10.59% ≥ true top rune 14.64 / 13.38 / 10.20%; entropy floor ≤ true entropy |
| Null: random text, 81% of repeats redrawn (20 runs) | bound 5.46% (range 5.32-5.58) |

LP2 looks exactly like random text under this bound. Any cipher whose plaintext rune is fixed by the current and the
previous ciphertext rune, linear or not, is excluded. Their sessions 34, 39-40 and 46-47 extend this to periods 2-3, two
previous runes (linear) and resets at each word. Memory of two or more previous runes is not constrained (15.6%, the same
as the random null).

### 4.6 Whole-word repetition and the repeated phrase

Corrected words, from `notebook_checks.py` section 5. "Uniform" means the expected number of equal pairs for uniform words
without doublets.

| Length | LP2: words / distinct / equal pairs (uniform) | LP1 plaintext: equal pairs (uniform) |
|---|---|---|
| 1 | 83 / 28 / 107 (117.3) | 181 (11.2) |
| 2 | 448 / 354 / 106 (123.3) | 1,547 (16.7) |
| 3 | 720 / 704 / 17 (11.4) | 825 (0.6) |
| 4+ | 1,645 / **1,645** / **0** | 355 |

Any fixed, invertible word-to-word cipher, nonlinear ones included, keeps the plaintext's repeats. LP2 has none above 3
runes and only random-level repeats below, so it behaves like a one-time pad at word level (their session 41).

**The phrase.** LP2 has 345 two-word spans of 6 runes, 183 of them shaped 3 + 3. The only repeated one is D J U | B E I.
If the ciphertext were uniform without doublets, the expected number of identical pairs would be 4.3·10⁻⁵ (the site
simulates ≤ 4·10⁻⁴). The statistic was chosen after the phrase was noticed, and a few dozen other coincidences would have
drawn attention too. So treat it as about 10⁻³, still a hint of key or state reuse between global offsets 6,555 and 12,950
(6,395 = 5 × 1,279). Section offsets are 28 and 3,310; page offsets 28 and 70.

## 5. Ideas worth taking, ranked

1. **Exact keyless bounds as a standard first screen.** These include the doublet floor, the feedback barrier, the
   per-state peak bound (any substitution for each state of a known state function: period, page offset, previous runes)
   and the one-rune forced-mass bound for fixed tables. Each takes seconds, needs an exhaustive small fixture or a planted
   control, and decides a whole family. It extends our Phase 10 keyless tests.
2. **Restarts at typography with the full library.** Candidate restart points:
   - the red 10- and 13-dot marks (the two 10-dot marks bracket the numbered list at 0.14 offsets 754 and 1,307);
   - list items 1-5 counted from their labels;
   - the five internal red headings;
   - the page-33 block split;
   - three-dot marks.

   The site tried only 3 streams. The second koan and page 56 are ready-made positive controls: their numbers show which
   restart rules break known decodes (session 62).
3. **Bigram-preserving surrogates.** Random Euler trails keep each page's exact adjacent-pair counts. They are a stricter
   null for the phrase, the lag-5 echo and the S-concentration of the lag-5 coincidences.
4. **One-rune words as hard filters, using the corrected 83.** For any candidate family, list what each one-rune word can
   decode to across all parameters; one impossible word kills the family. Page 0 offset 176 (EA) is a strong witness.
5. **A key-reuse scan anchored on the phrase.** Under the skip model the key-index gap between the copies is 6,395 plus
   the skipped key symbols. A periodic or restarting key must give equal six-rune key windows at that gap. This is the
   "key reuse between sections" lead in `docs/SESSION_LOG.md` with a concrete anchor.
6. **The 43 page-15 square streams** at every offset, if our library lacks them; the site tried offsets 0-16 only.
7. **Held-out continuation with a skip-tolerant beam** (0-2 skipped key symbols) as a second check for screen hits.

## 6. What to do with it

- **Toolkit fix, a separate change, done the same day** (`work/log/page_seam_fix_2026-10-17.md`). `lp.word_spans` now
  treats '%' like '\n', and so do the helpers modelled on it (`work/word_gaps.py` keeps lines per page and is unaffected).
  The word-based exports were regenerated and the word-level analyses rerun: the one-rune crib, the word-length tests,
  within-word lag 5, the per-word key tests and the Phase 9 family fingerprints.
- **Transcription.** No rune changes. The five three-dot marks could be added as a separator class if we ever test
  punctuation restarts. A diff against the site's newer cicada-solvers master needs the user's OK to download it.
- **Doublet floor.** It confirms that the anti-repeat rule (or feedback) is a necessary part of any additive model in the
  standard order. Keyed alphabets: see section 4.4.
- **Not adopted:** their scoring (an LP1 trigram model on prefixes of at most 256 runes) as evidence. Our whole-section
  verification stays the bar.
