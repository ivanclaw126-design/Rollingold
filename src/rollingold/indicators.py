"""Indicator calculations for the industry rotation report."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from .scoring import legacy_score_industry


@dataclass(frozen=True)
class RotationSnapshot:
    date: str
    price_x: float
    momentum_y: float
    quadrant: str
    path: list[dict[str, float | str]]


def zscore(series: pd.Series, lookback: int = 120) -> pd.Series:
    window = series.tail(lookback)
    mean = window.mean()
    std = window.std(ddof=0)
    if not math.isfinite(std) or std == 0:
        return pd.Series([0.0] * len(series), index=series.index)
    return (series - mean) / std


def quadrant(price_x: float, momentum_y: float) -> str:
    if price_x >= 0 and momentum_y >= 0:
        return "领涨"
    if price_x >= 0 and momentum_y < 0:
        return "走弱"
    if price_x < 0 and momentum_y < 0:
        return "领跌"
    return "走强"


def rotation_snapshot(
    industry_close: pd.Series,
    benchmark_close: pd.Series,
    *,
    momentum_window: int,
    lookback: int = 120,
    path_points: int = 20,
) -> RotationSnapshot:
    joined = pd.concat(
        [industry_close.rename("industry"), benchmark_close.rename("benchmark")],
        axis=1,
        join="inner",
    ).dropna()
    joined = joined[(joined["industry"] > 0) & (joined["benchmark"] > 0)]
    if len(joined) < momentum_window + 3:
        raise ValueError("not enough price history to compute rotation")

    relative_log = (joined["industry"] / joined["benchmark"]).map(math.log)
    price_series = zscore(relative_log, lookback=lookback)
    momentum_series = zscore(relative_log - relative_log.shift(momentum_window), lookback=lookback)
    frame = pd.concat(
        [price_series.rename("price_x"), momentum_series.rename("momentum_y")],
        axis=1,
    ).dropna()
    if frame.empty:
        raise ValueError("rotation frame is empty after momentum calculation")

    latest = frame.iloc[-1]
    path_frame = frame.tail(path_points)
    path = [
        {
            "date": str(idx.date() if hasattr(idx, "date") else idx),
            "x": round(float(row.price_x), 3),
            "y": round(float(row.momentum_y), 3),
        }
        for idx, row in path_frame.iterrows()
    ]
    return RotationSnapshot(
        date=str(frame.index[-1].date() if hasattr(frame.index[-1], "date") else frame.index[-1]),
        price_x=round(float(latest.price_x), 3),
        momentum_y=round(float(latest.momentum_y), 3),
        quadrant=quadrant(float(latest.price_x), float(latest.momentum_y)),
        path=path,
    )


def score_industry(
    *,
    price_x: float,
    momentum_y: float,
    breadth_ma20: float | None,
    breadth_delta_5d: float | None,
    amount_confirm: bool,
) -> float:
    return legacy_score_industry(
        price_x=price_x,
        momentum_y=momentum_y,
        breadth_ma20=breadth_ma20,
        breadth_delta_5d=breadth_delta_5d,
        amount_confirm=amount_confirm,
    )


def status_label(
    *,
    quadrant_value: str,
    momentum_y: float,
    breadth_ma20: float | None,
    market_breadth_avg: float | None,
    breadth_delta_5d: float | None,
    amount_confirm: bool,
) -> str:
    breadth_above_market = (
        breadth_ma20 is not None and market_breadth_avg is not None and breadth_ma20 > market_breadth_avg
    )
    breadth_improving = breadth_delta_5d is not None and breadth_delta_5d > 0
    breadth_falling = breadth_delta_5d is not None and breadth_delta_5d < 0
    if quadrant_value == "领涨" and breadth_above_market and breadth_improving and amount_confirm:
        return "强趋势共振"
    if quadrant_value in {"领涨", "走弱"} and (breadth_falling or momentum_y < 0):
        return "强势放缓"
    if quadrant_value == "走强" and breadth_improving:
        return "弱势修复"
    if quadrant_value == "领跌" and not breadth_above_market and momentum_y < 0:
        return "弱势衰减"
    return "观察"


def divergence_notes(
    *,
    price_x: float,
    momentum_y: float,
    breadth_ma20: float | None,
    market_breadth_avg: float | None,
    breadth_delta_5d: float | None,
    amount_confirm: bool,
) -> list[str]:
    notes: list[str] = []
    breadth_above_market = (
        breadth_ma20 is not None and market_breadth_avg is not None and breadth_ma20 >= market_breadth_avg
    )
    breadth_improving = breadth_delta_5d is not None and breadth_delta_5d > 0
    if price_x > 0 and not breadth_above_market:
        notes.append("价格强、宽度弱")
    if price_x < 0 and breadth_improving:
        notes.append("价格弱、宽度改善")
    if price_x > 0 and not amount_confirm:
        notes.append("价格强、成交弱")
    if breadth_above_market and momentum_y < 0:
        notes.append("宽度高、动量弱")
    return notes or ["无明显背离"]


def trace_comment(industry: dict[str, object]) -> str:
    quadrant_value = str(industry["quadrant"])
    score = industry["score"]
    breadth = industry.get("breadth_ma20")
    delta = industry.get("breadth_delta_5d")
    return f"{quadrant_value}象限，综合评分 {score}，MA20 宽度 {breadth if breadth is not None else '无数据'}，5 日变化 {delta if delta is not None else '无数据'}。"


def _z_to_score(value: float) -> float:
    return _clamp(50 + value * 15, 0, 100)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))
