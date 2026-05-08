from pathlib import Path

from rollingold.site import build_report, write_html


def test_offline_site_generation_contains_required_sections(tmp_path):
    report = build_report(offline_fixture="tests/fixtures")
    output = tmp_path / "index.html"
    write_html(output, report)
    html = output.read_text(encoding="utf-8")

    assert len(report["industries"]) == 26
    assert output.stat().st_size > 20_000
    assert "价格相对轮动" in html
    assert "市场宽度" in html
    assert "综合评分" in html
    assert "行业详情" in html
    assert "仅供研究参考，不构成投资建议" in html
    assert report["meta"]["latest_date"] >= "2026-05-06"

