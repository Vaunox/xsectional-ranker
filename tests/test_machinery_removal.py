"""Check 3 — machinery-removal falsification (Deep Dive 03, Completion Standard).

For EVERY adapter-surface function, a certifying check exercises it through
:class:`~xsranker.harness.adapter.HarnessAdapter` and asserts a real, known result.
This module proves each such check has teeth two ways:

* **positive control** — with the vendored machinery present, the check passes;
* **falsification** — stub the vendored entry point to raise, and the SAME check
  goes red.

A surface function whose certifying check survives its own removal certifies a
stub, not machinery — the predecessor's own historical failure mode. No exceptions:
the registry below must list every function the adapter fronts, and CI parametrizes
both directions over all of them.
"""

from __future__ import annotations

import tempfile
from collections.abc import Callable
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pytest

# Tests are exempt from the freeze boundary: they legitimately reach into vendored
# internals to build fixtures and to stub entry points.
from lab.core.types import BarInterval, Candle
from xsranker.core.config import load_settings
from xsranker.harness.adapter import HarnessAdapter

IST = ZoneInfo("Asia/Kolkata")


class MachineryRemovedError(RuntimeError):
    """Sentinel raised by a stubbed vendored entry point."""


def _removed(*_args: Any, **_kwargs: Any) -> Any:
    raise MachineryRemovedError("vendored entry point stubbed for falsification")


def _adapter() -> HarnessAdapter:
    return HarnessAdapter(load_settings())


def _windows(n: int) -> tuple[list[datetime], list[datetime]]:
    day0 = datetime(2024, 1, 1, tzinfo=IST)
    days: list[datetime] = []
    cur = day0
    while len(days) < n:
        if cur.weekday() < 5:
            days.append(cur)
        cur += timedelta(days=1)
    entries = [datetime.combine(d.date(), time(9, 15), tzinfo=IST) for d in days]
    exits = [datetime.combine(d.date(), time(15, 20), tzinfo=IST) for d in days]
    return entries, exits


def _candles(n: int) -> list[Candle]:
    base = datetime(2024, 1, 2, 9, 15, tzinfo=IST)
    price = 100.0
    out: list[Candle] = []
    for i in range(n):
        nxt = price * (1.0 + 0.001 * ((i % 5) - 2))
        out.append(
            Candle(
                "SYN",
                BarInterval.MIN_5,
                base + timedelta(minutes=5 * i),
                price,
                max(price, nxt) + 0.2,
                min(price, nxt) - 0.2,
                nxt,
                1000,
            )
        )
        price = nxt
    return out


# --- certifying checks (each asserts a real, known result through the adapter) -- #
def _c_per_period_sharpe(a: HarnessAdapter) -> None:
    assert a.per_period_sharpe([1, 2, 3, 4, 5]) == pytest.approx(3.0 / 2.5**0.5)


def _c_annualized_sharpe(a: HarnessAdapter) -> None:
    per = a.per_period_sharpe([1, 2, 3, 4, 5])
    assert a.annualized_sharpe([1, 2, 3, 4, 5], 4.0) == pytest.approx(per * 2.0)


def _c_probabilistic_sharpe_ratio(a: HarnessAdapter) -> None:
    assert a.probabilistic_sharpe_ratio(0.1, 0.0, 101, 0.0, 3.0) == pytest.approx(0.8407, abs=1e-3)


def _c_expected_max_sharpe(a: HarnessAdapter) -> None:
    # Monotone in trial count and strictly positive for >1 trial (teeth vs a constant).
    assert a.expected_max_sharpe(20.0, 0.1) > a.expected_max_sharpe(2.0, 0.1) > 0.0


def _c_deflated_sharpe_ratio(a: HarnessAdapter) -> None:
    few = a.deflated_sharpe_ratio(0.15, 300, 0.0, 3.0, effective_trials=2.0, trial_sharpe_std=0.05)
    many = a.deflated_sharpe_ratio(
        0.15, 300, 0.0, 3.0, effective_trials=60.0, trial_sharpe_std=0.05
    )
    assert 0.0 <= many < few <= 1.0


def _c_combinatorial_purged_cv(a: HarnessAdapter) -> None:
    entries, exits = _windows(24)
    returns = [0.01, -0.005] * 12
    result = a.combinatorial_purged_cv(
        returns, entries, exits, n_groups=6, k_test_groups=2, periods_per_year=252.0
    )
    assert result.n_finite_paths > 0


def _c_cpcv_distribution_summary(a: HarnessAdapter) -> None:
    assert a.cpcv_distribution_summary([1.0, -1.0, 2.0]).positive_fraction == pytest.approx(2 / 3)


def _c_probability_of_backtest_overfitting(a: HarnessAdapter) -> None:
    entries, exits = _windows(16)
    matrix = [[0.01, -0.002, 0.003, 0.0] for _ in range(16)]
    result = a.probability_of_backtest_overfitting(matrix, entries, exits, n_splits=8)
    assert 0.0 <= result.pbo <= 1.0


def _c_trial_ledger(a: HarnessAdapter) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ledger = a.trial_ledger(Path(tmp) / "trials")
        base = [0.01, -0.02, 0.015, 0.0, -0.01]
        ledger.log_trial("S", {"i": 0}, base)
        ledger.log_trial("S", {"i": 1}, base)
        assert ledger.effective_trials() == pytest.approx(1.0, abs=0.01)


def _c_load_cost_model(a: HarnessAdapter) -> None:
    assert a.load_cost_model().round_trip_cost(100_000, 100_000) == pytest.approx(
        182.4452, abs=1e-3
    )


def _c_trade_cost_fraction(a: HarnessAdapter) -> None:
    cm = a.load_cost_model()
    assert a.trade_cost_fraction(cm, 100_000, 100.0, 1_000_000.0) > 0.0


def _c_monte_carlo_sign_flip(a: HarnessAdapter) -> None:
    edge = [0.01, 0.012, 0.009, 0.011, 0.013, 0.008] * 8
    assert a.monte_carlo_sign_flip(edge, n_shuffles=200) > 0.9


def _c_inject_ohlc_noise(a: HarnessAdapter) -> None:
    candles = _candles(20)
    perturbed = a.inject_ohlc_noise(candles, relative_scale=0.001)
    assert len(perturbed) == len(candles) and perturbed[0].close != candles[0].close


def _c_fraction_positive(a: HarnessAdapter) -> None:
    assert a.fraction_positive([1.0, -1.0, 2.0, -3.0]) == 0.5


#: surface name -> (vendored entry point to stub, certifying check).
SURFACE: dict[str, tuple[str, Callable[[HarnessAdapter], None]]] = {
    "per_period_sharpe": ("lab.research.validation.sharpe.per_period_sharpe", _c_per_period_sharpe),
    "annualized_sharpe": ("lab.research.validation.sharpe.annualized_sharpe", _c_annualized_sharpe),
    "probabilistic_sharpe_ratio": (
        "lab.research.validation.metrics.probabilistic_sharpe_ratio",
        _c_probabilistic_sharpe_ratio,
    ),
    "expected_max_sharpe": (
        "lab.research.validation.metrics.expected_max_sharpe",
        _c_expected_max_sharpe,
    ),
    "deflated_sharpe_ratio": (
        "lab.research.validation.metrics.deflated_sharpe_ratio",
        _c_deflated_sharpe_ratio,
    ),
    "combinatorial_purged_cv": (
        "lab.research.validation.cpcv.combinatorial_purged_cv",
        _c_combinatorial_purged_cv,
    ),
    "cpcv_distribution_summary": (
        "lab.research.validation.cpcv.cpcv_distribution_summary",
        _c_cpcv_distribution_summary,
    ),
    "probability_of_backtest_overfitting": (
        "lab.research.validation.pbo.probability_of_backtest_overfitting",
        _c_probability_of_backtest_overfitting,
    ),
    "trial_ledger": ("lab.research.trials.ledger.TrialLedger", _c_trial_ledger),
    "load_cost_model": ("lab.research.validation.costs.load_cost_model", _c_load_cost_model),
    "trade_cost_fraction": (
        "lab.research.validation.costs.trade_cost_fraction",
        _c_trade_cost_fraction,
    ),
    "monte_carlo_sign_flip": (
        "lab.research.validation.robustness.monte_carlo_sign_flip",
        _c_monte_carlo_sign_flip,
    ),
    "inject_ohlc_noise": (
        "lab.research.validation.robustness.inject_ohlc_noise",
        _c_inject_ohlc_noise,
    ),
    "fraction_positive": (
        "lab.research.validation.robustness.fraction_positive",
        _c_fraction_positive,
    ),
}


@pytest.mark.parametrize("name", sorted(SURFACE))
def test_certifying_check_passes_with_machinery(name: str) -> None:
    """Positive control: with the vendored machinery present, the check passes."""
    _target, certify = SURFACE[name]
    certify(_adapter())


@pytest.mark.falsification
@pytest.mark.parametrize("name", sorted(SURFACE))
def test_certifying_check_goes_red_without_machinery(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Falsification: stub the vendored entry point → the same check goes red."""
    target, certify = SURFACE[name]
    monkeypatch.setattr(target, _removed, raising=True)
    with pytest.raises(
        (MachineryRemovedError, AssertionError, AttributeError, TypeError, ValueError)
    ):
        certify(_adapter())
