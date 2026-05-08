#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="$ROOT/src:${PYTHONPATH:-}"

python3 -m rollingold.breadth --output data/state/breadth_history.json
python3 -m rollingold.site --mode data --output reports/latest.json
python3 -m rollingold.site --data reports/latest.json --output docs/index.html

echo "generated docs/index.html and reports/latest.json"

