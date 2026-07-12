"""Load the survivor universe's adjusted, session-filtered OHLCV — with a pickle cache.

Loading 49 survivors x ~2,800 daily Parquet partitions is slow; the session-filtered series
are deterministic, so they are cached once to a machine-local pickle (``$XSR_PANEL_PICKLE`` or
an explicit path) and reused across the ledger regen / D8 / candidate-#2 runs. The cache is
never committed; the series it yields are identical whether loaded fresh or from the pickle.
"""

from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import cast

from xsranker.core.types import OHLCV
from xsranker.data.calendar import regular_session
from xsranker.data.factory import DataContext
from xsranker.data.universe.sector_map import sector_of

#: Env var pointing at the machine-local panel pickle (never committed).
PANEL_PICKLE_ENV = "XSR_PANEL_PICKLE"

SessionSeries = dict[str, tuple[OHLCV, str]]


def load_session_series(ctx: DataContext) -> SessionSeries:
    """Symbol -> (adjusted + regular-session-filtered OHLCV, sector) for every survivor."""
    start = ctx.config.calendar.regular_start_min
    end = ctx.config.calendar.regular_end_min
    out: SessionSeries = {}
    for sym in ctx.universe.symbols:
        series = regular_session(ctx.repository.adjusted(sym), start_min=start, end_min=end)
        out[sym] = (series, sector_of(ctx.sector_map, sym))
    return out


def cached_session_series(ctx: DataContext, cache_path: Path | None = None) -> SessionSeries:
    """Load the session series from a pickle if present, else build ONCE and write it.

    ``cache_path`` defaults to ``$XSR_PANEL_PICKLE`` when set. Never reload from Parquet when a
    valid cache exists — the whole point is to pay the ~2-minute load exactly once.
    """
    path = cache_path
    if path is None and os.environ.get(PANEL_PICKLE_ENV):
        path = Path(os.environ[PANEL_PICKLE_ENV])
    if path is not None and path.exists():
        with path.open("rb") as fh:
            # Trusted input: a self-produced, machine-local cache we wrote — never untrusted.
            return cast(SessionSeries, pickle.load(fh))  # noqa: S301
    series = load_session_series(ctx)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as fh:
            pickle.dump(series, fh, protocol=pickle.HIGHEST_PROTOCOL)
    return series
