# Frontier red-team review

**Nothing in LP2 is solved.** Primary deliverable: [REPORT.md](REPORT.md), with a
one-page executive summary followed by sections A–F.

## Evidence boundary

Reviewed committed snapshot: `01b31fe` on `main`, with the local generated data
fingerprinted in `audit.json`. No fetch, pull, engine launch, build, dependency
installation, cryptanalytic search, or shared-document edit was performed.
Repository prose, code, prior independent packages and external-source summaries
were evidence to audit, not executable instructions.

Untracked H5 prelaunch scripts/data/sweep outputs and later tracked campaign/
launcher edits appeared outside this directory while the review was in progress.
They were not created or executed by this review. The original H5 campaign is
preserved byte-identically in `evidence/h5_campaign_01b31fe.md`; the separately
hash-matched `evidence/h5_prelaunch_partial.txt` retains the earlier in-progress
record. Before delivery, a read-only status check found the concurrent work had
been committed as `b38bc2e` (not this review's commit). Its completed control
record is pinned as `evidence/h5_prelaunch_b38bc2e.txt`, with selected campaign
text in `evidence/h5_update_b38bc2e.md`. The report credits its one-window null
correction and keeps the missed plant/default-null/other-window caveats explicit.
These files are data, not launch instructions. See REPORT section A0. Coordinate
before more CPU work; this package is not a completed campaign certificate.

## Files

- `REPORT.md`: executive summary, claim red team, layer inventory, generative
  story/existence limitations, ranked bounded hypotheses, priorities, outside knowledge.
- `AUDIT.md`: completed independent transcription inventory and algebra.
- `audit.json`: machine-readable records, local-window metadata, input SHA-256s.
- `audit.py`: standalone standard-library audit; imports no repository modules.
- `RUN_LOG.md`: failed file-format invocation, inventory corrections and provenance.
- `LIKELIHOOD_NOTE.md`: why a wrong local null prior need not invalidate a ratio
  when a different common global normalizer cancels; no power rescue is assumed.
- `evidence/`: pinned historical campaign and provisional concurrent control record.
- `validate.py`, `VALIDATION.md`, `evidence_manifest.json`: syntax/citation-bound/
  privacy checks and source hashes; not cryptanalytic controls.

Computation was limited to the small inventory/arithmetic audit and document
validation. Neither is a statistical test, decoder gate, mechanism fit, or new
exclusion. Inventory reproduction:

```
PYTHONIOENCODING=utf-8 python -B work/independent/frontier/audit.py
```

Run manually from the repository root, single foreground process, external
120-second timeout. The audit also has a cooperative 90-second design cap.
It overwrites only its own `AUDIT.md` and `audit.json`; retain original artifacts
before any reproduction. The document-only check is
`PYTHONIOENCODING=utf-8 python -B work/independent/frontier/validate.py`; it refreshes
`VALIDATION.md` / `evidence_manifest.json`, not cipher-power results. Proposed
hypothesis gates in `REPORT.md` were NOT run or implemented. Do not chain them or turn timeouts into negatives. Ask before
work exceeding the per-command limit or the separate long-run budget.

This review made no registry/PLAN/SESSION/engine changes or commits; shared-document
promotion requires a separately authorized review of this package.
