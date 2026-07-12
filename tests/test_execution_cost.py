# mypy: disable-error-code="no-untyped-def, no-any-return, no-untyped-call"
"""Cost corridor tests — dispatches fees+fixed (live) vs Corwin-Schultz (historical regen)."""

from __future__ import annotations

from xsranker.core.config import load_settings
from xsranker.execution.config import CORWIN_SCHULTZ, FIXED_SPREAD, CostCorridorConfig
from xsranker.execution.cost import cost_corridor
from xsranker.harness.adapter import HarnessAdapter

_CS = CostCorridorConfig(
    mode=CORWIN_SCHULTZ,
    optimistic_spread_multiplier=1.0,
    pessimistic_spread_multiplier=3.0,
    optimistic_spread_bps=5.0,
    pessimistic_spread_bps=18.0,
)
_FIXED = CostCorridorConfig(
    mode=FIXED_SPREAD,
    optimistic_spread_multiplier=1.0,
    pessimistic_spread_multiplier=3.0,
    optimistic_spread_bps=5.0,
    pessimistic_spread_bps=18.0,
)


def _cost_model():
    return HarnessAdapter(load_settings()).load_cost_model()


def _bounds(cfg, *, spread, participation):
    return cost_corridor(
        _cost_model(),
        cfg,
        spread=spread,
        notional=100_000.0,
        participation=participation,
        participation_cap=0.01,
    )


# --------------------------------------------------------------------------- #
# CORWIN_SCHULTZ mode — historical (candidate #1 ledger regen only)             #
# --------------------------------------------------------------------------- #


def test_cs_pessimistic_exceeds_optimistic() -> None:
    b = _bounds(_CS, spread=0.002, participation=0.001)
    assert b.pessimistic_fraction > b.optimistic_fraction > 0.0


def test_cs_composes_frozen_statutory_charges() -> None:
    # spread 0 + no participation -> the optimistic bound is still strictly positive (the
    # frozen statutory brokerage/STT/etc.).
    b = _bounds(_CS, spread=0.0, participation=0.0)
    assert b.optimistic_fraction > 0.0


def test_cs_wider_spread_raises_both_bounds() -> None:
    narrow = _bounds(_CS, spread=0.001, participation=0.001)
    wide = _bounds(_CS, spread=0.004, participation=0.001)
    assert wide.optimistic_fraction > narrow.optimistic_fraction
    assert wide.pessimistic_fraction > narrow.pessimistic_fraction


# --------------------------------------------------------------------------- #
# FIXED_SPREAD mode — the candidate #2+ live standard (fees + fixed bps, no CS) #
# --------------------------------------------------------------------------- #


def test_fixed_pessimistic_exceeds_optimistic_and_positive() -> None:
    b = _bounds(_FIXED, spread=0.002, participation=0.001)
    assert b.pessimistic_fraction > b.optimistic_fraction > 0.0


def test_fixed_cost_is_independent_of_cs_spread_and_participation() -> None:
    """THE GUARD: the fixed corridor NEVER reads the CS spread or the participation, so
    candidate #2's cost cannot inherit the Corwin-Schultz over-read. Wildly different spread
    and participation inputs produce byte-identical bounds."""
    a = _bounds(_FIXED, spread=0.0, participation=0.0)
    b = _bounds(_FIXED, spread=0.05, participation=0.5)  # huge CS spread + full participation
    assert a == b


def test_fixed_spread_magnitude_is_the_pinned_5_and_18_bps() -> None:
    # fees are identical at both bounds, so the gap between them is exactly the spread
    # difference: 18 - 5 = 13 bps round-trip.
    b = _bounds(_FIXED, spread=0.0, participation=0.0)
    assert abs((b.pessimistic_fraction - b.optimistic_fraction) - 13e-4) < 1e-7
    # optimistic = fees + 5 bps round-trip; fees are a few bps, so it sits in a tight band.
    assert 9e-4 < b.optimistic_fraction < 14e-4
