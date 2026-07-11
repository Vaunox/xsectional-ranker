# mypy: disable-error-code="no-untyped-def, no-any-return"
"""Tests for hygiene jobs: bad-tick detection, grid-gap detection, liquidity floor."""

from __future__ import annotations

from datetime import date

from xsranker.data.hygiene.bad_ticks import detect_bad_ticks
from xsranker.data.hygiene.gaps import detect_intraday_gaps
from xsranker.data.hygiene.liquidity import (
    passes_liquidity_floor,
    trailing_median_daily_value,
)


def test_bad_tick_flagged_intraday_not_overnight(build_ohlcv) -> None:
    # day1: 100,101 ; day2: 200(overnight +98%),100(intraday -50% bad tick),101
    ohlcv = build_ohlcv(
        dates=[date(2024, 1, 2), date(2024, 1, 3)],
        bars_per_day=2,
        closes=[100.0, 101.0, 200.0, 100.0],
    )
    flags = detect_bad_ticks(ohlcv, max_bar_abs_return=0.35)
    assert list(flags) == [False, False, False, True]  # only the intraday -50% flagged


def test_intraday_gap_detection(build_ohlcv) -> None:
    # bars at 09:15 and 09:45 within a day -> a 30-min hole (6 intervals)
    ohlcv = build_ohlcv(dates=[date(2024, 1, 2)], bars_per_day=2, start_min=555, step=30)
    following, report = detect_intraday_gaps(ohlcv, interval_min=5)
    assert report.n_holes == 1 and report.max_hole_bars == 6
    assert list(following) == [False, True]


def test_trailing_liquidity_is_point_in_time(build_ohlcv) -> None:
    days = [date(2024, 1, d) for d in (2, 3, 4, 5, 8)]
    # daily traded value grows; volume 1000/bar, 1 bar/day, close = value/1000
    ohlcv = build_ohlcv(
        dates=days, bars_per_day=1, closes=[10, 20, 30, 40, 999], volumes=[1000] * 5
    )
    # trailing median over 3 days strictly before 2024-01-08 = median(20k,30k,40k)*...
    med = trailing_median_daily_value(ohlcv, as_of=date(2024, 1, 8), lookback_days=3)
    assert med == 30.0 * 1000  # excludes the as-of day (999) -> no lookahead
    assert passes_liquidity_floor(
        ohlcv, as_of=date(2024, 1, 8), lookback_days=3, min_median_value=10_000.0
    )


def test_liquidity_insufficient_history_fails_closed(build_ohlcv) -> None:
    ohlcv = build_ohlcv(dates=[date(2024, 1, 2), date(2024, 1, 3)], bars_per_day=1)
    # only 1 trailing day before as_of, need 20 -> nan -> floor fails closed
    assert not passes_liquidity_floor(
        ohlcv, as_of=date(2024, 1, 3), lookback_days=20, min_median_value=1.0
    )
