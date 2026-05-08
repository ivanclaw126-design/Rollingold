"""Industry rotation phase classification."""

from __future__ import annotations

from typing import Any


PHASE_ORDER = {
    "弱势下行": 0,
    "低位修复": 1,
    "价格确认": 2,
    "趋势扩散": 3,
    "高位背离": 2,
    "动能衰退": 1,
}


def classify_phase(row: dict[str, Any]) -> str:
    price_x = _num(row.get("price_x"), 0.0)
    momentum_y = _num(row.get("momentum_y"), 0.0)
    breadth_delta_5d = _num(row.get("breadth_delta_5d"), 0.0)
    breadth_ma20 = row.get("breadth_ma20")
    relative_breadth = _num(row.get("relative_breadth"), 0.0)
    persistence = _num(row.get("breadth_persistence"), 0.0)
    breadth_value = _num(breadth_ma20, 50.0)
    breadth_above_market = relative_breadth > 0

    if price_x < 0 and momentum_y < 0 and (breadth_value < 50 or relative_breadth < 0):
        return "弱势下行"
    if price_x < 0 and momentum_y > 0 and breadth_delta_5d > 0:
        return "低位修复"
    if price_x >= 0 and momentum_y > 0 and breadth_above_market and persistence >= 0.55:
        return "趋势扩散"
    if price_x >= 0 and momentum_y > 0:
        return "价格确认"
    if price_x > 0 and momentum_y < 0:
        return "动能衰退"
    if price_x > 0 and (breadth_delta_5d < 0 or not breadth_above_market):
        return "高位背离"
    return "观察"


def detect_phase_transition(prev: str | None, current: str | None) -> str:
    if not prev or not current:
        return "new"
    if prev == current:
        return "unchanged"
    previous_rank = PHASE_ORDER.get(prev, 1)
    current_rank = PHASE_ORDER.get(current, 1)
    if current_rank > previous_rank:
        return "upgrade"
    if current_rank < previous_rank:
        return "downgrade"
    return "rotate"


def transition_reason(row: dict[str, Any], transition: str) -> list[str]:
    reasons: list[str] = []
    if transition in {"upgrade", "new"}:
        if _num(row.get("momentum_y"), 0.0) > 0:
            reasons.append("相对动量上升")
        if _num(row.get("relative_breadth"), 0.0) > 0:
            reasons.append("MA20 宽度高于市场均值")
        if bool(row.get("amount_confirm")):
            reasons.append("成交占比高于 20 日均值")
    elif transition == "downgrade":
        if _num(row.get("momentum_y"), 0.0) < 0:
            reasons.append("相对动量转弱")
        if _num(row.get("breadth_delta_5d"), 0.0) < 0:
            reasons.append("MA20 宽度 5 日回落")
        if _num(row.get("drawdown_60"), 0.0) < -0.1:
            reasons.append("近 60 日回撤扩大")
    if not reasons:
        reasons.append("阶段规则重新归类")
    return reasons


def _num(value: Any, default: float) -> float:
    try:
        if value is None:
            return default
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if number == number else default
