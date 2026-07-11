"""Tests for the conservative circuit-lock filter (teeth on synthetic bars)."""

from __future__ import annotations

import numpy as np

from xsranker.core.types import OHLCV
from xsranker.data.config import CircuitConfig
from xsranker.data.universe.circuit import is_circuit_locked_at

CFG = CircuitConfig(recent_range_lookback_bars=5, min_range_ratio=0.10, low_volume_pctile=0.10)


def _bars(highs: list[float], lows: list[float], vols: list[int]) -> OHLCV:
    n = len(highs)
    ts = np.arange(n).astype("datetime64[s]").astype("datetime64[ns]")
    close = (np.array(highs) + np.array(lows)) / 2.0
    return OHLCV(
        "X",
        "5minute",
        ts,
        close.copy(),
        np.array(highs),
        np.array(lows),
        close,
        np.array(vols, dtype=np.int64),
    )


def test_near_zero_range_entry_is_locked() -> None:
    # 5 normal bars (range 1.0) then an entry bar with range 0.01 -> range lock
    highs = [100.5] * 5 + [100.005]
    lows = [99.5] * 5 + [99.995]
    ohlcv = _bars(highs, lows, [1000] * 6)
    assert is_circuit_locked_at(ohlcv, 5, CFG) is True


def test_normal_entry_is_not_locked() -> None:
    highs = [100.5] * 6
    lows = [99.5] * 6
    ohlcv = _bars(highs, lows, [1000] * 6)
    assert is_circuit_locked_at(ohlcv, 5, CFG) is False


def test_insufficient_history_is_conservatively_locked() -> None:
    ohlcv = _bars([100.5] * 4, [99.5] * 4, [1000] * 4)
    # entry_idx 2 with lookback 5 -> not enough trailing bars -> drop (conservative)
    assert is_circuit_locked_at(ohlcv, 2, CFG) is True


def test_low_volume_and_tight_range_flagged() -> None:
    # normal ranges, but the entry bar is unusually quiet AND tighter than typical
    highs = [100.5] * 5 + [100.2]
    lows = [99.5] * 5 + [99.8]  # entry range 0.4 < recent median 1.0
    ohlcv = _bars(highs, lows, [1000, 1000, 1000, 1000, 1000, 1])  # entry volume tiny
    assert is_circuit_locked_at(ohlcv, 5, CFG) is True
