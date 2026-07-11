"""``ParquetCacheBroker`` — read the inherited external Parquet OHLCV cache.

Hive layout ``<root>/symbol=<SYM>/interval=<interval>/<YYYY-MM-DD>.parquet``, one
partition per IST trading day. Read-only: this class never writes, regenerates, or
re-ingests — it treats the cache as an external input (hat 3). The parquet
timestamp column is ``timestamp[us, tz=Asia/Kolkata]``; its int64 storage is
epoch-microseconds UTC, which we lift to ``datetime64[ns]`` UTC.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from xsranker.core.logging import get_logger
from xsranker.core.types import OHLCV

_log = get_logger("data.brokers.parquet_cache")

_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


class ParquetCacheBroker:
    """Read-only :class:`~xsranker.data.brokers.base.BrokerAdapter` over the cache."""

    def __init__(self, cache_root: Path, interval: str) -> None:
        """Bind to the cache root and interval (both from config, never literals)."""
        self._root = cache_root
        self._interval = interval
        if not self._root.exists():
            raise FileNotFoundError(f"parquet cache root not found: {self._root}")

    def _symbol_dir(self, symbol: str) -> Path:
        return self._root / f"symbol={symbol}" / f"interval={self._interval}"

    def available_symbols(self) -> list[str]:
        """Symbols present under the cache root (sorted)."""
        return sorted(p.name[len("symbol=") :] for p in self._root.glob("symbol=*") if p.is_dir())

    def _partition_files(self, symbol: str) -> list[tuple[date, Path]]:
        out: list[tuple[date, Path]] = []
        for p in self._symbol_dir(symbol).glob("*.parquet"):
            try:
                d = date.fromisoformat(p.stem)
            except ValueError:
                continue  # ignore non-date partition names
            out.append((d, p))
        out.sort(key=lambda t: t[0])
        return out

    def trading_dates(self, symbol: str) -> list[date]:
        """IST trading dates available for ``symbol`` (ascending)."""
        return [d for d, _ in self._partition_files(symbol)]

    def load(self, symbol: str, *, start: date | None = None, end: date | None = None) -> OHLCV:
        """Load ``symbol`` over the inclusive IST date range (all partitions if None)."""
        files = [
            p
            for d, p in self._partition_files(symbol)
            if (start is None or d >= start) and (end is None or d <= end)
        ]
        if not files:
            raise FileNotFoundError(
                f"no partitions for symbol={symbol} interval={self._interval} "
                f"in [{start}, {end}] under {self._root}"
            )
        table = pa.concat_tables([pq.read_table(f, columns=_COLUMNS) for f in files])
        # int64 storage of timestamp[us, tz] is epoch-microseconds UTC.
        ts_us = pc.cast(table.column("timestamp"), pa.int64()).to_numpy()
        timestamp = (ts_us.astype(np.int64) * 1000).astype("datetime64[ns]")
        order = np.argsort(timestamp, kind="stable")
        ohlcv = OHLCV(
            symbol=symbol,
            interval=self._interval,
            timestamp=timestamp[order],
            open=table.column("open").to_numpy().astype(np.float64)[order],
            high=table.column("high").to_numpy().astype(np.float64)[order],
            low=table.column("low").to_numpy().astype(np.float64)[order],
            close=table.column("close").to_numpy().astype(np.float64)[order],
            volume=table.column("volume").to_numpy().astype(np.int64)[order],
        )
        _log.debug("loaded", symbol=symbol, bars=len(ohlcv), partitions=len(files))
        return ohlcv
