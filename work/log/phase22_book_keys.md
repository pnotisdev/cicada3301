# Phase 22: a book as LP2's running key ("OTP-class" from a referenced text) (2026-10-20, desktop)

**Nothing in LP2 is solved.** Prompted by the user: "This may be a OTP-Class. And since Cicada3301 has used a lot of books
and art as reference, maybe we should look closer into those."

## Question

A true one-time pad (uniform random key) cannot be broken from the ciphertext, by any method. The only "OTP-class" key
that leaves anything to find is a pad drawn from public material: here, the letters of a book Cicada referenced (Liber AL,
Agrippa, the Mabinogion, Self-Reliance, the 11th Britannica, Blake, the Bible, Dante, Nietzsche...; the archive under
`Other repositories and work/` names them). Earlier phases excluded an English running key in the standard rune mapping
(PLAN.md phase 3: IoC 1.04-1.06 predicted, LP2 0.9999) and kept book letters out of the key library because they fail
the flat-IoC rule (`docs/HYPOTHESES.md`, constraint 1). Not tested before: **other languages, and a letter -> rune table
other than Gematria Primus**, which an encryptor can choose freely.

## Method (keyless: no book or offset needs to be guessed)

For c = p + m*k (mod 29) the ciphertext's unigram distribution is the circular convolution of the plaintext's and the
key's, so its IoC is 1 + sum over f != 0 of |P^(f)|^2 |K^(f)|^2. It depends on the book only through its letter
frequencies, so a test on 16 Gutenberg texts in six languages (`work/ref/corpora`: English, Latin, Italian, French,
Spanish, German) plus Emerson covers any book in those languages. Plaintext model: Emerson's Essays in GP runes, spelled
with digraph runes (as the solved pages) and letter by letter. Statistic: LP2's IoC over all 12,956 runes (0.99987)
and per section.

- `work/book_key_flatness.py`: per book and key spelling, the IoC under the GP table; 20 real encryptions WITH the skip
  rule (q = 0.81) at multipliers 1, 28, 3, 17; a table-independent Fourier lower bound; and a swap hill-climb (40 random
  starts) for the table that makes the key flattest, then 40 encryptions at the flattest table found.
- `work/tmp/book_key_random_tables.py`: the same IoC under 20,000 random tables per book.
- `work/book_key_pairs.py`: the lag-2..8 pair chi-square (841 cells per lag), with a table searched to flatten the pairs.
- Null for all: uniform random key + skip rule, same length (200 reps; IoC 0.99986 +- 0.00051, max 1.00181).

## Results (`results/analysis/book_key_flatness.txt`, `book_key_random_tables.txt`, `book_key_pairs.txt`)

| Key table | Result | LP2 |
|---|---|---|
| Gematria Primus, multiplier 1 / 28 / 3 / 17, any of the 17 texts | the lowest plant per text and spelling +31.7 to +77.2 null sd (680 plants) | +0.02 |
| Random table (20,000 per book) | 0.01% quantile +11.3 (Paradise Lost) to +21.9 (Les Miserables) sd; median +41 to +71 | +0.02 |
| Table tuned to flatten the unigrams (heuristic search) | predicted +1.9 (Meditations) to +6.3 sd (French); 40 plants at the flattest table: IoC 1.00091 +- 0.00076, 6 of 40 above the null maximum | +0.02 |
| Same, per section (729-3,316 runes) | +0.1 to +0.6 sd | -1.5 to +0.9 |
| Pairs, lags 2-8, unigram- or pair-tuned table (Bible, Paradise Lost) | plants +1.3 to +2.2 sd on average, 1-9 of 30 above the null max | +0.27 |

The table-independent Fourier bound is useless here (+0.7 to +1.1 sd): the digraph-spelled plaintext has one almost flat
frequency (|P^(8)|^2 = 0.0003), and a tuned table puts the key's non-uniformity there.

## What this establishes

- **Excluded:** a running key taken letter by letter from any natural-language book in English, Latin, Italian, French,
  Spanish or German (and, by the same letter statistics, Old English / Welsh translations very likely; not measured),
  under the GP table or any table an encryptor would pick without optimising it (a keyword-mixed alphabet is a random
  table here: fewer than 1 in 10,000 tables comes within +11 sd), any multiplier, either sign, with the skip rule. This
  covers book letters picked at pointer positions (book-code letters) under the same tables.
- **NOT excluded:** the same with a table chosen to flatten the key against the plaintext's own letter frequencies.
  It is invisible to every unigram and pair statistic at LP2's length. It is a deliberate design (the encryptor needs
  both frequency tables) and nothing in the record suggests it, but the flatness argument cannot exclude it.
- **Also not covered:** keys computed from a book (word sums, hashes, prefix sums except the ones in the library, book-code
  numbers used as numbers), images or art as keys (pixel / byte streams: phase 21 screened the scans' signed payloads only),
  and plaintexts that are not English-like.

## Next step (not run)

A table-invariant decoder for a candidate book: group the ciphertext by the key letter under it; at the right book and
offset every group is a Caesar shift of plaintext, so the mean within-group IoC is about 1.8 against 1.0, whatever the
table. The skip rule shifts the alignment every ~36 runes, which is why the H2 table statistic fell from z 41.7 to 1.2
(`phase10_proposals_review.md`); it needs a drift-tracking version (DP over skips). Candidate books: those Cicada cited
(list above), downloaded as data. Controls: a plant with a tuned table and the skip rule; nulls with the wrong book.

## Reproduce

    python work/book_key_flatness.py          # ~40 min on one core
    python work/tmp/book_key_random_tables.py # ~1 min
    python work/book_key_pairs.py             # ~10 min

## Addendum (same evening): E4-letters, power of chanscreen v2 under letter spelling

`work/chanscreen/v2/step3/e4_letters.py` reruns E4's 200 plants (same seeds, streams, offsets, channels, frozen decoder /
LM / T300) with the held plaintext pools spelled letter by letter (TH, ING, EO, OE, AE, IA, EA expanded); 4 workers,
about 6 min. Records `results/chanscreen/e4_letters/`, summary `results/chanscreen/e4_letters_summary/e4_summary.txt`
(the digraph E4 summary is untouched).

| | digraph E4 | letter-spelled |
|---|---|---|
| 300 runes | 200 / 200 | 200 / 200 (50 per channel; winner sign correct 198) |
| 60-rune prefix | 194 / 200 | 180 / 200 (hold 44, spend 40, skip5 48, coin 48) |
| 80-200-rune prefixes | 200 / 200 | 200 / 200 |

The frozen contract keeps its power on letter-spelled English: the n300 and clause-scan negatives stand for it; the
shortest clauses (about 60 runes) lose a little. Viterbi accuracy was not run for these plants.
