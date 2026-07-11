"""Core data types for the new program (Layer 1+).

These are ORIGINAL to this program — deliberately not the vendored ``lab.core.types``
(that is frozen Layer-0, reachable only through the harness adapter). A numpy-backed
:class:`OHLCV` is the currency of the data/universe layer: one symbol's time-ordered
5-minute bars, with fixed-offset IST helpers (IST is UTC+05:30 year-round, no DST,
so wall-clock is a pure integer offset — no per-row zoneinfo).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float64]
IntArray = npt.NDArray[np.int64]
BoolArray = npt.NDArray[np.bool_]
DatetimeArray = npt.NDArray[np.datetime64]

#: IST is UTC+05:30 all year (no DST): 5h30m in nanoseconds.
IST_OFFSET_NS: int = 5 * 3_600 * 1_000_000_000 + 30 * 60 * 1_000_000_000


@dataclass(frozen=True, slots=True)
class OHLCV:
    """One symbol's time-ordered OHLCV bars (UTC instants; O/H/L/C/volume arrays).

    All arrays share length ``n`` and index-align. ``timestamp`` holds UTC instants
    (``datetime64[ns]``); IST wall-clock and IST trading dates are derived by the
    fixed +05:30 offset via :meth:`ist_wall` / :meth:`ist_dates`.
    """

    symbol: str
    interval: str
    timestamp: DatetimeArray  # UTC instants, datetime64[ns], strictly increasing
    open: FloatArray
    high: FloatArray
    low: FloatArray
    close: FloatArray
    volume: IntArray

    def __post_init__(self) -> None:
        """Validate index-alignment and dtype invariants (fail closed)."""
        n = self.timestamp.shape[0]
        for name in ("open", "high", "low", "close", "volume"):
            arr = getattr(self, name)
            if arr.shape[0] != n:
                raise ValueError(f"{self.symbol}: {name} length {arr.shape[0]} != timestamp {n}")

    def __len__(self) -> int:
        """Number of bars."""
        return int(self.timestamp.shape[0])

    def ist_wall(self) -> DatetimeArray:
        """Bar timestamps as IST wall-clock (naive ``datetime64[ns]``)."""
        return self.timestamp + np.timedelta64(IST_OFFSET_NS, "ns")

    def ist_dates(self) -> DatetimeArray:
        """IST trading date per bar (``datetime64[D]``)."""
        return self.ist_wall().astype("datetime64[D]")

    def ist_minutes(self) -> IntArray:
        """Minutes since IST midnight per bar (e.g. 09:15 -> 555)."""
        wall = self.ist_wall()
        midnight = wall.astype("datetime64[D]").astype("datetime64[ns]")
        delta: IntArray = (wall - midnight).astype("timedelta64[m]").astype(np.int64)
        return delta

    def traded_value(self) -> FloatArray:
        """Per-bar traded value (close * volume), a liquidity proxy."""
        return self.close * self.volume.astype(np.float64)

    def slice(self, start: int, stop: int) -> OHLCV:
        """Return a new OHLCV over the half-open bar range ``[start, stop)``."""
        return OHLCV(
            symbol=self.symbol,
            interval=self.interval,
            timestamp=self.timestamp[start:stop],
            open=self.open[start:stop],
            high=self.high[start:stop],
            low=self.low[start:stop],
            close=self.close[start:stop],
            volume=self.volume[start:stop],
        )
