"""Config-driven score calculation and explanation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .config import PROJECT_ROOT


DEFAULT_SCORING_PATH = PROJECT_ROOT / "config" / "scoring.default.yaml"


@dataclass(frozen=True)
class ScorePreset:
    name: str
    weights: dict[str, float]
    categories: dict[str, str]


@dataclass(frozen=True)
class ScoringResult:
    score: float
    breakdown: dict[str, float]
    top_contributors: list[str]
    risk_notes: list[str]


def load_scoring_presets(path: str | Path = DEFAULT_SCORING_PATH) -> dict[str, ScorePreset]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    presets: dict[str, ScorePreset] = {}
    for name, body in raw.get("score_presets", {}).items():
        weights: dict[str, float] = {}
        categories: dict[str, str] = {}
        for key, value in body.items():
            if isinstance(value, dict):
                category = str(key)
                for factor, weight in value.items():
                    weights[str(factor)] = float(weight)
                    categories[str(factor)] = category
            else:
                factor = str(key)
                weights[factor] = float(value)
                categories[factor] = _default_category(factor)
        total = sum(weights.values())
        if total <= 0:
            raise ValueError(f"score preset {name} has no positive weights")
        normalized = {factor: weight / total for factor, weight in weights.items()}
        presets[str(name)] = ScorePreset(name=str(name), weights=normalized, categories=categories)
    return presets


def calculate_score(row: dict[str, Any], preset: ScorePreset) -> ScoringResult:
    breakdown: dict[str, float] = {}
    for factor, weight in preset.weights.items():
        category = preset.categories.get(factor, _default_category(factor))
        breakdown[category] = breakdown.get(category, 0.0) + _factor_score(factor, row) * weight
    raw_total = sum(breakdown.values())
    score = round(_clamp(raw_total, 0, 100), 1)
    rounded = {key: round(value, 1) for key, value in breakdown.items()}
    rounded["total"] = score
    top = [
        key
        for key, _ in sorted(
            ((key, value) for key, value in rounded.items() if key != "total" and value > 0),
            key=lambda item: item[1],
            reverse=True,
        )[:3]
    ]
    risks = _risk_notes(row)
    return ScoringResult(score=score, breakdown=rounded, top_contributors=top, risk_notes=risks)


def legacy_score_industry(
    *,
    price_x: float,
    momentum_y: float,
    breadth_ma20: float | None,
    breadth_delta_5d: float | None,
    amount_confirm: bool,
) -> float:
    preset = load_scoring_presets()["default_v1"]
    result = calculate_score(
        {
            "price_x": price_x,
            "momentum_y": momentum_y,
            "breadth_ma20": breadth_ma20,
            "breadth_delta_5d": breadth_delta_5d,
            "amount_confirm": amount_confirm,
            "confidence": 1.0,
        },
        preset,
    )
    return result.score


def explain_industry_signal(item: dict[str, Any]) -> str:
    phase = item.get("phase") or item.get("status") or "观察"
    score = item.get("score")
    contributors = item.get("top_contributors") or []
    risks = item.get("risk_notes") or []
    etf = item.get("etf") or {}
    etf_consistency = etf.get("consistency") or "-"
    parts = [
        f"{item.get('name')}处于「{phase}」阶段，综合评分 {score}。",
        f"主要贡献来自{'、'.join(contributors) if contributors else '价格、宽度与成交信号'}。",
    ]
    if risks:
        parts.append(f"主要风险为{'、'.join(risks)}。")
    else:
        parts.append("风险项未显示显著异常。")
    parts.append(f"ETF 替代口径走势一致性为「{etf_consistency}」，仅供研究参考。")
    return "".join(parts)


def _factor_score(factor: str, row: dict[str, Any]) -> float:
    if factor == "price_relative_strength":
        return _z_to_score(_num(row.get("price_x"), 0.0))
    if factor == "relative_momentum":
        return _z_to_score(_num(row.get("momentum_y"), 0.0))
    if factor == "ma20_breadth":
        return _clamp(_num(row.get("breadth_ma20"), 50.0), 0, 100)
    if factor == "breadth_delta_5d":
        return _clamp(50 + _num(row.get("breadth_delta_5d"), 0.0) * 2, 0, 100)
    if factor == "amount_confirm":
        return 100.0 if bool(row.get("amount_confirm")) else 40.0
    if factor in {"rs_z_120", "rs_mom_20_z", "rs_mom_60_z", "rs_accel_5_20", "amount_share_z_60"}:
        return _z_to_score(_num(row.get(factor), 0.0))
    if factor == "rs_rank_pct":
        return _clamp(_num(row.get(factor), 50.0), 0, 100)
    if factor == "breadth_ma20":
        return _clamp(_num(row.get(factor), 50.0), 0, 100)
    if factor in {"breadth_slope_5", "breadth_slope_10"}:
        return _clamp(50 + _num(row.get(factor), 0.0) * 3, 0, 100)
    if factor == "breadth_persistence":
        return _clamp(_num(row.get(factor), 0.5) * 100, 0, 100)
    if factor == "amount_mom_5":
        return _clamp(50 + _num(row.get(factor), 0.0) * 800, 0, 100)
    if factor == "vol_penalty":
        return -_clamp(_num(row.get("vol_20"), 0.0) * 1200, 0, 100)
    if factor == "drawdown_penalty":
        return -_clamp(abs(min(_num(row.get("drawdown_60"), 0.0), 0.0)) * 300, 0, 100)
    if factor == "confidence":
        return _clamp(_num(row.get("confidence"), 0.75) * 100, 0, 100)
    return _num(row.get(factor), 50.0)


def _risk_notes(row: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    vol = _num(row.get("vol_20"), 0.0)
    drawdown = _num(row.get("drawdown_60"), 0.0)
    if vol >= 0.025:
        notes.append("近20日波动率偏高")
    if drawdown <= -0.12:
        notes.append("近60日回撤偏深")
    if _num(row.get("breadth_divergence_score"), 0.0) < -20:
        notes.append("价格与宽度存在背离")
    return notes


def _default_category(factor: str) -> str:
    if factor in {"price_relative_strength", "rs_z_120", "rs_rank_pct"}:
        return "trend"
    if factor in {"relative_momentum", "rs_mom_20_z", "rs_mom_60_z", "rs_accel_5_20"}:
        return "momentum"
    if "breadth" in factor:
        return "breadth"
    if "amount" in factor or "liquidity" in factor:
        return "liquidity"
    if "risk" in factor or "penalty" in factor or "drawdown" in factor or "vol" in factor:
        return "risk"
    if factor == "confidence":
        return "data_quality"
    return "other"


def _z_to_score(value: float) -> float:
    return _clamp(50 + value * 15, 0, 100)


def _num(value: Any, default: float) -> float:
    try:
        if value is None:
            return default
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if number == number else default


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))
