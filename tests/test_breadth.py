from rollingold.breadth import aggregate_breadth, load_raw_payload
from rollingold.config import IndustryConfig, PriceSource, load_config


def test_aggregate_breadth_filters_zero_values():
    industries = (
        IndustryConfig(
            name="测试行业",
            breadth_sources=("A", "B"),
            price_sources=(PriceSource(name="测试", code="000001"),),
        ),
    )
    raw = {
        "dates": ["2026-01-01", "2026-01-02"],
        "industries": ["A", "B"],
        "data": [[0, 0, 0.0], [0, 1, 20.0], [1, 0, 40.0], [1, 1, 60.0]],
    }

    result = aggregate_breadth(raw, industries)

    assert result["values"] == [[20.0, 50.0]]
    assert result["latest_values"]["测试行业"] == 50.0
    assert result["market_average"] == [20.0, 50.0]


def test_fixture_aggregates_to_26_page_industries():
    config = load_config()
    raw = load_raw_payload("tests/fixtures/breadth_raw.json")
    result = aggregate_breadth(raw, config.industries, fill_missing=True)

    assert len(result["industries"]) == 26
    assert result["latest_date"] == "2026-05-06"
    assert all(len(row) == len(result["dates"]) for row in result["values"])

