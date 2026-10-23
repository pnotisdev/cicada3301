# The detached job queues (2026-10-18)

**Status (2026-10-18 10:35): stopped, nothing is running.** The first run (01:25 - 08:37) did its direct jobs (the sign campaign, 16 page sweeps, the ms months; `work/log/phase10_overnight_queue.md`) but every runner-based job (periodic templates, layer2, prng-bg) crashed because the driver was first called `jobs/queue.py` and shadowed Python's `queue` module (renamed
`jobs/jobqueue.py`). The user then asked for no more long runs: both tasks were ended and deleted. To use the queues again, recreate the tasks as below or run `python jobs/jobqueue.py <lane> jobs/queues/<lane>.txt` by hand.

Two queues keep the desktop busy for about 12 hours and **keep running when the interactive session that started them ends** (a usage limit, a closed window). They are ordinary Windows scheduled tasks (`LP_queue_cpu`, `LP_queue_gpu`, run once, started immediately,
parent `svchost.exe`), each running `jobs/jobqueue.py` on a queue file in `jobs/queues/`. Nothing in LP2 is solved; every job is a test with a planted control and a null (see the campaign descriptions in `docs/CAMPAIGNS.md` and `docs/NEGATIVE_SPACE.md`).

## What the drivers do

- run the jobs of the queue file in order, one at a time; a job that exits non-zero is recorded as failed and the queue goes on; a job already `ok` in the state file is skipped, so a restart resumes;
- `WAIT | <text>` first lets a job that was started by hand finish (any `python.exe` whose command line contains the text; two minutes without it, at most 8 hours), because those hand-started jobs die with their session and the queue then takes over their remaining work (all jobs are resumable);
- keep Windows awake while they run (`SetThreadExecutionState`; no setting is changed). They do **not** survive a log-off, a shutdown or a sleep that the machine takes anyway (battery, lid); after a reboot, start them again with the commands below (finished jobs are skipped);
- write `results/overnight/desktop/queue/<queue>.tsv` (job, start, status, end, exit code) and one log per job, `<queue>__<job>.log`; delete their own scheduled task when the queue is done (`QUEUE_DONE` in the state file).

## The CPU lane (`jobs/queues/cpu.txt`, 14 threads, about 12 h)

| job | what | about |
|---|---|---|
| `signs` | `kscreen-signs`: 61 word-level key-sign rules over the 581 flat-IoC library streams (`work/log/phase10_signrules.md`); the campaign started by hand is on rule 9 of 61 | 6 h left |
| `signs-periodic` | `kscreen-signs-periodic`: 25 per-rune periodic sign templates (period 2-5), control `results/kscreen/sign_periodic_selftest.txt` (9/9 windows) | 2.7 h |
| `layer2` | the remaining `layer2` slices: H1 with known keywords (null, bigram-solved, bigram-words, periodic) | 3 h |

## The GPU lane (`jobs/queues/gpu.txt`, about 13 h)

| job | what | about |
|---|---|---|
| `months-java`, `months-py3` | the remaining millisecond-timestamp months 2012-01 .. 2013-02 (resumable) | 2.5 h |
| `pages-epoch-<gen>`, `-verify` | per-page seeds (44 page windows, `bg.make_windows("pages")`, gate `test_bgmt_pages.py`) over the epoch seconds 2011-2015 for php, glibc, mt32, mt31, msvc, drand48, ruby (py3 is done) | 1.3 h |
| `pages-small-<gen>`, `-verify` | the same over the seeds 0 .. 2^27 for py3 and those seven | 1.5 h |
| `months-java-abs`, `months-ruby` | the abs() key map of java, and Ruby, millisecond timestamps, newest months first | 3 h |
| `prng-bg` | the runner campaign `prng-bg` on the GPU lane, `--hours 4.5`: boundary-free full-seed sweeps of the sections | 4.5 h |

## Looking at it, stopping it, restarting it

```
type results\overnight\desktop\queue\cpu.tsv        # status of each job
type results\overnight\desktop\queue\gpu.tsv
schtasks /query /tn LP_queue_cpu                    # is the task there / running
schtasks /end /tn LP_queue_cpu                      # stop a lane (the job in progress is killed; its work is resumable)
schtasks /delete /tn LP_queue_cpu /f                # remove the task
.venv\Scripts\python.exe jobs\queue.py cpu jobs\queues\cpu.txt    # run a lane by hand (after a reboot)
```

## Recording the results (nothing records itself)

The queues only produce files: `results/kscreen/signs/`, `results/kscreen/signs_periodic/`, `results/layer2/`, `results/prng/` (`time_gpu/`, `bgtime_<gen>_pages.*`, `bgsmall_<gen>_pages.*`), `results/overnight/desktop/` (reports, logs, the queue state). Read them as the earlier logs did
(`work/log/phase10_signrules.md`, `phase10_pages_py3.md`, `phase10_prng_time_gpu.md`): best score against the rule (IoC 1.40 for kscreen, +300 for the seed sweeps), the verification files, a privacy scan of the added lines (no computer or user names, no absolute paths), then PLAN.md, the ledger and a commit.
A line `0 of N` in a `_verify.txt` is a negative; anything at or above the rule is a candidate and needs the whole-section verification of `docs/CAMPAIGNS.md` before anyone says more.

## night2 (2026-10-19, started by hand, not a scheduled task)

`jobs/queues/night2.txt`, about 10-12 h on the desktop CPU (my estimate from 18-19k decodes/s): the H5 sweep (`work/h5rs`) over the flat library at L = 2..13 in 5 offset blocks of 400, the campaign-size null (`null581.ksb`, the real 581-stream size: the
8-stream null undershoots the maximum by 0.26-0.34) at the same L range, `jobs/night2_summary.py` (candidate rule with that null -> `results/h5rs_flat_summary.txt`), the 858 streams the standalone flat-IoC filter excluded (built by
`jobs/night2_prepare.py`) at L = 2..8 in two offset blocks (-> `results/h5rs_nonflat_summary.txt`), then the remaining `layer2` slices. The L range follows the power map (`work/log/phase16_h5_power_map.md`): recall falls from 84% at L = 2 to 7% at L = 20.
Start from the repository root: `Start-Process .venv\Scripts\python.exe -ArgumentList 'jobs\jobqueue.py','night2','jobs\queues\night2.txt' -WindowStyle Hidden`. Status: `results\overnight\desktop\queue\night2.tsv` and the
per-job logs next to it. A finished job is skipped on a restart (an interrupted H5 block restarts from zero). A candidate is UNVERIFIED until the whole-window re-decode (`work/h5slice`) and the whole-section verification
of `docs/CAMPAIGNS.md`. **A negative result excludes little** (recall at the campaign floor averages 28%); the grid can also miss a true cell at the init abort.

**night2 finished at 09:11 on 2026-10-19** (H5 sweeps: 0 candidates, best real IoC 1.517 flat / 1.32 non-flat; layer2: 0 of 15 / 15 / 100 re-decoded hits pass).

## 2026-10-19 (day): gpu4h, gpu_rest, chanscreen (started by hand, not scheduled tasks)

* `jobs/queues/gpu4h.txt`: `prng-bg` over sections 0.8-0.15 for py3 and java (time-boxed to 4 h). `jobs/queues/gpu_rest.txt` waits for it and runs the other eight generators (php, glibc, mt32, msvc, drand48, ruby, mt31, net), about 1.1-1.7 h each, 2 CPU threads each.
  Results in `results/prng/bg_<gen>_all.*`; `0 candidates` is a negative; a candidate needs the verification of `docs/CAMPAIGNS.md`.
* `jobs/queues/chanscreen.txt`: the chanscreen v2 campaign (`work/chanscreen/v2/step3/PROTOCOL.md`). It waits for the E3b null scan, checks its gate, then runs the 82 LP2 windows of 300 runes (about 49 CPU-hours, 12 workers) and the clause-aligned scan
  (82 clauses of at least 60 runes, about 21 CPU-hours); `summary_n300.txt` and `summary_clause.txt` appear in `results/chanscreen/`. Tier-1 cells are candidates, not leads. Stop: end the python.exe processes whose command line contains `campaign.py` or `jobqueue.py chanscreen`;
  a restart skips finished tasks (one npz per window and stream chunk).

## When the 2026-10-19 queues finish (written for the days without a Claude allowance)

Expected (2026-10-19): the n300 campaign about 20:30, the clause scan about 23:40, `gpu_rest` (the other eight generators, `--hours 14` from 13:10) between 23:30 and 03:10. Nothing else has to be started: the queues run their own summaries. Every runner campaign in `python jobs/overnight.py list` is already done.

1. **Finished?** `type results\overnight\desktop\queue\chanscreen.tsv` and `type results\overnight\desktop\queue\gpu_rest.tsv`: every job `ok`, the last row `QUEUE_DONE`. If a step says `failed` (n300-a did at 15:07), run its campaign command again: it computes only the missing tasks (`.venv\Scripts\python.exe work\chanscreen\v2\step3\campaign.py run n300 --workers 12 --windows 0:21` for that step). If a lane stopped early (reboot, sleep, the 14 h budget), run the same command again; finished steps are skipped:
   `.venv\Scripts\python.exe jobs\jobqueue.py chanscreen jobs\queues\chanscreen.txt` and `.venv\Scripts\python.exe jobs\jobqueue.py gpu_rest jobs\queues\gpu_rest.txt`.
2. **Verdict**, two commands: `findstr /C:"TIER 1" results\chanscreen\summary_n300.txt results\chanscreen\summary_clause.txt` and `findstr /C:"candidates >=" results\prng\bg_*_all.log`.
   `TIER 1 (S_guard >= T): 0 cells` and `candidates >= 300: 0` are negatives. With cells the header reads `N cells, M of them reproduced by an independent recomputation`: only reproduced cells are candidates, and a `NOT REPRODUCED` line is a computation fault (three isolated faults so far, `work/chanscreen/v2/step3/PROTOCOL.md` amendment 3), not a result. The `null` summary lists 137 reproduced cells because its records were planted with library keys; that is expected there.
3. **A tier-1 cell or a candidate:** start nothing new. Copy the lines. `python work\chanscreen\v2\step3\verify_cell.py <set> <window> "<stream>" <sign> <channel> <offset>` (the values are in the tier-1 tuple, in that order after the window name) prints a dense re-score and the most likely plaintext:
   readable English is the signal to bring it to Claude at once; letter soup is an alias. The whole-section verification of `docs/CAMPAIGNS.md` is not something to do by hand.
4. **Before committing in GitHub Desktop:** `python scripts\privacy_scan.py` must print `no hits` (computer name, Windows user name, home folder, repository path, conda and app-data folders in any modified or new file). Fix or ask before pushing.
5. **Commit and push everything** (the result files are the record). The registry, PLAN.md and STATUS.md do not mention the outcomes until a Claude session records them; in that session say "read the finished queues and record them" (the memory note `chanscreen-takeover-2026-10-19` and `work/log/phase20_segmentation_plan.md` section 5 have the steps).

## Using the PC while the queues run (2026-10-19)

`python scripts/queue_priority.py` (the system Python, which has psutil; the `.venv` one does not) acts on every running `jobs/jobqueue.py` and everything it started. Applied on 2026-10-19 at about 15:00 to `chanscreen` and `gpu_rest`: 22 python processes now run at below-normal priority.

* **Priority (done, free).** Your own programs win every contest for a core; while the PC is otherwise idle the runs go at full speed, so the finish times do not move, and Task Manager still shows the CPU busy. Steps a queue starts later inherit the level; a queue you restart begins at normal priority, so run the command again. Undo: `python scripts/queue_priority.py normal`.
* **Fewer cores (slower in proportion).** `python scripts/queue_priority.py --cores 8` pins every queue process to logical processors 0-7 of the 16; the n300 campaign has 12 workers, so 8 cores make it about 1.5 times slower (about 885 of 1,148 tasks were left at 15:00, 2.6 tasks per minute). Undo: `--cores 0`. The CPU lane keeps about 14 of the 16 threads busy, so about 2 are free even without this.
* **GPU (needs an administrator PowerShell).** Process priority does not touch the GPU. The lever is the power cap: the 2080 Ti has a range of 100-280 W, default 250 W, and draws about 183 W at 100% load and 84 C on these sweeps. `nvidia-smi -pl 150` caps it; `nvidia-smi -pl 250` restores it (also undone by a reboot). I did not measure the slowdown (about 930k seeds/s before; read the seeds/s in
  `results/overnight/desktop/queue/gpu_rest__prng-bg-rest.log` after the change); a lower cap means longer sweeps and a cooler, quieter card.
* **Pause (when you need everything).** `python scripts/queue_priority.py pause --queue gpu_rest` and `resume --queue gpu_rest` (the same with `chanscreen`). Nothing is lost; a paused GPU queue keeps its GPU memory and the card idles once the running kernel ends. Wall-clock time keeps counting against the `--hours 14` budget of `gpu_rest`, so after a long pause the last generator may be left
  unrun: start the queue again with its usual command.

## Outcome of the 2026-10-19 queues (2026-10-20 04:20)

All three queues ended (`chanscreen` at 02:15, `gpu_rest` at 23:55). n300: 0 tier-1 cells. Clause scan: its step failed on five tasks and stored one false cell; repaired at 04:17 (1,148 of 1,148 tasks, 0 tier-1 cells). Seed sweeps: 0 candidates in all ten generators. Details: `work/log/phase19_try_all_four.md` section 5 and `PROTOCOL.md` amendment 3.
The queue runner process keeps the scrubber it started with, so a log written after the 2026-10-19 fix can still hold an interpreter folder path: `python scripts/privacy_scan.py --fix` scrubs it before a commit.

## 2026-10-20 / 21: booknight, gpunight, pdir, layout, wordjump (and edge, not launched)

Running detached on the desktop, in this dependency order (each later queue holds on `WAIT` lines until the earlier ones have no python.exe):

| queue | what | interpreter / environment | about |
|---|---|---|---|
| `booknight` | phase 23 table-free book-key screen, stage 1 (Liber AL, Blake x2, Emerson, the Mabinogion done; Agrippa, the KJV) | the conda Python with numba + scipy (not `.venv`) | KJV about 40 h at 10 cores |
| `gpunight` | GPU: millisecond months (done), `prng-step` (ten generators, two left) | `.venv` | about 1.2 h per generator |
| `pdir` | phase 30 pointer direction, stage 1 (windows 0.7 + 0.8, six conventions, matched null for 000) | `.venv`, `QUEUE_MAX_WAIT_SECONDS=172800`, `KSCREEN_BIN` = `work\kscreen\target\pdir\kscreen.exe` (the guard in `pdir_pilot.py` refuses an engine without `pdir=`) | about 24 h at 14 threads |
| `layout` | phase 36: 13 line / position sign rules + matched null | `.venv`, `QUEUE_MAX_WAIT_SECONDS=172800` | about 3 h |
| `wordjump` | phase 37: advsep=3/4/5, each with a matched null | `.venv`, `QUEUE_MAX_WAIT_SECONDS=172800` (engine `target/advlen`) | about 1 h at 14 threads |
| `edge` | phase 24 word-edge campaign, 82 n300 windows x 3 kinds | **written, NOT launched** (owner's decision, about 300 CPU-hours) | 20-29 h at 14 workers |

**After a reboot** (from the repository root, PowerShell): start `booknight` FIRST (otherwise the waiting queues find no book screen and start at once), then the others with their environment:
```
Start-Process <conda python> -ArgumentList 'jobs\jobqueue.py','booknight','jobs\queues\booknight.txt' -WindowStyle Hidden
Start-Process .venv\Scripts\python.exe -ArgumentList 'jobs\jobqueue.py','gpunight','jobs\queues\gpunight.txt' -WindowStyle Hidden
$env:QUEUE_MAX_WAIT_SECONDS='172800'; $env:KSCREEN_BIN=(Resolve-Path work\kscreen\target\pdir\kscreen.exe).Path
Start-Process .venv\Scripts\python.exe -ArgumentList 'jobs\jobqueue.py','pdir','jobs\queues\pdir.txt' -WindowStyle Hidden
Remove-Item Env:KSCREEN_BIN
Start-Process .venv\Scripts\python.exe -ArgumentList 'jobs\jobqueue.py','layout','jobs\queues\layout.txt' -WindowStyle Hidden
Start-Process .venv\Scripts\python.exe -ArgumentList 'jobs\jobqueue.py','wordjump','jobs\queues\wordjump.txt' -WindowStyle Hidden
python scripts\queue_priority.py --cores 10      # cooler CPU; reapply after a queue starts a new step
```
Finished jobs are skipped on a restart (every step is resumable). If the GPU validation fails with "kscreen port, decode by decode", check that `work\kscreen\data\pages.txt` is not empty: `export.py` needs OpenCV (`.venv`) for the page windows (2026-10-21 incident). Before recording a pdir result: `pdir.tsv` shows `gates ... ok`, 132 tsv files per convention, `pdir=` in every header.

## 2026-10-22: r4lib (R4 library campaign at the section starts)

`jobs/queues/r4lib.txt`: the phase 51 mid-word engine (`lp_pilot_mid.py`, now with `--sec/--start/--n/--channels`) on the n300 windows at the start of sections 0.8, 0.9, 0.11-0.15, channels hold and spend, the full 1,439-stream library, both signs, every offset; about 2.8 CPU-h per window (about 20 CPU-h). Justified by phase 57 (R4 is the best description of LP2; the library had been searched under it on two windows only). Waits for booknight, pdir, layout and wordjump. Launch (repository root, `QUEUE_MAX_WAIT_SECONDS=172800`): `Start-Process .venv\Scripts\python.exe -ArgumentList 'jobs\jobqueue.py','r4lib','jobs\queues\r4lib.txt' -WindowStyle Hidden`. Hit rule: S_guard >= T300 = 29.80, then `work/kscreen/verify.py`.

## 2026-10-22: launch queues outside the Claude app

Queues started with `Start-Process` from a Claude Code shell die when the Claude desktop app restarts (they stay in its process tree; this happened at an app update on 2026-10-22, KJV at 495/761, nothing finished was lost). Launch them through WMI instead, so their parent is the WMI service and they survive app restarts (PowerShell, repository root; environment variables go inside a `cmd /c`):

```
$root=(Get-Location).Path; $venv="$root\.venv\Scripts\python.exe"; $kb="$root\work\kscreen\target\pdir\kscreen.exe"
Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine="`"$((Get-Command python).Source)`" jobs\jobqueue.py booknight jobs\queues\booknight.txt"; CurrentDirectory=$root}
Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine="cmd /c set QUEUE_MAX_WAIT_SECONDS=172800&& set `"KSCREEN_BIN=$kb`"&& `"$venv`" jobs\jobqueue.py pdir jobs\queues\pdir.txt"; CurrentDirectory=$root}
```
(the same `cmd /c set QUEUE_MAX_WAIT_SECONDS=172800&& ...` form for layout, wordjump and r4lib), then `python scripts/queue_priority.py` for below-normal priority. A PC reboot still stops everything.

After a reboot, double-click `scripts/restart_queues.bat` (it calls `scripts/restart_queues.ps1`, which does exactly the above, refuses to start a second copy when queues already run, and `-DryRun` only prints).
