"""Build industry-date factor panels for scoring and strategy research."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from .config import AppConfig
from .indicators import quadrant


def rolling_zscore(series: pd.Series, lookback: int, *, min_periods: int | None = None) -> pd.Series:
    periods = min_periods if min_periods is not None else max(2, lookback // 2)
    mean = series.rolling(lookback, min_periods=periods).mean()
    std = series.rolling(lookback, min_periods=periods).std(ddof=0)
    return (series - mean) / std.replace(0, pd.NA)


def build_factor_panel(
    *,
    config: AppConfig,
    page_closes: dict[str, pd.Series],
    page_amounts: dict[str, pd.Series],
    benchmark_close: pd.Series,
    breadth: dict[str, Any],
    period: str,
) -> pd.DataFrame:
    amount_frame = pd.concat(page_amounts, axis=1, join="outer").fillna(0).sort_index()
    amount_total = amount_frame.sum(axis=1).replace(0, pd.NA)
    amount_share = amount_frame.div(amount_total, axis=0).fillna(0)
    market_breadth = _breadth_market_series(breadth)
    rows: list[pd.DataFrame] = []

    for industry in config.industries:
        name = industry.name
        close = page_closes[name].sort_index().dropna()
        joined = pd.concat(
            [close.rename("close"), benchmark_close.rename("benchmark")],
            axis=1,
            join="inner",
        ).dropna()
        joined = joined[(joined["close"] > 0) & (joined["benchmark"] > 0)]
        if len(joined) < 8:
            continue
        relative = (joined["close"] / joined["benchmark"]).map(math.log)
        returns = joined["close"].pct_change()
        benchmark_returns = joined["benchmark"].pct_change()
        rs_z_120 = rolling_zscore(relative, 120, min_periods=5)
        rs_mom_20_raw = relative - relative.shift(20)
        rs_mom_60_raw = relative - relative.shift(60)
        rs_mom_20_z = rolling_zscore(rs_mom_20_raw, 120, min_periods=5)
        rs_mom_60_z = rolling_zscore(rs_mom_60_raw, 120, min_periods=5)
        rs_accel = (relative - relative.shift(5)) - (relative - relative.shift(20))
        amount = amount_share[name].reindex(joined.index).fillna(0)
        amount_ma20 = amount.rolling(20, min_periods=5).mean()
        observed_breadth = _breadth_series(breadth, name).reindex(joined.index)
        industry_breadth = observed_breadth.ffill()
        breadth_delta_1d = industry_breadth.diff(1)
        breadth_delta_5d = industry_breadth.diff(5)
        relative_breadth = industry_breadth - market_breadth.reindex(joined.index).ffill()
        frame = pd.DataFrame(
            {
                "date": [str(idx.date() if hasattr(idx, "date") else idx) for idx in joined.index],
                "period": period,
                "industry": name,
                "close": joined["close"],
                "price_x": rs_z_120,
                "momentum_y": rs_mom_20_z,
                "rs_z_120": rs_z_120,
                "rs_mom_20_z": rs_mom_20_z,
                "rs_mom_60_z": rs_mom_60_z,
                "rs_accel_5_20": rs_accel,
                "rs_new_high_60": relative >= relative.rolling(60, min_periods=5).max(),
                "breadth_ma20": industry_breadth,
                "breadth_observed": observed_breadth.notna(),
                "breadth_delta_1d": breadth_delta_1d,
                "breadth_delta_5d": breadth_delta_5d,
                "relative_breadth": relative_breadth,
                "breadth_slope_5": industry_breadth.rolling(5, min_periods=3).apply(_slope, raw=False),
                "breadth_slope_10": industry_breadth.rolling(10, min_periods=3).apply(_slope, raw=False),
                "breadth_above_50": industry_breadth >= 50,
                "breadth_thrust": (industry_breadth.shift(5) < 30) & (industry_breadth >= 50),
                "breadth_persistence": (industry_breadth > market_breadth.reindex(joined.index).ffill())
                .rolling(20, min_periods=5)
                .mean(),
                "amount_share": amount,
                "amount_share_ma20": amount_ma20,
                "amount_confirm": amount > amount_ma20.fillna(amount),
                "amount_share_z_60": rolling_zscore(amount, 60, min_periods=5),
                "amount_mom_5": amount.diff(5),
                "vol_20": returns.rolling(20, min_periods=5).std(ddof=0),
                "vol_60": returns.rolling(60, min_periods=5).std(ddof=0),
                "drawdown_60": joined["close"] / joined["close"].rolling(60, min_periods=5).max() - 1,
                "downside_vol_60": returns.where(returns < 0, 0).rolling(60, min_periods=5).std(ddof=0),
                "correlation_to_benchmark": returns.rolling(60, min_periods=5).corr(benchmark_returns),
                "source": "sw_index/breadth_ma20",
            },
            index=joined.index,
        )
        frame["breadth_divergence_score"] = frame["breadth_ma20"] - 50 - frame["price_x"].fillna(0) * 12
        frame["price_amount_confirm_score"] = frame["rs_mom_20_z"].fillna(0) * frame["amount_share_z_60"].fillna(0)
        frame["trend_stability"] = (
            ((frame["price_x"] >= 0) & (frame["momentum_y"] >= 0)).rolling(20, min_periods=5).mean()
        )
        frame["confidence"] = frame.apply(_confidence, axis=1)
        frame["quadrant"] = [
            quadrant(_num(price, 0.0), _num(mom, 0.0))
            for price, mom in zip(frame["price_x"], frame["momentum_y"])
        ]
        rows.append(frame.reset_index(drop=True))

    if not rows:
        return pd.DataFrame()
    panel = pd.concat(rows, ignore_index=True)
    panel["rs_rank_pct"] = panel.groupby("date")["rs_z_120"].rank(pct=True) * 100
    fill_defaults = {
        "price_x": 0.0,
        "momentum_y": 0.0,
        "rs_z_120": 0.0,
        "rs_mom_20_z": 0.0,
        "rs_mom_60_z": 0.0,
        "rs_accel_5_20": 0.0,
        "rs_rank_pct": 50.0,
        "breadth_delta_1d": 0.0,
        "breadth_delta_5d": 0.0,
        "relative_breadth": 0.0,
        "breadth_slope_5": 0.0,
        "breadth_slope_10": 0.0,
        "breadth_persistence": 0.5,
        "amount_share_ma20": 0.0,
        "amount_share_z_60": 0.0,
        "amount_mom_5": 0.0,
        "vol_20": 0.0,
        "vol_60": 0.0,
        "drawdown_60": 0.0,
        "downside_vol_60": 0.0,
        "correlation_to_benchmark": 0.0,
        "breadth_divergence_score": 0.0,
        "price_amount_confirm_score": 0.0,
        "trend_stability": 0.0,
    }
    return panel.fillna(fill_defaults)


def _breadth_series(breadth: dict[str, Any], industry: str) -> pd.Series:
    dates = pd.to_datetime(breadth.get("dates", []))
    industries = list(breadth.get("industries", []))
    if industry not in industries or len(dates) == 0:
        return pd.Series(dtype=float)
    values = breadth.get("values", [])[industries.index(industry)]
    return pd.Series(values, index=dates, dtype="float64")


def _breadth_market_series(breadth: dict[str, Any]) -> pd.Series:
    dates = pd.to_datetime(breadth.get("dates", []))
    values = breadth.get("market_average", [])
    return pd.Series(values, index=dates, dtype="float64")


def _slope(series: pd.Series) -> float:
    valid = series.dropna()
    if len(valid) < 2:
        return 0.0
    y = valid.to_list()
    n = len(y)
    x_mean = (n - 1) / 2
    y_mean = sum(y) / n
    denom = sum((idx - x_mean) ** 2 for idx in range(n))
    if denom == 0:
        return 0.0
    return float(sum((idx - x_mean) * (value - y_mean) for idx, value in enumerate(y)) / denom)


def _confidence(row: pd.Series) -> float:
    confidence = 1.0
    if pd.isna(row.get("breadth_ma20")) or not bool(row.get("breadth_observed", True)):
        confidence -= 0.2
    if pd.isna(row.get("price_x")) or pd.isna(row.get("momentum_y")):
        confidence -= 0.2
    if pd.isna(row.get("amount_share")):
        confidence -= 0.1
    return round(max(0.45, confidence), 2)


def _num(value: Any, default: float) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default
