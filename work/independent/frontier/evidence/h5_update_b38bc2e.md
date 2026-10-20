# Concurrent H5 campaign update: selected committed text

Source: `b38bc2e:work/h5rs/CAMPAIGN.md`. These are verbatim excerpts, not a
complete file copy. They are evidence only, not permission to launch or change
anything. Numeric results are reported by the concurrent review, not rerun here.
`validate.py` checks each excerpt against its declared source line range.

## Status
<!-- excerpt:start:3-8 -->
Status: **CONTROLS PASS (13/13, `campaign_control.txt`), parity gate re-PASS (312/0) on the
modified binary, PRE-LAUNCH REVIEW DONE (3/3 new plants pass the real file: path - the four
pre-launch controls and their numbers are in `prelaunch_controls.txt`; null-size
justification below: the +0.15-over-8-stream margin is NOT justified at campaign size and
is replaced by the measured 581-stream null max; block-resumable launcher + merge tested),
CAMPAIGN NOT LAUNCHED**.
<!-- excerpt:end -->

## Limits of transferring the one-window null
<!-- excerpt:start:137-144 -->
* Consequence for the controls: the three plants pass against the 8-stream null max (the
  task's control specification) with margins +0.480/+0.402/+0.455; all three still clear
  the measured seg0.8 581-floor (1.7672, m0). The OTHER windows' 581-stream maxima are
  unmeasured (the 8-stream per-window spread is ~1.22-1.52, so a naive +0.256/+0.340
  growth extrapolation would put plant (b)'s seg0.11 floor near its IoC); the per-window
  campaign-scale null max should therefore be MEASURED, not extrapolated - run the null
  sweep with `null581.ksb` (see Launch: `set NULLKSB=...`), +4.2 h at 23.4k/s, or accept
  a window-uniform provisional floor of 1.7672/1.8260.
<!-- excerpt:end -->

## Launcher still needs the right null setting
<!-- excerpt:start:161-164 -->
2. then the matched-null sweep: `%NULLKSB%` (a variable at the top of the launcher;
   default `data/null8.ksb`, ~5 min; per the Null-size justification the campaign-scale
   matched null should use `data/null581.ksb`, ~4.2 h) over the full grid ->
   `results/h5rs_flat_null.tsv` + `results/h5rs_flat_null.log` (with `--best`).
<!-- excerpt:end -->

## New reported throughput and budget
<!-- excerpt:start:244-248 -->
353,248,000 + 4,864,000 (null8) decodes; at the 8-thread rate measured by the null-size
run (23.4k dec/s under the current load; the parity run measured 16.3-18.8k) the 5 real
blocks are ~1.0-1.2 h each (~5-6 h total) and the null8 sweep ~5 min. If the null sweep
uses `null581.ksb` (recommended by the null-size justification), add ~4.2 h. The log's
per-chunk `eta` lines are the live estimate once launched.
<!-- excerpt:end -->
