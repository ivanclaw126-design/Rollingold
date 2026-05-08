from rollingold.backtest import StrategyConfig, run_top_n_backtest
from rollingold.breadth import aggregate_breadth, load_raw_payload
from rollingold.config import load_config
from rollingold.data_sources import amount_series, close_series, equal_weight_series, load_sw_history
from rollingold.factor_panel import build_factor_panel


def _panel_and_returns():
    config = load_config()
    histories = {
        code: load_sw_history(code, period="day", offline_fixture="tests/fixtures")
        for code in [config.benchmark_code] + config.all_price_codes
    }
    page_closes = {}
    page_amounts = {}
    for industry in config.industries:
        page_closes[industry.name] = equal_weight_series(
            [close_series(histories[source.code]) for source in industry.price_sources]
        )
        page_amounts[industry.name] = sum(
            amount_series(histories[source.code]) for source in industry.price_sources
        )
    breadth = aggregate_breadth(load_raw_payload("tests/fixtures/breadth_raw.json"), config.industries, fill_missing=True)
    panel = build_factor_panel(
        config=config,
        page_closes=page_closes,
        page_amounts=page_amounts,
        benchmark_close=close_series(histories[config.benchmark_code]),
        breadth=breadth,
        period="daily",
    )
    return panel, page_closes, close_series(histories[config.benchmark_code])


def test_backtest_supports_costs_and_no_lookahead():
    panel, page_closes, benchmark = _panel_and_returns()
    config = StrategyConfig(
        score_preset="balanced_v2",
        top_n=5,
        rebalance_days=5,
        cost_bps=10,
        risk_filter="none",
        max_replacements=None,
    )

    result = run_top_n_backtest(panel, page_closes, benchmark, config)

    assert result.metrics["turnover_total"] >= 0
    assert result.metrics["cost_total"] >= 0
    assert len(result.equity_curve) == len(result.benchmark_curve)
    assert all(trade["execution_date"] > trade["signal_date"] for trade in result.trades)
    assert "历史模拟，不代表未来收益" in result.disclaimer
