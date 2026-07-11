"""Logged diagnostics — informational, NEVER gates (operator ruling, 2026-07-11).

DD04 listed profit factor / expectancy / regime stability as gate criteria, but they
are ABSENT from the frozen harness. Resolved: LOGGED DIAGNOSTICS, not gates. Profit
factor and expectancy are small helpers over the net-return stream; "regime stability"
folds into market-day conditioning (P&L split by index intraday direction). The binding
gate stays {beat-random, DSR, PBO, CPCV median/10th, path-positivity} — only beat-random
is new. Recorded as a resolved doc-vs-code discrepancy, same class as A-Z / truncation.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


def profit_factor(returns: Sequence[float]) -> float:
    """Gross profit / gross loss (a diagnostic).

    ``inf`` when there are gains and no losses; ``nan`` when the stream is empty or
    has no non-zero trades. Not a gate — reported alongside the verdict.
    """
    arr = np.asarray(returns, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    gains = float(arr[arr > 0.0].sum())
    losses = float(-arr[arr < 0.0].sum())
    if losses == 0.0:
        return float("inf") if gains > 0.0 else float("nan")
    return gains / losses


def expectancy(returns: Sequence[float]) -> float:
    """Mean per-period net return (a diagnostic); ``nan`` for an empty stream."""
    arr = np.asarray(returns, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    return float(arr.mean()) if arr.size else float("nan")


@dataclass(frozen=True, slots=True)
class MarketDayConditioning:
    """P&L split by index intraday direction — the 'regime stability' diagnostic.

    A residual-tilt tell: a truly market-neutral book's mean return should not depend
    on whether the index rose or fell that day. NOT a gate — truncation is the
    neutrality mechanism, and OLS/averaging washes out *conditional* tail-beta, so a
    non-zero spread is a flag to inspect, not a kill.
    """

    mean_up: float
    mean_down: float
    n_up: int
    n_down: int

    @property
    def spread(self) -> float:
        """``mean_up - mean_down`` — a large magnitude is a direction tilt to inspect."""
        return self.mean_up - self.mean_down


def market_day_conditioning(
    returns: Sequence[float], index_up: Sequence[bool]
) -> MarketDayConditioning:
    """Split the net-return stream by whether the index was up that day.

    Raises:
        ValueError: if ``returns`` and ``index_up`` do not align in length.
    """
    r = np.asarray(returns, dtype=np.float64)
    up = np.asarray(index_up, dtype=bool)
    if r.shape != up.shape:
        raise ValueError(f"returns {r.shape} and index_up {up.shape} must align")
    up_r, down_r = r[up], r[~up]
    return MarketDayConditioning(
        mean_up=float(up_r.mean()) if up_r.size else float("nan"),
        mean_down=float(down_r.mean()) if down_r.size else float("nan"),
        n_up=int(up.sum()),
        n_down=int((~up).sum()),
    )
