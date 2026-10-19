# Follow-up state, 2026-10-19

**Nothing in LP2 is solved. No LP2 search, null, plant or campaign has been run.**

- F1, F3, F4 PASS; F2 descriptive audit complete (`REPORT.md`). Every part ran once; write-once
  markers reject reruns. No process is running.
- E3' proof stays FAIL. E3 (real-bank sanity nulls), E4 (200 plants) and E5 (queue and summary
  script) are not started: they wait for the decision in `REPORT.md` ("Needs a decision").
- Recommended contract: tier 1 is S_guard = min(S, S_W) >= T (T300 = 29.799206297530528,
  T600 = 29.5821417922927 from `../thresholds.json`), with a frozen +-k alias exclusion for the
  wrong-offset count. Freeze it in a new protocol file before running anything.
- Inherited cost (E2 projections, not measured runs): 5 n300 + 3 n600 sanity nulls about 2.0 wall
  hours on 4 workers; 200 conditional-stream plant scans about 5 minutes of scoring; full 82-window
  campaign about 15 wall hours on 4 workers (not to be launched without approval).
- Checks: `python -B work/chanscreen/v2/step2/followup/test_followup.py` (4 tests, about 4 s);
  `deliver.py` wrote `immutability.json`, `privacy_scan.json`, `artifacts_sha256.json` once.
