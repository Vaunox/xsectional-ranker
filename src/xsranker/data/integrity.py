"""GATE ZERO — data-integrity validation before any downstream trusts a number.

Runs against the REAL cache: confirms the (stub) universe reconstructs on sampled
dates, the sector map covers the universe, known corporate actions leave NO
spurious split-scale gap in the adjusted series (the second-source cross-check),
hand-verified reference closes match, the Phase-1 derived layer is identity
(adjusted == raw), and the tradability masks produce the expected ~0% fire on the
survivor set. A cross-sectional edge on dirty gaps is worthless and the failure is
invisible unless checked.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from xsranker.core.logging import get_logger
from xsranker.data.factory import DataContext
from xsranker.data.universe.eligibility import (
    SecurityStatus,
    Series,
    long_eligible,
    short_eligible,
)
from xsranker.data.universe.sector_map import uncovered_symbols
from xsranker.features.point_in_time import overnight_gap

_log = get_logger("data.integrity")


@dataclass(frozen=True, slots=True)
class Check:
    """One integrity check's outcome."""

    name: str
    passed: bool
    detail: str


@dataclass(frozen=True, slots=True)
class GateZeroReport:
    """The full gate-zero result."""

    checks: list[Check] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        """Whether every check passed."""
        return all(c.passed for c in self.checks)

    def failures(self) -> list[Check]:
        """The failed checks (empty if clean)."""
        return [c for c in self.checks if not c.passed]


def load_reference(config_dir: Path) -> dict[str, Any]:
    """Load the gate-zero second-source reference (``integrity_reference.yaml``)."""
    data: Any = yaml.safe_load((config_dir / "integrity_reference.yaml").read_text("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("integrity_reference.yaml must be a mapping")
    return data


def _check_universe_reconstructs(ctx: DataContext, sample_dates: list[date]) -> Check:
    survivors = set(ctx.universe.symbols)
    for d in sample_dates:
        constituents = set(ctx.universe.as_of(d))
        if constituents != survivors or not constituents:
            return Check("universe_reconstructs", False, f"mismatch on {d}")
    return Check("universe_reconstructs", True, f"{len(sample_dates)} dates -> full survivor set")


def _check_sector_coverage(ctx: DataContext) -> Check:
    missing = uncovered_symbols(ctx.sector_map, ctx.universe.symbols)
    return Check("sector_coverage", not missing, f"uncovered={missing}" if missing else "full")


def _check_known_split_no_spurious_gap(
    ctx: DataContext, actions: list[dict[str, Any]], threshold: float
) -> Check:
    worst = 0.0
    worst_sym = ""
    for action in actions:
        sym = str(action["symbol"])
        ex = action["ex_date"]
        ex_date = ex if isinstance(ex, date) else date.fromisoformat(str(ex))
        adj = ctx.repository.adjusted(
            sym, start=ex_date - timedelta(days=8), end=ex_date + timedelta(days=3)
        )
        _days, gaps = overnight_gap(adj)
        finite = gaps[np.isfinite(gaps)]
        peak = float(np.max(np.abs(finite))) if finite.size else 0.0
        if peak > worst:
            worst, worst_sym = peak, sym
    passed = worst < threshold
    return Check(
        "known_split_no_spurious_gap",
        passed,
        f"max |adjusted gap| across known ex-dates = {worst:.4f} ({worst_sym}); "
        f"threshold {threshold}",
    )


def _check_reference_closes(ctx: DataContext, refs: list[dict[str, Any]]) -> Check:
    for ref in refs:
        sym = str(ref["symbol"])
        d = ref["date"] if isinstance(ref["date"], date) else date.fromisoformat(str(ref["date"]))
        o = ctx.repository.raw(sym, start=d, end=d)
        got = float(o.close[-1])
        want = float(ref["close"])
        tol = float(ref["tol"])
        if abs(got / want - 1.0) > tol:
            return Check("reference_closes", False, f"{sym} {d}: got {got}, want ~{want}")
    return Check("reference_closes", True, f"{len(refs)} reference closes within tolerance")


def _check_adjusted_identity_phase1(ctx: DataContext, sample_symbol: str) -> Check:
    days = ctx.broker.trading_dates(sample_symbol)
    window = (days[len(days) // 2], days[len(days) // 2 + 3])
    raw = ctx.repository.raw(sample_symbol, start=window[0], end=window[1])
    adj = ctx.repository.adjusted(sample_symbol, start=window[0], end=window[1])
    identical = bool(
        np.array_equal(raw.close, adj.close) and np.array_equal(raw.volume, adj.volume)
    )
    return Check(
        "adjusted_identity_phase1",
        identical,
        "Phase-1 adjusted == raw (empty action list) as stamped",
    )


def _check_tradability_masks(ctx: DataContext) -> Check:
    # Survivor status: all EQ / non-surveillance / shortable -> both masks pass.
    excluded = 0
    for sym in ctx.universe.symbols:
        status = SecurityStatus(sym, Series.EQ, asm=False, gsm=False, shortable=True)
        if not (long_eligible(status) and short_eligible(status)):
            excluded += 1
    fire_rate = excluded / len(ctx.universe.symbols)
    _log.info("mask_fire_rate", fire_rate=fire_rate, expected="~0.0 (survivor stub)")
    return Check(
        "tradability_masks",
        fire_rate == 0.0,
        f"survivor-set mask fire-rate = {fire_rate:.4f} (expected ~0%, the correct signature)",
    )


def run_gate_zero(ctx: DataContext) -> GateZeroReport:
    """Run all gate-zero checks against the real cache; return the report."""
    ref = load_reference(ctx.settings.config_dir)
    sample_dates = [
        d if isinstance(d, date) else date.fromisoformat(str(d))
        for d in ref.get("universe_sample_dates", [])
    ]
    threshold = float(ref["spurious_gap_threshold"])
    checks = [
        _check_universe_reconstructs(ctx, sample_dates),
        _check_sector_coverage(ctx),
        _check_known_split_no_spurious_gap(ctx, list(ref.get("known_actions", [])), threshold),
        _check_reference_closes(ctx, list(ref.get("reference_closes", []))),
        _check_adjusted_identity_phase1(ctx, ctx.universe.symbols[0]),
        _check_tradability_masks(ctx),
    ]
    report = GateZeroReport(checks=checks)
    _log.info(
        "gate_zero",
        passed=report.all_passed,
        checks=len(checks),
        failures=[c.name for c in report.failures()],
    )
    return report
