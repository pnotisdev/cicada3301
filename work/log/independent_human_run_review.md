# Independent review and human-run deliverables (not executed)

**Nothing in LP2 is solved. No new experiment or selftest was run in this pass.**

## User constraints

* Review prior work; do not guess a translation by eye.
* Assess the claimed `7A35090F` → Z5 books connection.
* Write mathematically specified tools that a human starts and returns logs for.
* Keep API/compute spending bounded; do not launch agents or external model calls.
* Another agent is running `work/tmp/relabel_all.py`. Do not touch its process,
  script, results, actively edited engine files or shared documentation.

## Repository review

Read, in project order: `STATUS.md`, `docs/SESSION_LOG.md`, all of `PLAN.md`,
`docs/CAMPAIGNS.md`, newest runner report `results/overnight/desktop/REPORT.md`.
Also read the README, code map, Phase 11/12 reviews, relabel documentation and
relevant parser/decoder/export/verifier code. Initial Git status showed the local
branch aligned with its tracked `origin/main`; no fetch was performed. Existing
uncommitted edits were left alone. Engines/data directories already existed, and
no setup/selftest/build was started.

The runner report contains historical automatic 'CANDIDATE' headings for short
windows; later reviews/STATUS classify them as selection noise. This review uses
the corrected scope, not those headings as decryptions.

Closest reported screen score: 1.415 on 300 runes, dropping to 1.073 over its full
window. It is not a partial plaintext. The word-internal lag-5/lag-6 relations and
unmodelled alignment rules are more useful motivations than near-threshold maxima.

## Deductions, not claimed experimental results

1. **Byte conversion:** `7A 35 09 0F` is lowercase z, digit 5, tab, Shift In.
   It does not encode z5 twice. This leaves a weak prefix/title lead, not evidence
   for two particular books. Bibliography, pre-2014 availability and an authenticated
   Cicada connection were not verified. No book was fetched or read.
2. **Affine coverage:** `c=a(p+m*k)+b` implies
   `c-(a*m)*k=a*p+b`. Thus IoC-based outer-affine searches are already represented
   by the existing all-multiplier screen on the same windows/offsets/models.
   Equality checks are invariant under the bijection. Atbash is covered by a key
   sign. Non-affine keyword alphabets remain a genuinely different case. No job
   was interrupted on account of this observation.
3. **Power claim scope:** the previous free-per-word maximum-IoC null decoder's
   null ceiling does not prove impossibility for a value-gated, fixed-prior
   marginal-likelihood decoder. A planted recovery gate is needed before trying
   LP2 with such a model. No power is asserted for the new implementation.

## New files, all isolated

`work/independent/` contains:

* `MATH.md`: proofs, exact keyless-echo model, controls, limitations and rules;
* `audit.py`: reproducible byte conversion and affine identity/countercontrols;
* `echo_nulls.py`: gate / bounded screen / separate full-section verification;
* `test_core.py`: local unit tests, including an independent exhaustive enumerator;
* `source_gate.py`: optional local-book marginal preflight, not a decryption;
* `manual_common.py`: read-only inputs, fresh per-command logs, hashes and budgets;
* `README.md`: PowerShell commands and exact files to return;
* `.gitignore`: ignores only local third-party `sources/` copies.

The proposed decoder treats a word-internal `c_i=24-2*c_(i-6)` rune as a possible
keyless null with fixed prior, not as an arbitrarily deletable rune. It sums paths
under English and uniform plaintext models, both with the same cipher. It does
not copy the free null beam or modify Rust/CUDA. Its narrow family does not explain
the 42%-of-words length fit or the lag-5 S concentration; those are explicitly out
of scope. The reported lag-6 rate is per eligible pair, not per all-book rune.

The default real search would have 128 settings and 19 whole-search shuffled-key
controls. A passing, current-code/input-hash gate is required. Full-section
verification is a separate human command and includes 20 unsearched same-stream
offsets, unseen-tail scoring and IoC margins. Runtime and power are unmeasured.

## What was NOT done

No new Python program was executed, including `--help`, syntax checks or tests.
No LP2 sweep, background process, GPU use, network fetch, API call, corpus download,
engine build, data export, commit, branch switch or shared-ledger regeneration.
No experiment result files or fake console transcripts were manufactured.

Only the new independent directory and this new review file were written. The
shared project ledger is not changed because there are no new empirical results,
and another agent owns active edits. After a human returns actual logs, record
successes **and failures**, scope and controls in PLAN/registry and regenerate the
overviews in a coordinated follow-up. Start with `audit.py`, then send its log;
there is no reason to queue all proposed commands before review.
