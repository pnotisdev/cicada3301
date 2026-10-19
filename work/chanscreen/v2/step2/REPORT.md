# Step2: E3' proof FAIL — finite-key null mismatch

**Nothing in LP2 is solved. No LP2 search or campaign was launched.**

The elapsed-time clarification is accepted: <=8 hours wall, <=4 CPU threads,
commands <=30 minutes, no GPU. This stop is **not a budget stop**. The requested
normalization-only common-null proof is false for included short-suffix hold
cells. The cell-matched LR theorem and the existing v2 DP remain valid.

All new files are here. **1,926 pre-existing chanscreen/v2/M04 files unchanged**
against the first-action SHA-256 snapshot (including v1 GPU failure artifacts).
No edits to the phase17 log or any other existing file; session notes instead
are in `WORK_LOG.md`. Existing dirty shared/results files were left alone.

## Frozen inventory and threshold

| n | windows | N_cells | T_n = ln(N_cells/.001), nats |
|---:|---:|---:|---:|
|300|82|8,742,403,760|29.799206297530528|
|600|66|7,036,568,880|29.582141792292700|

n300 is the previous inventory. n600 is explicitly an additional length inventory
using the same stride150 and section-end-anchor rule, from stored section lengths
only. E5's proposed campaign remains82 n300 windows. Counts include all offsets,
including short finite-key suffixes, four channels and two signs. No ciphertext
was decoded for this inventory. Alpha=.001 is per length, not a combined-length
familywise allocation. `thresholds.json` is the untouched pre-gate freeze, not a
certified deployable threshold; consult `E3_proof.json` and `summary.json`.

## Status

| Requirement | Status | Evidence |
|---|---|---|
| Exact rational bound under each cell's U | **PASS** |340,800 enumerated output/model cells;34,080 normalized language event trees;46,602 exact tail inequalities;20,928 common-law checks for sufficiently long hold/spend keys. |
| E3' common-null normalization-only proof | **FAIL** |Exact finite-key hold counterexamples, including Q29/n300 at the frozen T300. |
| Skip5/coin gap | **PARTIAL** |Exact tiny-key distribution gaps measured; full-bank gap unknown. |
|5 n300 +3 n600 full-bank sanity nulls|**INCOMPLETE**|0 run; stopped at failed proof prerequisite. All eight maxima unknown. |
| E4'200 conditional-stream plants + first-repair controls | **INCOMPLETE** |0 run. Detection, exact identification, +/-3 aliases, Viterbi/source strata and first-repair power all unknown. |
| E4' wrong-offset count checks | **INCOMPLETE** |No passes run; logical limitations documented, not silently waived. |
| E5 queue and candidate/ranking summary | **INCOMPLETE** |No queue or campaign scoring script created; not launched. Source invariant review completed in `REVIEW.md`. |

The JSON counter named `output_comparisons` counts enumerated output/model cells,
not independent DP parity comparisons. The46,602 tail inequalities are the exact
bound checks; the small and long witnesses have separate rational-DP cross-checks.

The inherited first-failed-gate rule prevents running later searches and calling
this a passing E3'. No seeds replaced, no threshold adjusted, no failed record
removed. All checks in this proof gate are deterministic, not planted-key power
experiments or a cryptanalytic negative. No LP2 key family is excluded.

## The distinction that breaks the proof

For each fixed cell, on successful outputs:

    P_(U_cell)(S>=t) <= exp(-t) * sum_c Z_L(c) <= exp(-t).

This is EXACT for **all channels**, including skip5/coin. But a campaign union
bound needs these inequalities under the SAME ciphertext law W. In general:

    E_W[exp(S)] = sum_c W(c) * Z_L(c)/Z_U_cell(c),

which is not sum_c Z_L(c). Hold's Z_U is independent of key VALUES, but still
depends on available key length and the finite-key survival event. In the
inventory's suffix offsets it need not equal the common anti-repeat W. With
m-offset>=n, hold/spend DO match W, as positive controls verify exactly.

### Small Q3 witness

Key(0,0), n3, q3/5, constant-zero plaintext LM, t=ln20. The only L-supported
successful outputs are010 and020. Each has L=3/10, U_cell=13/900, LR=270/13.

- Exact matched-cell tail: **13/450 = .0288889 <= .05**.
- Exact common anti-repeat tail: **169/1350 = .125185 > .05**.

The theorem under U passes; its substitution under W fails. This is a finite
failure-mass issue, not rounding or a Viterbi/summed-path confusion.

### At the actual frozen T300, Q29

Key(3,0), n300, q=.81, uniform pi, normalized toy bigram LM uniform over26
increments3..28. This is **not the production English LM**. A family of outputs
with298 increments in that set followed by a repeat has:

- S=299*ln(29/26)=**32.6505882975**, above T300=29.7992062975;
- exact rational W event probability approximately **2.3692317941e-13**;
- allotted per-cell tail bound **1/8,742,403,760,000 = 1.1438501669e-13**;
- event probability **2.0712780945 times the proposed bound**.

Event mass is a LOWER bound on the full tail. The representative path's L and U
were independently verified by the existing rational DP. No full alphabet^300
enumeration or simulation is being claimed; `PROOF.md` derives the event family
and its exact counting formula. Exact fractions are retained in `E3_proof.json`.
This disproves the normalization-only proof even at Q29/n300/T300. It does NOT
show the actual English-LM library FWER exceeds .001; that remains unknown.

Q3 long controls: n300 also refutes at T300 (event probability2.15765e-10,
1,886.308 times its per-cell bound). The predeclared Q3 n600 event does NOT refute
at T600 (probability6.44913e-19, below its per-cell bound). That non-refutation is
preserved, not presented as a positive witness.

## Skip5/coin gap and other statistical limitations

For each channel, Q3/n2/q3/5 keys0000000 versus0011111 give exact U distribution
TV distance **1/5**. Relative to common W, their TV distances are1/5 and1/10;
maximum pointwise W/U is **13/10** for each of these specific keys. All have
success mass1, so this is genuine key-content dependence, not exhaustion.
These tiny examples are NOT a library-wide error bound. Real-bank gap unknown.

The wrong-offset criterion count(S>=t)<=N*exp(-t) is stronger than the theorem:
under a valid null the theorem bounds an EXPECTATION, not every realized count.
Offsets neighboring a positive plant can also be non-null aliases. With fewer
than22,027 wrong cells, t10 demands zero exceedances; one real alias fails it.
We preserved the requested check literally in the protocol, rather than quietly
removing aliases or assigning it a false deterministic guarantee.

The v1 wrong-key generator encrypts English through M04, not iid uniform
plaintext. Matching its doublet rate to W does not prove equality of the entire
output law. Eight sanity nulls cannot certify a .001 library-wide tail rate.
Also, conditional-stream E4' cannot measure identification of that stream among
1439 alternatives: stream identity is supplied, not recovered. All such claims
remain explicitly conditional or unknown.

## Cost and resources

Inherited E2 benchmarks, NOT new measured search times:

-5 n300 +3 n600 sanity searches: **2.019 projected wall hours** at the measured
 four-worker speedup3.24415, plus export/checkpoint/contended-system overhead.
-200 planted-stream-only scans at20,000 key values: **.0832 projected wall hours**
 (~5 minutes) for scoring, NOT full-bank power searches. Generation, Viterbi,
 extra controls and diagnostics are additional; their duration is unknown.
-82-window n300 full campaign: **14.964 projected wall hours at four workers**.
 It would require additional elapsed-time authorization IF eventually launched;
 this request authorizes packaging only. No14-thread projection is used to
 justify exceeding the four-thread limit.

Thus the newly requested sanity/scoring work is not rejected on CPU-work-hour
accounting. It is blocked by the false proof prerequisite.

This session: proof audit5.33 seconds; **6/6 unit tests PASS in9.076 seconds**.
Tests assert that the counterexamples persist: they do not relabel E3' as PASS.
One CPU worker, BLAS limited to one thread; GPU computation0. No compilation,
installation, download, external API call, commit, shared/results write or
process interference. Existing four Python processes and queue TSVs inspected
read-only. Exact assistant-session monetary cost unknown. See `resources.json`
for elapsed delivery timestamp accounting, and `privacy_scan.json` for privacy.

## Needs your approval

A separately labeled follow-up must preserve this failed attempt. Options:

1. **Use one common-null denominator**, keeping the v2 engine unchanged:
   S_W=log Z_L-log W(c) = S+log Z_U-log W(c). Then sum_c Z_L<=1 gives the exact
   bound under W for EVERY channel and finite offset. This changes the frozen
   statistic and needs fresh power checks; it does not prove that the English
   M04 sanity null or LP2 follows W. No such change was implemented here.
2. Keep S but authorize a new rigorously bounded density correction / offset
   scope. Restricting hold/spend to sufficient key length fixes their common-W
   issue but does NOT by itself fix skip5/coin. No offset exclusion was applied.
3. Keep the requested numeric T as a **heuristic** with no certified common-null
   alpha guarantee; explicitly authorize continuing past the failed proof to
   the eight sanity searches and conditional power checks. Do not call this a
   proof repair or use eight maxima as a .001 calibration.

Also clarify whether the wrong-offset observed-count inequality is intentionally
a hard empirical stop despite alias/non-null and finite-sample issues, or should
be diagnostic only. Its present protocol remains the literal hard check.

## Deliverables / registry proposal only

`README.md`, `thresholds.json`, `PROOF.md`, exact audit code/results,
`REVIEW.md`, `tests.txt`, `RUNNING.md`, `WORK_LOG.md`, read-only `summary.py` and
`summary.json`, immutable hashes and final privacy/resource records. No campaign
queue exists. `summary.py` summarizes this failed audit, not LP2 candidates.

Proposed row, NOT entered in the registry: chanscreen-v2-step2-bound; scope
finite-key matched-U versus common anti-repeat W; controls340,800 exact output/model
cells /46,602 tail bounds and sufficiently long-key W equality; result
common-null proof FAIL (Q29/n300 toy LM at proposed T300:2.0713x bound), own-U
PASS. Actual English false-positive rate and real-library power not measured;
no LP2 negative or exclusion. Files this folder, detailed notes `WORK_LOG.md`.
