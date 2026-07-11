"""Liquidity floor — never rank a name you cannot exit.

The point-in-time feature is the **trailing** median daily traded value over a
lookback window ending strictly BEFORE the as-of date. Trailing-only (never
including the as-of day or the future) is what keeps it leakage-safe — the
prefix-invariance suite exercises exactly this property.
"""

from __future__ import annotations

from datetime import date

import numpy as np

from xsranker.core.types import OHLCV, DatetimeArray, FloatArray


def daily_traded_value(ohlcv: OHLCV) -> tuple[DatetimeArray, FloatArray]:
    """Per-day (IST) total traded value (sum of close*volume), days ascending."""
    dates = ohlcv.ist_dates()
    value = ohlcv.traded_value()
    unique_days, inverse = np.unique(dates, return_inverse=True)
    totals = np.zeros(unique_days.shape[0], dtype=np.float64)
    np.add.at(totals, inverse, value)
    return unique_days, totals


def trailing_median_daily_value(ohlcv: OHLCV, *, as_of: date, lookback_days: int) -> float:
    """Median daily traded value over the ``lookback_days`` days strictly before ``as_of``.

    Returns ``nan`` if fewer than ``lookback_days`` trailing days are available
    (fail closed — a name without enough history cannot clear the floor).
    """
    days, totals = daily_traded_value(ohlcv)
    cutoff = np.datetime64(as_of, "D")
    prior = totals[days < cutoff]
    if prior.shape[0] < lookback_days:
        return float("nan")
    window = prior[-lookback_days:]
    return float(np.median(window))


def passes_liquidity_floor(
    ohlcv: OHLCV, *, as_of: date, lookback_days: int, min_median_value: float
) -> bool:
    """Whether the trailing median daily traded value clears the frozen floor."""
    median = trailing_median_daily_value(ohlcv, as_of=as_of, lookback_days=lookback_days)
    return bool(np.isfinite(median) and median >= min_median_value)
