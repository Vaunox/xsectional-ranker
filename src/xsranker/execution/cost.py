"""Cost corridor — bounded, not point-estimated (murder-board: OHLCV can't measure depth).

Every study runs twice, **composing the frozen** ``round_trip_cost`` with two bounds. The
mode is config-selected (``CostCorridorConfig.mode``):

* **FIXED_SPREAD (candidate #2+, the live standard)** — verified statutory fees + a pinned,
  uniform **fixed** round-trip spread (optimistic / pessimistic bps). The square-root impact
  term is **zeroed**: the fixed spread IS the conservative slippage envelope, so participation
  no longer drives a slippage add-on, and **Corwin-Schultz is never touched**. This is the
  RESEARCH_FINDINGS §7.3 standard cost model that retires the CS over-read (§5.3) which
  produced candidate #1's inflated -74/-220 figures.
* **CORWIN_SCHULTZ (historical only)** — the raw Corwin-Schultz spread x {1x, 3x}, with the
  base model's square-root impact term. Retained **solely** to regenerate candidate #1's
  ledger streams at historical fidelity (the cost model in force when they were run). It is
  NEVER used for a live verdict; the regen script pins this mode explicitly.

A single point estimate is FORBIDDEN. All spread params are frozen, never swept to conjure a
flattering fill. The frozen ``CostModel`` is composed via ``dataclasses.replace`` — never edited.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from xsranker.execution.config import CORWIN_SCHULTZ, FIXED_SPREAD, CostCorridorConfig
from xsranker.harness.adapter import CostModel

#: One basis point as a fraction.
_BPS = 1e-4


@dataclass(frozen=True, slots=True)
class CostBounds:
    """The two round-trip cost fractions bounding the corridor (pessimistic >= optimistic)."""

    optimistic_fraction: float
    pessimistic_fraction: float


def _fixed_spread_bounds(
    base_cost_model: CostModel,
    *,
    notional: float,
    optimistic_spread_bps: float,
    pessimistic_spread_bps: float,
) -> CostBounds:
    """Fees + a fixed round-trip spread at both bounds; impact term ZEROED (no CS, no depth).

    A round-trip proportional spread of ``s`` bps is realised as a per-side base slippage of
    ``s/2`` bps (paid on the buy and the sell), with ``slippage_impact_coefficient = 0`` so
    participation never adds slippage. The statutory charges of the frozen model are unchanged.
    """
    optimistic = replace(
        base_cost_model,
        slippage_base_rate=optimistic_spread_bps * _BPS / 2.0,
        slippage_impact_coefficient=0.0,
    )
    pessimistic = replace(
        base_cost_model,
        slippage_base_rate=pessimistic_spread_bps * _BPS / 2.0,
        slippage_impact_coefficient=0.0,
    )
    return CostBounds(
        optimistic_fraction=optimistic.round_trip_cost_fraction(notional),
        pessimistic_fraction=pessimistic.round_trip_cost_fraction(notional),
    )


def _corwin_schultz_bounds(
    base_cost_model: CostModel,
    spread: float,
    *,
    notional: float,
    participation: float,
    participation_cap: float,
    optimistic_multiplier: float,
    pessimistic_multiplier: float,
) -> CostBounds:
    """Corwin-Schultz spread x {opt, pess} multiplier (HISTORICAL — candidate #1 regen only).

    The per-side slippage of the frozen cost model is set to the estimated half-spread x
    multiplier; the pessimistic bound evaluates the base model's square-root impact at the
    participation cap (worst-case slippage). Behaviourally identical to the pre-swap corridor.
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


def cost_corridor(
    base_cost_model: CostModel,
    cost_cfg: CostCorridorConfig,
    *,
    spread: float,
    notional: float,
    participation: float,
    participation_cap: float,
) -> CostBounds:
    """Round-trip cost fraction at both corridor bounds, dispatched by ``cost_cfg.mode``.

    ``FIXED_SPREAD`` (live) ignores ``spread`` / ``participation`` entirely — it is fees + a
    fixed bps spread. ``CORWIN_SCHULTZ`` (historical regen) uses the estimated ``spread``.

    Raises:
        ValueError: if ``cost_cfg.mode`` is not a recognised corridor mode.
    """
    if cost_cfg.mode == FIXED_SPREAD:
        return _fixed_spread_bounds(
            base_cost_model,
            notional=notional,
            optimistic_spread_bps=cost_cfg.optimistic_spread_bps,
            pessimistic_spread_bps=cost_cfg.pessimistic_spread_bps,
        )
    if cost_cfg.mode == CORWIN_SCHULTZ:
        return _corwin_schultz_bounds(
            base_cost_model,
            spread,
            notional=notional,
            participation=participation,
            participation_cap=participation_cap,
            optimistic_multiplier=cost_cfg.optimistic_spread_multiplier,
            pessimistic_multiplier=cost_cfg.pessimistic_spread_multiplier,
        )
    raise ValueError(f"unknown cost corridor mode: {cost_cfg.mode!r}")
