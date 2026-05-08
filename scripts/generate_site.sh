#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="$ROOT/src:${PYTHONPATH:-}"

PYTHON_BIN="${ROLLINGOLD_PYTHON:-}"
if [ -n "$PYTHON_BIN" ] && [ ! -x "$PYTHON_BIN" ]; then
  echo "configured ROLLINGOLD_PYTHON is not executable: $PYTHON_BIN" >&2
  exit 1
fi
if [ -z "$PYTHON_BIN" ]; then
  if [ -x "$ROOT/.venv/bin/python" ]; then
    PYTHON_BIN="$ROOT/.venv/bin/python"
  else
    PYTHON_BIN="python3"
  fi
fi

"$PYTHON_BIN" -m rollingold.breadth --output data/state/breadth_history.json
"$PYTHON_BIN" -m rollingold.site --mode data --refresh-cache --output reports/latest.json
"$PYTHON_BIN" -m rollingold.site --data reports/latest.json --output docs/index.html

echo "generated docs/index.html and reports/latest.json"
