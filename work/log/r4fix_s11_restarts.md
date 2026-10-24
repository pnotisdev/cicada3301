# s11: R4 x key restarts at page and clause starts, 61 Cicada-named streams (laptop, 2026-10-24)

**Nothing in LP2 is solved.** Idea 13 of `work/laptop_review/11_next_100.md`, spec `work/log/r4fix_s09_scope.md`. Every
earlier restart test (page, paragraph, line, sentence, clause starts: `restart-units`, `restart-library`,
`open-clause-windows`) was R4-free. Here a named key stream restarts (key index 0) at a page start or a clause start, and LP2
is decoded under R4 with the gated union arc. Script `work/r4fix/s11_restarts.py`; results `results/r4fix/s11_restarts/`.
The session was written by a sub-session; after the owner's pause and two forced hand-backs the orchestrator ran its last
two steps (`run`, `summary`) and wrote this log.

## Method
- **Decoder**: union arc (`work/r4fix/s08_engine_union.py`; one null at any cipher position of a word, nu 0.42), q 0.81,
  hold and spend, both signs, key offsets 0-28 (0 = the restart; 1-28 a shifted start), T300 = 29.80 (`hit_rule.py`).
  Word-start flags from the transcription's real word boundaries (`lp_mask.section_edges`), so a window that starts
  mid-word is flagged correctly; the selftest showed that flag 0 has no numeric effect in this engine (s09's bug is harmless here).
- **Streams**: 61 named library streams (list with library indices in `results/r4fix/s11_restarts/streams_and_windows.txt`):
  the 20 `layer2 periodic_core20` streams, pi(n), n^3, Pell, sqrt3 and ln2 in base 29, the 1033 / 3301 families (1033*n, 3301^n,
  digits, 1/3301, sqrt3301, ln3301, 3301*p_n, p_n mod 3301, 1033 square rows, page-30 grid primes), An End's hash as bytes and
  nibbles, SHA-256 counter / chain streams (mod and reject) of "an end", "welcome", "instar", "3301", "Cicada 3301", and the
  corrected 256-byte payload. The PGP key id is not in the library and was not added.
- **Windows**: 46 page starts and 82 clause starts (>= 60 runes, `open-clause-windows`), each in two variants: A
  n = min(300, runes to the section end), B n = min(300, runes to the next restart of the same kind). Windows under 150 runes
  skipped (77 of 256 window-variants, listed in `streams_and_windows.txt`; s05: recall at n 100 is only 67%). 179 windows,
  167 unique (section, start, n) tasks. 30 of 44 page windows start mid-word.
- **Null of the maximum**: 100 random streams of the same length on every LP2 window.

## Controls
- **Positive**: 28 R4 plants (`work/r4fix/r4sim.py`, slots `any`, q 0.81, nu 0.45, T repair, checked visible nulls), each a
  random named stream restarted at an LP2 page start of solved-text or English plaintext, 7 per channel x source cell, signs
  alternating; 21 start mid-word. Detected (S_guard of the true cell at offset 0 >= 29.8): **28/28 at n 150** (true-cell
  score 45.2 / 64.0 / 78.1 min / median / max) and **28/28 at n 300** (104.5 / 134.6 / 163.9); true cell within 3 nats of the
  best cell 28/28 at both n. Gate (>= 11/12 at n 300 among the first 12): passed, 12/12.
- **Null**: matched iid-key plants searched with the same 61 streams: max -9.9 (n 150), -43.6 (n 300), 0/28 at or above T300.
- **Other-stream maximum on the plants** (`plants/w_*.json`, n 300): every non-alias other stream stays at or below -15.7.
  The six plants keyed by a SHA-256 "mod" stream show an other-stream score of 40-118: that is the same hash's "reject" twin,
  which equals the "mod" stream wherever the byte is below 232, i.e. an alias of the true key, not a failure of the null.
  `plants_summary.txt`'s "best wrong" column also contains the true stream's other channel (an alias) and is not a null.

## Result: negative
1,181,692 named cells (40,748 at offset 0) plus 1,937,200 random-stream cells, 2.88 CPU-hours.
**No LP2 cell reaches T300 = 29.80** (0 cells; none even reaches 0). Best named cell -26.84 (clause B, 0.12 clause at 677+156,
n 156, sha256-ctr mod :3301, offset 15) against a random-stream null maximum of -24.93 over the same windows; at offset 0 the
named best is -28.13 against -27.15. Per window type (named best at offset 0 / random max): clause A -28.13 / -38.35, clause B
-34.13 / -32.97, page A -44.70 / -47.38, page B -42.27 / -27.15. No whole-section verification was needed.

## What it does NOT exclude
Streams outside these 61 (the rest of the library under restarts is a 1,439-stream job); windows under 150 runes (77 skipped)
and restart points other than page and clause starts; skip5 / coin channels; more than one null per word; a restart at a
key offset beyond 28; non-additive key use. The plant set is 28 plants; recall at these n is high (s05), not measured on
clause-sized windows with variant B's short lengths specifically.

## Process notes
- Paused by the owner mid-run; plant records are written atomically and all 28 were valid on resume (nothing discarded).
- The first 4 plant workers ran at Normal priority for about 15 minutes before being set to below-normal (`LPM.lower()` did not
  reach the pool workers); a duplicate `pwrong` tree briefly ran 8 workers before the sub-session killed the newer one.
- Fix made by the orchestrator: `cmd_run` and `cmd_summary` built the window list before loading the library (the pool
  initializer only runs in the workers): both now call `P._init()` and `_setup()` first.
- CPU: plants 0.70 h, other-stream pass about 0.25 h, LP2 scan 2.88 h; about 3.9 CPU-hours in total, under the 12-hour budget.
