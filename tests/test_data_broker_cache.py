# mypy: disable-error-code="no-untyped-def, no-any-return"
"""Broker load against the REAL external cache (local; SKIPS in CI without the cache)."""

from __future__ import annotations

from datetime import date

from xsranker.data.brokers.base import BrokerAdapter
from xsranker.data.brokers.parquet_cache import ParquetCacheBroker


def test_broker_loads_real_symbol(cache_config) -> None:
    broker = ParquetCacheBroker(cache_config.data.cache_path, cache_config.data.interval)
    assert isinstance(broker, BrokerAdapter)
    assert len(broker.available_symbols()) == 49
    ohlcv = broker.load("TATASTEEL", start=date(2022, 7, 25), end=date(2022, 7, 25))
    assert len(ohlcv) > 0
    # 09:15 IST first bar, split-adjusted price scale (~90, not ~900)
    assert int(ohlcv.ist_minutes()[0]) == 555
    assert 50.0 < ohlcv.open[0] < 200.0
