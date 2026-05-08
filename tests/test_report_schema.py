import json
from pathlib import Path

from rollingold.site import build_report


def test_report_schema_required_keys_are_present():
    schema = json.loads(Path("schemas/report.schema.json").read_text(encoding="utf-8"))
    report = build_report(offline_fixture="tests/fixtures")

    for key in schema["required"]:
        assert key in report
    for key in schema["properties"]["meta"]["required"]:
        assert key in report["meta"]
    for key in schema["properties"]["industry_item"]["required"]:
        assert key in report["industries"][0]

    assert report["change_log"]
    assert report["strategy_lab"]["results"]
