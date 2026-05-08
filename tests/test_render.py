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
    assert "ETF 业绩" in html
    assert "行业 ETF 归一化业绩" in html
    assert "今日变化" in html
    assert "分数贡献" in html
    assert "数据质量" in html
    assert "口径说明" in html
    assert "复制当前视图链接" in html
    assert "恢复默认" in html
    assert "下载因子 CSV" in html
    assert "复制行业详情摘要" in html
    assert "行业对比" not in html
    assert "compare-controls" not in html
    assert "策略实验室" in html
    assert "历史模拟，不代表未来收益" in html
    assert len(report["etfs"]["items"]) == 26
    assert "仅供研究参考，不构成投资建议" in html
    assert "etf-line-hit" in html
    assert "etf-end-label" in html
    assert "pointerenter" in html
    assert report["meta"]["latest_date"] >= "2026-05-06"


def test_interactive_industry_items_are_keyboard_accessible(tmp_path):
    report = build_report(offline_fixture="tests/fixtures")
    output = tmp_path / "index.html"
    write_html(output, report)
    html = output.read_text(encoding="utf-8")

    # Regression: ISSUE-001 — clickable industry items were not keyboard reachable.
    # Found by /qa on 2026-05-08
    # Report: .gstack/qa-reports/qa-report-local-file-2026-05-08.md
    assert 'class="rank-item" data-name="${name}"' in html
    assert 'class="signal-item" data-name="${item.name}"' in html
    assert 'class="industry-dot" data-name="${item.name}"' in html
    assert 'type="button" aria-label="选择${name}"' in html
    assert 'role="button" tabindex="0"' in html
    assert "data-focus-key" in html
    assert "node.addEventListener('focus', pick)" in html
    assert "restoreFocus(focusKey)" in html
    assert "onIndustryKey(event, node.dataset.name, node.dataset.focusKey)" in html


def test_rotation_hover_trace_respects_selected_window(tmp_path):
    report = build_report(offline_fixture="tests/fixtures")
    output = tmp_path / "index.html"
    write_html(output, report)
    html = output.read_text(encoding="utf-8")

    assert "const focusPathPoints = displayPath(focusPoint.path);" in html
    assert "Boolean(hovered)" not in html
    assert "forceFull" not in html
