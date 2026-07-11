"""Shared pytest configuration + fixtures for the verification gate and Layer 1.

Threading is pinned to one thread BEFORE numpy/scipy import anywhere, so
golden-master reductions are order-deterministic and bit-for-bit reconciliation
does not trip on a ~1e-13 thread-reduction difference (Deep Dive 03, Check 4).
Best-effort at import time; CI also sets OMP_NUM_THREADS=1 in the job env.

Fixtures:
* ``build_ohlcv`` — synthetic OHLCV builder so Layer-1 correctness/leakage tests
  run WITHOUT the external cache (i.e. in CI).
* ``cache_config`` / ``data_ctx`` — real-cache fixtures that SKIP when the cache is
  absent (CI), so gate-zero and broker tests run locally but never fail CI.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from datetime import date
from typing import TYPE_CHECKING

for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_var, "1")

import numpy as np  # noqa: E402  (must follow the thread-pin above)
import pytest  # noqa: E402

from xsranker.core.types import IST_OFFSET_NS, OHLCV  # noqa: E402

if TYPE_CHECKING:
    from xsranker.data.config import DataUniverseConfig
    from xsranker.data.factory import DataContext

OhlcvBuilder = Callable[..., OHLCV]


def _ist_timestamps(
    dates: Sequence[date], bars_per_day: int, start_min: int, step: int
) -> np.ndarray:
    stamps: list[np.datetime64] = []
    for d in dates:
        day = np.datetime64(d, "ns")
        for b in range(bars_per_day):
            secs = (start_min + b * step) * 60
            wall = day + np.timedelta64(secs, "s").astype("timedelta64[ns]")
            stamps.append(wall - np.timedelta64(IST_OFFSET_NS, "ns"))
    return np.array(stamps, dtype="datetime64[ns]")


@pytest.fixture
def build_ohlcv() -> OhlcvBuilder:
    """Factory: build a synthetic multi-day 5-min OHLCV series.

    ``closes``/``volumes`` (flat, length days*bars_per_day) override the defaults;
    otherwise a gentle deterministic ramp is used. High/low bracket open/close.
    """

    def _build(
        symbol: str = "SYN",
        dates: Sequence[date] | None = None,
        *,
        bars_per_day: int = 6,
        start_min: int = 555,  # 09:15 IST
        step: int = 5,
        closes: Sequence[float] | None = None,
        opens: Sequence[float] | None = None,
        volumes: Sequence[float] | None = None,
        base: float = 100.0,
    ) -> OHLCV:
        dates = (
            list(dates)
            if dates is not None
            else [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
        )
        n = len(dates) * bars_per_day
        ts = _ist_timestamps(dates, bars_per_day, start_min, step)
        close = (
            base + 0.1 * np.arange(n, dtype=np.float64)
            if closes is None
            else np.asarray(closes, dtype=np.float64)
        )
        if opens is not None:
            open_ = np.asarray(opens, dtype=np.float64)
        else:
            open_ = np.empty(n, dtype=np.float64)
            open_[0] = close[0]
            open_[1:] = close[:-1]
        high = np.maximum(open_, close) + 0.5
        low = np.minimum(open_, close) - 0.5
        vol = (
            np.full(n, 1000, dtype=np.int64)
            if volumes is None
            else np.asarray(volumes, dtype=np.int64)
        )
        return OHLCV(symbol, "5minute", ts, open_, high, low, close, vol)

    return _build


@pytest.fixture
def cache_config() -> DataUniverseConfig:
    """Real Layer-1 config; SKIP when the external Parquet cache is absent (CI)."""
    from xsranker.core.config import load_settings
    from xsranker.data.config import load_data_universe_config

    cfg = load_data_universe_config(load_settings())
    if not cfg.data.cache_path.exists():
        pytest.skip("external Parquet cache not available (CI / no local cache)")
    return cfg


@pytest.fixture
def data_ctx() -> DataContext:
    """Wired DataContext over the real cache; SKIP when the cache is absent."""
    from xsranker.core.config import load_settings
    from xsranker.data.config import load_data_universe_config
    from xsranker.data.factory import build_data_context

    settings = load_settings()
    if not load_data_universe_config(settings).data.cache_path.exists():
        pytest.skip("external Parquet cache not available (CI / no local cache)")
    return build_data_context(settings)
