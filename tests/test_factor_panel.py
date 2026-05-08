import pandas as pd

from rollingold.breadth import aggregate_breadth, load_raw_payload
from rollingold.config import load_config
from rollingold.data_sources import amount_series, close_series, equal_weight_series, load_sw_history
from rollingold.factor_panel import build_factor_panel, rolling_zscore


def _fixture_inputs():
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
    return config, page_closes, page_amounts, close_series(histories[config.benchmark_code]), breadth


def test_factor_panel_has_required_columns():
    config, page_closes, page_amounts, benchmark, breadth = _fixture_inputs()

    panel = build_factor_panel(
        config=config,
        page_closes=page_closes,
        page_amounts=page_amounts,
        benchmark_close=benchmark,
        breadth=breadth,
        period="daily",
    )

    assert len(panel["industry"].unique()) == 26
    assert {
        "price_x",
        "momentum_y",
        "breadth_ma20",
        "breadth_delta_5d",
        "amount_share",
        "vol_20",
        "drawdown_60",
        "confidence",
    }.issubset(panel.columns)


def test_factor_panel_no_lookahead_for_rolling_zscore():
    base = pd.Series([1, 2, 3, 4, 5, 6, 7], dtype=float)
    changed_future = base.copy()
    changed_future.iloc[-1] = 1000

    before = rolling_zscore(base, lookback=3)
    after = rolling_zscore(changed_future, lookback=3)

    assert before.iloc[4] == after.iloc[4]
    assert before.iloc[5] == after.iloc[5]
    assert before.iloc[-1] != after.iloc[-1]


def test_factor_panel_has_26_industries_per_date():
    config, page_closes, page_amounts, benchmark, breadth = _fixture_inputs()

    panel = build_factor_panel(
        config=config,
        page_closes=page_closes,
        page_amounts=page_amounts,
        benchmark_close=benchmark,
        breadth=breadth,
        period="daily",
    )
    latest = panel[panel["date"] == panel["date"].max()]

    assert len(latest) == 26


def test_factor_panel_handles_missing_breadth():
    config, page_closes, page_amounts, benchmark, breadth = _fixture_inputs()
    breadth["values"][0][-1] = None

    panel = build_factor_panel(
        config=config,
        page_closes=page_closes,
        page_amounts=page_amounts,
        benchmark_close=benchmark,
        breadth=breadth,
        period="daily",
    )

    row = panel[(panel["industry"] == config.industries[0].name) & (panel["date"] == panel["date"].max())].iloc[0]
    assert row["confidence"] < 1.0
