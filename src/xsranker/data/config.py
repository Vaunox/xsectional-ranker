"""Typed Layer-1 (data & universe) configuration, built off :class:`Settings`.

Kept separate from the always-present core :class:`~xsranker.core.config.Settings`
so the core loader stays minimal; this is required only where the data layer runs.
Every path/threshold here is config, never a code literal (Part I §1).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from xsranker.core.config import Settings

#: Env var that overrides the (placeholder) cache path in config, so no absolute
#: machine path is ever committed. Set this locally to point at the real cache.
CACHE_PATH_ENV = "XSR_DATA_CACHE_PATH"


def _minutes(hhmm: str) -> int:
    """Parse ``"HH:MM"`` to minutes since midnight."""
    hh, mm = hhmm.split(":")
    return int(hh) * 60 + int(mm)


def _require(mapping: Mapping[str, Any], key: str, ctx: str) -> Any:
    if key not in mapping:
        raise ValueError(f"config: missing '{key}' under {ctx}")
    return mapping[key]


@dataclass(frozen=True, slots=True)
class DataConfig:
    """Where raw OHLCV is read from and where derived layers are written."""

    cache_path: Path
    interval: str
    derived_path: Path


@dataclass(frozen=True, slots=True)
class CalendarConfig:
    """Regular-session bounds (IST minutes) and the default entry window."""

    regular_start_min: int
    regular_end_min: int
    entry_window_default_min: int

    @property
    def entry_minute_default(self) -> int:
        """IST minute of the default entry instant (regular open + entry window)."""
        return self.regular_start_min + self.entry_window_default_min


@dataclass(frozen=True, slots=True)
class HygieneConfig:
    """Bad-tick and liquidity-floor thresholds (the liquidity floor is frozen)."""

    max_bar_abs_return: float
    liquidity_min_median_daily_value_inr: float
    liquidity_lookback_days: int


@dataclass(frozen=True, slots=True)
class CircuitConfig:
    """Conservative circuit-lock detection parameters."""

    recent_range_lookback_bars: int
    min_range_ratio: float
    low_volume_pctile: float


@dataclass(frozen=True, slots=True)
class DataUniverseConfig:
    """The full Layer-1 config surface."""

    data: DataConfig
    calendar: CalendarConfig
    hygiene: HygieneConfig
    circuit: CircuitConfig
    universe_file: Path
    sector_file: Path


def load_data_universe_config(settings: Settings) -> DataUniverseConfig:
    """Build the typed Layer-1 config from the merged mapping on ``settings``."""
    raw = settings.raw
    cfg_dir = settings.config_dir

    data = _require(raw, "data", "root")
    calendar = _require(raw, "calendar", "root")
    session = _require(calendar, "session", "calendar")
    hygiene = _require(raw, "hygiene", "root")
    liquidity = _require(hygiene, "liquidity_floor", "hygiene")
    bad_tick = _require(hygiene, "bad_tick", "hygiene")
    circuit = _require(raw, "circuit", "root")
    universe = _require(raw, "universe", "root")
    sector = _require(raw, "sector", "root")

    # Cache path: the env var (a local, uncommitted override) wins over the config
    # placeholder, so no absolute machine path is committed. Relative paths resolve
    # against the repo root; a non-existent path simply makes cache-backed tests skip.
    cache_raw = os.environ.get(CACHE_PATH_ENV) or str(_require(data, "cache_path", "data"))
    cache_path = Path(cache_raw).expanduser()
    if not cache_path.is_absolute():
        cache_path = cfg_dir.parent / cache_path

    derived = data.get("derived_path", "data/derived")
    return DataUniverseConfig(
        data=DataConfig(
            cache_path=cache_path,
            interval=str(_require(data, "interval", "data")),
            derived_path=(cfg_dir.parent / str(derived)),
        ),
        calendar=CalendarConfig(
            regular_start_min=_minutes(str(_require(session, "regular_start", "calendar.session"))),
            regular_end_min=_minutes(str(_require(session, "regular_end", "calendar.session"))),
            entry_window_default_min=int(
                _require(calendar, "entry_window_default_min", "calendar")
            ),
        ),
        hygiene=HygieneConfig(
            max_bar_abs_return=float(_require(bad_tick, "max_bar_abs_return", "hygiene.bad_tick")),
            liquidity_min_median_daily_value_inr=float(
                _require(liquidity, "min_median_daily_value_inr", "hygiene.liquidity_floor")
            ),
            liquidity_lookback_days=int(
                _require(liquidity, "lookback_days", "hygiene.liquidity_floor")
            ),
        ),
        circuit=CircuitConfig(
            recent_range_lookback_bars=int(
                _require(circuit, "recent_range_lookback_bars", "circuit")
            ),
            min_range_ratio=float(_require(circuit, "min_range_ratio", "circuit")),
            low_volume_pctile=float(_require(circuit, "low_volume_pctile", "circuit")),
        ),
        universe_file=cfg_dir / str(_require(universe, "survivor_cache_file", "universe")),
        sector_file=cfg_dir / str(_require(sector, "map_file", "sector")),
    )
