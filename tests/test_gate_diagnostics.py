"""Logged diagnostics — hand-computed teeth. These are NOT gates (operator ruling)."""

from __future__ import annotations

import math

from xsranker.gate.diagnostics import expectancy, market_day_conditioning, profit_factor


def test_profit_factor_gross_profit_over_gross_loss() -> None:
    # gains 3 + 1 = 4; losses |-2| = 2  ->  2.0
    assert profit_factor([3.0, -2.0, 1.0]) == 2.0


def test_profit_factor_no_losses_is_inf() -> None:
    assert profit_factor([1.0, 2.0]) == float("inf")


def test_profit_factor_empty_is_nan() -> None:
    assert math.isnan(profit_factor([]))


def test_expectancy_is_the_mean() -> None:
    assert expectancy([1.0, 2.0, 3.0]) == 2.0


def test_expectancy_empty_is_nan() -> None:
    assert math.isnan(expectancy([]))


def test_market_day_conditioning_splits_by_index_direction() -> None:
    # returns [1,2,3,4] with index up on days 0 and 2:
    #   mean_up = (1+3)/2 = 2 ; mean_down = (2+4)/2 = 3 ; spread = -1
    mdc = market_day_conditioning([1.0, 2.0, 3.0, 4.0], [True, False, True, False])
    assert mdc.mean_up == 2.0
    assert mdc.mean_down == 3.0
    assert mdc.n_up == 2
    assert mdc.n_down == 2
    assert mdc.spread == -1.0


def test_market_day_conditioning_rejects_misaligned_inputs() -> None:
    import pytest

    with pytest.raises(ValueError):
        market_day_conditioning([1.0, 2.0, 3.0], [True, False])
