# Phase 23: a table-invariant, drift-tracking decoder for a book as LP2's running key (gate only) (2026-10-20, desktop)

**Nothing in LP2 is solved. LP2 was not decoded in this phase.** This file is the spec, the controls and the decision
rule, fixed before any LP2 run. The LP2 screen waits for the user's go-ahead.

## Question

Phase 22 (`phase22_book_keys.md`, row `book-running-key`) excluded a book's letters as LP2's running key under the GP
table or any untuned letter->rune table. It could NOT exclude a table tuned to flatten the key against the plaintext's
letter frequencies: that leaves LP2's IoC only +1.9 to +6.3 sd above a uniform key. Closing the gap needs a statistic that
does not depend on the table. It also has to track the key pointer through the anti-repeat skips (q = 0.81, one every
~36 runes). The H2 coincidence statistic did not track them and fell from z 41.7 to 1.2 (`phase10_proposals_review.md`).

Model under test: c_i = p_i + pi(k_j) (mod 29). Here k is a candidate book in runes (digraph or letter spelling), pi is any
unknown letter->rune table, and j advances by one per rune plus the skips of the anti-repeat rule (as `encrypt_skip`
in `work/book_key_flatness.py`).

## Decoder (`work/book_key_decoder.py`)

At the right book and offset, the ciphertext runes grouped by the key letter under them are each a Caesar shift of the
plaintext, whatever pi is. Two stages:

1. **Table-free beam** (`beam_decode`, numba): the H5 column beam (`work/h5slice`, `beam_coincidence_nats`), with the
   29 key letters as the columns. Per group g it keeps G[g, v] = sum log(29 f(c_i - v)) and scores
   sum_g logsumexp_v (G[g, v] - log 29), so the shift pi(g) is integrated out under a uniform prior and no table is
   assumed (it need not even be a permutation). Each skip costs ln(0.81/29) = -3.58 nats. The pointer branches by +0/+1/+2
   per rune. The beam is 64 states with **up to 8 histories per pointer**. One history per pointer (the h5slice rule)
   lost the true path in 11-14 of 16 plants: the score is not additive, so an early lucky history displaces the true one
   (`work/tmp/bkd_diag.py`, `bkd_diag2.py`). The first 8 pointers are free (`spread` = 8), so a screen steps the book
   offset by 8.
   **Detection statistic = this beam score, in nats per rune against a uniform cipher.**
2. **Hard EM** (`decode`), used only for decryption and verification: the table s is estimated from the beam path as
   a permutation (assignment problem, `linear_sum_assignment`). Then an exact Viterbi over the drift with s fixed
   (`viterbi_fixed`) uses the anti-repeat rule's exact likelihood: a skip is possible only where
   c_(i-1) - s(k_j) = c_i - s(k_(j+1)). The two steps repeat (at most 4 rounds). With the true table the Viterbi
   recovers 99.6% of pointers (`bkd_diag5.py`). The EM score is not used for detection: it overfits the table, and its
   null sd is about 4x the beam's at 300 runes.

Plaintext model f: Walden (digraph runes). Plants use Emerson's Essays (disjoint text).

## Controls (`results/analysis/book_key_decoder.txt`, one run of the final code, 8 processes, ~7 min)

- **Positive:** Emerson plaintext encrypted with key books KJV, Paradise Lost, Meditations, Zarathustra and Republic. Each
  plant has its own **flattening table** (`flattest_table` from phase 22, 3 restarts) and uses the skip rule q = 0.81.
  The decode starts at the screen's grid offset, 0-7 below the true offset. Windows of 300 and 729 runes and the section
  lengths 1,524 and 3,316. Key spelled with digraph runes or letter by letter.
- **Null, per plant:** the same cipher against a wrong offset of the right book, against a random offset of a wrong
  book, and a uniform-key cipher against the right book at the plant's grid offset (612 nulls per statistic in all).
- **Tail (sets the threshold):** 400-3,000 decodes of flat uniform-key ciphers against random KJV offsets.
  Threshold = max(mu + 6.1 sd, exponential tail fitted to the top 5% and extrapolated to p = 5e-10, tail maximum). The
  exponential part decides at every length. At 300 runes the tail is 2-3x heavier than Gaussian at 3 sd (0.0027-0.0037
  against 0.0013). p = 5e-10 = 0.05 / 1e8, the family of 8 windows x 2 spellings x ~6e6 book offsets.

| window | key spelling | power (beam score > threshold) | plant median z | path accuracy (median) | nulls above threshold | cost per book-offset |
|---|---|---|---|---|---|---|
| 300 | digraph | **21/40** | +10.6 | 0.900 | 0/120 | 9.8 ms |
| 300 | letters | **27/40** | +12.1 | 0.950 | 0/120 | 10.1 ms |
| 729 | digraph | **24/30** | +20.7 | 0.994 | 0/90 | 22.3 ms |
| 729 | letters | **28/30** | +22.2 | 0.997 | 0/90 | 22.9 ms |
| 1,524 | digraph | **19/20** | +32.6 | 0.995 | 0/60 | 46.0 ms |
| 1,524 | letters | **17/20** | +31.9 | 0.998 | 0/60 | 44.9 ms |
| 3,316 | digraph | **12/12** | +46.6 | 0.997 | 0/36 | 99.0 ms |
| 3,316 | letters | **12/12** | +48.4 | 0.996 | 0/36 | 98.8 ms |

Cost is single-core time per decode divided by the stride of 8, measured with 8 decodes in parallel on the desktop. It
scales as ~0.033 ms per rune per book-offset. Misses are bimodal: the beam loses the path in the first skips and the score
falls to the null level (path accuracy < 0.5 in 0-8 plants per row). They are not weak hits. The mean decrypted IoC over
all plants is 1.63-1.83 (plaintext 1.77). On average 56-97% of the key letters present get the right table entry.

With the Gaussian 6.1 sd threshold the 300-rune power would be 32-33/40. The heavier tail is why the frozen rule uses the
exponential extrapolation.

## Decision rule (fixed before any LP2 run)

1. **Screen.** For each candidate book and both key spellings, every offset in steps of 8, decode the first 729 runes
   of each of LP2's 8 sections of >= 729 runes (0.10, 9 runes, is skipped), passing the rune before the window as
   `prev0`. Statistic: beam score per rune. **Stage-1 hit:** score > -0.0112 (digraph) / -0.0417 (letters), the
   frozen 729-rune thresholds above.
2. **Verification** (all must hold):
   a. The beam is extended over the whole section from the hit's offset. The section-length score must beat the maximum
      of 200 random offsets of the same book on the same section (matched control) by 5 of their sd.
   b. The EM decryption of the whole section must reach IoC >= 1.40 (plant means 1.63-1.83).
   c. For a key that runs on, the next section's hit (if any) must sit near the end pointer of this one. This is
      reported, not required (a key may restart per section).
   d. The decrypted text is read. **Only a decryption that reads as language is a candidate.**
3. A screen with no stage-1 hit is a negative for these books, under the scope below. A stage-1 hit that fails
   verification is reported with its numbers.

Power of that screen, from the table: per section window 80-93%. For one continuous key, at least one of 8 windows is
detected with probability > 0.999 if the misses are independent. For a key that restarts at an unknown book offset in each
section, 80-93% per section.

Cost of the screen: 8 windows x 22.6 ms = 0.18 s per book-offset and spelling. The KJV (3.0 M digraph + 3.2 M letter
runes) is about 310 core-hours, about 19 h on 16 threads. Emerson's Essays (contains Self-Reliance; 0.31 M + 0.33 M) is
about 32 core-hours. The other candidates are estimated from their Gutenberg sizes, not measured: Liber AL ~0.05 M,
Mabinogion ~1 M, Blake ~0.5 M, Agrippa ~1.5 M. All six: about 1,100 core-hours, about 3 days on one 16-thread PC.
300-rune windows halve the cost at power 53-68% per window. Neither variant has been run.

## Candidate books

- In the repository: **KJV** (`work/ref/corpora/pg10.txt`, git-ignored), **Emerson, Essays First Series**
  (`work/ref/emerson_essays1.txt`, tracked; contains Self-Reliance).
- **Not present, not downloaded:** Liber AL vel Legis, Agrippa's Three Books of Occult Philosophy, the Mabinogion
  (Guest), and Blake (Marriage of Heaven and Hell; Songs of Innocence and of Experience). They would go to
  `work/ref/corpora/` as data only; that folder's `.gitignore` keeps them out of git. Downloading needs the user's OK.

## What this does NOT cover

- Plaintexts that are not English-like (the model f is English; a Latin or Welsh plaintext would need its own f).
- Key texts that differ from our copy. A letter missing from our edition looks like an extra skip (covered at the skip
  cost). A letter **extra** in our edition needs a backward step, which the decoder does not have. Other
  transliterations (numerals, J/V/K handling other than `to_runes`) are not covered either.
- Literal-F or other uncoded runes; the coin variant of the anti-repeat rule; q other than 0.81 (none simulated).
- Keys read backward, with pointer steps other than +1, or computed from the book (sums, hashes, book-code numbers).
- Windows that start mid-section with a key restart inside the window.

## Files

- `work/book_key_decoder.py`: decoder and gate (`python work/book_key_decoder.py`, ~7 min on 8 processes; `--quick` for
  300 / 729 only).
- `results/analysis/book_key_decoder.txt`: the gate output quoted above.
- `work/tmp/bkd_diag.py` .. `bkd_diag5.py`: the diagnostics behind the design choices (per-pointer merge, beam width,
  EM, true-table Viterbi).
