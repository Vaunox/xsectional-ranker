"""Circuit-lock / untradeable filter — conservative ghost-fill defense.

At the entry instant a name is flagged untradeable if EITHER:

* its entry-window bar has near-zero range **relative to the name's own recent
  intraday range** (catches full and intermittent locks), OR
* the entry bar is unusually quiet — volume in the bottom quantile of its recent
  bars AND a tighter-than-typical range (a price-at-band, low-time-of-day-volume
  proxy; the per-symbol band table is deferred).

Everything is computed from bars STRICTLY BEFORE the entry bar (trailing, point-in-
time). Conservative: on insufficient history or a degenerate (all-flat) recent
window, flag untradeable — a dropped tradeable name costs a little breadth; a kept
locked name fabricates alpha. The flagged fraction is logged as a diagnostic.
"""

from __future__ import annotations

import numpy as np

from xsranker.core.logging import get_logger
from xsranker.core.types import OHLCV, BoolArray, IntArray
from xsranker.data.config import CircuitConfig

_log = get_logger("data.universe.circuit")


def is_circuit_locked_at(ohlcv: OHLCV, entry_idx: int, cfg: CircuitConfig) -> bool:
    """Whether the entry bar at ``entry_idx`` is a suspected lock (trailing window)."""
    lo = entry_idx - cfg.recent_range_lookback_bars
    if lo < 0:
        return True  # insufficient trailing history -> conservative drop
    recent = ohlcv.slice(lo, entry_idx)
    recent_range = recent.high - recent.low
    recent_median = float(np.median(recent_range))
    if not np.isfinite(recent_median) or recent_median <= 0.0:
        return True  # degenerate flat window -> conservative drop
    entry_range = float(ohlcv.high[entry_idx] - ohlcv.low[entry_idx])
    range_lock = entry_range < cfg.min_range_ratio * recent_median
    vol_threshold = float(np.quantile(recent.volume.astype(np.float64), cfg.low_volume_pctile))
    low_volume = float(ohlcv.volume[entry_idx]) <= vol_threshold
    volume_anomaly = low_volume and entry_range < recent_median
    return bool(range_lock or volume_anomaly)


def circuit_flags(ohlcv: OHLCV, entry_indices: IntArray, cfg: CircuitConfig) -> BoolArray:
    """Boolean flags (untradeable) per entry bar, plus a logged flagged fraction."""
    flags: BoolArray = np.array(
        [is_circuit_locked_at(ohlcv, int(i), cfg) for i in entry_indices], dtype=np.bool_
    )
    if flags.size:
        _log.info(
            "circuit_flagged",
            symbol=ohlcv.symbol,
            flagged=int(flags.sum()),
            entries=int(flags.size),
            fraction=round(float(flags.mean()), 5),
        )
    return flags
