from rollingold.phase import classify_phase, detect_phase_transition


def test_phase_classification_rules():
    assert classify_phase(
        {
            "price_x": -0.6,
            "momentum_y": 0.8,
            "breadth_delta_5d": 6,
            "breadth_ma20": 42,
            "relative_breadth": -3,
            "breadth_persistence": 0.3,
        }
    ) == "低位修复"
    assert classify_phase(
        {
            "price_x": 0.7,
            "momentum_y": 0.8,
            "breadth_delta_5d": 4,
            "breadth_ma20": 75,
            "relative_breadth": 10,
            "breadth_persistence": 0.8,
        }
    ) == "趋势扩散"
    assert classify_phase(
        {
            "price_x": 0.7,
            "momentum_y": -0.2,
            "breadth_delta_5d": -4,
            "breadth_ma20": 60,
            "relative_breadth": 2,
            "breadth_persistence": 0.4,
        }
    ) == "动能衰退"


def test_phase_transition_detection():
    assert detect_phase_transition("价格确认", "趋势扩散") == "upgrade"
    assert detect_phase_transition("趋势扩散", "动能衰退") == "downgrade"
    assert detect_phase_transition("低位修复", "低位修复") == "unchanged"
