# Overnight runner output, one folder per PC

`jobs/overnight.py` writes everything about a run into `results/overnight/<alias>/`. The alias is never the
computer's real name, because the repository may become public. It comes from the git-ignored file `.lp_machine`
in the repository root (one word, e.g. `desktop`) or from the `LP_MACHINE` environment variable. Without
either, a random `pc-xxxxxx` is chosen and saved there. Paths and the computer name are scrubbed from the logs.
Two PCs can therefore run campaigns and push without ever editing the same file.

| File | Content |
|---|---|
| `REPORT.md` | Verdict per campaign, from the results this PC can see (its own plus everything pulled) |
| `logs/<campaign>__<step>.log` | Full output of each step: command, working folder, exit code, duration |
| `state.json` | Steps run on this PC: success, minutes, finish time |
| `unittests.ok` | Time of this PC's last passing run of the 44 tests |
| `kscreen_selftest.txt` | This PC's keystream-screen controls (planted keys recovered, random keys below threshold) |

The campaign results themselves live in the shared folders (`results/kscreen/`, `results/prng/`,
`results/walk/`, `results/screens/`, `results/analysis/`, `results/payload/`). A step whose output already exists
there is skipped on every PC, so work done on one machine is not repeated on the other after a pull.

Machines so far:
- `laptop`: the 15 W laptop (Ryzen 7 7730U, 16 threads) where the project started.
- `desktop`: the PC with the RTX 2080 Ti and 32 GB RAM (from the handoff on).
