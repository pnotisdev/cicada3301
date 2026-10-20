# Phase 34: coverage map of the signed 2016 message read literally

Message: "Liber Primus is the way. Its words are the map, their meaning is the road, and their numbers are the direction." Nothing in LP2 is solved. Row ids are those of `docs/registry.toml` (read 2026-10-20). Order = a rune's index 0-28; value = its Gematria Primus prime 2-109 (the table distinguishes them).
Costs: "14 thr" = hours on the 14-thread campaign engine (one full kscreen sweep of the 581 flat streams on the 8 sections = 355 M decodes = about 6.4 min); a planted-key control exists for every kscreen-type test (power: the sign and pdir planters recover 11-12 of 12 windows at the exact offset).
Tiny check run for this note (1 core, seconds): `work/phase34_clause_ioc.py` -> `results/analysis/phase34_clause_ioc.txt`.

## 1. "Its words are the map" (positions, lengths, boundaries as addresses or a route)

| mechanism | row | status / power / what it does NOT exclude |
|---|---|---|
| one key per word (constant, linear, periodic in the word) | per-word-keys, skeleton5 | excluded (strong for cribs, the dictionary tests are blind if the separators are not boundaries) |
| key restarts at word / line / sentence / paragraph / page / heading | restart-units, restart-library, typo-restarts, open-clause-windows | excluded for the units tested; not the 9 section starts (control only Z 2.7); short heading windows |
| word boundary consumes a key value (+1 per boundary, +1 per line/page) | advsep | excluded; NOT other advances (n, 2, rule-chosen) or advances at only ~42% of the boundaries |
| word edge is a keyless null | nulledge, open-unkeyed | excluded for 100% of the edges; the 42% mixture is untestable |
| segmentation depends on the ciphertext | segmentation-dependence | excluded above ~6-12% of the boundaries |
| position-in-word / (length, position) schedules | word-position-schedule | excluded for schedules on more than a quarter / half of the words |
| word lengths as pointers into a text (book codes) | book-codes | partial: word Gematria SUMS as pointers, 12 pointer sets x 10 formats x 4 books, negative; word LENGTHS are not a pointer set |
| word order permuted before encryption (route through the text) | transposition | undetectable by the row's own statement; not testable |
| the ciphertext route: lines/columns/boustrophedon/spiral read order | layout27, transposition (AFTER encryption, seams and doublets only) | only 27 x 27 and the seams are covered; other routes **untested** |
| LP2's own word-LENGTH or word-SUM sequence (numbers of the text) as an additive key stream | ciphertext-key (rune ciphertext only), hyp-streams (sums of the SOLVED plaintext) | **untested** for LP2's own length/sum sequences |
| word-length-driven pointer jump (key pointer advances by n_w at each word, or by a rule-chosen 1-3) | advsep (only +1), clock (rune-level steps) | **untested** |

## 2. "Their meaning is the road" (the solved text or its meaning as key or route)

| mechanism | row | status |
|---|---|---|
| hash streams of the 12,944 solved words and phrases | hashwords | excluded; other hash conventions and passphrases not in the solved text |
| prefix / word sums of the solved plaintext, Self-Reliance, decimations | hyp-streams | excluded (flat streams only) |
| keywords of the solved pages (DIVINITY, CIRCUMFERENCE, FIRFUMFERENFE) and any periodic key | periodic, fingerprint-families, layer2, open-layer2-slices | periodic keys to period ~400 excluded (drift-aware); layer2 slices solved keys x streams still open |
| a book as running key, any table: GP table / untuned tables excluded; tuned table -> table-invariant decoder | book-running-key, book-key-decoder, open-sources | the book screen is running (booknight); the SOLVED LP1 plaintext letters as the book are not in the list of books (16 Gutenberg + Emerson + the cited books): **untested** |
| the solved text's own numbers (prime sums of sentences) | lp1-prime-sums | observed only; says nothing about LP2's key |
| key constant per CLAUSE, chosen from the clause (sum, length) | per-word-keys (words only) | **checked now:** mean within-clause IoC of the clauses of >= 25 runes is 0.93-1.09 in every section (shuffle null 0.99-1.00, sd 0.02-0.05), never near the ~1.7 a constant shift would leave. Excludes clause-constant shifts; says nothing about a shift that changes inside a clause. |
| meaning-selected alphabet / outer alphabet | open-outer-alphabet, open-h2 | open |

## 3. "Their numbers are the direction" (signs, pointer direction, reading direction, steps; from order or value)

| mechanism | row | status |
|---|---|---|
| sign of the key per word from a number of the word (61 non-circular rules; order and prime-value quantities G, R, f, l, pf, pl; mod 2/3/5/7/29, comparisons, thresholds) | signs | excluded (best 1.388, noise); NOT rules on the page / line / section NUMBER, nor circular rules |
| sign per rune, periodic templates (period 2-5) | open-sign-periodic | excluded (built and controlled); longer periods not |
| pointer direction per word (122 vectors + 10 GP-value vectors, 18 conventions) | open-direction | engine, reference, planter and gates built (phase 30); pilot negative on 1% of the library; stage 1 (6 of 18 conventions, windows 0.7+0.8) queued (`jobs/queues/pdir.txt`); 12 conventions **untested** |
| key read backward through the whole text, with/without ciphertext feedback | reverse, ciphertext-key | excluded |
| clocked pointer: step = 1 + index, prime or prime - 1 of the cipher or plain rune (order AND value) | clock | excluded (six clocks); the first ~9,000 terms only for the prime clocks |
| step in the step (difference) domain, mod 28 | step28, open-prng-step | excluded (variants A-C); seed sweeps open |
| feedback in the prime-VALUE domain (affine, mixed index/prime) | prime-domain | excluded for affine feedback; arithmetic mod larger moduli untested |
| multiplier 28 (negated key) | multipliers | excluded; the multiplier 28 is also the global sign flip |
| direction of the reading of the ciphertext (a word, a clause or a line read right to left after encryption) | none | **untested** (not a pdir convention: the key runs forward, the runes are written reversed; equivalent to decoding a transformed window with the DEFAULT engine) |
| direction rule from the page / line / section number (even pages backward, alternate lines) | signs / open-direction use word, page-word and clause-word INDEXES, not page or line numbers | **untested** |
| rule-chosen pointer STEP (a, b in 1..3 from a word number) | none (round-4 B2, "six times the sign campaign") | **untested**, 39 h on 14 thr in full |
| arithmetic in the value domain mod M (e.g. p_value + k mod 113 mapped back) | prime-domain gap | structurally weak: the result is not a prime of the table in general; untested |

## 4. Untested mechanisms, ranked by plausibility x power / cost

Plausibility 1-5 (my judgment from the message wording and how Cicada used numbers), power 1-5 (5 = a planter of the same family recovers the key at the exact offset, as signs and pdir did), cost in hours on 14 threads (floor 0.2 h for code and controls). Score = plausibility x power / cost.

| rank | mechanism | plaus. | power | cost | score | cheapest controlled test |
|---|---|---|---|---|---|---|
| 1 | LP2's own word-length and word-sum sequences (per section, per page; lengths, G sums, R sums, mod 29) as additive key streams | 2 | 5 | 0.2 | 50 | build ~12 KSB streams, run the existing screen (`--streams`), planter = sign_selftest style; seconds per stream on 1 core |
| 2 | word-length-driven pointer jump (advance n_w, or 2, per word) and the rule-chosen step | 3 | 5 | 0.3 (n_w and 2: two sweeps) | 50 | generalise `advsep` to `advsep=<n>` / word length (a few lines of Rust, bit-identical default), planter + null as for advsep; each variant 6.4 min on 14 thr (~1.5 core-h); the full rule-chosen step (B2) is 39 h and ranks last |
| 3 | ciphertext written reversed per word / per clause / per line | 3 | 5 | 0.4 (3 sweeps) | 37 | transform the windows (reverse runes inside each word, clause, line from the L/B lines), run the DEFAULT engine; plant in the same transformed way; control = untransformed plant is blind |
| 4 | direction / sign rules from the page, line and section NUMBER (parity, mod 3, half splits) | 3 | 5 | 0.4 (6 rules as signs) or 3.4 per rule x convention as pdir | 37 | add rules to `signrules.py` (tokens give page and line), run kscreen-signs on them (6.4 min each on 14 thr), `sign_selftest` planter extended; pdir later for the surviving rule types |
| 5 | the SOLVED LP1 plaintext letters (and the three solved keywords repeated) as the running-key book | 3 | 3 | 3 | 3 | add to the booknight list (table-invariant decoder, same gate: 9/12 plants); needs the clean text of the solved pages |
| 6 | the remaining 12 pointer-direction conventions (c = 1, 2) | 3 | 5 | 41 | 1.8 | after the stage-1 result: windows 0.7+0.8, 3.4 h per convention, same gates |
| 7 | route transpositions of the ciphertext (columns of width 2-60, boustrophedon, spiral of a 27 x 27 / 29 x 29 layout) | 2 | 4 | 6.4 (58 routes) | 1.25 | permute the windows, default engine; plant through the same permutation; note a transposition that does not keep the key order for the whole window gives no signal in short windows, so use the full section |
| 8 | rule-chosen pointer step (round-4 B2) | 2 | 5 | 39 | 0.26 | only after 2 above |
| 9 | prime-value domain arithmetic mod M | 2 | 2 | needs a new decoder | <0.2 | design first; a mapping of the result back to a rune is the open point |

What the map says: the message has three clauses and the "numbers = direction" clause is where nearly all the tested work sits (signs, clock, step28, reverse, periodic signs, pdir). The "words = map" clause is covered only for boundaries as events (restart, +1 advance, null); the word-LENGTH sequence as a number stream and as a pointer step is open, and so is the reading direction of the ciphertext itself. The "meaning = road" clause is covered for hashes and sums of the solved words and for cited books; the solved plaintext letters as the key text are the visible gap.
