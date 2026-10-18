# Collision follow-up A–E — human-run only

**UNEXECUTED / UNVALIDATED. Nothing in LP2 is solved.** No program, test, syntax
check, simulation or discriminator was executed by the assistant. Existing files
were not edited. See [PROTOCOL.md](PROTOCOL.md) for evidence with file/line citations,
frozen choices, assumptions, limits and commands.

| Request | Deliverable | Important limit |
|---|---|---|
| A | Fixed training sections 7,9,12,14; validation 8,11,13,15; train full family, validate one frozen rule | Retrospective stability, not untouched replication |
| B | B=999 full test, five separately run changed-code controls, certificate with hashes | Each foreground gate capped at 95 s of cooperative work; runtime unknown |
| C | Own-doublet raw-T6 expected section counts; 199-book refitted heterogeneity bootstrap; 999 paired-null selection-optimism estimate | Plug-in/post-selection diagnostics; true inflation of the observed 80 remains unknown |
| D | Count-versus-LR explanation, one-branch S-copy candidate, opportunity-budget audit | No mechanism demonstrated to fit all constraints; no new post-hoc likelihood search |
| E | Exact rational reference power for 35 hidden repairs among 80 independent sites, external English difference law and stated re-collision geometry | Actual-site power unknown; no LP2 discriminator implemented or proposed |

Suggested first prerequisite is **power calculation only**, not an experiment on
LP2. From repository root, if the human chooses:

```powershell
$env:PYTHONIOENCODING='utf-8'
python work/independent/collision_followup/analysis.py power
```

This runs local identities (old exact-kernel suite plus the new tests), reads only
the existing English reference corpus and writes `power.json` plus `run.log` in a
fresh `results/independent/<alias>/...` folder. Require FINISHED. It uses the standard
library and NumPy; no network, install, GPU, build, subprocess or background job.
If it times out, preserve the failure and stop; do not extend the cap.

For B/A, run the five control cases separately, certify them, then separately
choose test and/or split as specified in PROTOCOL.md. Do not reuse old controls.
All old plant seeds are retained; no retries until a pass. Sections/optimism/
mechanisms are separately optional diagnostics, not automatically launched jobs.

Return completed JSON files with their FINISHED logs, including control misses.
Do not treat an incomplete gate or descriptive lack of significance as an exclusion.
