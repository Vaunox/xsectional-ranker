# mypy: disable-error-code="no-untyped-def, no-any-return, no-untyped-call"
"""The frozen order-of-operations pipeline — each step + the wired whole (Deep Dive 02)."""

from __future__ import annotations

from xsranker.core.config import load_settings
from xsranker.execution.book import Book, DayDropped, Side
from xsranker.execution.config import ExecutionConfig
from xsranker.execution.pipeline import SymbolInputs, build_book
from xsranker.harness.adapter import HarnessAdapter

CFG = ExecutionConfig(
    k_per_leg=2, participation_cap=0.01, gross_floor_inr=1_000.0, sector_cap_divisor=2
)


def _adapter() -> HarnessAdapter:
    return HarnessAdapter(load_settings())


def _sym(symbol, signal, sector="IT", atr=2.0, ewv=100_000_000.0, le=True, se=True, locked=False):
    return SymbolInputs(symbol, signal, sector, atr, ewv, le, se, locked)


def _distinct_panel():
    # signals distinct; 6 names across sectors. Lowest 2 -> LONG; highest 2 -> SHORT.
    return [
        _sym("A", -0.05, "IT"),
        _sym("B", -0.03, "Auto"),
        _sym("C", -0.01, "FMCG"),
        _sym("D", 0.01, "Metals"),
        _sym("E", 0.03, "Pharma"),
        _sym("F", 0.05, "Energy"),
    ]


def test_pipeline_builds_a_book_selecting_extremes() -> None:
    book = build_book(_distinct_panel(), _adapter(), CFG)
    assert isinstance(book, Book)
    assert {p.symbol for p in book.longs} == {"A", "B"}  # biggest gap-downs -> LONG
    assert {p.symbol for p in book.shorts} == {"E", "F"}  # biggest gap-ups -> SHORT
    assert all(p.side is Side.LONG for p in book.longs)
    assert book.gross_inr > 0.0


def test_pipeline_enforces_sector_cap() -> None:
    # top-3 gap-ups are all Metals; ceil(k/2)=1 cap forces the short leg to diversify.
    panel = [
        _sym("A", -0.05, "IT"),
        _sym("B", -0.04, "Auto"),
        _sym("M1", 0.05, "Metals"),
        _sym("M2", 0.04, "Metals"),
        _sym("M3", 0.03, "Metals"),
        _sym("X", 0.02, "FMCG"),
    ]
    book = build_book(panel, _adapter(), CFG)
    assert isinstance(book, Book)
    shorts = {p.symbol for p in book.shorts}
    assert "M1" in shorts and "M2" not in shorts  # only one Metals short (cap=1)
    assert "X" in shorts  # next eligible non-Metals filled the leg


def test_pipeline_drops_day_below_gross_floor() -> None:
    # tiny entry-window value -> cap tiny -> gross below floor -> day dropped
    panel = [_sym(s.symbol, s.signal, s.sector, ewv=10.0) for s in _distinct_panel()]
    assert isinstance(build_book(panel, _adapter(), CFG), DayDropped)


def test_pipeline_masks_and_circuit_exclude_names() -> None:
    panel = _distinct_panel()
    # F (top short) circuit-locked and E short-ineligible -> shorts fall back to D, then day-drops or picks next
    panel = [
        _sym("A", -0.05, "IT"),
        _sym("B", -0.03, "Auto"),
        _sym("C", -0.01, "FMCG"),
        _sym("D", 0.01, "Metals"),
        _sym("E", 0.03, "Pharma", se=False),
        _sym("F", 0.05, "Energy", locked=True),
    ]
    book = build_book(panel, _adapter(), CFG)
    assert isinstance(book, Book)
    shorts = {p.symbol for p in book.shorts}
    assert "F" not in shorts and "E" not in shorts  # locked / short-ineligible excluded
    assert shorts == {"C", "D"}  # next two short-eligible, non-locked names by rank
