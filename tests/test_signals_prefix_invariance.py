# mypy: disable-error-code="no-untyped-def, no-any-return"
"""Prefix-invariance / no-lookahead on Signals A and A-Z (load-bearing, CI, synthetic).

A signal at the entry instant must use only bars <= entry, so appending future bars
(later days) cannot change a past day's value. Proven for both arms, plus the new
intraday->daily resample's point-in-time property, plus teeth (a leaky future-using
variant is caught).
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from xsranker.core.config import load_settings
from xsranker.core.types import OHLCV
from xsranker.harness.adapter import HarnessAdapter
from xsranker.signals.spec import (
    SignalArm,
    atr_pct_by_day,
    resample_daily,
    signal_value_by_day,
)

DAYS = [date(2024, 1, 1) + timedelta(days=i) for i in range(25)]


def _adapter() -> HarnessAdapter:
    return HarnessAdapter(load_settings())


def _upto(series: OHLCV, cutoff: date) -> OHLCV:
    mask = series.ist_dates() <= np.datetime64(cutoff, "D")
    return OHLCV(
        series.symbol,
        series.interval,
        series.timestamp[mask],
        series.open[mask],
        series.high[mask],
        series.low[mask],
        series.close[mask],
        series.volume[mask],
    )


def _series(build_ohlcv) -> OHLCV:
    """Synthetic multi-day series WITH real (varying) overnight gaps + intraday drift."""
    rng = np.random.default_rng(3)
    bpd, nd = 3, len(DAYS)
    day_gaps = rng.normal(0.0, 0.02, nd)  # ~2% varying overnight gaps
    opens = np.empty(nd * bpd)
    closes = np.empty(nd * bpd)
    price = 100.0
    for di in range(nd):
        first_open = price * (1.0 + day_gaps[di]) if di > 0 else price
        for b in range(bpd):
            i = di * bpd + b
            opens[i] = first_open if b == 0 else closes[i - 1]
            closes[i] = opens[i] * (1.0 + float(rng.normal(0.0, 0.003)))
        price = closes[di * bpd + bpd - 1]
    return build_ohlcv(dates=DAYS, bars_per_day=bpd, closes=closes.tolist(), opens=opens.tolist())


def test_signal_a_is_prefix_invariant(build_ohlcv) -> None:
    a = _adapter()
    series = _series(build_ohlcv)
    full = signal_value_by_day(SignalArm.A, series, a, atr_period=20)
    cutoff = DAYS[22]
    trunc = signal_value_by_day(SignalArm.A, _upto(series, cutoff), a, atr_period=20)
    assert trunc, "expected some signal values"
    for d, v in trunc.items():
        assert full[d] == v  # unchanged by dropping future days


def test_signal_az_is_prefix_invariant(build_ohlcv) -> None:
    a = _adapter()
    series = _series(build_ohlcv)
    full = signal_value_by_day(SignalArm.A_Z, series, a, atr_period=20)
    cutoff = DAYS[23]
    trunc = signal_value_by_day(SignalArm.A_Z, _upto(series, cutoff), a, atr_period=20)
    assert trunc, "A-Z should produce values once ATR-20 warms up"
    for d, v in trunc.items():
        assert full[d] == v


def test_resample_daily_is_point_in_time(build_ohlcv) -> None:
    """A past day's daily bar does not change when future days are appended."""
    series = _series(build_ohlcv)
    cutoff = DAYS[20]
    fd, fh, fl, fc = resample_daily(series)
    td, th, tl, tc = resample_daily(_upto(series, cutoff))
    kept = len(td)
    assert np.array_equal(fh[:kept], th) and np.array_equal(fl[:kept], tl)
    assert np.array_equal(fc[:kept], tc) and fd[:kept] == td


def test_atr_pct_uses_only_completed_prior_days(build_ohlcv) -> None:
    """ATR% feeding day D is invariant to future bars (it is the day-(D-1) value)."""
    a = _adapter()
    series = _series(build_ohlcv)
    cutoff = DAYS[23]
    full = atr_pct_by_day(series, a, atr_period=20)
    trunc = atr_pct_by_day(_upto(series, cutoff), a, atr_period=20)
    for d, v in trunc.items():
        assert full[d] == v


def test_leaky_future_normalization_is_caught(build_ohlcv) -> None:
    """Teeth: normalizing by a FULL-SERIES statistic (peeks at the future) is not invariant."""
    a = _adapter()
    series = _series(build_ohlcv)

    def _leaky(s: OHLCV) -> dict[date, float]:
        # blatant lookahead: every day takes the LATEST available day's gap
        gaps = signal_value_by_day(SignalArm.A, s, a, atr_period=20)
        last_gap = gaps[max(gaps)]
        return dict.fromkeys(gaps, last_gap)

    cutoff = DAYS[15]
    full = _leaky(series)
    trunc = _leaky(_upto(series, cutoff))
    assert any(full[d] != trunc[d] for d in trunc)  # NOT invariant -> caught
