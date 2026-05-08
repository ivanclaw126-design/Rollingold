import pytest

from rollingold.scoring import calculate_score, load_scoring_presets


def test_scoring_config_weights_sum_to_one_or_normalize():
    presets = load_scoring_presets("config/scoring.default.yaml")

    assert "default_v1" in presets
    assert "balanced_v2" in presets
    assert pytest.approx(sum(presets["default_v1"].weights.values()), abs=0.001) == 1.0
    assert pytest.approx(sum(presets["balanced_v2"].weights.values()), abs=0.001) == 1.0


def test_default_v1_score_matches_previous_formula():
    row = {
        "price_x": 1.0,
        "momentum_y": 0.5,
        "breadth_ma20": 70.0,
        "breadth_delta_5d": 8.0,
        "amount_confirm": True,
        "confidence": 1.0,
    }

    result = calculate_score(row, load_scoring_presets("config/scoring.default.yaml")["default_v1"])

    assert result.score == pytest.approx(67.8, abs=0.1)
    assert result.breakdown["total"] == pytest.approx(result.score, abs=0.1)
    assert result.top_contributors


def test_balanced_score_breakdown_total_matches_score():
    row = {
        "rs_z_120": 0.8,
        "rs_rank_pct": 78.0,
        "rs_mom_20_z": 1.2,
        "rs_accel_5_20": 0.4,
        "breadth_ma20": 68.0,
        "breadth_slope_5": 4.0,
        "breadth_persistence": 0.7,
        "amount_share_z_60": 0.6,
        "amount_mom_5": 0.01,
        "vol_20": 0.02,
        "drawdown_60": -0.08,
        "confidence": 0.86,
    }

    result = calculate_score(row, load_scoring_presets("config/scoring.default.yaml")["balanced_v2"])

    assert 0 <= result.score <= 100
    assert result.breakdown["total"] == pytest.approx(result.score, abs=0.1)
    assert "risk" in result.breakdown
