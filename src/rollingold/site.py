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
from .data_contracts import DataQualityReport, summarize_quality
from .factor_panel import build_factor_panel
from .indicators import (
    divergence_notes,
    rotation_snapshot,
    status_label,
    trace_comment,
)
from .phase import classify_phase, detect_phase_transition, transition_reason
from .render import render_html
from .scoring import calculate_score, explain_industry_signal, load_scoring_presets
from .strategy_lab import build_strategy_lab


def build_report(
    *,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    breadth_path: str | Path = PROJECT_ROOT / "data" / "state" / "breadth_history.json",
    cache_dir: str | Path = PROJECT_ROOT / "data" / "cache",
    offline_fixture: str | Path | None = None,
    refresh_cache: bool = False,
) -> dict[str, Any]:
    return build_report_bundle(
        config_path=config_path,
        breadth_path=breadth_path,
        cache_dir=cache_dir,
        offline_fixture=offline_fixture,
        refresh_cache=refresh_cache,
    )["report"]


def build_report_bundle(
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

    etfs = _build_etf_section(
        app_config,
        page_closes_day,
        cache_dir=cache_dir,
        offline_fixture=offline_fixture,
        refresh_cache=refresh_cache,
    )
    etf_by_industry = {item["industry"]: item for item in etfs.get("items", [])}
    scoring_preset = load_scoring_presets()["balanced_v2"]
    panel_day = build_factor_panel(
        config=app_config,
        page_closes=page_closes_day,
        page_amounts=page_amounts,
        benchmark_close=benchmark_day,
        breadth=breadth,
        period="daily",
    )
    panel_week = build_factor_panel(
        config=app_config,
        page_closes=page_closes_week,
        page_amounts=page_amounts,
        benchmark_close=benchmark_week,
        breadth=breadth,
        period="weekly",
    )
    panel_day = _score_and_phase_panel(panel_day, scoring_preset)
    panel_week = _score_and_phase_panel(panel_week, scoring_preset)

    industries: list[dict[str, Any]] = []
    market_avg = breadth.get("latest_market_average")
    for industry in app_config.industries:
        latest_row = _latest_panel_row(panel_day, industry.name)
        previous_row = _previous_panel_row(panel_day, industry.name)
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
        breadth_ma20 = _row_value(latest_row, "breadth_ma20", breadth["latest_values"].get(industry.name))
        delta_1d = _row_value(latest_row, "breadth_delta_1d", breadth["delta_1d"].get(industry.name))
        delta_5d = _row_value(latest_row, "breadth_delta_5d", breadth["delta_5d"].get(industry.name))
        confirmed = bool(_row_value(latest_row, "amount_confirm", False))
        etf = etf_by_industry.get(industry.name, {})
        score = _row_value(latest_row, "score", 0.0)
        score_delta = (
            round(float(score) - float(previous_row["score"]), 1)
            if previous_row is not None and "score" in previous_row
            else 0.0
        )
        item: dict[str, Any] = {
            "name": industry.name,
            "aliases": list(industry.aliases),
            "price_sources": [source.name for source in industry.price_sources],
            "breadth_sources": list(industry.breadth_sources),
            "price_x": _row_value(latest_row, "price_x", daily.price_x),
            "momentum_y": _row_value(latest_row, "momentum_y", daily.momentum_y),
            "quadrant": _row_value(latest_row, "quadrant", daily.quadrant),
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
            "amount_share": _row_value(latest_row, "amount_share", None),
            "amount_share_ma20": _row_value(latest_row, "amount_share_ma20", None),
            "score": score,
            "score_delta_1d": score_delta,
            "score_breakdown": _row_value(latest_row, "score_breakdown", {}),
            "top_contributors": _row_value(latest_row, "top_contributors", []),
            "risk_notes": _row_value(latest_row, "risk_notes", []),
            "phase": _row_value(latest_row, "phase", "观察"),
            "phase_transition": _row_value(latest_row, "phase_transition", "unchanged"),
            "change_reason": _row_value(latest_row, "change_reason", []),
            "confidence": _row_value(latest_row, "confidence", 0.75),
            "factors": _factor_payload(latest_row),
            "risk": _risk_payload(latest_row),
            "breadth": {
                "ma20": breadth_ma20,
                "delta_1d": delta_1d,
                "delta_5d": delta_5d,
                "relative": _row_value(latest_row, "relative_breadth", None),
                "slope_5": _row_value(latest_row, "breadth_slope_5", None),
                "persistence": _row_value(latest_row, "breadth_persistence", None),
            },
            "etf": etf,
            "data_quality": _industry_quality(latest_row, breadth, etf),
            "methodology_note": _methodology_note(industry, etf),
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
        item["interpretation"] = explain_industry_signal(item)
        industries.append(item)

    industries.sort(key=lambda item: item["score"], reverse=True)
    for rank, item in enumerate(industries, start=1):
        item["rank"] = rank

    latest_price_date = max(str(path[-1]["date"]) for path in (item["path_daily"] for item in industries) if path)
    latest_etf_date = str(etfs.get("meta", {}).get("latest_date") or "")
    latest_report_date = max(str(breadth["latest_date"]), latest_price_date, latest_etf_date)
    data_quality_reports = _source_quality_reports(
        histories_day=histories_day,
        breadth=breadth,
        etfs=etfs,
        latest_price_date=latest_price_date,
        latest_etf_date=latest_etf_date,
    )
    data_quality = summarize_quality(data_quality_reports)
    change_log = _change_log(panel_day, industries)
    strategy_lab = build_strategy_lab(panel_day, page_closes_day, benchmark_day)
    report = {
        "meta": {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "latest_report_date": latest_report_date,
            "latest_date": latest_report_date,
            "price_date": latest_price_date,
            "breadth_date": breadth["latest_date"],
            "etf_date": latest_etf_date,
            "date_alignment_status": _alignment_status(latest_price_date, str(breadth["latest_date"]), latest_etf_date),
            "price_latest_date": latest_price_date,
            "breadth_latest_date": breadth["latest_date"],
            "etf_latest_date": latest_etf_date,
            "benchmark": {"name": app_config.benchmark_name, "code": app_config.benchmark_code},
            "data_quality": data_quality,
            "methodology_version": "v2.0",
        },
        "industries": industries,
        "change_log": change_log,
        "rankings": _rankings(industries),
        "breadth": breadth,
        "etfs": etfs,
        "factor_history": _factor_history(panel_day),
        "strategy_lab": strategy_lab,
        "methodology": {
            "score_preset": scoring_preset.name,
            "score_weights": scoring_preset.weights,
            "disclaimer": "仅供研究参考，不构成投资建议；历史模拟，不代表未来收益",
        },
    }
    return {"report": report, "panel_day": panel_day, "panel_week": panel_week}


def _score_and_phase_panel(panel: pd.DataFrame, scoring_preset: Any) -> pd.DataFrame:
    panel = panel.copy()
    scores: list[float] = []
    breakdowns: list[dict[str, float]] = []
    contributors: list[list[str]] = []
    risks: list[list[str]] = []
    phases: list[str] = []
    for _, row in panel.iterrows():
        payload = row.to_dict()
        result = calculate_score(payload, scoring_preset)
        scores.append(result.score)
        breakdowns.append(result.breakdown)
        contributors.append(result.top_contributors)
        risks.append(result.risk_notes)
        phases.append(classify_phase(payload))
    panel["score"] = scores
    panel["score_breakdown"] = breakdowns
    panel["top_contributors"] = contributors
    panel["risk_notes"] = risks
    panel["phase"] = phases
    panel["phase_transition"] = "new"
    panel["change_reason"] = [[] for _ in range(len(panel))]
    for _, group in panel.sort_values("date").groupby("industry"):
        previous_phase: str | None = None
        for idx, row in group.iterrows():
            current_phase = str(row["phase"])
            transition = detect_phase_transition(previous_phase, current_phase)
            panel.at[idx, "phase_transition"] = transition
            panel.at[idx, "change_reason"] = transition_reason(row.to_dict(), transition)
            previous_phase = current_phase
    return panel


def _latest_panel_row(panel: pd.DataFrame, industry: str) -> pd.Series | None:
    rows = panel[panel["industry"] == industry].sort_values("date")
    return None if rows.empty else rows.iloc[-1]


def _previous_panel_row(panel: pd.DataFrame, industry: str) -> pd.Series | None:
    rows = panel[panel["industry"] == industry].sort_values("date")
    return None if len(rows) < 2 else rows.iloc[-2]


def _row_value(row: pd.Series | dict[str, Any] | None, key: str, default: Any) -> Any:
    if row is None:
        return default
    value = row.get(key, default)
    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        return value
    if hasattr(value, "item"):
        try:
            return value.item()
        except ValueError:
            return value
    return value


def _factor_payload(row: pd.Series | None) -> dict[str, Any]:
    keys = [
        "rs_z_120",
        "rs_mom_20_z",
        "rs_mom_60_z",
        "rs_accel_5_20",
        "rs_rank_pct",
        "rs_new_high_60",
        "breadth_slope_5",
        "breadth_slope_10",
        "breadth_above_50",
        "breadth_thrust",
        "breadth_divergence_score",
        "breadth_persistence",
        "amount_share_z_60",
        "amount_mom_5",
        "price_amount_confirm_score",
        "trend_stability",
        "correlation_to_benchmark",
    ]
    return {key: _round_metric(_row_value(row, key, None)) for key in keys}


def _risk_payload(row: pd.Series | None) -> dict[str, Any]:
    return {
        "vol_20": _round_metric(_row_value(row, "vol_20", None)),
        "vol_60": _round_metric(_row_value(row, "vol_60", None)),
        "max_drawdown_60": _round_metric(_row_value(row, "drawdown_60", None)),
        "downside_vol_60": _round_metric(_row_value(row, "downside_vol_60", None)),
    }


def _industry_quality(row: pd.Series | None, breadth: dict[str, Any], etf: dict[str, Any]) -> dict[str, Any]:
    confidence = float(_row_value(row, "confidence", 0.75))
    breadth_status = breadth.get("quality", {}).get("status", "fresh")
    etf_status = "complete" if etf.get("latest_date") else "partial"
    status = "complete"
    if breadth_status == "stale":
        status = "stale"
    elif confidence < 0.95 or etf_status != "complete":
        status = "partial"
    return {
        "status": status,
        "confidence": round(confidence, 2),
        "price": "complete",
        "breadth": breadth_status,
        "etf": etf_status,
        "message": "价格、宽度、ETF 数据已对齐" if status == "complete" else "存在缺失、滞后或替代口径",
    }


def _methodology_note(industry: IndustryConfig, etf: dict[str, Any]) -> str:
    price = " + ".join(source.name for source in industry.price_sources)
    breadth = " / ".join(industry.breadth_sources)
    return (
        f"价格端：{price}；宽度端：{breadth}；ETF："
        f"{etf.get('name') or industry.etf_rule.fallback_name}，{industry.etf_rule.match_note}"
    )


def _source_quality_reports(
    *,
    histories_day: dict[str, pd.DataFrame],
    breadth: dict[str, Any],
    etfs: dict[str, Any],
    latest_price_date: str,
    latest_etf_date: str,
) -> list[DataQualityReport]:
    breadth_quality = breadth.get("quality", {})
    missing_sources = breadth_quality.get("missing_sources", {})
    breadth_status = str(breadth_quality.get("status", "fresh"))
    breadth_latest = str(breadth.get("latest_date", ""))
    breadth_aligned = not latest_price_date or not breadth_latest or breadth_latest == latest_price_date
    etf_aligned = not latest_price_date or not latest_etf_date or latest_etf_date == latest_price_date
    return [
        DataQualityReport(
            source="sw_index",
            latest_date=latest_price_date,
            expected_latest_date=None,
            is_fresh=True,
            rows=sum(len(frame) for frame in histories_day.values()),
            missing_fields=[],
            missing_industries=[],
            stale_reason=None,
            confidence=0.95,
        ),
        DataQualityReport(
            source="breadth_ma20",
            latest_date=breadth_latest,
            expected_latest_date=latest_price_date,
            is_fresh=breadth_status != "stale" and breadth_aligned,
            rows=len(breadth.get("dates", [])),
            missing_fields=[],
            missing_industries=sorted(missing_sources),
            stale_reason=(
                breadth_quality.get("message")
                if breadth_status == "stale"
                else (
                    f"日期不一致：宽度 {breadth_latest}，价格 {latest_price_date}"
                    if not breadth_aligned
                    else None
                )
            ),
            confidence=0.65 if breadth_status == "stale" else (0.75 if not breadth_aligned else 0.85),
        ),
        DataQualityReport(
            source="etf",
            latest_date=latest_etf_date,
            expected_latest_date=latest_price_date,
            is_fresh=bool(latest_etf_date) and etf_aligned,
            rows=len(etfs.get("items", [])),
            missing_fields=[],
            missing_industries=[item["industry"] for item in etfs.get("items", []) if not item.get("latest_date")],
            stale_reason=(
                None
                if latest_etf_date and etf_aligned
                else (
                    f"日期不一致：ETF {latest_etf_date}，价格 {latest_price_date}"
                    if latest_etf_date
                    else "ETF 历史数据缺失"
                )
            ),
            confidence=0.8 if latest_etf_date and etf_aligned else 0.55,
        ),
    ]


def _alignment_status(price_date: str, breadth_date: str, etf_date: str) -> str:
    dates = [value for value in (price_date, breadth_date, etf_date) if value]
    if not dates:
        return "missing"
    if len(set(dates)) == 1:
        return "aligned"
    if price_date and breadth_date and price_date == breadth_date:
        return "partial_aligned"
    return "date_mismatch"


def _change_log(panel: pd.DataFrame, industries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest_by_name = {item["name"]: item for item in industries}
    changes: list[dict[str, Any]] = []
    for name, item in latest_by_name.items():
        transition = item.get("phase_transition", "unchanged")
        if transition == "unchanged" and abs(float(item.get("score_delta_1d") or 0)) < 1:
            continue
        rows = panel[panel["industry"] == name].sort_values("date")
        previous_phase = rows.iloc[-2]["phase"] if len(rows) >= 2 else None
        changes.append(
            {
                "industry": name,
                "type": "phase_" + str(transition),
                "from": previous_phase,
                "to": item.get("phase"),
                "score_delta": item.get("score_delta_1d"),
                "reason": item.get("change_reason") or ["分数或阶段发生变化"],
            }
        )
    if not changes:
        leaders = sorted(industries, key=lambda item: abs(float(item.get("score_delta_1d") or 0)), reverse=True)[:5]
        changes = [
            {
                "industry": item["name"],
                "type": "score_watch",
                "from": item.get("phase"),
                "to": item.get("phase"),
                "score_delta": item.get("score_delta_1d"),
                "reason": ["阶段未变，跟踪分数边际变化"],
            }
            for item in leaders
        ]
    return changes[:12]


def _factor_history(panel: pd.DataFrame) -> dict[str, dict[str, list[Any]]]:
    history: dict[str, dict[str, list[Any]]] = {}
    for name, group in panel.sort_values("date").groupby("industry"):
        recent = group.tail(120)
        history[name] = {
            "dates": recent["date"].tolist(),
            "score": [_round_metric(value) for value in recent["score"].tolist()],
            "rs": [_round_metric(value) for value in recent["rs_z_120"].tolist()],
            "breadth": [_round_metric(value) for value in recent["breadth_ma20"].tolist()],
        }
    return history


def _round_metric(value: Any, digits: int = 4) -> Any:
    try:
        if value is None or pd.isna(value):
            return None
        if isinstance(value, bool):
            return value
        return round(float(value), digits)
    except (TypeError, ValueError):
        return value


def write_report(path: str | Path, report: dict[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_html(path: str | Path, report: dict[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(report), encoding="utf-8")


def write_panel(path: str | Path, panel: pd.DataFrame) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(output, index=False)


def write_history_report(path: str | Path, report: dict[str, Any]) -> None:
    latest = str(report["meta"].get("latest_report_date") or report["meta"].get("latest_date") or "latest")
    output = Path(path) / f"{latest}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    parser = argparse.ArgumentParser(description="Generate Rollingold report data, panels, backtest, or static HTML.")
    parser.add_argument("--mode", choices=("html", "data", "panel", "backtest"), default="html")
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
        bundle = build_report_bundle(
            config_path=args.config,
            breadth_path=args.breadth_input,
            cache_dir=args.cache_dir,
            offline_fixture=args.offline_fixture,
            refresh_cache=args.refresh_cache,
        )
        report = bundle["report"]
        write_report(args.output, report)
        write_panel(PROJECT_ROOT / "data" / "history" / "signal_panel_daily.csv", bundle["panel_day"])
        write_panel(PROJECT_ROOT / "data" / "history" / "signal_panel_weekly.csv", bundle["panel_week"])
        write_history_report(PROJECT_ROOT / "reports" / "history", report)
        print(f"wrote {args.output} ({len(report['industries'])} industries, latest {report['meta']['latest_date']})")
        return 0

    if args.mode == "panel":
        bundle = build_report_bundle(
            config_path=args.config,
            breadth_path=args.breadth_input,
            cache_dir=args.cache_dir,
            offline_fixture=args.offline_fixture,
            refresh_cache=args.refresh_cache,
        )
        output = args.output if args.output != "docs/index.html" else PROJECT_ROOT / "data" / "history" / "signal_panel_daily.csv"
        write_panel(output, bundle["panel_day"])
        write_panel(PROJECT_ROOT / "data" / "history" / "signal_panel_weekly.csv", bundle["panel_week"])
        print(f"wrote {output} ({len(bundle['panel_day'])} rows)")
        return 0

    if args.mode == "backtest":
        bundle = build_report_bundle(
            config_path=args.config,
            breadth_path=args.breadth_input,
            cache_dir=args.cache_dir,
            offline_fixture=args.offline_fixture,
            refresh_cache=args.refresh_cache,
        )
        output = Path(args.output) if args.output != "docs/index.html" else PROJECT_ROOT / "data" / "history" / "backtest_summary.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(bundle["report"]["strategy_lab"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {output} ({len(bundle['report']['strategy_lab']['results'])} strategy presets)")
        return 0

    if args.data:
        report = json.loads(Path(args.data).read_text(encoding="utf-8"))
    else:
        report = build_report_bundle(
            config_path=args.config,
            breadth_path=args.breadth_input,
            cache_dir=args.cache_dir,
            offline_fixture=args.offline_fixture,
            refresh_cache=args.refresh_cache,
        )["report"]
    write_html(args.output, report)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
