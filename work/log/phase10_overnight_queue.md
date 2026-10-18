# The first overnight run of the detached queues (2026-10-18 01:25 - 08:37; stopped at the user's request 10:35)

Scope: LP2 sections 0.7-0.15 and the 44 page windows. **Nothing in LP2 is solved.** The queues of `docs/QUEUE.md` ran unattended. All results are negative.

## What ran

**The sign campaign** (`kscreen-signs`, started by hand at 00:15, finished about 06:26): all 61 word-level key-sign rules over the 581 flat-IoC library streams, 8 sections at every offset, 21.7 billion decodes in all. **Best IoC 1.388** (C_cur_ws), then 1.388 (B7_prev_pf), 1.380 (B5_cur_wp and B5_cur_w), 1.371 (A_prev_pf), 1.366 (C_cur_n); **none reaches the 1.40 rule**, and the whole-window
re-decode keeps none of the top hits of any rule (61 verification files: '0 of 5'). Random keys reach about 1.37 at 10^10 decodes (`docs/CAMPAIGNS.md`) and the campaign made about 2 x 10^10, so 1.388 is noise-level, thin margin as predicted. With the five sign-flat streams (best 1.293) this closes the value-sign mechanism for the 61 rules:
**negative**. Rules flipping 20% of the runes or fewer were already covered by the earlier unsigned screens (`phase10_signrules.md`).

**The GPU lane** (about 8 h): the per-page seed sweeps of `phase10_pages_py3.md` for the other seven generators over the epoch seconds 2011-2015 (php, glibc, mt32, mt31, msvc, drand48, ruby; 126,230,400 seeds x 44 page windows, about 10.5 min each) and for all eight over the seeds 0 .. 2^27 (134,217,728 seeds, about 10.5 min each):
**16 sweeps with the one from before (py3 epoch seconds), 0 candidates at +300 in every one** (`results/prng/bgtime_<gen>_pages.*`, `bgsmall_<gen>_pages.*`, all `_verify.txt`: no candidate reached the floor). The millisecond-timestamp months (section 0.7, 120-rune windows, gate +300): java and py3 now cover all 25 months 2012-01 .. 2014-01
(66 billion seeds each: 1.95 h and 3.02 h of GPU time); **java-abs** 2012-03 .. 2014-01 (23 months, 60.8 billion seeds, 1.48 h); **ruby** 2012-12 .. 2014-01 (14 months, 37.1 billion, 1.42 h); 0 candidates in every month (`results/prng/time_gpu/`). Not swept: java-abs 2012-01 and 2012-02, ruby 2012-01 .. 2012-11.

## What did not run, and why

`signs-periodic` (the 25 per-rune periodic sign templates), `layer2` (the remaining H1 slices) and `prng-bg` (the full-seed section sweeps) failed within a second of starting: **my queue driver was called `jobs/queue.py`, which shadows Python's standard `queue` module for every script in `jobs/`; the runner imports it** ('module queue has no attribute Queue'). Renamed
`jobs/jobqueue.py`; the runner imports again. The direct GPU jobs were not affected. When the fix was restarted the user asked for no more long runs, so both lanes were stopped and their scheduled tasks deleted (10:35); a few seconds of the restarted jobs left only logs. Still queued, nothing running: the periodic templates (about 2.7 h CPU), `layer2` (about 3 h CPU), `prng-bg` (4.5 h GPU), java-abs 2012-01 / 02 and ruby 2012-01 .. 11 (about 1.5 h GPU).
