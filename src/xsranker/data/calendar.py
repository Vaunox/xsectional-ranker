"""NSE trading calendar + IST session tagging.

The Phase-1 trading calendar is derived from the cache itself — the union of
partition dates across the universe IS the set of days NSE traded over the cache's
span, which is provably consistent with the data (no external holiday list, no
extra dependency; swappable for an authoritative source later).

Session tagging classifies each bar by IST wall-clock: the regular session is
09:15-15:30; out-of-session bars (Diwali Muhurat evenings ~18:15-19:15, any
pre-open/post-close) are filtered at this boundary, never trimmed from raw.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date

import numpy as np

from xsranker.core.types import OHLCV, BoolArray, IntArray
from xsranker.data.brokers.base import BrokerAdapter


class NseCalendar:
    """A set of IST trading days, with membership and ordering helpers."""

    def __init__(self, trading_days: Iterable[date]) -> None:
        """Build from an iterable of trading dates (deduplicated, sorted)."""
        self._days: tuple[date, ...] = tuple(sorted(set(trading_days)))
        self._day_set: frozenset[date] = frozenset(self._days)

    @classmethod
    def from_broker(cls, broker: BrokerAdapter, symbols: Sequence[str]) -> NseCalendar:
        """Derive the calendar from the union of partition dates across ``symbols``."""
        days: set[date] = set()
        for sym in symbols:
            days.update(broker.trading_dates(sym))
        if not days:
            raise ValueError("no trading dates found for any symbol")
        return cls(days)

    def is_trading_day(self, d: date) -> bool:
        """Whether ``d`` is an NSE trading day in this calendar."""
        return d in self._day_set

    def trading_days(self) -> tuple[date, ...]:
        """All trading days, ascending."""
        return self._days

    def __len__(self) -> int:
        """Number of trading days."""
        return len(self._days)


def regular_session_mask(ohlcv: OHLCV, *, start_min: int, end_min: int) -> BoolArray:
    """Boolean mask of bars inside the regular session ``[start_min, end_min)`` IST.

    5-min bars are start-stamped, so the last regular bar starts at ``end_min-5``
    (15:25 for a 15:30 close); Muhurat evening bars (~18:15+) fall outside.
    """
    minutes = ohlcv.ist_minutes()
    mask: BoolArray = (minutes >= start_min) & (minutes < end_min)
    return mask


def regular_session(ohlcv: OHLCV, *, start_min: int, end_min: int) -> OHLCV:
    """Return ``ohlcv`` restricted to regular-session bars (out-of-session dropped)."""
    mask = regular_session_mask(ohlcv, start_min=start_min, end_min=end_min)
    return OHLCV(
        symbol=ohlcv.symbol,
        interval=ohlcv.interval,
        timestamp=ohlcv.timestamp[mask],
        open=ohlcv.open[mask],
        high=ohlcv.high[mask],
        low=ohlcv.low[mask],
        close=ohlcv.close[mask],
        volume=ohlcv.volume[mask],
    )


def entry_bar_indices(ohlcv: OHLCV, *, entry_minute: int) -> IntArray:
    """Index of the entry-window bar (IST minute == ``entry_minute``) per trading day.

    Returns one index per day that HAS an entry bar (days missing it are skipped),
    ascending — the point-in-time anchor for the circuit filter and leakage tests.
    """
    minutes = ohlcv.ist_minutes()
    dates = ohlcv.ist_dates()
    hits = np.nonzero(minutes == entry_minute)[0]
    # one per day (first match), preserving order
    seen: set[np.datetime64] = set()
    out: list[int] = []
    for i in hits:
        d = dates[i]
        if d not in seen:
            seen.add(d)
            out.append(int(i))
    return np.array(out, dtype=np.int64)
