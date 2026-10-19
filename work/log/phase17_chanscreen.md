# Phase 17: chanscreen session log

Nothing in LP2 is solved. User authorized a new channel-aware engine, gated in
order, stop at first failed gate. No campaign, commits or shared-file edits.

## 1. Intake

- Read CLAUDE.md, STATUS.md, SESSION_LOG.md, PLAN.md, CAMPAIGNS.md and newest
  runner report; branch main matches locally recorded origin/main (no network).
- Existing untracked queue outputs and other agents' folders left alone.
- Builds and kscreen data exist; shared overnight selftest not invoked.
- Read M04 harness/README/baseline log, catalogue and collision definitions.
- Python 3.12.0 available; Numba not installed. Metadata probe stopped on missing
  Numba; no install attempted. No GPU computation performed.
- Frozen protocol written to work/chanscreen/README.md before any gate execution.
- Important semantics: fixed-stream skip tail cannot be replaced with an iid-key
  geometric approximation. Uncapped skip and harness skip5 are distinct kernels.
  Key exhaustion must be a failure atom, not conditioned away.

## 2. G0/G1 and training integration

- G0 PASS: 340,800 rational comparisons, 34,080 normalized trees, 45 long-tail
  checks, four mutation witnesses; 13.51 s. Raw: work/chanscreen/g0.json.
- G1 PASS: 230,040 NumPy comparisons +50 random edge cells; max probability
  error 5.55e-17, 43.30 s. Rust CPU accelerator 1,000 parity cases, max log
  error 3.55e-15; raw g1.json and g1_cpu.json.
- Full six-test suite passed in 69.43 s, including genuine branching 300/600
  cases and Viterbi-vs-enumerated maxima. Rust 1.99.1, local rustc cdylib build;
  no shared cargo build, no GPU work.
- First training invocation hit a bytes-to-NumPy ctypes adapter bug before any
  score. All eight attempt markers and original adapter/manifest preserved in
  work/chanscreen/history/training_integration_failure/. Corrected bytes input
  conversion, added regression test, reran SAME training seeds. No threshold
  tuning or held-out evaluation. Seven-test corrected suite passed.
- Training positives (four strata) scores 196.783, 193.300, 165.783, 204.089;
  winning plaintext accuracy .9933, .9900, .9767, .9867. Four matched training
  wrong-key maxima -135.873, -148.097, -150.738, -161.059. Not G2 power estimates.
- Model fitted only on training Emerson; q fits read unchanged. Frozen input
  and source hashes in frozen.json; raw bank/ciphertext/plaintext/all 1024 cell
  scores saved per case. Calibration begins with original baseline seeds,
  batches <=50 (roughly 5 minutes, four workers). No held-out scores at that point.

## 3. Calibration and held-out G2

- Calibration 200/200 complete, original seeds, 1,024 cells each. Frozen
  threshold -135.15812268992306 nats; max -123.567331, median -149.381151.
- Held-out run order: hold records 0..99; nulls 280..379 to check size before
  spending further effort; spend/regression 100..279. Every held-out seed once.
  No model/threshold/seed modifications after inspection.
- G2 PASS: M04 100/100, every stratum 25/25, 100/100 winning decodes >=.95
  accurate (mean .988633), exact offset 98/100, +/-3 alias 100/100. Spend 100/100;
  skip5 40/40; coin 40/40. Nulls 4/100 (two Cicada/iid, two Emerson/iid).
- All null winners used hold; this confirms relative path-freedom score elevation,
  not a failed size gate at this small scope. Full-bank null behavior unknown.
- Calibration took 1,260.45 s in four batches; held-out 2,892.92 s in eight
  batches, every invocation below 30 min. Four workers, one BLAS thread each.
- All raw banks, plaintexts, ciphers, scores and traces retained in
  work/chanscreen/raw/. Full seven-test suite passed in 68.49 s, zero skips.

## 4. G3 failure — STOP

- After G2 passed, wrote GPU_README.md protocol supplement, float64-only CUDA
  forward port and one-shot 100,020-cell parity harness. No cascade implemented.
- First invocation: NVRTC cannot open math.h at generated-source line 2.
  G3 FAIL, 0 completed parity cells, 0 measured engine-kernel device seconds.
  No workaround/retry, no alternate seed, no G4/G5 execution.
- g3.json preserves the diagnostic with temporary compiler path removed for
  privacy. gpu_parity.npz preserves generated inputs; result arrays are NaN,
  not results. GPU throughput and occupancy unknown.
- Proposed untested repair only in REPORT.md: use NVRTC built-in math instead
  of that header and provide an explicit supported infinity expression. Requires
  a separately authorized follow-up preserving this failed attempt.

## 5. Delivery / audit

- REPORT.md gives gate statuses, every failure/correction, power/alias results,
  costs, caveats, remaining work, proposed registry rows (not written to registry).
  RUNNING.md gives local rebuild, <5-minute suite and read-only audit commands.
- Read-only audit PASS: 588 records, 602,112 scores, model/input/calibration hashes
  and selected maxima consistent. Actual calibration throughput 162.48 normalized
  scores/s at four workers. Optimistic 2e8-cell CPU projection 341.9 h; four-channel
  8e8-cell projection 1,367.7 h. These are not real-key-length campaign estimates.
- Privacy scan before final report: 1,229 text files /178,796,861 bytes, no flagged
  user/computer identifiers or absolute paths; binaries/cache ignored locally.
  Final deliverable scan PASS: 1,231 text files, zero flags (privacy_scan.json).
  Git diff of tracked files was empty at delivery. No installs, downloads, network calls,
  commits, campaign or LP2 searches. Existing queue files changed while working,
  consistent with the user's other queue; none was read for results or modified.
- Needs approval: continuation after G3 failure; any future >30-minute run or
  >4-hour cumulative GPU use. No such long run was used here. API credit balance
  and session dollar cost unknown; no project script called an external API.

## 2026-10-19 — v2 authorized continuation (entry before E0)

- User authorized R1 sparse-state / R2 all-offset backward investigation with
  v1 immutable. First deliverable: v2/v1_m04_snapshot.json hashes every v1 and
  M04 file, including builds, excluding the new v2 tree. No existing file edited.
- Read requested files in the specified order. Git main matches locally recorded
  origin/main; no fetch/network, existing dirty/shared files left untouched.
- Read all three desktop queue TSVs and inspected process list: layer2 is active;
  no process disturbed. At intake GPU reports 3% use and 7,317 MiB allocated;
  existing desktop/application processes present, no GPU work started here.
- Wrote v2/README.md protocols for E0-E5 before gate execution. CPU <=4 threads,
  single commands <30 min, compute <=8 CPU h /2 GPU h; later gates blocked.
- Preliminary derivation suggests an even tighter R1 bound: at most TWO distinct
  plaintext classes per pointer, one for skip channels. Rational proof/checker
  and NumPy log-space all-offset reference implemented, not yet validated.
  Per-state log probabilities avoid shared-offset row-scale underflow.

### 2026-10-19 — v2 gate results and budget stop

- E0 PASS: 340,800 exact rational comparisons, 96,000 all-offset passes,
  34,080 normalized trees, 405 extra finite-tail offset checks. All seven
  mutations caught. 25.37 s. R1 bound at most2; skip/skip5 at most1. A separate
  longer-key coin test shows2 classes (the tiny m<=3 grid only reached1).
- Built a NEW dependency-free Rust cdylib under v2/build. O(n*m) all-offset
  log-DP, O(m) memory; uncapped equal-key skip tails handled by a reverse
  recurrence and precomputed run ends. No lag approximation or cascade.
- E1 PASS: all593,920 stored cal/held cells plus100,020 unchanged parity inputs;
  max log error1.319e-11 and score error1.274e-11 nats, limit1e-9. Same support.
  First10 and all520 long/plant parity inputs checked directly with v1 NumPy;
  all inputs checked against the dense Rust reference. No new power seeds.
  An additional115,020 tiny-offset comparisons pass; a12,433.96-nat offset
  gap stays finite. One calibration equality is flagged within1e-9 ambiguity.
  Checkpoints total2,056.60 s single-worker wall time, no command over30 min.
- E2 PASS: all five channels, both signs, n300/600, keys2000/20000, warmup+3
  timings; measured median four-worker speedup3.244x. n300/m20000 hold30,690
  offsets/s one worker; spend31,581; skip149,548; skip5126,992; coin125,562.
  No LP2 scores: only section lengths and library lengths read.
- Real inventory1439 streams /13,326,835 values; stride150 plus end anchors
  gives82 n300 windows,943,984 passes /8,742,403,760 cells for four channels
  and both signs. Projection48.55 CPU-work hours,14.96 wall hours on4 workers,
  4.28 wall hours on14 threads by UNMEASURED linear extrapolation. Thus the
  user's conditional GPU branch is not triggered; no g3b attempt.
- E3 budget stop, INCOMPLETE: zero real-bank nulls. Even30 n300 null windows
  project17.76 CPU-work hours; frozen protocol's30 per length53.66 CPU-work
  hours /16.54 four-worker wall hours. Both-length199 calibration355.94 CPU
  hours;200 recovery plants178.86 CPU hours. No over-budget pilot launched.
  Pre-registered symbolic candidate rule max(null maxima)+10 nats; numeric
  threshold unknown. LM-mismatch/library power unmeasured. E4/E5 blocked.
- Budget interpretation explicitly conservative: CPU-hours count compute work.
  If the intended limit was8 wall hours at4 workers, a30-window n300-only pilot
  might fit (~5.47 h), but needs an explicit follow-up scope decision. Alternate
  approval request: GPU calibration acceleration even though campaign estimate
  is below8 h. No installs/downloads requested.
- Final six-test suite PASS in36.15 s, zero skips. SHA-256 verification: all1241
  v1/M04 files unchanged, no added original-tree files. Final artifacts and
  instructions in v2/REPORT.md and RUNNING.md; proposed registry rows only.
- Measured/upper-bound-proxy compute including tests is below0.7 CPU-work hours;
  GPU compute0. Existing layer2 process, queue outputs and dirty shared files
  untouched. No commits, installs, downloads, network calls or LP2 search.
- Delivery privacy check included binary builds, not only text. It caught local
  paths in new v2 MSVC backward.pdb /backward.dll.exp; removed those nonessential
  debug/linker artifacts (DLL/source/gate results unchanged). Redacted finding
  retained as v2/privacy_initial.json; final scan recorded separately. RUNNING.md
  now documents removal after rebuild. No original v1 file was touched.


### 2026-10-19 — step2 (GPT) and follow-up F1-F4 (GPT, finished by Claude)

- step2 (`v2/step2/`): thresholds frozen before any scoring, T300 = 29.799206297530528
  (82 windows, 8,742,403,760 cells), T600 = 29.5821417922927, alpha .001 per length.
  E3' proof gate FAIL: the per-cell bound under U_cell holds for all channels, but U_cell is
  not one common null near the key end (hold) or across key content (skip5, coin). Exact
  witnesses, incl. Q29/n300 toy LM at 2.07x the per-cell bound. E3/E4/E5 stopped there.
- Follow-up (`v2/step2/followup/`, protocols frozen per part): F1 common-null score S_W PASS
  (340,800 cells, 48,696 exact tails under W); F2 reuse of the 380 saved held records,
  descriptive: 280/280 true cells at T300 for S and S_W, nulls 0/100; F3 exact finite-hold
  factor PASS, skip5/coin worst-case penalty 8.53 / 17.08 nats (n300 / n600).
- F4 guard S_guard = min(S, S_W): GPT wrote the protocol and f4.py and did not run it.
  Claude reviewed f4.py against F4_PROTOCOL.md (no change) and ran each part once: exact
  m 0..3 PASS (340,800 cells, 48,708 tails checked under both U_cell and W, 46,488 uniform-LM
  controls <= 1), numeric PASS (1.8e-15 nats vs saved F1 exact arrays), reuse 280/280 kept,
  0/100 nulls, null max -132.15. All 2,325 original-score wrong-offset exceedances at t = 10
  lie within +-15 of the true offset (aliases, the only offsets v1 stored): the literal
  count rule fails 403 of 2,240 passes, so it needs an alias exclusion.
- Added test_followup.py (4 tests, about 4 s) and deliver.py: originals unchanged against
  the follow-up baseline, privacy scan PASS (174 files), artifact hashes. Report and
  decision list in `v2/step2/followup/REPORT.md`. E3-E5 not started; no LP2 search.
- Line endings: GPT wrote many v1/v2/step2 JSON and log files with CRLF; `.gitattributes`
  stores them as LF. The SHA-256 manifests (v2 and step2 snapshots, follow-up baseline and
  artifacts) hash the desktop's CRLF working copies, so their verify commands and
  test_followup's originals test report those files as changed on a fresh checkout. The
  content is the same; only the desktop working copy matches the recorded bytes.
