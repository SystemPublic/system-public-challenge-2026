#!/bin/sh
# Verify this replication package. Set PYTHON to an interpreter that has the packages in requirements.txt.
# The Python version the package was recorded under is on the first line of requirements.txt. With uv:
#   uv venv --python <that version> .venv && uv pip install --python .venv/bin/python -r requirements.txt
#   PYTHON=.venv/bin/python ./run.sh
# Pass --refetch to compare the pinned sources with the live ones.
set -e
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
exec "$PY" verify.py --python "$PY" "$@"
