"""OHLCV bridge correctness — a gate-zero-class seam (not plumbing).

The converter between ``xsranker.core.types.OHLCV`` and the vendored OHLCV sits
directly between our data and the frozen gap/ATR math. A timezone slip or a wrong
"which bar is the day's open" there silently corrupts the signal — exactly what
gate-zero exists to prevent — so it gets explicit correctness tests:
round-trip identity, volume-type preservation, the IST date boundary (with teeth
against a UTC-date slip), and the day-open the vendored ``gap`` actually receives.
"""

from __future__ import annotations

from datetime import date

import numpy as np

from xsranker.core.config import load_settings
from xsranker.core.types import IST_OFFSET_NS, OHLCV
from xsranker.harness.adapter import HarnessAdapter


def _adapter() -> HarnessAdapter:
    return HarnessAdapter(load_settings())


def _ist_ts(d: date, minute: int) -> np.datetime64:
    wall = np.datetime64(d, "ns") + np.timedelta64(minute * 60, "s").astype("timedelta64[ns]")
    out: np.datetime64 = wall - np.timedelta64(IST_OFFSET_NS, "ns")
    return out


def test_bridge_round_trip_and_volume_type() -> None:
    ts = np.array(
        [_ist_ts(date(2024, 1, 2), 555), _ist_ts(date(2024, 1, 2), 560)], "datetime64[ns]"
    )
    o = OHLCV(
        "X",
        "5minute",
        ts,
        np.array([100.0, 100.5]),
        np.array([101.0, 101.5]),
        np.array([99.0, 99.5]),
        np.array([100.5, 101.0]),
        np.array([1000, 2000], dtype=np.int64),
    )
    v = _adapter()._to_vendored_ohlcv(o)
    # O/H/L/C pass through byte-for-byte; int volume becomes float64 (vendored dtype)
    assert np.array_equal(v.open, o.open) and np.array_equal(v.close, o.close)
    assert np.array_equal(v.high, o.high) and np.array_equal(v.low, o.low)
    assert v.volume.dtype == np.float64
    assert list(v.volume) == [1000.0, 2000.0]
    assert len(v.timestamps) == 2


def test_bridge_localizes_to_ist_date_not_utc() -> None:
    """Teeth: a 20:00-UTC instant is 01:30 IST the NEXT day — the bridge must say so.

    A UTC-date bridge would mislabel this bar's day, corrupting the vendored gap's
    day grouping. Session bars (09:15-15:25 IST) share their UTC date, so this
    out-of-session instant is what actually discriminates a timezone slip.
    """
    ts = np.array([np.datetime64("2024-01-02T20:00:00", "ns")], "datetime64[ns]")
    o = OHLCV(
        "X",
        "5m",
        ts,
        np.array([1.0]),
        np.array([1.0]),
        np.array([1.0]),
        np.array([1.0]),
        np.array([1], dtype=np.int64),
    )
    v = _adapter()._to_vendored_ohlcv(o)
    assert v.timestamps[0].date() == date(2024, 1, 3)  # IST next day, NOT UTC's Jan 2
    offset = v.timestamps[0].utcoffset()
    assert offset is not None and offset.total_seconds() == 5.5 * 3600  # +05:30


def test_bridge_feeds_correct_day_open_to_gap() -> None:
    """The vendored gap receives each IST day's FIRST open and prior day's LAST close."""
    a = _adapter()
    # day1: 3 bars (opens 100/100.5/101, closes 100.5/101/101.5 -> last close 101.5)
    # day2: 3 bars (first open 110) -> gap = 110/101.5 - 1
    rows = [
        (date(2024, 1, 2), 555, 100.0, 100.5),
        (date(2024, 1, 2), 560, 100.5, 101.0),
        (date(2024, 1, 2), 565, 101.0, 101.5),
        (date(2024, 1, 3), 555, 110.0, 110.5),
        (date(2024, 1, 3), 560, 110.5, 111.0),
        (date(2024, 1, 3), 565, 111.0, 111.5),
    ]
    ts = np.array([_ist_ts(d, m) for d, m, _o, _c in rows], "datetime64[ns]")
    opens = np.array([o for _d, _m, o, _c in rows])
    closes = np.array([c for _d, _m, _o, c in rows])
    series = OHLCV(
        "X", "5m", ts, opens, opens + 0.2, opens - 0.2, closes, np.full(6, 1000, dtype=np.int64)
    )
    g = a.gap(series)
    assert np.isnan(g[0])  # day1 has no prior day
    assert g[-1] == g[3]  # constant within day2
    assert g[3] == 110.0 / 101.5 - 1.0  # first-open / prior-day-last-close
