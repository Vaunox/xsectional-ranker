# mypy: disable-error-code="no-untyped-def, no-any-return, no-untyped-call"
"""Cost corridor tests — composes the frozen round_trip_cost at both bounds."""

from __future__ import annotations

from xsranker.core.config import load_settings
from xsranker.execution.cost import cost_corridor
from xsranker.harness.adapter import HarnessAdapter


def _cost_model():
    return HarnessAdapter(load_settings()).load_cost_model()


def test_pessimistic_exceeds_optimistic() -> None:
    bounds = cost_corridor(
        _cost_model(),
        spread=0.002,
        notional=100_000.0,
        participation=0.001,
        participation_cap=0.01,
        optimistic_multiplier=1.0,
        pessimistic_multiplier=3.0,
    )
    assert bounds.pessimistic_fraction > bounds.optimistic_fraction > 0.0


def test_corridor_composes_frozen_statutory_charges() -> None:
    # With spread 0 and no participation, the optimistic bound is the frozen statutory
    # + base cost with zero spread-slippage -> strictly positive (brokerage/STT/etc.).
    bounds = cost_corridor(
        _cost_model(),
        spread=0.0,
        notional=100_000.0,
        participation=0.0,
        participation_cap=0.01,
        optimistic_multiplier=1.0,
        pessimistic_multiplier=3.0,
    )
    assert bounds.optimistic_fraction > 0.0  # statutory charges from the frozen model


def test_wider_spread_raises_both_bounds() -> None:
    narrow = cost_corridor(
        _cost_model(),
        spread=0.001,
        notional=100_000.0,
        participation=0.001,
        participation_cap=0.01,
        optimistic_multiplier=1.0,
        pessimistic_multiplier=3.0,
    )
    wide = cost_corridor(
        _cost_model(),
        spread=0.004,
        notional=100_000.0,
        participation=0.001,
        participation_cap=0.01,
        optimistic_multiplier=1.0,
        pessimistic_multiplier=3.0,
    )
    assert wide.optimistic_fraction > narrow.optimistic_fraction
    assert wide.pessimistic_fraction > narrow.pessimistic_fraction
