"""Check-1 port of the predecessor's robustness-battery tests (P2.5).

Ported from ``intraday-strategy-lab`` ``tests/unit/test_robustness.py`` at pinned
commit ``0c5c592`` (see ``src/vendored/VENDORED_FROM.md``). The three battery tests
below — and the ``_synthetic`` helper — are **byte-identical** to the source.

OMITTED (documented, not silent): ``test_two_engines_reconcile_on_reference_spec``
and ``test_two_engines_disagree_on_different_targets``. Both import the predecessor
*strategy* layer (``lab.research.strategies.reference.ReferenceMomentumSpec``,
``lab.research.strategies.adapter.signals_to_targets``) purely to synthesize target
positions — that layer is NOT the statistical harness and is deliberately not
vendored (it has no call site in this program). The two-engine reconciliation
function itself (``two_engines_agree`` / ``vectorized_backtest`` / ``run_backtest``)
is still exercised here by ``test_validation_core.py`` using hand-built targets, so
the vendored reconciliation is covered without the strategy dependency.

Carry-forward: the vendored single-name backtester will NOT reconcile the new
cross-sectional book — that two-engine check is new Phase-2 code (VENDORED_FROM.md).
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

from lab.core.types import BarInterval, Candle
from lab.research.validation.robustness import (
    fraction_positive,
    inject_ohlc_noise,
    monte_carlo_sign_flip,
)

IST = ZoneInfo("Asia/Kolkata")


def _synthetic() -> list[Candle]:
    rng = np.random.default_rng(13)
    candles: list[Candle] = []
    price = 100.0
    for day in (date(2024, 7, 15), date(2024, 7, 16), date(2024, 7, 18)):
        open_ts = datetime(day.year, day.month, day.day, 9, 15, tzinfo=IST)
        for bar in range(30):
            prev = price
            price = prev * math.exp(float(rng.normal(0.0, 0.003)))
            candles.append(
                Candle(
                    "SYN",
                    BarInterval.MIN_5,
                    open_ts + timedelta(minutes=5 * bar),
                    prev,
                    max(prev, price) + 0.3,
                    min(prev, price) - 0.3,
                    price,
                    1000,
                )
            )
    return candles


def test_monte_carlo_sign_flip_discriminates_edge() -> None:
    rng = np.random.default_rng(0)
    edge = rng.normal(0.01, 0.005, 200)  # clear positive edge (per-period Sharpe ~2)
    noise = rng.normal(0.0, 0.01, 200)  # no directional edge
    # A real edge clears the kill-gate bar; a no-edge series does not.
    assert monte_carlo_sign_flip(edge, n_shuffles=500) > 0.95
    assert monte_carlo_sign_flip(noise, n_shuffles=500) < 0.95


def test_inject_noise_keeps_valid_and_close() -> None:
    candles = _synthetic()
    perturbed = inject_ohlc_noise(candles, relative_scale=0.001, seed=1)
    assert len(perturbed) == len(candles)
    # Levels are jittered but close, and OHLC validity held (construction didn't raise).
    assert perturbed[0].close != candles[0].close
    assert abs(perturbed[0].close / candles[0].close - 1) < 0.01


def test_fraction_positive() -> None:
    assert fraction_positive([1.0, -1.0, 2.0, -3.0]) == 0.5
    assert fraction_positive([0.1, 0.2, float("nan")]) == 1.0
