"""Book value types for the cross-sectional long-short book."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Side(StrEnum):
    """Book side. LONG the biggest gap-downs; SHORT the biggest gap-ups."""

    LONG = "LONG"
    SHORT = "SHORT"


@dataclass(frozen=True, slots=True)
class Candidate:
    """A selected name pre-truncation: its risk-parity weight and per-name ₹ cap.

    ``risk_weight`` is the inverse-vol weight WITHIN its leg (the leg's weights sum
    to 1). ``max_fill_inr`` is the pessimistic participation cap (≤ 1% of the
    entry-window traded value), the most this name can absorb.
    """

    symbol: str
    side: Side
    sector: str
    risk_weight: float
    max_fill_inr: float


@dataclass(frozen=True, slots=True)
class Position:
    """A name in the final book: its risk-parity weight and post-truncation ₹ notional."""

    symbol: str
    side: Side
    sector: str
    weight: float
    notional_inr: float


@dataclass(frozen=True, slots=True)
class Book:
    """A tradeable, dollar-neutral book for one day (gross matched across legs)."""

    longs: tuple[Position, ...]
    shorts: tuple[Position, ...]
    gross_inr: float  # per-leg gross (legs are matched); book notional = 2 * gross_inr


@dataclass(frozen=True, slots=True)
class DayDropped:
    """A day dropped from the sample (untradeable). NEVER drop names — drop the day."""

    reason: str
