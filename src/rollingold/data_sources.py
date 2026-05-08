"""Data source adapters for AKShare and offline fixtures."""

from __future__ import annotations

import hashlib
from datetime import date, timedelta
from pathlib import Path

import pandas as pd


def load_sw_history(
    code: str,
    *,
    period: str,
    cache_dir: str | Path = "data/cache",
    offline_fixture: str | Path | None = None,
    refresh: bool = False,
) -> pd.DataFrame:
    if offline_fixture:
        return _load_fixture_history(code, period, Path(offline_fixture))

    cache_path = Path(cache_dir) / f"sw_index_hist_{code}_{period}.csv"
    if cache_path.exists() and not refresh:
        return normalize_history(pd.read_csv(cache_path))

    import akshare as ak

    df = ak.index_hist_sw(symbol=code, period=period)
    normalized = normalize_history(df)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_csv(cache_path, index=False)
    return normalized


def load_realtime_amounts(offline_fixture: str | Path | None = None) -> dict[str, float]:
    if offline_fixture:
        return {}
    import akshare as ak

    df = ak.index_realtime_sw(symbol="一级行业")
    amounts: dict[str, float] = {}
    for _, row in df.iterrows():
        amounts[str(row["指数代码"])] = float(row["成交额"])
    return amounts


def load_etf_spot(
    *,
    cache_dir: str | Path = "data/cache",
    offline_fixture: str | Path | None = None,
    refresh: bool = False,
) -> pd.DataFrame:
    if offline_fixture:
        fixture = Path(offline_fixture) / "etf_spot.csv"
        return pd.read_csv(fixture) if fixture.exists() else pd.DataFrame()

    cache_path = Path(cache_dir) / "etf_spot.csv"
    if cache_path.exists() and not refresh:
        return pd.read_csv(cache_path)

    import akshare as ak

    df = ak.fund_etf_spot_em()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cache_path, index=False)
    return df


def load_etf_history(
    code: str,
    *,
    cache_dir: str | Path = "data/cache",
    offline_fixture: str | Path | None = None,
    refresh: bool = False,
    start_date: str | None = None,
    end_date: str = "20500101",
    adjust: str = "qfq",
) -> pd.DataFrame:
    if offline_fixture:
        fixture = Path(offline_fixture) / f"etf_hist_{code}_daily.csv"
        if fixture.exists():
            return normalize_history(pd.read_csv(fixture))
        return _load_fixture_history(code, "day", Path(offline_fixture))

    if start_date is None:
        start_date = (date.today() - timedelta(days=820)).strftime("%Y%m%d")
    adjust_key = adjust or "raw"
    cache_path = Path(cache_dir) / f"etf_hist_{code}_daily_{adjust_key}.csv"
    if cache_path.exists() and not refresh:
        return normalize_history(pd.read_csv(cache_path))

    import akshare as ak

    df = ak.fund_etf_hist_em(
        symbol=code,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust=adjust,
    )
    normalized = normalize_history(df)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_csv(cache_path, index=False)
    return normalized


def normalize_history(df: pd.DataFrame) -> pd.DataFrame:
    expected = {"日期", "收盘", "成交额"}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"history data missing columns: {', '.join(sorted(missing))}")
    out = df.copy()
    out["日期"] = pd.to_datetime(out["日期"])
    out["收盘"] = pd.to_numeric(out["收盘"], errors="coerce")
    out["成交额"] = pd.to_numeric(out["成交额"], errors="coerce")
    out = out.dropna(subset=["日期", "收盘"]).sort_values("日期")
    return out


def close_series(df: pd.DataFrame) -> pd.Series:
    normalized = normalize_history(df)
    return pd.Series(normalized["收盘"].values, index=pd.to_datetime(normalized["日期"]))


def amount_series(df: pd.DataFrame) -> pd.Series:
    normalized = normalize_history(df)
    return pd.Series(normalized["成交额"].fillna(0).values, index=pd.to_datetime(normalized["日期"]))


def equal_weight_series(series: list[pd.Series]) -> pd.Series:
    if not series:
        raise ValueError("cannot average empty series list")
    frame = pd.concat(series, axis=1, join="inner").dropna()
    if frame.empty:
        raise ValueError("no overlapping data for equal-weight series")
    return frame.mean(axis=1)


def _load_fixture_history(code: str, period: str, fixture_dir: Path) -> pd.DataFrame:
    exact = fixture_dir / f"sw_index_hist_{code}_{period}.csv"
    legacy = fixture_dir / f"sw_index_hist_{code}.csv"
    if exact.exists():
        return normalize_history(pd.read_csv(exact))
    if period == "day" and legacy.exists():
        return normalize_history(pd.read_csv(legacy))

    benchmark = fixture_dir / f"sw_index_hist_801003_{period}.csv"
    if not benchmark.exists() and period == "day":
        benchmark = fixture_dir / "sw_index_hist_801003.csv"
    template = fixture_dir / f"sw_index_hist_801080_{period}.csv"
    if not template.exists() and period == "day":
        template = fixture_dir / "sw_index_hist_801080.csv"
    source = benchmark if benchmark.exists() else template
    if not source.exists():
        raise FileNotFoundError(f"offline fixture missing price history for {code} {period}")
    return _synthetic_from_template(pd.read_csv(source), code)


def _synthetic_from_template(df: pd.DataFrame, code: str) -> pd.DataFrame:
    normalized = normalize_history(df)
    digest = hashlib.sha256(code.encode("utf-8")).digest()
    drift = (digest[0] - 127) / 12700
    scale = 0.86 + digest[1] / 255 * 0.32
    out = normalized.copy()
    steps = range(len(out))
    out["收盘"] = [round(float(value) * scale * (1 + drift * idx), 4) for idx, value in zip(steps, out["收盘"])]
    out["成交额"] = [round(float(value) * (0.7 + digest[2] / 255 * 0.8), 4) for value in out["成交额"]]
    return out
