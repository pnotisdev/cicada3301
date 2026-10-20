# D2 first-gate result

**FAILED_RECOVERY_GATE**. Nothing in LP2 is solved (`result.json:3`).

Elapsed seconds: 2.680275. One invocation; no automatic retry (`result.json:592`).

All numbers below are from `result.json`, the retained native rows and the frozen protocol.
This is a synthetic bounded feasibility gate, not a family exclusion or a global power test.

| Case | Long forward IoC | Known-keyword accuracy | Native keyword + independent alignment accuracy | Native control pass | Composition witness | Native source |
|---|---:|---:|---:|---|---|---|
| L13_m0_attempt | 1.001397 | 1.000000 | 0.7833333333333333 | False | False | native_cells.txt:3; result.json:99-165 |
| L13_m0_emission | 1.001982 | 0.993333 | None | False | False | native_cells.txt:21; result.json:166-215 |
| L13_m1_attempt | 1.002196 | 0.993333 | 0.9933333333333333 | True | False | native_cells.txt:40; result.json:216-282 |
| L13_m1_emission | 1.002326 | 0.996667 | None | False | False | native_cells.txt:58; result.json:283-332 |
| L20_m0_attempt | 1.001048 | 1.000000 | None | False | False | native_cells.txt:75; result.json:333-389 |
| L20_m0_emission | 1.000811 | 1.000000 | None | False | False | native_cells.txt:93; result.json:390-446 |
| L20_m1_attempt | 1.001582 | 1.000000 | None | False | False | native_cells.txt:112; result.json:447-503 |
| L20_m1_emission | 1.000540 | 1.000000 | None | False | False | native_cells.txt:130; result.json:504-560 |

## Limits

- Emission-clock cases are unsupported by the native H5 model; retain them as diagnostics.
- The retained c1500 failure is not replaced by a passing offset or counted as recovery.
- Tiny matched null menus do not estimate campaign-wide error or twenty-case power.
- No LP2 look, later calibration, engine patch, build or long run is authorized by this result.
- All inputs/code/protocol hashes, partial results and exceptions: `result.json`.
- Failed or incomplete cases are retained. Do not rerun this gate to improve its outcome.
