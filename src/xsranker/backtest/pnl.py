"""Book -> per-day NET RETURN — the P&L engine (return per unit of one leg's gross).

For a dollar-neutral, risk-parity-weighted book (each leg's weights sum to 1), the
realized return on a leg's gross ``G`` over entry->close is::

    net = ( Σ_long  wᵢ·holdᵢ  -  Σ_short wⱼ·holdⱼ )   # the market-neutral spread P&L
          - ( Σ_long wᵢ·costᵢ +  Σ_short wⱼ·costⱼ )   # round-trip cost, BOTH legs

The short leg profits when its names FALL, hence the ``-holdⱼ``; cost is always a
subtraction on both legs. A uniform (common-factor) move cancels in the spread, leaving
only cost — the neutrality property the hand-worked tests pin. Scale (whether per one
leg's ``G`` or the total ``2G``) is a positive constant, so it changes neither the
Sharpe/percentile/PBO the gate uses nor the sign of the verdict.

The engine is PURE: it takes pre-computed hold returns and per-position cost fractions
(one corridor bound at a time), so it is hand-checkable and free of any data/cost
plumbing. The harness computes the cost fractions via the frozen cost corridor and calls
this once per bound.
"""

from __future__ import annotations

from collections.abc import Mapping

from xsranker.execution.book import Book, Position


def _leg_return(positions: tuple[Position, ...], direction: float, holds, costs) -> float:  # type: ignore[no-untyped-def]
    total = 0.0
    for p in positions:
        if p.symbol not in holds:
            raise KeyError(f"no hold return for book symbol {p.symbol!r}")
        if p.symbol not in costs:
            raise KeyError(f"no cost fraction for book symbol {p.symbol!r}")
        total += p.weight * (direction * holds[p.symbol] - costs[p.symbol])
    return total


def book_net_return(
    book: Book,
    hold_by_symbol: Mapping[str, float],
    cost_frac_by_symbol: Mapping[str, float],
) -> float:
    """Net entry->close return of ``book`` (one cost-corridor bound), on one leg's gross.

    Args:
        book: the day's matched long/short book (risk-parity weights, Σ=1 per leg).
        hold_by_symbol: entry->close hold return per symbol (from ``hold_return``).
        cost_frac_by_symbol: round-trip cost fraction per symbol at ONE corridor bound.

    Raises:
        KeyError: if a book symbol is missing a hold return or a cost fraction (fail
            closed — the harness must supply both for every held name).
    """
    long_leg = _leg_return(book.longs, +1.0, hold_by_symbol, cost_frac_by_symbol)
    short_leg = _leg_return(book.shorts, -1.0, hold_by_symbol, cost_frac_by_symbol)
    return long_leg + short_leg
