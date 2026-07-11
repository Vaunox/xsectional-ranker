"""Tests for the survivor-stub universe, sector map, and Layer-1 config parsing.

These use the committed config files (not the external cache), so they run in CI.
"""

from __future__ import annotations

from datetime import date

import pytest

from xsranker.core.config import load_settings
from xsranker.data.config import load_data_universe_config
from xsranker.data.universe.point_in_time import load_survivor_universe
from xsranker.data.universe.sector_map import load_sector_map, sector_of, uncovered_symbols


def test_survivor_universe_loads_49_and_stamps() -> None:
    cfg = load_data_universe_config(load_settings())
    uni = load_survivor_universe(cfg.universe_file)
    assert len(uni.symbols) == 49
    assert uni.is_survivor_stub
    assert "survivorship" in uni.stamp.lower()


def test_stub_universe_returns_full_set_on_any_date() -> None:
    cfg = load_data_universe_config(load_settings())
    uni = load_survivor_universe(cfg.universe_file)
    assert uni.as_of(date(2016, 6, 1)) == uni.symbols
    assert uni.as_of(date(2025, 3, 10)) == uni.symbols


def test_sector_map_covers_universe() -> None:
    cfg = load_data_universe_config(load_settings())
    uni = load_survivor_universe(cfg.universe_file)
    smap = load_sector_map(cfg.sector_file)
    assert uncovered_symbols(smap, uni.symbols) == []
    assert sector_of(smap, "TCS") == "Information Technology"


def test_sector_uncovered_and_missing_raise() -> None:
    smap = {"A": "Sector1"}
    assert uncovered_symbols(smap, ("A", "B")) == ["B"]
    with pytest.raises(KeyError):
        sector_of(smap, "B")


def test_layer1_config_parses() -> None:
    cfg = load_data_universe_config(load_settings())
    assert cfg.data.interval == "5minute"
    assert cfg.calendar.entry_minute_default == 555 + 30  # 09:45
    assert cfg.hygiene.liquidity_min_median_daily_value_inr == 50_000_000
    assert cfg.circuit.min_range_ratio == 0.10
