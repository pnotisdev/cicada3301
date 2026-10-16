#!/usr/bin/env bash
# One-time setup on a new machine: Python deps, data, Rust builds, test suite.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PYTHON:-python3}
$PY -m pip install -r requirements.txt
$PY scripts/fetch_data.py --images          # transcription, word list, Emerson, 75 page images (verified)
$PY work/phpmt/export_data.py              # PRNG sweep inputs
$PY work/walk/make_data.py                 # solver inputs (LM, LP2, held-out English)
(cd work/phpmt && cargo build --release)
(cd work/walk && cargo build --release)
$PY -m unittest discover -s work/tests -v
echo "setup complete"
