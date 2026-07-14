#!/usr/bin/env bash
# Run the birthday wish mailer from its own venv, independent of caller's CWD
# (the app reads .secret.json and birthdays.csv relative to the repo root).
# Usage: ./run.sh [--test]
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")"

PYTHON="${PYTHON:-python3}"

if [[ ! -x .venv/bin/python ]]; then
    echo "No venv found - creating one with ${PYTHON} ..."
    "$PYTHON" -m venv .venv
    .venv/bin/pip install --quiet -r requirements.txt
fi

exec .venv/bin/python main.py "$@"
