# Phase 30: pointer-direction mechanism (pdir) built and gated; no LP2 campaign, pilot not run

Nothing in LP2 is solved. Status: engine option, reference, planter, gates built; usage limit reached before the pilot and the cost write-up were finished.

## Built (work/kscreen)
- `src/main.rs`: `pdir=<h><m><c> [pad=300] [dirneg=1]`, window `D` line (+1/-1 per rune). Separate beam `ioc_beam_dir` / `full_decode_dir`; default path untouched. Reads key values before the start offset (buffer starts `pad` earlier, pointers < 0 are dead). Modes screen, trace, verify. 18 conventions: h first read of a backward word (0 read then step, 1 step then read), m movement between words (0 none, 1 old direction, 2 new direction), c comparator (0 previous emitted, 1 previous in word, 2 previous backward rune).
- `dirrules.py` (66 rules = 61 sign rules + 5 GP-prime rules G4_prev, GP_prev, G2_cur, G4_cur, GP_cur (the *_cur ones are acausal), 132 vectors with dirneg), `pdir_ref.py` (plan, exact beam emulation, exhaustive search, independent planter), `pdir_selftest.py`, `pdir_identity.py`, `pdir_pilot.py` (pilot/campaign driver, untested). `signrules.section_tables` now tolerates B lines; `verify.py` passes pdir options and honours KSCREEN_BIN.
- Binary built outside the repo (the repo exe was in use).

## Results
- Bit identity (`pdir_identity.py`, orig = HEAD build): 12 option sets (default, S, G, nulledge 1/2, advsep 1/2, dir=back, clock, abort) IDENTICAL, trace and screen files.
- Existing selftest.py and sign_selftest.py PASSED with the new engine (null 1.306 / 1.286).
- Reference: 8,640 engine decodes = exact emulation, all 18 conventions x 2 orientations x 2 models, incl. dead pointers; each convention distinguished from its neighbour.
- Exhaustive: 299/300 tiny cases equal the best over all paths (merge loses at most 2).
- Equivalence: all-forward D equals default (000) and advsep=1 (010), 800 decodes each (needed forward-movement key slack in `dir_need`).
- Plants (4 rule/convention/orientation cases x 3 windows, q=0.81): 11/12 recovered at exact offset with screen IoC >= 1.6; one 1.594 (B5_prev_R, 021, window 2; whole-window re-decode 1.746). Default engine best 1.22-1.27; wrong rule 1.03-1.10 at truth; wrong convention 1.03-1.10. Gate now: exact offset and >= 1.40, re-decode >= 1.6.
- Final full run (incl. null) of pdir_selftest was still running; read work/tmp/kscreen/pdir_full_stdout.txt.

## Cost (measured under load, 2 threads ~93k decodes/s; pdir not slower than default)
Per vector (8 windows, 581 flat streams) ~347M decodes; per convention 132 vectors ~45.8G = ~13.7 h at 14 threads (66k/s/thread); 18 conventions ~247 h. Plan: stage 1 on windows seg0.7+seg0.8 only (a true key shows in both) = 3.4 h per convention, c=0 conventions first (000,100,020,120,010,110); matched null of equal size for the first convention (random max at ~1e11 decodes is near 1.40); hits >= 1.40 -> verify.py (20 offsets) -> full window. Queue file not written.

## Left
Pilot (`python work/kscreen/pdir_pilot.py --conv 000 --streams 6 --null 6 --threads 2`, ~25 min), queue file, registry/PLAN rows (not mine to edit), commit (nothing committed).

## Pilot (done after the limit reset)
Convention 000, window seg0.7 only, 6 of the 581 flat streams (every 96th), all 132 vectors (66 rules x both orientations), both mults and models, about 61M decodes real and the same for the null (6 random keystreams, same vectors); 2 threads, a few minutes each part (far under 30 min).
- Real: best IoC 1.2951 (B7_prev_R forward); vectors >= 1.30: 0, >= 1.35: 0, >= 1.40: 0; median per-vector best 1.2486.
- Matched null: best 1.3055 (A_prev_l reversed); >= 1.30: 2; none >= 1.35; median 1.2518.
- Negative on this slice and no better than the null. The 6-stream slice is 1% of the library on one window: a pipeline and cost check, not a test of the mechanism.
Outputs: results/kscreen/pdir/pilot/000/{real,null}/*.tsv, summary.txt. Draft queue (not started): jobs/queues/pdir.txt.
Pilot-slice rate: about 61M decodes in a few minutes on 2 loaded threads, consistent with the cost section above.

## Queued (2026-10-20 night): stage 1, running detached, waiting for booknight
`jobs/queues/pdir.txt`, launched with `.venv\Scripts\python.exe jobs\jobqueue.py pdir jobs\queues\pdir.txt` (hidden) and KSCREEN_BIN = `work/kscreen/target/pdir/kscreen.exe` (the pdir engine, a copy of the build; the repo's own release exe is older and was in use). It holds on `WAIT | book_key_screen` (five times, 8 h each at most) until booknight's python processes are gone.
Order: `gates` (pdir_selftest --quick), then per convention 000, 100, 020, 120, 010, 110: `pdir-<c>` (windows seg0.7 + seg0.8, 581 flat streams, 132 vectors, mults 1/28, both models, 14 threads, about 3.4 h) and `verify-<c>` (pdir_verify.py: verify.py top 5 hits of every vector, 20 random-offset controls, minutes); after verify-000, `null-000` (rand:581, same windows and vectors: equal size, about 3.4 h). Total about 24 h of 14 threads. Dry run done (queue parse 19 jobs; a 2-stream pilot step and the verify step ran with the .venv interpreter).
Decision rule: a vector's best IoC >= 1.40 on the first 300 runes is a hit; `verify_summary.txt` per convention must show candidates 0 or the hit is read by eye and given the whole-section verification of docs/CAMPAIGNS.md. At about 10^11 decodes the random maximum sits near 1.40, so compare with null-000's best (results/kscreen/pdir/stage1/000/summary_null.txt). Nothing here is recorded: read results/kscreen/pdir/stage1/<conv>/{summary_real.txt,verify_summary.txt}.
Status: `type results\overnight\desktop\queue\pdir.tsv`. Stop: end the python.exe processes whose command line contains `jobqueue.py` + `pdir` or `pdir_pilot.py`; a finished vector file is skipped on restart (restart with the same launch command and KSCREEN_BIN).

## Relaunch after the review (parent session, 2026-10-20 about 23:10)
`work/log/phase30_review.md` found that five 8-hour WAITs (40 h) end before the booknight queue (expected to finish about 2026-10-22 15:30), and that an engine without the pdir option silently ignores `pdir=`. No pdir job had started (no `pdir.tsv`). Fixes: `pdir_pilot.py` now refuses a tsv whose header lacks `pdir=<conv>` (deletes it and exits non-zero); the driver was stopped and relaunched detached with `QUEUE_MAX_WAIT_SECONDS=172800` (48 h per WAIT, up to 240 h) and `KSCREEN_BIN` pointing at `work/kscreen/target/pdir/kscreen.exe`. Before recording any stage-1 result: `pdir.tsv` must show `gates ... ok`, 132 tsv files per convention, and `pdir=` in every header. Planted recovery exists for conventions 000 and 110 only (100, 020, 120, 010 rest on the exact-emulation gate).
