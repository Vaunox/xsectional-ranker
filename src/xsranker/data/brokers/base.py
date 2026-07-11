"""The ``BrokerAdapter`` protocol — the only sanctioned source of raw OHLCV.

Business code depends on this Protocol, never on a concrete broker, so the
live-Kite adapter (deferred) can drop in behind the same surface later without a
downstream change (Part I §1).
"""

from __future__ import annotations

from datetime import date
from typing import Protocol, runtime_checkable

from xsranker.core.types import OHLCV


@runtime_checkable
class BrokerAdapter(Protocol):
    """Read-only provider of historical OHLCV for a symbol.

    Implementations must be point-in-time honest: ``load`` returns only bars that
    existed at their timestamps, never future-adjusted in a way that leaks (split
    back-adjustment is a level shift applied uniformly and is not lookahead).
    """

    def available_symbols(self) -> list[str]:
        """Symbols the source can serve (sorted)."""
        ...

    def trading_dates(self, symbol: str) -> list[date]:
        """IST trading dates available for ``symbol`` (sorted, ascending)."""
        ...

    def load(self, symbol: str, *, start: date | None = None, end: date | None = None) -> OHLCV:
        """Load ``symbol``'s bars over the inclusive IST date range (all if None)."""
        ...
