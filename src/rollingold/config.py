"""Project configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "industry_mapping.yaml"


@dataclass(frozen=True)
class PriceSource:
    name: str
    code: str


@dataclass(frozen=True)
class EtfRule:
    include_any: tuple[str, ...]
    fallback_code: str
    fallback_name: str
    match_note: str
    exclude_any: tuple[str, ...] = ()


@dataclass(frozen=True)
class IndustryConfig:
    name: str
    breadth_sources: tuple[str, ...]
    price_sources: tuple[PriceSource, ...]
    etf_rule: EtfRule = EtfRule((), "", "", "")
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class AppConfig:
    benchmark_name: str
    benchmark_code: str
    industries: tuple[IndustryConfig, ...]

    @property
    def industry_names(self) -> list[str]:
        return [industry.name for industry in self.industries]

    @property
    def all_price_codes(self) -> list[str]:
        seen: set[str] = {self.benchmark_code}
        codes: list[str] = []
        for industry in self.industries:
            for source in industry.price_sources:
                if source.code not in seen:
                    seen.add(source.code)
                    codes.append(source.code)
        return codes


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    """Load the industry mapping YAML into typed config objects."""

    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    benchmark = raw["benchmark"]
    industries = tuple(_parse_industry(item) for item in raw["industries"])
    return AppConfig(
        benchmark_name=str(benchmark["name"]),
        benchmark_code=str(benchmark["code"]),
        industries=industries,
    )


def _parse_industry(raw: dict[str, Any]) -> IndustryConfig:
    etf = raw.get("etf", {})
    return IndustryConfig(
        name=str(raw["name"]),
        aliases=tuple(str(item) for item in raw.get("aliases", ())),
        breadth_sources=tuple(str(item) for item in raw.get("breadth_sources", ())),
        price_sources=tuple(
            PriceSource(name=str(item["name"]), code=str(item["code"]))
            for item in raw.get("price_sources", ())
        ),
        etf_rule=EtfRule(
            include_any=tuple(str(item) for item in etf.get("include_any", ())),
            exclude_any=tuple(str(item) for item in etf.get("exclude_any", ())),
            fallback_code=str(etf.get("fallback_code", "")),
            fallback_name=str(etf.get("fallback_name", "")),
            match_note=str(etf.get("match_note", "")),
        ),
    )
