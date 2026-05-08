"""Strategy lab presets and sensitivity helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .backtest import StrategyConfig, run_top_n_backtest
from .config import PROJECT_ROOT


DEFAULT_STRATEGY_PATH = PROJECT_ROOT / "config" / "strategy_presets.yaml"


def load_strategy_presets(path: str | Path = DEFAULT_STRATEGY_PATH) -> list[StrategyConfig]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    configs: list[StrategyConfig] = []
    for body in raw.get("strategy_presets", {}).values():
        configs.append(
            StrategyConfig(
                score_preset=str(body.get("score_preset", "balanced_v2")),
                top_n=int(body.get("top_n", 5)),
                rebalance_days=int(body.get("rebalance_days", 5)),
                cost_bps=float(body.get("cost_bps", 10)),
                risk_filter=None if body.get("risk_filter") in (None, "none") else str(body.get("risk_filter")),
                max_replacements=(
                    None if body.get("max_replacements") in (None, "") else int(body.get("max_replacements"))
                ),
            )
        )
    return configs


def build_strategy_lab(
    panel: pd.DataFrame,
    page_closes: dict[str, pd.Series],
    benchmark_close: pd.Series,
    presets: list[StrategyConfig] | None = None,
) -> dict[str, Any]:
    configs = presets or load_strategy_presets()
    results = [
        run_top_n_backtest(panel, page_closes, benchmark_close, config).to_dict()
        for config in configs
    ]
    latest = panel[panel["date"] == panel["date"].max()].sort_values("score", ascending=False)
    candidates = latest.head(8)[
        ["industry", "score", "phase", "vol_20", "drawdown_60", "phase_transition"]
    ].to_dict(orient="records")
    sensitivity = [
        {
            "top_n": result["config"]["top_n"],
            "rebalance_days": result["config"]["rebalance_days"],
            "annual_return": result["metrics"].get("annual_return"),
            "max_drawdown": result["metrics"].get("max_drawdown"),
            "turnover_average": result["metrics"].get("turnover_average"),
            "current_overlap": len(set(result["holdings"][-1]["industries"]) & set(latest.head(8)["industry"]))
            if result["holdings"]
            else 0,
        }
        for result in results
    ]
    return {
        "presets": [config.to_dict() for config in configs],
        "results": results,
        "current_candidates": candidates,
        "sensitivity": sensitivity,
        "disclaimer": "研究参考，不构成投资建议；历史模拟，不代表未来收益",
    }
