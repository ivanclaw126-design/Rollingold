"""Top-N industry rotation backtest for static strategy research."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class StrategyConfig:
    score_preset: str
    top_n: int
    rebalance_days: int
    cost_bps: float
    risk_filter: str | None = None
    max_replacements: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BacktestResult:
    dates: list[str]
    equity_curve: list[float]
    benchmark_curve: list[float]
    drawdown_curve: list[float]
    holdings: list[dict[str, Any]]
    trades: list[dict[str, Any]]
    metrics: dict[str, float]
    config: dict[str, Any]
    disclaimer: str = "历史模拟，不代表未来收益"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_top_n_backtest(
    panel: pd.DataFrame,
    page_closes: dict[str, pd.Series],
    benchmark_close: pd.Series,
    config: StrategyConfig,
) -> BacktestResult:
    panel = panel.copy()
    if "score" not in panel.columns:
        if "rs_rank_pct" in panel.columns:
            panel["score"] = panel["rs_rank_pct"]
        elif "rs_z_120" in panel.columns:
            panel["score"] = (50 + panel["rs_z_120"].fillna(0) * 15).clip(0, 100)
        else:
            panel["score"] = 50.0
    prices = pd.concat(page_closes, axis=1, join="inner").sort_index().dropna(how="all")
    returns = prices.pct_change().fillna(0)
    benchmark = benchmark_close.reindex(prices.index).ffill().pct_change().fillna(0)
    panel_by_date = {
        date: group.sort_values("score", ascending=False)
        for date, group in panel.dropna(subset=["score"]).groupby("date")
    }

    dates = [str(idx.date() if hasattr(idx, "date") else idx) for idx in prices.index]
    current: list[str] = []
    equity = 1.0
    benchmark_equity = 1.0
    equity_curve: list[float] = []
    benchmark_curve: list[float] = []
    drawdown_curve: list[float] = []
    holdings: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []
    peak = 1.0
    daily_returns: list[float] = []
    turnover_values: list[float] = []
    cost_total = 0.0

    for idx, date_text in enumerate(dates):
        if idx > 0 and current:
            ret = float(returns.iloc[idx][current].mean())
        else:
            ret = 0.0
        equity *= 1 + ret
        benchmark_equity *= 1 + float(benchmark.iloc[idx])
        daily_returns.append(ret)

        if idx == 0 or idx % max(1, config.rebalance_days) == 0:
            signal_date = date_text
            execution_date = dates[min(idx + 1, len(dates) - 1)]
            candidates = _select_candidates(panel_by_date.get(signal_date), config)
            next_holdings = _apply_turnover_constraint(current, candidates, config.max_replacements)
            turnover = _turnover(current, next_holdings)
            cost = turnover * config.cost_bps / 10000
            if idx < len(dates) - 1:
                equity *= 1 - cost
            cost_total += cost
            turnover_values.append(turnover)
            if set(next_holdings) != set(current):
                trades.append(
                    {
                        "signal_date": signal_date,
                        "execution_date": execution_date,
                        "from": current,
                        "to": next_holdings,
                        "turnover": round(turnover, 4),
                        "cost": round(cost, 6),
                        "reason": "分数排序、阶段与风险过滤后进入 Top-N",
                    }
                )
            current = next_holdings

        peak = max(peak, equity)
        drawdown = equity / peak - 1 if peak else 0.0
        equity_curve.append(round(equity, 6))
        benchmark_curve.append(round(benchmark_equity, 6))
        drawdown_curve.append(round(drawdown, 6))
        holdings.append({"date": date_text, "industries": current})

    metrics = _metrics(equity_curve, benchmark_curve, daily_returns, turnover_values, cost_total)
    return BacktestResult(
        dates=dates,
        equity_curve=equity_curve,
        benchmark_curve=benchmark_curve,
        drawdown_curve=drawdown_curve,
        holdings=holdings,
        trades=trades,
        metrics=metrics,
        config=config.to_dict(),
    )


def _select_candidates(frame: pd.DataFrame | None, config: StrategyConfig) -> list[str]:
    if frame is None or frame.empty:
        return []
    candidates = frame.copy()
    if config.risk_filter == "exclude_high_vol" and "vol_20" in candidates:
        threshold = candidates["vol_20"].quantile(0.8)
        candidates = candidates[candidates["vol_20"] <= threshold]
    if config.risk_filter == "exclude_deep_drawdown" and "drawdown_60" in candidates:
        candidates = candidates[candidates["drawdown_60"] > -0.15]
    return candidates.sort_values("score", ascending=False)["industry"].head(config.top_n).tolist()


def _apply_turnover_constraint(current: list[str], target: list[str], max_replacements: int | None) -> list[str]:
    if not current or max_replacements is None:
        return target
    kept = [name for name in current if name in target]
    additions = [name for name in target if name not in kept]
    allowed = additions[: max(0, max_replacements)]
    result = (kept + allowed)[: len(target)]
    if len(result) < len(target):
        for name in current:
            if name not in result:
                result.append(name)
            if len(result) == len(target):
                break
    return result


def _turnover(current: list[str], target: list[str]) -> float:
    if not current and not target:
        return 0.0
    if not current or not target:
        return 1.0
    changed = len(set(current) ^ set(target))
    return min(1.0, changed / max(len(current), len(target), 1))


def _metrics(
    equity_curve: list[float],
    benchmark_curve: list[float],
    daily_returns: list[float],
    turnovers: list[float],
    cost_total: float,
) -> dict[str, float]:
    if not equity_curve:
        return {}
    total_return = equity_curve[-1] - 1
    benchmark_return = benchmark_curve[-1] - 1 if benchmark_curve else 0
    periods = max(1, len(equity_curve))
    annual_return = (equity_curve[-1] ** (252 / periods) - 1) if equity_curve[-1] > 0 else -1
    returns = pd.Series(daily_returns)
    annual_vol = float(returns.std(ddof=0) * (252**0.5))
    max_drawdown = min((value / max(equity_curve[: idx + 1]) - 1) for idx, value in enumerate(equity_curve))
    win_rate = float((returns > 0).mean()) if len(returns) else 0.0
    active_returns = returns - returns.mean()
    info_like = float((total_return - benchmark_return) / annual_vol) if annual_vol else 0.0
    return {
        "annual_return": round(float(annual_return), 4),
        "annual_volatility": round(annual_vol, 4),
        "sharpe_like_ratio": round(float(annual_return / annual_vol), 4) if annual_vol else 0.0,
        "max_drawdown": round(float(max_drawdown), 4),
        "calmar_like_ratio": round(float(annual_return / abs(max_drawdown)), 4) if max_drawdown else 0.0,
        "win_rate_daily": round(win_rate, 4),
        "win_rate_rebalance": round(win_rate, 4),
        "turnover_average": round(float(sum(turnovers) / len(turnovers)), 4) if turnovers else 0.0,
        "turnover_total": round(float(sum(turnovers)), 4),
        "active_return_vs_benchmark": round(float(total_return - benchmark_return), 4),
        "information_ratio_like": round(info_like, 4),
        "cost_total": round(float(cost_total), 6),
        "active_return_std_like": round(float(active_returns.std(ddof=0)), 4) if len(active_returns) else 0.0,
    }
