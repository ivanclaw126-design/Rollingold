# Rollingold Agent Notes

Rollingold is a static A-share industry rotation research site. Keep the public output in `docs/index.html` and the latest report data in `reports/latest.json`; GitHub Pages serves from `main:/docs`.

## Local Workflow

- Install once with `python3 -m pip install -e ".[dev]"` inside the repo venv when possible.
- Generate current live data with `python3 -m rollingold.site --mode data --refresh-cache --output reports/latest.json`.
- Generate the static page from report data with `python3 -m rollingold.site --data reports/latest.json --output docs/index.html`.
- Use `python3 -m rollingold.site --offline-fixture tests/fixtures --output /tmp/rollingold-fixture.html` for structure tests only; do not overwrite `docs/index.html` or `reports/latest.json` with fixture output.
- Run `.venv/bin/python -m pytest` for the full suite when the venv exists. On this machine, `/opt/homebrew/bin/pytest` also works, but `python3 -m pytest` may fail if the active Homebrew Python lacks pytest.
- For focused indicator/display changes, `.venv/bin/python -m pytest tests/test_indicators.py` is the minimum useful check.

## Data And Publish Rules

- `scripts/publish_daily.sh` is the automated publish path. It only runs after 18:30 Asia/Shanghai on weekdays and must not overwrite the published report when price and breadth dates are not aligned.
- The source-of-truth freshness fields are in `reports/latest.json` under `meta.latest_date`, `meta.price_latest_date`, and `meta.breadth_latest_date`.
- Width data comes from Dapanyuntu MA20 breadth and is aggregated to the 26 page industries. Price and ETF data come from AKShare.

## Display Contracts

- User-facing metric text should not expose Python float tails. `trace_comment()` formats score, MA20 breadth, and 5-day breadth change to one decimal place and uses `无数据` for missing or non-finite values.
- Keep page copy clear that this is research output only: no individual stock recommendations, no automatic trading instructions, and no return promises.

## Repo Hygiene

- Avoid committing generated cache noise unless it is part of the intended publish artifact. Expected generated publish artifacts are `reports/latest.json`, `docs/index.html`, `data/history/*.csv`, and `data/history/backtest_summary.json`.
- There may be old `tijiao/*` branches from previous submissions. Do not delete unmerged local or remote branches unless the user explicitly asks for cleanup and the branch has no local-only work.
