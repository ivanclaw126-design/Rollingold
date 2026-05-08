"""Data source quality contracts for report generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class DataQualityReport:
    source: str
    latest_date: str
    expected_latest_date: str | None
    is_fresh: bool
    rows: int
    missing_fields: list[str]
    missing_industries: list[str]
    stale_reason: str | None
    confidence: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def summarize_quality(reports: list[DataQualityReport]) -> dict[str, object]:
    if not reports:
        return {"status": "partial", "summary": "无数据质量报告", "sources": [], "confidence": 0.0}
    if any((report.stale_reason or "").startswith("日期不一致") for report in reports):
        status = "date_mismatch"
    elif any(not report.is_fresh for report in reports):
        status = "stale"
    elif any(report.missing_fields or report.missing_industries for report in reports):
        status = "partial"
    else:
        status = "complete"
    confidence = round(sum(report.confidence for report in reports) / len(reports), 3)
    labels = {"complete": "完整", "partial": "部分缺失", "stale": "沿用旧数据", "date_mismatch": "日期不一致"}
    return {
        "status": status,
        "summary": labels[status],
        "confidence": confidence,
        "sources": [report.to_dict() for report in reports],
    }
