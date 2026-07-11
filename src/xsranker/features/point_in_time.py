"""Point-in-time features: open/close, gap, entry-window return, hold return, entry value.

* ``daily_open_close`` — first-bar open and last-bar close per IST session.
* ``overnight_gap`` — ``(day_open - prior_day_close) / prior_day_close``; the
  gate-zero split check asserts this shows no spurious jump across a known split in
  the adjusted series. (This is the *foundation* of Signal A, but the ranking
  itself is Phase 2.)
* ``entry_window_return`` — ``(entry_bar_close / day_open) - 1`` computed from the
  morning window ``[open .. entry]`` ONLY. It is invariant to appending afternoon or
  future bars — the property the prefix-invariance suite proves is load-bearing.
* ``hold_return`` — ``(day_close / entry_bar_close) - 1``: the realized entry->close
  return of a position entered at the entry instant and held to that session's close.
  Uses ONLY that day's bars from the entry bar to the day's last bar; appending future
  bars/days cannot change a day's value (the no-lookahead property — a hold return that
  reaches even one bar past its own session close would leak). This is the P&L basis
  for the book's per-day net return.
* ``entry_window_value`` — ₹ traded value summed over the morning window
  ``[open .. entry]`` (per-bar ``close * volume``); the base for the 1%-participation
  fill cap. Entry-window only, so it never sees post-entry or future volume.
"""

from __future__ import annotations

from datetime import date

import numpy as np

from xsranker.core.types import OHLCV, DatetimeArray, FloatArray


def daily_open_close(ohlcv: OHLCV) -> tuple[DatetimeArray, FloatArray, FloatArray]:
    """Per IST day: (days ascending, first-bar open, last-bar close).

    Bars are time-ordered, so IST dates are non-decreasing: the last bar of a day is
    the bar just before the next day's first bar (and the final bar for the last day).
    """
    dates = ohlcv.ist_dates()
    unique_days, first_idx = np.unique(dates, return_index=True)
    last_idx = np.empty_like(first_idx)
    last_idx[:-1] = first_idx[1:] - 1
    last_idx[-1] = len(dates) - 1
    return unique_days, ohlcv.open[first_idx], ohlcv.close[last_idx]


def overnight_gap(ohlcv: OHLCV) -> tuple[DatetimeArray, FloatArray]:
    """Per-day overnight gap ``(open - prior_close)/prior_close`` (first day = nan)."""
    days, opens, closes = daily_open_close(ohlcv)
    gaps = np.full(opens.shape[0], np.nan, dtype=np.float64)
    if opens.shape[0] >= 2:
        gaps[1:] = opens[1:] / closes[:-1] - 1.0
    return days, gaps


def entry_window_return(ohlcv: OHLCV, *, entry_minute: int) -> tuple[DatetimeArray, FloatArray]:
    """Per-day open-to-entry return using the morning window ``[open .. entry]`` only.

    A day contributes only if it has both a first bar and an entry-minute bar. The
    value depends solely on bars at or before the entry instant — appending later
    bars (afternoon, future days) cannot change it.
    """
    minutes = ohlcv.ist_minutes()
    dates = ohlcv.ist_dates()
    unique_days = np.unique(dates)
    out_days: list[np.datetime64] = []
    out_vals: list[float] = []
    for d in unique_days:
        day_mask = dates == d
        day_minutes = minutes[day_mask]
        entry_pos = np.nonzero(day_minutes == entry_minute)[0]
        if entry_pos.size == 0:
            continue
        day_open = ohlcv.open[day_mask][0]
        entry_close = ohlcv.close[day_mask][int(entry_pos[0])]
        out_days.append(d)
        out_vals.append(float(entry_close / day_open - 1.0))
    return np.array(out_days, dtype="datetime64[D]"), np.array(out_vals, dtype=np.float64)


def hold_return(ohlcv: OHLCV, *, entry_minute: int) -> dict[date, float]:
    """Per-day entry->close hold return ``(day_close / entry_bar_close) - 1``.

    A position entered at ``entry_minute`` and held to that IST session's close. A day
    contributes only if it has an entry-minute bar. The exit is the day's OWN last bar,
    isolated by the day mask — so appending later bars or future days cannot change a
    day's value (no-lookahead). A variant that reaches past the session close (e.g. the
    series' final bar, or the next day's open) would break that invariance.
    """
    minutes = ohlcv.ist_minutes()
    dates = ohlcv.ist_dates()
    out: dict[date, float] = {}
    for d in np.unique(dates):
        day_mask = dates == d
        entry_pos = np.nonzero(minutes[day_mask] == entry_minute)[0]
        if entry_pos.size == 0:
            continue
        entry_close = ohlcv.close[day_mask][int(entry_pos[0])]
        day_close = ohlcv.close[day_mask][-1]  # this day's last bar, never a later one
        out[d.astype("datetime64[D]").astype(date)] = float(day_close / entry_close - 1.0)
    return out


def entry_window_value(ohlcv: OHLCV, *, entry_minute: int) -> dict[date, float]:
    """Per-day ₹ traded value over the morning window ``[open .. entry]`` (inclusive).

    Sums per-bar ``close * volume`` from the day's first bar to the entry-minute bar —
    the base for the 1%-participation fill cap. Entry-window only: post-entry and
    future-day volume never enter it. A day contributes only if it has an entry bar.
    """
    minutes = ohlcv.ist_minutes()
    dates = ohlcv.ist_dates()
    tv = ohlcv.traded_value()
    out: dict[date, float] = {}
    for d in np.unique(dates):
        day_mask = dates == d
        entry_pos = np.nonzero(minutes[day_mask] == entry_minute)[0]
        if entry_pos.size == 0:
            continue
        window = tv[day_mask][: int(entry_pos[0]) + 1]
        out[d.astype("datetime64[D]").astype(date)] = float(window.sum())
    return out
