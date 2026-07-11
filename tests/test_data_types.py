# mypy: disable-error-code="no-untyped-def, no-any-return"
"""Tests for the numpy-backed OHLCV type and its fixed-offset IST helpers."""

from __future__ import annotations

from datetime import date

import numpy as np
import pytest

from xsranker.core.types import OHLCV


def test_ist_helpers(build_ohlcv) -> None:
    ohlcv = build_ohlcv(dates=[date(2024, 1, 2)], bars_per_day=3, start_min=555, step=5)
    # 09:15, 09:20, 09:25 IST
    assert list(ohlcv.ist_minutes()) == [555, 560, 565]
    assert list(np.unique(ohlcv.ist_dates())) == [np.datetime64("2024-01-02")]
    assert len(ohlcv) == 3


def test_traded_value_and_slice(build_ohlcv) -> None:
    ohlcv = build_ohlcv(bars_per_day=2, closes=[10, 20, 30, 40, 50, 60], volumes=[1, 2, 3, 4, 5, 6])
    tv = ohlcv.traded_value()
    assert tv[0] == 10 * 1 and tv[3] == 40 * 4
    sub = ohlcv.slice(2, 4)
    assert len(sub) == 2 and sub.close[0] == 30


def test_length_mismatch_fails_closed() -> None:
    ts = np.array(["2024-01-02T03:45"], dtype="datetime64[ns]")
    with pytest.raises(ValueError, match="length"):
        OHLCV(
            "X",
            "5minute",
            ts,
            np.array([1.0, 2.0]),  # wrong length
            np.array([1.0]),
            np.array([1.0]),
            np.array([1.0]),
            np.array([1], dtype=np.int64),
        )
