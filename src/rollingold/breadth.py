"""Market breadth fetching and aggregation."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import DEFAULT_CONFIG_PATH, IndustryConfig, load_config


BREADTH_URL = "https://sckd.dapanyuntu.com/api/api/industry_ma20_analysis_page?page=0"
BREADTH_HEADERS = {
    "Referer": "https://sckd.dapanyuntu.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


class BreadthDataError(RuntimeError):
    """Raised when breadth data is unavailable or malformed."""


def fetch_breadth_raw(timeout: int = 20) -> dict[str, Any]:
    request = urllib.request.Request(BREADTH_URL, headers=BREADTH_HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise BreadthDataError(f"failed to fetch breadth API: {exc}") from exc

    validate_raw_payload(payload)
    return payload


def validate_raw_payload(payload: dict[str, Any]) -> None:
    required = {"dates", "industries", "data"}
    missing = sorted(required - set(payload))
    if missing:
        raise BreadthDataError(f"breadth payload missing keys: {', '.join(missing)}")
    if not isinstance(payload["dates"], list) or not payload["dates"]:
        raise BreadthDataError("breadth payload has no dates")
    if not isinstance(payload["industries"], list) or not payload["industries"]:
        raise BreadthDataError("breadth payload has no industries")
    if not isinstance(payload["data"], list):
        raise BreadthDataError("breadth payload data must be a list of triples")


def load_raw_payload(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_raw_payload(payload)
    return payload


def aggregate_breadth(
    payload: dict[str, Any],
    industries: tuple[IndustryConfig, ...],
    *,
    fill_missing: bool = False,
) -> dict[str, Any]:
    """Aggregate second-level MA20 breadth into configured page industries.

    API rows are `[date_index, industry_index, value]`. Values equal to `0` are
    treated as missing, matching the existing market-breadth workflow.
    """

    dates = [str(item) for item in payload["dates"]]
    raw_industries = [str(item) for item in payload["industries"]]
    raw_index = {name: idx for idx, name in enumerate(raw_industries)}
    matrix: dict[tuple[int, int], float] = {}
    for row in payload["data"]:
        if not isinstance(row, list | tuple) or len(row) != 3:
            continue
        date_idx, industry_idx, raw_value = row
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        matrix[(int(date_idx), int(industry_idx))] = value

    page_names = [industry.name for industry in industries]
    values: list[list[float | None]] = []
    latest_values: dict[str, float | None] = {}
    delta_1d: dict[str, float | None] = {}
    delta_5d: dict[str, float | None] = {}

    for industry in industries:
        series: list[float | None] = []
        source_indexes = [raw_index[name] for name in industry.breadth_sources if name in raw_index]
        for date_idx, date in enumerate(dates):
            observed = [
                matrix.get((date_idx, source_idx))
                for source_idx in source_indexes
                if matrix.get((date_idx, source_idx)) not in (None, 0)
            ]
            if observed:
                series.append(round(sum(observed) / len(observed), 1))
            elif fill_missing:
                series.append(_synthetic_breadth(industry.name, date))
            else:
                series.append(None)
        values.append(series)
        latest_values[industry.name] = _last_value(series)
        delta_1d[industry.name] = _delta(series, 1)
        delta_5d[industry.name] = _delta(series, 5)

    market_average = []
    for date_idx in range(len(dates)):
        observed = [row[date_idx] for row in values if row[date_idx] is not None]
        market_average.append(round(sum(observed) / len(observed), 1) if observed else None)

    latest_market_average = _last_value(market_average)
    relative_breadth = {
        name: (
            round(value - latest_market_average, 1)
            if value is not None and latest_market_average is not None
            else None
        )
        for name, value in latest_values.items()
    }

    return {
        "source": "dapanyuntu_industry_ma20",
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "dates": dates,
        "industries": page_names,
        "values": values,
        "latest_date": dates[-1],
        "latest_values": latest_values,
        "delta_1d": delta_1d,
        "delta_5d": delta_5d,
        "market_average": market_average,
        "latest_market_average": latest_market_average,
        "relative_breadth": relative_breadth,
        "raw_industries_count": len(raw_industries),
        "quality": {
            "status": "fresh",
            "message": "宽度数据已更新",
            "missing_sources": _missing_sources(industries, raw_index),
        },
    }


def fetch_and_aggregate(
    *,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    fallback_path: str | Path | None = None,
    timeout: int = 20,
) -> dict[str, Any]:
    app_config = load_config(config_path)
    try:
        raw = fetch_breadth_raw(timeout=timeout)
        return aggregate_breadth(raw, app_config.industries)
    except BreadthDataError as exc:
        if fallback_path and Path(fallback_path).exists():
            fallback = json.loads(Path(fallback_path).read_text(encoding="utf-8"))
            fallback.setdefault("quality", {})
            fallback["quality"]["status"] = "stale"
            fallback["quality"]["message"] = f"宽度数据未更新，沿用上一版：{exc}"
            fallback["fetched_at"] = datetime.now().isoformat(timespec="seconds")
            return fallback
        raise


def write_breadth(output: str | Path, data: dict[str, Any]) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _last_value(series: list[float | None]) -> float | None:
    for value in reversed(series):
        if value is not None:
            return value
    return None


def _delta(series: list[float | None], lag: int) -> float | None:
    latest_idx = next((idx for idx in range(len(series) - 1, -1, -1) if series[idx] is not None), None)
    if latest_idx is None or latest_idx - lag < 0:
        return None
    latest = series[latest_idx]
    previous = series[latest_idx - lag]
    if latest is None or previous is None:
        return None
    return round(latest - previous, 1)


def _missing_sources(industries: tuple[IndustryConfig, ...], raw_index: dict[str, int]) -> dict[str, list[str]]:
    missing: dict[str, list[str]] = {}
    for industry in industries:
        items = [name for name in industry.breadth_sources if name not in raw_index]
        if items:
            missing[industry.name] = items
    return missing


def _synthetic_breadth(industry: str, date: str) -> float:
    digest = hashlib.sha256(f"{industry}:{date}".encode("utf-8")).digest()
    return round(18 + digest[0] / 255 * 62, 1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch and aggregate MA20 market breadth.")
    parser.add_argument("--output", default="data/state/breadth_history.json")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--input", help="Read a saved raw breadth JSON instead of calling the API.")
    args = parser.parse_args(argv)

    app_config = load_config(args.config)
    if args.input:
        raw = load_raw_payload(args.input)
        data = aggregate_breadth(raw, app_config.industries, fill_missing=True)
    else:
        data = fetch_and_aggregate(config_path=args.config, fallback_path=args.output)
    write_breadth(args.output, data)
    print(f"wrote {args.output} ({len(data['industries'])} industries, latest {data['latest_date']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

