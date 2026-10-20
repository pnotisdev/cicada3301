# Phase 23 stage 2: whole-section verifier for booknight hits, and a sentinel-safe summary re-reader (side session, 2026-10-20)

Nothing in LP2 is solved. No stage-1 hit existed when this was written (liber_al, blake_songs, blake_mhh: 0 hits; later books were still running). The queue's files were only imported, never edited.

## What was built
- `work/book_key_verify.py`: the verifier of the spec's decision rule step 2.
  - `hit <book> <digraph|letters> <offset> <section>`: decodes the WHOLE section from the hit's grid offset with the table-free beam (8 free starts cover the true offset inside the cell) and then hard EM (`book_key_decoder.decode`: assignment-problem table + exact skip-rule Viterbi).
  - **Verified only if both hold:** (a) the section-length beam score per rune beats the maximum of 200 beam scores of the same book at random offsets by >= 5 of their sd; (b) the EM decryption has IoC >= 1.40.
  - **Also reported, not gates:** recovered table, decrypted text (with word breaks for a real section; a human must read it, spec 2d), bigram score per rune (Walden bigram model, nats against uniform), prime-sum check of the decoded clauses (`work/prime_check.py`), matched EM nulls (20 random offsets of the same book; 20 uniform-key ciphers with the decoded plaintext's statistics at the hit's offset), the end pointer (spec 2c: compare with the next section's hit).
  - `gate [--quick]`: plants through this same code path -> `results/analysis/book_key_verify_gate.txt`.
- `work/book_key_summary_fixed.py [machine]`: re-reads the chunk files; a (chunk, window) stats row whose mean is below -1 (the -1e18 sentinel, see `phase23_review.md`) is dropped from mean/sd and counted; `top` and `HIT` lines are kept (they come from individual scores). Output `results/analysis/book_key_screen_<machine>_fixed.txt`, with the verify command printed next to every HIT. On the three finished books it gives own z +3.1 to +4.3 where the old summary printed +0.0, e.g. liber_al digraph 0.12: mean -0.2332 sd 0.0215, 2,604 offsets, 54 dropped. The sentinel still cannot be subtracted exactly; the proper repair is rerunning each book's last chunk with a patched `scan()` after the queue ends.

## Gate (quick: 2-3 plants per cell; Liber AL as the key; Emerson plaintext; per-plant flattening table; skip rule q = 0.81; 60 beam nulls and 4 EM nulls per verification, a real hit uses 200 and 20)
| key | plaintext | runes | verified | plaintext accuracy (median / min) | table agreement (median) | decrypted IoC (median) | wrong-offset nulls verified | uniform-key nulls verified |
|---|---|---|---|---|---|---|---|---|
| digraph | digraph | 1,524 | 2/3 | 0.998 / 0.937 | 1.00 | 1.768 | 0/3 | 0/3 |
| digraph | letters | 1,524 | 3/3 | 0.996 / 0.992 | 0.93 | 2.024 | 0/3 | 0/3 |
| digraph | digraph | 3,316 | 2/2 | 0.992 / 0.991 | 0.97 | 1.814 | 0/2 | 0/2 |
| letters | digraph | 1,524 | 3/3 | 0.999 / 0.998 | 0.95 | 1.800 | 0/3 | 0/3 |
| letters | letters | 1,524 | 1/3 | 0.995 / 0.041 | 0.91 | 1.973 | 0/3 | 0/3 |
| letters | digraph | 3,316 | 2/2 | 0.993 / 0.992 | 1.00 | 1.787 | 0/2 | 0/2 |
Totals: 13 of 16 true plants verified; 0 of 32 matched nulls (16 wrong-offset, 16 uniform-key) verified. The three failed plants were not examined individually; the letters/letters cell has one plant with plaintext accuracy 0.041 (the beam lost the path, as the stage-1 gate's bimodal misses). When the path is found, plaintext accuracy is 0.99-1.00 and the table agrees on 91-100% of the key letters present.

## Limits of this gate
- 2-3 plants per cell: the verification rate (81%) has a wide interval (about 55-95%); the full gate (`python work/book_key_verify.py gate`, 6 and 4 plants per cell, about 4x the time) was not run. The null count (0/32) bounds the false-verification rate at about 10% at 95% confidence; the criteria are far from the null in the plants (beam margin tens of sd), but the criteria were not tuned on a large null sample.
- Plants use Liber AL (22 k runes) as the key; other books are not planted. Plaintext is Emerson only; the model is Walden.
- Hits are verified under the same scope as stage 1 (English-like plaintext, q = 0.81, forward book key, our edition).
- The prime-sum check is supplementary, not a gate (needs >= 6 short clauses).

## How to run it on a hit
1. After booknight reports: `python work/book_key_summary_fixed.py` (writes the `_fixed.txt` summary; each `HIT` line carries its verify command).
2. `python work/book_key_verify.py hit <book> <digraph|letters> <offset> <section, e.g. 0.12>` (use a Python that has numba and scipy; about 1-2 minutes per hit on one core; set NUMBA_NUM_THREADS=1 if the machine is shared).
3. Read the decrypted text; check the recovered table and the end pointer against the next section's hit. A verified hit is a candidate to read, not a solution. Record results in PLAN.md, the phase-23 log, registry row `book-key-decoder`, run `scripts/build_overview.py`, privacy scan.
