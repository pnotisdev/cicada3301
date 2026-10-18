# Prespecified three-scale T6 echo-hit dispersion

Executed once on user authorization, 2026-10-18. **Nothing in LP2 is solved.**
Frozen decisions and limitations: [PROTOCOL.md](PROTOCOL.md).

- Within-word T6 hits ONLY; exactly 80 hits among 1290 eligible pairs.
- Three frozen lower-tail scales: section counts, section-reset 100-eligible-pair
  bins (partial tails included), internal inter-hit gap CV in eligible exposure.
- Independent inhomogeneous Bernoulli BEFORE conditioning on total 80; exact
  conditional finite sampling by dynamic program. Prior doublet-fit q_s frozen.
- Bernoulli negative controls: 0/4 flags. Random-phase evenly spaced positive
  controls: 4/4 flags, all three scales at raw p=.001 / adjusted .003 floor.
  Plants match both total and every site's conditional inclusion marginal.
- LP2 raw p=.024 / .030 / .687; Bonferroni .072 / .090 / 1.000. Omnibus **.072,
  no flag**. No scale/offset/tail changed after seeing the result.
- Both invocations FINISHED in 11.6 s and 7.2 s; each passed 28 tests, zero skips,
  unchanged 95 s cap, no failures, retries, code/protocol edits, GPU or background job.

Full report with file/line citations, raw controls/test JSON and original logs:
`results/independent/desktop/20261018-echo-dispersion-summary/REPORT.md`.

This is a SITE-PROCESS diagnostic, not an exact forward-cipher test. Shared-
ciphertext dependence and uncertainty in q_s are not propagated. The hypothesis
was motivated by previous LP2 smoothness, not independently replicated. Strong
fully regular 80-hit controls do not measure power for 35 regular hidden repairs
among natural hits; that power remains unknown. No new exclusion or decryption.

Original commands (do not automatically rerun):

```
python work/independent/echo_dispersion/gate.py controls
python work/independent/echo_dispersion/gate.py test --controls <current FINISHED controls.json>
```
