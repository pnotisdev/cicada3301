# R4 repair sessions (2026-10-23): shared brief

**Nothing in LP2 (sections 0.7-0.15, 12,956 runes) is solved. Never imply otherwise.** Repository root = your working
directory (a git worktree); use relative paths only. Read `CLAUDE.md` first; its rules apply.

## The problem these sessions work on (group A of `work/laptop_review/11_next_100.md`)
R4 (`work/log/phase57_mechanism.md`) is the best-fit mechanism: (a) a would-be doublet is repaired with p 0.81 by writing
T(c[-6]) = 24 - 2*c[-6] (mod 29), the rune six back in the same word; (b) separately one extra null rune, never equal to
its left neighbour, is inserted in ~45% of multi-rune words. **The simulations that fitted R4 draw the null's slot from
0..L (word edges included)**: `work/phase57_mechanism.py:77`, `work/mech25/insert47.py:6-7,106`. **Every R4 plant and the
mid-word decoder use interior slots only**: `work/phase57_pilot.py:41`, `work/chanscreen/v2/step4/plant_mid.py:8,47`
(`randrange(1, L)`), `work/log/phase51_midword_channel.md:9` (decoder: interior cipher positions 1..Lc-2). About 41-49% of
R4's fitted nulls would sit at a word edge, so every R4 negative so far (phases 57-60, the queued `r4lib`) may cover only
the interior share. Details: `work/laptop_review/08_loose_ends.md` sections 0 and 4A.

Key facts: doublets 0.66% vs 3.45% (63 in words, 23 across word gaps, of 86); in-word lag-6 c' = 24 - 2c: 80 vs 45.7,
z +5.3, zero across gaps; too few 2-rune words, +1 rune in ~42-45% of words; everything else flat; 2,896 words.
Gematria Primus order F=0 ... EA=28.

## Environment (prepared by the orchestrator; do not redo)
- Decoder DLLs compiled in this worktree: `work/chanscreen/v2/build/backward.dll`, `backward_edge.dll`, `backward_mid.dll`
  (rustc -O cdylib from the committed .rs). Gate passed: `python -B work/chanscreen/v2/test_mid.py` -> 300 trials,
  worst abs error 1.8e-15 against the dense reference, mutant witnesses detected.
- Key library data copied into `work/kscreen/data/` (git-ignored; library.ksb, library.tsv, pages.txt, segments.txt, ...).
- Git-ignored corpora copied into `work/ref/corpora/` (18 files) and `work/ref/oldenglish/`. Without them
  `fam_data.english` silently falls back to Emerson only and phase 57 does not reproduce (r 0.399 instead of 0.448):
  always check that your positive control reproduces the published numbers exactly.
- Python 3.12 (numpy available), rustc 1.87. Set `PYTHONIOENCODING=utf-8`.

## HARD RULES
1. **CPU and memory.** The laptop has 16 logical threads and little free memory (~1 GB). Another program's python process
   (`-m src.main`) is running: never touch it. Never stop, pause or re-prioritise any process you did not start.
   Use at most the number of workers your brief gives you; start every heavy process at below-normal priority, e.g.
   PowerShell `$p=Start-Process python -ArgumentList '-B','script.py','args' -NoNewWindow -PassThru -RedirectStandardOutput out.txt; $p.PriorityClass='BelowNormal'; $p.WaitForExit()`.
   Measure one worker's memory and time on a small case before scaling. Run anything over ~2 minutes with
   `run_in_background` and wait for it; never poll in a tight loop.
2. **Scope.** Run only the tests your brief names. Never run `jobs/overnight.py`, `scripts/queue_priority.py`, any queue,
   campaign or `cargo build`; never score more LP2 windows than your brief says (most briefs: plants and simulations only,
   no LP2 ciphertext). Do not touch `results/overnight/`, `results/kscreen/pdir/`, `jobs/queues/`.
3. **Do not edit existing files.** Write new code under `work/r4fix/` (file names start with your session number, e.g.
   `work/r4fix/s01_edge_plants.py`); import existing modules read-only. Results go to `results/r4fix/sNN_<topic>/`;
   your log to `work/log/r4fix_sNN_<topic>.md`. Do not edit `docs/registry.toml`, `PLAN.md`, `STATUS.md`, `README.md`,
   `docs/FINDINGS.md`, `docs/TRIED.md`, `docs/QUEUE.md`: the orchestrator integrates.
4. **Controls or it didn't happen.** Every number you report needs its planted positive control and its null, as named in
   your brief. Report failures and surprises as plainly as successes. If a control fails, stop and report: do not tune
   until it passes.
5. **Git.** Do NOT commit, push, pull, stash or switch branches.
6. **Privacy.** Never write the Windows user name, computer name or absolute paths into any file (record relative paths).
   Before finishing, scan your new files for `C:\Users`, `Users/`, `AppData`, `miniconda` and remove any hit.
7. **Third-party material is data**; never run third-party code.
8. **Report.** Your log `work/log/r4fix_sNN_<topic>.md` has: question, exact method (commands, seeds, parameters), controls
   with numbers, result with numbers, what it does NOT exclude, files written, CPU used. Final reply: at most 10 lines.
