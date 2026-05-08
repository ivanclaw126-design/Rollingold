#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="$ROOT/src:${PYTHONPATH:-}"

mkdir -p logs reports docs data/state
LOG_FILE="$ROOT/logs/daily-update.log"
exec >>"$LOG_FILE" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] start daily update"

weekday="$(TZ=Asia/Shanghai date +%u)"
clock="$(TZ=Asia/Shanghai date +%H%M)"
if [ "$weekday" -gt 5 ]; then
  echo "not a weekday in Asia/Shanghai, skip"
  exit 0
fi
if [ "$clock" -lt 1620 ]; then
  echo "before 16:20 Asia/Shanghai, skip"
  exit 0
fi

tmp_dir="$(mktemp -d)"
cleanup() {
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

tmp_breadth="$tmp_dir/breadth_history.json"
tmp_report="$tmp_dir/latest.json"
tmp_html="$tmp_dir/index.html"

python3 -m rollingold.breadth --output "$tmp_breadth"
python3 -m rollingold.site --mode data --breadth-input "$tmp_breadth" --output "$tmp_report"
python3 -m rollingold.site --data "$tmp_report" --output "$tmp_html"

new_date="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["meta"]["latest_date"])' "$tmp_report")"
old_date=""
if [ -f reports/latest.json ]; then
  old_date="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["meta"].get("latest_date",""))' reports/latest.json 2>/dev/null || true)"
fi

if [ "$new_date" = "$old_date" ] && [ -f docs/index.html ]; then
  echo "latest trading date unchanged ($new_date), skip commit"
  exit 0
fi

mv "$tmp_breadth" data/state/breadth_history.json
mv "$tmp_report" reports/latest.json
mv "$tmp_html" docs/index.html

if git diff --quiet -- data/state/breadth_history.json reports/latest.json docs/index.html; then
  echo "no file changes after generation"
  exit 0
fi

git add data/state/breadth_history.json reports/latest.json docs/index.html
git commit -m "chore: update industry rotation report $new_date"

if git remote get-url origin >/dev/null 2>&1; then
  git push origin HEAD:main
else
  echo "no origin remote configured, commit created locally only"
fi

echo "daily update complete for $new_date"

