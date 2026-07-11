"""Cost corridor — bounded, not point-estimated (murder-board: OHLCV can't measure depth).

Every study runs twice, **composing the frozen** ``round_trip_cost`` with two spread
inputs (the frozen cost primitive is unchanged; the corridor is the new wrapper that
sets its per-side slippage from the estimated spread):

* **Optimistic** — the raw Corwin-Schultz implied spread (x 1.0), full fill.
* **Pessimistic** — ~3x the implied spread and the ≤1%-volume participation cap, so
  the frozen square-root impact term is evaluated at the cap (max slippage).

A single point estimate is FORBIDDEN. The cap and multipliers are frozen, never swept
to conjure a flattering fill.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from xsranker.harness.adapter import CostModel


@dataclass(frozen=True, slots=True)
class CostBounds:
    """The two round-trip cost fractions bounding the corridor (pessimistic >= optimistic)."""

    optimistic_fraction: float
    pessimistic_fraction: float


def cost_corridor(
    base_cost_model: CostModel,
    spread: float,
    *,
    notional: float,
    participation: float,
    participation_cap: float,
    optimistic_multiplier: float,
    pessimistic_multiplier: float,
) -> CostBounds:
    """Round-trip cost fraction at both corridor bounds for one trade.

    The per-side slippage of the frozen cost model is replaced by the estimated
    half-spread x multiplier (``dataclasses.replace`` builds a new frozen instance —
    the vendored class is composed, never edited). Statutory charges are unchanged.
    """
    half = spread / 2.0
    optimistic = replace(base_cost_model, slippage_base_rate=half * optimistic_multiplier)
    pessimistic = replace(base_cost_model, slippage_base_rate=half * pessimistic_multiplier)
    return CostBounds(
        optimistic_fraction=optimistic.round_trip_cost_fraction(
            notional, participation=participation
        ),
        pessimistic_fraction=pessimistic.round_trip_cost_fraction(
            notional, participation=participation_cap
        ),
    )
