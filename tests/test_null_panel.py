# mypy: disable-error-code="no-untyped-def, no-any-return, no-untyped-call"
"""Global Null Panel — symmetric-execution proof + seeded reproducibility.

The null must traverse the byte-identical execution path as the signal, differing only
at selection; and the same seed must reproduce the panel byte-for-byte.
"""

from __future__ import annotations

from datetime import date

import numpy as np

from xsranker.core.config import load_settings
from xsranker.execution import pipeline
from xsranker.execution.book import Book, DayDropped
from xsranker.execution.config import ExecutionConfig
from xsranker.execution.pipeline import SymbolInputs, build_book
from xsranker.harness.adapter import HarnessAdapter
from xsranker.null import panel as null_panel
from xsranker.null.panel import build_random_book, generate_null_panel

CFG = ExecutionConfig(
    k_per_leg=2, participation_cap=0.01, gross_floor_inr=1_000.0, sector_cap_divisor=2
)


def _adapter() -> HarnessAdapter:
    return HarnessAdapter(load_settings())


def _sym(symbol, signal, sector="IT", atr=2.0, ewv=100_000_000.0, le=True, se=True, locked=False):
    return SymbolInputs(symbol, signal, sector, atr, ewv, le, se, locked)


def _rich_panel():
    # 8 names across sectors, all eligible -> real selection freedom for both paths
    return [
        _sym("A", -0.06, "IT"),
        _sym("B", -0.04, "Auto"),
        _sym("C", -0.02, "FMCG"),
        _sym("D", -0.01, "Metals"),
        _sym("E", 0.01, "Pharma"),
        _sym("F", 0.02, "Energy"),
        _sym("G", 0.04, "Power"),
        _sym("H", 0.06, "Cement"),
    ]


def test_signal_and_null_share_the_identical_execution(monkeypatch) -> None:
    """Both paths route through the SAME finalize — only the ordering (selection) differs."""
    seen: list[tuple[tuple[str, ...], tuple[str, ...]]] = []
    real = pipeline.finalize

    def spy(long_ordered, short_ordered, by_symbol, cfg):
        seen.append((tuple(long_ordered), tuple(short_ordered)))
        return real(long_ordered, short_ordered, by_symbol, cfg)

    monkeypatch.setattr(pipeline, "finalize", spy)
    monkeypatch.setattr(null_panel, "finalize", spy)
    build_book(_rich_panel(), _adapter(), CFG)
    build_random_book(_rich_panel(), CFG, np.random.default_rng(0))
    assert len(seen) == 2  # both the signal and the null invoked the shared finalize


def test_same_selection_yields_byte_identical_book() -> None:
    """With exactly k eligible per leg, signal and null MUST select the same names -> same book."""
    # 2 long-only + 2 short-only (disjoint, no excess) -> selection is forced for both
    panel = [
        _sym("L1", -0.05, "IT", se=False),
        _sym("L2", -0.04, "Auto", se=False),
        _sym("S1", 0.04, "FMCG", le=False),
        _sym("S2", 0.05, "Metals", le=False),
    ]
    signal_book = build_book(panel, _adapter(), CFG)
    null_book, _ = build_random_book(panel, CFG, np.random.default_rng(123))
    assert isinstance(signal_book, Book) and isinstance(null_book, Book)

    # identical economic book: same gross, same {name, weight, notional} per leg
    # (tuple order within a leg is presentation, not economics)
    def _leg(positions):
        return {(p.symbol, p.side, p.weight, p.notional_inr) for p in positions}

    assert signal_book.gross_inr == null_book.gross_inr
    assert _leg(signal_book.longs) == _leg(null_book.longs)
    assert _leg(signal_book.shorts) == _leg(null_book.shorts)


def test_seeded_panel_is_reproducible() -> None:
    days = {date(2024, 1, d): _rich_panel() for d in (2, 3, 4)}
    p1 = generate_null_panel(days, CFG, seed=42, draws_per_day=8)
    p2 = generate_null_panel(days, CFG, seed=42, draws_per_day=8)
    assert p1 == p2  # byte-identical panel from the same seed
    p3 = generate_null_panel(days, CFG, seed=43, draws_per_day=8)
    assert p1 != p3  # a different seed draws differently


def test_slice_to_surviving_days() -> None:
    days = {date(2024, 1, d): _rich_panel() for d in (2, 3, 4)}
    panel = generate_null_panel(days, CFG, seed=7, draws_per_day=4)
    sliced = panel.slice_to({date(2024, 1, 2), date(2024, 1, 4)})
    assert sliced.days() == (date(2024, 1, 2), date(2024, 1, 4))
    assert sliced.draws[date(2024, 1, 2)] == panel.draws[date(2024, 1, 2)]  # unchanged draws


def test_random_null_book_is_feasible_on_every_draw() -> None:
    """No zero-pads (the 2026-07-11 fix): on a feasible panel every draw yields a valid
    Book, never a DayDropped. Before the fix ~50% of draws were infeasible and zero-padded."""
    panel = _rich_panel()  # 8 distinct-sector names, k=2 -> a valid disjoint 2+2 book exists
    drops = sum(
        isinstance(build_random_book(panel, CFG, np.random.default_rng(seed))[0], DayDropped)
        for seed in range(300)
    )
    assert drops == 0


def test_random_null_book_respects_the_cap_and_disjointness() -> None:
    """The random book obeys the SAME ⌈k/2⌉ sector cap + disjoint legs as the signal book."""
    book, _ = build_random_book(_rich_panel(), CFG, np.random.default_rng(1))
    assert isinstance(book, Book)
    longs = {p.symbol for p in book.longs}
    shorts = {p.symbol for p in book.shorts}
    assert len(longs) == CFG.k_per_leg and len(shorts) == CFG.k_per_leg
    assert longs.isdisjoint(shorts)  # disjoint legs
    for leg in (book.longs, book.shorts):
        by_sector: dict[str, int] = {}
        for p in leg:
            by_sector[p.sector] = by_sector.get(p.sector, 0) + 1
        assert max(by_sector.values()) <= CFG.sector_cap


def test_null_and_signal_share_a_genuinely_infeasible_day() -> None:
    """Shared day-drop: when no valid k+k capped disjoint book is feasible at all, BOTH the
    signal and the null drop the day (symmetry) — the null never zero-pads it instead."""
    # 4 names, all one sector; ⌈2/2⌉ = 1 per sector per leg -> a 2-name leg is impossible.
    panel = [
        _sym("A", -0.05, "IT"),
        _sym("B", -0.04, "IT"),
        _sym("C", 0.04, "IT"),
        _sym("D", 0.05, "IT"),
    ]
    assert isinstance(build_random_book(panel, CFG, np.random.default_rng(0))[0], DayDropped)
    assert isinstance(build_book(panel, _adapter(), CFG), DayDropped)  # the signal shares it


def test_null_book_must_clear_the_same_floor_as_the_signal() -> None:
    """The null faces the IDENTICAL gross floor (2026-07-11 correction — NOT floor 0): when
    every feasible book is below the floor, BOTH the signal and the null drop the day."""
    # entry-window value Rs 1,000 -> per-name cap Rs 10 -> book gross ~ Rs 20, far below the floor.
    cfg = ExecutionConfig(
        k_per_leg=2, participation_cap=0.01, gross_floor_inr=5_000_000.0, sector_cap_divisor=2
    )
    panel = [
        _sym("A", -0.05, "IT", ewv=1_000.0),
        _sym("B", -0.04, "Auto", ewv=1_000.0),
        _sym("C", 0.04, "FMCG", ewv=1_000.0),
        _sym("D", 0.05, "Metals", ewv=1_000.0),
    ]
    assert isinstance(build_random_book(panel, cfg, np.random.default_rng(0))[0], DayDropped)
    assert isinstance(build_book(panel, _adapter(), cfg), DayDropped)  # the signal shares the floor


def test_null_endures_circuit_and_mask_like_the_signal() -> None:
    panel = [_sym(s.symbol, s.signal, s.sector) for s in _rich_panel()]
    panel[0] = _sym("A", -0.06, "IT", locked=True)  # circuit-locked
    panel[7] = _sym("H", 0.06, "Cement", se=False)  # short-ineligible
    for _ in range(50):
        book, _ = build_random_book(panel, CFG, np.random.default_rng(_))
        if isinstance(book, DayDropped):
            continue
        names = {p.symbol for p in book.longs + book.shorts}
        assert "A" not in names  # circuit-locked never appears
        assert "H" not in {p.symbol for p in book.shorts}  # short-ineligible never shorted
