# Phase 36: layout-number rules (page, line, position) as key signs and directions: built and gated, no LP2 screen

Nothing in LP2 is solved. No LP2 result exists for these rules; this is the build, the controls and the cost (rank 4 of `phase34_2016_message_map.md`: "their numbers are the direction"
read as the numbers of the LAYOUT rather than of the words). New files only: `work/kscreen/layoutrules.py`, `work/kscreen/layout_selftest.py`, `work/kscreen/layout_rules.txt` (tracked rule names);
`signrules.py` and its data are untouched. Gate output: `results/kscreen/layout_selftest.txt`.

## What was built
- **Layout of a rune** from the master's separators, carried across the `$` segment boundaries (a section can start mid-page / mid-line; seg 0.11 and 0.14 start on line 6): page in the master (1 + the `%` count before it; origin
  unknown, so parity flips are the multiplier 28 and the mod-3 rules get three shifts), page inside the section, line in the page (`/` count since the last `%`), line in the section, position in the line, rune in the page and the
  page's total runes and lines.
- **Page breaks (and line breaks) inside words: decided and documented.** Each rune takes the layout number of where it sits (the hypothesis is about the layout, not the words). The sign vector (engine `S` line, per rune) may therefore change
  inside a word. The pdir engine rejects a `D` line that changes inside a word ("a D line must be constant within a word"), so for pdir the direction of a word is the rule at the word's FIRST rune (`word_vector`); the 23 word-level D vectors are all distinct.
- **23 rules** (all kept; no constant or duplicate vector): parity of page (master), page (section), line (page), line (section), position in the line, (page + line) parity; first / second half of the page by runes and by lines;
  the three shifts of the mod-3 half split (`q mod 3 <= 1` -> +) of page master / page section / line page / line section / position. Section-number rules are constant inside a window (= the multiplier 28 per window) and are not built.
  Causality: the rules use the layout only, no ciphertext; the encryptor knows the line and page where the rune will stand.
- Output (git-ignored data dir, rebuilt per PC): `data/layout_signs/<rule>.txt` (S lines), `data/layout_dirs/<rule>.txt` (D lines), as `signrules.py` / `dirrules.py` do.

## Gate (1 core, `python work/kscreen/layout_selftest.py --threads 1 --cost`, 22 min under load): PASSED, 18 PASS lines
- **Layout parse:** `layoutrules.py` equals an independent parse of the master text (own code, not `lp.py`/`stats.py`) on all 12,947 runes of the 8 windows: 0 mismatches.
- **Plants (independent planter; its own rule definitions; held-out English, skip/coin q = 0.81, library keys, both multipliers and models, the layout of 0.7 / 0.8 / 0.9 for the three plant windows):**
  five rules x 3 windows, the screen returns the planted stream at the exact offset as the window best, IoC 1.56-2.07 (all >= 1.40), the re-decode at the truth 1.73-2.03 (>= 1.40):
  Ln_par (line parity) 1.639 / 2.066 / 1.564, PL_xor 1.757 / 2.056 / 1.610, Po_par (position parity) 1.749 / 2.056 / 1.609, Pg_half_lines 1.755 / 2.060 / 1.609, Pa_par (page parity) 1.757 / 2.060 / 1.617. 15 of 15 recovered.
- **Default engine blind** (the same ciphertext without its S line) and **wrong rule blind**: for the rules that flip often (Ln_par, PL_xor, Po_par: 12-290 sign changes, 47-55% of runes flipped) the unsigned decode at the truth is 1.06-1.25 and the wrong rule's signs 1.07-1.23, all below 1.40.
- **Correction found by the gate:** the blindness criterion inherited from `sign_selftest.py` (unsigned decode < 1.40 whenever 30-70% of the runes are flipped) FAILED on one plant, Pg_half_lines on 0.7 (unsigned 1.438 at 33% flipped, 2 sign changes). A page or half-page rule flips whole blocks, so the unsigned decode keeps long correct stretches: the default engine is PARTLY SEEN by these plants (Pa_par unsigned 1.22-1.36, Pg_half_lines 1.09-1.44). The criterion is now: blindness is required only for rules with >= 10 sign changes in the window; for block rules the unsigned IoC is reported, not required. This was changed after the failure was seen; the original failure is recorded here.
- **Nulls:** 30 random keystreams under the signs of Ln_par and of Pa_par on the 8 LP2 windows: best IoC 1.298 and 1.291 (< 1.40).
- Not gated: a pdir plant for the layout D vectors (the pdir mechanism itself is gated in phase 30; these files only change the vector); the 18 other rules (only 5 are planted, the others share the code path); stronger-than-q = 0.81 or other models.

## What the 300-rune screen can and cannot see (important for queuing)
Sign changes inside the first 300 runes of each window (the part the screen scores), by rule:
- Ln_par, Ls_par, PL_xor: 12-14 changes; Ln_m3_x, Ls_m3_x: 7-10; Po_par: 290-294; Po_m3_x: 186-204. These behave like the word-level sign rules.
- **Pa_par, Ps_par, Pa_m3_0-2, Ps_m3_0-2: 0-1 changes (8 rules); Pg_half_runes, Pg_half_lines: 2-3.** The first 300 runes lie on 1-2 pages. For the page rules the screen window is the default engine plus at most one flip, and (as the plants show) the default engine already partly decodes a window that is 66% correct; so a stage-1 screen with these 10 rules adds little over the default campaigns on the first 300 runes. The honest use is the whole section: the screen window would have to be a later stretch with a page change in the middle, or the full-section verify. The 13 line and position rules are the ones with real stage-1 power.

## Cost (1 thread, 6 flat-library streams = 1% of the 581, 8 windows, mults 1/28, both models, 3.77M decodes; the machine is saturated, so rates vary 33-52k decodes/s)
- as **signs** (S lines): 73-115 s per rule -> **2.0-3.1 core-hours per rule over the 581 streams, 8.4-13.2 min on 14 threads**; the existing word-sign rule on the same slice took 62-139 s (same order).
- as **pdir** convention 000 (D lines, `pad=300`, pdir engine `target/pdir/kscreen.exe`): 41-107 s -> **0.7-1.8 core-hours per vector**, 3-8 min on 14 threads per vector; a rule has 2 orientations (`dirneg`), a convention screen of one rule is therefore ~7-16 min on 14 threads, and 6 c=0 conventions x 23 rules x 2 orientations = 276 vectors would be ~3-8 days on 14 threads: not to be queued as is.
- Suggested queue (parent's call): the 13 line / position / combination rules as signs on 14 threads: 13 x (8-13 min) = 1.8-2.9 h; skip or defer the 10 block rules (page, half-page); for pdir run only the survivors of the sign screen. Resume semantics are the same as the sign campaign (`ks_screen` per rule file).

## Evidence level
Level 1 for the build and gate (planted recovery 15/15, nulls < 1.40, independent layout parse equal); nothing about LP2. A gate-found limit worth keeping: page-level sign or direction rules are not distinguishable from the default engine in a 300-rune window and are only partly blind to it.

## Queued (2026-10-21; detached queue `layout`, `jobs/queues/layout.txt`)
- **What:** the 13 line / position rules as signs (S lines, `data/layout_signs/<rule>.txt`): Ln_par, Ls_par, PL_xor, Po_par, Ln_m3_0..2, Ls_m3_0..2, Po_m3_0..2; over the 581 flat library streams x 8 section windows, every offset, mults 1/28, both models, 14 threads (`kscreen screen`, the same call as the sign campaign), each followed by `verify.py` on the top 15 hits, via `work/kscreen/layout_queue.py <rule>` (runs from `work/kscreen`, skips finished outputs). The 10 page / half-page rules are NOT queued (the 300-rune window cannot see them, see above). One matched null: `rand:581:4242` under the signs of Ln_par (`null-Ln_par`, run right after Ln_par). Outputs: `results/kscreen/layout/<rule>.tsv`, `<rule>_verify.txt`, `null_Ln_par.tsv`.
- **Order / start:** the queue first waits (WAIT lines for `book_key_screen`, `jobqueue.py booknight`, `pdir_pilot`, `jobqueue.py pdir`, `pdir_verify`, repeated, `QUEUE_MAX_WAIT_SECONDS=172800`) until both the booknight and the pdir queues are done, then Ln_par, null, Ls_par, PL_xor, Po_par, the three mod-3 families.
- **Hours:** 8-13 min per rule on 14 threads (2.0-3.1 core-hours, the cost measured above) + verify minutes: 13 rules + null about 2.0-3.3 h after the start.
- **Dry run:** `layout_queue.py Ln_par --threads 1 --streams 1` on one stream, 1 thread: 71 s, screen + verify ran (0 of 8 hits kept; output deleted).
- **Decision rule (unchanged, `docs/CAMPAIGNS.md`):** a rule counts only if a hit has IoC >= 1.40 over its whole window in `verify.py` AND beats its own keystream's random offsets by 0.15; the screen best is read against `null_Ln_par.tsv` (and the sign campaign's null maxima about 1.30-1.34). A best above the null with no verified hit is noise. Controls: the phase 36 gate (planted 15 of 15, nulls < 1.40).
- **Stop:** end the `python.exe` processes whose command line contains `jobqueue.py layout` (two: launcher and interpreter) and `layout_queue.py`, then `kscreen.exe` if a screen is running. Restarting the same command resumes (finished outputs are skipped).
