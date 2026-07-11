# mypy: disable-error-code="no-untyped-def, no-any-return"
"""Tests for corporate-action back-adjustment (original Layer-1 code)."""

from __future__ import annotations

from datetime import date

import numpy as np

from xsranker.data.hygiene.corp_actions import CorporateAction, adjust
from xsranker.features.point_in_time import overnight_gap


def test_split_factor_math() -> None:
    a = CorporateAction.split(date(2022, 7, 28), 10.0)
    assert a.price_factor == 0.1 and a.volume_factor == 10.0
    b = CorporateAction.bonus(date(2017, 9, 7), held=1, received=1)  # 1:1 bonus => halve
    assert b.price_factor == 0.5 and b.volume_factor == 2.0
    d = CorporateAction.dividend(date(2020, 1, 1), dividend=5.0, reference_close=100.0)
    assert d.price_factor == 0.95 and d.volume_factor == 1.0


def test_split_removes_the_spurious_gap(build_ohlcv) -> None:
    """A raw 10:1 discontinuity becomes continuous after adjustment (teeth)."""
    d1, d2 = date(2022, 7, 27), date(2022, 7, 28)
    # raw/unadjusted: day1 at ~1000 (pre-split), day2 at ~100 (post-split)
    ohlcv = build_ohlcv(
        dates=[d1, d2], bars_per_day=1, closes=[1000.0, 100.0], opens=[1000.0, 100.0]
    )
    _d, raw_gap = overnight_gap(ohlcv)
    assert raw_gap[1] < -0.85  # a giant, spurious ~-90% gap

    adjusted = adjust(ohlcv, [CorporateAction.split(d2, 10.0)])
    _d2, adj_gap = overnight_gap(adjusted)
    assert abs(adj_gap[1]) < 1e-9  # continuous after adjustment


def test_empty_actions_is_identity(build_ohlcv) -> None:
    """Phase-1 path: no actions -> adjusted equals raw (bit-for-bit)."""
    ohlcv = build_ohlcv(bars_per_day=3)
    out = adjust(ohlcv, [])
    assert np.array_equal(out.close, ohlcv.close)
    assert np.array_equal(out.volume, ohlcv.volume)
    assert out is not ohlcv  # a new object, raw not mutated


def test_raw_not_mutated(build_ohlcv) -> None:
    ohlcv = build_ohlcv(dates=[date(2022, 7, 27), date(2022, 7, 28)], bars_per_day=1)
    before = ohlcv.close.copy()
    adjust(ohlcv, [CorporateAction.split(date(2022, 7, 28), 10.0)])
    assert np.array_equal(ohlcv.close, before)  # input untouched
