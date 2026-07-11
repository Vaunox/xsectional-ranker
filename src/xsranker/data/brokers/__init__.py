"""Broker adapters — the read-only historical-OHLCV seam.

Phase 1 ships :class:`~xsranker.data.brokers.parquet_cache.ParquetCacheBroker`
over the inherited external cache. The live-Kite implementation is deferred; the
seam (protocol) is built now, the ingestion is not.
"""

from __future__ import annotations
