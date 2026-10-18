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
