"""Run-level logged diagnostics (informational, never gates).

Computed from the run counters + the assembled cross-section. Market-day conditioning
lives in ``gate.diagnostics`` and needs an index return series — the survivor cache has
none (49 stocks, no index partition), so it is marked UNAVAILABLE for the smoke run
rather than fed an improvised proxy.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from xsranker.backtest.harness import ArmRun, SymbolDay
from xsranker.execution.book import Book


@dataclass(frozen=True, slots=True)
class RunDiagnostics:
    """Per-arm logged diagnostics (fractions in [0, 1])."""

    surviving_days: int
    signal_day_drop_fraction: float
    null_draw_day_drop_fraction: float
    short_ban_fire_rate: float  # over all null draws; expect ~0 on large-cap survivors
    circuit_flag_fraction: float


def run_diagnostics(
    arm_run: ArmRun,
    cross_section: Mapping[date, Sequence[SymbolDay]],
    *,
    draws_per_day: int,
) -> RunDiagnostics:
    """Summarize the run's structural diagnostics for one arm."""
    surviving = len(arm_run.optimistic.signal_by_day)
    attempted = surviving + arm_run.signal_day_drops
    total_null = surviving * draws_per_day
    symbol_days = sum(len(panel) for panel in cross_section.values())
    circuit_locked = sum(
        1 for panel in cross_section.values() for sd in panel if sd.inputs.circuit_locked
    )
    return RunDiagnostics(
        surviving_days=surviving,
        signal_day_drop_fraction=(arm_run.signal_day_drops / attempted) if attempted else 0.0,
        null_draw_day_drop_fraction=(
            (arm_run.null_draw_day_drops / total_null) if total_null else 0.0
        ),
        short_ban_fire_rate=(arm_run.short_ban_fires / total_null) if total_null else 0.0,
        circuit_flag_fraction=(circuit_locked / symbol_days) if symbol_days else 0.0,
    )


def sector_concentration(book: Book) -> float:
    """Post-hoc max single-sector share across the two legs (behind the ex-ante cap).

    1.0 means a leg was entirely one sector; the ex-ante ceil(k/2) cap already bounds
    this, so a value near the cap's implied share is expected, not alarming.
    """
    shares: list[float] = []
    for leg in (book.longs, book.shorts):
        if not leg:
            continue
        by_sector: dict[str, int] = {}
        for p in leg:
            by_sector[p.sector] = by_sector.get(p.sector, 0) + 1
        shares.append(max(by_sector.values()) / len(leg))
    return max(shares) if shares else 0.0
