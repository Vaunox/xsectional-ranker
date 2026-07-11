"""Assemble the Layer-1 data & universe context from settings — the real call site.

``build_data_context`` is where every Layer-1 capability is actually invoked
together (broker, repository, universe stub, calendar, sector map), so the
Completion Standard's "claimed at a call site" holds for the layer as a whole.
"""

from __future__ import annotations

from dataclasses import dataclass

from xsranker.core.config import Settings
from xsranker.data.brokers.parquet_cache import ParquetCacheBroker
from xsranker.data.calendar import NseCalendar
from xsranker.data.config import DataUniverseConfig, load_data_universe_config
from xsranker.data.repository import Repository
from xsranker.data.universe.point_in_time import PointInTimeUniverse, load_survivor_universe
from xsranker.data.universe.sector_map import load_sector_map


@dataclass(frozen=True, slots=True)
class DataContext:
    """The wired Layer-1 substrate: config + seam + universe machinery."""

    settings: Settings
    config: DataUniverseConfig
    broker: ParquetCacheBroker
    repository: Repository
    universe: PointInTimeUniverse
    calendar: NseCalendar
    sector_map: dict[str, str]


def build_data_context(settings: Settings) -> DataContext:
    """Wire the full Layer-1 context from ``settings`` (reads the external cache)."""
    config = load_data_universe_config(settings)
    broker = ParquetCacheBroker(config.data.cache_path, config.data.interval)
    repository = Repository(broker, config.data.derived_path)
    universe = load_survivor_universe(config.universe_file)
    calendar = NseCalendar.from_broker(broker, universe.symbols)
    sector_map = load_sector_map(config.sector_file)
    return DataContext(
        settings=settings,
        config=config,
        broker=broker,
        repository=repository,
        universe=universe,
        calendar=calendar,
        sector_map=sector_map,
    )
