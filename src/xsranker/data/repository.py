"""``Repository`` — immutable raw + versioned derived OHLCV layers.

* **raw** — served straight from the :class:`BrokerAdapter` (the external cache);
  never written, never mutated.
* **derived** — back-adjusted (or otherwise processed) series, written under
  ``<derived_root>/version=<v>/symbol=<SYM>.parquet``. A version is **immutable**:
  persisting over an existing (symbol, version) raises. A *correction* is a NEW
  version, never an in-place edit (Part III Layer 1).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import date
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from xsranker.core.logging import get_logger
from xsranker.core.types import OHLCV
from xsranker.data.brokers.base import BrokerAdapter
from xsranker.data.hygiene.corp_actions import CorporateAction, adjust

_log = get_logger("data.repository")


#: Phase-1 corp-action provider: no actions (cache is already Kite split/bonus
#: adjusted; dividends deferred to Phase 4). Adjusted == raw.
def no_corporate_actions(_symbol: str) -> Sequence[CorporateAction]:
    """Return no corporate actions (the Phase-1 provider)."""
    return ()


class Repository:
    """Immutable raw + versioned-derived access over a :class:`BrokerAdapter`."""

    def __init__(
        self,
        broker: BrokerAdapter,
        derived_root: Path,
        *,
        action_provider: Callable[[str], Sequence[CorporateAction]] = no_corporate_actions,
    ) -> None:
        """Bind to a broker (raw source), a derived-layer root, and an action provider."""
        self._broker = broker
        self._derived_root = derived_root
        self._action_provider = action_provider

    # -- raw (immutable external) -------------------------------------------- #
    def raw(self, symbol: str, *, start: date | None = None, end: date | None = None) -> OHLCV:
        """The raw OHLCV as stored — never mutated."""
        return self._broker.load(symbol, start=start, end=end)

    # -- derived (adjusted) -------------------------------------------------- #
    def adjusted(self, symbol: str, *, start: date | None = None, end: date | None = None) -> OHLCV:
        """Corp-action-adjusted OHLCV (Phase 1: equals raw, empty action list)."""
        return adjust(self.raw(symbol, start=start, end=end), self._action_provider(symbol))

    # -- versioned derived persistence (immutable) --------------------------- #
    def _derived_path(self, symbol: str, version: str) -> Path:
        return self._derived_root / f"version={version}" / f"symbol={symbol}.parquet"

    def persist_derived(self, symbol: str, ohlcv: OHLCV, *, version: str) -> Path:
        """Write ``ohlcv`` as derived (symbol, version); refuse to overwrite.

        Immutability is enforced here: a correction must be a NEW ``version``, never
        an in-place rewrite of an existing one.
        """
        path = self._derived_path(symbol, version)
        if path.exists():
            raise FileExistsError(
                f"derived layer is immutable: (symbol={symbol}, version={version}) already "
                f"exists at {path}; a correction must use a new version"
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        table = pa.table(
            {
                "timestamp_ns": ohlcv.timestamp.astype("datetime64[ns]").astype(np.int64),
                "open": ohlcv.open,
                "high": ohlcv.high,
                "low": ohlcv.low,
                "close": ohlcv.close,
                "volume": ohlcv.volume,
            }
        )
        pq.write_table(table, path)
        _log.info("persisted_derived", symbol=symbol, version=version, bars=len(ohlcv))
        return path

    def load_derived(self, symbol: str, *, version: str) -> OHLCV:
        """Load a persisted derived (symbol, version) series."""
        path = self._derived_path(symbol, version)
        if not path.exists():
            raise FileNotFoundError(f"no derived layer at {path}")
        table = pq.read_table(path)
        return OHLCV(
            symbol=symbol,
            interval="derived",
            timestamp=table.column("timestamp_ns").to_numpy().astype("datetime64[ns]"),
            open=table.column("open").to_numpy().astype(np.float64),
            high=table.column("high").to_numpy().astype(np.float64),
            low=table.column("low").to_numpy().astype(np.float64),
            close=table.column("close").to_numpy().astype(np.float64),
            volume=table.column("volume").to_numpy().astype(np.int64),
        )
