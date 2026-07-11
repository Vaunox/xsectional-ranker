"""Signals A and A-Z: per-day cross-sectional ranking features (point-in-time).

* **A** = gap% (frozen ``gap`` primitive).
* **A-Z** = gap% ÷ ATR% where ATR% = ATR-20(daily) / price. The ATR feeding day D's
  signal is taken at day **D-1** (a shift), so it uses only completed days < D — the
  point-in-time property the prefix-invariance suite proves. The daily resample
  aggregates each IST day's bars into one daily OHLC bar (own point-in-time test).

Selection: rank the panel by the signal via the frozen ``cross_sectional_rank``;
SHORT the top-k (largest gap-ups), LONG the bottom-k (largest gap-downs).
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum

import numpy as np

from xsranker.core.types import OHLCV, FloatArray
from xsranker.harness.adapter import HarnessAdapter


class SignalArm(StrEnum):
    """The two pre-registered signal arms (both charged to the ledger)."""

    A = "A"  # raw gap%
    A_Z = "A-Z"  # gap% / ATR% (volatility-adjusted)


def resample_daily(series: OHLCV) -> tuple[list[date], FloatArray, FloatArray, FloatArray]:
    """Aggregate intraday bars into one daily bar per IST day: (days, high, low, close).

    Point-in-time by construction: a day's daily bar uses ONLY that day's bars (the
    max high / min low / last close), never a future day's.
    """
    dates = series.ist_dates()
    unique, first_idx = np.unique(dates, return_index=True)
    last_idx = np.empty_like(first_idx)
    last_idx[:-1] = first_idx[1:] - 1
    last_idx[-1] = len(dates) - 1
    days = [d.astype("datetime64[D]").astype(date) for d in unique]
    highs = np.array(
        [series.high[first_idx[i] : last_idx[i] + 1].max() for i in range(len(unique))]
    )
    lows = np.array([series.low[first_idx[i] : last_idx[i] + 1].min() for i in range(len(unique))])
    closes = series.close[last_idx]
    return days, highs, lows, closes


def gap_pct_by_day(series: OHLCV, adapter: HarnessAdapter) -> dict[date, float]:
    """Per-IST-day overnight gap% via the frozen ``gap`` primitive (constant within a day)."""
    values = adapter.gap(series)  # per-bar, constant within a day
    dates = series.ist_dates()
    _unique, first_idx = np.unique(dates, return_index=True)
    out: dict[date, float] = {}
    for i, idx in enumerate(first_idx):
        v = float(values[idx])
        if np.isfinite(v):
            out[_unique[i].astype("datetime64[D]").astype(date)] = v
    return out


def atr_pct_by_day(series: OHLCV, adapter: HarnessAdapter, *, atr_period: int) -> dict[date, float]:
    """ATR-20% for each day's signal, taken at the PRIOR day (point-in-time shift).

    ATR is computed once on the daily series (``talib.ATR`` at index i uses only bars
    <= i); the value at day D-1 normalizes day D's gap, so no future bar leaks.
    """
    days, highs, lows, closes = resample_daily(series)
    n = len(days)
    if n < 2:
        return {}
    # a daily OHLCV (atr ignores timestamps; 09:15-IST stamps keep the bridge valid)
    ts = np.array(
        [np.datetime64(d, "ns") + np.timedelta64(3 * 3600 + 45 * 60, "s") for d in days],
        dtype="datetime64[ns]",
    )
    daily = OHLCV(
        series.symbol, "1day", ts, closes, highs, lows, closes, np.ones(n, dtype=np.int64)
    )
    atr_abs = adapter.atr(daily, atr_period)
    with np.errstate(divide="ignore", invalid="ignore"):
        atr_pct_full = atr_abs / closes
    out: dict[date, float] = {}
    for i in range(1, n):  # day i's signal uses ATR% at day i-1 (completed)
        v = float(atr_pct_full[i - 1])
        if np.isfinite(v) and v > 0.0:
            out[days[i]] = v
    return out


def signal_value_by_day(
    arm: SignalArm, series: OHLCV, adapter: HarnessAdapter, *, atr_period: int
) -> dict[date, float]:
    """Per-day signal value for ``series``: gap% (A) or gap% ÷ ATR% (A-Z)."""
    gaps = gap_pct_by_day(series, adapter)
    if arm is SignalArm.A:
        return gaps
    atr_pct = atr_pct_by_day(series, adapter, atr_period=atr_period)
    return {d: gaps[d] / atr_pct[d] for d in gaps if d in atr_pct}
