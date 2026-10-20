# Frontier review execution log

Scope: offline read-only inventory and algebra only; no engine or key search.
All new files stay in `work/independent/frontier/`. Nothing in LP2 is solved.

## Inventory invocation A — FAILED before writing final artifacts

Command: `PYTHONIOENCODING=utf-8 python -B work/independent/frontier/audit.py`
External timeout: 120 seconds. Single foreground process.

The independent transcription assertions passed. Parsing the local generated
`work/kscreen/data/library.tsv` with ordinary CSV/splitlines failed:
`TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'`.
No completed `AUDIT.md` or `audit.json` was produced by that invocation.

Correction: parse numeric TSV tails without treating control characters in stream
names as ordinary row/column boundaries; independently read the KSB1 record count.
This is a file-format correction to an inventory, not a resampled statistical gate.
The failed invocation is retained here rather than represented as a completed run.

## Inventory invocation B — FINISHED

Same command and timeout, after the file-format correction. Audit runtime:
0.259 seconds. Standard library only, one foreground process. No simulated
ciphertexts, parameter fitting, significance tests or engine subprocesses.

Independent transcription assertions: 12,956 runes, 2,896 words, 86 doublets in
12,947 within-section transitions; lag-5 104/2,105 with 11 S-S hits at 74 source-S
opportunities; lag-6 T hits 80/1,290. Library TSV numeric-tail record count agrees
with its KSB1 header: 1,439, of which 858 have the plain-additive marginal flag and
581 do not. Full values and input hashes are in `audit.json`.

Found one malformed heading layout: `head0.15@2982`, 334 runes versus an L sum of
333. The local generated `pages.txt` is empty; this does NOT invalidate an older
page-restart experiment with different input hashes. Both issues need provenance
and export checks before reusing those local files.

## Inventory invocation C — FINISHED; historical-menu correction

Same command and timeout. Runtime: 0.081 seconds. Recomputed the inventory only;
no simulations, gates, random seeds or searches. Transcription/library/window
results unchanged. Source and implementation hashes are recorded in `audit.json`.

Additional source inspection showed that the non-word lag-feedback scope extension
actually covers lags 5 and 6, not the full lag-1..8 rectangle suggested by the
registry shorthand. Corrected this review's own menu arithmetic before using it
as historical evidence. The advertised 25,984-cell rectangle is NOT counted as
executed. The recorded residual grid also identifies all shifts under chi-square;
it has fewer distinct scores than printed rows. Retained this correction rather
than promoting an inflated look count. `AUDIT.md` now describes the final inventory.

## Inventory invocation D — FINISHED; prior/ratio qualification

Same inventory command and timeout; runtime 0.067 seconds. Counts unchanged.
Added a formal qualification before delivery: the ungated prototype is not its
claimed local Bernoulli-prior process, but a common whole-layout normalizer can
cancel between the language and uniform masses under stated assumptions. The
one-step mass 1.784 is not, alone, proof of an invalid likelihood ratio under
EVERY reinterpretation. `LIKELIHOOD_NOTE.md` derives the different mask prior and
keeps finite-key/layout-conditioning limitations explicit. No decoder was run
or gate retried; no claim that a corrected prior restores power.

## Concurrent files outside the review

A later read-only `git status` showed untracked H5 prelaunch scripts, generated
plant/null data, logs and sweep TSVs outside this directory. They were not written
or executed by this review; they are left untouched and excluded from the
completed-evidence snapshot. The user was notified. Later the working campaign
and launcher also changed. A read-only diff was inspected; no script was run.

Preserved the original campaign in `evidence/h5_campaign_01b31fe.md`, SHA-256
`b8a43ad2b7a0e66a823e826d16e57ba5420d04c216f392cb2ca1a3501d5ec94d`, independently
checked against `git show 01b31fe:work/h5rs/CAMPAIGN.md`. Preserved the provisional
control report in `evidence/h5_prelaunch_partial.txt`, SHA-256
`8a86c91af69a1ce4f496b44ac184a41925e8ee0da3129f169d8c2a2ee825769a`, matching
`work/h5rs/prelaunch_controls.txt` when copied. It retains the failed true-offset
plant, the passing replacement and the then-incomplete larger-null measurement.
This review did not execute/revalidate those experiments or change their files.
They are separately labelled provisional evidence, not a completed certificate.

No fetch/pull/push/commit was performed, and no shared tracked file was edited by
this review. Its pinned snapshots prevent concurrent changes from silently
rewriting the evidence behind the report's H5 citations.

## Artifact validation — initial invocation FAILED; citation bounds corrected

Command: `PYTHONIOENCODING=utf-8 python -B work/independent/frontier/validate.py`,
external timeout 120 seconds, one foreground process. This validates document
shape, Python syntax, citation line bounds, source hashes and privacy only.
It is not a cipher, null, planted-key, power or significance test.

Initial result: two out-of-range citations (`red_runs.py:44-97` in a 92-line file,
`phase10_squares.md:23-32` in a 30-line file). Corrected them to their actual
end lines. All other line-bound checks and the pinned campaign-hash check passed.
The executive summary was counted at 502 whitespace words including citations.
Subsequent validation output and source manifest are retained in `VALIDATION.md`
and `evidence_manifest.json`; rerunning this document validator refreshes those
artifacts and never changes a statistical seed, hypothesis or gate.

## Corrected artifact validation — FINISHED

After correcting the two citation endpoints, validation completed with zero
errors: 12 claim rows, 8 hypothesis entries, 147 numbered citation occurrences,
and 502 executive-summary whitespace words including citations. Python syntax
checks and the privacy/pinned-source checks passed. Final metadata-only reruns
of this validator may refresh hashes after report edits; the final source hashes
and invocation duration are in `evidence_manifest.json` / `VALIDATION.md`.
No result is represented as a passed cryptanalytic gate.

## Final reconciliation — concurrent HEAD advanced to b38bc2e

The final read-only `git status` / `git log -3` check found HEAD had advanced from
01b31fe to b38bc2e through the other review, not an operation by this audit.
Read the updated campaign completely and the completed prelaunch control report.
Its one-window campaign-size null result supersedes the earlier incomplete copy;
the report now credits that measurement and rule correction instead of repeating
the smaller-bank criticism as an untouched current omission. Other-window null
matching, the launcher's documented default and the missed true plant remain
explicit limitations. New throughput is credited rather than dismissed using the
older loaded rate. No engine, benchmark, campaign or comparison was rerun here.

The new `evidence/h5_prelaunch_b38bc2e.txt` is byte-identical to the b38bc2e Git
blob (SHA-256 `8be6a0b0a8dad6c07b781527972f22932176d80f76057eeaa5340eeebbee54f4`).
`evidence/h5_update_b38bc2e.md` preserves four declared campaign excerpts, checked
against the source line ranges. The original full campaign and in-progress
control snapshot remain for traceability. Final artifact validation is rerun to
refresh report/source hashes; its current citation count may exceed the earlier
147. This does not add a cryptanalytic trial or authorize execution.

## Inventory invocation E — FINISHED; equivalence-class wording

Same inventory command, external cap 120 seconds; runtime 0.3846 seconds. Counts
unchanged. Clarified that 392 b-shift classes are an UPPER BOUND on the number of
distinct residual chi-square values, not a numerical-uniqueness measurement.
Changed the JSON/markdown field name and explanatory sentence accordingly.
This was a deterministic inventory/document correction, not a statistical retry.

Final source check: the live campaign SHA-256 and `git show
b38bc2e:work/h5rs/CAMPAIGN.md` both equal
`8cd9a55a298c902700f34233bef51d3937e2b048ad22dd287f3b62f534d74262`.
The latest completed artifact check before this metadata edit had 152 numbered
citation occurrences, 505 executive-summary whitespace words and zero errors;
the final validator output supersedes its timing/hash metadata only.
