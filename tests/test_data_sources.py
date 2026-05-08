import sys
from types import SimpleNamespace

import pandas as pd

from rollingold.data_sources import load_etf_history, load_sw_history


def _history(close):
    return pd.DataFrame(
        {
            "日期": ["2026-01-01"],
            "收盘": [close],
            "成交额": [1000],
        }
    )


def test_load_sw_history_refreshes_existing_cache(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    cache_path = cache_dir / "sw_index_hist_801003_day.csv"
    _history(1).to_csv(cache_path, index=False)

    fake_akshare = SimpleNamespace(index_hist_sw=lambda symbol, period: _history(2))
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)

    cached = load_sw_history("801003", period="day", cache_dir=cache_dir)
    refreshed = load_sw_history("801003", period="day", cache_dir=cache_dir, refresh=True)

    assert cached["收盘"].iloc[-1] == 1
    assert refreshed["收盘"].iloc[-1] == 2
    assert pd.read_csv(cache_path)["收盘"].iloc[-1] == 2


def test_offline_fixture_does_not_fabricate_etf_history_from_sw_index(tmp_path):
    _history(100).to_csv(tmp_path / "sw_index_hist_801003_day.csv", index=False)

    history = load_etf_history("159825", offline_fixture=tmp_path)

    assert list(history.columns) == ["日期", "收盘", "成交额"]
    assert history.empty
