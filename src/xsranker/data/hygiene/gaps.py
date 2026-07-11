"""Intraday grid-gap (missing-bar) detection within a session.

Distinct from the *price* gap (Signal A, Phase 2): this finds holes in the 5-min
grid — a within-session jump between consecutive bars larger than one interval —
so a downstream feature never treats a data hole as a real quote sequence.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from xsranker.core.logging import get_logger
from xsranker.core.types import OHLCV, BoolArray

_log = get_logger("data.hygiene.gaps")


@dataclass(frozen=True, slots=True)
class GapReport:
    """Missing-bar summary for a symbol."""

    symbol: str
    n_holes: int
    max_hole_bars: int


def detect_intraday_gaps(ohlcv: OHLCV, *, interval_min: int = 5) -> tuple[BoolArray, GapReport]:
    """Mask of bars that FOLLOW a within-session grid hole, plus a summary.

    A hole is a same-day pair of consecutive bars more than one interval apart.
    """
    n = len(ohlcv)
    following_hole: BoolArray = np.zeros(n, dtype=np.bool_)
    if n < 2:
        return following_hole, GapReport(ohlcv.symbol, 0, 0)
    minutes = ohlcv.ist_minutes()
    dates = ohlcv.ist_dates()
    same_day = dates[1:] == dates[:-1]
    delta = minutes[1:] - minutes[:-1]
    holes = same_day & (delta > interval_min)
    following_hole[1:] = holes
    n_holes = int(holes.sum())
    max_hole = int((delta[holes] // interval_min).max()) if n_holes else 0
    if n_holes:
        _log.warning("intraday_gaps", symbol=ohlcv.symbol, holes=n_holes, max_hole_bars=max_hole)
    return following_hole, GapReport(ohlcv.symbol, n_holes, max_hole)
