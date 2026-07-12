"""Execution-Aware Dollar Neutrality — the frozen truncation (murder-board #1/#2/#3).

Neutrality is enforced in EXECUTION, not construction or attribution. The REQUIRED
(frozen) form:

1. Each name is capped at the pessimistic participation rule (``max_fill_inr``,
   ≤ 1% of its entry-window traded value).
2. A leg deploys its risk-parity weights ``w_i`` (Σ = 1 within the leg) at some gross
   ``G``; name ``i`` then absorbs ``w_i · G``, which must not exceed its cap ``c_i``.
   So the leg's maximum feasible gross at its risk-parity weights is
   ``G_leg = min_i(c_i / w_i)`` — the point where the first name hits its cap.
3. The **smaller leg sets book gross**: ``gross = min(G_long, G_short)`` (dollar-
   neutral). The larger leg is scaled down PRO-RATA to this gross — every name keeps
   its risk-parity weight; only leg leverage shrinks. **k is fixed; names are never
   dropped to rebalance** (rank-preserving/floating-k is FORBIDDEN — it corrupts the
   null and force-concentrates risk, Concession #3).
4. If ``gross`` falls below the pre-registered gross floor, the **day is dropped**
   (never names).

Resolved spec ambiguity (frozen 2026-07-11): the deep dive's "sum the caps per leg"
shorthand and the cap-respecting ``min(c_i/w_i)`` coincide only for equal-cap weights;
under risk-parity weights (Concession #5), summing caps and redistributing by weight
can hand a name more than its own 1%-participation cap (an un-fillable order). So the
leg gross is ``min_i(cap_i / weight_i)`` — the largest gross at which no name breaches
its cap at its risk-parity weight. Honors BOTH constraints. (Deep Dive 02, resolved
2026-07-11; operator-confirmed.)
"""

from __future__ import annotations

from collections.abc import Sequence

from xsranker.core.logging import get_logger
from xsranker.execution.book import Book, Candidate, DayDropped, Position, Side

_log = get_logger("execution.truncation")


def _leg_max_gross(leg: Sequence[Candidate]) -> float:
    """Largest gross a leg can deploy at its risk-parity weights without breaching a cap."""
    return min(c.max_fill_inr / c.risk_weight for c in leg)


def truncate(
    longs: Sequence[Candidate], shorts: Sequence[Candidate], *, gross_floor_inr: float
) -> Book | DayDropped:
    """Apply Execution-Aware Dollar Neutrality; return a matched Book or a dropped day.

    ``longs``/``shorts`` are the fixed-k legs with risk-parity weights (each leg's
    weights sum to 1) and per-name ₹ caps. k is preserved; the day is dropped whole
    if the neutral gross is below the floor.
    """
    if not longs or not shorts:
        return DayDropped("empty leg (no eligible names)")
    for leg_name, leg in (("long", longs), ("short", shorts)):
        total = sum(c.risk_weight for c in leg)
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"{leg_name} leg risk weights must sum to 1 (got {total})")
        if any(c.risk_weight <= 0.0 for c in leg):
            raise ValueError(f"{leg_name} leg has a non-positive risk weight")

    g_long = _leg_max_gross(longs)
    g_short = _leg_max_gross(shorts)
    gross = min(g_long, g_short)  # smaller leg sets gross (dollar-neutral)

    if gross < gross_floor_inr:
        # DEBUG, not INFO: a below-floor drop is a routine, expected event and fires on EVERY
        # sub-floor null rejection (build_random_book's loop) — logging each at INFO floods the
        # hot path (~500k lines/run). The INFO-level summaries are the arm's day-drop fraction
        # and the null-health aggregate (run_arm), not the per-occurrence drop.
        _log.debug("day_dropped", reason="below_gross_floor", gross=gross, floor=gross_floor_inr)
        return DayDropped(f"gross {gross:.2f} < floor {gross_floor_inr:.2f} (liquidity too thin)")

    def _positions(leg: Sequence[Candidate], side: Side) -> tuple[Position, ...]:
        return tuple(
            Position(c.symbol, side, c.sector, c.risk_weight, c.risk_weight * gross) for c in leg
        )

    return Book(
        longs=_positions(longs, Side.LONG),
        shorts=_positions(shorts, Side.SHORT),
        gross_inr=gross,
    )
