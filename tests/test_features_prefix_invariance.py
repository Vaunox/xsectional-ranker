# mypy: disable-error-code="no-untyped-def, no-any-return"
"""Prefix-invariance / no-lookahead suite (load-bearing, runs in CI on synthetic data).

The morning window (09:15 -> entry) is where leakage hides. A feature computable at
the entry instant must use ONLY bars <= entry, so appending future bars (the day's
afternoon, or later days) cannot change a past value. The suite proves the honest
feature has this property AND that it has teeth — a deliberately leaky feature that
peeks at the day's close is caught.
"""

from __future__ import annotations

from datetime import date

import numpy as np

from xsranker.core.types import OHLCV
from xsranker.features.dual_path import trailing_mean_vectorized
from xsranker.features.point_in_time import entry_window_return

ENTRY_MINUTE = 570  # 09:30, inside a 6-bar morning window 09:15..09:40


def _morning_only(ohlcv: OHLCV, entry_minute: int) -> OHLCV:
    """Drop every bar strictly after ``entry_minute`` (the 'future' within each day)."""
    mask = ohlcv.ist_minutes() <= entry_minute
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


def _leaky_close_return(ohlcv: OHLCV, *, entry_minute: int) -> np.ndarray:
    """A LEAKY feature: open-to-*day-close* return (peeks past the entry instant)."""
    dates = ohlcv.ist_dates()
    out: list[float] = []
    for d in np.unique(dates):
        day = dates == d
        out.append(float(ohlcv.close[day][-1] / ohlcv.open[day][0] - 1.0))
    return np.array(out, dtype=np.float64)


def test_entry_window_return_is_invariant_to_afternoon_bars(build_ohlcv) -> None:
    """Honest feature: identical whether or not post-entry bars are present."""
    ohlcv = build_ohlcv(bars_per_day=6)
    _d1, full = entry_window_return(ohlcv, entry_minute=ENTRY_MINUTE)
    _d2, morning = entry_window_return(
        _morning_only(ohlcv, ENTRY_MINUTE), entry_minute=ENTRY_MINUTE
    )
    assert np.allclose(full, morning)


def test_entry_window_return_is_invariant_to_future_days(build_ohlcv) -> None:
    """A past day's value does not depend on later days being appended."""
    days = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4), date(2024, 1, 5)]
    ohlcv = build_ohlcv(dates=days, bars_per_day=6)
    _d, full = entry_window_return(ohlcv, entry_minute=ENTRY_MINUTE)
    two_day = ohlcv.slice(0, 2 * 6)
    _d2, first_two = entry_window_return(two_day, entry_minute=ENTRY_MINUTE)
    assert np.allclose(full[:2], first_two)


def test_leaky_feature_is_caught(build_ohlcv) -> None:
    """Teeth: a feature that peeks at the day close CHANGES when afternoon bars appear."""
    ohlcv = build_ohlcv(bars_per_day=6)
    full = _leaky_close_return(ohlcv, entry_minute=ENTRY_MINUTE)
    morning = _leaky_close_return(_morning_only(ohlcv, ENTRY_MINUTE), entry_minute=ENTRY_MINUTE)
    # the leaky feature is NOT invariant -> the invariance check discriminates
    assert not np.allclose(full, morning)


def test_trailing_normalization_excludes_current_bar(build_ohlcv) -> None:
    """Trailing/expanding normalization must not include the current observation."""
    x = np.arange(1.0, 11.0)
    out = trailing_mean_vectorized(x, window=100)  # expanding trailing mean
    assert np.isnan(out[0])  # nothing before the first
    assert out[1] == 1.0  # mean of {x[0]} only
    assert out[3] == np.mean(x[:3])  # excludes x[3]
