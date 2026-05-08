import pandas as pd

from rollingold.indicators import (
    divergence_notes,
    quadrant,
    rotation_snapshot,
    score_industry,
    status_label,
    trace_comment,
)


def test_quadrant_mapping():
    assert quadrant(1, 1) == "领涨"
    assert quadrant(1, -1) == "走弱"
    assert quadrant(-1, -1) == "领跌"
    assert quadrant(-1, 1) == "走强"


def test_rotation_snapshot_computes_path_and_quadrant():
    dates = pd.date_range("2026-01-01", periods=35, freq="D")
    industry = pd.Series([100 + idx * 2 for idx in range(35)], index=dates)
    benchmark = pd.Series([100 + idx for idx in range(35)], index=dates)

    result = rotation_snapshot(industry, benchmark, momentum_window=5, path_points=10)

    assert result.quadrant in {"领涨", "走强", "走弱", "领跌"}
    assert len(result.path) == 10
    assert result.price_x > 0


def test_score_status_and_divergence_rules():
    score = score_industry(
        price_x=1.0,
        momentum_y=0.5,
        breadth_ma20=70,
        breadth_delta_5d=8,
        amount_confirm=True,
    )
    assert score > 60
    assert (
        status_label(
            quadrant_value="领涨",
            momentum_y=0.5,
            breadth_ma20=70,
            market_breadth_avg=50,
            breadth_delta_5d=8,
            amount_confirm=True,
        )
        == "强趋势共振"
    )
    assert "价格强、宽度弱" in divergence_notes(
        price_x=1.0,
        momentum_y=0.2,
        breadth_ma20=30,
        market_breadth_avg=50,
        breadth_delta_5d=-2,
        amount_confirm=True,
    )


def test_trace_comment_formats_float_metrics_to_one_decimal():
    assert (
        trace_comment(
            {
                "quadrant": "走强",
                "score": 51.1,
                "breadth_ma20": 79.8,
                "breadth_delta_5d": 39.099999999999994,
            }
        )
        == "走强象限，综合评分 51.1，MA20 宽度 79.8，5 日变化 39.1。"
    )
