# mypy: disable-error-code="no-untyped-def, no-any-return"
"""Tests for the NSE calendar, regular-session filter, and entry-bar anchoring."""

from __future__ import annotations

from datetime import date

from xsranker.data.calendar import (
    NseCalendar,
    entry_bar_indices,
    regular_session,
    regular_session_mask,
)


def test_regular_session_filters_out_of_session_bars(build_ohlcv) -> None:
    # two bars per day at 09:15 (555) and 18:15 (1095, a Muhurat-evening-like bar)
    ohlcv = build_ohlcv(dates=[date(2024, 1, 2)], bars_per_day=2, start_min=555, step=540)
    mask = regular_session_mask(ohlcv, start_min=555, end_min=930)
    assert list(mask) == [True, False]  # 18:15 bar dropped
    filtered = regular_session(ohlcv, start_min=555, end_min=930)
    assert len(filtered) == 1 and int(filtered.ist_minutes()[0]) == 555


def test_entry_bar_indices_one_per_day(build_ohlcv) -> None:
    days = [date(2024, 1, 2), date(2024, 1, 3)]
    ohlcv = build_ohlcv(dates=days, bars_per_day=7, start_min=555, step=5)  # 555..585
    idx = entry_bar_indices(ohlcv, entry_minute=585)  # 09:45
    assert len(idx) == 2
    assert list(ohlcv.ist_minutes()[idx]) == [585, 585]


def test_nse_calendar_dedup_sort_membership() -> None:
    cal = NseCalendar([date(2024, 1, 3), date(2024, 1, 2), date(2024, 1, 3)])
    assert len(cal) == 2
    assert cal.trading_days() == (date(2024, 1, 2), date(2024, 1, 3))
    assert cal.is_trading_day(date(2024, 1, 2))
    assert not cal.is_trading_day(date(2024, 1, 1))
