"""Build Rollingold data reports and static HTML."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .breadth import aggregate_breadth, fetch_and_aggregate, load_raw_payload
from .config import DEFAULT_CONFIG_PATH, PROJECT_ROOT, AppConfig, IndustryConfig, load_config
from .data_sources import (
    amount_series,
    close_series,
    equal_weight_series,
    load_etf_history,
    load_etf_spot,
    load_sw_history,
)
from .indicators import (
    divergence_notes,
    rotation_snapshot,
    score_industry,
    status_label,
    trace_comment,
)
from .render import render_html


def build_report(
    *,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    breadth_path: str | Path = PROJECT_ROOT / "data" / "state" / "breadth_history.json",
    cache_dir: str | Path = PROJECT_ROOT / "data" / "cache",
    offline_fixture: str | Path | None = None,
    refresh_cache: bool = False,
) -> dict[str, Any]:
    app_config = load_config(config_path)
    breadth = _load_breadth(app_config, breadth_path=breadth_path, offline_fixture=offline_fixture)
    histories_day = _load_histories(
        app_config,
        period="day",
        cache_dir=cache_dir,
        offline_fixture=offline_fixture,
        refresh_cache=refresh_cache,
    )
    histories_week = _load_histories(
        app_config,
        period="week",
        cache_dir=cache_dir,
        offline_fixture=offline_fixture,
        refresh_cache=refresh_cache,
    )
    benchmark_day = close_series(histories_day[app_config.benchmark_code])
    benchmark_week = close_series(histories_week[app_config.benchmark_code])

    page_amounts: dict[str, pd.Series] = {}
    page_closes_day: dict[str, pd.Series] = {}
    page_closes_week: dict[str, pd.Series] = {}
    for industry in app_config.industries:
        page_closes_day[industry.name] = equal_weight_series(
            [close_series(histories_day[source.code]) for source in industry.price_sources]
        )
        page_closes_week[industry.name] = equal_weight_series(
            [close_series(histories_week[source.code]) for source in industry.price_sources]
        )
        page_amounts[industry.name] = _sum_series(
            [amount_series(histories_day[source.code]) for source in industry.price_sources]
        )

    amount_confirm = _amount_confirmations(page_amounts)
    industries = []
    market_avg = breadth.get("latest_market_average")
    for industry in app_config.industries:
        daily = rotation_snapshot(
            page_closes_day[industry.name],
            benchmark_day,
            momentum_window=20,
            path_points=60,
        )
        weekly = rotation_snapshot(
            page_closes_week[industry.name],
            benchmark_week,
            momentum_window=4,
            path_points=52,
        )
        breadth_ma20 = breadth["latest_values"].get(industry.name)
        delta_1d = breadth["delta_1d"].get(industry.name)
        delta_5d = breadth["delta_5d"].get(industry.name)
        confirmed = amount_confirm.get(industry.name, False)
        score = score_industry(
            price_x=daily.price_x,
            momentum_y=daily.momentum_y,
            breadth_ma20=breadth_ma20,
            breadth_delta_5d=delta_5d,
            amount_confirm=confirmed,
        )
        item: dict[str, Any] = {
            "name": industry.name,
            "aliases": list(industry.aliases),
            "price_sources": [source.name for source in industry.price_sources],
            "price_x": daily.price_x,
            "momentum_y": daily.momentum_y,
            "quadrant": daily.quadrant,
            "path_daily": daily.path,
            "path_weekly": weekly.path,
            "weekly": {
                "date": weekly.date,
                "price_x": weekly.price_x,
                "momentum_y": weekly.momentum_y,
                "quadrant": weekly.quadrant,
            },
            "breadth_ma20": breadth_ma20,
            "breadth_delta_1d": delta_1d,
            "breadth_delta_5d": delta_5d,
            "relative_breadth": breadth["relative_breadth"].get(industry.name),
            "amount_confirm": confirmed,
            "amount_share": amount_confirm.get(f"{industry.name}:share"),
            "amount_share_ma20": amount_confirm.get(f"{industry.name}:share_ma20"),
            "score": score,
        }
        item["status"] = status_label(
            quadrant_value=daily.quadrant,
            momentum_y=daily.momentum_y,
            breadth_ma20=breadth_ma20,
            market_breadth_avg=market_avg,
            breadth_delta_5d=delta_5d,
            amount_confirm=confirmed,
        )
        item["divergences"] = divergence_notes(
            price_x=daily.price_x,
            momentum_y=daily.momentum_y,
            breadth_ma20=breadth_ma20,
            market_breadth_avg=market_avg,
            breadth_delta_5d=delta_5d,
            amount_confirm=confirmed,
        )
        item["comment"] = trace_comment(item)
        industries.append(item)

    industries.sort(key=lambda item: item["score"], reverse=True)
    for rank, item in enumerate(industries, start=1):
        item["rank"] = rank

    latest_price_date = max(str(path[-1]["date"]) for path in (item["path_daily"] for item in industries) if path)
    etfs = _build_etf_section(
        app_config,
        page_closes_day,
        cache_dir=cache_dir,
        offline_fixture=offline_fixture,
        refresh_cache=refresh_cache,
    )
    latest_etf_date = str(etfs.get("meta", {}).get("latest_date") or "")
    report = {
        "meta": {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "latest_date": max(str(breadth["latest_date"]), latest_price_date, latest_etf_date),
            "price_latest_date": latest_price_date,
            "breadth_latest_date": breadth["latest_date"],
            "etf_latest_date": latest_etf_date,
            "benchmark": {"name": app_config.benchmark_name, "code": app_config.benchmark_code},
            "data_quality": breadth.get("quality", {}).get("message", "数据已生成"),
        },
        "industries": industries,
        "rankings": _rankings(industries),
        "breadth": breadth,
        "etfs": etfs,
        "methodology": {
            "score_weights": {
                "price_relative_strength": 0.30,
                "relative_momentum": 0.25,
                "ma20_breadth": 0.20,
                "breadth_delta_5d": 0.15,
                "amount_confirm": 0.10,
            },
            "disclaimer": "仅供研究参考，不构成投资建议",
        },
    }
    return report


def write_report(path: str | Path, report: dict[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_html(path: str | Path, report: dict[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(report), encoding="utf-8")


def _load_breadth(
    app_config: AppConfig,
    *,
    breadth_path: str | Path,
    offline_fixture: str | Path | None,
) -> dict[str, Any]:
    if offline_fixture:
        raw = load_raw_payload(Path(offline_fixture) / "breadth_raw.json")
        return aggregate_breadth(raw, app_config.industries, fill_missing=True)
    path = Path(breadth_path)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return fetch_and_aggregate(fallback_path=path)


def _load_histories(
    app_config: AppConfig,
    *,
    period: str,
    cache_dir: str | Path,
    offline_fixture: str | Path | None,
    refresh_cache: bool,
) -> dict[str, pd.DataFrame]:
    codes = [app_config.benchmark_code] + app_config.all_price_codes
    histories: dict[str, pd.DataFrame] = {}
    for code in codes:
        histories[code] = load_sw_history(
            code,
            period=period,
            cache_dir=cache_dir,
            offline_fixture=offline_fixture,
            refresh=refresh_cache,
        )
    return histories


def _build_etf_section(
    app_config: AppConfig,
    page_closes_day: dict[str, pd.Series],
    *,
    cache_dir: str | Path,
    offline_fixture: str | Path | None,
    refresh_cache: bool,
) -> dict[str, Any]:
    spot = load_etf_spot(cache_dir=cache_dir, offline_fixture=offline_fixture, refresh=refresh_cache)
    items: list[dict[str, Any]] = []
    for industry in app_config.industries:
        selected = _select_etf(spot, industry)
        history = load_etf_history(
            selected["code"],
            cache_dir=cache_dir,
            offline_fixture=offline_fixture,
            refresh=refresh_cache,
        )
        etf_close = close_series(history)
        consistency = _etf_consistency(etf_close, page_closes_day[industry.name])
        points = _etf_points(etf_close)
        latest_point = points[-1] if points else {}
        item = {
            "industry": industry.name,
            "code": selected["code"],
            "name": selected["name"],
            "match_note": industry.etf_rule.match_note,
            "match_source": selected["source"],
            "candidates": selected["candidates"],
            "market_value_yuan": selected["market_value_yuan"],
            "market_value_100m": _round_or_none(
                selected["market_value_yuan"] / 100_000_000 if selected["market_value_yuan"] is not None else None,
                2,
            ),
            "latest_price": selected["latest_price"],
            "latest_return_pct": consistency["etf_latest_return_pct"],
            "industry_latest_return_pct": consistency["industry_latest_return_pct"],
            "consistency": consistency["label"],
            "correlation": consistency["correlation"],
            "direction_match_pct": consistency["direction_match_pct"],
            "latest_date": latest_point.get("date"),
            "points": points,
        }
        items.append(item)
    latest_dates = [str(item["latest_date"]) for item in items if item.get("latest_date")]
    return {
        "meta": {
            "latest_date": max(latest_dates) if latest_dates else "",
            "spot_date": _spot_date(spot),
            "source": "AKShare fund_etf_spot_em / fund_etf_hist_em",
            "consistency_window": "最近 120 个共同交易日",
        },
        "items": items,
    }


def _select_etf(spot: pd.DataFrame, industry: IndustryConfig) -> dict[str, Any]:
    rule = industry.etf_rule
    fallback = {
        "code": rule.fallback_code,
        "name": rule.fallback_name,
        "source": "fallback",
        "market_value_yuan": None,
        "latest_price": None,
        "candidates": 0,
    }
    if spot.empty or "名称" not in spot.columns or "代码" not in spot.columns:
        return fallback

    frame = spot.copy()
    frame["代码"] = frame["代码"].map(_code_str)
    frame["名称"] = frame["名称"].astype(str)
    frame["总市值_num"] = pd.to_numeric(frame.get("总市值"), errors="coerce")
    frame["最新价_num"] = pd.to_numeric(frame.get("最新价"), errors="coerce")

    mask = pd.Series(False, index=frame.index)
    for term in rule.include_any:
        mask = mask | frame["名称"].str.contains(term, regex=False, na=False)
    for term in rule.exclude_any:
        mask = mask & ~frame["名称"].str.contains(term, regex=False, na=False)
    candidates = frame[mask].sort_values("总市值_num", ascending=False)

    if candidates.empty and rule.fallback_code:
        candidates = frame[frame["代码"] == rule.fallback_code].copy()

    if candidates.empty:
        return fallback

    row = candidates.iloc[0]
    market_value = _float_or_none(row.get("总市值_num"))
    latest_price = _float_or_none(row.get("最新价_num"))
    return {
        "code": _code_str(row.get("代码")),
        "name": str(row.get("名称") or rule.fallback_name),
        "source": "live",
        "market_value_yuan": market_value,
        "latest_price": latest_price,
        "candidates": int(len(candidates)),
    }


def _etf_consistency(etf_close: pd.Series, industry_close: pd.Series) -> dict[str, Any]:
    frame = pd.concat(
        [etf_close.rename("etf"), industry_close.rename("industry")],
        axis=1,
        join="inner",
    ).dropna()
    returns = frame.pct_change().replace([float("inf"), float("-inf")], pd.NA).dropna().tail(120)
    if returns.empty:
        return {
            "label": "数据不足",
            "correlation": None,
            "direction_match_pct": None,
            "etf_latest_return_pct": None,
            "industry_latest_return_pct": None,
        }

    correlation = _float_or_none(returns["etf"].corr(returns["industry"]))
    direction_match = float(((returns["etf"] >= 0) == (returns["industry"] >= 0)).mean() * 100)
    if correlation is not None and correlation >= 0.72 and direction_match >= 62:
        label = "一致"
    elif correlation is not None and correlation >= 0.50 and direction_match >= 55:
        label = "部分一致"
    else:
        label = "偏离"

    return {
        "label": label,
        "correlation": _round_or_none(correlation, 2),
        "direction_match_pct": _round_or_none(direction_match, 1),
        "etf_latest_return_pct": _round_or_none(float(returns["etf"].iloc[-1] * 100), 2),
        "industry_latest_return_pct": _round_or_none(float(returns["industry"].iloc[-1] * 100), 2),
    }


def _etf_points(close: pd.Series, limit: int = 240) -> list[dict[str, Any]]:
    series = close.sort_index().dropna().tail(limit)
    returns = series.pct_change() * 100
    points: list[dict[str, Any]] = []
    for date_value, close_value in series.items():
        daily_return = returns.loc[date_value]
        points.append(
            {
                "date": str(date_value.date() if hasattr(date_value, "date") else date_value),
                "close": round(float(close_value), 4),
                "return": _round_or_none(_float_or_none(daily_return), 2),
            }
        )
    return points


def _spot_date(spot: pd.DataFrame) -> str:
    if spot.empty or "数据日期" not in spot.columns:
        return ""
    values = [str(item)[:10] for item in spot["数据日期"].dropna().tolist()]
    return max(values) if values else ""


def _float_or_none(value: Any) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _round_or_none(value: float | None, digits: int) -> float | None:
    return None if value is None else round(float(value), digits)


def _code_str(value: Any) -> str:
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text.zfill(6)


def _sum_series(series: list[pd.Series]) -> pd.Series:
    frame = pd.concat(series, axis=1, join="outer").fillna(0)
    return frame.sum(axis=1)


def _amount_confirmations(page_amounts: dict[str, pd.Series]) -> dict[str, Any]:
    frame = pd.concat(page_amounts, axis=1, join="outer").fillna(0).sort_index()
    total = frame.sum(axis=1).replace(0, pd.NA)
    shares = frame.div(total, axis=0).fillna(0)
    confirmations: dict[str, Any] = {}
    for name in frame.columns:
        share = shares[name]
        ma20 = share.rolling(20, min_periods=5).mean()
        latest_share = float(share.iloc[-1])
        latest_ma20 = float(ma20.iloc[-1]) if not pd.isna(ma20.iloc[-1]) else latest_share
        confirmations[name] = latest_share > latest_ma20
        confirmations[f"{name}:share"] = round(latest_share, 5)
        confirmations[f"{name}:share_ma20"] = round(latest_ma20, 5)
    return confirmations


def _rankings(industries: list[dict[str, Any]]) -> dict[str, list[str]]:
    by_score = sorted(industries, key=lambda item: item["score"], reverse=True)
    by_delta = sorted(
        industries,
        key=lambda item: item["breadth_delta_5d"] if item["breadth_delta_5d"] is not None else -999,
        reverse=True,
    )
    by_bad_delta = sorted(
        industries,
        key=lambda item: item["breadth_delta_5d"] if item["breadth_delta_5d"] is not None else 999,
    )
    weak_repair = [item for item in by_score if item["status"] == "弱势修复" or item["quadrant"] == "走强"]
    slowing = [item for item in by_score if item["status"] == "强势放缓" or item["quadrant"] == "走弱"]
    return {
        "top_strength": [item["name"] for item in by_score[:5]],
        "improving": [item["name"] for item in by_delta[:5]],
        "deteriorating": [item["name"] for item in by_bad_delta[:5]],
        "weak_repair": [item["name"] for item in weak_repair[:5]],
        "slowing": [item["name"] for item in slowing[:5]],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Rollingold report data or static HTML.")
    parser.add_argument("--mode", choices=("html", "data"), default="html")
    parser.add_argument("--output", default="docs/index.html")
    parser.add_argument("--data", help="Render HTML from an existing report JSON.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--breadth-input", default=str(PROJECT_ROOT / "data" / "state" / "breadth_history.json"))
    parser.add_argument("--cache-dir", default=str(PROJECT_ROOT / "data" / "cache"))
    parser.add_argument("--offline-fixture", help="Directory containing offline fixture files.")
    parser.add_argument(
        "--refresh-cache",
        action="store_true",
        help="Refresh AKShare price history even when local cache files exist.",
    )
    args = parser.parse_args(argv)

    if args.mode == "data":
        report = build_report(
            config_path=args.config,
            breadth_path=args.breadth_input,
            cache_dir=args.cache_dir,
            offline_fixture=args.offline_fixture,
            refresh_cache=args.refresh_cache,
        )
        write_report(args.output, report)
        print(f"wrote {args.output} ({len(report['industries'])} industries, latest {report['meta']['latest_date']})")
        return 0

    if args.data:
        report = json.loads(Path(args.data).read_text(encoding="utf-8"))
    else:
        report = build_report(
            config_path=args.config,
            breadth_path=args.breadth_input,
            cache_dir=args.cache_dir,
            offline_fixture=args.offline_fixture,
            refresh_cache=args.refresh_cache,
        )
    write_html(args.output, report)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
