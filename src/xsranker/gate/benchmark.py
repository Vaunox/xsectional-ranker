"""Beat-random-percentile — the ONE new gate criterion (Layer 3).

Everything else in the gate is the frozen harness, unedited, reached through the
adapter. This is the only new benchmark: a study's realized net return is judged
against the Global Null Panel — random long-k/short-k books pushed through the
IDENTICAL execution — not against zero.

Operator ruling (2026-07-11): each arm's per-day quantity is redefined as **net minus
the null median** (:func:`excess_over_null_median`) — the isolated selection alpha —
and that excess stream feeds the imported CPCV/DSR/PBO. The arm must additionally
clear a pre-registered percentile of the null aggregate distribution
(:func:`beat_random_percentile`): under H0 (ranked ≈ random) the signal is one more
draw, so ``P(beat_percentile ≥ P) = (100 - P)/100`` — the per-arm false-positive rate
the threshold pins a-priori.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

import numpy as np

from xsranker.core.types import FloatArray


@dataclass(frozen=True, slots=True)
class BeatRandomResult:
    """Where an arm's aggregate net return lands in the null aggregate distribution."""

    signal_aggregate: float
    #: The ``threshold``-th percentile of the null aggregate distribution (the bar).
    null_bar: float
    #: The signal's percentile within the null distribution, in ``[0, 100]``.
    beat_percentile: float
    threshold: float
    n_draws: int
    passed: bool
    #: Per-day net-minus-null-median stream (Ruling 1) — feeds the imported criteria.
    excess_stream: tuple[float, ...]


def excess_over_null_median(
    signal_by_day: Mapping[date, float],
    null_by_day: Mapping[date, Sequence[float]],
) -> list[float]:
    """Per surviving day: signal net return minus that day's null MEDIAN.

    The operator-ruled quantity (2026-07-11): selection alpha over an execution-matched
    random book, stripped of the per-day structure/liquidity/survivorship luck that
    ranked and random share. This — never the raw net — is what the imported
    CPCV/DSR/PBO deflate. Days are taken in sorted (chronological) order.
    """
    out: list[float] = []
    for day in sorted(signal_by_day):
        null = np.asarray(null_by_day[day], dtype=np.float64)
        if null.size == 0:
            raise ValueError(f"empty null draws for {day.isoformat()}")
        out.append(float(signal_by_day[day] - np.median(null)))
    return out


def _null_aggregate_distribution(
    days: Sequence[date], null_by_day: Mapping[date, Sequence[float]]
) -> FloatArray:
    """Assemble the N null strategies by draw index → their per-strategy aggregates.

    Draw ``j`` across the surviving days is one null strategy (the draws are
    memoryless/exchangeable across the index, so index assembly is a valid — and,
    given the seeded panel, deterministic/reproducible — resample). Its aggregate is
    the mean of its per-day net returns. Requires a rectangular panel (equal N per
    day); the run harness maps a ``DayDropped`` draw to ``0.0`` (a flat book) to keep
    it so.
    """
    matrix = np.asarray([np.asarray(null_by_day[d], dtype=np.float64) for d in days])
    if matrix.ndim != 2 or matrix.size == 0:
        raise ValueError("null panel slice must be a non-empty rectangular (days x N) panel")
    aggregates: FloatArray = matrix.mean(axis=0)
    return aggregates


def beat_random_percentile(
    signal_by_day: Mapping[date, float],
    null_by_day: Mapping[date, Sequence[float]],
    *,
    threshold: float,
) -> BeatRandomResult:
    """Compare the arm's aggregate net return to the null aggregate distribution.

    The percentile rank is invariant to any common location shift, so it is identical
    whether computed on raw net or on the excess-over-median — it is a rank *within*
    the null. The arm passes iff its percentile ``≥ threshold``.

    Raises:
        ValueError: if the null panel slice is empty or ragged.
    """
    days = sorted(signal_by_day)
    if not days:
        raise ValueError("empty signal (no surviving days)")
    signal_agg = float(np.mean([signal_by_day[d] for d in days]))
    null_aggs = _null_aggregate_distribution(days, null_by_day)
    beat_pct = 100.0 * float(np.mean(null_aggs < signal_agg))
    null_bar = float(np.percentile(null_aggs, threshold))
    return BeatRandomResult(
        signal_aggregate=signal_agg,
        null_bar=null_bar,
        beat_percentile=beat_pct,
        threshold=float(threshold),
        n_draws=int(null_aggs.size),
        passed=beat_pct >= threshold,
        excess_stream=tuple(excess_over_null_median(signal_by_day, null_by_day)),
    )
