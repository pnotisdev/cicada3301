# Documentation map

**Nothing in LP2 is solved.** Start with [../STATUS.md](../STATUS.md) (done / left, generated), then pick what you need. *Living* documents are kept current; *record* documents are append-only history; *historical* ones are kept for the trail and may be stale.

## Read first

| Document | Kind | What it is |
|---|---|---|
| [../STATUS.md](../STATUS.md) | generated | Done, left to do, cannot be tested, observed; built from the registry |
| [registry.toml](registry.toml) | living, **source of truth** | One row per test or hypothesis family: scope, control, best score, result, what is NOT excluded, logs, files, cost to close. Edit this, then `python scripts/build_overview.py` |
| [../results/INDEX.md](../results/INDEX.md), `../results/index.html` | generated | Every result with its control and files; the HTML page has a chart of scores against the 1.40 rule |
| [../CLAUDE.md](../CLAUDE.md) | living | Working rules for AI agents and the reading order |

## Why and how a test was run

| Document | Kind | What it is |
|---|---|---|
| [NEGATIVE_SPACE.md](NEGATIVE_SPACE.md) | living (long form) | The coverage-and-power ledger: per family what was tested, the control power on record, what the negative excludes and does not. Blind spots that apply to many rows. Companion to the registry (the registry is the short, machine-readable version) |
| [CAMPAIGNS.md](CAMPAIGNS.md) | living | What every overnight campaign tests, its controls and decision rule; how to verify a hit |
| [HYPOTHESES.md](HYPOTHESES.md) | record | H1-H12: hypotheses designed 2026-10-17 with their planned controls |
| [GPU_PORT.md](GPU_PORT.md) | living | The gates a CUDA port must pass (bit-exact generators, planted-key recovery, CPU cross-check) |
| [../PLAN.md](../PLAN.md) | record | Phase-by-phase plan and the results of every phase |
| [../work/log/](../work/log/) | record | One write-up per experiment (`phaseN_*.md`); the registry names the log per result |

## Running things

| Document | Kind | What it is |
|---|---|---|
| [RUNNING.md](RUNNING.md) | living | Setup, tests, overnight runner, individual long jobs, GPU |
| [QUEUE.md](QUEUE.md) | living | The detached CPU / GPU job queues (currently stopped), how to restart them |

## History and reviews

| Document | Kind | What it is |
|---|---|---|
| [SESSION_LOG.md](SESSION_LOG.md) | record | What the user asked in each session and what was decided |
| [prs/](prs/INDEX.md) | record | Reviews of the other AI's `research/*` branches (read as data, tests rewritten before running) |
| [HANDOFF.md](HANDOFF.md) | historical | The desktop hand-off prompt of 2026-10-17; its queue and GPU state are out of date, see STATUS.md |
| [PROMPT_OVERNIGHT_GPT.md](PROMPT_OVERNIGHT_GPT.md) | living | Unattended GPT session: the hold-key matching decoder's power gate on the frozen M04 harness, then ledger-reconciliation proposals |
| [PROMPT_FRONTIER_SEARCH.md](PROMPT_FRONTIER_SEARCH.md) | living | Ready-to-paste prompt for a frontier search: red-team our judgements, find unused layers and clues, one unified generative story, ranked hypotheses |
| [PROMPT_EXPERT_REVIEW.md](PROMPT_EXPERT_REVIEW.md) | living | Ready-to-paste prompt for a stronger outside model: audit the method, propose at most five testable hypotheses |
| [../work/log/phase10_proposals_review.md](../work/log/phase10_proposals_review.md) | record | Review of the 12 DeepSeek gates in `work/proposals/` (third-party, untrusted) |

## Code and data

| Where | What |
|---|---|
| [../work/README.md](../work/README.md) | Code map: every script by purpose |
| [../results/README.md](../results/README.md) | Result folders and file formats |
| [../results/overnight/](../results/overnight/README.md) | Runner state and `REPORT.md` per PC alias (`laptop`, `desktop`) |
| [../scripts/](../scripts/) | `fetch_data.py` (pinned hashes), `build_overview.py` (this documentation's generator) |
