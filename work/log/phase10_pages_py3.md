# Per-page seeds, first generator: py3 over the epoch-second range (2026-10-18 00:18)

Scope: LP2 pages that start inside an unsolved section. **Nothing in LP2 is solved.** Hypothesis H11 (`docs/HYPOTHESES.md`): a fresh seed per PAGE instead of per section. `prng-all` and the time-seed sweeps used the 8 section windows; the page starts were never swept.

**Windows** (`bg.make_windows("pages")`, new): the first 120 runes of every page that starts inside an unsolved section (not at its first rune) and has at least 120 runes of its own: **44 windows** (of 55 unsolved pages; 7 start at a section start and are in the section windows, the rest are shorter than 120 runes); the previous rune is the last rune of the page before.
**Gate** (`work/tests/test_bgmt_pages.py`, new, passes with 0 skips): the window set is what it claims; a planted seed (php 777777, py3 123456, java 42424, glibc 424242) is recovered among the 44 page windows with every other window silent below 150; random ciphertext gives no candidate for py3, java and php (300,000 seeds x 44 windows).
**Sweep:** `bg.py sweep py3 pages 1293840000 1420070400` (epoch seconds 2011-01-01 to 2015-01-01 UTC, 126,230,400 seeds, a fresh seed per window, 16 variants): **640 s on the GPU, 0 candidates at or above +300** (`results/prng/bgtime_py3_pages.*`, `_verify.txt`: no candidate reached the floor).
A true key passes the +300 gate in every 120-rune window of Cicada's text (`results/analysis/true_key_score.txt`).

**Not done:** the other seven time-seed generators (php, glibc, mt32, mt31, msvc, drand48, ruby; about 11 min each), small-integer seeds < 2^27 for the three generators that were swept on sections, and java / .NET (64-bit and tick seeds).
