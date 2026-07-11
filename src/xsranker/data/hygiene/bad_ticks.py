"""Bad-tick detection — flag (never silently keep) implausible single-bar moves.

An intraday close-to-close move larger than the configured threshold, *within the
same session* (overnight gaps are legitimate, not bad ticks), is flagged and
logged. This returns the flags; callers decide to drop/repair, and every
correction is logged (Part I §2).
"""

from __future__ import annotations

import numpy as np

from xsranker.core.logging import get_logger
from xsranker.core.types import OHLCV, BoolArray

_log = get_logger("data.hygiene.bad_ticks")


def detect_bad_ticks(ohlcv: OHLCV, *, max_bar_abs_return: float) -> BoolArray:
    """Boolean mask of bars whose in-session close-to-close |return| exceeds threshold.

    The first bar of each IST day has no in-session predecessor, so it is never
    flagged on an overnight move.
    """
    n = len(ohlcv)
    flagged: BoolArray = np.zeros(n, dtype=np.bool_)
    if n < 2:
        return flagged
    dates = ohlcv.ist_dates()
    close = ohlcv.close
    same_day = dates[1:] == dates[:-1]
    with np.errstate(divide="ignore", invalid="ignore"):
        ret = np.abs(close[1:] / close[:-1] - 1.0)
    intrabar = same_day & (ret > max_bar_abs_return)
    flagged[1:] = intrabar
    count = int(flagged.sum())
    if count:
        _log.warning("bad_ticks_flagged", symbol=ohlcv.symbol, count=count, bars=n)
    return flagged
