import json

from rollingold.breadth import BreadthDataError, fetch_and_aggregate
from rollingold.data_contracts import DataQualityReport, summarize_quality
from rollingold.site import build_report


def test_report_contains_structured_data_quality():
    report = build_report(offline_fixture="tests/fixtures")

    quality = report["meta"]["data_quality"]
    assert quality["status"] in {"complete", "partial", "stale", "date_mismatch"}
    assert "sources" in quality
    assert all("data_quality" in industry for industry in report["industries"])


def test_breadth_fallback_exposes_stale_status(tmp_path, monkeypatch):
    fallback_path = tmp_path / "breadth_history.json"
    fallback_path.write_text(
        json.dumps(
            {
                "dates": ["2026-01-01"],
                "industries": ["测试行业"],
                "values": [[50.0]],
                "latest_date": "2026-01-01",
                "quality": {"status": "fresh", "message": "old"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    def fail_fetch(timeout=20):
        raise BreadthDataError("offline")

    monkeypatch.setattr("rollingold.breadth.fetch_breadth_raw", fail_fetch)
    result = fetch_and_aggregate(fallback_path=fallback_path)

    assert result["quality"]["status"] == "stale"
    assert "沿用上一版" in result["quality"]["message"]


def test_quality_summary_surfaces_date_mismatch():
    quality = summarize_quality(
        [
            DataQualityReport("sw_index", "2026-05-08", None, True, 10, [], [], None, 0.95),
            DataQualityReport(
                "breadth_ma20",
                "2026-05-07",
                "2026-05-08",
                False,
                10,
                [],
                [],
                "日期不一致：宽度 2026-05-07，价格 2026-05-08",
                0.75,
            ),
        ]
    )

    assert quality["status"] == "date_mismatch"
    assert quality["summary"] == "日期不一致"
