# Step2 frozen protocol — 2026-10-19

Nothing in LP2 is solved. New writes only in this folder. v1/v2/M04 immutable,
SHA-256 snapshot first. <=8 HOURS ELAPSED total, <=4 CPU threads, every command
<=30 min with checkpoints; NO GPU. No installs, downloads, commits, process
changes or writes to results/shared documents. Stop at the first failed gate.

## Inventory and frozen thresholds (before any score/null/plant computation)

Read v2/e2.json, not LP2 ciphertext. n300 uses its82 windows and full inventory:
1439 streams,13,326,835 key values, two signs, four channels, every initial offset
0..m-1 (including short suffixes). N300=82*13,326,835*8.
There is no previous n600 window inventory. Extend the SAME stride150 and final
end-anchor policy to n600 using the stored section lengths; this is an explicit
additional length inventory, NOT a second launched campaign. E5 remains n300's
82 windows only. Define N600 analogously. Include impossible cells in N for a
conservative count; never drop finite-key hold suffixes silently.

alpha=1/1000 PER LENGTH, T_n=ln(N_n/alpha). Store exact integer R_n=N_n*1000;
S>=T is equivalent to Z_L/Z_U>=R. Two lengths together would require another
multiplicity allocation for a global alpha=.001; per-length allocation alone
would only give a sum bound of .002 IF its per-cell assumptions were true.
Neither the v1 empirical threshold nor max-null+10 is used here.

## E3' proof prerequisite — distinguish two null measures

1. Cell-matched U: iid uniform PLAINTEXT through that EXACT fixed finite key,
   offset and channel, including failure outcomes. For every channel the
   likelihood-ratio tail inequality should be EXACT, not approximate.
2. Common uniform anti-repeat output process W: first output uniform, repeat
   probability (1-q)/Q, each nonrepeat (Q-1+q)/(Q*(Q-1)). Outputs are Markov,
   not iid; the iid quantities are the underlying fresh uniform plaintext
   draws. W is the common law for unlimited hold/spend, but finite exhaustion
   must be checked, not assumed away. The supplied score remains unchanged.

Freeze the proof gate before running anything:
A. Full v1 G0 tiny grid, Q3, key lengths0..3, offsets0..m, signs +/-1, q0,3/5,1,
all five channels, n0..3, uniform and the v1 nonuniform rational language models.
Enumerate event trees. Success+failure=1; L support contained in U; for EVERY
attained positive rational LR threshold R require exact matched-U tail <=1/R.
Also require sum_U(L/U)=sum_L(success)<=1. Positive controls: L=U; hold/spend
with m-o>=n must have U=W. Save counters and a digest of all exact comparisons.

B. Adversarial finite-key checks (fixed now, no seed search):
- Q3, key(0,0), n3, sign+, q3/5, deterministic constant-zero plaintext, LR
  threshold20. Compute the full W tail and the cell-matched U tail independently.
- Q3, key(1,0), q81/100, pi uniform and bigram uniform among symbols DIFFERENT
  from the previous plaintext, n300 and600. Event: first n-2 transitions all
  nonrepeats, final transition repeats. Exact finite-key LR and W event mass,
  with one representative sequence cross-checked by v1 rational DP.
- Q29, key(3,0), q81/100, pi uniform, bigram uniform over the26 increments
  excluding0,1,2, n300. Event: first n-2 ciphertext increments in that same set,
  final transition repeats. Compute exact event mass under W and representative
  finite-key L/U by rational DP, and compare at the frozen campaign threshold.
These are valid normalized toy LMs, NOT the English production LM and NOT LP2
observations. They test whether normalization alone proves the proposed rule.

C. Fixed key-dependence diagnostics for skip5/coin: Q3, n2, q3/5, sign+,
keys(0,0,0,0,0,0,0) and(0,0,1,1,1,1,1), uniform plaintext. Exact total variation
and maximum W/U density ratio (infinite if W>0,U=0). Report only this toy gap;
the full-bank gap is not inferred from it.

Acceptance: A must pass; any counterexample to the claimed common-null exact
hold/spend bound on included finite-key cells is E3' FAIL, even if A passes.
Report it, preserve unchanged scores/thresholds, STOP before sanity searches,
E4' or queue construction. No silent replacement of the null, offset filter,
LM or denominator. This gate tests a universal proof claim, not actual English
false-positive frequency. A failure does not prove campaign FWER>.001.

## E3' sanity searches (only if proof prerequisite passes)

Five n300 full-bank wrong-key windows: original v1 cal records0..4, unchanged.
Three n600 windows: original v1 English/iid cal seeds100..102, extended because
v1 has no n600 M04 null ciphertext records. Reconstruct original RNG state using
the original300-rune window selection and398-value draws; take600 plaintext
runes from the stored start, append independently seeded iid secret-key values
using SHA-256 domain 'step2-n600-tail|original_seed', without perturbing the
original encryption RNG state. Require first300 ciphertext runes to equal v1,
and sufficient source/key extent; otherwise fail, no replacement seed. These
extensions are explicitly not existing stored n600 v1 plants. Decoder q=.81;
generator uses original q fit, matching v1, not a refit. No new library null
calibration: every maximum MUST be below T_n or E3' fails. Record observed doublets,
all maxima and scan counts. Five/three windows cannot certify a .001 tail rate.
The English M04 generator is not proven to follow W; report that null mismatch.

## E4' conditional-stream power (only after E3' passes)

200 plants:25/channel/length, four channels, n300/600. Seed prefix
chanscreen-step2-plant, fixed tuple(channel,n,index). For each group12 held
Cicada /13 held Emerson, signs alternate. Choose uniformly among library streams
with enough length for the channel's maximum key consumption, then uniformly
among eligible offsets (hold/spend need n, skip5 6n, coin 3n). Short ineligible
streams remain in the bank inventory but are not power-tested by these plants.
Search ONLY the planted stream: all offsets, four channels, both signs. No
claim of identifying that stream among1439 is possible under this conditional
scope. Report true-cell detection S>=T, exact offset/sign/channel, +/-3 aliases,
winner and true-cell Viterbi accuracy, source strata. Visible engineering target:
>=90% pooled and >=20/25 each channel/length; >half detected winners accurate>=.95.

For EVERY pass count wrong-offset exceedances at t=0,5,10 against N_wrong*exp(-t).
Wrong offsets include +/-3 aliases: do not remove them after inspection. This is
a requested empirical check, not a deterministic consequence of the LR theorem:
counts can exceed expectations, and plant-neighbor offsets are not null data.
A failed requested check is reported and stops the gate, not tuned away.

Additional fixed test: seed prefix step2-first-repair, English held pool, M04,
n300 and600; cut at the FIRST repaired output in a fixed128-rune prefix, with
sufficient following plaintext/key. Absence of a repair is a reported failure,
not a new seed. The unchanged decoder initializes with no previous ciphertext;
measure this known initialization mismatch rather than changing v2.

## E5 (blocked until controls pass)

Resumable stream-block jobqueue package over the82 n300 windows; tier1 S>=T300,
tier2 top50 per channel/window explicitly UNVERIFIED ranks (not leads). Frozen
summary must refuse unsupported proof/gate status. No LP2 search launched.
Whole-window/section verification with positive and matched-null controls.
Human REVIEW.md documents backward.rs invariants even if statistical gates fail.

## Reproduction

Use .venv/Scripts/python.exe -B. Freeze: python -B freeze.py (write-once).
Proof gate: python -B gate.py (write-once; returns failure on refutation).
Deterministic unit suite: python -B test_step2.py (expected counterexamples may
be asserted as regression tests without turning a failed gate into PASS).
All paths in commands are relative to this folder or the repository root.
