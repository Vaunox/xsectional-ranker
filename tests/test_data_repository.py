# mypy: disable-error-code="no-untyped-def, no-any-return"
"""Tests for the Repository: raw passthrough, adjusted identity, versioned immutability."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pytest

from xsranker.core.types import OHLCV
from xsranker.data.repository import Repository


class _FakeBroker:
    """Minimal BrokerAdapter returning one synthetic series (no external cache)."""

    def __init__(self, ohlcv: OHLCV) -> None:
        self._ohlcv = ohlcv

    def available_symbols(self) -> list[str]:
        return [self._ohlcv.symbol]

    def trading_dates(self, symbol: str) -> list[date]:
        return [date(2024, 1, 2)]

    def load(self, symbol: str, *, start: date | None = None, end: date | None = None) -> OHLCV:
        return self._ohlcv


def _synth(build_ohlcv) -> OHLCV:
    return build_ohlcv(bars_per_day=3)


def test_raw_and_adjusted_identity_phase1(build_ohlcv, tmp_path: Path) -> None:
    ohlcv = _synth(build_ohlcv)
    repo = Repository(_FakeBroker(ohlcv), tmp_path / "derived")
    raw = repo.raw("SYN")
    adj = repo.adjusted("SYN")  # Phase-1 no-op provider
    assert np.array_equal(raw.close, adj.close)
    assert np.array_equal(raw.volume, adj.volume)


def test_derived_is_immutable_corrections_are_new_versions(build_ohlcv, tmp_path: Path) -> None:
    ohlcv = _synth(build_ohlcv)
    repo = Repository(_FakeBroker(ohlcv), tmp_path / "derived")

    repo.persist_derived("SYN", ohlcv, version="v1")
    back = repo.load_derived("SYN", version="v1")
    assert np.array_equal(back.close, ohlcv.close)

    # re-writing the SAME version is refused (immutability)
    with pytest.raises(FileExistsError, match="immutable"):
        repo.persist_derived("SYN", ohlcv, version="v1")

    # a correction goes to a NEW version; v1 is untouched
    corrected = OHLCV(
        ohlcv.symbol,
        ohlcv.interval,
        ohlcv.timestamp,
        ohlcv.open,
        ohlcv.high,
        ohlcv.low,
        ohlcv.close * 1.01,
        ohlcv.volume,
    )
    repo.persist_derived("SYN", corrected, version="v2")
    assert np.array_equal(repo.load_derived("SYN", version="v1").close, ohlcv.close)
    assert np.allclose(repo.load_derived("SYN", version="v2").close, ohlcv.close * 1.01)
