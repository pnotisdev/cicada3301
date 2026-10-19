# Logged diagnostic follow-up — frozen 2026-10-19

Nothing in LP2 is solved. User asked to continue useful work and log checkpoints.
This is NOT permission silently to replace the original statistic or erase E3'.
The failed common-null proof, thresholds and all pre-existing files stay immutable.
New files only here. <=4 CPU workers (use1), no GPU, commands<=10min, overall8h
elapsed from the step2 intake. Write-once checkpoints after each part. No installs,
commits, external API calls, LP2 scores, null generation, new plants or queue launch.

## F1: independently test a PROPOSED correction, not deploy it

Original S=log Z_L-log Z_U_cell remains unchanged. For diagnostics ONLY define
S_W=log Z_L-log W(c), W the common anti-repeat Markov law at a fixed q.
Compute directly from log Z_L, never through inf-inf subtraction. If W(c)=0,
return rejected score -infinity and an explicit outside-null-support flag. These
observations have zero probability under W; rejection preserves the tail bound.
For n0 use log W=0. W need not match the actual English-M04 or LP2 data law.

Prove normalization, finite-key boundaries and common-W union bound. Verify exact
rational tails on the full Q3 grid: all keys lengths0..3, all offsets, signs +/-1,
q0,3/5,1, five channels, n0..3, the same two rational LMs as the original E0.
For every attained positive LR require P_W(S_W>=ln R)<=1/R. Include null controls
L=U; these yield S_W=0 only where U_cell=W, not for arbitrary channels/finite ends.
Compare Float64 S_W calculated from UNCHANGED v2 backward.rs log_L against exact
probabilities at1e-9 nats; unsupported outputs must be consistently rejected.
Save comparison arrays and checkpoints separately per key length, then aggregate.
Fail and stop diagnostics on any arithmetic mismatch; no retry/tolerance change.

Independent long counterexample check: same Q29/n300/2-key example as step2,
using the immutable Rust DLL plus dense v1 rational DP and the closed-form
probabilities. Save old S and proposed S_W. q.81; no new seed. Do not present
this as performance, English power or an E3 pass.

## F2: audit SAVED controls, do not rerun held-out seeds

Read all380 original held JSON records exactly once for this audit (100 hold,
100 spend,40 skip5,40 coin,100 nulls). No new decoder calls or generator execution.
Retain original per-cell log_L/log_U and source-specific decoder q fits. Compare
saved S and counterfactual S_W with FIXED W(q=.81), at the already frozen T300.
This keeps each original numerator unchanged; it is NOT equivalent to a new
campaign whose numerator decoder q=.81. It is exploratory reuse of held data,
not independent power validation and not a replacement for8 full-bank nulls.
No threshold/model/seed tuning from these observations.

For the280 positives, group saved true-stream cells by sign/channel (eight passes).
Exclude the true offset in EVERY pass, even on wrong channels/signs; retain all
other offsets including +/-3 aliases. For t0,5,10 save counts on the stored15
wrong offsets, compare both to15*exp(-t) and to(m-1)*exp(-t), where m is the full
stored stream length. If the observed subset count exceeds the full-pass bound,
the full pass MUST fail that requested count criterion: missing offsets cannot
reduce a count. Otherwise full-pass status is UNKNOWN, not assumed to pass.
Perform this on both old S and proposed S_W. Report strata, individual pass counts,
example cells, and simple maxima; no plaintext reconstruction or cryptanalytic
claim. The old v1 task markers and results remain untouched.

F2 is a diagnostic with descriptive outcomes, not an acceptance gate that can
repair E3. A positive-plant alias is not a null trial. Count bounds from an LR
theorem are expectations, not deterministic upper bounds on observed counts.

## Delivery and continuation

New checkpoint JSON records after each part; raw arrays and audit records saved
before aggregating. Finish with REPORT.md and STATE.md here, immutable-file check,
privacy scan, hashes, and a <5min deterministic unit suite. Production E3/E4/E5
remain blocked until user chooses/authorizes the statistical contract. State
exactly what is known and what remains unknown. No credit balance is available;
do not spend resources merely to exhaust an unknown balance.
