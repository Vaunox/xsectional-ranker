"""Execution-Aware truncation — hand-worked example (numbers checkable by hand).

Long leg (risk-parity weights, per-name ₹ caps):
  L1: w=0.6, cap=600,000 -> c/w = 1,000,000
  L2: w=0.4, cap=1,000,000 -> c/w = 2,500,000   => G_long = 1,000,000 (L1 binds)
Short leg:
  S1: w=0.5, cap=300,000 -> c/w = 600,000
  S2: w=0.5, cap=500,000 -> c/w = 1,000,000     => G_short = 600,000 (S1 binds)

book gross = min(1,000,000, 600,000) = 600,000  (SHORT leg is smaller -> sets gross;
LONG leg scaled pro-rata down to 600,000, weights preserved, k unchanged).

Notionals: L1 360,000 · L2 240,000 · S1 300,000 · S2 300,000 (both legs gross 600,000).
"""

from __future__ import annotations

from xsranker.execution.book import Book, Candidate, DayDropped, Side
from xsranker.execution.truncation import truncate

LONGS = [
    Candidate("L1", Side.LONG, "IT", 0.6, 600_000.0),
    Candidate("L2", Side.LONG, "FMCG", 0.4, 1_000_000.0),
]
SHORTS = [
    Candidate("S1", Side.SHORT, "Auto", 0.5, 300_000.0),
    Candidate("S2", Side.SHORT, "Metals", 0.5, 500_000.0),
]


def test_smaller_leg_sets_gross_larger_scales_pro_rata() -> None:
    book = truncate(LONGS, SHORTS, gross_floor_inr=500_000.0)
    assert isinstance(book, Book)
    assert book.gross_inr == 600_000.0  # the smaller (short) leg sets it
    by = {p.symbol: p for p in book.longs + book.shorts}
    # weights preserved, notionals = weight * gross
    assert by["L1"].weight == 0.6 and by["L1"].notional_inr == 360_000.0
    assert by["L2"].weight == 0.4 and by["L2"].notional_inr == 240_000.0
    assert by["S1"].notional_inr == 300_000.0 and by["S2"].notional_inr == 300_000.0
    # dollar-neutral: both legs gross to 600,000
    assert sum(p.notional_inr for p in book.longs) == 600_000.0
    assert sum(p.notional_inr for p in book.shorts) == 600_000.0
    # k unchanged (2 per leg); no name exceeds its cap
    assert len(book.longs) == 2 and len(book.shorts) == 2
    for p in book.longs + book.shorts:
        cap = {"L1": 600_000, "L2": 1_000_000, "S1": 300_000, "S2": 500_000}[p.symbol]
        assert p.notional_inr <= cap


def test_below_gross_floor_drops_the_day_not_names() -> None:
    dropped = truncate(LONGS, SHORTS, gross_floor_inr=700_000.0)  # 600k < 700k
    assert isinstance(dropped, DayDropped)
    assert "floor" in dropped.reason


def test_weights_must_sum_to_one() -> None:
    import pytest

    bad = [Candidate("A", Side.LONG, "IT", 0.7, 1.0), Candidate("B", Side.LONG, "IT", 0.7, 1.0)]
    with pytest.raises(ValueError, match="sum to 1"):
        truncate(bad, SHORTS, gross_floor_inr=0.0)


def test_empty_leg_drops_the_day() -> None:
    assert isinstance(truncate([], SHORTS, gross_floor_inr=0.0), DayDropped)
